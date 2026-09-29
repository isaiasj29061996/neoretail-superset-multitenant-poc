"""Reconcile Panorama stock evolution against the Power BI DAX contract."""
from __future__ import annotations

import json
import math

from flask import g
from flask_login import login_user
from sqlalchemy import text
from superset.app import create_app

from profile_dashboard_performance import build_queries

CUSTOMER_ID = 142
DASHBOARD = "neoretail-v9-panorama-industria"

MONTHLY_SOURCE = text("""
WITH monthly AS (
  SELECT
    f.mes_ano::date AS data,
    f.id_customer,
    SUM(COALESCE(f.estoque_medio,0) * COALESCE(f.avg_price_cost,0))::float8 AS stock_cost_sum,
    SUM(COALESCE(f.estoque_unidades,0))::float8 AS stock_qty_base
  FROM gold.fato_historico f
  WHERE f.id_customer=:customer
  GROUP BY f.mes_ano,f.id_customer
), factor AS (
  SELECT
    f.mes_ano::date AS data,
    MAX(c.conversion_rate)::float8 AS conversion_factor
  FROM gold.fato_historico f
  JOIN gold.dim_conversao c
    ON c.id_customer=f.id_customer
   AND c.id_item::text=f.id_item::text
   AND c.nm_measure=:measure
  WHERE f.id_customer=:customer
  GROUP BY f.mes_ano
)
SELECT
  m.data,
  m.stock_cost_sum,
  (m.stock_qty_base * f.conversion_factor)::float8 AS stock_qty_sum
FROM monthly m
JOIN factor f USING(data)
ORDER BY m.data
""")

WEEKLY_SOURCE = text("""
WITH latest AS (
  SELECT cd_week
  FROM gold.fato_semanal
  WHERE id_customer=:customer
  GROUP BY cd_week
  ORDER BY cd_week DESC
  LIMIT 13
), weekly AS (
  SELECT
    f.id_time::date AS data,
    MAX(f.cd_week) AS cd_week,
    SUM(COALESCE(f.estoque_medio,0) * COALESCE(f.avg_price_cost,0))::float8 AS stock_cost_sum,
    SUM(COALESCE(f.estoque_unidades,0))::float8 AS stock_qty_base
  FROM gold.fato_semanal f
  JOIN latest l USING(cd_week)
  WHERE f.id_customer=:customer
  GROUP BY f.id_time
), factor AS (
  SELECT
    f.id_time::date AS data,
    MAX(c.conversion_rate)::float8 AS conversion_factor
  FROM gold.fato_semanal f
  JOIN latest l USING(cd_week)
  JOIN gold.dim_conversao c
    ON c.id_customer=f.id_customer
   AND c.id_item::text=f.id_item::text
   AND c.nm_measure=:measure
  WHERE f.id_customer=:customer
  GROUP BY f.id_time
)
SELECT
  w.data,
  w.cd_week,
  w.stock_cost_sum,
  (w.stock_qty_base * f.conversion_factor)::float8 AS stock_qty_sum
FROM weekly w
JOIN factor f USING(data)
ORDER BY w.data
""")

NON_UNIT_MEASURE = text("""
SELECT c.nm_measure
FROM gold.dim_conversao c
WHERE c.id_customer=:customer
GROUP BY c.nm_measure
HAVING MAX(c.conversion_rate) <> 1
ORDER BY c.nm_measure
LIMIT 1
""")


def close(left, right):
    if left is None or right is None:
        return left is None and right is None
    return math.isclose(float(left), float(right), rel_tol=1e-9, abs_tol=1e-7)


def execute(factory, command, chart, filters):
    form = json.loads(chart.params)
    queries, _ = build_queries(form)
    for query in queries:
        query["filters"] = [*query.get("filters", []), *filters]
    g.form_data = {"extra_filters": filters}
    result = command(factory.create(
        datasource={"id": chart.datasource_id, "type": "table"},
        queries=queries,
        form_data={**form, "force": True, "extra_filters": filters},
    )).run()
    g.form_data = {}
    responses = result["queries"]
    for response in responses:
        if response.get("error"):
            raise AssertionError(response["error"])
    return responses


def rows_by_date(rows):
    return {str(row["data"])[:10]: row for row in rows}


