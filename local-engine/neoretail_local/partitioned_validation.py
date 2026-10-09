"""Quality gate Silver para a origem diaria particionada da AMBEV.

A origem AMBEV usa uma unica Bronze (candidate_customer_daily) para derivar
varias tabelas Silver. Por isso o gate legado, que procurava uma Bronze por
familia, nao representa esse layout. Este modulo valida a fonte unica, o tenant,
os contratos minimos de cada saida e as relacoes esperadas de cardinalidade.
"""

from __future__ import annotations

import argparse
import json

from pyspark.sql import Row
from pyspark.sql import functions as F

from .pipeline import (
    ensure_schemas,
    power_query_contracts,
    read_lake,
    write_postgres_customer,
)
from .settings import Settings
from .spark import create_spark


TARGETS: dict[str, dict[str, object]] = {
    "fato_diaria": {
        "required": {"data", "id_item", "id_location", "id_customer"},
        "cardinality": "same_as_source",
    },
    "fato_semanal": {
        "required": {"id_time", "cd_week", "id_item", "id_location", "id_customer"},
        "cardinality": "reduced",
    },
    "fato_historico": {
        "required": {"mes_ano", "id_item", "id_location", "id_customer"},
        "cardinality": "reduced",
    },
    "fato_ivd_tvd": {
        "required": {
            "id_time", "id_item", "id_location", "tvd_simplificado",
            "ivd_simplificado", "id_customer",
        },
        "cardinality": "same_as_source",
    },
    "fato_nivel_atividade": {
        "required": {
            "id_item", "id_location", "tp_activity_level",
            "nm_activity_level", "id_customer",
        },
        "cardinality": "reduced",
    },
    "fato_mensal_causa_osa": {
        "required": {
            "data", "id_item", "id_location", "causa_osa", "motivo_osa",
            "id_customer",
        },
        "cardinality": "reduced",
    },
    "fato_preco": {
        "required": {
            "mes", "ano", "id_item", "id_location", "customer", "id_customer",
        },
        "cardinality": "reduced",
    },
    "etl_calc_v2": {
        "required": {
            "id_item", "id_location", "estoque_unidades", "expectativa_vendas",
            "venda_hoje_qtd", "venda_hoje_valor", "id_customer",
        },
        "cardinality": "reduced",
    },
}


def _check_row(
    settings: Settings,
    *,
    name: str,
    source_count: int,
    target_count: int,
    missing: list[str] | None = None,
    passed: bool,
    status: str | None = None,
) -> Row:
    return Row(
        id_customer=settings.id_customer,
        check_name=name,
        source_count=int(source_count),
        target_count=int(target_count),
        missing_columns=",".join(missing or []),
        status=status or ("passed" if passed else "failed"),
        passed=bool(passed),
    )


