"""Validate Panorama inventory tabs: Giro x ROI, OSA and Falta x Excesso."""
from __future__ import annotations

import json
import math
import os
from pathlib import Path

from flask import g
from flask_login import login_user
from sqlalchemy import text
from superset.app import create_app

from profile_dashboard_performance import build_queries

CUSTOMER_ID = int(os.getenv("NEORETAIL_VALIDATION_CUSTOMER", "142"))
DASHBOARD = "neoretail-v9-panorama-industria"


def close(left, right):
    if left is None or right is None:
        return left is None and right is None
    return math.isclose(float(left), float(right), rel_tol=1e-9, abs_tol=1e-7)


def json_safe(value):
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return value


def safe_ratio(numerator, denominator, *, one_minus=False):
    if numerator is None or denominator in (None, 0):
        return None
    value = float(numerator) / float(denominator)
    return 100 * (1 - value) if one_minus else 100 * value


def roi(sellout, cost, stock_cost):
    if sellout in (None, 0) or cost in (None, 0):
        return 0.0
    if stock_cost in (None, 0):
        return None
    return 100 * (float(sellout) - float(cost)) / float(stock_cost)


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


def assert_chart_params(chart, expected):
    params = json.loads(chart.params)
    for key, value in expected.items():
        if params.get(key) != value:
            raise AssertionError({
                "chart": chart.slice_name,
                "param": key,
                "expected": value,
                "actual": params.get(key),
            })


def require_rows(name, responses, weekly=False):
    if len(responses) != (2 if weekly else 1):
        raise AssertionError(f"{name}: unexpected query count {len(responses)}")
    timeline = responses[0].get("data") or []
    if not timeline:
        raise AssertionError(f"{name}: empty timeline")
    if weekly and len(timeline) != 13:
        raise AssertionError(f"{name}: expected exactly 13 weekly rows, got {len(timeline)}")
    if weekly and not (responses[1].get("data") or []):
        raise AssertionError(f"{name}: monthly summary query is empty")
    return timeline


MONTHLY_SOURCE = text("""
WITH monthly AS (
  SELECT
    f.mes_ano::date AS data,
    SUM(COALESCE(f.faturamento,0))::float8 AS faturamento_sum,
    SUM(COALESCE(f.volume_unidades,0))::float8 AS volume_sum,
    SUM(COALESCE(f.avg_sales_price,0))::float8 AS fallback_price_sum,
    COUNT(f.avg_sales_price)::bigint AS fallback_price_count,
    SUM(COALESCE(f.volume_unidades,0)*COALESCE(f.avg_price_cost,0))::float8 AS sales_cost_sum,
    SUM(COALESCE(f.estoque_medio,0)*COALESCE(f.avg_price_cost,0))::float8 AS stock_cost_sum,
    SUM(f.giro) FILTER (WHERE f.giro>0)::float8 AS giro_num,
    COUNT(f.giro) FILTER (WHERE f.giro>0)::bigint AS giro_den,
    SUM(COALESCE(f.qtd_problemas_osa,0))::float8 AS osa_problem_sum,
    SUM(COALESCE(f.qtd_item_ativo_osa,0))::float8 AS osa_active_sum,
    SUM(COALESCE(f.rup,0))::float8 AS rupture_sum,
    SUM(COALESCE(f.status_item_geral,0))::float8 AS status_sum,
    SUM(COALESCE(f.est_virtual,0))::float8 AS isv_sum
  FROM gold.fato_historico f
  WHERE f.id_customer=:customer
  GROUP BY f.mes_ano
), factor AS (
  SELECT f.mes_ano::date AS data,MAX(c.conversion_rate)::float8 AS conversion_factor
  FROM gold.fato_historico f
  JOIN gold.dim_conversao c
    ON c.id_customer=f.id_customer
   AND c.id_item::text=f.id_item::text
   AND c.nm_measure=:measure
  WHERE f.id_customer=:customer
  GROUP BY f.mes_ano
)
SELECT m.data,
  CASE WHEN m.faturamento_sum>0 THEN m.faturamento_sum
       WHEN f.conversion_factor IS NOT NULL AND m.fallback_price_count>0
       THEN (m.volume_sum*f.conversion_factor)
          *((m.fallback_price_sum/m.fallback_price_count)*f.conversion_factor)
       ELSE NULL END::float8 AS sellout_sum,
  m.sales_cost_sum,m.stock_cost_sum,m.giro_num,m.giro_den,
  m.osa_problem_sum,m.osa_active_sum,m.rupture_sum,m.status_sum,m.isv_sum
FROM monthly m JOIN factor f USING(data)
ORDER BY m.data
""")

