"""Regras puras e testaveis usadas na reconstrucao do Power Query."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable


IDENTIFIER = re.compile(r"^[a-z_][a-z0-9_]*$")


def canonical_column_name(value: str) -> str:
    """Converte nomes do Power Query em identificadores SQL/Spark estaveis."""

    ascii_name = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    normalized = re.sub(r"[^a-z0-9]+", "_", ascii_name.lower()).strip("_")
    if normalized and normalized[0].isdigit():
        normalized = f"col_{normalized}"
    if not normalized or not IDENTIFIER.fullmatch(normalized):
        raise ValueError(f"Coluna nao pode ser normalizada: {value!r}")
    return normalized


def canonical_column_mapping(columns: Iterable[str]) -> dict[str, str]:
    """Retorna o rename completo e rejeita colisoes silenciosas."""

    mapping = {column: canonical_column_name(column) for column in columns}
    reverse: dict[str, list[str]] = {}
    for source, target in mapping.items():
        reverse.setdefault(target, []).append(source)
    collisions = {target: sources for target, sources in reverse.items() if len(sources) > 1}
    if collisions:
        raise ValueError(f"Colisoes apos normalizacao de colunas: {collisions}")
    return mapping


def family_table_prefix(family: str) -> str:
    if not IDENTIFIER.fullmatch(family):
        raise ValueError(f"Familia invalida: {family!r}")
    return f"candidate_{family}_"
