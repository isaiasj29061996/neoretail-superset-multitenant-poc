from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_pbip_comparison_hierarchies_and_tabs_are_preserved():
    bootstrap = read("superset/bootstrap_panorama.py")
    assert '"region": ("regiao", "uf", "cidade")' in bootstrap
    assert '"retail": ("rede", "bandeira", "loja")' in bootstrap
    assert '"hierarchy": ("hierarquia_1", "hierarquia_2", "item")' in bootstrap
    for tab in ("Valor", "Quantidade", "R$ Estoque", "OSA", "Falta x Excesso"):
        assert f'("{tab}",' in bootstrap
    assert '"viz_type": "pivot_table_v2"' in bootstrap
    assert '"rowOrder": "value_z_to_a"' in bootstrap
    assert '"order_desc": True' in bootstrap


def test_comparisons_are_not_the_old_top_ten_rankbars():
    bootstrap = read("superset/bootstrap_panorama.py")
    assert 'f"Comparativo — {dimension_label}"' in bootstrap
    assert '"row_limit": 10000' in bootstrap
    assert 'row_limit=10))' not in bootstrap
    assert 'variant="rankbars"' not in bootstrap


def test_history_comparison_uses_physical_mart_and_exact_tmdl_components():
    mart = read("analytics-db/marts/43_panorama_inventory_semantic.sql")
    bootstrap = read("superset/bootstrap_panorama.py")
    assert "gold.nr_panorama_comparison_history_detail" in mart
    assert "status_item_geral" in mart
    assert "FROM gold.nr_panorama_comparison_history_detail h" in bootstrap
    assert '"1-SUM(osa_problem_sum)/NULLIF(SUM(osa_active_sum),0)"' in bootstrap
    assert '"% RUP", "SUM(rupture_sum)/NULLIF(SUM(status_sum),0)"' in bootstrap
    assert '"% ISV", "SUM(isv_sum)/NULLIF(SUM(status_sum),0)"' in bootstrap
    assert "SUM(giro_num)/NULLIF(SUM(giro_den),0)" in bootstrap


def test_comparison_conversion_and_time_defaults_are_governed():
    bootstrap = read("superset/bootstrap_panorama.py")
    assert "get_filters('nm_measure', remove_filter=True)" in bootstrap
    assert "o.nm_measure='unidade'" in bootstrap
    assert "JOIN gold.nr_conversion_options o" in bootstrap
    assert "h.data >= DATE_TRUNC('year', CURRENT_DATE)" in bootstrap
    assert "o.data >= DATE_TRUNC('year', CURRENT_DATE)" in bootstrap


def test_gap_comparison_preserves_lastnonblank_and_physical_serving():
    mart = read("analytics-db/marts/43_panorama_inventory_semantic.sql")
    bootstrap = read("superset/bootstrap_panorama.py")
    assert "gold.nr_panorama_comparison_gap_daily" in mart
    assert "FROM gold.nr_panorama_opportunities o" in mart
    assert "FROM gold.nr_panorama_comparison_gap_daily o" in bootstrap
    assert "ARRAY_AGG(tvd ORDER BY data DESC) FILTER (WHERE tvd IS NOT NULL)" in bootstrap
    assert "ARRAY_AGG(ivd ORDER BY data DESC) FILTER (WHERE ivd IS NOT NULL)" in bootstrap
    assert '"R$ Pré-ruptura"' in bootstrap
    assert '"R$ Excesso"' in bootstrap
    assert "has_dimension_filter" in bootstrap
    assert "FROM gold.nr_panorama_opportunities o" in bootstrap


def test_all_comparison_datasets_receive_rls_and_native_filters():
    bootstrap = read("superset/bootstrap_panorama.py")
    assert "*comparison_dataset_ids" in bootstrap
    assert "filter_targets[\"nm_measure\"] = conversion_options.id" in bootstrap
    assert "for dataset in (*comparison_history.values(), *comparison_gap.values())" in bootstrap


def test_runtime_gate_compares_source_mart_and_actual_chartdata():
    validator = read("superset/validate_panorama_comparisons.py")
    assert "gold.fato_historico" in validator
    assert "gold.fato_ivd_tvd" in validator
    assert "gold.nr_panorama_comparison_history_detail" in validator
    assert "gold.nr_panorama_comparison_gap_daily" in validator
    assert "ChartDataCommand" in validator
    assert "source-mart:" in validator
    assert "source-chart:" in validator


def test_comparison_pivots_keep_individual_metric_formats():
    bootstrap = read("superset/bootstrap_panorama.py")
    # A single SMART_NUMBER formatter was flattening ratios such as Markup
    # into 1.17 instead of the Power BI-style 117%. Pivot v2 supports
    # per-metric columnFormats, so the semantic value remains a ratio.
    assert '"columnFormats": {' in bootstrap
    assert 'item["label"]: item.get("d3Format")' in bootstrap
    assert 'formatted_metric("Markup",' in bootstrap
    assert '".2%"' in bootstrap
    assert "filtered-source-chart:" in validator


def test_detail_analysis_matches_power_bi_dax_contract_and_uses_raw_status_denominator():
    bootstrap = read("superset/bootstrap_panorama.py")
    validator = read("superset/validate_panorama_details.py")

    # Power BI current-snapshot formulas.
    assert "def detail_semantic_sql(group_column: str)" in bootstrap
    assert "SUM(COALESCE(h.status_item_geral,0))::float8 AS status_sum" in bootstrap
    assert "(c.rupture_sum/NULLIF(c.status_sum,0))::float8 AS rupture_value" in bootstrap
    assert "(c.isv_sum/NULLIF(c.status_sum,0))::float8 AS isv_value" in bootstrap
    assert "SUM(COALESCE(h.avg_sales_price,0)) FILTER (WHERE h.faturamento>0)" in bootstrap
    assert "(m.price_sum/m.price_count)*m.conversion_factor" in bootstrap
    assert "ELSE m.loss_qty_sum*m.conversion_factor END::float8 AS osa_loss_value" in bootstrap

    # ROI Anual is SUMX(month, ROI) over the trailing 12-month window,
    # not current ROI * 12.
    assert "SUM(r.roi_value) FILTER" in bootstrap
    assert "r.data > l.latest_data - INTERVAL '12 months'" in bootstrap
    assert "1200.0 *" in bootstrap  # legacy P dict remains for unrelated callers
    assert 'formatted_metric("ROI anual", "MAX(roi_annual_value)", ".2%")' in bootstrap

    # All five visual tabs now use governed virtual datasets rather than the
    # former latest-only physical table.
    for dimension in ("regiao", "rede", "hierarquia_1", "item", "activity_level"):
        assert f'nr_panorama_detail_{{column}}' in bootstrap
    assert "detail_table_params(detail_dataset, column, 20)" in bootstrap

    # Percent display metadata is explicit.
    for metric in ("Markup", "ROI", "ROI anual", "OSA", "Ruptura", "Item sem venda"):
        assert f'"{metric}": {{"d3NumberFormat": ".2%"}}' in bootstrap

    # Runtime gate independently queries fato_historico and ChartData.
    assert "gold.fato_historico" in validator
    assert "ChartDataCommand" in validator
    assert "status_item_geral" in validator
    assert "SUM(roi_value)" in validator
    assert "source-chart:" in validator
