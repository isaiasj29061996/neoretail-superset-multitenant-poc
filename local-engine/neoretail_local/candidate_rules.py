"""Regras puras para classificar os Parquets candidatos de cada cliente."""

from __future__ import annotations

import re
from typing import Any


def safe_identifier(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    if not normalized or not re.fullmatch(r"[a-z_][a-z0-9_]*", normalized):
        raise ValueError(f"Identificador candidato invalido: {value!r}")
    return normalized


def family_rules(catalog: dict[str, Any]) -> dict[str, re.Pattern[str]]:
    configured = catalog.get("discovery", {}).get("families", {})
    if not configured:
        raise RuntimeError("Nenhuma familia candidata configurada em source_catalog.yaml")
    return {
        safe_identifier(name): re.compile(str(definition["regex"]))
        for name, definition in configured.items()
    }


def classify_file(
    file_name: str,
    rules: dict[str, re.Pattern[str]],
) -> tuple[str, str] | None:
    matches: list[tuple[str, str]] = []
    for family, pattern in rules.items():
        match = pattern.fullmatch(file_name)
        if match:
            retailer = safe_identifier(match.group("retailer"))
            matches.append((family, retailer))
    if len(matches) > 1:
        raise RuntimeError(f"Arquivo classificado em mais de uma familia: {file_name}")
    return matches[0] if matches else None


def candidate_table(family: str, retailer: str) -> str:
    table = f"candidate_{safe_identifier(family)}_{safe_identifier(retailer)}"
    if len(table) > 63:
        raise ValueError(f"Nome de tabela Bronze excede 63 caracteres: {table}")
    return table
