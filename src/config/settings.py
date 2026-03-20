"""
settings.py — Configurações centralizadas da aplicação.

Centraliza todas as constantes, carregamento de variáveis de ambiente,
e configuração de logging em um único lugar, evitando valores hardcoded
espalhados pelo código.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# --- Caminhos ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SRC_DIR = Path(__file__).resolve().parent.parent
PROMPTS_DIR = SRC_DIR / "prompts"

# --- Variáveis de Ambiente ---
load_dotenv(BASE_DIR / ".env")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- Modelo da IA ---
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# --- Limites ---
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# --- Retry ---
RETRY_ATTEMPTS = int(os.getenv("RETRY_ATTEMPTS", "3"))
RETRY_MIN_WAIT = int(os.getenv("RETRY_MIN_WAIT", "2"))
RETRY_MAX_WAIT = int(os.getenv("RETRY_MAX_WAIT", "30"))

# --- Formatos Suportados ---
SUPPORTED_INPUT_EXTENSIONS = {".pdf", ".txt", ".docx"}
SUPPORTED_OUTPUT_FORMATS = {"csv", "tsv", "json", "xlsx"}

# --- Logging ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging():
    """Configura o logging global da aplicação."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
    )
    # Reduz verbosidade de bibliotecas externas
    logging.getLogger("google").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_available_templates():
    """Retorna os templates de prompt disponíveis na pasta de prompts."""
    templates = {}
    if PROMPTS_DIR.exists():
        for f in sorted(PROMPTS_DIR.glob("*.txt")):
            # Nome amigável: "juridico_pje" → "Jurídico PJE"
            name = f.stem.replace("_", " ").title()
            templates[name] = f
    return templates
