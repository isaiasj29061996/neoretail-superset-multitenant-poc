import ast
from pathlib import Path

from panorama_contract_sources import read_panorama

import pytest
from jinja2 import Environment


ROOT = Path(__file__).resolve().parents[2]


def read(path):
    if path == "superset/bootstrap_panorama.py":
        return read_panorama('inventory', 'osa', 'gaps', 'filters', 'layout')
    return (ROOT / path).read_text(encoding="utf-8")


def test_giro_roi_matches_report_and_tmdl_contracts():
    bootstrap = read("superset/bootstrap_panorama.py")
    assert 'labels="Estoque Preço Custo|% ROI|Giro"' in bootstrap
    assert 'styles="bar|line|line"' in bootstrap
    assert 'formats="currency|percent|number"' in bootstrap
    assert 'giro_roi_semantics = "direct_average:0:1|roi:1:3|weighted_average:4:2"' in bootstrap
    assert 'summary_labels="U3M|Anual|U3M"' in bootstrap
    assert 'metric_summary_modes="u3m|annual12|u3m"' in bootstrap
    assert 'timeline_zero_blank_indices="1"' in bootstrap
    assert 'add("giro_roi_mensal", monthly_inventory' in bootstrap
    assert 'add("giro_roi_semanal", weekly_inventory_card' in bootstrap


def test_giro_semantics_preserve_monthly_positive_filter_and_latest_week_blank():
    mart = read("analytics-db/marts/43_panorama_inventory_semantic.sql")
    compact = "".join(mart.split())
    assert "SUM(f.giro)FILTER(WHEREf.giro>0)::doubleprecisionASgiro_num" in compact
    assert "COUNT(f.giro)FILTER(WHEREf.giro>0)::bigintASgiro_den" in compact
    assert "CASEWHENw.cd_week=w.latest_cd_weekTHENNULLELSEw.giro_num_rawEND" in compact
    assert "CASEWHENw.cd_week=w.latest_cd_weekTHENNULLELSEw.giro_den_rawEND" in compact


def test_roi_is_recomputed_from_sellout_cost_and_stock_cost():
    bootstrap = read("superset/bootstrap_panorama.py")
    transform = read("superset/frontend-plugin/plugin-chart-neoretail-kpi/src/transformProps.js")
    assert 'metric("Venda sell out", "SUM(sellout_sum)")' in bootstrap
    assert 'metric("Venda custo", "SUM(sales_cost_sum)")' in bootstrap
    assert 'metric("Estoque custo ROI", "SUM(stock_cost_sum)")' in bootstrap
    assert "100 * (numerator - denominator) / stockCost" in transform
    assert "if (numerator === 0 || denominator === 0) return [0]" in transform


def test_roi_annual_summary_and_zero_blank_chart_are_explicit():
    bootstrap = read("superset/bootstrap_panorama.py")
    transform = read("superset/frontend-plugin/plugin-chart-neoretail-kpi/src/transformProps.js")
    control = read("superset/frontend-plugin/plugin-chart-neoretail-kpi/src/controlPanel.js")
    renderer = read("superset/frontend-plugin/plugin-chart-neoretail-kpi/src/NeoRetailKpi.jsx")
    assert "metric_summary_modes" in control
    assert "summary_labels" in control
    assert "timeline_zero_blank_indices" in control
    assert "mode === 'annual12'" in transform
    assert "timelineZeroBlankIndices.has(index) && value === 0 ? null : value" in transform
    assert "summaryLabels?.[index] || 'U3M'" in renderer
    assert 'summary_labels="U3M|Anual|U3M"' in bootstrap


def test_osa_uses_exact_denominators_from_tmdl():
    bootstrap = read("superset/bootstrap_panorama.py")
    assert 'osa_semantics = "one_minus_ratio:0:2|ratio_percent:2:2|ratio_percent:4:2"' in bootstrap
    assert 'metric("OSA problemas", "SUM(osa_problem_sum)")' in bootstrap
    assert 'metric("OSA ativos", "SUM(osa_active_sum)")' in bootstrap
    assert 'metric("Ruptura numerador", "SUM(rupture_sum)")' in bootstrap
    assert 'metric("Ruptura denominador", "SUM(status_sum)")' in bootstrap
    assert 'metric("ISV numerador", "SUM(isv_sum)")' in bootstrap
    assert 'metric("ISV denominador", "SUM(status_sum)")' in bootstrap
    assert 'labels="% OSA|% Ruptura|% ISV"' in bootstrap
    assert 'styles="line|line|line"' in bootstrap


def test_osa_monthly_and_weekly_are_single_cards_with_thirteen_periods():
    bootstrap = read("superset/bootstrap_panorama.py")
    assert 'add("osa_mensal", monthly_inventory' in bootstrap
    assert 'add("osa_semanal", weekly_inventory_card' in bootstrap
    assert bootstrap.count("timeline_limit=13") >= 8
    assert 'summary_query_scope="summary"' in bootstrap
    assert 'timeline_query_scope="timeline"' in bootstrap


def test_gap_uses_lastnonblank_serving_marts_and_u3m_average():
    mart = read("analytics-db/marts/43_panorama_inventory_semantic.sql")
    bootstrap = read("superset/bootstrap_panorama.py")
    compact = "".join(mart.split())
    assert "MAX(data)FILTER(WHEREtvdISNOTNULL)AStvd_date" in compact
    assert "MAX(data)FILTER(WHEREivdISNOTNULL)ASivd_date" in compact
    assert "gold.nr_panorama_gap_monthly_default" in mart
    assert "gold.nr_panorama_gap_weekly_card_default" in mart
    assert 'gap_semantics = "direct_average:0:1|direct_average:1:1"' in bootstrap
    assert 'labels="TVD - Risco|IVD - Excesso"' in bootstrap
    assert 'add("gap_mensal", gap_monthly' in bootstrap
    assert 'add("gap_semanal", gap_weekly_card' in bootstrap


