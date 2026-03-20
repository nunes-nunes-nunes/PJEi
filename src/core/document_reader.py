"""
document_reader.py — Módulo responsável pela leitura de documentos.

Extrai texto de PDF, TXT e DOCX com validação de tipo e tamanho.
Separado do handler de IA para respeitar o princípio de responsabilidade única.
"""

import logging
from pathlib import Path

import PyPDF2

from src.config.settings import MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB, SUPPORTED_INPUT_EXTENSIONS

logger = logging.getLogger(__name__)


class DocumentReadError(Exception):
    """Erro na leitura de um documento."""
    pass


class UnsupportedFormatError(DocumentReadError):
    """Formato de arquivo não suportado."""
    pass


class FileTooLargeError(DocumentReadError):
    """Arquivo excede o tamanho máximo."""
    pass


def validate_file(file_path: str) -> Path:
    """
    Valida existência, extensão e tamanho do arquivo.
    
    Returns:
        Path validado
    Raises:
        FileNotFoundError, UnsupportedFormatError, FileTooLargeError
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    if path.suffix.lower() not in SUPPORTED_INPUT_EXTENSIONS:
        raise UnsupportedFormatError(
            f"Formato '{path.suffix}' não suportado. "
            f"Use: {', '.join(SUPPORTED_INPUT_EXTENSIONS)}"
        )

    file_size = path.stat().st_size
    if file_size > MAX_FILE_SIZE_BYTES:
        raise FileTooLargeError(
            f"Arquivo muito grande ({file_size / 1024 / 1024:.1f} MB). "
            f"Máximo: {MAX_FILE_SIZE_MB} MB"
        )

    logger.info(f"Arquivo validado: {path.name} ({file_size / 1024:.1f} KB)")
    return path


def read_pdf(file_path: Path) -> str:
    """Extrai texto de um arquivo PDF usando PyPDF2."""
    text = ""
    try:
        with open(file_path, "rb") as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            total_pages = len(reader.pages)
            logger.info(f"PDF com {total_pages} página(s)")

            for i, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                text += page_text
                logger.debug(f"Página {i+1}/{total_pages}: {len(page_text)} caracteres")

    except PyPDF2.errors.PdfReadError as e:
        raise DocumentReadError(f"PDF corrompido ou protegido por senha: {e}")

    if not text.strip():
        raise DocumentReadError(
            "Nenhum texto extraído do PDF. "
            "O arquivo pode ser uma imagem escaneada (necessita OCR)."
        )

    return text


def read_txt(file_path: Path) -> str:
    """Lê conteúdo de um arquivo de texto puro."""
    encodings = ["utf-8", "latin-1", "cp1252"]

    for encoding in encodings:
        try:
            text = file_path.read_text(encoding=encoding)
            logger.info(f"TXT lido com encoding {encoding}: {len(text)} caracteres")
            return text
        except UnicodeDecodeError:
            continue

    raise DocumentReadError(
        f"Não foi possível ler o arquivo TXT com os encodings: {encodings}"
    )


def read_docx(file_path: Path) -> str:
    """Extrai texto de um arquivo DOCX."""
    try:
        import docx
    except ImportError:
        raise DocumentReadError(
            "Biblioteca 'python-docx' não instalada. "
            "Execute: pip install python-docx"
        )

    try:
        doc = docx.Document(str(file_path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        text = "\n".join(paragraphs)
        logger.info(f"DOCX lido: {len(paragraphs)} parágrafos, {len(text)} caracteres")
        return text
    except Exception as e:
        raise DocumentReadError(f"Erro ao ler DOCX: {e}")


def read_document(file_path: str) -> str:
    """
    Função principal: valida e lê qualquer documento suportado.

    Args:
        file_path: Caminho do arquivo (PDF, TXT ou DOCX)
    
    Returns:
        Texto extraído do documento
    """
    path = validate_file(file_path)
    ext = path.suffix.lower()

    readers = {
        ".pdf": read_pdf,
        ".txt": read_txt,
        ".docx": read_docx,
    }

    reader = readers.get(ext)
    if not reader:
        raise UnsupportedFormatError(f"Formato '{ext}' não suportado")

    text = reader(path)
    logger.info(f"Documento lido com sucesso: {len(text)} caracteres totais")
    return text
