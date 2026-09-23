from pathlib import Path
import os
import re
import sys

import yaml


ROOT = Path(
    os.getenv("NEORETAIL_REPO_ROOT", str(Path(__file__).resolve().parents[2]))
).resolve()
sys.path.insert(0, str(ROOT / "local-engine"))

from neoretail_local.candidate_rules import candidate_table, classify_file, family_rules
from neoretail_local.silver_contracts import (
    canonical_column_mapping,
    canonical_column_name,
    family_table_prefix,
)


def test_local_architecture_has_no_databricks_runtime():
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    assert "databricks-dev" not in compose["services"]
    assert "local-engine" in compose["services"]
    assert "analytics-db" in compose["services"]


def test_source_of_truth_remains_blob():
    catalog = yaml.safe_load((ROOT / "config/source_catalog.yaml").read_text(encoding="utf-8"))
    assert catalog["source_of_truth"] == "azure_blob"
    assert catalog["runtime"] == "local_pyspark_postgres_multitenant"


def test_gold_is_served_by_separate_postgres():
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    assert compose["services"]["superset-db"]["environment"]["POSTGRES_DB"] == "superset"
    assert "ANALYTICS_DB_NAME" in str(compose["services"]["analytics-db"]["environment"])


def test_multitenant_candidate_families_are_disjoint_and_complete():
    catalog = yaml.safe_load((ROOT / "config/source_catalog.yaml").read_text(encoding="utf-8"))
    rules = family_rules(catalog)
    examples = {
        "ETL_CALC_CARREFOUR.snappy.parquet": ("etl_calc_v1", "carrefour"),
        "ETL_CALC_V2_CARREFOUR.snappy.parquet": ("etl_calc_v2", "carrefour"),
        "PARTICULAR_FATO_DIARIA_CARREFOUR_3CORACOES.snappy.parquet": ("fato_diaria", "carrefour"),
        "PARTICULAR_FATO_HISTORICO_GPA_3CORACOES.snappy.parquet": ("fato_historico", "gpa"),
        "PARTICULAR_FATO_IVD_TVD_GPA.snappy.parquet": ("fato_ivd_tvd", "gpa"),
        "PARTICULAR_FATO_NIVEL_ATIVIDADE_GPA_3CORACOES.snappy.parquet": ("fato_nivel_atividade", "gpa"),
        "PARTICULAR_FATO_PRECO_GPA.snappy.parquet": ("fato_preco", "gpa"),
        "PARTICULAR_MENSAL_CAUSA_OSA_GPA_3CORACOES.snappy.parquet": ("mensal_causa_osa", "gpa"),
        "PARTICULAR_SEMANAL_GPA.snappy.parquet": ("semanal", "gpa"),
        "PARTICULAR_FATO_DIARIA_CARREFOUR_BASTON.snappy.parquet": ("fato_diaria", "carrefour"),
        "PARTICULAR_FATO_HISTORICO_GPA_SAFIRA.snappy.parquet": ("fato_historico", "gpa"),
    }
    assert set(rules) == {family for family, _ in examples.values()}
    for file_name, expected in examples.items():
        assert classify_file(file_name, rules) == expected
    assert classify_file("README.txt", rules) is None


def test_candidate_table_is_safe_and_versioned():
    assert candidate_table("etl_calc_v1", "carrefour") == "candidate_etl_calc_v1_carrefour"
    assert candidate_table("etl_calc_v2", "carrefour") == "candidate_etl_calc_v2_carrefour"
    assert re.fullmatch(r"[a-z_][a-z0-9_]*", candidate_table("semanal", "gpa"))


def test_power_query_columns_are_normalized_for_spark_and_postgres():
    assert canonical_column_name("Nivel de atividade TVD") == "nivel_de_atividade_tvd"
    assert canonical_column_name("CAUSA_OSA_M0") == "causa_osa_m0"
    assert canonical_column_name("Status Ruptura") == "status_ruptura"
    assert family_table_prefix("etl_calc_v2") == "candidate_etl_calc_v2_"


def test_power_query_column_collision_is_rejected():
    try:
        canonical_column_mapping(["Preço", "Preco"])
    except ValueError as exc:
        assert "Colisoes" in str(exc)
    else:
        raise AssertionError("Colisoes de nomes precisam interromper a Silver")


