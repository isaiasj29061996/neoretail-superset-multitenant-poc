"""Reconcile AP_KPI_INDUSTRIA source -> compact mart -> Superset ChartData."""
from __future__ import annotations

import json
import math
from time import perf_counter

from flask import g
from flask_login import login_user
from sqlalchemy import text
from superset.app import create_app

from profile_dashboard_performance import build_queries


CUSTOMER_ID = 142
YEAR = 2026
DASHBOARD = "neoretail-v9-panorama-industria"
SCOPES = {
    "Região": ("region", "regiao", "l.regiao"),
    "Varejo": ("retail", "rede", "l.rede"),
    "Hierarquia de item": ("hierarchy", "hierarquia_1", "i.hierarquia_1"),
}
OPTIONS = (
    ("Venda R$", "sales_value"),
    ("Estoque qtd", "stock_quantity"),
    ("%OSA", "osa_percent"),
    ("%Ruptura", "rupture_percent"),
    ("%Item sem Venda", "no_sales_percent"),
    ("Cobertura de estoque", "coverage"),
    ("Giro de estoque", "inventory_turnover"),
    ("%ROI", "roi_percent"),
    ("TVD - Pré-Ruptura", "tvd"),
    ("IVD - Excesso de estoque", "ivd"),
)


def close(left, right):
    left_blank = left is None or (isinstance(left, float) and math.isnan(left))
    right_blank = right is None or (isinstance(right, float) and math.isnan(right))
    if left_blank or right_blank:
        return left_blank and right_blank
    return math.isclose(float(left), float(right), rel_tol=1e-8, abs_tol=1e-5)


def compare(expected, actual, context):
    if expected.keys() != actual.keys():
        raise AssertionError({
            "context": context,
            "missing": list(expected.keys() - actual.keys())[:10],
            "unexpected": list(actual.keys() - expected.keys())[:10],
        })
    for row_key, wanted in expected.items():
        got = actual[row_key]
        if not close(wanted, got):
            raise AssertionError({
                "context": context, "row": row_key,
                "expected": wanted, "actual": got,
            })


def history_source_sql(dimension_sql, extra=""):
    return text(f"""
WITH monthly AS (
  SELECT h.mes_ano::date AS data,{dimension_sql}::text AS dimension_1,
    SUM(COALESCE(h.faturamento,0))::float8 AS sellout_sum,
    SUM(COALESCE(h.volume_unidades,0))::float8 AS volume_sum,
    SUM(h.avg_sales_price)::float8 AS price_sum,
    COUNT(h.avg_sales_price)::bigint AS price_count,
    SUM(COALESCE(h.volume_unidades,0)*COALESCE(h.avg_price_cost,0))::float8 AS sales_cost_sum,
    SUM(COALESCE(h.estoque_medio,0)*COALESCE(h.avg_price_cost,0))::float8 AS stock_cost_sum,
    SUM(COALESCE(h.estoque_unidades,0))::float8 AS stock_qty_sum,
    SUM(COALESCE(h.demanda_media,0))::float8 AS demand_sum,
    SUM(h.giro) FILTER (WHERE h.giro>0)::float8 AS giro_sum,
    COUNT(h.giro) FILTER (WHERE h.giro>0)::bigint AS giro_count,
    SUM(COALESCE(h.qtd_problemas_osa,0))::float8 AS osa_problem_sum,
    SUM(COALESCE(h.qtd_item_ativo_osa,0))::float8 AS osa_active_sum,
    SUM(COALESCE(h.rup,0))::float8 AS rupture_sum,
    SUM(COALESCE(h.status_item_geral,0))::float8 AS status_sum,
    SUM(COALESCE(h.est_virtual,0))::float8 AS isv_sum
  FROM gold.fato_historico h
  LEFT JOIN gold.dim_local l ON l.id_customer=h.id_customer AND l.id_location=h.id_location
  LEFT JOIN gold.dim_itens i ON i.id_customer=h.id_customer AND i.id_item=h.id_item
  WHERE h.id_customer=:customer AND EXTRACT(YEAR FROM h.mes_ano::date)=:year {extra}
  GROUP BY h.mes_ano,{dimension_sql}
), annual AS (
  SELECT dimension_1,
    SUM(sellout_sum)::float8 AS sellout_sum,SUM(volume_sum)::float8 AS volume_sum,
    SUM(price_sum)::float8 AS price_sum,SUM(price_count)::bigint AS price_count,
    SUM(sales_cost_sum)::float8 AS sales_cost_sum,SUM(stock_cost_sum)::float8 AS stock_cost_sum,
    SUM(stock_qty_sum)::float8 AS stock_qty_period_sum,SUM(demand_sum)::float8 AS demand_sum,
    SUM(giro_sum)::float8 AS giro_sum,SUM(giro_count)::bigint AS giro_count,
    SUM(osa_problem_sum)::float8 AS osa_problem_sum,SUM(osa_active_sum)::float8 AS osa_active_sum,
    SUM(rupture_sum)::float8 AS rupture_sum,SUM(status_sum)::float8 AS status_sum,
    SUM(isv_sum)::float8 AS isv_sum,
    (ARRAY_AGG(stock_qty_sum ORDER BY data DESC))[1]::float8 AS latest_stock_qty
  FROM monthly GROUP BY dimension_1
)
SELECT dimension_1,
  CASE WHEN sellout_sum>0 THEN sellout_sum WHEN price_count>0 THEN volume_sum*(price_sum/price_count) END::float8 AS sales_value,
  latest_stock_qty::float8 AS stock_quantity,
  (100.0*(1-osa_problem_sum/NULLIF(osa_active_sum,0)))::float8 AS osa_percent,
  (100.0*rupture_sum/NULLIF(status_sum,0))::float8 AS rupture_percent,
  (100.0*isv_sum/NULLIF(status_sum,0))::float8 AS no_sales_percent,
  (stock_qty_period_sum/NULLIF(demand_sum,0))::float8 AS coverage,
  (giro_sum/NULLIF(giro_count,0))::float8 AS inventory_turnover,
  (CASE WHEN sellout_sum=0 OR sales_cost_sum=0 THEN 0 ELSE 100.0*(sellout_sum-sales_cost_sum)/NULLIF(stock_cost_sum,0) END)::float8 AS roi_percent
FROM annual
""")


