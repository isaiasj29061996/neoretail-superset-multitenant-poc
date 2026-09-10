from __future__ import annotations

import argparse
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg2
import yaml
from azure.storage.blob import BlobServiceClient
from pyspark.sql import DataFrame, Row
from pyspark.sql import functions as F

from .settings import Settings
from .power_query import apply_fact_contract, build_activity_dimension, transform_dimensions
from .silver import normalize_frame, union_frames
from .silver_contracts import family_table_prefix
from .spark import create_spark


IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
DIMENSIONS = {
    "dim_itens": "dim_itens_raw",
    "dim_local": "dim_local_raw",
    "dim_customer": "dim_customer_raw",
    "dim_conversao": "dim_conversao_raw",
    "dim_catalogo_produtos": "dim_catalogo_produtos_raw",
    "dim_catalogo_local": "dim_local_raw",
    "dim_nivel_atividade": "candidate_fato_nivel_atividade_*",
}


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def validate_identifier(value: str) -> str:
    if not IDENTIFIER.fullmatch(value):
        raise ValueError(f"Identificador invalido: {value!r}")
    return value


def layer_path(settings: Settings, layer: str, table: str) -> Path:
    validate_identifier(layer)
    validate_identifier(table)
    return settings.data_root / "lake" / layer / table


def customer_layer_path(settings: Settings, layer: str, table: str) -> Path:
    return layer_path(settings, layer, table) / settings.customer.partition