def test_certified_tabs_use_physical_serving_defaults():
    bootstrap = read("superset/bootstrap_panorama.py")
    mart = read("analytics-db/marts/43_panorama_inventory_semantic.sql")
    for name in (
        "nr_panorama_inventory_monthly_default",
        "nr_panorama_inventory_weekly_card_default",
        "nr_panorama_gap_monthly_default",
        "nr_panorama_gap_weekly_card_default",
    ):
        assert name in mart
        assert name in bootstrap


def test_inventory_tabs_keep_report_layout_names():
    bootstrap = read("superset/bootstrap_panorama.py")
    assert '(("Estoque", "stock"), ("Giro x ROI", "giro_roi"), ("OSA", "osa"), ("Falta x Excesso", "gap"))' in bootstrap


def test_inventory_datasets_are_in_native_filter_scope():
    bootstrap = read("superset/bootstrap_panorama.py")
    for dataset in ("monthly_inventory.id", "weekly_inventory_card.id", "gap_monthly.id", "gap_weekly_card.id"):
        assert dataset in bootstrap


def test_monthly_osa_status_denominator_comes_from_fato_historico():
    mart = read("analytics-db/marts/43_panorama_inventory_semantic.sql")
    bootstrap = read("superset/bootstrap_panorama.py")
    assert "FROM gold.fato_historico f" in mart
    assert "SUM(COALESCE(f.status_item_geral,0))::double precision AS status_sum" in mart
    assert "f.status_item_geral," in bootstrap
    assert "FROM gold.fato_historico f" in bootstrap
    assert "SUM(COALESCE(status_item_geral,0))::float8 AS status_sum" in bootstrap


def weekly_inventory_template():
    # Execute the SQL generator without importing the Superset application.
    namespace = {}
    for path, names in (
        ("superset/neoretail_bootstrap/core/filters.py", {"_jinja_filter_predicates"}),
        ("superset/neoretail_bootstrap/panorama/inventory.py", {"weekly_inventory_card_semantic_sql"}),
    ):
        tree = ast.parse(read(path))
        nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
        exec(compile(ast.Module(body=nodes, type_ignores=[]), path, "exec"), namespace)
    columns = ("rede", "bandeira", "uf", "cidade", "tipo_local", "loja", "regiao",
               "item", "descricao_marca", "hierarquia_1", "hierarquia_2", "hierarquia_3",
               "tp_activity_level")
    namespace["WEEKLY_FILTER_COLUMNS"] = columns
    return namespace["weekly_inventory_card_semantic_sql"](), columns


def test_filtered_weekly_inventory_summary_uses_governed_detail_and_valid_aliases():
    sql, columns = weekly_inventory_template()
    environment = Environment()
    environment.filters["where_in"] = lambda values: "('selected')"
    for column in columns:
        for operator in ("IN", "NOT IN"):
            rendered = environment.from_string(sql).render(
                get_filters=lambda name, **kwargs: (
                    [{"op": operator, "val": ["selected"]}] if name == column else []
                ),
            )
            monthly = rendered.split("monthly_filtered AS (", 1)[1].split("), monthly AS (", 1)[0]
            weekly = rendered.split("weekly_filtered AS (", 1)[1].split("), ranked_weeks AS (", 1)[0]
            assert "FROM gold.nr_panorama_inventory_weekly_detail w" in weekly
            assert f"AND w.{column} {operator} ('selected')" in weekly
            for invalid_alias in ("l", "i", "h", "f"):
                assert f"{invalid_alias}.{column}" not in weekly
            assert "FROM gold.nr_panorama_comparison_history_detail f" in monthly
            assert f"AND f.{column} {operator} ('selected')" in monthly
            assert "l." not in monthly and "i." not in monthly and "h." not in monthly
            assert "nr_overview_history" not in monthly


@pytest.mark.parametrize("column,operator,value", [
    ("uf", "IN", "RJ"),
    ("uf", "NOT IN", "RJ"),
    ("item", "IN", "item-test"),
    ("item", "NOT IN", "item-test"),
])
def test_weekly_inventory_filter_has_no_missing_dimension_alias(column, operator, value):
    sql, _ = weekly_inventory_template()
    environment = Environment()
    environment.filters["where_in"] = lambda values: "(" + ", ".join(
        "'" + item.replace("'", "''") + "'" for item in values
    ) + ")"
    rendered = environment.from_string(sql).render(
        get_filters=lambda name, **kwargs: (
            [{"op": operator, "val": [value]}] if name == column else []
        ),
    )
    weekly = rendered.split("weekly_filtered AS (", 1)[1].split("), ranked_weeks AS (", 1)[0]
    monthly = rendered.split("monthly_filtered AS (", 1)[1].split("), monthly AS (", 1)[0]
    assert "FROM gold.nr_panorama_inventory_weekly_detail w" in weekly
    assert f"AND w.{column} {operator} ('{value}')" in weekly
    assert "FROM gold.nr_panorama_comparison_history_detail f" in monthly
    assert f"AND f.{column} {operator} ('{value}')" in monthly
    for invalid_alias in ("l", "i", "h"):
        assert f"{invalid_alias}.{column}" not in rendered