def compare(expected, actual, cost_label, qty_label, *, context):
    actual_dates = rows_by_date(actual)
    for row in expected:
        key = str(row["data"])[:10]
        got = actual_dates.get(key)
        if got is None:
            raise AssertionError(f"{context}: missing period {key}")
        if not close(row["stock_cost_sum"], got.get(cost_label)):
            raise AssertionError({
                "context": context,
                "period": key,
                "metric": cost_label,
                "expected": row["stock_cost_sum"],
                "actual": got.get(cost_label),
            })
        if not close(row["stock_qty_sum"], got.get(qty_label)):
            raise AssertionError({
                "context": context,
                "period": key,
                "metric": qty_label,
                "expected": row["stock_qty_sum"],
                "actual": got.get(qty_label),
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
        monthly_name = "[Panorama] Evolutivo de estoque — Estoque mensal"
        weekly_name = "[Panorama] Evolutivo de estoque — Estoque semanal"
        monthly_chart = charts[monthly_name]
        weekly_chart = charts[weekly_name]

        expected_semantics = "direct_average:0:1|direct_average:1:1"
        for name, chart in ((monthly_name, monthly_chart), (weekly_name, weekly_chart)):
            params = json.loads(chart.params)
            if params.get("metric_semantics") != expected_semantics:
                raise AssertionError(f"{name}: metric_semantics diverged")
            if int(params.get("summary_count", -1)) != 2:
                raise AssertionError(f"{name}: summary_count diverged")
            if int(params.get("timeline_limit", -1)) != 13:
                raise AssertionError(f"{name}: timeline_limit diverged")
            if params.get("metric_labels") != "Estoque Preço Custo|Estoque Quantidade":
                raise AssertionError(f"{name}: metric labels diverged")
            if params.get("metric_formats") != "currency|quantity":
                raise AssertionError(f"{name}: metric formats diverged")

        weekly_params = json.loads(weekly_chart.params)
        if weekly_params.get("timeline_query_scope") != "timeline":
            raise AssertionError("weekly stock timeline scope diverged")
        if weekly_params.get("summary_query_scope") != "summary":
            raise AssertionError("weekly stock summary scope diverged")

        database = monthly_chart.table.database
        factory = QueryContextFactory()
        cost_label = "Estoque preço custo"
        qty_label = "Estoque quantidade"

        with database.get_sqla_engine().connect() as connection:
            candidate = connection.execute(
                NON_UNIT_MEASURE, {"customer": CUSTOMER_ID}
            ).scalar()
            measures = ["unidade"]
            if candidate and candidate not in measures:
                measures.append(candidate)

            report = {"tenant": CUSTOMER_ID, "measures": {}, "charts": {}}
            for measure in measures:
                params = {"customer": CUSTOMER_ID, "measure": measure}
                monthly_expected = [
                    dict(row._mapping)
                    for row in connection.execute(MONTHLY_SOURCE, params)
                ]
                weekly_expected = [
                    dict(row._mapping)
                    for row in connection.execute(WEEKLY_SOURCE, params)
                ]

                filters = [
                    {"col": "id_customer", "op": "IN", "val": [CUSTOMER_ID]},
                    {"col": "nm_measure", "op": "IN", "val": [measure]},
                ]
                monthly_responses = execute(
                    factory, ChartDataCommand, monthly_chart, filters
                )
                weekly_responses = execute(
                    factory, ChartDataCommand, weekly_chart, filters
                )

                if len(monthly_responses) != 1:
                    raise AssertionError("monthly stock must use one query")
                if len(weekly_responses) != 2:
                    raise AssertionError(
                        "weekly stock must use one slice with timeline + monthly summary"
                    )

                monthly_data = monthly_responses[0].get("data") or []
                weekly_data = weekly_responses[0].get("data") or []
                summary_data = weekly_responses[1].get("data") or []

                if len(weekly_data) != 13:
                    raise AssertionError(
                        f"weekly stock expected 13 periods, got {len(weekly_data)}"
                    )

                compare(
                    monthly_expected,
                    monthly_data,
                    cost_label,
                    qty_label,
                    context=f"monthly/{measure}",
                )
                compare(
                    weekly_expected,
                    weekly_data,
                    cost_label,
                    qty_label,
                    context=f"weekly/{measure}",
                )
                compare(
                    monthly_expected,
                    summary_data,
                    cost_label,
                    qty_label,
                    context=f"weekly-summary/{measure}",
                )
                report["measures"][measure] = {
                    "monthly_rows": len(monthly_data),
                    "weekly_rows": len(weekly_data),
                    "summary_rows": len(summary_data),
                }

        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
