"""Cadastro e resolucao da identidade multi-industria da V9."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Customer:
    id_customer: int
    nm_customer: str
    display_name: str
    source_prefix: str
    modules: tuple[str, ...]
    enabled: bool

    @property
    def partition(self) -> str:
        return f"id_customer={self.id_customer}"


def _customer(row: dict[str, Any]) -> Customer:
    try:
        customer_id = int(row["id_customer"])
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("customers.yaml contem id_customer invalido") from exc
    if customer_id <= 0:
        raise RuntimeError("id_customer precisa ser positivo")
    name = str(row.get("nm_customer", "")).strip().upper()
    prefix = str(row.get("source_prefix", "")).strip().strip("/")
    if not name or not prefix:
        raise RuntimeError(f"Cliente {customer_id} sem nm_customer ou source_prefix")
    return Customer(
        id_customer=customer_id,
        nm_customer=name,
        display_name=str(row.get("display_name") or name).strip(),
        source_prefix=prefix,
        modules=tuple(str(value) for value in row.get("modules", [])),
        enabled=bool(row.get("enabled", True)),
    )


def load_customer_registry(path: Path) -> tuple[dict[str, Any], list[Customer]]:
    document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if document.get("version") != "9.0":
        raise RuntimeError("customers.yaml ausente ou com versao diferente de 9.0")
    customers = [_customer(row) for row in document.get("customers", [])]
    if not customers:
        raise RuntimeError("Nenhum cliente configurado em customers.yaml")
    ids = [customer.id_customer for customer in customers]
    names = [customer.nm_customer for customer in customers]
    if len(ids) != len(set(ids)):
        raise RuntimeError("customers.yaml contem id_customer duplicado")
    if len(names) != len(set(names)):
        raise RuntimeError("customers.yaml contem nm_customer duplicado")
    return document, customers


def resolve_customer(path: Path, selector: str | int | None) -> Customer:
    document, customers = load_customer_registry(path)
    requested = str(
        selector if selector is not None else document.get("default_customer", "")
    ).strip()
    if not requested:
        raise RuntimeError("Informe --customer ou default_customer em customers.yaml")
    normalized = requested.upper()
    matches = [
        customer
        for customer in customers
        if str(customer.id_customer) == requested or customer.nm_customer == normalized
    ]
    if len(matches) != 1:
        raise RuntimeError(f"Cliente nao encontrado ou ambiguo: {requested!r}")
    customer = matches[0]
    if not customer.enabled:
        raise RuntimeError(f"Cliente desabilitado: {customer.nm_customer}")
    return customer

