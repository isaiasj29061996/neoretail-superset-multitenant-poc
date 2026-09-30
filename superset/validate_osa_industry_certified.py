"""Runtime certification gate for the isolated OSA Industry dashboard.

Checks:
1. required source value-loss column exists;
2. every chart executes through Superset ChartData under tenant 142;
3. latest monthly Value/Quantity cards reconcile to raw Power BI fact formulas;
4. latest weekly Value/Quantity cards reconcile to raw weekly formulas;
5. MTD motive bars reconcile to the monthly cause source.

Run only after Silver/Gold republishes fato_mensal_causa_osa with vl_perda_osa
and after bootstrap_osa_industry_certified.py.
"""
from __future__ import annotations

import json
import math
from time import perf_counter

from flask import g
from flask_login import login_user
from sqlalchemy import text
from superset.app import create_app
from superset.commands.chart.data.get_data_command import ChartDataCommand
from superset.common.query_context_factory import QueryContextFactory
from superset.models.dashboard import Dashboard

from profile_dashboard_performance import build_queries


CUSTOMER_ID = 142
DASHBOARD = "neoretail-v9-osa-industria-certified"
PREFIX = "[OSA Certificada]"


def close(left, right):
    if left is None or right is None:
        return left is None and right is None
    try:
        return math.isclose(float(left), float(right), rel_tol=1e-7, abs_tol=1e-5)
    except (TypeError, ValueError):
        return left == right


def chart_data(factory, chart, *, period=None):
    form = json.loads(chart.params)
    queries, _ = build_queries(form)
    filters = [
        {"col": "id_customer", "op": "IN", "val": [CUSTOMER_ID]},
        {"col": "nm_measure", "op": "IN", "val": ["unidade"]},
    ]
    if period is not None:
        filters.append({"col": "osa_period", "op": "IN", "val": [period]})
    for query in queries:
        query["filters"] = [*query.get("filters", []), *filters]
    g.form_data = {"extra_filters": filters}
    started = perf_counter()
    result = ChartDataCommand(factory.create(
        datasource={"id": chart.datasource_id, "type": "table"},
        queries=queries,
        form_data={**form, "force": True, "extra_filters": filters},
    )).run()
    elapsed = (perf_counter() - started) * 1000
    errors = [
        query.get("error") for query in result.get("queries", [])
        if query.get("error")
    ]
    if errors:
        raise AssertionError({"chart": chart.slice_name, "errors": errors})
    rows = []
    for query in result.get("queries", []):
        rows.extend(query.get("data") or [])
    return rows, elapsed


def latest_row(rows):
    if not rows:
        raise AssertionError("ChartData sem linhas")
    def key(row):
        value = row.get("data") or row.get("__timestamp") or ""
        return str(value)
    return sorted(rows, key=key)[-1]


