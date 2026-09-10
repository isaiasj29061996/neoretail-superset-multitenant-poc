from __future__ import annotations

import compileall
import importlib.util
import inspect
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def run_tests(directory: Path) -> None:
    for path in sorted(directory.glob("test_*.py")):
        if path.name == "test_power_query_runtime.py":
            # Executado dentro do local-engine, onde PySpark/Java estao instalados.
            continue
        spec = importlib.util.spec_from_file_location(path.stem, path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        for name in sorted(dir(module)):
            test = getattr(module, name)
            if (
                name.startswith("test_")
                and callable(test)
                and not inspect.signature(test).parameters
            ):
                test()


def main() -> None:
    assert compileall.compile_dir(ROOT / "blob-profiler", quiet=1)
    assert compileall.compile_dir(ROOT / "local-engine", quiet=1)

    yaml_files = [ROOT / "docker-compose.yml", *sorted((ROOT / "config").glob("*.yaml"))]
    for path in yaml_files:
        assert yaml.safe_load(path.read_text(encoding="utf-8")) is not None, path

    run_tests(ROOT / "local-engine" / "tests")

    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    services = compose["services"]
    assert "converter" not in services
    assert "databricks-dev" not in services
    assert "local-engine" in services
    assert "analytics-db" in services
    assert "superset-db" in services
    assert "blob-profiler" in services
    assert not (ROOT / "pbix").exists()
    assert not (ROOT / "pbi-live").exists()
    assert (ROOT / "config/customers.yaml").is_file()

    source_catalog = yaml.safe_load((ROOT / "config/source_catalog.yaml").read_text(encoding="utf-8"))
    assert source_catalog["version"] == "9.0"
    assert source_catalog["source_of_truth"] == "azure_blob"
    assert source_catalog["runtime"] == "local_pyspark_postgres_multitenant"
    discovery = source_catalog["discovery"]
    assert discovery["facts_prefix_source"] == "customers.yaml"
    assert len(discovery["families"]) == 9
    assert discovery["candidate_policy"]["gold_requires_approval"] is True

    notebooks = sorted((ROOT / "local-engine" / "notebooks").glob("*.py"))
    assert [path.name for path in notebooks] == [
        "00_setup_local.py",
        "01_discover_blob.py",
        "02a_bronze_dimensions.py",
        "02b_bronze_fact_candidates.py",
        "02c_bronze_market.py",
        "03a_silver_dimensions.py",
        "03b_silver_facts.py",
        "03c_silver_opportunities.py",
        "03d_validate_power_query_parity.py",
        "04_approve_facts.py",
        "05_gold_dimensions_e_postgresql.py",
        "06_silver_gold_facts.py",
        "07_metric_readiness.py",
        "08_quality_gate.py",
    ]

    start_script = (ROOT / "start.ps1").read_text(encoding="utf-8")
    health_script = (ROOT / "health.ps1").read_text(encoding="utf-8")
    assert all(f'Write-Step {step} ' in start_script for step in range(1, 8))
    assert 'Wait-NeoRetailOneShot "superset-init"' in start_script
    for service in (
        "superset-db", "analytics-db", "redis", "superset",
        "local-engine", "embedded-app",
    ):
        assert f'Wait-NeoRetailHealthy "{service}"' in health_script

    dockerfile = (ROOT / "superset/Dockerfile").read_text(encoding="utf-8")
    assert "databricks" not in dockerfile.lower()
    assert "bootstrap_analytics.py" in dockerfile
    assert "plugin-chart-neoretail-kpi" in dockerfile
    assert "npm run build" in dockerfile

    plugin = ROOT / "superset/frontend-plugin/plugin-chart-neoretail-kpi/src"
    assert (plugin / "NeoRetailKpi.jsx").is_file()
    assert (plugin / "buildQuery.js").is_file()
    assert (plugin / "controlPanel.js").is_file()
    assert (plugin / "transformProps.js").is_file()
    register = (ROOT / "superset/frontend-plugin/register-plugin.mjs").read_text(
        encoding="utf-8"
    )
    assert "neoretail-kpi-card" in register

    bootstrap = (ROOT / "superset/bootstrap_analytics.py").read_text(encoding="utf-8")
    assert "database.set_sqlalchemy_uri(uri)" in bootstrap
    assert "database.sqlalchemy_uri = uri" not in bootstrap
    assert "with database.get_sqla_engine() as engine:" in bootstrap
    assert "with engine.begin() as connection:" in bootstrap
    assert "get_sqla_engine().begin()" not in bootstrap
    assert bootstrap.index("db.session.flush()") < bootstrap.index("database.get_sqla_engine()")
    assert bootstrap.index("database.get_sqla_engine()") < bootstrap.index("db.session.commit()")

    local_dockerfile = (ROOT / "local-engine/Dockerfile").read_text(encoding="utf-8")
    assert local_dockerfile.startswith("FROM python:3.11-slim-bookworm\n")
    assert "openjdk-17-jre-headless" in local_dockerfile

    candidate_script = (ROOT / "ingest-fact-candidates.ps1").read_text(encoding="utf-8")
    assert "neoretail_local.candidates" in candidate_script
    assert "AZURE_STORAGE_CONNECTION_STRING" in candidate_script
    candidates_module = (ROOT / "local-engine/neoretail_local/candidates.py").read_text(encoding="utf-8")
    assert 'status_by_path[candidate.blob_path] = "empty_source"' in candidates_module
    assert '"passed_with_empty_sources"' in candidates_module
    pipeline_script = (ROOT / "run-local-pipeline.ps1").read_text(encoding="utf-8")
    assert 'if ($Step -eq "02B")' in pipeline_script
    assert '$pipelineStep = if ($Step -eq "02A") { "02" } else { $Step }' in pipeline_script
    pipeline_module = (ROOT / "local-engine/neoretail_local/pipeline.py").read_text(encoding="utf-8")
    assert '"customer_facts_files"' in pipeline_module
    assert 'customer_selector=args.customer' not in pipeline_module
    assert 'run_pipeline(args.customer)' in pipeline_module
    assert 'tenant_id' not in pipeline_module
    assert '"03A": step_03a_silver_dimensions' in pipeline_module
    assert '"03B": step_03b_silver_facts' in pipeline_module
    assert '"03C": step_03c_opportunities' in pipeline_module
    assert '"03D": step_03d_silver_validation' in pipeline_module
    power_query_contracts = yaml.safe_load(
        (ROOT / "config/power_query_contracts.yaml").read_text(encoding="utf-8")
    )
    assert power_query_contracts["policy"]["no_unproven_business_formula"] is True
    assert power_query_contracts["opportunities"]["source_table"] == "etl_calc_v2"
    assert power_query_contracts["opportunities"]["formula_parity"] == (
        "power_query_m_exact_dax_deferred_to_semantic_layer"
    )
    assert len(power_query_contracts["dimensions"]) == 8
    assert len(power_query_contracts["fact_families"]["etl_calc_v2"]["columns"]) == 39
    assert power_query_contracts["market"]["status"] == "excluded_from_pipeline"
    assert 'glob("candidate_mercado_*")' not in pipeline_module
    assert '"02C"' not in pipeline_script

    customers = yaml.safe_load(
        (ROOT / "config/customers.yaml").read_text(encoding="utf-8")
    )["customers"]
    assert [row["id_customer"] for row in customers] == [259, 609, 16868]
    assert len({row["source_prefix"] for row in customers}) == 3

    embedded = (ROOT / "embedded-app/server.js").read_text(encoding="utf-8")
    assert "id_customer = ${idCustomer}" in embedded
    assert "allowedCustomerIds.includes(idCustomer)" in embedded
    assert 'app.get("/api/catalog"' in embedded
    assert "dashboardKey" in embedded
    assert "authorizedDashboard(identity, dashboardKey)" in embedded
    assert "tenant_id =" not in embedded

    tenants = yaml.safe_load(
        (ROOT / "config/tenants.yaml").read_text(encoding="utf-8")
    )
    assert tenants["default_dashboard"] == "overview"
    assert set(tenants["dashboards"]) == {"overview", "panorama", "osa", "tasks"}
    assert len({item["embedded_id"] for item in tenants["dashboards"].values()}) == 4
    assert [item["key"] for item in tenants["navigation"]] == [
        "overview", "panorama", "tasks"
    ]

    print("Validacao V9 concluida: clientes, particoes, Gold e RLS aprovados.")


if __name__ == "__main__":
    main()
