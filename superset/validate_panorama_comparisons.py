"""Certify the five Panorama comparison matrices against source, mart and ChartData."""
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
    "Região": ("regiao", "uf", "cidade"),
    "Varejo": ("rede", "bandeira", "loja"),
    "Hierarquia de item": ("hierarquia_1", "hierarquia_2", "item"),
}
TABS = {
    "Valor": ("Sell out venda", "Sell out custo", "Markup"),
    "Quantidade": ("Qtd venda", "Qtd Perda OSA", "Preço Médio"),
    "R$ Estoque": ("Estoque custo", "Estoque qtd", "ROI", "Giro"),
    "OSA": ("% OSA", "% RUP", "% ISV"),
    "Falta x Excesso": ("R$ Pré-ruptura", "R$ Excesso"),
}


def close(left, right):
    left_blank = left is None or (isinstance(left, float) and math.isnan(left))
    right_blank = right is None or (isinstance(right, float) and math.isnan(right))
    if left_blank or right_blank:
        return left_blank and right_blank
    return math.isclose(float(left), float(right), rel_tol=1e-8, abs_tol=1e-6)


def key(row, columns):
    return tuple(row.get(column) for column in columns)


def history_sql(columns, *, mart, filter_sql=""):
    dims = ",".join(columns)
    if mart:
        source = "gold.nr_panorama_comparison_history_detail h"
    else:
        source = """gold.fato_historico h
LEFT JOIN gold.dim_local l
  ON l.id_customer=h.id_customer AND l.id_location=h.id_location
LEFT JOIN gold.dim_itens i
  ON i.id_customer=h.id_customer AND i.id_item=h.id_item"""
    projection = dims if mart else ",".join(
        f"l.{column}" if column in {"regiao", "uf", "cidade", "rede", "bandeira", "loja"}
        else f"i.{column}" for column in columns
    )
    item = "h.id_item"
    date = "h.data" if mart else "h.mes_ano::date"
    return text(f"""
WITH expanded AS (
  SELECT {date} AS data,{projection},h.faturamento,h.volume_unidades,
         h.qtd_perda_osa,h.avg_sales_price,h.avg_price_cost,h.estoque_medio,
         h.estoque_unidades,h.giro,h.qtd_problemas_osa,h.qtd_item_ativo_osa,
         h.rup,h.status_item_geral,h.est_virtual,c.conversion_rate
  FROM {source}
  LEFT JOIN gold.dim_conversao c
    ON c.id_customer=h.id_customer AND c.id_item::text={item}::text
   AND c.nm_measure='unidade'
  WHERE h.id_customer=:customer AND {date}>=DATE_TRUNC('year',CURRENT_DATE)
  {filter_sql}
), monthly AS (
  SELECT data,{dims},
    SUM(COALESCE(faturamento,0))::float8 faturamento_sum,
    SUM(COALESCE(volume_unidades,0))::float8 volume_sum,
    SUM(COALESCE(qtd_perda_osa,0))::float8 loss_sum,
    SUM(avg_sales_price) FILTER (WHERE faturamento>0)::float8 price_sum,
    COUNT(avg_sales_price) FILTER (WHERE faturamento>0)::bigint price_count,
    SUM(COALESCE(volume_unidades,0)*COALESCE(avg_price_cost,0))::float8 sales_cost_sum,
    SUM(COALESCE(estoque_medio,0)*COALESCE(avg_price_cost,0))::float8 stock_cost_sum,
    SUM(COALESCE(estoque_unidades,0))::float8 stock_qty_base_sum,
    SUM(giro) FILTER (WHERE giro>0)::float8 giro_num,
    COUNT(giro) FILTER (WHERE giro>0)::bigint giro_den,
    SUM(COALESCE(qtd_problemas_osa,0))::float8 osa_problem_sum,
    SUM(COALESCE(qtd_item_ativo_osa,0))::float8 osa_active_sum,
    SUM(COALESCE(rup,0))::float8 rupture_sum,
    SUM(COALESCE(status_item_geral,0))::float8 status_sum,
    SUM(COALESCE(est_virtual,0))::float8 isv_sum,
    MAX(conversion_rate)::float8 conversion_factor
  FROM expanded GROUP BY data,{dims}
)
SELECT {dims},
  CASE WHEN SUM(faturamento_sum)>0 THEN SUM(faturamento_sum) END::float8 AS "Sell out venda",
  SUM(sales_cost_sum)::float8 AS "Sell out custo",
  CASE WHEN SUM(faturamento_sum)>0 AND SUM(sales_cost_sum)<>0
       THEN SUM(faturamento_sum)/SUM(sales_cost_sum) ELSE 0 END::float8 AS "Markup",
  CASE WHEN MAX(conversion_factor) IS NULL THEN NULL
       ELSE SUM(volume_sum)*MAX(conversion_factor) END::float8 AS "Qtd venda",
  CASE WHEN MAX(conversion_factor) IS NULL THEN NULL
       ELSE SUM(loss_sum)*MAX(conversion_factor) END::float8 AS "Qtd Perda OSA",
  CASE WHEN MAX(conversion_factor) IS NULL OR SUM(price_count)=0 THEN NULL
       ELSE SUM(price_sum)/SUM(price_count)*MAX(conversion_factor) END::float8 AS "Preço Médio",
  SUM(stock_cost_sum)::float8 AS "Estoque custo",
  CASE WHEN MAX(conversion_factor) IS NULL THEN NULL ELSE
       (ARRAY_AGG(stock_qty_base_sum ORDER BY data DESC))[1]*MAX(conversion_factor) END::float8 AS "Estoque qtd",
  CASE WHEN SUM(faturamento_sum)>0 AND SUM(sales_cost_sum)<>0
       THEN (SUM(faturamento_sum)-SUM(sales_cost_sum))/NULLIF(SUM(stock_cost_sum),0)
       ELSE 0 END::float8 AS "ROI",
  SUM(giro_num)/NULLIF(SUM(giro_den),0)::float8 AS "Giro",
  (1-SUM(osa_problem_sum)/NULLIF(SUM(osa_active_sum),0))::float8 AS "% OSA",
  (SUM(rupture_sum)/NULLIF(SUM(status_sum),0))::float8 AS "% RUP",
  (SUM(isv_sum)/NULLIF(SUM(status_sum),0))::float8 AS "% ISV"
FROM monthly GROUP BY {dims}
""")