def history_mart_sql(scope):
    return text("""
SELECT dimension_1,sales_value,stock_quantity,osa_percent,rupture_percent,
       no_sales_percent,coverage,inventory_turnover,roi_percent
FROM gold.nr_panorama_kpi_dimension_history_default
WHERE id_customer=:customer AND comparison_year=:year
  AND comparison_scope=:scope AND drill_level=0
""")


def gap_source_sql(dimension_sql, extra=""):
    return text(f"""
WITH daily AS (
  SELECT h.id_time::date AS data,{dimension_sql}::text AS dimension_1,
         SUM(h.tvd_simplificado)::float8 AS tvd,
         SUM(h.ivd_simplificado)::float8 AS ivd
  FROM gold.fato_ivd_tvd h
  LEFT JOIN gold.dim_local l ON l.id_customer=h.id_customer AND l.id_location=h.id_location
  LEFT JOIN gold.dim_itens i ON i.id_customer=h.id_customer AND i.id_item=h.id_item
  WHERE h.id_customer=:customer AND EXTRACT(YEAR FROM h.id_time::date)=:year {extra}
  GROUP BY h.id_time,{dimension_sql}
)
SELECT DISTINCT ON (dimension_1) dimension_1,tvd,ivd
FROM daily ORDER BY dimension_1,data DESC
""")


def gap_mart_sql(scope):
    return text("""
SELECT dimension_1,tvd,ivd
FROM gold.nr_panorama_kpi_dimension_gap_default
WHERE id_customer=:customer AND comparison_year=:year
  AND comparison_scope=:scope AND drill_level=0
""")


def mapped(rows, metric):
    return {row["dimension_1"]: row[metric] for row in rows}


def execute_chart(factory, command, chart, selector, extra_filters=()):
    form = json.loads(chart.params)
    queries, _ = build_queries(form)
    filters = [
        {"col": "id_customer", "op": "IN", "val": [CUSTOMER_ID]},
        {"col": "comparison_year", "op": "IN", "val": [YEAR]},
        {"col": "comparison_kpi", "op": "IN", "val": [selector]},
        {"col": "nm_measure", "op": "IN", "val": ["unidade"]},
        *extra_filters,
    ]
    for query in queries:
        query["filters"] = [*query.get("filters", []), *filters]
    g.form_data = {"extra_filters": filters}
    started = perf_counter()
    result = command(factory.create(
        datasource={"id": chart.datasource_id, "type": "table"},
        queries=queries,
        form_data={**form, "force": True, "extra_filters": filters},
    )).run()
    elapsed = (perf_counter() - started) * 1000
    g.form_data = {}
    response = result["queries"][0]
    if response.get("error"):
        raise AssertionError({"chart": chart.slice_name, "selector": selector, "error": response["error"]})
    return response.get("data") or [], elapsed


