"""Descobre e materializa fatos candidatos do cliente selecionado na Bronze."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from pyspark.sql import Row
from pyspark.sql import functions as F

from .candidate_rules import (
    candidate_table,
    classify_file,
    family_rules,
    safe_identifier,
)
from .pipeline import (
    blob_service,
    ensure_schemas,
    load_yaml,
    write_lake,
    write_postgres_customer,
)
from .settings import Settings
from .spark import create_spark


@dataclass(frozen=True)
class Candidate:
    blob_path: str
    relative_path: str
    file_name: str
    family: str
    retailer: str
    bronze_table: str
    size_bytes: int
    last_modified: str | None


def join_blob_path(*parts: str) -> str:
    return "/".join(part.strip("/") for part in parts if part.strip("/"))


def discover_candidates(
    settings: Settings,
    catalog: dict[str, Any],
    selected_family: str = "all",
    max_files: int = 0,
) -> tuple[list[Candidate], list[str]]:
    facts_prefix = settings.customer_source_prefix
    prefix = join_blob_path(settings.blob_prefix, facts_prefix)
    rules = family_rules(catalog)
    if selected_family != "all" and selected_family not in rules:
        raise ValueError(
            f"Familia invalida: {selected_family}. Use uma de {sorted(rules)} ou all."
        )

    container = blob_service(settings).get_container_client(settings.container)
    candidates: list[Candidate] = []
    unclassified: list[str] = []
    for blob in container.list_blobs(name_starts_with=f"{prefix}/"):
        if not blob.name.lower().endswith(".parquet"):
            continue
        file_name = PurePosixPath(blob.name).name
        classification = classify_file(file_name, rules)
        if classification is None:
            unclassified.append(blob.name)
            continue
        family, retailer = classification
        if selected_family != "all" and family != selected_family:
            continue
        relative = blob.name[len(prefix) :].lstrip("/")
        candidates.append(
            Candidate(
                blob_path=blob.name,
                relative_path=relative,
                file_name=file_name,
                family=family,
                retailer=retailer,
                bronze_table=candidate_table(family, retailer),
                size_bytes=int(blob.size or 0),
                last_modified=(
                    blob.last_modified.isoformat() if blob.last_modified else None
                ),
            )
        )
        if max_files > 0 and len(candidates) >= max_files:
            break
    candidates.sort(key=lambda item: (item.family, item.retailer, item.file_name))
    if not candidates:
        raise RuntimeError(f"Nenhum fato candidato encontrado sob {prefix}")
    return candidates, sorted(unclassified)


def download_candidate(settings: Settings, candidate: Candidate) -> Path:
    parts = PurePosixPath(candidate.blob_path).parts
    if not parts or ".." in parts:
        raise ValueError(f"Path de Blob invalido: {candidate.blob_path!r}")
    target = settings.data_root / "raw-cache" / Path(*parts)
    target.parent.mkdir(parents=True, exist_ok=True)
    blob = blob_service(settings).get_blob_client(settings.container, candidate.blob_path)
    properties = blob.get_blob_properties()
    etag_path = target.with_suffix(target.suffix + ".etag")
    etag = str(properties.etag)
    if target.is_file() and etag_path.is_file():
        if etag_path.read_text(encoding="utf-8") == etag:
            return target
    temporary = target.with_suffix(target.suffix + ".part")
    with temporary.open("wb") as handle:
        blob.download_blob(max_concurrency=4).readinto(handle)
    temporary.replace(target)
    etag_path.write_text(etag, encoding="utf-8")
    return target


def inventory_rows(
    settings: Settings,
    candidates: list[Candidate],
    default_status: str,
    status_by_path: dict[str, str] | None = None,
) -> list[Row]:
    statuses = status_by_path or {}
    return [
        Row(
            id_customer=settings.id_customer,
            nm_customer=settings.nm_customer,
            blob_path=item.blob_path,
            relative_path=item.relative_path,
            file_name=item.file_name,
            family=item.family,
            retailer=item.retailer,
            bronze_table=item.bronze_table,
            size_bytes=item.size_bytes,
            last_modified=item.last_modified,
            status=statuses.get(item.blob_path, default_status),
        )
        for item in candidates
    ]


def write_inventory(
    spark,
    settings: Settings,
    candidates: list[Candidate],
    default_status: str,
    status_by_path: dict[str, str] | None = None,
) -> None:
    inventory = spark.createDataFrame(
        inventory_rows(settings, candidates, default_status, status_by_path)
    )
    write_postgres_customer(inventory, settings, "audit", "fact_candidate_inventory")


def run(
    family: str = "all",
    max_files: int = 0,
    inventory_only: bool = False,
    customer_selector: str | int | None = None,
) -> dict[str, Any]:
    settings = Settings.from_env(
        require_blob=True,
        customer_selector=customer_selector,
    )
    ensure_schemas(settings)
    catalog = load_yaml(settings.source_catalog_path)
    family = safe_identifier(family) if family != "all" else "all"
    spark = create_spark(settings)
    try:
        candidates, unclassified = discover_candidates(
            settings,
            catalog,
            selected_family=family,
            max_files=max_files,
        )
        write_inventory(spark, settings, candidates, "discovered")
        loaded: list[str] = []
        empty_sources: list[str] = []
        status_by_path: dict[str, str] = {}
        if not inventory_only:
            for index, candidate in enumerate(candidates, start=1):
                print(
                    f"[{index}/{len(candidates)}] {candidate.family} / "
                    f"{candidate.retailer}: {candidate.file_name}",
                    flush=True,
                )
                local_file = download_candidate(settings, candidate)
                frame = spark.read.parquet(str(local_file))
                if not frame.take(1):
                    print(
                        f"AVISO: fonte vazia registrada e ignorada: "
                        f"{candidate.blob_path}",
                        flush=True,
                    )
                    empty_sources.append(candidate.blob_path)
                    status_by_path[candidate.blob_path] = "empty_source"
                    continue
                enriched = (
                    frame.withColumn("id_customer", F.lit(settings.id_customer).cast("long"))
                    .withColumn("_customer_name", F.lit(settings.nm_customer))
                    .withColumn("_source_file", F.lit(candidate.blob_path))
                    .withColumn("_retailer", F.lit(candidate.retailer))
                    .withColumn("_fact_family", F.lit(candidate.family))
                    .withColumn("_candidate_status", F.lit("candidate"))
                    .withColumn("_ingested_at", F.current_timestamp())
                )
                write_lake(
                    enriched,
                    settings,
                    "bronze",
                    candidate.bronze_table,
                    customer_scoped=True,
                )
                loaded.append(candidate.bronze_table)
                status_by_path[candidate.blob_path] = "bronze_candidate"
            write_inventory(
                spark,
                settings,
                candidates,
                "discovered",
                status_by_path,
            )

        summary = {
            "version": "9.0",
            "id_customer": settings.id_customer,
            "nm_customer": settings.nm_customer,
            "prefix": settings.customer_source_prefix,
            "family": family,
            "status": (
                "inventory_only"
                if inventory_only
                else "passed_with_empty_sources"
                if empty_sources
                else "passed"
            ),
            "discovered": len(candidates),
            "loaded": len(loaded),
            "empty": len(empty_sources),
            "empty_files": empty_sources,
            "unclassified": len(unclassified),
            "bronze_tables": loaded,
            "gold_promoted": 0,
        }
        output = settings.output_dir / f"fact_candidate_ingestion_{settings.id_customer}.json"
        output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return summary
    finally:
        spark.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingestao Bronze de fatos candidatos")
    parser.add_argument("--family", default="all")
    parser.add_argument("--max-files", type=int, default=0)
    parser.add_argument("--inventory-only", action="store_true")
    parser.add_argument(
        "--customer",
        help="ID_CUSTOMER ou NM_CUSTOMER registrado em config/customers.yaml",
    )
    args = parser.parse_args()
    run(
        family=args.family,
        max_files=max(args.max_files, 0),
        inventory_only=args.inventory_only,
        customer_selector=args.customer,
    )


if __name__ == "__main__":
    main()
