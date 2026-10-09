"""Opt-in PostgreSQL test of mart/serving atomic refresh, never Analytics."""
import os
from pathlib import Path
import sys
import pytest
import psycopg2

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'local-engine'))
from neoretail_local.settings import Settings
from neoretail_local import marts

@pytest.mark.skipif(os.getenv('FASTTRACK_PUBLISHER_TEST') != '1',reason='requires disposable PostgreSQL probe')
def test_marts_and_serving_refresh_idempotently_and_rollback_together(tmp_path,monkeypatch):
    settings = Settings.from_env(require_blob=False,customer_selector='pandurata')
    assert settings.analytics_database == 'tenant_publisher_probe'
    with psycopg2.connect(settings.psycopg_dsn) as c,c.cursor() as q:
        q.execute('CREATE SCHEMA IF NOT EXISTS gold_pandurata; CREATE SCHEMA gold_lactalis; CREATE TABLE gold_lactalis.untouched (id_customer bigint, value int); INSERT INTO gold_lactalis.untouched VALUES (290,77)')
    directory=tmp_path/'analytics-db/marts'; directory.mkdir(parents=True)
    (tmp_path/'analytics-db/views').mkdir()
    names=['nr_overview_history','nr_panorama_weekly','nr_stock_tasks','nr_export_daily','nr_export_monthly','nr_filter_options']
    path=directory/'30_fixture.sql'
    def write(value=1,fail=False):
        script='BEGIN;\n'
        for name in names:
            script += f'DROP MATERIALIZED VIEW IF EXISTS gold.{name};\nCREATE MATERIALIZED VIEW gold.{name} AS SELECT 17066::bigint id_customer, {value}::int value;\n'
        if fail: script += 'SELECT 1/0;\n'
        path.write_text(script+'COMMIT;\n',encoding='utf-8')
    def serving_snapshot():
        with psycopg2.connect(settings.psycopg_dsn) as c,c.cursor() as q:
            q.execute("SELECT viewname,definition FROM pg_views WHERE schemaname='serving' ORDER BY viewname")
            return q.fetchall()
    monkeypatch.setattr(marts,'ROOT',tmp_path)
    write()
    marts.build_marts(settings)
    marts.publish_serving(settings,['pandurata'])
    before=serving_snapshot()
    marts.build_marts(settings)
    assert serving_snapshot() == before
    write(value=99,fail=True)
    with pytest.raises(psycopg2.errors.DivisionByZero): marts.build_marts(settings)
    assert serving_snapshot() == before
    with psycopg2.connect(settings.psycopg_dsn) as c,c.cursor() as q:
        q.execute('SELECT id_customer,value FROM serving.nr_overview_history')
        assert q.fetchall() == [(17066,1)]
        q.execute('SELECT id_customer,value FROM gold_lactalis.untouched')
        assert q.fetchall() == [(290,77)]
        q.execute('CREATE TABLE gold_pandurata.untouched (id_customer bigint, value int); INSERT INTO gold_pandurata.untouched VALUES (17066,88)')
        for name in names:
            q.execute(f'CREATE MATERIALIZED VIEW gold_lactalis.{name} AS SELECT 290::bigint id_customer, 2::int value')
    marts.publish_serving(settings,['pandurata'])
    # A selected LACTALIS refresh retains already-published PANDURATA.
    marts.publish_serving(settings,['lactalis'],keep_published=True)
    shared = serving_snapshot()
    marts.publish_serving(settings,['lactalis'],keep_published=True)
    assert serving_snapshot() == shared
    with psycopg2.connect(settings.psycopg_dsn) as c,c.cursor() as q:
        q.execute('SELECT id_customer,value FROM serving.nr_overview_history ORDER BY id_customer')
        assert q.fetchall() == [(290,2),(17066,1)]
        q.execute('SELECT id_customer,value FROM gold_lactalis.untouched')
        assert q.fetchall() == [(290,77)]
        q.execute('CREATE SCHEMA unexpected_source; CREATE TABLE unexpected_source.data (id_customer bigint); CREATE VIEW serving.unregistered AS SELECT id_customer FROM unexpected_source.data')
    rejected_before = serving_snapshot()
    with pytest.raises(RuntimeError,match='Unregistered or legacy serving dependency'):
        marts.publish_serving(settings,['lactalis'],keep_published=True)
    assert serving_snapshot() == rejected_before
