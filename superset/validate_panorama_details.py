"""Reconcile Panorama detailed-analysis tables with Power BI DAX semantics.

The gate checks all five tabs against the prejoined Gold history mart, reconciles
the compact detail mart, and then compares the same values with Superset ChartData.  It intentionally uses the
default conversion measure 'unidade', which is the dashboard default.
"""
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
DASHBOARD = "neoretail-v9-panorama-industria"
SCOPES = {
    "Região": ("regiao", "h.regiao"),
    "Rede": ("rede", "h.rede"),
    "Categoria": ("hierarquia_1", "h.hierarquia_1"),
    "Produto": ("item", "h.item"),
    "Nível de atividade": (
        "activity_level",
        """CASE h.tp_activity_level
             WHEN 'F' THEN 'Fast Mover'
             WHEN 'S' THEN 'Slow Mover'
             WHEN 'US' THEN 'Ultra Slow Mover'
             WHEN 'U' THEN 'Ultra Slow Mover'
             WHEN 'N' THEN 'New Mover'
             ELSE COALESCE(h.tp_activity_level, 'Outros')
           END""",
    ),
}
METRICS = (
    "Venda qtd", "Venda sell out", "Venda custo", "Markup", "Preço médio",
    "Estoque custo", "Estoque qtd", "ROI", "ROI anual", "Giro", "OSA",
    "Ruptura", "Item sem venda", "Perda OSA",
)


def close(left, right):
    left_blank = left is None or (isinstance(left, float) and math.isnan(left))
    right_blank = right is None or (isinstance(right, float) and math.isnan(right))
    if left_blank or right_blank:
        return left_blank and right_blank
    return math.isclose(float(left), float(right), rel_tol=1e-8, abs_tol=1e-6)


def expected_sql(column: str, dimension_expr: str):
    # column and expression come exclusively from SCOPES above.
    return text(f"""
WITH latest AS (
  SELECT MAX(data)::date AS latest_data
  FROM gold.nr_panorama_comparison_history_detail
  WHERE id_customer=:customer
), raw AS (
  SELECT
    h.data::date AS data,
    h.id_customer,
    h.id_item::text AS id_item,
    {dimension_expr}::text AS dimension_value,
    h.volume_unidades,h.faturamento,h.estoque_unidades,h.qtd_perda_osa,
    h.rup,h.est_virtual,h.giro,h.qtd_problemas_osa,h.qtd_item_ativo_osa,
    h.status_item_geral,h.avg_sales_price,h.avg_price_cost,h.estoque_medio
  FROM gold.nr_panorama_comparison_history_detail h
  JOIN latest d
    ON h.data::date > d.latest_data - INTERVAL '12 months'
   AND h.data::date <= d.latest_data
  WHERE h.id_customer=:customer
), factor AS (
  SELECT
    r.dimension_value,
    MAX(c.conversion_rate)::float8 AS conversion_factor
  FROM (SELECT DISTINCT dimension_value,id_item FROM raw) r
  LEFT JOIN gold.dim_conversao c
    ON c.id_customer=:customer
   AND c.id_item::text=r.id_item
   AND c.nm_measure='unidade'
  GROUP BY r.dimension_value
), monthly AS (
  SELECT
    r.data,r.dimension_value,MAX(f.conversion_factor)::float8 conversion_factor,
    SUM(COALESCE(r.faturamento,0))::float8 faturamento_sum,
    SUM(COALESCE(r.volume_unidades,0))::float8 volume_sum,
    SUM(COALESCE(r.volume_unidades,0)*COALESCE(r.avg_price_cost,0))::float8 sales_cost_sum,
    SUM(COALESCE(r.estoque_medio,0)*COALESCE(r.avg_price_cost,0))::float8 stock_cost_sum,
    SUM(COALESCE(r.estoque_unidades,0))::float8 stock_units_sum,
    SUM(COALESCE(r.qtd_perda_osa,0))::float8 loss_qty_sum,
    SUM(COALESCE(r.avg_sales_price,0)) FILTER (WHERE r.faturamento>0)::float8 price_sum,
    COUNT(r.avg_sales_price) FILTER (WHERE r.faturamento>0)::bigint price_count,
    SUM(COALESCE(r.giro,0)) FILTER (WHERE r.giro>0)::float8 giro_sum,
    COUNT(r.giro) FILTER (WHERE r.giro>0)::bigint giro_count,
    SUM(COALESCE(r.qtd_problemas_osa,0))::float8 osa_problem_sum,
    SUM(COALESCE(r.qtd_item_ativo_osa,0))::float8 osa_active_sum,
    SUM(COALESCE(r.rup,0))::float8 rupture_sum,
    SUM(COALESCE(r.status_item_geral,0))::float8 status_sum,
    SUM(COALESCE(r.est_virtual,0))::float8 isv_sum
  FROM raw r LEFT JOIN factor f USING (dimension_value)
  GROUP BY r.data,r.dimension_value
), calc AS (
  SELECT m.*,
    CASE WHEN faturamento_sum>0 THEN faturamento_sum
         WHEN conversion_factor IS NOT NULL AND price_count>0
         THEN (volume_sum*conversion_factor)
            *((price_sum/price_count)*conversion_factor)
    END::float8 AS sellout_value,
    (volume_sum*conversion_factor)::float8 AS sales_qty_value,
    CASE WHEN conversion_factor IS NULL OR price_count=0 THEN NULL
         ELSE (price_sum/price_count)*conversion_factor END::float8 AS price_value,
    (stock_units_sum*conversion_factor)::float8 AS stock_qty_value,
    (loss_qty_sum*conversion_factor)::float8 AS osa_loss_value
  FROM monthly m
), ratios AS (
  SELECT c.*,
    CASE WHEN sellout_value IS NULL OR sales_cost_sum=0 THEN 0
         ELSE sellout_value/sales_cost_sum END::float8 AS markup_value,
    CASE WHEN sellout_value IS NULL OR sales_cost_sum=0 THEN 0
         ELSE (sellout_value-sales_cost_sum)/NULLIF(stock_cost_sum,0) END::float8 AS roi_value,
    (giro_sum/NULLIF(giro_count,0))::float8 AS giro_value,
    (1-osa_problem_sum/NULLIF(osa_active_sum,0))::float8 AS osa_value,
    (rupture_sum/NULLIF(status_sum,0))::float8 AS rupture_value,
    (isv_sum/NULLIF(status_sum,0))::float8 AS isv_value
  FROM calc c
), annual AS (
  SELECT dimension_value,SUM(roi_value)::float8 AS roi_annual_value
  FROM ratios GROUP BY dimension_value
), current_rows AS (
  SELECT r.* FROM ratios r CROSS JOIN latest d WHERE r.data=d.latest_data
)
SELECT
  c.dimension_value AS "{column}",
  c.sales_qty_value AS "Venda qtd",
  c.sellout_value AS "Venda sell out",
  c.sales_cost_sum AS "Venda custo",
  c.markup_value AS "Markup",
  c.price_value AS "Preço médio",
  c.stock_cost_sum AS "Estoque custo",
  c.stock_qty_value AS "Estoque qtd",
  c.roi_value AS "ROI",
  a.roi_annual_value AS "ROI anual",
  c.giro_value AS "Giro",
  c.osa_value AS "OSA",
  c.rupture_value AS "Ruptura",
  c.isv_value AS "Item sem venda",
  c.osa_loss_value AS "Perda OSA"
FROM current_rows c
LEFT JOIN annual a USING (dimension_value)
ORDER BY c.dimension_value
""")



