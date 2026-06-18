"""
ai_analyzer.py — Módulo de comunicação com a API do Google Gemini.

Responsável por: carregar templates de prompt, montar o prompt final,
enviar à API com retry automático, e limpar a resposta.
"""

import logging
from pathlib import Path

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.config.settings import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    RETRY_ATTEMPTS,
    RETRY_MIN_WAIT,
    RETRY_MAX_WAIT,
    PROMPTS_DIR,
)

logger = logging.getLogger(__name__)

# --- Configuração da API ---
_api_configured = False


def _ensure_api_configured():
    """Configura a API do Gemini apenas uma vez."""
    global _api_configured
    if _api_configured:
        return

    if not GEMINI_API_KEY:
        raise ConnectionError(
            "Chave da API Gemini não encontrada. "
            "Configure GEMINI_API_KEY no arquivo .env"
        )

    genai.configure(api_key=GEMINI_API_KEY)
    _api_configured = True
    logger.info(f"API Gemini configurada com modelo: {GEMINI_MODEL}")


def load_prompt_template(template_path: Path) -> str:
    """
    Carrega um template de prompt de um arquivo .txt.

    O template deve conter o placeholder {file_content} onde o 
    conteúdo do documento será injetado.

    Args:
        template_path: Caminho para o arquivo .txt do template

    Returns:
        String do template com placeholder {file_content}
    """
    if not template_path.exists():
        raise FileNotFoundError(f"Template não encontrado: {template_path}")

    template = template_path.read_text(encoding="utf-8")

    if "{file_content}" not in template:
        raise ValueError(
            f"Template inválido: '{template_path.name}' não contém "
            "o placeholder {{file_content}}"
        )

    logger.info(f"Template carregado: {template_path.name} ({len(template)} chars)")
    return template


def build_prompt(template: str, file_content: str) -> str:
    """Monta o prompt final injetando o conteúdo do documento no template."""
    prompt = template.replace("{file_content}", file_content)
    logger.debug(f"Prompt montado: {len(prompt)} caracteres")
    return prompt


def clean_response(raw_response: str) -> str:
    """
    Limpa a resposta da IA removendo artefatos markdown.
    
    A IA frequentemente retorna a resposta envolvida em blocos 
    de código (```tsv...```) mesmo quando instruída a não fazê-lo.
    """
    cleaned = raw_response.strip()

    # Remove blocos de código markdown (```tsv ... ```)
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Remove primeira linha (```tsv ou ```)
        if lines[0].startswith("```"):
            lines = lines[1:]
        # Remove última linha (```)
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)

    # Remove backticks soltos
    cleaned = cleaned.replace("`", "").strip()

    # Remove prefixos de formato
    for prefix in ["tsv", "csv", "TSV", "CSV"]:
        if cleaned.lower().startswith(prefix):
            cleaned = cleaned[len(prefix):].strip()

    return cleaned


@retry(
    stop=stop_after_attempt(RETRY_ATTEMPTS),
    wait=wait_exponential(min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    before_sleep=lambda retry_state: logger.warning(
        f"Tentativa {retry_state.attempt_number} falhou. "
        f"Aguardando antes de tentar novamente..."
    ),
)
def _call_gemini(prompt: str) -> str:
    """
    Chama a API do Gemini com retry automático e backoff exponencial.

    Tentativas: até RETRY_ATTEMPTS vezes
    Espera: começa em RETRY_MIN_WAIT segundos, dobra até RETRY_MAX_WAIT
    """
    _ensure_api_configured()

    logger.info(f"Enviando prompt ao Gemini ({GEMINI_MODEL})...")
    model = genai.GenerativeModel(GEMINI_MODEL)
    response = model.generate_content(prompt)

    if not response.text:
        raise ValueError("A API retornou uma resposta vazia")

    logger.info(f"Resposta recebida: {len(response.text)} caracteres")
    return response.text


def analyze_document(file_content: str, template_path: Path) -> str:
    """
    Pipeline completo de análise: template → prompt → API → limpeza.

    Args:
        file_content: Texto do documento a ser analisado
        template_path: Caminho para o arquivo de template do prompt

    Returns:
        Dados estruturados (TSV) limpos, prontos para validação e escrita
    """
    template = load_prompt_template(template_path)
    prompt = build_prompt(template, file_content)
    raw_response = _call_gemini(prompt)
    cleaned = clean_response(raw_response)

    logger.info("Análise concluída com sucesso")
    return cleaned


def analyze_batch(
    file_contents: list[tuple[str, str]],
    template_path: Path,
    progress_callback=None,
) -> list[tuple[str, str, str | None]]:
    """
    Analisa múltiplos documentos em sequência.

    Args:
        file_contents: Lista de tuplas (nome_arquivo, conteúdo_texto)
        template_path: Caminho do template de prompt
        progress_callback: Função(current, total, filename) para reportar progresso

    Returns:
        Lista de tuplas (nome_arquivo, resultado_ou_vazio, erro_ou_none)
    """
    results = []
    total = len(file_contents)

    for i, (filename, content) in enumerate(file_contents):
        if progress_callback:
            progress_callback(i, total, filename)

        try:
            logger.info(f"[{i+1}/{total}] Analisando: {filename}")
            result = analyze_document(content, template_path)
            results.append((filename, result, None))
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[{i+1}/{total}] Erro em {filename}: {error_msg}")
            results.append((filename, "", error_msg))

    if progress_callback:
        progress_callback(total, total, "Concluído")

    return results
