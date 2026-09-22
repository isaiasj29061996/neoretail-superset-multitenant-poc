"""Reconcile quantity Overview between source facts, serving mart and Superset."""
from __future__ import annotations

import json
import math

from flask import g
from flask_login import login_user
from sqlalchemy import text
from superset.app import create_app

from profile_dashboard_performance import build_queries

CUSTOMER_ID = 142
MEASURE = "unidade"
DASHBOARD = "neoretail-v9-visao-geral-quantidade"
CASES = {
    "[Visão quantidade] Vendas": ["Venda quantidade"],
    "[Visão quantidade] Perda de vendas OSA": ["Perda OSA quantidade"],
    "[Visão quantidade] Preço médio": ["Preço soma elegível", "Preço linhas elegíveis"],
    "[Visão quantidade] Distribuição e sortimento": ["Quantidade de lojas", "Quantidade de itens", "Lojas U3M", "Itens U3M"],
    "[Visão quantidade] % OSA": ["OSA problemas", "OSA ativos", "Itens críticos OSA", "Itens risco OSA"],
    "[Visão quantidade] Ruptura": ["Ruptura numerador", "Status item denominador", "Itens críticos Ruptura", "Itens risco Ruptura"],
    "[Visão quantidade] Item sem venda": ["ISV numerador", "Status item denominador", "Itens críticos ISV", "Itens risco ISV"],
    "[Visão quantidade] Cobertura de estoque": ["Estoque unidades", "Demanda média"],
}
MART_COLUMNS = {
    "Venda quantidade": "sales_sum", "Perda OSA quantidade": "loss_sum",
    "Preço soma elegível": "price_numerator", "Preço linhas elegíveis": "price_count",
    "Quantidade de lojas": "store_count", "Quantidade de itens": "item_count",
    "Lojas U3M": "store_count_u3m", "Itens U3M": "item_count_u3m",
    "OSA problemas": "osa_problem_sum", "OSA ativos": "osa_active_sum",
    "Itens críticos OSA": "osa_critical_count", "Itens risco OSA": "osa_risk_count",
    "Ruptura numerador": "rupture_sum", "Status item denominador": "status_sum",
    "Itens críticos Ruptura": "rupture_critical_count", "Itens risco Ruptura": "rupture_risk_count",
    "ISV numerador": "isv_sum", "Itens críticos ISV": "isv_critical_count",
    "Itens risco ISV": "isv_risk_count", "Estoque unidades": "stock_sum",
    "Demanda média": "demand_sum",
}


def execute(factory, command, chart, filters):
    form = json.loads(chart.params)
    queries, _ = build_queries(form)
    for query in queries:
        query["filters"] = [*query.get("filters", []), *filters]
    g.form_data = {"extra_filters": filters}
    result = command(factory.create(
        datasource={"id": chart.datasource_id, "type": "table"}, queries=queries,
        form_data={**form, "force": True, "extra_filters": filters},
    )).run()
    g.form_data = {}
    response = result.get("queries", [])[0]
    if response.get("error"):
        raise AssertionError(response["error"])
    return response


def close(left, right):
    if left is None or right is None:
        return left is None and right is None
    return math.isclose(float(left), float(right), rel_tol=1e-10, abs_tol=1e-8)