def test_power_query_contract_covers_dimensions_facts_and_opportunities():
    contract = yaml.safe_load(
        (ROOT / "config/power_query_contracts.yaml").read_text(encoding="utf-8")
    )
    assert set(contract["dimensions"]) == {
        "dim_itens", "dim_local", "dim_customer", "dim_conversao",
        "dim_catalogo_produtos", "dim_catalogo_local",
        "aux_contratado_local", "aux_contratado_segmento",
    }
    assert set(contract["fact_families"]) == {
        "fato_diaria", "fato_historico", "fato_ivd_tvd",
        "fato_nivel_atividade", "fato_preco", "mensal_causa_osa",
        "semanal", "etl_calc_v1", "etl_calc_v2",
    }
    assert contract["opportunities"]["required_key_columns"] == [
        "id_location", "id_item"
    ]
    assert len(contract["fact_families"]["etl_calc_v2"]["columns"]) == 39
    assert contract["fact_families"]["fato_diaria"]["aliases"] == {
        "dias_sem_venda": ["dias_sem_vendas"]
    }
    assert contract["fact_families"]["etl_calc_v2"]["types"]["tvd"] == "decimal_19_4"
    assert contract["market"]["status"] == "excluded_from_pipeline"


def test_market_fact_is_excluded_from_pipeline():
    pipeline = (ROOT / "local-engine/neoretail_local/pipeline.py").read_text(encoding="utf-8")
    runner = (ROOT / "run-local-pipeline.ps1").read_text(encoding="utf-8")
    refresh = (ROOT / "run-multitenant-refresh.ps1").read_text(encoding="utf-8")
    assert 'glob("candidate_mercado_*")' not in pipeline
    assert '"02C"' not in runner
    assert "IncludeMarket" not in refresh


def test_gold_dimension_set_includes_market_and_activity_dimensions():
    pipeline = (ROOT / "local-engine/neoretail_local/pipeline.py").read_text(encoding="utf-8")
    assert '"dim_catalogo_local": "dim_local_raw"' in pipeline
    assert '"dim_nivel_atividade": "candidate_fato_nivel_atividade_*"' in pipeline


def test_auxiliary_retailer_dimension_is_an_approved_bronze_source():
    catalog = yaml.safe_load((ROOT / "config/source_catalog.yaml").read_text(encoding="utf-8"))
    source = catalog["sources"]["dim_varejo_contratado"]
    assert source["path"] == "DIMENSAO/DIMENSAO_VAREJO_CONTRATADO.snappy.parquet"
    assert source["bronze_table"] == "dim_varejo_contratado_raw"


def test_approved_facts_promote_validated_silver_without_blob_download():
    approval = yaml.safe_load(
        (ROOT / "config/approved_facts.yaml").read_text(encoding="utf-8")
    )
    assert approval["policy"]["source"] == "silver_validated"
    assert len(approval["facts"]) == 8
    assert all(fact["status"] == "approved" for fact in approval["facts"])
    assert all("silver_table" in fact for fact in approval["facts"])
    assert all(fact["tenant_column"] == "id_customer" for fact in approval["facts"])

    pipeline = (ROOT / "local-engine/neoretail_local/pipeline.py").read_text(
        encoding="utf-8"
    )
    step_04 = pipeline.split("def step_04_approve_facts", 1)[1].split(
        "def step_05_gold_dimensions", 1
    )[0]
    step_06 = pipeline.split("def step_06_silver_gold_facts", 1)[1].split(
        "def step_07_metric_readiness", 1
    )[0]
    assert 'spark, settings, "silver", silver_table, customer_scoped=True' in step_04
    assert "download_approved_source" not in step_04
    assert 'spark, settings, "silver", silver_table, customer_scoped=True' in step_06
    assert 'write_lake(frame, settings, "silver", logical)' not in step_06


def test_handlebars_card_assets_and_sanitization_are_present():
    config = (ROOT / "superset/superset_config.py").read_text(encoding="utf-8")
    template = (
        ROOT / "superset/chart-templates/neoretail_kpi_card_tvd.html"
    ).read_text(encoding="utf-8")
    css = (
        ROOT / "superset/chart-templates/neoretail_kpi_card_tvd.css"
    ).read_text(encoding="utf-8")
    sql = (ROOT / "analytics-db/views/10_kpi_card_tvd.sql").read_text(
        encoding="utf-8"
    )
    assert "HTML_SANITIZATION = True" in config
    assert '"tagNames": ["style", "header", "svg", "polygon", "polyline"]' in config
    assert '{{#each data}}' in template
    assert 'class="nr-kpi-card"' in template
    assert ".nr-kpi-card" in css
    assert "CREATE OR REPLACE VIEW gold.vw_kpi_card_tvd" in sql
    assert "id_customer" in sql


