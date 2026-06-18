"""
main.py — Ponto de entrada da aplicação.

Suporta dois modos de execução:
  - GUI (padrão):  python main.py
  - CLI:           python main.py --cli -i arquivo.pdf -o resultado.csv

Use --help para ver todas as opções do modo CLI.
"""

import sys
import os

# Garante que o diretório raiz do projeto está no sys.path
# para que imports como "from src.xxx" funcionem de qualquer lugar
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


def _check_dependencies(is_cli=False):
    """Verifica se as dependências obrigatórias estão instaladas."""
    missing = []
    required = {
        "dotenv": "python-dotenv",
        "google.generativeai": "google-generativeai",
        "PyPDF2": "PyPDF2",
        "tenacity": "tenacity",
    }
    
    # CustomTkinter só é obrigatório se não for rodar via CLI
    if not is_cli:
        required["customtkinter"] = "customtkinter"
        
    for module, package in required.items():
        try:
            import importlib
            importlib.import_module(module)
        except ImportError:
            missing.append(package)

    if missing:
        print("❌ Dependências não instaladas:")
        for pkg in missing:
            print(f"   • {pkg}")
        print(f"\nExecute: pip install -r requirements.txt")
        print(f"Ou:      pip install {' '.join(missing)}")
        if "customtkinter" in missing:
            print(f"\nNota para Linux (Ubuntu/Debian): Se o erro for sobre o pacote 'tkinter', instale-o com:")
            print(f"sudo apt install python3-tk")
        sys.exit(1)


def main():
    is_cli = "--cli" in sys.argv or "--list-templates" in sys.argv
    _check_dependencies(is_cli)

    from src.cli import build_parser, run_cli

    parser = build_parser()
    args = parser.parse_args()

    if args.cli or args.list_templates:
        # Modo CLI — sem interface gráfica
        run_cli(args)
    else:
        # Modo GUI — interface gráfica
        from src.ui.app import App
        app = App()
        app.mainloop()


if __name__ == "__main__":
    main()