MONTHLY_EXPECTED = text("""
WITH latest AS (
  SELECT MAX(mes_ano)::date AS data
  FROM gold.fato_historico
  WHERE id_customer=:customer
), h AS (
  SELECT f.*
  FROM gold.fato_historico f
  JOIN latest x ON f.mes_ano::date=x.data
  WHERE f.id_customer=:customer
), c AS (
  SELECT f.*
  FROM gold.fato_mensal_causa_osa f
  JOIN latest x ON f.data=x.data
  WHERE f.id_customer=:customer
), hf AS (
  SELECT MAX(cv.conversion_rate)::float8 AS factor
  FROM (SELECT DISTINCT id_item FROM h) x
  JOIN gold.dim_conversao cv
    ON cv.id_customer=:customer
   AND cv.id_item::text=x.id_item::text
   AND cv.nm_measure='unidade'
), cf AS (
  SELECT MAX(cv.conversion_rate)::float8 AS factor
  FROM (SELECT DISTINCT id_item FROM c) x
  JOIN gold.dim_conversao cv
    ON cv.id_customer=:customer
   AND cv.id_item::text=x.id_item::text
   AND cv.nm_measure='unidade'
), hs AS (
  SELECT
    SUM(COALESCE(faturamento,0))::float8 faturamento,
    SUM(COALESCE(volume_unidades,0))::float8 volume,
    SUM(COALESCE(qtd_perda_osa,0))::float8 loss_qty,
    SUM(COALESCE(qtd_problemas_osa,0))::float8 problems,
    SUM(COALESCE(qtd_item_ativo_osa,0))::float8 active,
    AVG(avg_sales_price)::float8 avg_price
  FROM h
), cs AS (
  SELECT
    SUM(COALESCE(vl_perda_osa,0))::float8 loss_value,
    SUM(COALESCE(qtd_perda_osa,0))::float8 loss_qty,
    SUM(COALESCE(volume_unidades,0))::float8 volume,
    SUM(COALESCE(faturamento,0))::float8 faturamento,
    SUM(COALESCE(preco_medio,0))::float8 price_sum
  FROM c
)
SELECT
  (SELECT data FROM latest) AS data,
  CASE WHEN hs.faturamento>0 THEN hs.faturamento
       ELSE (hs.volume*hf.factor)*(hs.avg_price*hf.factor) END::float8 AS "Sell Out Venda",
  cs.loss_value::float8 AS "Perda R$ OSA",
  CASE WHEN cs.faturamento>0
       THEN 100.0*cs.loss_value/NULLIF(cs.faturamento,0)
       ELSE 100.0*cs.loss_value/NULLIF(cs.volume*cs.price_sum,0)
  END::float8 AS "% Perda Valor",
  (100.0*(1-hs.problems/NULLIF(hs.active,0)))::float8 AS "%OSA",
  (cs.volume*cf.factor)::float8 AS "Venda qtd",
  (cs.loss_qty*cf.factor)::float8 AS "Perda OSA qtd",
  (100.0*(hs.loss_qty*hf.factor)
    / NULLIF(hs.volume*hf.factor,0))::float8 AS "% Perda Qtd"
FROM hs CROSS JOIN cs CROSS JOIN hf CROSS JOIN cf
""")


WEEKLY_EXPECTED = text("""
WITH latest AS (
  SELECT MAX(id_time)::date AS data
  FROM gold.fato_semanal
  WHERE id_customer=:customer
), w AS (
  SELECT f.*
  FROM gold.fato_semanal f
  JOIN latest x ON f.id_time::date=x.data
  WHERE f.id_customer=:customer
), factor AS (
  SELECT MAX(cv.conversion_rate)::float8 AS factor
  FROM (SELECT DISTINCT id_item FROM w) x
  JOIN gold.dim_conversao cv
    ON cv.id_customer=:customer
   AND cv.id_item::text=x.id_item::text
   AND cv.nm_measure='unidade'
), s AS (
  SELECT
    SUM(COALESCE(faturamento,0))::float8 faturamento,
    SUM(COALESCE(volume_unidade,0))::float8 volume,
    SUM(COALESCE(qtd_perda_osa,0))::float8 loss_qty,
    SUM(COALESCE(qtd_problemas_osa,0))::float8 problems,
    SUM(COALESCE(qtd_item_ativo_osa,0))::float8 active,
    AVG(avg_sales_price)::float8 avg_sales,
    AVG(avg_price_cost)::float8 avg_cost
  FROM w
), demand AS (
  SELECT SUM(COALESCE(demanda_media,0))::float8 AS demand_sum
  FROM gold.calculo_oportunidades
  WHERE id_customer=:customer
    AND COALESCE(qtd_item_ativo_osa_m0,0)>0
)
SELECT
  (SELECT data FROM latest) AS data,
  CASE WHEN s.faturamento>0 THEN s.faturamento
       ELSE (s.volume*factor.factor)*(s.avg_sales*factor.factor) END::float8
       AS "Sell Out Venda",
  (s.loss_qty*s.avg_cost)::float8 AS "Perda R$ OSA",
  CASE WHEN s.faturamento>0
       THEN 100.0*(s.loss_qty*s.avg_cost)/NULLIF(s.faturamento,0)
       ELSE 100.0*(s.loss_qty*s.avg_cost)
          / NULLIF(s.volume*s.avg_cost,0)
  END::float8 AS "% Perda Valor",
  (100.0*(1-s.problems/NULLIF(s.active,0)))::float8 AS "%OSA",
  (s.volume*factor.factor)::float8 AS "Venda qtd",
  (s.loss_qty*factor.factor)::float8 AS "Perda OSA qtd",
  (100.0*s.loss_qty/NULLIF(demand.demand_sum*30.0,0))::float8 AS "% Perda Qtd"
FROM s CROSS JOIN factor CROSS JOIN demand
""")


