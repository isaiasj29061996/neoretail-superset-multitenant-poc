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

import os

import json
import math
from time import perf_counter

from flask import g
from flask_login import login_user
from sqlalchemy import text
from superset.app import create_app

from profile_dashboard_performance import build_queries


CUSTOMER_ID = int(os.getenv("NEORETAIL_VALIDATION_CUSTOMER", "142"))
DASHBOARD = "neoretail-v9-osa-industria-certified"
PREFIX = "[OSA Certificada]"
PERFORMANCE_BUDGET_MS = 3000.0
FILTER_REDE = "CENCOSUD"


def close(left, right):
    def is_blank(value):
        return value is None or (
            isinstance(value, float) and math.isnan(value)
        )

    if is_blank(left) or is_blank(right):
        return is_blank(left) and is_blank(right)
    try:
        return math.isclose(float(left), float(right), rel_tol=1e-7, abs_tol=1e-5)
    except (TypeError, ValueError):
        return left == right


def chart_data(factory, command, chart, *, period=None, extra_filters=None, include_query=False):
    form = json.loads(chart.params)
    queries, _ = build_queries(form)
    filters = [
        {"col": "id_customer", "op": "IN", "val": [CUSTOMER_ID]},
        {"col": "nm_measure", "op": "IN", "val": ["unidade"]},
    ]
    if period is not None:
        filters.append({"col": "osa_period", "op": "IN", "val": [period]})
    filters.extend(extra_filters or [])
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
    errors = [
        query.get("error") for query in result.get("queries", [])
        if query.get("error")
    ]
    if errors:
        raise AssertionError({"chart": chart.slice_name, "errors": errors})
    rows = []
    for query in result.get("queries", []):
        rows.extend(query.get("data") or [])
    if include_query:
        return rows, elapsed, "\n".join(query.get("query", "") for query in result.get("queries", []))
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


FILTERED_MONTHLY_EXPECTED = text("""
WITH latest AS (
  SELECT MAX(mes_ano)::date AS data
  FROM gold.fato_historico
  WHERE id_customer=:customer
), h AS (
  SELECT f.*
  FROM gold.fato_historico f
  JOIN gold.dim_local l
    ON l.id_customer=f.id_customer AND l.id_location=f.id_location
  JOIN latest x ON f.mes_ano::date=x.data
  WHERE f.id_customer=:customer AND l.rede=:rede
), c AS (
  SELECT f.*
  FROM gold.fato_mensal_causa_osa f
  JOIN gold.dim_local l
    ON l.id_customer=f.id_customer AND l.id_location=f.id_location
  JOIN latest x ON f.data=x.data
  WHERE f.id_customer=:customer AND l.rede=:rede
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
), week_locations AS (
  SELECT DISTINCT id_location FROM w
), demand AS (
  SELECT SUM(COALESCE(o.demanda_media,0))::float8 AS demand_sum
  FROM gold.calculo_oportunidades o
  JOIN week_locations l
    ON l.id_location::text=o.id_location::text
  WHERE o.id_customer=:customer
    AND COALESCE(o.qtd_item_ativo_osa_m0,0)>0
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


CAUSE_VALUE_EXPECTED = text("""
WITH latest AS (
  SELECT MAX(data)::date AS data
  FROM gold.fato_mensal_causa_osa
  WHERE id_customer=:customer
)
SELECT causa_osa,SUM(COALESCE(vl_perda_osa,0))::float8 AS value
FROM gold.fato_mensal_causa_osa f
JOIN latest x ON f.data=x.data
WHERE f.id_customer=:customer
GROUP BY causa_osa
ORDER BY value DESC
""")


CAUSE_QTY_EXPECTED = text("""
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
  SELECT b.causa_osa,b.qtd_perda_osa,cv.conversion_rate
  FROM base b
  LEFT JOIN gold.dim_conversao cv
    ON cv.id_customer=b.id_customer
   AND cv.id_item::text=b.id_item::text
   AND cv.nm_measure='unidade'
)
SELECT causa_osa,
       (SUM(COALESCE(qtd_perda_osa,0))*MAX(conversion_rate))::float8 AS value
