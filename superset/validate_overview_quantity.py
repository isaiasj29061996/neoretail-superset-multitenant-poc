"""Reconcile Quantity Overview source, marts, Superset and displayed periods."""
from __future__ import annotations

import os

import json
import math
from datetime import date, datetime

from flask import g
from flask_login import login_user
from sqlalchemy import text
from superset.app import create_app

from profile_dashboard_performance import build_queries

CUSTOMER_ID = int(os.getenv("NEORETAIL_VALIDATION_CUSTOMER", "142"))
MEASURE = "unidade"
DASHBOARD = "neoretail-v9-visao-geral-quantidade"

CARDS = {
    "[Visão quantidade] Vendas": {"labels": ["Venda quantidade"], "profile": "direct_average"},
    "[Visão quantidade] Perda de vendas OSA": {"labels": ["Perda OSA quantidade"], "profile": "direct_sum"},
    "[Visão quantidade] Preço médio": {
        "labels": ["Preço soma elegível", "Preço linhas elegíveis"],
        "profile": "weighted_average", "disable_ly": True,
    },
    "[Visão quantidade] Distribuição e sortimento": {
        "labels": ["Quantidade de lojas", "Quantidade de itens", "Lojas U3M", "Itens U3M"],
        "profile": "distribution_bundle", "outputs": 2,
    },
    "[Visão quantidade] % OSA": {
        "labels": ["OSA problemas", "OSA ativos"], "profile": "one_minus_ratio",
        "tasks": ["Itens críticos OSA", "Itens risco OSA"],
    },
    "[Visão quantidade] Ruptura": {
        "labels": ["Ruptura numerador", "Status item denominador"], "profile": "ratio_percent",
        "tasks": ["Itens críticos Ruptura", "Itens risco Ruptura"],
    },
    "[Visão quantidade] Item sem venda": {
        "labels": ["ISV numerador", "Status item denominador"], "profile": "ratio_percent",
        "tasks": ["Itens críticos ISV", "Itens risco ISV"],
    },
    "[Visão quantidade] Cobertura de estoque": {
        "labels": ["Estoque unidades", "Demanda média"], "profile": "ratio",
    },
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

SOURCE_COLUMNS = [
    "sales_sum", "loss_sum", "price_numerator", "price_count",
    "osa_problem_sum", "osa_active_sum", "rupture_sum", "status_sum",
    "isv_sum", "stock_sum", "demand_sum", "store_count", "item_count",
    "store_count_u3m", "item_count_u3m",
]


def blank(value):
    return value is None or (isinstance(value, float) and math.isnan(value))


def close(left, right):
    if blank(left) or blank(right):
        return blank(left) and blank(right)
    return math.isclose(float(left), float(right), rel_tol=1e-10, abs_tol=1e-8)


def month_date(value):
    if isinstance(value, datetime):
        return value.date().replace(day=1)
    if isinstance(value, date):
        return value.replace(day=1)
    return date.fromisoformat(str(value)[:10]).replace(day=1)


def shift_month(value, offset):
    value = month_date(value)
    index = value.year * 12 + value.month - 1 + offset
    return date(index // 12, index % 12 + 1, 1)


def semantic_value(profile, components):
    if profile in {"direct_average", "direct_sum"}:
        return [components[0]]
    if profile == "distribution_bundle":
        return components[:2]
    numerator, denominator = components[:2]
    if blank(numerator) or blank(denominator) or float(denominator) == 0:
        return [None]
    if profile == "weighted_average":
        return [float(numerator) / float(denominator)]
    if profile == "one_minus_ratio":
        return [100 * (1 - float(numerator) / float(denominator))]
    if profile == "ratio_percent":
        return [100 * float(numerator) / float(denominator)]
    if profile == "ratio":
        return [float(numerator) / float(denominator)]
    raise AssertionError(f"Unknown semantic profile: {profile}")


def semantic_aggregate(profile, rows, index):
    available = [row for row in rows if row is not None]
    if profile == "direct_average":
        values = [row["values"][index] for row in available if row["values"][index] is not None]
        return sum(values) / 3 if values else None
    if profile == "direct_sum":
        values = [row["values"][index] for row in available if row["values"][index] is not None]
        return sum(values) if values else None
    if profile == "distribution_bundle":
        if not available:
            return None
        latest = max(available, key=lambda row: row["date"])
        value = latest["components"][index + 2]
        return None if value is None else float(value)
    width = max((len(row["components"]) for row in available), default=2)
    components = []
    for component_index in range(width):
        values = [row["components"][component_index] for row in available
                  if row["components"][component_index] is not None]
        components.append(sum(values) if values else None)
    return semantic_value(profile, components)[index]


def semantic_rows(rows, labels, profile, *, mart):
    result = []
    for row in rows:
        components = [row[MART_COLUMNS[label] if mart else label] for label in labels]
        components = [None if blank(value) else value for value in components]
        result.append({
            "date": month_date(row["data"]),
            "components": components,
            "values": semantic_value(profile, components),
        })
    return result


def displayed_periods(rows, profile, outputs=1, disable_ly=False):
    by_month = {row["date"]: row for row in rows}
    latest = max(by_month) if by_month else None
    result = []
    for index in range(outputs):
        current = by_month.get(latest) if latest else None
        previous = by_month.get(shift_month(latest, -1)) if latest else None
        u3m = [by_month.get(shift_month(latest, offset)) for offset in (-1, -2, -3)] if latest else []
        if disable_ly:
            ly_current = ly_previous = ly_u3m = None
        else:
            ly_current_row = by_month.get(shift_month(latest, -12)) if latest else None
            ly_previous_row = by_month.get(shift_month(latest, -13)) if latest else None
            ly_rows = [by_month.get(shift_month(latest, offset)) for offset in (-13, -14, -15)] if latest else []
            ly_current = ly_current_row["values"][index] if ly_current_row else None
            ly_previous = ly_previous_row["values"][index] if ly_previous_row else None
            ly_u3m = semantic_aggregate(profile, ly_rows, index) if latest else None
        result.append({
            "mtd": current["values"][index] if current else None,
            "m_1": previous["values"][index] if previous else None,
            "u3m": semantic_aggregate(profile, u3m, index) if latest else None,
            "mtd_ly": ly_current,
            "m_1_ly": ly_previous,
            "u3m_ly": ly_u3m,
        })
    return result


def assert_periods(chart_name, expected, actual):
    mismatches = {}
    for index, expected_values in enumerate(expected):
        for period, expected_value in expected_values.items():
            actual_value = actual[index][period]
            if not close(expected_value, actual_value):
                mismatches[f"metric_{index}.{period}"] = {
                    "independent": expected_value, "frontend_contract": actual_value,
                }
    if mismatches:
        raise AssertionError(f"{chart_name} period divergence: {mismatches}")


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


def execute_option_query(factory, command, dataset):
    query = {
        "columns": ["nm_measure"], "metrics": [],
        "filters": [{"col": "id_customer", "op": "IN", "val": [CUSTOMER_ID]}],
        "orderby": [], "row_limit": 1000,
    }
    result = command(factory.create(
        datasource={"id": dataset.id, "type": "table"}, queries=[query],
        form_data={"force": True},
    )).run()
    response = result.get("queries", [])[0]
    if response.get("error"):
        raise AssertionError(response["error"])
    return sorted({row["nm_measure"] for row in response.get("data", [])})


SOURCE_MONTHLY_SQL = text("""
WITH monthly AS (
  SELECT f.mes_ano::date data,f.id_customer,
    SUM(COALESCE(f.volume_unidades,0))::float8 volume_sum,
    SUM(COALESCE(f.faturamento,0))::float8 faturamento_sum,
    SUM(COALESCE(f.qtd_perda_osa,0))::float8 loss_qty_sum,
    SUM(COALESCE(f.avg_sales_price,0)) FILTER (WHERE f.faturamento>0)::float8 price_sum,
    COUNT(f.avg_sales_price) FILTER (WHERE f.faturamento>0)::bigint price_count,
    SUM(COALESCE(f.qtd_problemas_osa,0))::float8 osa_problem_sum,
    SUM(COALESCE(f.qtd_item_ativo_osa,0))::float8 osa_active_sum,
    SUM(COALESCE(f.rup,0))::float8 rupture_sum,
    SUM(COALESCE(f.status_item_geral,0))::float8 status_sum,
    SUM(COALESCE(f.est_virtual,0))::float8 isv_sum,
    SUM(COALESCE(f.estoque_unidades,0))::float8 stock_sum,
    SUM(COALESCE(f.demanda_media,0))::float8 demand_sum,
    COUNT(DISTINCT f.cnpj) FILTER (WHERE f.positivacao=1)::bigint store_count,
    COUNT(DISTINCT f.ean) FILTER (WHERE f.positivacao=1)::bigint item_count
  FROM gold.fato_historico f WHERE f.id_customer=:customer
  GROUP BY f.mes_ano,f.id_customer
), factors AS (
  SELECT f.mes_ano::date data,f.id_customer,MAX(c.conversion_rate)::float8 conversion_factor
  FROM gold.fato_historico f
  JOIN gold.dim_conversao c ON c.id_customer=f.id_customer AND c.id_item::text=f.id_item
    AND c.nm_measure=:measure
  WHERE f.id_customer=:customer GROUP BY f.mes_ano,f.id_customer
), expanded AS (
  SELECT m.*,k.conversion_factor FROM monthly m JOIN factors k USING(data,id_customer)
  WHERE :measure <> 'valor'
  UNION ALL SELECT m.*,NULL::float8 FROM monthly m WHERE :measure='valor'
), distribution_u3m AS (
  SELECT a.mes_ano::date data,a.id_customer,
    COUNT(DISTINCT f.cnpj) FILTER (WHERE f.positivacao=1)::bigint store_count_u3m,
    COUNT(DISTINCT f.ean) FILTER (WHERE f.positivacao=1)::bigint item_count_u3m
  FROM (SELECT DISTINCT mes_ano,id_customer FROM gold.fato_historico WHERE id_customer=:customer) a
  JOIN gold.fato_historico f ON f.id_customer=a.id_customer
    AND f.mes_ano>=a.mes_ano-INTERVAL '2 months' AND f.mes_ano<=a.mes_ano
  GROUP BY a.mes_ano,a.id_customer
)
SELECT e.data,e.id_customer,
  CASE WHEN :measure='valor' THEN e.faturamento_sum ELSE e.volume_sum*e.conversion_factor END::float8 sales_sum,
  CASE WHEN :measure='valor' THEN NULL ELSE e.loss_qty_sum*e.conversion_factor END::float8 loss_sum,
  (e.price_sum*e.conversion_factor)::float8 price_numerator,e.price_count,
  e.osa_problem_sum,e.osa_active_sum,e.rupture_sum,e.status_sum,e.isv_sum,e.stock_sum,e.demand_sum,
  e.store_count,e.item_count,d.store_count_u3m,d.item_count_u3m
FROM expanded e JOIN distribution_u3m d USING(data,id_customer) ORDER BY e.data
""")

TASKS_SQL = text("""
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
""")


def main():
    app = create_app()
    with app.test_request_context("/"):
        from superset import db, security_manager
        from superset.commands.chart.data.get_data_command import ChartDataCommand
        from superset.common.query_context_factory import QueryContextFactory
        from superset.connectors.sqla.models import SqlaTable
        from superset.models.dashboard import Dashboard

        admin = security_manager.find_user(username="admin") or db.session.query(security_manager.user_model).first()
        login_user(admin)
        g.user = admin
        dashboard = db.session.query(Dashboard).filter(Dashboard.slug == DASHBOARD).one()
        charts = {chart.slice_name: chart for chart in dashboard.slices}
        factory = QueryContextFactory()
        database = next(iter(charts.values())).table.database
        conversion_dataset = db.session.query(SqlaTable).filter(
            SqlaTable.database_id == database.id,
            SqlaTable.table_name == "nr_conversion_options",
        ).one()

        metadata = json.loads(dashboard.json_metadata or "{}")
        measure_filter = next(item for item in metadata["native_filter_configuration"]
                              if item["targets"][0]["column"]["name"] == "nm_measure")
        if measure_filter["targets"][0]["datasetId"] != conversion_dataset.id:
            raise AssertionError("Medida filter is not mapped to nr_conversion_options")
        if measure_filter["controlValues"].get("multiSelect") is not False:
            raise AssertionError("Medida filter must remain single-select")
        default_values = measure_filter["defaultDataMask"]["filterState"].get("value")
        if default_values != ["unidade"]:
            raise AssertionError(f"Unexpected Medida default: {default_values}")

        superset_options = execute_option_query(factory, ChartDataCommand, conversion_dataset)
        with database.get_sqla_engine() as engine, engine.connect() as connection:
            real_options = [row[0] for row in connection.execute(text("""
                SELECT nm_measure FROM gold.nr_conversion_options
                WHERE id_customer=:customer ORDER BY lower(nm_measure)
            """), {"customer": CUSTOMER_ID})]
            dimension_options = [row[0] for row in connection.execute(text("""
                SELECT DISTINCT nm_measure FROM gold.dim_conversao
                WHERE id_customer=:customer ORDER BY nm_measure
            """), {"customer": CUSTOMER_ID})]
            expected_options = sorted({*dimension_options, "valor"})
            if sorted(real_options) != expected_options or superset_options != expected_options:
                raise AssertionError({
                    "conversion_dataset": real_options,
                    "dim_conversao_plus_valor": expected_options,
                    "superset": superset_options,
                })
            print(json.dumps({
                "measure_filter": "reconciled", "dataset": "nr_conversion_options",
                "single_select": True, "default": "unidade", "options": superset_options,
            }, ensure_ascii=False))

            filters = [
                {"col": "id_customer", "op": "IN", "val": [CUSTOMER_ID]},
                {"col": "nm_measure", "op": "IN", "val": [MEASURE]},
            ]
            mart_rows = list(connection.execute(text("""
                SELECT * FROM gold.nr_overview_quantity_default
                WHERE id_customer=:customer AND nm_measure=:measure ORDER BY data
            """), {"customer": CUSTOMER_ID, "measure": MEASURE}).mappings())
            source_rows = list(connection.execute(SOURCE_MONTHLY_SQL, {
                "customer": CUSTOMER_ID, "measure": MEASURE,
            }).mappings())
            if len(source_rows) != len(mart_rows):
                raise AssertionError(f"Source/mart month count: {len(source_rows)} != {len(mart_rows)}")
            mart_by_month = {month_date(row["data"]): row for row in mart_rows}
            source_mismatches = {}
            for source in source_rows:
                month = month_date(source["data"])
                mart = mart_by_month.get(month)
                for column in SOURCE_COLUMNS:
                    if mart is None or not close(source[column], mart[column]):
                        source_mismatches[f"{month}.{column}"] = {
                            "source": source[column], "mart": None if mart is None else mart[column],
                        }
            if source_mismatches:
                raise AssertionError(f"Source/mart divergence: {source_mismatches}")

            task_source = connection.execute(TASKS_SQL, {"customer": CUSTOMER_ID}).mappings().one()
            latest_mart = mart_rows[-1]
            task_columns = [MART_COLUMNS[label] for contract in CARDS.values()
                            for label in contract.get("tasks", [])]
            task_mismatches = {column: {"source": task_source[column], "mart": latest_mart[column]}
                               for column in task_columns
                               if not close(task_source[column], latest_mart[column])}
            if task_mismatches:
                raise AssertionError(f"Task source/mart divergence: {task_mismatches}")
            print(json.dumps({
                "source_to_mart": "reconciled", "months": len(source_rows),
                "columns": SOURCE_COLUMNS, "tasks": task_columns,
            }, ensure_ascii=False))

            for chart_name, contract in CARDS.items():
                response = execute(factory, ChartDataCommand, charts[chart_name], filters)
                superset_rows = response.get("data") or []
                if not superset_rows:
                    raise AssertionError(f"{chart_name}: Superset returned no rows")
                sql = response.get("query") or response.get("sql") or ""
                if "nr_overview_quantity_default" not in sql:
                    raise AssertionError(f"{chart_name}: compact mart not used")
                response_by_month = {month_date(row["data"]): row for row in superset_rows}
                labels = [*contract["labels"], *contract.get("tasks", [])]
                component_mismatches = {}
                for month, mart in mart_by_month.items():
                    response_row = response_by_month.get(month)
                    for label in labels:
                        actual = None if response_row is None else response_row.get(label)
                        expected = mart[MART_COLUMNS[label]]
                        if not close(expected, actual):
                            component_mismatches[f"{month}.{label}"] = {
                                "mart": expected, "superset": actual,
                            }
                if component_mismatches:
                    raise AssertionError(f"{chart_name} mart/Superset divergence: {component_mismatches}")

                independent = semantic_rows(source_rows, contract["labels"], contract["profile"], mart=True)
                frontend_contract = semantic_rows(superset_rows, contract["labels"], contract["profile"], mart=False)
                expected_periods = displayed_periods(
                    independent, contract["profile"], contract.get("outputs", 1),
                    contract.get("disable_ly", False),
                )
                actual_periods = displayed_periods(
                    frontend_contract, contract["profile"], contract.get("outputs", 1),
                    contract.get("disable_ly", False),
                )
                assert_periods(chart_name, expected_periods, actual_periods)
                form = json.loads(charts[chart_name].params)
                if contract.get("disable_ly") and form.get("semantic_disable_ly") is not True:
                    raise AssertionError(f"{chart_name}: LY must remain disabled without original DAX")
                print(json.dumps({
                    "chart": chart_name, "months": len(superset_rows),
                    "period_status": "PARCIAL_CALENDARIO", "periods": actual_periods,
                }, ensure_ascii=False))

            option_results = {}
            option_charts = [
                "[Visão quantidade] Vendas", "[Visão quantidade] Perda de vendas OSA",
                "[Visão quantidade] Preço médio",
            ]
            for option in superset_options:
                option_filters = [
                    {"col": "id_customer", "op": "IN", "val": [CUSTOMER_ID]},
                    {"col": "nm_measure", "op": "IN", "val": [option]},
                ]
                option_results[option] = {}
                for chart_name in option_charts:
                    response = execute(factory, ChartDataCommand, charts[chart_name], option_filters)
                    rows = response.get("data") or []
                    if not rows:
                        raise AssertionError(f"{chart_name}/{option}: no data")
                    latest = max(rows, key=lambda row: month_date(row["data"]))
                    contract = CARDS[chart_name]
                    components = [latest.get(label) for label in contract["labels"]]
                    value = semantic_value(contract["profile"], components)[0]
                    mart = connection.execute(text("""
                        SELECT * FROM gold.nr_overview_quantity_default
                        WHERE id_customer=:customer AND nm_measure=:measure
                        ORDER BY data DESC LIMIT 1
                    """), {"customer": CUSTOMER_ID, "measure": option}).mappings().one()
                    expected_components = [mart[MART_COLUMNS[label]] for label in contract["labels"]]
                    expected = semantic_value(contract["profile"], expected_components)[0]
                    if not close(expected, value):
                        raise AssertionError(f"{chart_name}/{option}: {value} != {expected}")
                    option_results[option][chart_name.removeprefix("[Visão quantidade] ")] = value
            print(json.dumps({"measure_results": option_results}, ensure_ascii=False))

            filtered = execute(factory, ChartDataCommand, charts["[Visão quantidade] Vendas"], [
                *filters, {"col": "rede", "op": "IN", "val": [os.getenv("NEORETAIL_VALIDATION_REDE", "AKKIATACADO")]},
            ])
            filtered_sql = filtered.get("query") or filtered.get("sql") or ""
            if "nr_overview_quantity_detail" not in filtered_sql or "nr_overview_quantity_default" in filtered_sql:
                raise AssertionError("Filtered request did not switch to the detailed semantic path")
            if not (filtered.get("data") or []):
                raise AssertionError("Filtered request returned no rows")
            print(json.dumps({
                "filtered_chart": "Vendas", "rows": len(filtered["data"]),
                "source": "nr_overview_quantity_detail",
                "rede": os.getenv("NEORETAIL_VALIDATION_REDE", "AKKIATACADO"),
            }, ensure_ascii=False))


if __name__ == "__main__":
    main()