def test_v9_customer_registry_and_embedded_rls():
    registry = yaml.safe_load(
        (ROOT / "config/customers.yaml").read_text(encoding="utf-8")
    )
    assert [row["id_customer"] for row in registry["customers"]] == [142]
    assert registry["default_customer"] == 142
    assert registry["customers"][0]["nm_customer"] == "AMBEV"
    assert registry["customers"][0]["source_prefix"] == "FATO/CUSTOMER/DAILY/NM_CUSTOMER=AMBEV"
    assert registry["customers"][0]["source_layout"] == "partitioned_customer_daily_v1"
    server = (ROOT / "embedded-app/server.js").read_text(encoding="utf-8")
    assert "id_customer = ${idCustomer}" in server
    assert "allowedCustomerIds.includes(idCustomer)" in server
    assert 'app.get("/api/catalog"' in server
    assert "authorizedDashboard(identity, dashboardKey)" in server
    assert "tenant_id =" not in server

    tenant_config = yaml.safe_load(
        (ROOT / "config/tenants.yaml").read_text(encoding="utf-8")
    )
    assert set(tenant_config["dashboards"]) == {
        "overview", "overview_quantity", "panorama", "osa", "tasks",
        "export_daily", "export_monthly",
    }
    assert len({
        definition["embedded_id"]
        for definition in tenant_config["dashboards"].values()
    }) == 7

    smoke = (ROOT / "embedded-app/smoke.mjs").read_text(encoding="utf-8")
    assert "TENANTS_CONFIG" in smoke
    assert "assertSameDashboardSet" in smoke
    assert "missing" in smoke
    assert "unexpected" in smoke
    assert re.search(r"dashboards\?\.length\s*!==\s*\d+", smoke) is None
    assert re.search(r"dashboards:\s*\d+", smoke) is None

    smoke = (ROOT / "embedded-app/smoke.mjs").read_text(encoding="utf-8")
    assert "TENANTS_CONFIG" in smoke
    assert "assertSameDashboardSet" in smoke
    assert "missing" in smoke
    assert "unexpected" in smoke
    assert re.search(r"dashboards\?\.length\s*!==\s*\d+", smoke) is None
    assert re.search(r"dashboards:\s*\d+", smoke) is None


def test_concurrency_benchmark_uses_real_cache_bypass_and_safe_stats_monitor():
    benchmark = (ROOT / "superset/concurrent_dashboard_benchmark.py").read_text(
        encoding="utf-8"
    )
    wrapper = (ROOT / "load-test-users.ps1").read_text(encoding="utf-8")
    monitor = (ROOT / "scripts/monitor-docker-stats.ps1").read_text(
        encoding="utf-8"
    )

    assert "force=FORCE" in benchmark
    assert 'LOAD_TEST_MAX_WORKERS", "12"' in benchmark
    assert "[int]$MaxWorkers = 12" in wrapper
    assert "Start-Job" not in wrapper
    assert "Start-Process" in wrapper
    assert "WaitForExit" in wrapper
    assert "System.IO.StreamWriter" in monitor
    assert "docker stats --no-stream" in monitor


def test_overview_quantity_uses_certified_components_and_filtered_fallback():
    sql = (ROOT / "analytics-db/marts/40_overview_quantity_semantic.sql").read_text(
        encoding="utf-8"
    )
    bootstrap = (ROOT / "superset/bootstrap_overview_quantity.py").read_text(
        encoding="utf-8"
    )
    validator = (ROOT / "superset/validate_overview_quantity.py").read_text(
        encoding="utf-8"
    )

    assert "nr_overview_quantity_default" in sql
    assert "FILTER (WHERE faturamento > 0)" in sql
    assert "COUNT(DISTINCT cnpj) FILTER (WHERE positivacao = 1)" in sql
    assert "SUM(COALESCE(status_item_geral, 0))" in sql
    assert "SUM(COALESCE(demanda_media, 0))" in sql
    assert "COUNT(o.id_item) FILTER" in sql
    assert "nr_overview_quantity_detail" in bootstrap
    assert "remove_filter=True" in bootstrap or "_jinja_filter_predicates" in bootstrap
    assert "ratio_percent" in bootstrap
    assert "nr_overview_quantity_default" in validator