def mart_sql(column: str):
    return text(f"""
SELECT
  dimension_value AS "{column}",
  sales_qty_value AS "Venda qtd",
  sellout_value AS "Venda sell out",
  sales_cost_value AS "Venda custo",
  markup_value AS "Markup",
  price_value AS "Preço médio",
  stock_cost_value AS "Estoque custo",
  stock_qty_value AS "Estoque qtd",
  roi_value AS "ROI",
  roi_annual_value AS "ROI anual",
  giro_value AS "Giro",
  osa_value AS "OSA",
  rupture_value AS "Ruptura",
  isv_value AS "Item sem venda",
  osa_loss_value AS "Perda OSA"
FROM gold.nr_panorama_detail_default
WHERE id_customer=:customer
  AND detail_scope=:scope
  AND nm_measure='unidade'
ORDER BY dimension_value
""")



def chart_rows(factory, command, chart):
    form = json.loads(chart.params)
    queries, _ = build_queries(form)
    filters = [
        {"col": "id_customer", "op": "IN", "val": [CUSTOMER_ID]},
        {"col": "nm_measure", "op": "IN", "val": ["unidade"]},
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
    elapsed_ms = (perf_counter() - started) * 1000
    query = result["queries"][0]
    if query.get("error"):
        raise AssertionError({"chart": chart.slice_name, "error": query["error"]})
    return query.get("data") or [], elapsed_ms


def compare(expected, actual, column, context):
    left = {row[column]: row for row in expected}
    right = {row[column]: row for row in actual}
    if left.keys() != right.keys():
        raise AssertionError({
            "context": context,
            "missing": list(left.keys() - right.keys())[:10],
            "unexpected": list(right.keys() - left.keys())[:10],
            "expected_rows": len(left),
            "actual_rows": len(right),
        })
    for key, wanted in left.items():
        got = right[key]
        for metric in METRICS:
            if not close(wanted.get(metric), got.get(metric)):
                raise AssertionError({
                    "context": context, "dimension": key, "metric": metric,
                    "expected": wanted.get(metric), "actual": got.get(metric),
                })


def main():
    app = create_app()
    with app.test_request_context("/"):
        from superset import db, security_manager
        from superset.commands.chart.data.get_data_command import ChartDataCommand
        from superset.common.query_context_factory import QueryContextFactory
        from superset.models.dashboard import Dashboard

        admin = security_manager.find_user(username="admin") or db.session.query(
            security_manager.user_model
        ).first()
        login_user(admin)
        g.user = admin

        dashboard = db.session.query(Dashboard).filter(Dashboard.slug == DASHBOARD).one()
        charts = {chart.slice_name: chart for chart in dashboard.slices}
        factory = QueryContextFactory()
        report = {"tenant": CUSTOMER_ID, "tabs": {}}

        first = charts["[Panorama] Análise detalhada — Região"]
        with first.table.database.get_sqla_engine() as engine, engine.connect() as connection:
            for label, (column, expression) in SCOPES.items():
                title = f"[Panorama] Análise detalhada — {label}"
                if title not in charts:
                    raise AssertionError({"missing_chart": title})
                expected = list(connection.execute(
                    expected_sql(column, expression), {"customer": CUSTOMER_ID}
                ).mappings())
                mart = list(connection.execute(
                    mart_sql(column),
                    {"customer": CUSTOMER_ID, "scope": column},
                ).mappings())
                compare(expected, mart, column, f"source-mart:{label}")
                actual, elapsed = chart_rows(factory, ChartDataCommand, charts[title])
                compare(expected, actual, column, f"source-chart:{label}")
                report["tabs"][label] = {
                    "rows": len(actual),
                    "mart_rows": len(mart),
                    "elapsed_ms": round(elapsed, 2),
                    "metrics": list(METRICS),
                }

        print(json.dumps(report, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