MONTHLY_MART = text("""
SELECT data::date data,sellout_sum,sales_cost_sum,stock_cost_sum,giro_num,giro_den,
       osa_problem_sum,osa_active_sum,rupture_sum,status_sum,isv_sum
FROM gold.nr_panorama_inventory_monthly_default
WHERE id_customer=:customer AND nm_measure=:measure
ORDER BY data
""")

WEEKLY_SOURCE = text("""
WITH latest AS (
  SELECT cd_week
  FROM gold.fato_semanal
  WHERE id_customer=:customer
  GROUP BY cd_week ORDER BY cd_week DESC LIMIT 13
), global_latest AS (
  SELECT MAX(cd_week) AS cd_week FROM gold.fato_semanal WHERE id_customer=:customer
), weekly AS (
  SELECT
    f.id_time::date AS data,
    MAX(f.cd_week) AS cd_week,
    SUM(COALESCE(f.faturamento,0))::float8 AS faturamento_sum,
    SUM(COALESCE(f.volume_unidade,0))::float8 AS volume_sum,
    SUM(COALESCE(f.avg_sales_price,0))::float8 AS fallback_price_sum,
    COUNT(f.avg_sales_price)::bigint AS fallback_price_count,
    SUM(COALESCE(f.volume_unidade,0)*COALESCE(f.avg_price_cost,0))::float8 AS sales_cost_sum,
    SUM(COALESCE(f.estoque_medio,0)*COALESCE(f.avg_price_cost,0))::float8 AS stock_cost_sum,
    SUM(f.giro)::float8 AS giro_num_raw,
    COUNT(f.giro)::bigint AS giro_den_raw,
    SUM(COALESCE(f.qtd_problemas_osa,0))::float8 AS osa_problem_sum,
    SUM(COALESCE(f.qtd_item_ativo_osa,0))::float8 AS osa_active_sum,
    SUM(COALESCE(f.rup,0))::float8 AS rupture_sum,
    SUM(COALESCE(f.status_item_geral,0))::float8 AS status_sum,
    SUM(COALESCE(f.est_virtual,0))::float8 AS isv_sum
  FROM gold.fato_semanal f
  JOIN latest l USING(cd_week)
  WHERE f.id_customer=:customer
  GROUP BY f.id_time
), factor AS (
  SELECT f.id_time::date AS data,MAX(c.conversion_rate)::float8 AS conversion_factor
  FROM gold.fato_semanal f
  JOIN latest l USING(cd_week)
  JOIN gold.dim_conversao c
    ON c.id_customer=f.id_customer
   AND c.id_item::text=f.id_item::text
   AND c.nm_measure=:measure
  WHERE f.id_customer=:customer
  GROUP BY f.id_time
)
SELECT w.data,w.cd_week,
  CASE WHEN w.faturamento_sum>0 THEN w.faturamento_sum
       WHEN f.conversion_factor IS NOT NULL AND w.fallback_price_count>0
       THEN (w.volume_sum*f.conversion_factor)
          *((w.fallback_price_sum/w.fallback_price_count)*f.conversion_factor)
       ELSE NULL END::float8 AS sellout_sum,
  w.sales_cost_sum,w.stock_cost_sum,
  CASE WHEN w.cd_week=g.cd_week THEN NULL ELSE w.giro_num_raw END::float8 AS giro_num,
  CASE WHEN w.cd_week=g.cd_week THEN NULL ELSE w.giro_den_raw END::bigint AS giro_den,
  w.osa_problem_sum,w.osa_active_sum,w.rupture_sum,w.status_sum,w.isv_sum
FROM weekly w JOIN factor f USING(data) CROSS JOIN global_latest g
ORDER BY w.data
""")

WEEKLY_MART = text("""
SELECT data::date data,cd_week,sellout_sum,sales_cost_sum,stock_cost_sum,giro_num,giro_den,
       osa_problem_sum,osa_active_sum,rupture_sum,status_sum,isv_sum
FROM gold.nr_panorama_inventory_weekly_card_default
WHERE id_customer=:customer AND nm_measure=:measure AND row_scope='timeline'
ORDER BY data
""")

GAP_MONTHLY_SOURCE = text("""
WITH daily AS (
  SELECT id_time::date AS data,
         SUM(tvd_simplificado)::float8 AS tvd,
         SUM(ivd_simplificado)::float8 AS ivd
  FROM gold.fato_ivd_tvd
  WHERE id_customer=:customer
  GROUP BY id_time::date
), tagged AS (
  SELECT d.*,DATE_TRUNC('month',data)::date AS period_start FROM daily d
), anchors AS (
  SELECT period_start,
         MAX(data) FILTER (WHERE tvd IS NOT NULL) AS tvd_date,
         MAX(data) FILTER (WHERE ivd IS NOT NULL) AS ivd_date
  FROM tagged GROUP BY period_start
)
SELECT a.period_start AS data,t.tvd,i.ivd
FROM anchors a
LEFT JOIN daily t ON t.data=a.tvd_date
LEFT JOIN daily i ON i.data=a.ivd_date
ORDER BY a.period_start
""")

