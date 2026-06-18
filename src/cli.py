"""
cli.py — Interface de linha de comando (CLI).

Permite usar o analisador via terminal, sem interface gráfica,
para integração com scripts, automações e pipelines de dados.

Exemplos de uso:
    # Análise de arquivo único
    python main.py --cli -i processo.pdf -o resultado.csv -t "Juridico Pje"

    # Análise em lote de uma pasta
    python main.py --cli -i ./processos/ -o relatorio.xlsx -t "Juridico Pje" -f xlsx

    # Listar templates disponíveis
    python main.py --cli --list-templates
"""

import argparse
import sys
import os
import logging
from pathlib import Path

from src.config.settings import (
    setup_logging,
    get_available_templates,
    SUPPORTED_INPUT_EXTENSIONS,
    SUPPORTED_OUTPUT_FORMATS,
)
from src.core.document_reader import read_document, DocumentReadError
from src.core.ai_analyzer import analyze_document, analyze_batch
from src.core.output_writer import save_result, merge_batch_results
from src.validators.response_validator import validate_response, ValidationError

logger = logging.getLogger(__name__)


def list_templates():
    """Lista todos os templates de prompt disponíveis."""
    templates = get_available_templates()
    if not templates:
        print("Nenhum template encontrado na pasta src/prompts/")
        return

    print("\n📋 Templates de análise disponíveis:\n")
    print(f"  {'Nome':<30} {'Arquivo'}")
    print(f"  {'─' * 30} {'─' * 40}")
    for name, path in templates.items():
        print(f"  {name:<30} {path.name}")
    print(f"\n  Total: {len(templates)} template(s)")
    print(f"  Para criar um novo, copie 'custom_template.txt' na pasta src/prompts/\n")


def collect_files(input_path: str) -> list[str]:
    """Coleta arquivos de um caminho (arquivo ou diretório)."""
    path = Path(input_path)

    if path.is_file():
        return [str(path)]

    if path.is_dir():
        files = []
        for ext in SUPPORTED_INPUT_EXTENSIONS:
            files.extend(path.rglob(f"*{ext}"))
        files = [str(f) for f in sorted(files)]
        if not files:
            print(f"❌ Nenhum arquivo suportado encontrado em: {path}")
            sys.exit(1)
        return files

    print(f"❌ Caminho não encontrado: {input_path}")
    sys.exit(1)


def run_cli(args: argparse.Namespace):
    """Executa a análise via CLI."""
    setup_logging()

    # Listar templates
    if args.list_templates:
        list_templates()
        return

    # Validar argumentos obrigatórios
    if not args.input:
        print("❌ Argumento --input (-i) obrigatório. Use --help para ver opções.")
        sys.exit(1)

    # Obter template
    templates = get_available_templates()
    if args.template:
        template_path = templates.get(args.template)
        if not template_path:
            print(f"❌ Template '{args.template}' não encontrado.")
            print(f"   Disponíveis: {', '.join(templates.keys())}")
            sys.exit(1)
    else:
        # Usar primeiro template disponível
        if templates:
            first_name = list(templates.keys())[0]
            template_path = templates[first_name]
            print(f"ℹ️  Usando template padrão: {first_name}")
        else:
            print("❌ Nenhum template encontrado.")
            sys.exit(1)

    # Coletar arquivos
    files = collect_files(args.input)
    output_format = args.format.lower()
    output_path = args.output

    print(f"\n🔍 Arquivos encontrados: {len(files)}")
    print(f"📋 Template: {args.template or 'padrão'}")
    print(f"💾 Formato de saída: {output_format.upper()}")
    print(f"📁 Destino: {output_path}\n")

    if len(files) == 1:
        # Arquivo único
        file_path = files[0]
        print(f"📄 Lendo: {os.path.basename(file_path)}...")

        try:
            content = read_document(file_path)
        except DocumentReadError as e:
            print(f"❌ Erro na leitura: {e}")
            sys.exit(1)

        print("🤖 Analisando com IA...")
        try:
            result = analyze_document(content, template_path)
        except Exception as e:
            print(f"❌ Erro na análise: {e}")
            sys.exit(1)

        # Validar
        try:
            validation = validate_response(result)
            if validation["warnings"]:
                for w in validation["warnings"]:
                    print(f"⚠️  {w}")
        except ValidationError as e:
            print(f"⚠️  Aviso de validação: {e}")

        # Salvar
        try:
            save_result(result, output_path, output_format)
            print(f"\n✅ Resultado salvo em: {output_path}")
        except Exception as e:
            print(f"❌ Erro ao salvar: {e}")
            sys.exit(1)

    else:
        # Lote
        file_contents = []
        for fp in files:
            try:
                content = read_document(fp)
                file_contents.append((os.path.basename(fp), content))
                print(f"  ✔ {os.path.basename(fp)}")
            except DocumentReadError as e:
                print(f"  ✖ {os.path.basename(fp)}: {e}")

        if not file_contents:
            print("❌ Nenhum documento pôde ser lido.")
            sys.exit(1)

        def progress_cb(current, total, filename):
            if current < total:
                print(f"  [{current+1}/{total}] Analisando: {filename}...")

        print(f"\n🤖 Analisando {len(file_contents)} documento(s)...\n")
        results = analyze_batch(file_contents, template_path, progress_cb)

        # Consolidar
        merged = merge_batch_results(results)
        if not merged:
            print("❌ Nenhum resultado gerado.")
            sys.exit(1)

        # Salvar
        try:
            save_result(merged, output_path, output_format)
        except Exception as e:
            print(f"❌ Erro ao salvar: {e}")
            sys.exit(1)

        # Relatório
        errors = [r for r in results if r[2] is not None]
        success = len(results) - len(errors)
        print(f"\n{'─' * 50}")
        print(f"✅ {success} analisado(s) com sucesso")
        if errors:
            print(f"❌ {len(errors)} erro(s):")
            for name, _, err in errors:
                print(f"   • {name}: {err}")
        print(f"💾 Salvo em: {output_path}")
        print(f"{'─' * 50}\n")


def build_parser() -> argparse.ArgumentParser:
    """Constrói o parser de argumentos CLI."""
    parser = argparse.ArgumentParser(
        description="AI Document Analyzer — Análise inteligente de documentos com IA",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  %(prog)s --cli -i processo.pdf -o resultado.csv
  %(prog)s --cli -i ./processos/ -o relatorio.xlsx -f xlsx -t "Juridico Pje"
  %(prog)s --cli --list-templates
        """,
    )

    parser.add_argument(
        "--cli",
        action="store_true",
        help="Executar em modo CLI (sem interface gráfica)",
    )

    parser.add_argument(
        "-i", "--input",
        type=str,
        help="Arquivo ou pasta de entrada (PDF, TXT, DOCX)",
    )

    parser.add_argument(
        "-o", "--output",
        type=str,
        default="resultado.csv",
        help="Arquivo de saída (padrão: resultado.csv)",
    )

    parser.add_argument(
        "-t", "--template",
        type=str,
        help="Nome do template de análise (use --list-templates para ver)",
    )

    parser.add_argument(
        "-f", "--format",
        type=str,
        choices=["csv", "tsv", "json", "xlsx"],
        default="csv",
        help="Formato de saída (padrão: csv)",
    )

    parser.add_argument(
        "--list-templates",
        action="store_true",
        help="Listar templates de análise disponíveis",
    )

    return parser
