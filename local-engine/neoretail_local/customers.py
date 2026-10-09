"""Canonical tenant identity. Authorization and automatic execution are separate."""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml


class UniqueKeyLoader(yaml.SafeLoader):
    """Reject duplicate YAML keys rather than silently keeping the last value."""


def _unique_mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise RuntimeError(f"Duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping)


def load_document(path: Path) -> dict[str, Any]:
    document = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
    if not isinstance(document, dict) or document.get("version") != "9.0":
        raise RuntimeError(f"Invalid registry version/document: {path}")
    return document


@dataclass(frozen=True)
class TenantContext:
    tenant_key: str
    id_customer: int
    nm_customer: str
    display_name: str
    gold_schema: str
    source_prefix: str | None
    source_layout: str | None
    execution_active: bool
    enabled: bool = True

    @property
    def partition(self) -> str:
        return f"id_customer={self.id_customer}"

    @property
    def source_ready(self) -> bool:
        return bool(self.source_prefix and self.source_layout)

    def require_source(self) -> "TenantContext":
        missing = [name for name in ("source_prefix", "source_layout") if not getattr(self, name)]
        if missing:
            raise RuntimeError(f"Tenant {self.tenant_key}: pending source configuration: {', '.join(missing)}")
        return self

    def require_automatic_execution(self) -> "TenantContext":
        if not self.execution_active:
            raise RuntimeError(f"Tenant {self.tenant_key} inactive for automatic execution")
        return self.require_source()


# Compatibility for existing pipeline imports; no physical schema is changed here.
Customer = TenantContext


def _customer(row: dict[str, Any]) -> TenantContext:
    if not isinstance(row, dict):
        raise RuntimeError("Invalid tenant record")
    customer_id = row.get("id_customer")
    if type(customer_id) is not int or not 0 < customer_id <= 9007199254740991:
        raise RuntimeError("id_customer must be a positive safe integer")
    key, schema = row.get("tenant_key"), row.get("gold_schema")
    for label, value in (("tenant_key", key), ("gold_schema", schema)):
        if not isinstance(value, str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,62}", value):
            raise RuntimeError(f"Invalid physical identifier: {label}={value!r}")
    name = row.get("nm_customer")
    if not isinstance(name, str) or not name.strip():
        raise RuntimeError("Missing nm_customer")
    for label in ("execution_active", "enabled"):
        if type(row.get(label, True if label == "enabled" else None)) is not bool:
            raise RuntimeError(f"{label} must be boolean")
    source = {}
    for label in ("source_prefix", "source_layout"):
        value = row.get(label)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise RuntimeError(f"Invalid {label}; use null for pending configuration")
        if value is not None and ("<" in value or ">" in value or "\\" in value or ".." in value.split("/")):
            raise RuntimeError(f"Invalid {label}")
        source[label] = value.strip().strip("/") if value is not None else None
        if value is not None and not source[label]:
            raise RuntimeError(f"Invalid {label}")
    return TenantContext(
        tenant_key=key, id_customer=customer_id, nm_customer=name.strip().upper(),
        display_name=str(row.get("display_name") or name).strip(), gold_schema=schema,
        execution_active=row["execution_active"], enabled=row.get("enabled", True), **source,
    )


def load_customer_registry(path: Path) -> tuple[dict[str, Any], list[TenantContext]]:
    document = load_document(path)
    rows = document.get("customers")
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("No tenants configured")
    customers = [_customer(row) for row in rows]
    for label in ("tenant_key", "id_customer", "nm_customer", "gold_schema"):
        values = [getattr(customer, label) for customer in customers]
        if len(values) != len(set(values)):
            raise RuntimeError(f"Duplicate {label}")
    owners = {}
    for customer in customers:
        for selector in (customer.tenant_key.upper(), customer.nm_customer):
            if selector in owners and owners[selector] != customer.id_customer:
                raise RuntimeError(f"Ambiguous tenant selector: {selector}")
            owners[selector] = customer.id_customer
    return document, customers


def resolve_tenant(path: Path, selector: str | int | None, *, require_source=False, automatic=False) -> TenantContext:
    document, customers = load_customer_registry(path)
    requested = str(selector if selector is not None else document.get("default_customer", "")).strip().upper()
    matches = [c for c in customers if requested in (str(c.id_customer), c.tenant_key.upper(), c.nm_customer)]
    if len(matches) != 1:
        raise RuntimeError(f"Unknown or ambiguous tenant: {requested!r}")
    customer = matches[0]
    if not customer.enabled:
        raise RuntimeError(f"Tenant disabled: {customer.tenant_key}")
    if automatic:
        customer.require_automatic_execution()
    elif require_source:
        customer.require_source()
    return customer


resolve_customer = resolve_tenant


def automatic_tenants(path: Path, *, require_source=True) -> list[TenantContext]:
    _, customers = load_customer_registry(path)
    active = [c for c in customers if c.enabled and c.execution_active]
    if require_source:
        for customer in active:
            customer.require_automatic_execution()
    return active


def customer_modules(path: Path, customer: TenantContext) -> tuple[str, ...]:
    """Product entitlements live outside canonical identity."""
    document = load_document(path)
    if "customers" in document:
        raise RuntimeError("Duplicate identity: use customer_access and canonical customers.yaml")
    access = document.get("customer_access", {})
    if not isinstance(access, dict):
        raise RuntimeError("Invalid customer_access")
    modules = access.get(customer.tenant_key, {}).get("modules", [])
    if not isinstance(modules, list) or any(not isinstance(value, str) for value in modules):
        raise RuntimeError("Invalid tenant modules")
    return tuple(modules)


def main():
    import os
    parser = argparse.ArgumentParser(description="Resolve tenant identity without starting Spark or publishing data")
    parser.add_argument("--config", type=Path, default=Path(os.getenv("CUSTOMERS_CONFIG_PATH", "/workspace/config/customers.yaml")))
    parser.add_argument("--tenant", "--customer", dest="selector")
    parser.add_argument("--active", action="store_true")
    parser.add_argument("--require-source", action="store_true")
    args = parser.parse_args()
    if args.active and args.selector is not None:
        parser.error("--active cannot be combined with --tenant/--customer")
    contexts = automatic_tenants(args.config, require_source=args.require_source) if args.active else resolve_tenant(args.config, args.selector, require_source=args.require_source)
    print(json.dumps([asdict(c) for c in contexts] if isinstance(contexts, list) else asdict(contexts)))


if __name__ == "__main__":
    main()