def gap_sql(columns, *, mart, filter_sql=""):
    dims = ",".join(columns)
    if mart:
        source = "gold.nr_panorama_comparison_gap_daily f"
        projection = dims
        date = "f.data"
        tvd = "f.tvd"
        ivd = "f.ivd"
    else:
        source = """gold.fato_ivd_tvd f
LEFT JOIN gold.dim_local l
  ON l.id_customer=f.id_customer AND l.id_location=f.id_location
LEFT JOIN gold.dim_itens i
  ON i.id_customer=f.id_customer AND i.id_item=f.id_item"""
        projection = ",".join(
            f"l.{column}" if column in {"regiao", "uf", "cidade", "rede", "bandeira", "loja"}
            else f"i.{column}" for column in columns
        )
        date = "f.id_time::date"
        tvd = "f.tvd_simplificado"
        ivd = "f.ivd_simplificado"
    return text(f"""
WITH daily AS (
  SELECT {date} AS data,{projection},
         SUM({tvd})::float8 tvd,SUM({ivd})::float8 ivd
  FROM {source}
  WHERE f.id_customer=:customer
    {"AND f.comparison_scope=:scope" if mart else ""}
    AND {date}>=DATE_TRUNC('year',CURRENT_DATE)
    {filter_sql}
  GROUP BY {date},{projection}
)
SELECT {dims},
 (ARRAY_AGG(tvd ORDER BY data DESC) FILTER (WHERE tvd IS NOT NULL))[1]::float8 AS "R$ Pré-ruptura",
 (ARRAY_AGG(ivd ORDER BY data DESC) FILTER (WHERE ivd IS NOT NULL))[1]::float8 AS "R$ Excesso"
FROM daily GROUP BY {dims}
""")


def compare_rows(expected, actual, columns, metrics, context):
    left = {key(row, columns): row for row in expected}
    right = {key(row, columns): row for row in actual}
    if left.keys() != right.keys():
        raise AssertionError({
            "context": context,
            "missing": list(left.keys() - right.keys())[:5],
            "unexpected": list(right.keys() - left.keys())[:5],
            "expected_rows": len(left), "actual_rows": len(right),
        })
    for row_key, wanted in left.items():
        got = right[row_key]
        for metric in metrics:
            if not close(wanted.get(metric), got.get(metric)):
                raise AssertionError({
                    "context": context, "row": row_key, "metric": metric,
                    "expected": wanted.get(metric), "actual": got.get(metric),
                })