def validate(settings: Settings, spark) -> dict[str, object]:
    if settings.customer.source_layout != "partitioned_customer_daily_v1":
        raise RuntimeError(
            "partitioned_validation so pode ser usado com partitioned_customer_daily_v1"
        )

    contracts = power_query_contracts(settings)
    checks: list[Row] = []

    # Mantem os mesmos checks dimensionais do gate V9.
    for name, definition in contracts.get("dimensions", {}).items():
        source_table = str(definition["source_table"])
        target_table = str(definition["target_table"])
        source_count = read_lake(spark, settings, "bronze", source_table).count()
        target_count = read_lake(
            spark, settings, "silver", target_table, customer_scoped=True
        ).count()
        allow_empty = bool(definition.get("allow_empty", False))
        passed = source_count > 0 and (target_count > 0 or allow_empty)
        checks.append(
            _check_row(
                settings,
                name=f"dimension_{name}",
                source_count=source_count,
                target_count=target_count,
                passed=passed,
            )
        )

    source = read_lake(
        spark,
        settings,
        "bronze",
        "candidate_customer_daily",
        customer_scoped=True,
    )
    source_count = source.count()
    source_missing = sorted({"id_customer", "id_time", "id_item", "id_location"} - set(source.columns))
    source_invalid_tenant = (
        1
        if "id_customer" not in source.columns
        else source.filter(
            F.col("id_customer").cast("long") != F.lit(settings.id_customer)
        ).limit(1).count()
    )
    source_passed = source_count > 0 and not source_missing and source_invalid_tenant == 0
    checks.append(
        _check_row(
            settings,
            name="source_customer_daily",
            source_count=source_count,
            target_count=source_count,
            missing=source_missing,
            passed=source_passed,
            status="passed" if source_passed else "failed_source_contract",
        )
    )

    for target, rule in TARGETS.items():
        frame = read_lake(
            spark, settings, "silver", target, customer_scoped=True
        )
        target_count = frame.count()
        required = set(rule["required"])
        missing = sorted(required - set(frame.columns))
        invalid_tenant = (
            1
            if "id_customer" not in frame.columns
            else frame.filter(
                F.col("id_customer").cast("long") != F.lit(settings.id_customer)
            ).limit(1).count()
        )
        if rule["cardinality"] == "same_as_source":
            cardinality_ok = source_count > 0 and target_count == source_count
        else:
            cardinality_ok = source_count > 0 and 0 < target_count <= source_count
        passed = not missing and invalid_tenant == 0 and cardinality_ok
        checks.append(
            _check_row(
                settings,
                name=f"fact_{target}",
                source_count=source_count,
                target_count=target_count,
                missing=missing,
                passed=passed,
                status="passed" if passed else "failed_partitioned_contract",
            )
        )

    # ETL_CALC_V2 deve conter no maximo uma linha por item/local no snapshot atual.
    opportunities = read_lake(
        spark, settings, "silver", "etl_calc_v2", customer_scoped=True
    )
    duplicate_grain = (
        opportunities.groupBy("id_customer", "id_location", "id_item")
        .count()
        .filter(F.col("count") > 1)
        .limit(1)
        .count()
    )
    opportunity_count = opportunities.count()
    checks.append(
        _check_row(
            settings,
            name="etl_calc_v2_unique_grain",
            source_count=opportunity_count,
            target_count=opportunity_count,
            missing=[] if duplicate_grain == 0 else ["duplicate_id_location_id_item"],
            passed=duplicate_grain == 0 and opportunity_count > 0,
        )
    )

    activity = read_lake(
        spark, settings, "silver", "fato_nivel_atividade", customer_scoped=True
    )
    activity_dim = read_lake(
        spark, settings, "silver", "dim_nivel_atividade", customer_scoped=True
    )
    activity_missing = sorted(
        {"tp_activity_level", "nm_activity_level", "id"} - set(activity_dim.columns)
    )
    activity_count = activity.count()
    activity_dim_count = activity_dim.count()
    activity_passed = activity_count > 0 and activity_dim_count > 0 and not activity_missing
    checks.append(
        _check_row(
            settings,
            name="dimension_dim_nivel_atividade",
            source_count=activity_count,
            target_count=activity_dim_count,
            missing=activity_missing,
            passed=activity_passed,
        )
    )

    opportunity_contract = contracts["opportunities"]
    source_frame = read_lake(
        spark, settings, "silver", str(opportunity_contract["source_table"]), customer_scoped=True
    )
    target_frame = read_lake(
        spark, settings, "silver", str(opportunity_contract["target_table"]), customer_scoped=True
    )
    required = set(opportunity_contract.get("required_key_columns", [])) | set(
        opportunity_contract.get("required_source_columns", [])
    )
    missing = sorted(required - set(target_frame.columns))
    source_opportunity_count = source_frame.count()
    target_opportunity_count = target_frame.count()
    parity_passed = (
        source_opportunity_count > 0
        and source_opportunity_count == target_opportunity_count
        and not missing
    )
    checks.append(
        _check_row(
            settings,
            name="opportunity_structural_parity",
            source_count=source_opportunity_count,
            target_count=target_opportunity_count,
            missing=missing,
            passed=parity_passed,
        )
    )

    result = spark.createDataFrame(checks)
    write_postgres_customer(result, settings, "audit", "silver_quality_gate")
    failed = result.filter(F.col("passed") == F.lit(False)).count()
    if failed:
        failed_names = [
            row.check_name
            for row in result.filter(F.col("passed") == F.lit(False)).select("check_name").collect()
        ]
        raise RuntimeError(
            "Validacao Silver AMBEV falhou: " + ", ".join(failed_names)
            + ". Consulte audit.silver_quality_gate"
        )

    return {
        "step": "03D_silver_validation",
        "status": "passed_partitioned_customer_daily_v1",
        "checks": len(checks),
        "source_rows": source_count,
        "formula_parity": opportunity_contract.get("formula_parity"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Gate Silver da origem particionada NeoRetail")
    parser.add_argument("--customer", "--tenant")
    args = parser.parse_args()

    settings = Settings.from_env(require_blob=False, customer_selector=args.customer)
    ensure_schemas(settings)
    spark = create_spark(settings)
    try:
        result = validate(settings, spark)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
