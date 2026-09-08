"""Descobre e materializa na Bronze os Parquets usados por FATO_MERCADO."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any

from pyspark.sql import Row
from pyspark.sql import functions as F

from .pipeline import (
    blob_service,
    ensure_schemas,
    load_yaml,
    write_lake,
    write_postgres_customer,
)
from .settings import Settings
from .spark import create_spark


def bronze_table(blob_path: str, segment: str) -> str:
    digest = hashlib.sha1(blob_path.encode("utf-8")).hexdigest()[:10]
    safe_segment = "".join(character.lower() if character.isalnum() else "_" for character in segment)
    return f"candidate_mercado_{safe_segment}_{digest}"


def discover(settings: Settings, contract: dict[str, Any], max_files: int = 0) -> list[dict[str, Any]]:
    prefix = "/".join(filter(None, (settings.blob_prefix, contract["blob_prefix"]))).strip("/")
    contains = str(contract["path_contains"])
    excluded = str(contract.get("exclude_path_contains", "")).lower()
    valid = set(contract.get("allowed_segments", []))
    container = blob_service(settings).get_container_client(settings.container)
    result: list[dict[str, Any]] = []
    for blob in container.list_blobs(name_starts_with=f"{prefix}/"):
        path = blob.name
        if not path.lower().endswith(".parquet") or contains not in path:
            continue
        if excluded and excluded in path.lower():
            continue
        parts = PurePosixPath(path).parts
        try:
            market_index = parts.index("MERCADO")
            segment = parts[market_index + 1]
        except (ValueError, IndexError):
            continue
        if segment not in valid:
            continue
        result.append(
            {
                "blob_path": path,
                "segment": segment,
                "bronze_table": bronze_table(path, segment),
                "size_bytes": int(blob.size or 0),
                "last_modified": blob.last_modified.isoformat() if blob.last_modified else None,
            }
        )
        if max_files > 0 and len(result) >= max_files:
            break
    return sorted(result, key=lambda item: item["blob_path"])


def download(settings: Settings, blob_path: str) -> Path:
    parts = PurePosixPath(blob_path).parts
    if not parts or ".." in parts:
        raise ValueError(f"Path de Blob invalido: {blob_path!r}")
    target = settings.data_root / "raw-cache" / Path(*parts)
    target.parent.mkdir(parents=True, exist_ok=True)
    client = blob_service(settings).get_blob_client(settings.container, blob_path)
    properties = client.get_blob_properties()
    etag = str(properties.etag)
    etag_path = target.with_suffix(target.suffix + ".etag")
    if target.is_file() and etag_path.is_file() and etag_path.read_text(encoding="utf-8") == etag:
        return target
    temporary = target.with_suffix(target.suffix + ".part")
    with temporary.open("wb") as handle:
        client.download_blob(max_concurrency=4).readinto(handle)
    temporary.replace(target)
    etag_path.write_text(etag, encoding="utf-8")
    return target


def run(
    max_files: int = 0,
    inventory_only: bool = False,
    customer_selector: str | int | None = None,
) -> dict[str, Any]:
    settings = Settings.from_env(
        require_blob=True,
        customer_selector=customer_selector,
    )
    ensure_schemas(settings)
    contracts = load_yaml(settings.power_query_contracts_path)
    contract = contracts["market"]
    spark = create_spark(settings)
    try:
        candidates = discover(settings, contract, max_files)
        if not candidates:
            raise RuntimeError("Nenhum Parquet de mercado aderente ao Power Query foi encontrado")
        loaded: list[str] = []
        empty: list[str] = []
        rows: list[Row] = []
        for index, candidate in enumerate(candidates, start=1):
            status = "discovered"
            if not inventory_only:
                print(f"[{index}/{len(candidates)}] {candidate['segment']}: {candidate['blob_path']}", flush=True)
                local_file = download(settings, candidate["blob_path"])
                frame = spark.read.parquet(str(local_file))
                if not frame.take(1):
                    status = "empty_source"
                    empty.append(candidate["blob_path"])
                else:
                    enriched = (
                        frame.withColumn("id_customer", F.lit(settings.id_customer).cast("long"))
                        .withColumn("_customer_name", F.lit(settings.nm_customer))
                        .withColumn("SEGMENTO", F.lit(candidate["segment"]))
                        .withColumn("_source_file", F.lit(candidate["blob_path"]))
                        .withColumn("_candidate_status", F.lit("candidate"))
                        .withColumn("_ingested_at", F.current_timestamp())
                    )
                    write_lake(
                        enriched,
                        settings,
                        "bronze",
                        candidate["bronze_table"],
                        customer_scoped=True,
                    )
                    status = "bronze_candidate"
                    loaded.append(candidate["bronze_table"])
            rows.append(
                Row(
                    id_customer=settings.id_customer,
                    nm_customer=settings.nm_customer,
                    **candidate,
                    status=status,
                )
            )
        write_postgres_customer(
            spark.createDataFrame(rows),
            settings,
            "audit",
            "market_candidate_inventory",
        )
        summary = {
            "version": "9.0",
            "id_customer": settings.id_customer,
            "nm_customer": settings.nm_customer,
            "status": "inventory_only" if inventory_only else "passed_with_empty_sources" if empty else "passed",
            "discovered": len(candidates),
            "loaded": len(loaded),
            "empty": len(empty),
            "bronze_tables": loaded,
            "gold_promoted": 0,
        }
        (settings.output_dir / f"market_candidate_ingestion_{settings.id_customer}.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return summary
    finally:
        spark.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingestao Bronze dos fatos de mercado")
    parser.add_argument("--max-files", type=int, default=0)
    parser.add_argument("--inventory-only", action="store_true")
    parser.add_argument("--customer")
    args = parser.parse_args()
    run(max(args.max_files, 0), args.inventory_only, args.customer)


if __name__ == "__main__":
    main()
