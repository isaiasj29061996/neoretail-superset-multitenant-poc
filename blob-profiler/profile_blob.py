"""Inventário Blob First: lista Parquets e lê metadata/schema sem depender de PBIX."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
import yaml
import certifi
from adlfs import AzureBlobFileSystem
from azure.storage.blob import BlobServiceClient


def required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} não configurada. Preencha o .env sem versioná-lo.")
    return value


def configure_company_ca() -> None:
    extra_path = Path(os.getenv("COMPANY_CA_BUNDLE", "/certs/company-root-ca.crt"))
    if not extra_path.is_file():
        return
    combined = Path("/tmp/neoretail-ca-bundle.crt")
    combined.write_bytes(Path(certifi.where()).read_bytes() + b"\n" + extra_path.read_bytes())
    os.environ["REQUESTS_CA_BUNDLE"] = str(combined)
    os.environ["SSL_CERT_FILE"] = str(combined)


def env_int(name: str, default: int, minimum: int = 1) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} precisa ser um inteiro; recebido: {raw!r}") from exc
    return max(value, minimum)


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name, str(default)).strip().lower()
    return value in {"1", "true", "yes", "sim"}


def json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, bytes):
        return f"<bytes:{len(value)}>"
    if isinstance(value, list):
        return [json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): json_value(item) for key, item in value.items()}
    return str(value)


def classify(path: str) -> str:
    upper = path.upper()
    if "/DIMENSAO/" in f"/{upper}" or "DIMENSAO_" in upper or "CATALOGO_" in upper:
        return "dimension_candidate"
    if "ETL_CALC_" in upper:
        return "fact_candidate_unmapped"
    if any(token in upper for token in ("FATO", "FATOS", "VENDA", "ESTOQUE", "RUPTURA", "OSA")):
        return "fact_candidate_unmapped"
    return "unclassified"


def fingerprint(columns: list[dict[str, Any]]) -> str:
    payload = json.dumps(columns, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def write_json(path: Path, value: Any) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def write_yaml(path: Path, value: Any) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(yaml.safe_dump(value, allow_unicode=True, sort_keys=False), encoding="utf-8")
    temp.replace(path)


def profile_file(
    filesystem: AzureBlobFileSystem,
    container: str,
    name: str,
    sample_rows: int,
    include_samples: bool,
) -> dict[str, Any]:
    remote_path = f"{container}/{name}"
    with filesystem.open(remote_path, "rb") as handle:
        parquet = pq.ParquetFile(handle)
        arrow_schema = parquet.schema_arrow
        columns = [
            {"name": field.name, "type": str(field.type), "nullable": field.nullable}
            for field in arrow_schema
        ]
        result: dict[str, Any] = {
            "path": name,
            "status": "profiled",
            "row_count": parquet.metadata.num_rows,
            "row_groups": parquet.metadata.num_row_groups,
            "columns": columns,
            "schema_fingerprint": fingerprint(columns),
        }
        if parquet.metadata.num_row_groups and sample_rows:
            sample = parquet.read_row_group(0).slice(0, sample_rows)
            result["sample_profile"] = {
                "rows_read": sample.num_rows,
                "columns": [
                    {
                        "name": name0,
                        "null_count": sample.column(name0).null_count,
                        "distinct_count": len(set(map(str, sample.column(name0).to_pylist()))),
                    }
                    for name0 in sample.column_names
                ],
            }
            if include_samples:
                result["sample_rows"] = [json_value(row) for row in sample.slice(0, 20).to_pylist()]
        return result


def main() -> None:
    configure_company_ca()
    connection_string = required("AZURE_STORAGE_CONNECTION_STRING")
    container = os.getenv("AZURE_STORAGE_CONTAINER", "neoretail").strip() or "neoretail"
    prefix = os.getenv("AZURE_BLOB_PREFIX", "").strip().lstrip("/")
    max_files = env_int("BLOB_PROFILE_MAX_FILES", 250)
    sample_rows = env_int("BLOB_PROFILE_SAMPLE_ROWS", 1000, minimum=0)
    include_samples = env_bool("BLOB_PROFILE_INCLUDE_SAMPLES", False)
    output = Path(os.getenv("OUTPUT_DIR", "/generated"))
    output.mkdir(parents=True, exist_ok=True)

    service = BlobServiceClient.from_connection_string(connection_string)
    container_client = service.get_container_client(container)
    blobs = [
        blob
        for blob in container_client.list_blobs(name_starts_with=prefix or None)
        if blob.name.lower().endswith(".parquet")
    ]
    blobs.sort(key=lambda blob: blob.name)

    inventory_path = output / "blob_inventory.csv"
    with inventory_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["path", "size_bytes", "last_modified", "classification", "profile_selected"],
        )
        writer.writeheader()
        for index, blob in enumerate(blobs):
            writer.writerow(
                {
                    "path": blob.name,
                    "size_bytes": blob.size,
                    "last_modified": blob.last_modified.isoformat() if blob.last_modified else "",
                    "classification": classify(blob.name),
                    "profile_selected": index < max_files,
                }
            )

    filesystem = AzureBlobFileSystem(connection_string=connection_string)
    profiles: list[dict[str, Any]] = []
    for index, blob in enumerate(blobs[:max_files], start=1):
        print(f"[{index}/{min(len(blobs), max_files)}] {blob.name}", flush=True)
        try:
            profile = profile_file(filesystem, container, blob.name, sample_rows, include_samples)
        except Exception as exc:  # cada arquivo falha isoladamente e permanece no inventário
            profile = {"path": blob.name, "status": "profile_error", "error": str(exc)[:800]}
        profile["classification"] = classify(blob.name)
        profiles.append(profile)

    write_json(
        output / "blob_schemas.json",
        {
            "version": "8.1",
            "source": "azure_blob",
            "container": container,
            "prefix": prefix,
            "total_parquet_files": len(blobs),
            "profiled_or_attempted": len(profiles),
            "sample_values_included": include_samples,
            "files": profiles,
        },
    )

    candidates = [
        {
            "logical_name": Path(profile["path"]).stem.lower(),
            "path": profile["path"],
            "classification": profile["classification"],
            "status": "discovery",
            "schema_fingerprint": profile.get("schema_fingerprint"),
        }
        for profile in profiles
    ]
    write_yaml(
        output / "source_candidates.yaml",
        {
            "version": "8.1",
            "policy": "Candidato não é tabela aprovada. Revisão humana é obrigatória.",
            "sources": candidates,
        },
    )
    summary = {
        "total_parquet_files": len(blobs),
        "profiled": sum(item.get("status") == "profiled" for item in profiles),
        "errors": sum(item.get("status") == "profile_error" for item in profiles),
        "dimensions_candidates": sum(item["classification"] == "dimension_candidate" for item in profiles),
        "fact_candidates_unmapped": sum(item["classification"] == "fact_candidate_unmapped" for item in profiles),
        "output": str(output),
    }
    write_json(output / "blob_profile_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