def main():
    app = create_app()
    with app.test_request_context("/"):
        from superset import db, security_manager
        from superset.commands.chart.data.get_data_command import ChartDataCommand
        from superset.common.query_context_factory import QueryContextFactory
        from superset.connectors.sqla.models import SqlaTable
        from superset.models.dashboard import Dashboard

        admin = security_manager.find_user(username="admin") or db.session.query(
            security_manager.user_model
        ).first()
        login_user(admin)
        g.user = admin
        dashboard = db.session.query(Dashboard).filter(Dashboard.slug == DASHBOARD).one()
        charts = {chart.slice_name: chart for chart in dashboard.slices}
        titles = {label: f"[Panorama] Comparativo de KPIs — {label}" for label in SCOPES}
        missing = [title for title in titles.values() if title not in charts]
        if missing:
            raise AssertionError({"missing_charts": missing})

        factory = QueryContextFactory()
        database = charts[next(iter(titles.values()))].table.database
        report = {"tenant": CUSTOMER_ID, "year": YEAR, "selectors": list(dict(OPTIONS)), "scopes": {}}

        filter_dataset = db.session.query(SqlaTable).filter(
            SqlaTable.table_name == "nr_panorama_kpi_filter_options"
        ).one()
        selector_result = ChartDataCommand(factory.create(
            datasource={"id": filter_dataset.id, "type": "table"},
            queries=[{
                "columns": ["comparison_kpi"],
                "metrics": ["AP KPI ordem"],
                "filters": [{"col": "comparison_year", "op": "IN", "val": [YEAR]}],
                "orderby": [["AP KPI ordem", True]],
                "row_limit": 100,
                "time_range": "No filter",
            }],
            form_data={"force": True, "native_filter_id": "NATIVE_FILTER-panorama-kpi-selector"},
        )).run()["queries"][0]
        if selector_result.get("error"):
            raise AssertionError({"selector_error": selector_result["error"]})
        selector_order = [row["comparison_kpi"] for row in selector_result.get("data") or []]
        expected_order = [label for label, _ in OPTIONS]
        if selector_order != expected_order:
            raise AssertionError({"selector_order": selector_order, "expected": expected_order})
        report["selector_order"] = selector_order

        with database.get_sqla_engine() as engine, engine.connect() as connection:
            for label, (scope, first, source_dimension) in SCOPES.items():
                source_history = list(connection.execute(
                    history_source_sql(source_dimension), {"customer": CUSTOMER_ID, "year": YEAR}
                ).mappings())
                mart_history = list(connection.execute(
                    history_mart_sql(scope), {"customer": CUSTOMER_ID, "year": YEAR, "scope": scope}
                ).mappings())
                source_gap = list(connection.execute(
                    gap_source_sql(source_dimension), {"customer": CUSTOMER_ID, "year": YEAR}
                ).mappings())
                mart_gap = list(connection.execute(
                    gap_mart_sql(scope), {"customer": CUSTOMER_ID, "year": YEAR, "scope": scope}
                ).mappings())
                for _, metric in OPTIONS[:8]:
                    compare(mapped(source_history, metric), mapped(mart_history, metric), f"source-mart:{label}:{metric}")
                for _, metric in OPTIONS[8:]:
                    compare(mapped(source_gap, metric), mapped(mart_gap, metric), f"source-mart:{label}:{metric}")

                chart = charts[titles[label]]
                scope_report = {"source_rows": len(source_history), "gap_rows": len(source_gap), "charts": {}}
                for selector, metric in OPTIONS:
                    rows, elapsed = execute_chart(factory, ChartDataCommand, chart, selector)
                    root_rows = [row for row in rows if int(row.get("drill_level", -1)) == 0]
                    actual = {row.get(first): row.get("KPI valor") for row in root_rows}
                    expected_rows = source_gap if metric in {"tvd", "ivd"} else source_history
                    compare(mapped(expected_rows, metric), actual, f"source-chart:{label}:{selector}")
                    scope_report["charts"][selector] = {
                        "rows": len(rows), "root_rows": len(root_rows),
                        "elapsed_ms": round(elapsed, 2),
                    }
                report["scopes"][label] = scope_report

            # The fallback must apply a retail filter before aggregating a region.
            rede = connection.execute(text("""
                SELECT rede FROM gold.nr_panorama_comparison_history_detail
                WHERE id_customer=:customer AND rede IS NOT NULL
                GROUP BY rede ORDER BY COUNT(*) DESC LIMIT 1
            """), {"customer": CUSTOMER_ID}).scalar_one()
            source_filtered = list(connection.execute(
                history_source_sql("l.regiao", "AND l.rede=:rede"),
                {"customer": CUSTOMER_ID, "year": YEAR, "rede": rede},
            ).mappings())
            rows, elapsed = execute_chart(
                factory, ChartDataCommand, charts[titles["Região"]], "Venda R$",
                ({"col": "rede", "op": "IN", "val": [rede]},),
            )
            actual = {row.get("regiao"): row.get("KPI valor") for row in rows if int(row.get("drill_level", -1)) == 0}
            compare(mapped(source_filtered, "sales_value"), actual, "filtered-source-chart:Região:Venda R$")
            report["filtered_fallback"] = {"rede": rede, "elapsed_ms": round(elapsed, 2), "rows": len(rows)}

        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
