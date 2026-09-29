"""Reconcile Panorama sales evolution from source to mart to Superset."""
from __future__ import annotations

import json
import math
import time

from flask import g
from flask_login import login_user
from sqlalchemy import text
from superset.app import create_app

from profile_dashboard_performance import build_queries

CUSTOMER_ID = 142
MEASURES = ("unidade", "quilograma")
DASHBOARD = "neoretail-v9-panorama-industria"


def close(left, right):
    if left is None or right is None:
        return left is None and right is None
    return math.isclose(float(left), float(right), rel_tol=1e-9, abs_tol=1e-7)


def rows_equal(left, right, columns):
    if len(left) != len(right):
        raise AssertionError(f"row count diverged: {len(left)} != {len(right)}")
    for source, mart in zip(left, right):
        for column in columns:
            if not close(source[column], mart[column]):
                raise AssertionError({"column": column, "source": source[column], "mart": mart[column]})


def execute(factory, command, chart, filters):
    form = json.loads(chart.params)
    queries, _ = build_queries(form)
    for query in queries:
        query["filters"] = [*query.get("filters", []), *filters]
    g.form_data = {"extra_filters": filters}
    result = command(factory.create(
        datasource={"id": chart.datasource_id, "type": "table"},
        queries=queries, form_data={**form, "force": True, "extra_filters": filters},
    )).run()
    g.form_data = {}
    response = result["queries"][0]
    if response.get("error"):
        raise AssertionError(response["error"])
    return response


MONTHLY_VALUE_SOURCE = text("""
SELECT mes_ano::date data,
  CASE WHEN SUM(faturamento)>0 THEN SUM(faturamento)
       ELSE SUM(volume_unidades*avg_sales_price) END::float8 sellout_sum,
  SUM(volume_unidades*avg_price_cost)::float8 cost_sum
FROM gold.fato_historico WHERE id_customer=:customer
 AND mes_ano >= (SELECT MAX(mes_ano)-INTERVAL '15 months' FROM gold.fato_historico WHERE id_customer=:customer)
GROUP BY mes_ano ORDER BY mes_ano
""")
MONTHLY_VALUE_MART = text("""
SELECT data::date data,
  CASE WHEN SUM(faturamento)>0 THEN SUM(faturamento)
       ELSE SUM(volume_unidades*avg_sales_price) END::float8 sellout_sum,
  SUM(volume_unidades*avg_price_cost)::float8 cost_sum
FROM gold.nr_overview_history WHERE id_customer=:customer
 AND data >= (SELECT MAX(data)-INTERVAL '15 months' FROM gold.nr_overview_history WHERE id_customer=:customer)
GROUP BY data ORDER BY data
""")
MONTHLY_QUANTITY_SOURCE = text("""
WITH monthly AS (
 SELECT mes_ano::date data,id_customer,SUM(COALESCE(volume_unidades,0)) volume_sum,
  SUM(COALESCE(qtd_perda_osa,0)) loss_sum,
  SUM(COALESCE(avg_sales_price,0)) FILTER(WHERE faturamento>0) price_sum,
  COUNT(avg_sales_price) FILTER(WHERE faturamento>0) price_count
 FROM gold.fato_historico WHERE id_customer=:customer
  AND mes_ano >= (SELECT MAX(mes_ano)-INTERVAL '15 months' FROM gold.fato_historico WHERE id_customer=:customer)
 GROUP BY mes_ano,id_customer
), factor AS (
 SELECT f.mes_ano::date data,MAX(c.conversion_rate)::float8 conversion_factor
 FROM gold.fato_historico f JOIN gold.dim_conversao c
  ON c.id_customer=f.id_customer AND c.id_item::text=f.id_item AND c.nm_measure=:measure
 WHERE f.id_customer=:customer
  AND f.mes_ano >= (SELECT MAX(mes_ano)-INTERVAL '15 months' FROM gold.fato_historico WHERE id_customer=:customer)
 GROUP BY f.mes_ano
)
SELECT m.data,(m.volume_sum*f.conversion_factor)::float8 sales_sum,
 (m.loss_sum*f.conversion_factor)::float8 loss_sum,
 (m.price_sum*f.conversion_factor)::float8 price_numerator,m.price_count::bigint
FROM monthly m JOIN factor f USING(data) ORDER BY data
""")
MONTHLY_QUANTITY_MART = text("""
SELECT data::date data,sales_sum,loss_sum,price_numerator,price_count
FROM gold.nr_overview_quantity_default
WHERE id_customer=:customer AND nm_measure=:measure
 AND data >= (SELECT MAX(data)-INTERVAL '15 months' FROM gold.nr_overview_quantity_default WHERE id_customer=:customer)
ORDER BY data
""")
WEEKLY_SOURCE = text("""
WITH latest AS (
 SELECT cd_week FROM gold.fato_semanal WHERE id_customer=:customer
 GROUP BY cd_week ORDER BY cd_week DESC LIMIT 13
), weekly AS (
 SELECT f.id_time::date data,MAX(f.cd_week) cd_week,
  SUM(COALESCE(f.faturamento,0)) faturamento_sum,
  SUM(COALESCE(f.volume_unidade,0)*COALESCE(f.avg_sales_price,0)) fallback_sum,
  SUM(COALESCE(f.volume_unidade,0)*COALESCE(f.avg_price_cost,0)) cost_sum,
  SUM(COALESCE(f.volume_unidade,0)) volume_sum,
  SUM(COALESCE(f.qtd_perda_osa,0)) loss_base,
  SUM(COALESCE(f.avg_sales_price,0)) FILTER(WHERE f.faturamento>0) price_sum,
  COUNT(f.avg_sales_price) FILTER(WHERE f.faturamento>0) price_count
 FROM gold.fato_semanal f JOIN latest l USING(cd_week)
 WHERE f.id_customer=:customer GROUP BY f.id_time
), factor AS (
 SELECT f.id_time::date data,MAX(c.conversion_rate)::float8 conversion_factor
 FROM gold.fato_semanal f JOIN latest l USING(cd_week)
 JOIN gold.dim_conversao c ON c.id_customer=f.id_customer
  AND c.id_item::text=f.id_item AND c.nm_measure=:measure
 WHERE f.id_customer=:customer GROUP BY f.id_time
)
SELECT w.data,w.cd_week,
 CASE WHEN w.faturamento_sum>0 THEN w.faturamento_sum ELSE w.fallback_sum END::float8 sellout_sum,
 w.cost_sum::float8,(w.volume_sum*f.conversion_factor)::float8 sales_sum,
 (w.loss_base*f.conversion_factor)::float8 loss_sum,
 (w.price_sum*f.conversion_factor)::float8 price_numerator,w.price_count::bigint
FROM weekly w JOIN factor f USING(data) ORDER BY w.data
""")
WEEKLY_MART = text("""
SELECT data::date data,cd_week,sellout_sum,cost_sum,sales_sum,loss_sum,price_numerator,price_count
FROM gold.nr_panorama_sales_weekly_default
WHERE id_customer=:customer AND nm_measure=:measure
ORDER BY data DESC LIMIT 13
""")


