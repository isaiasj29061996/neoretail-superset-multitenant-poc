"""Escrita PostgreSQL tolerante a reordenacao de colunas e tipos compativeis.

O Spark/JDBC cria uma tabela de staging com o schema atual do DataFrame. Tabelas
Gold persistentes podem ter sido criadas por uma versao anterior com a mesma
lista de colunas em outra ordem ou com representacoes numericas equivalentes.
INSERT ... SELECT * e posicional e pode, nesse caso, deslocar valores entre
colunas. Este modulo promove o staging por nome de coluna, suporta evolucao
aditiva de schema e faz CAST explicito apenas entre tipos compativeis.
"""

from __future__ import annotations

import re
import uuid
import json

import psycopg2
from psycopg2 import sql
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from .pipeline import validate_identifier
from .settings import Settings
from .customers import resolve_tenant


def publication_schema(settings: Settings, requested: str) -> str:
    context = resolve_tenant(settings.customers_config_path, settings.id_customer, require_source=True)
    if context != settings.tenant_context:
        raise RuntimeError("Publication context differs from canonical registry")
    if requested == "audit":
        return requested
    if requested not in ("gold", context.gold_schema):
        raise RuntimeError("Publication schema must come from canonical TenantContext")
    return context.gold_schema


_NUMERIC_TYPES = {
    "smallint",
    "integer",
    "bigint",
    "real",
    "double precision",
}
_TEXT_PREFIXES = (
    "text",
    "character varying",
    "character",
)


def _columns_with_types(cursor, schema: str, table: str) -> list[tuple[str, str]]:
    cursor.execute(
        """
        SELECT
            a.attname,
            pg_catalog.format_type(a.atttypid, a.atttypmod)
        FROM pg_catalog.pg_attribute a
        JOIN pg_catalog.pg_class c ON c.oid = a.attrelid
        JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = %s
          AND c.relname = %s
          AND a.attnum > 0
          AND NOT a.attisdropped
        ORDER BY a.attnum
        """,
        (schema, table),
    )
    return [(str(name), str(pg_type)) for name, pg_type in cursor.fetchall()]


def _type_family(pg_type: str) -> str:
    normalized = re.sub(r"\s+", " ", pg_type.strip().lower())
    if normalized in _NUMERIC_TYPES or normalized.startswith("numeric(") or normalized == "numeric":
        return "numeric"
    if normalized.startswith(_TEXT_PREFIXES):
        return "text"
    return normalized


def _types_compatible(target_type: str, stage_type: str) -> bool:
    if target_type == stage_type:
        return True
    target_family = _type_family(target_type)
    stage_family = _type_family(stage_type)
    return target_family == stage_family and target_family in {"numeric", "text"}


def _select_expression(name: str, target_type: str, stage_type: str):
    """Retorna expressao SQL segura para promover uma coluna do staging.

    Tipos identicos sao lidos diretamente. Familias numericas/textuais
    compativeis recebem CAST explicito para o tipo fisico da tabela Gold.
    """

    identifier = sql.Identifier(name)
    if target_type == stage_type:
        return identifier
    if not _types_compatible(target_type, stage_type):
        raise RuntimeError(
            f"{name}: target={target_type} stage={stage_type}"
        )
    return sql.SQL("CAST({} AS {})").format(identifier, sql.SQL(target_type))