GAP_MONTHLY_MART = text("""
SELECT data::date data,tvd,ivd
FROM gold.nr_panorama_gap_monthly_default
WHERE id_customer=:customer
ORDER BY data
""")

GAP_WEEKLY_SOURCE = text("""
WITH daily AS (
  SELECT id_time::date AS data,
         SUM(tvd_simplificado)::float8 AS tvd,
         SUM(ivd_simplificado)::float8 AS ivd
  FROM gold.fato_ivd_tvd
  WHERE id_customer=:customer
  GROUP BY id_time::date
), tagged AS (
  SELECT d.*,DATE_TRUNC('week',data)::date AS period_start FROM daily d
), anchors AS (
  SELECT period_start,
         MAX(data) FILTER (WHERE tvd IS NOT NULL) AS tvd_date,
         MAX(data) FILTER (WHERE ivd IS NOT NULL) AS ivd_date
  FROM tagged GROUP BY period_start
), values AS (
  SELECT a.period_start AS data,t.tvd,i.ivd,
         DENSE_RANK() OVER (ORDER BY a.period_start DESC) AS week_rank
  FROM anchors a
  LEFT JOIN daily t ON t.data=a.tvd_date
  LEFT JOIN daily i ON i.data=a.ivd_date
)
SELECT data,tvd,ivd FROM values
WHERE week_rank<=13
ORDER BY data
""")

GAP_WEEKLY_MART = text("""
SELECT data::date data,tvd,ivd
FROM gold.nr_panorama_gap_weekly_card_default
WHERE id_customer=:customer AND row_scope='timeline'
ORDER BY data
""")