def execute_chart(factory, command, chart, extra_filters=()):
    form = json.loads(chart.params)
    queries, _ = build_queries(form)
    filters = [
        {"col": "id_customer", "op": "IN", "val": [CUSTOMER_ID]},
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
        raise AssertionError({"chart": chart.slice_name, "error": response["error"]})
    return response.get("data") or [], elapsed


def chart_title(tab, scope):
    if tab == "Valor":
        return f"[Panorama] Comparativo — {scope}"
    return f"[Panorama] Comparativo {tab} — {scope}"


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
        expected_titles = [chart_title(tab, scope) for tab in TABS for scope in SCOPES]
        missing = [title for title in expected_titles if title not in charts]
        if missing:
            raise AssertionError({"missing_charts": missing})

        report = {"tenant": CUSTOMER_ID, "scopes": {}, "charts": {}}
        database = charts[expected_titles[0]].table.database
        factory = QueryContextFactory()
        with database.get_sqla_engine() as engine, engine.connect() as connection:
            expected_by_scope = {}
            gap_by_scope = {}
            for scope, columns in SCOPES.items():
                source = list(connection.execute(
                    history_sql(columns, mart=False), {"customer": CUSTOMER_ID}
                ).mappings())
                mart = list(connection.execute(
                    history_sql(columns, mart=True), {"customer": CUSTOMER_ID}
                ).mappings())
                history_metrics = tuple(metric for tab, metrics in TABS.items()
                                        if tab != "Falta x Excesso" for metric in metrics)
                compare_rows(source, mart, columns, history_metrics, f"source-mart:{scope}")
                gap_source = list(connection.execute(
                    gap_sql(columns, mart=False), {"customer": CUSTOMER_ID}
                ).mappings())
                gap_mart = list(connection.execute(
                    gap_sql(columns, mart=True), {
                        "customer": CUSTOMER_ID,
                        "scope": next(key for key, value in {
                            "region": SCOPES["Região"],
                            "retail": SCOPES["Varejo"],
                            "hierarchy": SCOPES["Hierarquia de item"],
                        }.items() if value == columns),
                    }
                ).mappings())
                compare_rows(
                    gap_source, gap_mart, columns, TABS["Falta x Excesso"],
                    f"source-mart-gap:{scope}",
                )
                expected_by_scope[scope] = source
                gap_by_scope[scope] = gap_source
                report["scopes"][scope] = {
                    "history_rows": len(source), "gap_rows": len(gap_source)
                }

            for tab, metrics in TABS.items():
                for scope, columns in SCOPES.items():
                    title = chart_title(tab, scope)
                    chart = charts[title]
                    params = json.loads(chart.params)
                    if params.get("viz_type") != "pivot_table_v2":
                        raise AssertionError(f"{title}: expected pivot_table_v2")
                    if tuple(params.get("groupbyRows") or ()) != columns:
                        raise AssertionError(f"{title}: hierarchy diverged")
                    if int(params.get("row_limit", 0)) < 10000:
                        raise AssertionError(f"{title}: row limit truncates PBIP matrix")
                    configured_metrics = tuple(
                        metric.get("label") if isinstance(metric, dict) else metric
                        for metric in params.get("metrics") or ()
                    )
                    if configured_metrics != metrics:
                        raise AssertionError({
                            "chart": title, "expected_metrics": metrics,
                            "actual_metrics": configured_metrics,
                        })
                    if params.get("rowOrder") != "value_z_to_a" or not params.get("order_desc"):
                        raise AssertionError(f"{title}: PBIP descending order diverged")
                    rows, elapsed = execute_chart(factory, ChartDataCommand, chart)
                    expected = gap_by_scope[scope] if tab == "Falta x Excesso" else expected_by_scope[scope]
                    compare_rows(expected, rows, columns, metrics, f"source-chart:{title}")
                    report["charts"][title] = {
                        "rows": len(rows), "elapsed_ms": round(elapsed, 2),
                        "metrics": list(metrics),
                    }

            # Prove that a native filter is pushed below aggregation.  This
            # exercises the detailed fallback while the default path above
            # exercises the compact daily mart.
            filter_value = connection.execute(text("""
                SELECT rede
                FROM gold.nr_panorama_comparison_history_detail
                WHERE id_customer=:customer AND data>=DATE_TRUNC('year',CURRENT_DATE)
                  AND rede IS NOT NULL
                GROUP BY rede ORDER BY COUNT(*) DESC LIMIT 1
            """), {"customer": CUSTOMER_ID}).scalar_one()
            region_columns = SCOPES["Região"]
            filtered_history = list(connection.execute(
                history_sql(region_columns, mart=False, filter_sql="AND l.rede=:filter_value"),
                {"customer": CUSTOMER_ID, "filter_value": filter_value},
            ).mappings())
            filtered_gap = list(connection.execute(
                gap_sql(region_columns, mart=False, filter_sql="AND l.rede=:filter_value"),
                {"customer": CUSTOMER_ID, "filter_value": filter_value},
            ).mappings())
            native_filter = ({"col": "rede", "op": "IN", "val": [filter_value]},)
            value_rows, value_ms = execute_chart(
                factory, ChartDataCommand, charts[chart_title("Valor", "Região")], native_filter
            )
            gap_rows, gap_ms = execute_chart(
                factory, ChartDataCommand,
                charts[chart_title("Falta x Excesso", "Região")], native_filter,
            )
            compare_rows(
                filtered_history, value_rows, region_columns, TABS["Valor"],
                "filtered-source-chart:Valor:Região",
            )
            compare_rows(
                filtered_gap, gap_rows, region_columns, TABS["Falta x Excesso"],
                "filtered-source-chart:Falta x Excesso:Região",
            )
            report["native_filter_probe"] = {
                "rede": filter_value,
                "value_rows": len(value_rows), "value_elapsed_ms": round(value_ms, 2),
                "gap_rows": len(gap_rows), "gap_elapsed_ms": round(gap_ms, 2),
            }

        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
