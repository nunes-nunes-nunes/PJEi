"""
response_validator.py — Validação estrutural da resposta da IA.

Verifica que a resposta é um TSV válido antes de prosseguir com
o salvamento, evitando dados corrompidos ou respostas alucinadas.
"""

import csv
import io
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Erro na validação da resposta da IA."""
    pass


class EmptyResponseError(ValidationError):
    """Resposta vazia da IA."""
    pass


class MalformedTSVError(ValidationError):
    """Resposta não é um TSV válido."""
    pass


class MissingColumnsError(ValidationError):
    """TSV com colunas faltando."""
    pass


def validate_response(tsv_text: str, min_columns: int = 2) -> dict:
    """
    Valida a resposta da IA como TSV estruturado.

    Verificações realizadas:
    1. Resposta não está vazia
    2. Tem pelo menos 2 linhas (cabeçalho + dados)
    3. É parseável como TSV
    4. Tem o número mínimo de colunas
    5. Linha de dados tem o mesmo número de colunas que o cabeçalho

    Args:
        tsv_text: Texto TSV retornado pela IA
        min_columns: Número mínimo de colunas esperado

    Returns:
        Dicionário com metadados da validação:
        {
            "valid": True,
            "header": [...],
            "rows": [...],
            "num_columns": int,
            "num_rows": int,
            "warnings": [...]
        }
    
    Raises:
        EmptyResponseError, MalformedTSVError, MissingColumnsError
    """
    warnings = []

    # 1. Verificar se não está vazio
    if not tsv_text or not tsv_text.strip():
        raise EmptyResponseError("A IA retornou uma resposta vazia")

    # 2. Verificar número de linhas
    lines = [l for l in tsv_text.strip().split("\n") if l.strip()]

    if len(lines) < 2:
        raise MalformedTSVError(
            f"Esperado pelo menos 2 linhas (cabeçalho + dados), "
            f"mas recebeu {len(lines)}"
        )

    # 3. Parsear como TSV
    try:
        reader = csv.reader(lines, delimiter="\t", quoting=csv.QUOTE_ALL)
        parsed = list(reader)
    except csv.Error as e:
        raise MalformedTSVError(f"Não foi possível parsear como TSV: {e}")

    header = parsed[0]
    data_rows = parsed[1:]

    # 4. Verificar número mínimo de colunas
    if len(header) < min_columns:
        raise MissingColumnsError(
            f"Esperado no mínimo {min_columns} colunas, "
            f"mas o cabeçalho tem {len(header)}: {header}"
        )

    # 5. Verificar consistência de colunas nas linhas de dados
    for i, row in enumerate(data_rows):
        if len(row) != len(header):
            warnings.append(
                f"Linha {i+2}: esperado {len(header)} colunas, "
                f"encontrado {len(row)}"
            )

    # 6. Verificar campos vazios
    for i, row in enumerate(data_rows):
        empty_fields = [header[j] for j, val in enumerate(row) if not val.strip()]
        if empty_fields:
            warnings.append(
                f"Linha {i+2}: campos vazios: {', '.join(empty_fields)}"
            )

    # Log dos resultados
    if warnings:
        for w in warnings:
            logger.warning(f"Validação: {w}")
    else:
        logger.info("Validação TSV: OK — todos os campos preenchidos")

    return {
        "valid": True,
        "header": header,
        "rows": data_rows,
        "num_columns": len(header),
        "num_rows": len(data_rows),
        "warnings": warnings,
    }