def u3m(rows, kind, columns):
    prior = rows[-4:-1]
    if not prior:
        return None
    if kind == "average":
        return sum(float(row[columns[0]]) for row in prior) / 3
    if kind == "sum":
        return sum(float(row[columns[0]]) for row in prior)
    numerator = sum(float(row[columns[0]]) for row in prior)
    denominator = sum(float(row[columns[1]]) for row in prior)
    return None if denominator == 0 else numerator / denominator


def main():
    app = create_app()
    with app.test_request_context("/"):
        from superset import db, security_manager
        from superset.commands.chart.data.get_data_command import ChartDataCommand
        from superset.common.query_context_factory import QueryContextFactory
        from superset.models.dashboard import Dashboard

        admin = security_manager.find_user(username="admin") or db.session.query(security_manager.user_model).first()
        login_user(admin); g.user = admin
        dashboard = db.session.query(Dashboard).filter(Dashboard.slug == DASHBOARD).one()
        charts = {chart.slice_name: chart for chart in dashboard.slices}
        database = next(iter(charts.values())).table.database
        factory = QueryContextFactory()
        report = {"tenant": CUSTOMER_ID, "paths": {}, "measures": {}}

        with database.get_sqla_engine() as engine, engine.connect() as connection:
            print("validating monthly value", flush=True)
            source = list(connection.execute(MONTHLY_VALUE_SOURCE, {"customer": CUSTOMER_ID}).mappings())
            mart = list(connection.execute(MONTHLY_VALUE_MART, {"customer": CUSTOMER_ID}).mappings())
            rows_equal(source, mart, ("sellout_sum", "cost_sum"))
            monthly_value_expected = mart
            report["paths"]["value_monthly"] = {"months": len(mart), "u3m_sellout": u3m(mart, "average", ("sellout_sum",)), "u3m_cost": u3m(mart, "average", ("cost_sum",)), "u3m_markup": 100 * u3m(mart, "ratio", ("sellout_sum", "cost_sum"))}

            for measure in MEASURES:
                print(f"validating quantity and weekly paths: {measure}", flush=True)
                mart_m = list(connection.execute(MONTHLY_QUANTITY_MART, {"customer": CUSTOMER_ID, "measure": measure}).mappings())
                if measure == "unidade":
                    source_m = list(connection.execute(MONTHLY_QUANTITY_SOURCE, {"customer": CUSTOMER_ID, "measure": measure}).mappings())
                    rows_equal(source_m, mart_m, ("sales_sum", "loss_sum", "price_numerator", "price_count"))
                    monthly_quantity_expected = mart_m
                source_w = list(connection.execute(WEEKLY_SOURCE, {"customer": CUSTOMER_ID, "measure": measure}).mappings())
                mart_w = list(reversed(list(connection.execute(WEEKLY_MART, {"customer": CUSTOMER_ID, "measure": measure}).mappings())))
                rows_equal(source_w, mart_w, ("sellout_sum", "cost_sum", "sales_sum", "loss_sum", "price_numerator", "price_count"))
                if measure == "unidade":
                    weekly_expected = mart_w
                if len(mart_w) > 13 or [row["cd_week"] for row in mart_w] != sorted(row["cd_week"] for row in mart_w):
                    raise AssertionError("weekly TOP 13/order contract failed")
                report["measures"][measure] = {
                    "monthly_rows": len(mart_m), "weekly_rows": len(mart_w),
                    "weekly_cd_week": [row["cd_week"] for row in mart_w],
                    "u3m_sales": u3m(mart_m, "average", ("sales_sum",)),
                    "u3m_loss": u3m(mart_m, "sum", ("loss_sum",)),
                    "u3m_price": u3m(mart_m, "ratio", ("price_numerator", "price_count")),
                }

            chart_contracts = {
                "[Panorama] Evolutivo de vendas — Valor mensal": ([], monthly_value_expected, {"sellout_sum": "Venda sell out", "cost_sum": "Venda custo"}),
                "[Panorama] Evolutivo de vendas — Valor semanal": ([{"col": "nm_measure", "op": "IN", "val": ["unidade"]}], weekly_expected, {"sellout_sum": "Venda sell out semanal", "cost_sum": "Venda custo semanal"}),
                "[Panorama] Evolutivo de vendas — Quantidade mensal": ([{"col": "nm_measure", "op": "IN", "val": ["unidade"]}], monthly_quantity_expected, {"sales_sum": "Venda quantidade", "loss_sum": "Perda OSA quantidade", "price_numerator": "Preço soma elegível", "price_count": "Preço linhas elegíveis"}),
                "[Panorama] Evolutivo de vendas — Quantidade semanal": ([{"col": "nm_measure", "op": "IN", "val": ["unidade"]}], weekly_expected, {"sales_sum": "Venda quantidade semanal", "loss_sum": "Perda OSA semanal", "price_numerator": "Preço soma semanal", "price_count": "Preço linhas semanal"}),
                "[Panorama] Evolutivo de vendas — Resumo Valor mensal": ([], monthly_value_expected, {"sellout_sum": "Venda sell out", "cost_sum": "Venda custo"}),
                "[Panorama] Evolutivo de vendas — Resumo Valor semanal": ([], monthly_value_expected, {"sellout_sum": "Venda sell out", "cost_sum": "Venda custo"}),
                "[Panorama] Evolutivo de vendas — Resumo Quantidade mensal": ([{"col": "nm_measure", "op": "IN", "val": ["unidade"]}], monthly_quantity_expected, {"sales_sum": "Venda quantidade", "loss_sum": "Perda OSA quantidade", "price_numerator": "Preço soma elegível", "price_count": "Preço linhas elegíveis"}),
                "[Panorama] Evolutivo de vendas — Resumo Quantidade semanal": ([{"col": "nm_measure", "op": "IN", "val": ["unidade"]}], monthly_quantity_expected, {"sales_sum": "Venda quantidade", "loss_sum": "Perda OSA quantidade", "price_numerator": "Preço soma elegível", "price_count": "Preço linhas elegíveis"}),
            }
            for name, (extra, expected, labels) in chart_contracts.items():
                print(f"validating Superset chart: {name}", flush=True)
                filters = [{"col": "id_customer", "op": "IN", "val": [CUSTOMER_ID]}, *extra]
                started = time.perf_counter()
                response = execute(factory, ChartDataCommand, charts[name], filters)
                elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
                data = response.get("data") or []
                if not data:
                    raise AssertionError(f"{name}: Superset returned no data")
                if "semanal" in name.lower() and "Resumo" not in name and len(data) > 13:
                    raise AssertionError(f"{name}: more than 13 weeks")
                actual_by_date = {str(row["data"])[:10]: row for row in data}
                for row in expected:
                    actual = actual_by_date.get(str(row["data"])[:10])
                    if actual is None:
                        raise AssertionError(f"{name}: missing Superset period {row['data']}")
                    for column, label in labels.items():
                        if not close(row[column], actual.get(label)):
                            raise AssertionError({"chart": name, "period": str(row["data"]), "metric": label, "mart": row[column], "superset": actual.get(label)})
                report["paths"][name] = {"superset_rows": len(data), "elapsed_ms": elapsed_ms}

        if close(report["measures"]["unidade"]["u3m_sales"], report["measures"]["quilograma"]["u3m_sales"]):
            raise AssertionError("conversion selector did not change quantity sales")
        print(json.dumps(report, ensure_ascii=False, default=str, indent=2))


if __name__ == "__main__":
    main()