def write_lake(
    frame: DataFrame,
    settings: Settings,
    layer: str,
    table: str,
    *,
    customer_scoped: bool = False,
) -> None:
    path = (
        customer_layer_path(settings, layer, table)
        if customer_scoped
        else layer_path(settings, layer, table)
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.write.mode("overwrite").format(settings.lake_format).save(str(path))


def read_lake(
    spark,
    settings: Settings,
    layer: str,
    table: str,
    *,
    customer_scoped: bool = False,
) -> DataFrame:
    path = (
        customer_layer_path(settings, layer, table)
        if customer_scoped
        else layer_path(settings, layer, table)
    )
    return spark.read.format(settings.lake_format).load(str(path))


def write_postgres(frame: DataFrame, settings: Settings, schema: str, table: str) -> None:
    validate_identifier(schema)
    validate_identifier(table)
    (
        frame.write.format("jdbc")
        .option("url", settings.jdbc_url)
        .option("dbtable", f"{schema}.{table}")
        .option("user", settings.analytics_user)
        .option("password", settings.analytics_password)
        .option("driver", "org.postgresql.Driver")
        .option("batchsize", "5000")
        .mode("overwrite")
        .save()
    )


def write_postgres_customer(
    frame: DataFrame,
    settings: Settings,
    schema: str,
    table: str,
) -> None:
    """Substitui atomicamente somente o ID_CUSTOMER processado."""

    validate_identifier(schema)
    validate_identifier(table)
    if "id_customer" not in frame.columns:
        raise RuntimeError(f"{schema}.{table}: id_customer ausente")
    invalid = frame.filter(F.col("id_customer") != F.lit(settings.id_customer)).limit(1).count()
    if invalid:
        raise RuntimeError(
            f"{schema}.{table}: linhas fora do cliente {settings.id_customer}"
        )
    suffix = uuid.uuid4().hex[:8]
    stage = validate_identifier(f"_stage_{table[:40]}_{suffix}")
    (
        frame.write.format("jdbc")
        .option("url", settings.jdbc_url)
        .option("dbtable", f"{schema}.{stage}")
        .option("user", settings.analytics_user)
        .option("password", settings.analytics_password)
        .option("driver", "org.postgresql.Driver")
        .option("batchsize", "5000")
        .mode("overwrite")
        .save()
    )
    quoted_schema = f'"{schema}"'
    quoted_table = f'"{table}"'
    quoted_stage = f'"{stage}"'
    index_name = validate_identifier(f"ix_{table[:45]}_id_customer")
    try:
        with psycopg2.connect(settings.psycopg_dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"CREATE TABLE IF NOT EXISTS {quoted_schema}.{quoted_table} "
                    f"(LIKE {quoted_schema}.{quoted_stage} INCLUDING ALL)"
                )
                cursor.execute(
                    f"DELETE FROM {quoted_schema}.{quoted_table} WHERE id_customer = %s",
                    (settings.id_customer,),
                )
                cursor.execute(
                    f"INSERT INTO {quoted_schema}.{quoted_table} "
                    f"SELECT * FROM {quoted_schema}.{quoted_stage}"
                )
                cursor.execute(
                    f"CREATE INDEX IF NOT EXISTS \"{index_name}\" "
                    f"ON {quoted_schema}.{quoted_table} (id_customer)"
                )
                cursor.execute(f"DROP TABLE {quoted_schema}.{quoted_stage}")
    except Exception:
        with psycopg2.connect(settings.psycopg_dsn) as cleanup:
            with cleanup.cursor() as cursor:
                cursor.execute(f"DROP TABLE IF EXISTS {quoted_schema}.{quoted_stage}")
        raise


def ensure_schemas(settings: Settings) -> None:
    settings.data_root.mkdir(parents=True, exist_ok=True)
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    for layer in ("raw-cache", "lake/bronze", "lake/silver", "lake/gold"):
        (settings.data_root / layer).mkdir(parents=True, exist_ok=True)
    with psycopg2.connect(settings.psycopg_dsn) as connection:
        with connection.cursor() as cursor:
            for schema in ("audit", "bronze", "silver", "gold"):
                cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')


def blob_service(settings: Settings) -> BlobServiceClient:
    return BlobServiceClient.from_connection_string(settings.connection_string)


def step_00_setup(settings: Settings, _spark) -> dict[str, Any]:
    ensure_schemas(settings)
    return {
        "step": "00_setup",
        "status": "passed",
        "lake_format": settings.lake_format,
        "id_customer": settings.id_customer,
        "nm_customer": settings.nm_customer,
    }


def step_01_discover_blob(settings: Settings, spark) -> dict[str, Any]:
    client = blob_service(settings).get_container_client(settings.container)
    catalog = load_yaml(settings.source_catalog_path)
    configured_prefix = settings.blob_prefix.strip().strip("/")
    facts_prefix = settings.customer_source_prefix
    targeted_facts_prefix = "/".join(
        part for part in (configured_prefix, facts_prefix) if part
    )

    scopes: list[tuple[str, str | None]] = [
        ("configured_root", configured_prefix or None)
    ]
    if targeted_facts_prefix:
        if targeted_facts_prefix == configured_prefix:
            scopes[0] = ("customer_facts", targeted_facts_prefix)
        else:
            scopes.append(("customer_facts", targeted_facts_prefix))

    inventory_by_path: dict[str, Row] = {}
    scope_counts: dict[str, int] = {}
    for scope, prefix in scopes:
        count = 0
        for blob in client.list_blobs(name_starts_with=prefix):
            if not blob.name.lower().endswith(".parquet"):
                continue
            inventory_by_path[blob.name] = Row(
                path=blob.name,
                scope=scope,
                id_customer=settings.id_customer,
                nm_customer=settings.nm_customer,
                size_bytes=int(blob.size or 0),
                last_modified=(
                    blob.last_modified.isoformat() if blob.last_modified else ""
                ),
            )
            count += 1
            if count >= settings.discovery_max_files:
                break
        scope_counts[scope] = count

    rows = [inventory_by_path[path] for path in sorted(inventory_by_path)]
    if not rows:
        raise RuntimeError("Nenhum Parquet encontrado no Blob com o prefixo configurado")
    if facts_prefix and scope_counts.get("customer_facts", 0) == 0:
        raise RuntimeError(f"Nenhum Parquet encontrado no prefixo de fatos {facts_prefix}")
    inventory = spark.createDataFrame(rows)
    write_postgres_customer(inventory, settings, "audit", "blob_inventory")
    output = settings.output_dir / "local_blob_inventory.json"
    output.write_text(
        json.dumps([row.asDict() for row in rows], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {
        "step": "01_discover_blob",
        "status": "passed",
        "files": len(rows),
        "root_files": scope_counts.get("configured_root", 0),
        "customer_facts_files": scope_counts.get("customer_facts", 0),
        "id_customer": settings.id_customer,
    }


def download_approved_source(settings: Settings, relative_path: str) -> Path:
    relative_path = relative_path.strip().lstrip("/")
    if not relative_path or ".." in Path(relative_path).parts:
        raise ValueError(f"Path de Blob invalido: {relative_path!r}")
    blob_name = "/".join(filter(None, (settings.blob_prefix, relative_path)))
    target = settings.data_root / "raw-cache" / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    blob = blob_service(settings).get_blob_client(settings.container, blob_name)
    properties = blob.get_blob_properties()
    etag_path = target.with_suffix(target.suffix + ".etag")
    etag = str(properties.etag)
    if target.is_file() and etag_path.is_file() and etag_path.read_text(encoding="utf-8") == etag:
        return target
    temp = target.with_suffix(target.suffix + ".part")
    with temp.open("wb") as handle:
        blob.download_blob(max_concurrency=4).readinto(handle)
    temp.replace(target)
    etag_path.write_text(etag, encoding="utf-8")
    return target


def step_02_bronze(settings: Settings, spark) -> dict[str, Any]:
    catalog = load_yaml(settings.source_catalog_path)
    approved = catalog.get("sources", {})
    loaded: list[str] = []
    for logical_name, source in approved.items():
        if source.get("status") != "approved_path":
            continue
        table = validate_identifier(source["bronze_table"])
        local_file = download_approved_source(settings, source["path"])
        frame = spark.read.parquet(str(local_file))
        if not frame.take(1):
            raise RuntimeError(f"{logical_name}: fonte aprovada nao retornou linhas")
        write_lake(frame, settings, "bronze", table)
        loaded.append(table)
    if not loaded:
        raise RuntimeError("Nenhuma fonte aprovada foi carregada na Bronze")
    return {"step": "02_bronze", "status": "passed", "tables": loaded}


def power_query_contracts(settings: Settings) -> dict[str, Any]:
    document = load_yaml(settings.power_query_contracts_path)
    if document.get("version") != "9.0":
        raise RuntimeError("power_query_contracts.yaml ausente ou com versao invalida")
    return document


def bronze_family_tables(settings: Settings, family: str) -> list[str]:
    prefix = family_table_prefix(family)
    bronze_root = settings.data_root / "lake" / "bronze"
    if not bronze_root.is_dir():
        return []
    return sorted(
        validate_identifier(path.name)
        for path in bronze_root.iterdir()
        if path.is_dir()
        and path.name.startswith(prefix)
        and (path / settings.customer.partition).is_dir()
    )


def step_03a_silver_dimensions(settings: Settings, spark) -> dict[str, Any]:
    contracts = power_query_contracts(settings)
    definitions = contracts.get("dimensions", {})
    source_tables = sorted(
        {validate_identifier(definition["source_table"]) for definition in definitions.values()}
    )
    raw = {
        table: read_lake(spark, settings, "bronze", table)
        for table in source_tables
    }
    transformed = transform_dimensions(raw, settings.nm_customer, settings.id_customer)
    customer_rows = transformed["dim_customer"].count()
    if customer_rows != 1:
        raise RuntimeError(
            f"DIM_CUSTOMER nao confirmou {settings.nm_customer}={settings.id_customer}"
        )
    written: list[str] = []
    for name, definition in definitions.items():
        target = validate_identifier(definition["target_table"])
        if name not in transformed:
            raise RuntimeError(f"Transformacao dimensional nao implementada: {name}")
        write_lake(
            transformed[name], settings, "silver", target, customer_scoped=True
        )
        written.append(target)
    if not written:
        raise RuntimeError("Nenhuma dimensao configurada para a Silver")
    return {"step": "03A_silver_dimensions", "status": "passed", "tables": written}


def step_03b_silver_facts(settings: Settings, spark) -> dict[str, Any]:
    contracts = power_query_contracts(settings)
    written: list[str] = []
    skipped: list[str] = []
    source_tables = 0
    for family, definition in contracts.get("fact_families", {}).items():
        tables = bronze_family_tables(settings, family)
        if not tables:
            skipped.append(family)
            continue
        frames = [
            normalize_frame(
                read_lake(
                    spark, settings, "bronze", table, customer_scoped=True
                ),
                id_customer=settings.id_customer,
                customer_name=settings.nm_customer,
                source_table=table,
                drop_exact_duplicates=False,
            )
            for table in tables
        ]
        target = validate_identifier(definition["target_table"])
        combined = union_frames(frames)
        transformed = apply_fact_contract(
            combined,
            definition,
            str(definition.get("power_query") or family),
        )
        write_lake(transformed, settings, "silver", target, customer_scoped=True)
        written.append(target)
        source_tables += len(tables)
    post_fact_written: list[str] = []
    activity = contracts.get("post_fact_dimensions", {}).get("dim_nivel_atividade")
    if activity and "fato_nivel_atividade" in written:
        target = validate_identifier(activity["target_table"])
        fact = read_lake(
            spark,
            settings,
            "silver",
            activity["source_table"],
            customer_scoped=True,
        )
        write_lake(
            build_activity_dimension(
                fact, settings.id_customer, settings.nm_customer
            ),
            settings,
            "silver",
            target,
            customer_scoped=True,
        )
        post_fact_written.append(target)
    if not written:
        raise RuntimeError("Nenhuma familia de fatos candidata encontrada na Bronze")
    return {
        "step": "03B_silver_facts",
        "status": "passed",
        "tables": written,
        "bronze_sources": source_tables,
        "skipped_families": skipped,
        "post_fact_dimensions": post_fact_written,
    }


def step_03c_opportunities(settings: Settings, spark) -> dict[str, Any]:
    contract = power_query_contracts(settings)["opportunities"]
    source = validate_identifier(contract["source_table"])
    target = validate_identifier(contract["target_table"])
    frame = read_lake(
        spark, settings, "silver", source, customer_scoped=True
    )
    required = set(contract.get("required_key_columns", [])) | set(
        contract.get("required_source_columns", [])
    )
    missing_required = sorted(required - set(frame.columns))
    if missing_required:
        raise RuntimeError(
            "ETL_CALC_V2 nao atende ao contrato minimo de oportunidades; "
            f"colunas ausentes: {missing_required}"
        )
    # O ETL_CALC_V2 ja foi selecionado, tipado e teve nulos tratados em 03B,
    # exatamente como na consulta M. Colunas DAX permanecem na camada semantica.
    write_lake(frame, settings, "silver", target, customer_scoped=True)
    readiness = spark.createDataFrame(
        [
            Row(
                id_customer=settings.id_customer,
                table=target,
                source_table=source,
                formula_parity=str(contract.get("formula_parity", "pending")),
                semantic_calculated_columns=",".join(
                    contract.get("semantic_calculated_columns", [])
                ),
                structurally_ready=not missing_required,
            )
        ]
    )
    write_postgres_customer(readiness, settings, "audit", "opportunity_readiness")
    return {
        "step": "03C_opportunities",
        "status": "passed_power_query_m",
        "table": target,
        "formula_parity": contract.get("formula_parity"),
        "semantic_calculated_columns": contract.get("semantic_calculated_columns", []),
    }


def step_03d_silver_validation(settings: Settings, spark) -> dict[str, Any]:
    contracts = power_query_contracts(settings)
    checks: list[Row] = []
    for name, definition in contracts.get("dimensions", {}).items():
        source = validate_identifier(definition["source_table"])
        target = validate_identifier(definition["target_table"])
        source_count = read_lake(spark, settings, "bronze", source).count()
        target_count = read_lake(
            spark, settings, "silver", target, customer_scoped=True
        ).count()
        # Joins internos, filtros e deduplicacoes do M podem reduzir linhas; o
        # join com a tabela de contratados tambem pode multiplicar chaves validas.
        allow_empty = bool(definition.get("allow_empty", False))
        passed = source_count > 0 and (target_count > 0 or allow_empty)
        checks.append(
            Row(
                id_customer=settings.id_customer,
                check_name=f"dimension_{name}",
                source_count=source_count,
                target_count=target_count,
                missing_columns="",
                status="passed" if passed else "failed",
                passed=passed,
            )
        )
    for family, definition in contracts.get("fact_families", {}).items():
        tables = bronze_family_tables(settings, family)
        if not tables:
            checks.append(
                Row(
                    id_customer=settings.id_customer,
                    check_name=f"fact_{family}",
                    source_count=0,
                    target_count=0,
                    missing_columns="",
                    status="skipped_no_bronze",
                    passed=True,
                )
            )
            continue
        source_count = sum(
            read_lake(
                spark, settings, "bronze", table, customer_scoped=True
            ).count()
            for table in tables
        )
        target = validate_identifier(definition["target_table"])
        target_count = read_lake(
            spark, settings, "silver", target, customer_scoped=True
        ).count()
        passed = source_count > 0 and target_count == source_count
        checks.append(
            Row(
                    id_customer=settings.id_customer,
                    check_name=f"fact_{family}",
                source_count=source_count,
                target_count=target_count,
                missing_columns="",
                status="passed" if passed else "failed",
                passed=passed,
            )
        )
    activity = contracts.get("post_fact_dimensions", {}).get("dim_nivel_atividade")
    if activity:
        fact_source = validate_identifier(activity["source_table"])
        dimension_target = validate_identifier(activity["target_table"])
        source_count = read_lake(
            spark, settings, "silver", fact_source, customer_scoped=True
        ).count()
        target_frame = read_lake(
            spark, settings, "silver", dimension_target, customer_scoped=True
        )
        missing = sorted(
            {"tp_activity_level", "nm_activity_level", "id"} - set(target_frame.columns)
        )
        target_count = target_frame.count()
        passed = source_count > 0 and target_count > 0 and not missing
        checks.append(
            Row(
                id_customer=settings.id_customer,
                check_name="dimension_dim_nivel_atividade",
                source_count=source_count,
                target_count=target_count,
                missing_columns=",".join(missing),
                status="passed" if passed else "failed",
                passed=passed,
            )
        )
    opportunity = contracts["opportunities"]
    source = validate_identifier(opportunity["source_table"])
    target = validate_identifier(opportunity["target_table"])
    source_frame = read_lake(
        spark, settings, "silver", source, customer_scoped=True
    )
    target_frame = read_lake(
        spark, settings, "silver", target, customer_scoped=True
    )
    required = set(opportunity.get("required_key_columns", [])) | set(
        opportunity.get("required_source_columns", [])
    )
    missing = sorted(required - set(target_frame.columns))
    source_count = source_frame.count()
    target_count = target_frame.count()
    passed = source_count > 0 and source_count == target_count and not missing
    checks.append(
        Row(
            id_customer=settings.id_customer,
            check_name="opportunity_structural_parity",
            source_count=source_count,
            target_count=target_count,
            missing_columns=",".join(missing),
            status="passed" if passed else "failed",
            passed=passed,
        )
    )
    result = spark.createDataFrame(checks)
    write_postgres_customer(result, settings, "audit", "silver_quality_gate")
    failed = result.filter(F.col("passed") == F.lit(False)).limit(1).count()
    if failed:
        raise RuntimeError("Validacao Silver falhou; consulte audit.silver_quality_gate")
    return {
        "step": "03D_silver_validation",
        "status": "passed",
        "checks": len(checks),
        "formula_parity": opportunity.get("formula_parity"),
    }


def step_03_silver_all(settings: Settings, spark) -> dict[str, Any]:
    results = [
        step_03a_silver_dimensions(settings, spark),
        step_03b_silver_facts(settings, spark),
        step_03c_opportunities(settings, spark),
        step_03d_silver_validation(settings, spark),
    ]
    return {"step": "03_silver", "status": "passed", "substeps": results}


def approved_facts(settings: Settings) -> list[dict[str, Any]]:
    document = load_yaml(settings.approved_facts_path)
    return [fact for fact in document.get("facts", []) if fact.get("status") == "approved"]


def step_04_approve_facts(settings: Settings, spark) -> dict[str, Any]:
    facts = approved_facts(settings)
    if not facts:
        return {"step": "04_approve_facts", "status": "blocked", "reason": "no_approved_facts"}
    loaded: list[str] = []
    required = {"logical_name", "silver_table", "grain", "tenant_column", "reviewer"}
    for fact in facts:
        missing = required - set(fact)
        if missing:
            raise RuntimeError(f"Fato aprovada sem campos: {sorted(missing)}")
        logical = validate_identifier(fact["logical_name"])
        silver_table = validate_identifier(fact["silver_table"])
        tenant_column = validate_identifier(fact["tenant_column"])
        frame = read_lake(
            spark, settings, "silver", silver_table, customer_scoped=True
        )
        if tenant_column not in frame.columns:
            raise RuntimeError(f"{logical}: coluna tenant ausente: {tenant_column}")
        if frame.limit(1).count() == 0:
            raise RuntimeError(f"{logical}: tabela Silver vazia")
        loaded.append(logical)
    return {"step": "04_approve_facts", "status": "passed", "tables": loaded}


def step_05_gold_dimensions(settings: Settings, spark) -> dict[str, Any]:
    published: list[str] = []
    for table in DIMENSIONS:
        frame = read_lake(
            spark, settings, "silver", table, customer_scoped=True
        )
        write_lake(frame, settings, "gold", table, customer_scoped=True)
        write_postgres_customer(frame, settings, "gold", table)
        published.append(table)
    return {"step": "05_gold_dimensions", "status": "passed", "tables": published}


def step_06_silver_gold_facts(settings: Settings, spark) -> dict[str, Any]:
    facts = approved_facts(settings)
    if not facts:
        return {"step": "06_silver_gold_facts", "status": "blocked", "reason": "no_approved_facts"}
    published: list[str] = []
    for fact in facts:
        logical = validate_identifier(fact["logical_name"])
        silver_table = validate_identifier(fact["silver_table"])
        tenant_column = validate_identifier(fact["tenant_column"])
        frame = read_lake(
            spark, settings, "silver", silver_table, customer_scoped=True
        )
        if tenant_column != "id_customer":
            raise RuntimeError(
                f"{logical}: tenant_column precisa ser id_customer na V9"
            )
        if "id_customer" not in frame.columns:
            raise RuntimeError(f"{logical}: id_customer ausente")
        write_lake(frame, settings, "gold", logical, customer_scoped=True)
        write_postgres_customer(frame, settings, "gold", logical)
        published.append(logical)
    return {"step": "06_silver_gold_facts", "status": "passed", "tables": published}


def step_07_metric_readiness(settings: Settings, spark) -> dict[str, Any]:
    document = load_yaml(settings.metric_contracts_path)
    required = {
        "business_definition",
        "gold_expression",
        "source_tables",
        "grain",
        "owner",
        "reviewer",
    }
    rows: list[Row] = []
    for metric, contract in document.get("metrics", {}).items():
        status = contract.get("status", "discovery")
        missing = sorted(required - set(contract)) if status == "approved" else []
        if status == "approved" and missing:
            raise RuntimeError(f"Metrica {metric} aprovada sem campos: {missing}")
        rows.append(
            Row(
                id_customer=settings.id_customer,
                metric=metric,
                status=status,
                missing_fields=",".join(missing),
            )
        )
    frame = spark.createDataFrame(rows)
    write_postgres_customer(frame, settings, "audit", "metric_readiness")
    return {"step": "07_metric_readiness", "status": "passed", "metrics": len(rows)}


def step_08_quality_gate(settings: Settings, spark) -> dict[str, Any]:
    tables = list(DIMENSIONS) + [fact["logical_name"] for fact in approved_facts(settings)]
    checks: list[Row] = []
    for table in tables:
        frame = read_lake(
            spark, settings, "gold", table, customer_scoped=True
        )
        row_count = frame.count()
        is_fact = table.startswith(("fato", "fact"))
        tenant_ready = "id_customer" in frame.columns
        allow_empty = (
            table == "dim_catalogo_produtos"
            and "mercado" not in settings.customer.modules
        )
        checks.append(
            Row(
                id_customer=settings.id_customer,
                table=table,
                row_count=row_count,
                tenant_ready=tenant_ready,
                passed=(row_count > 0 or allow_empty) and tenant_ready,
            )
        )
    result = spark.createDataFrame(checks)
    write_postgres_customer(result, settings, "audit", "gold_quality_gate")
    failed = result.filter(F.col("passed") == F.lit(False)).limit(1).count()
    if failed:
        raise RuntimeError("Quality Gate falhou; veja audit.gold_quality_gate")
    return {"step": "08_quality_gate", "status": "passed", "tables": len(checks)}


STEPS = {
    "00": step_00_setup,
    "01": step_01_discover_blob,
    "02": step_02_bronze,
    "03": step_03_silver_all,
    "03A": step_03a_silver_dimensions,
    "03B": step_03b_silver_facts,
    "03C": step_03c_opportunities,
    "03D": step_03d_silver_validation,
    "04": step_04_approve_facts,
    "05": step_05_gold_dimensions,
    "06": step_06_silver_gold_facts,
    "07": step_07_metric_readiness,
    "08": step_08_quality_gate,
}

PIPELINE_STEPS = [
    ("00", step_00_setup),
    ("01", step_01_discover_blob),
    ("02", step_02_bronze),
    ("03", step_03_silver_all),
    ("04", step_04_approve_facts),
    ("05", step_05_gold_dimensions),
    ("06", step_06_silver_gold_facts),
    ("07", step_07_metric_readiness),
    ("08", step_08_quality_gate),
]


def run_step(step: str, customer_selector: str | int | None = None) -> dict[str, Any]:
    if step not in STEPS:
        raise ValueError(f"Step invalido: {step}")
    settings = Settings.from_env(
        require_blob=step in {"01", "02"},
        customer_selector=customer_selector,
    )
    ensure_schemas(settings)
    spark = create_spark(settings)
    try:
        result = STEPS[step](settings, spark)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return result
    finally:
        spark.stop()


def run_pipeline(customer_selector: str | int | None = None) -> list[dict[str, Any]]:
    settings = Settings.from_env(
        require_blob=True,
        customer_selector=customer_selector,
    )
    ensure_schemas(settings)
    spark = create_spark(settings)
    results: list[dict[str, Any]] = []
    started = datetime.now(timezone.utc).isoformat()
    try:
        for step, function in PIPELINE_STEPS:
            print(f"[{step}/08] {function.__name__}", flush=True)
            results.append(function(settings, spark))
        summary = {
            "version": "9.0",
            "id_customer": settings.id_customer,
            "nm_customer": settings.nm_customer,
            "started_at": started,
            "steps": results,
        }
        (settings.output_dir / "local_pipeline_summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return results
    finally:
        spark.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline NeoRetail V9 multitenant")
    parser.add_argument("--step", choices=["all", *STEPS], default="all")
    parser.add_argument(
        "--customer",
        help="ID_CUSTOMER ou NM_CUSTOMER registrado em config/customers.yaml",
    )
    args = parser.parse_args()
    if args.step == "all":
        run_pipeline(args.customer)
    else:
        run_step(args.step, args.customer)


if __name__ == "__main__":
    main()