FROM rows
GROUP BY causa_osa
ORDER BY value DESC
""")


MATRIX_GROUPS = {
    "region": ("regiao", "l.regiao"),
    "retail": ("rede", "l.rede"),
    "item": ("hierarquia_1", "i.hierarquia_1"),
}


def matrix_expected_sql(scope):
    column, expression = MATRIX_GROUPS[scope]
    return text(f"""
WITH latest AS (
  SELECT MAX(mes_ano)::date AS data
  FROM gold.fato_historico
  WHERE id_customer=:customer
), history_rows AS (
  SELECT
    {expression}::text AS category,h.id_item,h.qtd_perda_osa,
    h.qtd_problemas_osa,h.qtd_item_ativo_osa
  FROM gold.fato_historico h
  LEFT JOIN gold.dim_local l
    ON l.id_customer=h.id_customer AND l.id_location=h.id_location
  LEFT JOIN gold.dim_itens i
    ON i.id_customer=h.id_customer AND i.id_item=h.id_item
  JOIN latest x ON h.mes_ano::date=x.data
  WHERE h.id_customer=:customer
), history_agg AS (
  SELECT
    r.category,
    (SUM(COALESCE(r.qtd_perda_osa,0))*MAX(cv.conversion_rate))::float8 AS loss_qty,
    (SUM(COALESCE(r.qtd_problemas_osa,0))*MAX(cv.conversion_rate))::float8 AS problem_qty,
    (1-SUM(COALESCE(r.qtd_problemas_osa,0))
       /NULLIF(SUM(COALESCE(r.qtd_item_ativo_osa,0)),0))::float8 AS osa
  FROM history_rows r
  LEFT JOIN gold.dim_conversao cv
    ON cv.id_customer=:customer
   AND cv.id_item::text=r.id_item::text
   AND cv.nm_measure='unidade'
  GROUP BY r.category
), cause_agg AS (
  SELECT {expression}::text AS category,
         SUM(COALESCE(c.vl_perda_osa,0))::float8 AS loss_value
  FROM gold.fato_mensal_causa_osa c
  LEFT JOIN gold.dim_local l
    ON l.id_customer=c.id_customer AND l.id_location=c.id_location
  LEFT JOIN gold.dim_itens i
    ON i.id_customer=c.id_customer AND i.id_item=c.id_item
  JOIN latest x ON c.data=x.data
  WHERE c.id_customer=:customer
  GROUP BY {expression}
)
SELECT h.category,c.loss_value,h.loss_qty,h.problem_qty,h.osa
FROM history_agg h
LEFT JOIN cause_agg c ON c.category IS NOT DISTINCT FROM h.category
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
    expected = {
        row[category]: row["value"]
        for row in expected_rows if row[category] is not None
    }
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


def compare_matrix(rows, expected_rows, category, loss_metric, context):
    actual = {
        row.get(category): row for row in rows if row.get(category) is not None
    }
    expected = {
        row["category"]: row
        for row in expected_rows if row["category"] is not None
    }
    if actual.keys() != expected.keys():
        raise AssertionError({
            "context": context,
            "missing": sorted(set(expected)-set(actual))[:10],
            "unexpected": sorted(set(actual)-set(expected))[:10],
        })
    expected_loss = "loss_value" if loss_metric == "Perda R$ OSA" else "loss_qty"
    for key, expected_row in expected.items():
        for actual_key, expected_key in (
            (loss_metric, expected_loss),
            ("Qtd Problema OSA", "problem_qty"),
            ("% OSA", "osa"),
        ):
            if not close(actual[key].get(actual_key), expected_row[expected_key]):
                raise AssertionError({
                    "context": context,"category": key,"metric": actual_key,
                    "expected": expected_row[expected_key],
                    "actual": actual[key].get(actual_key),
                })