MOTIVE_VALUE_EXPECTED = text("""
WITH latest AS (
  SELECT MAX(data)::date AS data
  FROM gold.fato_mensal_causa_osa
  WHERE id_customer=:customer
)
SELECT motivo_osa,SUM(COALESCE(vl_perda_osa,0))::float8 AS value
FROM gold.fato_mensal_causa_osa f
JOIN latest x ON f.data=x.data
WHERE f.id_customer=:customer
GROUP BY motivo_osa
""")


MOTIVE_QTY_EXPECTED = text("""
WITH latest AS (
  SELECT MAX(data)::date AS data
  FROM gold.fato_mensal_causa_osa
  WHERE id_customer=:customer
), base AS (
  SELECT f.*
  FROM gold.fato_mensal_causa_osa f
  JOIN latest x ON f.data=x.data
  WHERE f.id_customer=:customer
), rows AS (
  SELECT b.motivo_osa,b.qtd_perda_osa,cv.conversion_rate
  FROM base b
  LEFT JOIN gold.dim_conversao cv
    ON cv.id_customer=b.id_customer
   AND cv.id_item::text=b.id_item::text
   AND cv.nm_measure='unidade'
)
SELECT motivo_osa,
       (SUM(COALESCE(qtd_perda_osa,0))*MAX(conversion_rate))::float8 AS value
FROM rows
GROUP BY motivo_osa
""")


def assert_metric(row, expected, chart, mapping):
    for actual_key, expected_key in mapping.items():
        if actual_key not in row:
            raise AssertionError({
                "chart": chart, "missing_metric": actual_key,
                "available": sorted(row.keys()),
            })
        if not close(row.get(actual_key), expected.get(expected_key)):
            raise AssertionError({
                "chart": chart,
                "metric": actual_key,
                "expected": expected.get(expected_key),
                "actual": row.get(actual_key),
            })


def compare_categories(rows, expected_rows, category, metric, context):
    actual = {
        row.get(category): row.get(metric)
        for row in rows if row.get(category) is not None
    }
    expected = {row[category]: row["value"] for row in expected_rows}
    if actual.keys() != expected.keys():
        raise AssertionError({
            "context": context,
            "missing": sorted(set(expected)-set(actual))[:10],
            "unexpected": sorted(set(actual)-set(expected))[:10],
        })
    for key,value in expected.items():
        if not close(actual[key],value):
            raise AssertionError({
                "context": context,"category": key,
                "expected": value,"actual": actual[key],
            })


