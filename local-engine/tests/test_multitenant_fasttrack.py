from pathlib import Path
import sys
from types import SimpleNamespace
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "local-engine"))
sys.path.insert(0, str(ROOT / "superset"))
from neoretail_local.customers import resolve_tenant
from neoretail_local.postgres_serving import publication_schema
from neoretail_bootstrap.core.sql_sources import rewrite_gold_sources


def test_publication_schema_is_resolved_not_caller_selected():
    path = ROOT / "config/customers.yaml"
    context = resolve_tenant(path, "pandurata")
    settings = SimpleNamespace(customers_config_path=path, id_customer=17066, tenant_context=context)
    assert publication_schema(settings, "gold") == "gold_pandurata"
    assert publication_schema(settings, "gold_pandurata") == "gold_pandurata"
    assert publication_schema(settings, "audit") == "audit"
    for schema in ("gold_lactalis", "serving", "gold;DROP SCHEMA gold"):
        with pytest.raises(RuntimeError): publication_schema(settings, schema)


def test_renderer_changes_only_qualified_relations():
    original = """-- gold.nr_fake
SELECT 'gold.nr_literal', $$gold.nr_literal$$, $tag$gold.nr_literal$tag$, x
FROM gold.nr_overview_history h /* gold.nr_fake */
JOIN "gold"."dim_local" l ON l.id_customer=h.id_customer"""
    expected = original.replace("FROM gold.nr_overview_history", "FROM gold_pandurata.nr_overview_history").replace(
        'JOIN "gold"."dim_local"', 'JOIN gold_pandurata."dim_local"')
    assert rewrite_gold_sources(original, "gold_pandurata") == expected
    assert rewrite_gold_sources(original, "gold") == original
    with pytest.raises(ValueError): rewrite_gold_sources(original, "bad; DROP")
    with pytest.raises(ValueError): rewrite_gold_sources("SELECT * FROM gold.users", "serving")


def test_renderer_preserves_jinja_quotes_inside_sql_literals():
    original = '''{% set selected = get_filters('indicador', remove_filter=True) %}
SELECT '{{ selected | replace("'", "''") }}' AS indicador
FROM gold.nr_export_daily source'''
    assert rewrite_gold_sources(original,'serving') == original.replace('FROM gold.nr_export_daily','FROM serving.nr_export_daily')
    original = '''SELECT {{ {'x': {'end': '}}', 'other': "a\\\"b"}} }} FROM gold.nr_overview_history'''
    assert rewrite_gold_sources(original,'serving').endswith('FROM serving.nr_overview_history')


def test_all_versioned_sql_roundtrips_without_business_change():
    paths = list((ROOT / "analytics-db/marts").glob("*.sql")) + list((ROOT / "analytics-db/views").glob("*.sql"))
    assert not any("45_osa" in path.name for path in paths)
    for path in paths:
        original = path.read_text(encoding="utf-8")
        rendered = rewrite_gold_sources(original, "gold_pandurata")
        # Reverse only the generated identifier tokens, not comments/literals.
        assert rendered != original, path
        assert original.count("id_customer") == rendered.count("id_customer"), path
        from neoretail_bootstrap.core.sql_sources import _tokens
        before = [(kind, value) for kind,value in _tokens(original) if not (kind == "identifier" and value.strip('"') == "gold")]
        after = [(kind, value) for kind,value in _tokens(rendered) if not (kind == "identifier" and value == "gold_pandurata")]
        assert before == after, path


def test_dev_authorization_excludes_baseline_and_allows_only_three_registered_ids():
    import yaml
    config = yaml.safe_load((ROOT / "config/tenants.yaml").read_text(encoding="utf-8"))
    assert config["default_customer_id"] == 17066
    assert config["users"][0]["allowed_customer_ids"] == [17066, 290, 16868]
    assert "customers" not in config
    for customer_id in config["users"][0]["allowed_customer_ids"]:
        assert resolve_tenant(ROOT / "config/customers.yaml", customer_id).id_customer == customer_id