def main():
    app = create_app()
    with app.test_request_context("/"):
        from superset import db,security_manager
        from superset.commands.chart.data.get_data_command import ChartDataCommand
        from superset.common.query_context_factory import QueryContextFactory
        from superset.models.dashboard import Dashboard

        admin = security_manager.find_user(username="admin") or db.session.query(
            security_manager.user_model
        ).first()
        login_user(admin)
        g.user = admin

        dashboard = db.session.query(Dashboard).filter(
            Dashboard.slug==DASHBOARD
        ).one()
        charts = {chart.slice_name:chart for chart in dashboard.slices}
        # Verify the recreated runtime metadata, including the Medida fix.
        from superset.connectors.sqla.models import SqlaTable
        native = json.loads(dashboard.json_metadata)["native_filter_configuration"]
        measure = [item for item in native if item.get("name") == "Medida"]
        assert len(measure) == 1, "Medida filter missing or duplicated"
        measure = measure[0]
        assert measure["controlValues"]["multiSelect"] is False
        assert measure["defaultDataMask"]["filterState"]["value"] == ["unidade"]
        assert measure["scope"]["excluded"] == []
        for target in measure["targets"]:
            assert target["column"]["name"] == "nm_measure"
            options = db.session.get(SqlaTable, target["datasetId"])
            assert options and options.schema == "gold" and options.table_name == "nr_conversion_options"
        factory = QueryContextFactory()
        report = {
            "tenant":CUSTOMER_ID,
            "performance_budget_ms":PERFORMANCE_BUDGET_MS,
            "charts":{},
            "filtered_checks":{},
            "performance_violations":[],
            "serving_sources":{},
            "reconciliations":[],
            "measure_filter": {"default": "unidade", "source": "gold.nr_conversion_options", "scope": "all charts", "passed": True},
        }
        chart_rows = {}

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

            source_contracts = {
                "Visão geral — Valor mensal":"nr_osa_monthly_default",
                "Visão geral — Quantidade mensal":"nr_osa_monthly_default",
                "Visão geral — Valor semanal":"nr_osa_weekly_default",
                "Visão geral — Quantidade semanal":"nr_osa_weekly_default",
                "Perda OSA por motivo — Valor":"nr_osa_causes_default",
                "Perda OSA por causa — Valor":"nr_osa_causes_default",
                "Perda OSA por motivo — Quantidade":"nr_osa_causes_default",
                "Perda OSA por causa — Quantidade":"nr_osa_causes_default",
                "Região — Valor":"nr_osa_matrix_default",
                "Varejo — Valor":"nr_osa_matrix_default",
                "Hierarquia de item — Valor":"nr_osa_matrix_default",
                "Região — Quantidade":"nr_osa_matrix_default",
                "Varejo — Quantidade":"nr_osa_matrix_default",
                "Hierarquia de item — Quantidade":"nr_osa_matrix_default",
            }
            for suffix,mart in source_contracts.items():
                title = f"{PREFIX} {suffix}"
                sql = charts[title].table.sql or ""
                if mart not in sql:
                    raise AssertionError({
                        "chart":title,"expected_serving":mart,
                    })
                report["serving_sources"][title] = mart

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
                rows,elapsed = chart_data(factory, ChartDataCommand, charts[title],period=period)
                chart_rows[title] = rows
                report["charts"][title] = {
                    "rows":len(rows),"elapsed_ms":round(elapsed,2),
                }
                if elapsed > PERFORMANCE_BUDGET_MS:
                    report["performance_violations"].append({
                        "chart":title,"elapsed_ms":round(elapsed,2),
                    })

            row = latest_row(chart_rows[f"{PREFIX} Visão geral — Valor mensal"])
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

            filtered_expected = connection.execute(
                FILTERED_MONTHLY_EXPECTED,
                {"customer":CUSTOMER_ID,"rede":FILTER_REDE},
            ).mappings().one()
            filtered_rows,filtered_elapsed,filtered_sql = chart_data(
                factory,ChartDataCommand,
                charts[f"{PREFIX} Visão geral — Valor mensal"],
                extra_filters=[{
                    "col":"rede","op":"IN","val":[FILTER_REDE],
                }],
                include_query=True,
            )
            assert "nr_osa_monthly_retail" in filtered_sql, "Single retail request must use the compact serving path"
            filtered_row = latest_row(filtered_rows)
            assert_metric(
                filtered_row,filtered_expected,"monthly-value-filtered-rede",
                {
                    "Sell Out Venda":"Sell Out Venda",
                    "Perda R$ OSA":"Perda R$ OSA",
                    "% Perda":"% Perda Valor",
                    "%OSA":"%OSA",
                },
            )
            report["filtered_checks"]["monthly-value-rede"] = {
                "rede":FILTER_REDE,"rows":len(filtered_rows),
                "elapsed_ms":round(filtered_elapsed,2),
                "path":"compact_single_retail",
            }
            if filtered_elapsed > PERFORMANCE_BUDGET_MS:
                report["performance_violations"].append({
                    "chart":f"{PREFIX} Visão geral — Valor mensal",
                    "filter":f"rede={FILTER_REDE}",
                    "elapsed_ms":round(filtered_elapsed,2),
                })
            report["reconciliations"].append(
                "monthly-value-rede-filter:source=detail=ChartData"
            )

            row = latest_row(chart_rows[f"{PREFIX} Visão geral — Quantidade mensal"])
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

            row = latest_row(chart_rows[f"{PREFIX} Visão geral — Valor semanal"])
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

            row = latest_row(chart_rows[f"{PREFIX} Visão geral — Quantidade semanal"])
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
            rows = chart_rows[f"{PREFIX} Perda OSA por motivo — Valor"]
            compare_categories(
                rows,motive_value_expected,"motivo_osa","Perda R$ OSA",
                "motive-value-MTD",
            )
            report["reconciliations"].append("motive-value-MTD:source=ChartData")

            motive_qty_expected = list(connection.execute(
                MOTIVE_QTY_EXPECTED,{"customer":CUSTOMER_ID}
            ).mappings())
            rows = chart_rows[f"{PREFIX} Perda OSA por motivo — Quantidade"]
            compare_categories(
                rows,motive_qty_expected,"motivo_osa","Perda OSA qtd",
                "motive-quantity-MTD",
            )
            report["reconciliations"].append("motive-quantity-MTD:source=ChartData")

            cause_value_expected = list(connection.execute(
                CAUSE_VALUE_EXPECTED,{"customer":CUSTOMER_ID}
            ).mappings())
            compare_categories(
                chart_rows[f"{PREFIX} Perda OSA por causa — Valor"],
                cause_value_expected,"causa_osa","Perda R$ OSA",
                "cause-value-MTD",
            )
            report["reconciliations"].append("cause-value-MTD:source=mart=ChartData")

            cause_qty_expected = list(connection.execute(
                CAUSE_QTY_EXPECTED,{"customer":CUSTOMER_ID}
            ).mappings())
            compare_categories(
                chart_rows[f"{PREFIX} Perda OSA por causa — Quantidade"],
                cause_qty_expected,"causa_osa","Perda OSA qtd",
                "cause-quantity-MTD",
            )
            report["reconciliations"].append("cause-quantity-MTD:source=mart=ChartData")

            for scope,(category,_) in MATRIX_GROUPS.items():
                expected = list(connection.execute(
                    matrix_expected_sql(scope),{"customer":CUSTOMER_ID}
                ).mappings())
                label = {
                    "region":"Região", "retail":"Varejo",
                    "item":"Hierarquia de item",
                }[scope]
                for mode,loss_metric in (
                    ("Valor","Perda R$ OSA"),
                    ("Quantidade","Perda OSA qtd"),
                ):
                    compare_matrix(
                        chart_rows[f"{PREFIX} {label} — {mode}"],
                        expected,category,loss_metric,
                        f"matrix-{scope}-{mode.lower()}-MTD",
                    )
                    report["reconciliations"].append(
                        f"matrix-{scope}-{mode.lower()}-MTD:source=mart=ChartData"
                    )

            if report["performance_violations"]:
                raise AssertionError({
                    "performance_budget_ms":PERFORMANCE_BUDGET_MS,
                    "violations":report["performance_violations"],
                })

        print(json.dumps(report,ensure_ascii=False,indent=2,default=str))


if __name__=="__main__":
    main()
