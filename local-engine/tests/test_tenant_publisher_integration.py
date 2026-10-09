"""Real JDBC/PostgreSQL probe, opt-in against a disposable test database only."""
import os
from pathlib import Path
import sys
import pytest
import psycopg2

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "local-engine"))
from neoretail_local.settings import Settings
from neoretail_local.spark import create_spark
from neoretail_local.postgres_serving import write_postgres_customer_named


@pytest.mark.skipif(os.getenv("FASTTRACK_PUBLISHER_TEST") != "1", reason="requires disposable PostgreSQL probe")
def test_real_publisher_named_columns_constraints_nulls_mix_and_rollback(tmp_path):
    settings = Settings.from_env(require_blob=False, customer_selector="pandurata")
    assert settings.analytics_database == "tenant_publisher_probe", "Never run this fixture against Analytics"
    with psycopg2.connect(settings.psycopg_dsn) as connection, connection.cursor() as cursor:
        cursor.execute("CREATE SCHEMA gold_pandurata")
        cursor.execute("CREATE TABLE gold_pandurata.probe (id_customer bigint, amount double precision CHECK (amount>=0), label text)")
    spark = create_spark(settings)
    try:
        good = spark.createDataFrame([("keep", 17066, 1.0)], ["label", "id_customer", "amount"])
        write_postgres_customer_named(good, settings, "gold", "probe")
        for rows in ([("null", None, 1.0), ("valid",17066,1.0)], [("wrong",290,1.0)],
                     [("valid",17066,1.0), ("wrong",16868,1.0)]):
            with pytest.raises(RuntimeError):
                write_postgres_customer_named(spark.createDataFrame(rows, good.schema), settings, "gold", "probe")
        with pytest.raises(Exception):
            write_postgres_customer_named(spark.createDataFrame([("fail",17066,-1.0)], good.schema), settings, "gold", "probe")
        # A numeric cast must never truncate an invalid identity into the tenant.
        for identity in (17066.1, float('nan')):
            with pytest.raises(RuntimeError):
                frame = spark.createDataFrame([('fractional',identity,1.0)], ['label','id_customer','amount'])
                write_postgres_customer_named(frame,settings,'gold','probe')
        from dataclasses import replace
        from neoretail_local.pipeline import write_lake, read_lake
        lake_settings = replace(settings,data_root=tmp_path)
        write_lake(good,lake_settings,'gold','probe',customer_scoped=True)
        bad = spark.createDataFrame([('wrong',290,1.0)],good.schema)
        with pytest.raises(RuntimeError):
            write_lake(bad,lake_settings,'gold','probe',customer_scoped=True)
        with pytest.raises(RuntimeError):
            write_lake(good,lake_settings,'gold','probe',customer_scoped=False)
        assert [tuple(row) for row in read_lake(spark,lake_settings,'gold','probe',customer_scoped=True).collect()] == [('keep',17066,1.0)]
        with psycopg2.connect(settings.psycopg_dsn) as connection, connection.cursor() as cursor:
            cursor.execute("SELECT id_customer,amount,label FROM gold_pandurata.probe")
            assert cursor.fetchall() == [(17066,1.0,"keep")], "failed INSERT must rollback its preceding DELETE"
            cursor.execute("SELECT attnotnull FROM pg_attribute WHERE attrelid='gold_pandurata.probe'::regclass AND attname='id_customer'")
            assert cursor.fetchone()[0] is True
            cursor.execute("SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='gold_pandurata' AND c.relname LIKE '_stage_%'")
            assert cursor.fetchone()[0] == 0
    finally:
        spark.stop()