def compare_rows(source, mart, columns, context):
    if len(source) != len(mart):
        raise AssertionError(f"{context}: row count {len(source)} != {len(mart)}")
    for left, right in zip(source, mart):
        if str(left["data"])[:10] != str(right["data"])[:10]:
            raise AssertionError(f"{context}: date mismatch {left['data']} != {right['data']}")
        for column in columns:
            if not close(left[column], right[column]):
                raise AssertionError({
                    "context": context,
                    "date": str(left["data"]),
                    "column": column,
                    "source": left[column],
                    "mart": right[column],
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

        names = {
            "giro_m": "[Panorama] Evolutivo de estoque — Giro x ROI mensal",
            "giro_w": "[Panorama] Evolutivo de estoque — Giro x ROI semanal",
            "osa_m": "[Panorama] Evolutivo de estoque — OSA mensal",
            "osa_w": "[Panorama] Evolutivo de estoque — OSA semanal",
            "gap_m": "[Panorama] Evolutivo de estoque — Falta x Excesso mensal",
            "gap_w": "[Panorama] Evolutivo de estoque — Falta x Excesso semanal",
        }
        missing = [name for name in names.values() if name not in charts]
        if missing:
            raise AssertionError({"missing_charts": missing})

        giro_expected = {
            "metric_semantics": "direct_average:0:1|roi:1:3|weighted_average:4:2",
            "metric_labels": "Estoque Preço Custo|% ROI|Giro",
            "metric_formats": "currency|percent|number",
            "chart_styles": "bar|line|line",
            "summary_count": 3,
            "summary_labels": "U3M|Anual|U3M",
            "metric_summary_modes": "u3m|annual12|u3m",
            "timeline_zero_blank_indices": "1",
            "timeline_limit": 13,
        }
        osa_expected = {
            "metric_semantics": "one_minus_ratio:0:2|ratio_percent:2:2|ratio_percent:4:2",
            "metric_labels": "% OSA|% Ruptura|% ISV",
            "metric_formats": "percent|percent|percent",
            "chart_styles": "line|line|line",
            "summary_count": 3,
            "timeline_limit": 13,
        }
        gap_expected = {
            "metric_semantics": "direct_average:0:1|direct_average:1:1",
            "metric_labels": "TVD - Risco|IVD - Excesso",
            "metric_formats": "currency|currency",
            "chart_styles": "line|line",
            "summary_count": 2,
            "timeline_limit": 13,
        }

        for key in ("giro_m", "giro_w"):
            assert_chart_params(charts[names[key]], giro_expected)
        for key in ("osa_m", "osa_w"):
            assert_chart_params(charts[names[key]], osa_expected)
        for key in ("gap_m", "gap_w"):
            assert_chart_params(charts[names[key]], gap_expected)
        for key in ("giro_w", "osa_w", "gap_w"):
            params = json.loads(charts[names[key]].params)
            if params.get("timeline_query_scope") != "timeline" or params.get("summary_query_scope") != "summary":
                raise AssertionError(f"{names[key]}: weekly scopes diverged")

        database = charts[names["giro_m"]].table.database
        factory = QueryContextFactory()
        filters = [
            {"col": "id_customer", "op": "IN", "val": [CUSTOMER_ID]},
            {"col": "nm_measure", "op": "IN", "val": ["unidade"]},
        ]
        report = {"tenant": CUSTOMER_ID, "charts": {}, "probes": {}}
        runtime_fixture = {"charts": {}}

        with database.get_sqla_engine() as engine, engine.connect() as connection:
            source_m = list(connection.execute(
                MONTHLY_SOURCE, {"customer": CUSTOMER_ID, "measure": "unidade"}
            ).mappings())
            mart_m = list(connection.execute(
                MONTHLY_MART, {"customer": CUSTOMER_ID, "measure": "unidade"}
            ).mappings())
            compare_rows(source_m, mart_m, (
                "sellout_sum", "sales_cost_sum", "stock_cost_sum", "giro_num", "giro_den",
                "osa_problem_sum", "osa_active_sum", "rupture_sum", "status_sum", "isv_sum",
            ), "inventory-monthly")

            source_w = list(connection.execute(
                WEEKLY_SOURCE, {"customer": CUSTOMER_ID, "measure": "unidade"}
            ).mappings())
            mart_w = list(connection.execute(
                WEEKLY_MART, {"customer": CUSTOMER_ID, "measure": "unidade"}
            ).mappings())
            compare_rows(source_w, mart_w, (
                "sellout_sum", "sales_cost_sum", "stock_cost_sum", "giro_num", "giro_den",
                "osa_problem_sum", "osa_active_sum", "rupture_sum", "status_sum", "isv_sum",
            ), "inventory-weekly")
            if len(mart_w) != 13:
                raise AssertionError(f"inventory-weekly: expected 13 weeks, got {len(mart_w)}")

            gap_source_m = list(connection.execute(
                GAP_MONTHLY_SOURCE, {"customer": CUSTOMER_ID}
            ).mappings())
            gap_mart_m = list(connection.execute(
                GAP_MONTHLY_MART, {"customer": CUSTOMER_ID}
            ).mappings())
            compare_rows(gap_source_m, gap_mart_m, ("tvd", "ivd"), "gap-monthly")

            gap_source_w = list(connection.execute(
                GAP_WEEKLY_SOURCE, {"customer": CUSTOMER_ID}
            ).mappings())
            gap_mart_w = list(connection.execute(
                GAP_WEEKLY_MART, {"customer": CUSTOMER_ID}
            ).mappings())
            compare_rows(gap_source_w, gap_mart_w, ("tvd", "ivd"), "gap-weekly")
            if len(gap_mart_w) != 13:
                raise AssertionError(f"gap-weekly: expected 13 weeks, got {len(gap_mart_w)}")

            # Formula probes on the latest monthly serving row.
            last = mart_m[-1]
            report["probes"]["latest_month"] = {
                "roi": roi(last["sellout_sum"], last["sales_cost_sum"], last["stock_cost_sum"]),
                "giro": None if not last["giro_den"] else float(last["giro_num"]) / float(last["giro_den"]),
                "osa": safe_ratio(last["osa_problem_sum"], last["osa_active_sum"], one_minus=True),
                "ruptura": safe_ratio(last["rupture_sum"], last["status_sum"]),
                "isv": safe_ratio(last["isv_sum"], last["status_sum"]),
            }

        for key, chart_name in names.items():
            chart = charts[chart_name]
            chart_filters = [{"col": "id_customer", "op": "IN", "val": [CUSTOMER_ID]}]
            if key.startswith("giro") or key.startswith("osa"):
                chart_filters.append({"col": "nm_measure", "op": "IN", "val": ["unidade"]})
            responses = execute(factory, ChartDataCommand, chart, chart_filters)
            weekly = key.endswith("_w")
            timeline = require_rows(chart_name, responses, weekly=weekly)
            report["charts"][chart_name] = {
                "timeline_rows": len(timeline),
                "query_count": len(responses),
                "summary_rows": len(responses[1].get("data") or []) if weekly else 0,
            }
            runtime_fixture["charts"][chart_name] = {
                "rawFormData": json.loads(chart.params),
                "queriesData": [{"data": response.get("data") or []} for response in responses],
            }

        fixture_path = os.environ.get("PANORAMA_INVENTORY_RUNTIME_FIXTURE")
        if fixture_path:
            Path(fixture_path).write_text(
                json.dumps(json_safe(runtime_fixture), ensure_ascii=False, default=str, allow_nan=False),
                encoding="utf-8",
            )
            report["runtime_fixture"] = fixture_path

        print(json.dumps(report, ensure_ascii=False, default=str, indent=2))


if __name__ == "__main__":
    main()
