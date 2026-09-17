"""Escrita PostgreSQL tolerante a reordenacao de colunas.

O Spark/JDBC cria uma tabela de staging com o schema atual do DataFrame. Tabelas
Gold persistentes podem ter sido criadas por uma versao anterior com a mesma
lista de colunas em outra ordem. INSERT ... SELECT * e posicional e pode, nesse
caso, tentar inserir texto em uma coluna numerica. Este modulo promove o staging
por nome de coluna e suporta evolucao aditiva de schema.
"""

from __future__ import annotations

import uuid

import psycopg2
from psycopg2 import sql
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from .pipeline import validate_identifier
from .settings import Settings


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


def write_postgres_customer_named(
    frame: DataFrame,
    settings: Settings,
    schema: str,
    table: str,
) -> None:
    """Substitui um tenant alinhando staging e destino por nome de coluna."""

    schema = validate_identifier(schema)
    table = validate_identifier(table)
    if "id_customer" not in frame.columns:
        raise RuntimeError(f"{schema}.{table}: id_customer ausente")

    invalid = (
        frame.filter(
            F.col("id_customer").cast("long") != F.lit(settings.id_customer)
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

    try:
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
                stage_types = dict(stage_columns)
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
                    if name in target_types and target_types[name] != stage_type
                ]
                if incompatible:
                    raise RuntimeError(
                        f"{schema}.{table}: tipos incompativeis entre Gold e staging: "
                        + "; ".join(incompatible)
                    )

                ordered_names = [name for name, _ in stage_columns]
                columns_sql = sql.SQL(", ").join(
                    sql.Identifier(name) for name in ordered_names
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
                        columns_sql,
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