def main():
    app = create_app()
    with app.test_request_context("/"):
        from superset import db, security_manager
        from superset.commands.chart.data.get_data_command import ChartDataCommand
        from superset.common.query_context_factory import QueryContextFactory
        from superset.models.dashboard import Dashboard

        admin = security_manager.find_user(username="admin") or db.session.query(security_manager.user_model).first()
        login_user(admin)
        g.user = admin
        dashboard = db.session.query(Dashboard).filter(Dashboard.slug == DASHBOARD).one()
        charts = {chart.slice_name: chart for chart in dashboard.slices}
        factory = QueryContextFactory()
        filters = [
            {"col": "id_customer", "op": "IN", "val": [CUSTOMER_ID]},
            {"col": "nm_measure", "op": "IN", "val": [MEASURE]},
        ]
        database = next(iter(charts.values())).table.database
        with database.get_sqla_engine() as engine, engine.connect() as connection:
            mart = connection.execute(text("""
                SELECT * FROM gold.nr_overview_quantity_default
                WHERE id_customer=:customer AND nm_measure=:measure
                ORDER BY data DESC LIMIT 1
            """), {"customer": CUSTOMER_ID, "measure": MEASURE}).mappings().one()
            source = connection.execute(text("""
                WITH latest AS (
                    SELECT MAX(mes_ano) AS data FROM gold.fato_historico
                    WHERE id_customer=:customer
                ), factor AS (
                    SELECT MAX(c.conversion_rate)::float8 AS value
                    FROM gold.fato_historico f
                    JOIN latest x ON x.data=f.mes_ano
                    JOIN gold.dim_conversao c
                      ON c.id_customer=f.id_customer AND c.id_item::text=f.id_item
                     AND c.nm_measure=:measure
                    WHERE f.id_customer=:customer
                ), facts AS (
                    SELECT
                      SUM(COALESCE(f.volume_unidades,0))*MAX(k.value) sales_sum,
                      SUM(COALESCE(f.qtd_perda_osa,0))*MAX(k.value) loss_sum,
                      SUM(COALESCE(f.avg_sales_price,0)) FILTER (WHERE f.faturamento>0)*MAX(k.value) price_numerator,
                      COUNT(f.avg_sales_price) FILTER (WHERE f.faturamento>0)::bigint price_count,
                      SUM(COALESCE(f.qtd_problemas_osa,0)) osa_problem_sum,
                      SUM(COALESCE(f.qtd_item_ativo_osa,0)) osa_active_sum,
                      SUM(COALESCE(f.rup,0)) rupture_sum,
                      SUM(COALESCE(f.status_item_geral,0)) status_sum,
                      SUM(COALESCE(f.est_virtual,0)) isv_sum,
                      SUM(COALESCE(f.estoque_unidades,0)) stock_sum,
                      SUM(COALESCE(f.demanda_media,0)) demand_sum,
                      COUNT(DISTINCT COALESCE(f.cnpj,l.cnpj)) FILTER (WHERE f.positivacao=1)::bigint store_count,
                      COUNT(DISTINCT COALESCE(f.ean,i.cd_ean)) FILTER (WHERE f.positivacao=1)::bigint item_count
                    FROM gold.fato_historico f JOIN latest x ON x.data=f.mes_ano CROSS JOIN factor k
                    LEFT JOIN gold.dim_local l ON l.id_customer=f.id_customer AND l.id_location=f.id_location
                    LEFT JOIN gold.dim_itens i ON i.id_customer=f.id_customer AND i.id_item=f.id_item
                    WHERE f.id_customer=:customer
                ), tasks AS (
                    SELECT
                      COUNT(o.id_item) FILTER (WHERE COALESCE(o.qtd_problemas_osa_m0,0)>0 AND a.nm_activity_level='Fast Mover')::bigint osa_critical_count,
                      COUNT(o.id_item) FILTER (WHERE COALESCE(o.qtd_problemas_osa_m0,0)>0 AND o.max_tp_activity_level='S')::bigint osa_risk_count,
                      COUNT(o.id_item) FILTER (WHERE COALESCE(o.rup,0)>0 AND o.max_tp_activity_level='F')::bigint rupture_critical_count,
                      COUNT(o.id_item) FILTER (WHERE COALESCE(o.rup,0)>0 AND o.max_tp_activity_level='S')::bigint rupture_risk_count,
                      COUNT(o.id_item) FILTER (WHERE COALESCE(o.est_virtual,0)>0 AND o.max_tp_activity_level='F')::bigint isv_critical_count,
                      COUNT(o.id_item) FILTER (WHERE COALESCE(o.est_virtual,0)>0 AND o.max_tp_activity_level='S')::bigint isv_risk_count
                    FROM gold.calculo_oportunidades o
                    LEFT JOIN gold.dim_nivel_atividade a
                      ON a.id_customer=o.id_customer AND a.tp_activity_level=o.max_tp_activity_level
                    WHERE o.id_customer=:customer
                ) SELECT * FROM facts CROSS JOIN tasks
            """), {"customer": CUSTOMER_ID, "measure": MEASURE}).mappings().one()
            source_columns = [
                "sales_sum", "loss_sum", "price_numerator", "price_count",
                "osa_problem_sum", "osa_active_sum", "rupture_sum", "status_sum",
                "isv_sum", "stock_sum", "demand_sum", "store_count", "item_count",
                "osa_critical_count", "osa_risk_count", "rupture_critical_count",
                "rupture_risk_count", "isv_critical_count", "isv_risk_count",
            ]
            source_mismatches = {
                column: {"source": source[column], "mart": mart[column]}
                for column in source_columns if not close(source[column], mart[column])
            }
            if source_mismatches:
                raise AssertionError(f"Source/mart divergence: {source_mismatches}")
            print(json.dumps({"source_to_mart": "reconciled", "columns": source_columns}, ensure_ascii=False))
            for chart_name, labels in CASES.items():
                response = execute(factory, ChartDataCommand, charts[chart_name], filters)
                rows = response.get("data") or []
                if not rows:
                    raise AssertionError(f"{chart_name}: Superset returned no rows")
                latest = max(rows, key=lambda row: str(row.get("data") or ""))
                mismatches = {
                    label: {"mart": mart[MART_COLUMNS[label]], "superset": latest.get(label)}
                    for label in labels if not close(mart[MART_COLUMNS[label]], latest.get(label))
                }
                if mismatches:
                    raise AssertionError(f"{chart_name}: {mismatches}")
                sql = response.get("query") or response.get("sql") or ""
                if "nr_overview_quantity_default" not in sql:
                    raise AssertionError(f"{chart_name}: compact mart not used")
                print(json.dumps({"chart": chart_name, "rows": len(rows), "latest": str(latest.get("data"))[:10], "reconciled": labels}, ensure_ascii=False))

            filtered = execute(factory, ChartDataCommand, charts["[Visão quantidade] Vendas"], [
                *filters, {"col": "rede", "op": "IN", "val": ["AKKIATACADO"]},
            ])
            filtered_sql = filtered.get("query") or filtered.get("sql") or ""
            if "nr_overview_quantity_detail" not in filtered_sql or "nr_overview_quantity_default" in filtered_sql:
                raise AssertionError("Filtered request did not switch to the detailed semantic path")
            if not (filtered.get("data") or []):
                raise AssertionError("Filtered request returned no rows")
            print(json.dumps({"filtered_chart": "Vendas", "rows": len(filtered["data"]), "source": "nr_overview_quantity_detail"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