def main():
    app = create_app()
    with app.test_request_context("/"):
        from superset import db,security_manager

        admin = security_manager.find_user(username="admin") or db.session.query(
            security_manager.user_model
        ).first()
        login_user(admin)
        g.user = admin

        dashboard = db.session.query(Dashboard).filter(
            Dashboard.slug==DASHBOARD
        ).one()
        charts = {chart.slice_name:chart for chart in dashboard.slices}
        factory = QueryContextFactory()
        report = {"tenant":CUSTOMER_ID,"charts":{},"reconciliations":[]}

        any_chart = next(iter(charts.values()))
        with any_chart.table.database.get_sqla_engine() as engine, engine.connect() as connection:
            has_value_loss = connection.execute(text("""
                SELECT EXISTS (
                  SELECT 1 FROM information_schema.columns
                  WHERE table_schema='gold'
                    AND table_name='fato_mensal_causa_osa'
                    AND column_name='vl_perda_osa'
                )
            """)).scalar_one()
            if not has_value_loss:
                raise AssertionError(
                    "gold.fato_mensal_causa_osa ainda não possui vl_perda_osa. "
                    "Republique 03B e 06 desta branch antes do bootstrap certificado."
                )

            monthly_expected = connection.execute(
                MONTHLY_EXPECTED,{"customer":CUSTOMER_ID}
            ).mappings().one()
            weekly_expected = connection.execute(
                WEEKLY_EXPECTED,{"customer":CUSTOMER_ID}
            ).mappings().one()

            for title,period in (
                (f"{PREFIX} Visão geral — Valor mensal",None),
                (f"{PREFIX} Visão geral — Valor semanal",None),
                (f"{PREFIX} Visão geral — Quantidade mensal",None),
                (f"{PREFIX} Visão geral — Quantidade semanal",None),
                (f"{PREFIX} Perda OSA por motivo — Valor","MTD"),
                (f"{PREFIX} Perda OSA por causa — Valor","MTD"),
                (f"{PREFIX} Perda OSA por motivo — Quantidade","MTD"),
                (f"{PREFIX} Perda OSA por causa — Quantidade","MTD"),
                (f"{PREFIX} Região — Valor","MTD"),
                (f"{PREFIX} Varejo — Valor","MTD"),
                (f"{PREFIX} Hierarquia de item — Valor","MTD"),
                (f"{PREFIX} Região — Quantidade","MTD"),
                (f"{PREFIX} Varejo — Quantidade","MTD"),
                (f"{PREFIX} Hierarquia de item — Quantidade","MTD"),
            ):
                if title not in charts:
                    raise AssertionError({"missing_chart":title})
                rows,elapsed = chart_data(factory,charts[title],period=period)
                report["charts"][title] = {
                    "rows":len(rows),"elapsed_ms":round(elapsed,2),
                }

            row = latest_row(report_rows := chart_data(
                factory,charts[f"{PREFIX} Visão geral — Valor mensal"]
            )[0])
            assert_metric(
                row,monthly_expected,"monthly-value",
                {
                    "Sell Out Venda":"Sell Out Venda",
                    "Perda R$ OSA":"Perda R$ OSA",
                    "% Perda":"% Perda Valor",
                    "%OSA":"%OSA",
                },
            )
            report["reconciliations"].append("monthly-value:source=ChartData")

            row = latest_row(chart_data(
                factory,charts[f"{PREFIX} Visão geral — Quantidade mensal"]
            )[0])
            assert_metric(
                row,monthly_expected,"monthly-quantity",
                {
                    "Venda qtd":"Venda qtd",
                    "Perda OSA qtd":"Perda OSA qtd",
                    "% Perda":"% Perda Qtd",
                    "%OSA":"%OSA",
                },
            )
            report["reconciliations"].append("monthly-quantity:source=ChartData")

            row = latest_row(chart_data(
                factory,charts[f"{PREFIX} Visão geral — Valor semanal"]
            )[0])
            assert_metric(
                row,weekly_expected,"weekly-value",
                {
                    "Sell Out Venda":"Sell Out Venda",
                    "Perda R$ OSA":"Perda R$ OSA",
                    "% Perda":"% Perda Valor",
                    "%OSA":"%OSA",
                },
            )
            report["reconciliations"].append("weekly-value:source=ChartData")

            row = latest_row(chart_data(
                factory,charts[f"{PREFIX} Visão geral — Quantidade semanal"]
            )[0])
            assert_metric(
                row,weekly_expected,"weekly-quantity",
                {
                    "Venda qtd":"Venda qtd",
                    "Perda OSA qtd":"Perda OSA qtd",
                    "% Perda":"% Perda Qtd",
                    "%OSA":"%OSA",
                },
            )
            report["reconciliations"].append("weekly-quantity:source=ChartData")

            motive_value_expected = list(connection.execute(
                MOTIVE_VALUE_EXPECTED,{"customer":CUSTOMER_ID}
            ).mappings())
            rows,_ = chart_data(
                factory,charts[f"{PREFIX} Perda OSA por motivo — Valor"],
                period="MTD",
            )
            compare_categories(
                rows,motive_value_expected,"motivo_osa","Perda R$ OSA",
                "motive-value-MTD",
            )
            report["reconciliations"].append("motive-value-MTD:source=ChartData")

            motive_qty_expected = list(connection.execute(
                MOTIVE_QTY_EXPECTED,{"customer":CUSTOMER_ID}
            ).mappings())
            rows,_ = chart_data(
                factory,charts[f"{PREFIX} Perda OSA por motivo — Quantidade"],
                period="MTD",
            )
            compare_categories(
                rows,motive_qty_expected,"motivo_osa","Perda OSA qtd",
                "motive-quantity-MTD",
            )
            report["reconciliations"].append("motive-quantity-MTD:source=ChartData")

        print(json.dumps(report,ensure_ascii=False,indent=2,default=str))


if __name__=="__main__":
    main()
