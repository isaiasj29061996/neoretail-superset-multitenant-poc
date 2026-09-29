from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_weekly_sales_contract_uses_real_fact_and_top_13_cd_week():
    bootstrap = (ROOT / "superset" / "bootstrap_panorama.py").read_text(encoding="utf-8")
    assert "FROM gold.fato_semanal w" in bootstrap
    assert "ORDER BY cd_week DESC" in bootstrap
    assert "week_rank<=13" in bootstrap or "week_rank <= 13" in bootstrap
    assert "get_filters" in bootstrap and "remove_filter=True" in (
        ROOT / "superset" / "bootstrap_overview.py"
    ).read_text(encoding="utf-8")


def test_sales_tabs_and_per_metric_semantics_are_declared():
    bootstrap = (ROOT / "superset" / "bootstrap_panorama.py").read_text(encoding="utf-8")
    assert '("Valor", [(period, charts[f"sales_value_{period}"])' in bootstrap
    assert '("Quantidade", [(period, charts[f"sales_quantity_{period}"])' in bootstrap
    assert "direct_average:0:1|direct_sum:1:1|weighted_average:2:2" in bootstrap
    assert "direct_average:0:1|direct_average:1:1|markup_blank:0:2" in bootstrap


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
