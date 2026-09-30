from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_ap_kpi_industria_selector_order_and_formats_are_exact():
    bootstrap = read("superset/bootstrap_panorama.py")
    expected = (
        '("Venda R$", "currency")',
        '("Estoque qtd", "quantity")',
        '("%OSA", "percent")',
        '("%Ruptura", "percent")',
        '("%Item sem Venda", "percent")',
        '("Cobertura de estoque", "number")',
        '("Giro de estoque", "number")',
        '("%ROI", "percent")',
        '("TVD - Pré-Ruptura", "currency")',
        '("IVD - Excesso de estoque", "currency")',
    )
    offsets = [bootstrap.index(item) for item in expected]
    assert offsets == sorted(offsets)
    assert "AP_KPI_MERCADO" not in bootstrap
    assert "FATO_MERCADO" not in bootstrap


def test_three_hierarchies_and_layout_position_are_preserved():
    bootstrap = read("superset/bootstrap_panorama.py")
    assert '"region": ("regiao", "uf", "cidade")' in bootstrap
    assert '"retail": ("rede", "bandeira", "loja")' in bootstrap
    assert '"hierarchy": ("hierarquia_1", "descricao_marca", "item")' in bootstrap
    stock = bootstrap.index('"Evolutivo de estoque"')
    kpis = bootstrap.index('"Comparativo de KPIs por dimensão"')
    matrices = bootstrap.index('"Comparativos"', kpis)
    assert stock < kpis < matrices
    assert 'variant="hierarchyrank"' in bootstrap


def test_dynamic_contract_uses_original_measure_components():
    bootstrap = read("superset/bootstrap_panorama.py")
    mart = read("analytics-db/marts/43_panorama_inventory_semantic.sql")
    assert "demanda_media::double precision AS demanda_media" in mart
    assert "CASE WHEN a.sellout_sum>0 THEN a.sellout_sum" in bootstrap
    assert "a.latest_stock_qty*a.latest_conversion_factor" in bootstrap
    assert "100.0*(1-a.osa_problem_sum/NULLIF(a.osa_active_sum,0))" in bootstrap
    assert "100.0*a.rupture_sum/NULLIF(a.status_sum,0)" in bootstrap
    assert "100.0*a.isv_sum/NULLIF(a.status_sum,0)" in bootstrap
    assert "a.stock_qty_period_sum/NULLIF(a.demand_sum,0)" in bootstrap
    assert "a.giro_sum/NULLIF(a.giro_count,0)" in bootstrap
    assert "100.0*(a.sellout_sum-a.sales_cost_sum)/NULLIF(a.stock_cost_sum,0)" in bootstrap
    assert "SUM(o.tvd_simplificado)::float8 AS tvd" in bootstrap
    assert "SUM(o.ivd_simplificado)::float8 AS ivd" in bootstrap


def test_selector_year_measure_and_dimension_filters_are_governed():
    bootstrap = read("superset/bootstrap_panorama.py")
    assert "get_filters('comparison_kpi', remove_filter=True)" in bootstrap
    assert "get_filters('comparison_year', remove_filter=True)" in bootstrap
    assert "get_filters('nm_measure', remove_filter=True)" in bootstrap
    assert '"multiSelect": False' in bootstrap
    assert '"value": ["Venda R$"]' in bootstrap
    assert 'KPI_ORDER_METRIC_NAME = "AP KPI ordem"' in bootstrap
    assert 'expression="MIN(kpi_order)"' in bootstrap
    assert '"sortAscending": True' in bootstrap
    assert 'native_filters.extend(kpi_native_filters(kpi_filter_options.id))' in bootstrap
    assert "*kpi_dimension_dataset_ids" in bootstrap
    assert "_jinja_filter_predicates(\"h\")" in bootstrap
    assert "_jinja_filter_predicates(\"o\")" in bootstrap


def test_percent_format_is_restricted_to_percent_kpis():
    bootstrap = read("superset/bootstrap_panorama.py")
    assert "IN ('%OSA','%Ruptura','%Item sem Venda','%ROI') THEN 'percent'" in bootstrap
    assert "LIKE '%%' THEN 'percent'" not in bootstrap


def test_performance_profiler_executes_hierarchy_rank_as_grouped_query():
    profiler = read("superset/profile_dashboard_performance.py")
    assert '"stackedrank", "hierarchyrank"' in profiler


def test_runtime_gate_reconciles_raw_source_compact_mart_and_chartdata():
    validator = read("superset/validate_panorama_kpi_dimensions.py")
    assert "gold.fato_historico" in validator
    assert "gold.fato_ivd_tvd" in validator
    assert "gold.nr_panorama_kpi_dimension_history_default" in validator
    assert "gold.nr_panorama_kpi_dimension_gap_default" in validator
    assert "ChartDataCommand" in validator
    assert "source-mart:" in validator
    assert "source-chart:" in validator
    assert "filtered-source-chart:" in validator

