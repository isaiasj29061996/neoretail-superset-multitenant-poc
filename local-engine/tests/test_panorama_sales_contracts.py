from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_weekly_sales_contract_uses_real_fact_and_top_13_cd_week():
    bootstrap = (ROOT / "superset" / "bootstrap_panorama.py").read_text(encoding="utf-8")
    assert "FROM gold.fato_semanal w" in bootstrap
    assert "ORDER BY cd_week DESC" in bootstrap
    assert "week_rank<=13" in bootstrap or "week_rank <= 13" in bootstrap
    assert "get_filters" in bootstrap and "remove_filter=True" in (
        ROOT / "superset" / "neoretail_bootstrap" / "core" / "filters.py"
    ).read_text(encoding="utf-8")


def test_sales_tabs_and_per_metric_semantics_are_declared():
    bootstrap = (ROOT / "superset" / "bootstrap_panorama.py").read_text(encoding="utf-8")
    assert 'charts[f"sales_value_{period}"]' in bootstrap
    assert 'charts[f"sales_quantity_{period}"]' in bootstrap
    assert 'sales_value_summary_' not in bootstrap
    assert 'sales_quantity_summary_' not in bootstrap
    assert "direct_average:0:1|direct_sum:1:1|weighted_average:2:2" in bootstrap
    assert "direct_average:0:1|direct_average:1:1|markup_blank:0:2" in bootstrap
    assert "summary_count=3" in bootstrap


def test_quantity_reuses_certified_overview_contract():
    bootstrap = (ROOT / "superset" / "bootstrap_panorama.py").read_text(encoding="utf-8")
    assert "from bootstrap_overview_quantity import Q, quantity_semantic_sql" in bootstrap
    assert 'filter_targets["nm_measure"] = conversion_options.id' in bootstrap


def test_weekly_serving_keeps_value_and_conversion_components_separate():
    sql = (ROOT / "analytics-db" / "marts" / "41_panorama_sales_semantic.sql").read_text(encoding="utf-8")
    assert "sellout_sum" in sql and "cost_sum" in sql
    assert "sales_sum" in sql and "loss_sum" in sql
    assert "price_numerator" in sql and "price_count" in sql
    assert "id_customer = w.id_customer" in sql


def test_runtime_controls_register_persisted_panorama_parameters():
    controls = (
        ROOT
        / "superset"
        / "frontend-plugin"
        / "plugin-chart-neoretail-kpi"
        / "src"
        / "controlPanel.js"
    ).read_text(encoding="utf-8")
    for name in (
        "metric_semantics", "timeline_limit", "summary_count", "card_variant",
        "metric_labels", "metric_formats", "chart_styles",
        "timeline_query_scope", "summary_query_scope",
    ):
        assert f"name: '{name}'" in controls


def test_sellout_fallback_matches_literal_dax_aggregation():
    bootstrap = (ROOT / "superset" / "bootstrap_panorama.py").read_text(encoding="utf-8")
    mart = (ROOT / "analytics-db" / "marts" / "41_panorama_sales_semantic.sql").read_text(encoding="utf-8")
    for source in (bootstrap, mart):
        compact = "".join(source.split())
        assert "volume_sum*f.conversion_factor" in compact
        assert "fallback_price_sum" in compact
        assert "fallback_price_count" in compact
        assert "fallback_price_sum/" in compact
        assert "fallback_price_count" in compact
        assert "SUM(COALESCE(volume_unidade,0)*COALESCE(avg_sales_price,0))" not in compact
    # Counterexample: the requested DAX is deliberately not SUM(volume * price).
    volumes = (2, 8)
    prices = (100, 10)
    factor = 2
    dax_equivalent = (sum(volumes) * factor) * ((sum(prices) / len(prices)) * factor)
    row_product = sum(volume * price for volume, price in zip(volumes, prices))
    assert dax_equivalent == 2200
    assert row_product == 280


def test_monthly_value_uses_dedicated_certified_dataset():
    bootstrap = (ROOT / "superset" / "bootstrap_panorama.py").read_text(encoding="utf-8")
    assert '"nr_panorama_sales_monthly_interactive"' in bootstrap
    assert 'monthly_sales, "Evolutivo de vendas", value_measures, grain="P1M"' in bootstrap
    assert 'add("sales_value_mensal", monthly_sales' in bootstrap


def test_sales_uses_true_single_slice_with_embedded_summary():
    bootstrap = (ROOT / "superset" / "bootstrap_panorama.py").read_text(encoding="utf-8")
    build_query = (
        ROOT
        / "superset"
        / "frontend-plugin"
        / "plugin-chart-neoretail-kpi"
        / "src"
        / "buildQuery.js"
    ).read_text(encoding="utf-8")
    transform = (
        ROOT
        / "superset"
        / "frontend-plugin"
        / "plugin-chart-neoretail-kpi"
        / "src"
        / "transformProps.js"
    ).read_text(encoding="utf-8")

    assert '"nr_panorama_sales_weekly_card_interactive"' in bootstrap
    assert 'summary_query_scope="summary"' in bootstrap
    assert 'timeline_query_scope="timeline"' in bootstrap
    assert '("Valor", [(period, charts[f"sales_value_{period}"])' in bootstrap
    assert '("Quantidade", [(period, charts[f"sales_quantity_{period}"])' in bootstrap
    assert 'sales_value_summary_' not in bootstrap
    assert 'sales_quantity_summary_' not in bootstrap
    assert "summary_query_scope" in build_query
    assert "row_scope" in build_query
    assert "semanticSummaryTimeline" in transform
    assert "queriesData[1]" in transform
