from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_monthly_osa_value_uses_source_value_loss_not_price_reconstruction():
    bootstrap = read("superset/bootstrap_osa_industry_certified.py")
    partitioned = read("local-engine/neoretail_local/partitioned_daily.py")
    contract = read("config/power_query_contracts.yaml")

    assert 'F.sum(_double("vl_value_osa_lost_sales")).alias("vl_perda_osa")' in partitioned
    assert "vl_perda_osa" in contract
    assert "SUM(COALESCE(c.vl_perda_osa,0))" in bootstrap
    assert "loss_value_sum" in bootstrap
    assert "qtd_perda_osa *" not in bootstrap.split("def monthly_overview_sql",1)[1].split(
        "def weekly_overview_sql",1
    )[0]


def test_monthly_quantity_and_osa_match_tmdl_formula_shapes():
    bootstrap = read("superset/bootstrap_osa_industry_certified.py")
    assert "(c.volume_sum*cf.conversion_factor)" in bootstrap
    assert "(c.loss_qty_sum*cf.conversion_factor)" in bootstrap
    assert "h.loss_qty_sum*hf.conversion_factor" in bootstrap
    assert "h.volume_sum*hf.conversion_factor" in bootstrap
    assert "100.0*(1-h.problem_sum/NULLIF(h.active_sum,0))" in bootstrap


def test_weekly_value_quantity_and_osa_contracts_are_explicit():
    bootstrap = read("superset/bootstrap_osa_industry_certified.py")
    assert "(w.loss_qty_sum*w.avg_price_cost)" in bootstrap
    assert "(w.volume_sum*f.conversion_factor)" in bootstrap
    assert "(w.loss_qty_sum*f.conversion_factor)" in bootstrap
    assert "d.demand_sum*30.0" in bootstrap
    assert "100.0*(1-w.problem_sum/NULLIF(w.active_sum,0))" in bootstrap
    assert "r.week_rank<=13" in bootstrap


def test_power_bi_period_selector_contexts_are_materialized():
    bootstrap = read("superset/bootstrap_osa_industry_certified.py")
    for token in ("'MTD'","'Mês Anterior'","'U3M'","'YTD'"):
        assert token in bootstrap
    assert "NATIVE_FILTER-osa-certified-period" in bootstrap
    assert '"val": ["Mês Anterior"]' in bootstrap
    assert "DATE_TRUNC('month',b.data)" in bootstrap


def test_value_and_quantity_dashboard_isolated_from_legacy_page():
    bootstrap = read("superset/bootstrap_osa_industry_certified.py")
    matrices = read("superset/osa_certified_matrices.py")
    tenants = read("config/tenants.yaml")
    assert 'DASHBOARD_SLUG = "neoretail-v9-osa-industria-certified"' in bootstrap
    assert 'PREFIX = "[OSA Certificada]"' in bootstrap
    assert '("Valor",[' in bootstrap
    assert '("Quantidade",[' in bootstrap
    assert "comparison_pivot_params" in bootstrap
    assert '"region": ("Região", "regiao")' in matrices
    assert '"retail": ("Varejo", "rede")' in matrices
    assert '"item": ("Hierarquia de item", "hierarquia_1")' in matrices
    assert "SUM(loss_value)" in matrices
    assert "SUM(loss_qty)" in matrices
    assert "SUM(problem_qty)" in matrices
    assert "1 - SUM(problem_base)/NULLIF(SUM(active_base),0)" in matrices
    assert "osa_certified:" in tenants
    assert "neoretail-v9-osa-industria-certified" in tenants
    # Legacy key remains available for side-by-side homologation.
    assert "slug: neoretail-v9-osa-industria\n" in tenants


def test_osa_motive_groups_use_documented_business_families():
    partitioned = read("local-engine/neoretail_local/partitioned_daily.py")
    for label in (
        "Estoque virtual",
        "Falta de Exposição",
        "Falta de performance",
        "Ruptura na loja",
    ):
        assert label in partitioned
    assert 'r"ruptura|pedido"' in partitioned


def test_runtime_gate_checks_every_chart_and_raw_sources():
    validator = read("superset/validate_osa_industry_certified.py")
    assert "information_schema.columns" in validator
    assert "vl_perda_osa" in validator
    assert "MONTHLY_EXPECTED" in validator
    assert "WEEKLY_EXPECTED" in validator
    assert "MOTIVE_VALUE_EXPECTED" in validator
    assert "MOTIVE_QTY_EXPECTED" in validator
    assert "source=ChartData" in validator
    assert "ChartDataCommand" in validator


def test_full_ambev_runner_bootstraps_certified_dashboard_before_embedding():
    runner = read("run-ambev-35-full.ps1")
    assert '"bootstrap_osa_industry_certified.py"' in runner
    old = runner.index('"bootstrap_osa_industry.py"')
    new = runner.index('"bootstrap_osa_industry_certified.py"')
    embedded = runner.index('"bootstrap_embedded.py"')
    assert old < new < embedded