def write_postgres_customer_named(
    frame: DataFrame,
    settings: Settings,
    schema: str,
    table: str,
) -> None:
    """Substitui um tenant alinhando staging e destino por nome de coluna."""

    schema = validate_identifier(publication_schema(settings, schema))
    table = validate_identifier(table)
    if "id_customer" not in frame.columns:
        raise RuntimeError(f"{schema}.{table}: id_customer ausente")

    invalid = (
        frame.filter(
            F.col("id_customer").cast("long").isNull()
            | (F.col("id_customer") != F.lit(settings.id_customer))
        )
        .limit(1)
        .count()
    )
    if invalid:
        raise RuntimeError(
            f"{schema}.{table}: linhas fora do cliente {settings.id_customer}"
        )

    suffix = uuid.uuid4().hex[:8]
    stage = validate_identifier(f"_stage_{table[:40]}_{suffix}")
    try:
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
        with psycopg2.connect(settings.psycopg_dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL("CREATE TABLE IF NOT EXISTS {}.{} (LIKE {}.{} INCLUDING ALL)").format(
                        sql.Identifier(schema),
                        sql.Identifier(table),
                        sql.Identifier(schema),
                        sql.Identifier(stage),
                    )
                )

                stage_columns = _columns_with_types(cursor, schema, stage)
                target_columns = _columns_with_types(cursor, schema, table)
                target_types = dict(target_columns)

                if not stage_columns:
                    raise RuntimeError(f"{schema}.{stage}: staging sem colunas")

                # Evolucao aditiva: novas colunas do DataFrame sao adicionadas ao
                # destino usando exatamente o tipo PostgreSQL criado pelo JDBC.
                for name, pg_type in stage_columns:
                    if name in target_types:
                        continue
                    cursor.execute(
                        sql.SQL("ALTER TABLE {}.{} ADD COLUMN {} {}").format(
                            sql.Identifier(schema),
                            sql.Identifier(table),
                            sql.Identifier(name),
                            sql.SQL(pg_type),
                        )
                    )
                    target_types[name] = pg_type

                incompatible = [
                    f"{name}: target={target_types[name]} stage={stage_type}"
                    for name, stage_type in stage_columns
                    if name in target_types
                    and not _types_compatible(target_types[name], stage_type)
                ]
                if incompatible:
                    raise RuntimeError(
                        f"{schema}.{table}: tipos incompativeis entre Gold e staging: "
                        + "; ".join(incompatible)
                    )

                if schema != "audit":
                    cursor.execute(
                        sql.SQL("ALTER TABLE {}.{} ALTER COLUMN id_customer SET NOT NULL").format(
                            sql.Identifier(schema), sql.Identifier(table)
                        )
                    )
                    constraint = validate_identifier(f"ck_{table[:40]}_tenant")
                    cursor.execute(
                        "SELECT 1 FROM pg_constraint WHERE conrelid = %s::regclass AND conname = %s",
                        (f'"{schema}"."{table}"', constraint),
                    )
                    if not cursor.fetchone():
                        cursor.execute(
                            sql.SQL("ALTER TABLE {}.{} ADD CONSTRAINT {} CHECK (id_customer = %s)").format(
                                sql.Identifier(schema), sql.Identifier(table), sql.Identifier(constraint)
                            ),
                            (settings.id_customer,),
                        )

                ordered_names = [name for name, _ in stage_columns]
                columns_sql = sql.SQL(", ").join(
                    sql.Identifier(name) for name in ordered_names
                )
                select_sql = sql.SQL(", ").join(
                    _select_expression(name, target_types[name], stage_type)
                    for name, stage_type in stage_columns
                )

                cursor.execute(
                    sql.SQL("DELETE FROM {}.{} WHERE id_customer = %s").format(
                        sql.Identifier(schema), sql.Identifier(table)
                    ),
                    (settings.id_customer,),
                )
                cursor.execute(
                    sql.SQL("INSERT INTO {}.{} ({}) SELECT {} FROM {}.{}").format(
                        sql.Identifier(schema),
                        sql.Identifier(table),
                        columns_sql,
                        select_sql,
                        sql.Identifier(schema),
                        sql.Identifier(stage),
                    )
                )

                index_name = validate_identifier(f"ix_{table[:45]}_id_customer")
                cursor.execute(
                    sql.SQL("CREATE INDEX IF NOT EXISTS {} ON {}.{} (id_customer)").format(
                        sql.Identifier(index_name),
                        sql.Identifier(schema),
                        sql.Identifier(table),
                    )
                )
                cursor.execute(
                    sql.SQL("DROP TABLE {}.{}").format(
                        sql.Identifier(schema), sql.Identifier(stage)
                    )
                )
    except Exception:
        with psycopg2.connect(settings.psycopg_dsn) as cleanup:
            with cleanup.cursor() as cursor:
                cursor.execute(
                    sql.SQL("DROP TABLE IF EXISTS {}.{}").format(
                        sql.Identifier(schema), sql.Identifier(stage)
                    )
                )
        raise
    print(json.dumps({"publication": "committed", "tenant_key": settings.tenant_context.tenant_key,
                      "id_customer": settings.id_customer, "schema": schema, "table": table}))
