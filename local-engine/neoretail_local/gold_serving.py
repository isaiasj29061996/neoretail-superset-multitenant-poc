"""Publicacao Gold otimizada para serving local da POC.

A camada Gold no lake preserva os fatos completos aprovados. Para a origem
particionada da AMBEV, o PostgreSQL recebe apenas as tabelas usadas pelos
marts/dashboards e janelas temporais adequadas ao teste local. Isso evita
replicar centenas de milhoes de linhas que nao participam do serving.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import timedelta

import psycopg2
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from .pipeline import (
    approved_facts,
    ensure_schemas,
    read_lake,
    validate_identifier,
    write_lake,
)
from .postgres_serving import write_postgres_customer_named
from .settings import Settings
from .spark import create_spark


AMBEV_LAKE_ONLY = {
    "fato_diaria",
    "fato_nivel_atividade",
    "fato_preco",
}

# A fato diaria completa continua somente no lake. Para a tela de exportacao,
# publicamos no PostgreSQL apenas uma janela recente e somente as colunas
# necessarias ao grid/export CSV.
AMBEV_EXPORT_DAILY_SOURCE = "nr_export_daily_source"
AMBEV_EXPORT_DAILY_COLUMNS = [
    "data",
    "id_customer",
    "id_location",
    "id_item",
    "nivel_atividade",
    "status_item_geral",
    "volume_unidades",
    "faturamento",
    "estoque_unidades",
    "estoque_transito",
    "qtd_perda_osa",
    "qtd_problemas_osa",
    "qtd_item_ativo_osa",
    "preco_medio_ref",
    "rup",
    "est_virtual",
]
AMBEV_EXPORT_DAILY_WINDOW = (
    "data",
    "LOCAL_SERVING_EXPORT_DAILY_DAYS",
    62,
)

# logical_name -> (date column, environment variable, default days)
AMBEV_SERVING_WINDOWS = {
    "fato_ivd_tvd": ("id_time", "LOCAL_SERVING_TVD_DAYS", 180),
    "fato_semanal": ("id_time", "LOCAL_SERVING_WEEKLY_DAYS", 730),
    "fato_historico": ("mes_ano", "LOCAL_SERVING_MONTHLY_DAYS", 1095),
    "fato_mensal_causa_osa": ("data", "LOCAL_SERVING_OSA_DAYS", 1095),
}


def _env_days(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} precisa ser inteiro") from exc
    return max(value, 0)


def apply_serving_window(
    frame: DataFrame,
    date_column: str,
    days: int,
) -> tuple[DataFrame, str | None, str | None]:
    """Recorta o DataFrame em relacao a sua propria data maxima.

    days=0 desabilita o recorte e publica o historico completo.
    Retorna frame, data maxima e cutoff para auditoria no log.
    """

    if days <= 0:
        return frame, None, None
    if date_column not in frame.columns:
        raise RuntimeError(f"Coluna temporal ausente no serving: {date_column}")

    max_date = frame.select(
        F.max(F.to_date(F.col(date_column))).alias("max_date")
    ).first().max_date
    if max_date is None:
        raise RuntimeError(f"Nao foi possivel determinar max({date_column})")

    cutoff = max_date - timedelta(days=days - 1)
    filtered = frame.filter(F.to_date(F.col(date_column)) >= F.lit(cutoff))
    return filtered, str(max_date), str(cutoff)


def purge_postgres_customer(settings: Settings, table: str) -> None:
    """Remove eventual carga antiga da AMBEV de uma tabela lake-only."""

    table = validate_identifier(table)
    schema = settings.gold_schema
    qualified = f"{schema}.{table}"
    with psycopg2.connect(settings.psycopg_dsn) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT to_regclass(%s)", (qualified,))
            exists = cursor.fetchone()[0]
            if exists:
                cursor.execute(
                    f'DELETE FROM "{schema}"."{table}" WHERE id_customer = %s',
                    (settings.id_customer,),
                )


def _publish_daily_export_source(
    frame: DataFrame,
    settings: Settings,
) -> dict[str, object]:
    date_column, env_name, default_days = AMBEV_EXPORT_DAILY_WINDOW
    days = _env_days(env_name, default_days)
    serving_frame, max_date, cutoff = apply_serving_window(
        frame,
        date_column,
        days,
    )
    missing = [
        column for column in AMBEV_EXPORT_DAILY_COLUMNS
        if column not in serving_frame.columns
    ]
    if missing:
        raise RuntimeError(
            f"fato_diaria: colunas ausentes para exportacao: {missing}"
        )
    serving_frame = serving_frame.select(*AMBEV_EXPORT_DAILY_COLUMNS)
    write_postgres_customer_named(
        serving_frame,
        settings,
        "gold",
        AMBEV_EXPORT_DAILY_SOURCE,
    )
    return {
        "date_column": date_column,
        "days": days,
        "max_date": max_date,
        "cutoff": cutoff,
        "columns": AMBEV_EXPORT_DAILY_COLUMNS,
    }


def publish_daily_export_only(settings: Settings, spark) -> dict[str, object]:
    """Atualiza somente o source PostgreSQL da exportacao diaria.

    Usa o Gold lake completo ja publicado pelo pipeline, sem republicar as
    demais familias. E o caminho rapido para atualizar a aba Exportacao.
    """

    frame = read_lake(
        spark,
        settings,
        "gold",
        "fato_diaria",
        customer_scoped=True,
    )
    if "id_customer" not in frame.columns:
        raise RuntimeError("fato_diaria Gold: id_customer ausente")
    invalid = frame.filter(
        F.col("id_customer").cast("long").isNull()
        | (F.col("id_customer") != F.lit(settings.id_customer))
    ).limit(1).count()
    if invalid:
        raise RuntimeError("fato_diaria Gold contem linhas de outro tenant")

    window = _publish_daily_export_source(frame, settings)
    return {
        "step": "export_daily_serving",
        "status": "passed",
        "postgres_table": AMBEV_EXPORT_DAILY_SOURCE,
        "serving_window": window,
    }


def publish(settings: Settings, spark) -> dict[str, object]:
    facts = approved_facts(settings)
    if not facts:
        return {
            "step": "06_silver_gold_facts",
            "status": "blocked",
            "reason": "no_approved_facts",
        }

    ambev_local_serving = (
        settings.customer.source_layout == "partitioned_customer_daily_v1"
    )
    published_lake: list[str] = []
    published_postgres: list[str] = []
    lake_only: list[str] = []
    windows: dict[str, dict[str, object]] = {}

    for fact in facts:
        logical = validate_identifier(str(fact["logical_name"]))
        silver_table = validate_identifier(str(fact["silver_table"]))
        tenant_column = validate_identifier(str(fact["tenant_column"]))

        frame = read_lake(
            spark,
            settings,
            "silver",
            silver_table,
            customer_scoped=True,
        )
        if tenant_column != "id_customer":
            raise RuntimeError(
                f"{logical}: tenant_column precisa ser id_customer na V9"
            )
        if "id_customer" not in frame.columns:
            raise RuntimeError(f"{logical}: id_customer ausente")
        invalid = frame.filter(
            F.col("id_customer").cast("long").isNull()
            | (F.col("id_customer") != F.lit(settings.id_customer))
        ).limit(1).count()
        if invalid:
            raise RuntimeError(f"{logical}: linhas fora do tenant selecionado")

        # Gold lake permanece completo e e a referencia validada do fato.
        write_lake(
            frame,
            settings,
            "gold",
            logical,
            customer_scoped=True,
        )
        published_lake.append(logical)

        if ambev_local_serving and logical == "fato_diaria":
            # Nao replica a fato diaria completa no PostgreSQL. Publica apenas
            # a janela/projecao dedicada ao dashboard de exportacao diaria.
            purge_postgres_customer(settings, logical)
            windows[AMBEV_EXPORT_DAILY_SOURCE] = _publish_daily_export_source(
                frame,
                settings,
            )
            published_postgres.append(AMBEV_EXPORT_DAILY_SOURCE)
            lake_only.append(logical)
            continue

        if ambev_local_serving and logical in AMBEV_LAKE_ONLY:
            purge_postgres_customer(settings, logical)
            lake_only.append(logical)
            continue

        serving_frame = frame
        if ambev_local_serving and logical in AMBEV_SERVING_WINDOWS:
            date_column, env_name, default_days = AMBEV_SERVING_WINDOWS[logical]
            days = _env_days(env_name, default_days)
            serving_frame, max_date, cutoff = apply_serving_window(
                frame,
                date_column,
                days,
            )
            windows[logical] = {
                "date_column": date_column,
                "days": days,
                "max_date": max_date,
                "cutoff": cutoff,
            }

        write_postgres_customer_named(
            serving_frame,
            settings,
            "gold",
            logical,
        )
        published_postgres.append(logical)

    return {
        "step": "06_silver_gold_facts",
        "status": (
            "passed_local_serving_window"
            if ambev_local_serving
            else "passed"
        ),
        "gold_lake_tables": published_lake,
        "postgres_tables": published_postgres,
        "lake_only_tables": lake_only,
        "serving_windows": windows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Publica Gold e serving PostgreSQL do NeoRetail"
    )
    parser.add_argument("--customer", "--tenant")
    parser.add_argument(
        "--export-daily-only",
        action="store_true",
        help="Publica somente o source PostgreSQL da exportacao diaria.",
    )
    args = parser.parse_args()

    settings = Settings.from_env(
        require_blob=False,
        customer_selector=args.customer,
    )
    ensure_schemas(settings)
    spark = create_spark(settings)
    try:
        result = (
            publish_daily_export_only(settings, spark)
            if args.export_daily_only
            else publish(settings, spark)
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