def test_tenant_publisher_has_null_guard_and_database_constraints():
    source = (ROOT / "local-engine/neoretail_local/postgres_serving.py").read_text(encoding="utf-8")
    assert 'cast("long").isNull()' in source
    assert "ALTER COLUMN id_customer SET NOT NULL" in source
    assert "CHECK (id_customer = %s)" in source
    assert "INSERT INTO {}.{} ({}) SELECT {}" in source
    pipeline = (ROOT / "local-engine/neoretail_local/pipeline.py").read_text(encoding="utf-8")
    wrapper = pipeline[pipeline.index("def write_postgres_customer("):pipeline.index("def ensure_schemas(")]
    assert "write_postgres_customer_named" in wrapper and "SELECT *" not in wrapper


def test_consumption_schema_only_accepts_shared_serving_or_legacy_gold(monkeypatch):
    from neoretail_bootstrap.core.sql_sources import consumption_sql
    query = 'SELECT MAX(data) FROM gold.nr_export_daily'
    monkeypatch.delenv('NEORETAIL_CONSUMPTION_SCHEMA', raising=False)
    assert consumption_sql(query) == query
    monkeypatch.setenv('NEORETAIL_CONSUMPTION_SCHEMA', 'serving')
    assert consumption_sql(query) == 'SELECT MAX(data) FROM serving.nr_export_daily'
    monkeypatch.setenv('NEORETAIL_CONSUMPTION_SCHEMA', 'gold_lactalis')
    with pytest.raises(ValueError): consumption_sql(query)


def test_bootstrap_default_dates_use_same_controlled_source_as_datasets():
    import ast
    for name in ('overview', 'panorama', 'export', 'stock_optimization'):
        tree = ast.parse((ROOT/f'superset/bootstrap_{name}.py').read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'text':
                assert isinstance(node.args[0], ast.Call) and node.args[0].func.id == 'consumption_sql'


def test_refresh_never_runs_legacy_global_gold_mart_script():
    source = (ROOT/'run-multitenant-refresh.ps1').read_text(encoding='utf-8')
    assert 'create-superset-kpi-views.ps1' not in source
    assert 'neoretail_local.marts --tenant' in source
    assert '--serving-tenants' in source
    assert '--keep-published-tenants' in source
    assert '-not $context.execution_active -or $context.id_customer -eq 142' in source


def test_mart_transaction_wrapper_keeps_literals_and_functional_statements():
    from neoretail_bootstrap.core.sql_sources import in_caller_transaction
    original = "-- BEGIN;\nBEGIN;\nSELECT 'COMMIT;', $$BEGIN;$$ FROM gold.nr_overview_history;\nCOMMIT;"
    rendered = in_caller_transaction(original)
    assert rendered == "-- BEGIN;\n\nSELECT 'COMMIT;', $$BEGIN;$$ FROM gold.nr_overview_history;\n"
    assert in_caller_transaction("SELECT 1;") == "SELECT 1;"


def test_export_indicator_options_expose_tenant_without_changing_labels():
    from neoretail_bootstrap.export.options import INDICATORS, indicator_sql
    labels = INDICATORS
    assert labels == ('Venda','Cobertura estoque','Estoque','Estoque em Trânsito',
                      'ISV (%)','OSA (%)','Perda OSA vol.','Perda OSA R$','Preço médio (R$)')
    sql = indicator_sql()
    assert sql.startswith('SELECT customers.id_customer, options.indicador')
    assert 'SELECT DISTINCT id_customer FROM gold.dim_customer' in sql
    assert sql[sql.index('(VALUES'):] == '(VALUES\n    '+',\n    '.join(f"('{v}')" for v in labels)+'\n) AS options(indicador)'
    assert 'serving.dim_customer' in rewrite_gold_sources(sql,'serving')
