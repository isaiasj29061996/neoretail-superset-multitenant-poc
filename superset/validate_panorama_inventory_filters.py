"""Reconcile filtered inventory ChartData with raw facts, including weekly summaries."""
from __future__ import annotations

import json

from flask import g
from flask_login import login_user
from sqlalchemy import text
from superset.app import create_app

from validate_panorama_stock import (
    MONTHLY_SOURCE as STOCK_MONTHLY, WEEKLY_SOURCE as STOCK_WEEKLY,
    NON_UNIT_MEASURE,
)
from validate_panorama_inventory_tabs import (
    CUSTOMER_ID, DASHBOARD, MONTHLY_SOURCE, WEEKLY_SOURCE, close, execute, json_safe,
)


COMPONENTS = {
    "Estoque": {"Estoque preço custo": "stock_cost_sum", "Estoque quantidade": "stock_qty_sum"},
    "Giro x ROI": {
        "Estoque preço custo": "stock_cost_sum", "Venda sell out": "sellout_sum",
        "Venda custo": "sales_cost_sum", "Estoque custo ROI": "stock_cost_sum",
        "Giro soma": "giro_num", "Giro linhas": "giro_den",
    },
    "OSA": {
        "OSA problemas": "osa_problem_sum", "OSA ativos": "osa_active_sum",
        "Ruptura numerador": "rupture_sum", "Ruptura denominador": "status_sum",
        "ISV numerador": "isv_sum", "ISV denominador": "status_sum",
    },
}


def filtered_source(source, column, operator):
    # Only internal, allowlisted identifiers enter SQL; values remain bound.
    table, key = {"uf": ("dim_local", "id_location"), "item": ("dim_itens", "id_item")}[column]
    predicate = (
        f"f.{key} IN (SELECT d.{key} FROM gold.{table} d "
        f"WHERE d.id_customer=:customer AND d.{column} {operator} (:dimension))"
    )
    sql = str(source).replace(
        "WHERE f.id_customer=:customer", f"WHERE f.id_customer=:customer AND {predicate}",
    )
    # TOP 13 is selected within the filtered context. The global latest week
    # used for Giro BLANK deliberately remains tenant-wide.
    sql = sql.replace(
        "FROM gold.fato_semanal\n  WHERE id_customer=:customer",
        f"FROM gold.fato_semanal f\n  WHERE f.id_customer=:customer AND {predicate}",
    )
    return text(sql)


def compare_components(expected, actual, components, context):
    expected_dates = {str(row["data"])[:10]: row for row in expected}
    actual_dates = {str(row["data"])[:10]: json_safe(row) for row in actual}
    if not expected_dates or expected_dates.keys() != actual_dates.keys():
        raise AssertionError(f"{context}: empty or mismatched periods")
    for date, row in expected_dates.items():
        for label, component in components.items():
            if not close(row[component], actual_dates[date].get(label)):
                raise AssertionError({"context": context, "date": date, "metric": label,
                                      "expected": row[component], "actual": actual_dates[date].get(label)})


def main():
    app = create_app()
    with app.test_request_context("/"):
        from superset import db, security_manager
        from superset.commands.chart.data.get_data_command import ChartDataCommand
        from superset.common.query_context_factory import QueryContextFactory
        from superset.models.dashboard import Dashboard

        admin = security_manager.find_user(username="admin")
        login_user(admin)
        g.user = admin
        dashboard = db.session.query(Dashboard).filter(Dashboard.slug == DASHBOARD).one()
        charts = {chart.slice_name: chart for chart in dashboard.slices}
        database = next(iter(charts.values())).table.database
        factory = QueryContextFactory()
        report = []
        with database.get_sqla_engine() as engine, engine.connect() as connection:
            measure = connection.execute(NON_UNIT_MEASURE, {"customer": CUSTOMER_ID}).scalar()
            measures = list(dict.fromkeys(["unidade", measure])) if measure else ["unidade"]
            for column, operator in (("uf", "IN"), ("item", "IN"), ("uf", "NOT IN")):
                table = "dim_local" if column == "uf" else "dim_itens"
                dimension = connection.execute(text(
                    f"SELECT {column} FROM gold.{table} WHERE id_customer=:customer "
                    f"AND {column} IS NOT NULL GROUP BY {column} ORDER BY COUNT(*) DESC LIMIT 1"
                ), {"customer": CUSTOMER_ID}).scalar()
                if dimension is None:
                    raise AssertionError(f"No {column} available for filter validation")
                for measure in measures:
                    params = {"customer": CUSTOMER_ID, "measure": measure, "dimension": dimension}
                    sources = {}
                    for period, source, stock in (("mensal", MONTHLY_SOURCE, STOCK_MONTHLY),
                                                  ("semanal", WEEKLY_SOURCE, STOCK_WEEKLY)):
                        sources[period] = list(connection.execute(filtered_source(source, column, operator), params).mappings())
                        sources[f"stock_{period}"] = list(connection.execute(filtered_source(stock, column, operator), params).mappings())
                    filters = [{"col": "id_customer", "op": "IN", "val": [CUSTOMER_ID]},
                               {"col": "nm_measure", "op": "IN", "val": [measure]},
                               {"col": column, "op": operator, "val": [dimension]}]
                    for tab, components in COMPONENTS.items():
                        for period in ("mensal", "semanal"):
                            name = f"[Panorama] Evolutivo de estoque — {tab} {period}"
                            responses = execute(factory, ChartDataCommand, charts[name], filters)
                            if len(responses) != (2 if period == "semanal" else 1):
                                raise AssertionError(f"{name}: unexpected query count")
                            source_key = "stock_" if tab == "Estoque" else ""
                            context = f"{tab}/{period}/{column}/{operator}/{measure}"
                            compare_components(sources[f"{source_key}{period}"], responses[0].get("data") or [], components, context)
                            if period == "semanal":
                                compare_components(sources[f"{source_key}mensal"], responses[1].get("data") or [], components, context + "/summary")
                            report.append({"context": context, "rows": len(responses[0]["data"])})
        # An embedded guest from a different tenant must see no rows even
        # when a chart request explicitly asks for the known positive tenant.
        guest = security_manager.get_guest_user_from_token({
            "user": {"username": "panorama-stock-rls-audit"},
            "resources": [{"type": "dashboard", "id": str(dashboard.id)},
                          *[{"type": "dashboard", "id": str(item.uuid)} for item in dashboard.embedded]],
            "rls_rules": [{"clause": "id_customer = -1"}],
        })
        g.user = guest
        g._login_user = guest
        rls_checks = 0
        for chart in charts.values():
            if "[Panorama] Evolutivo de estoque" not in chart.slice_name:
                continue
            responses = execute(factory, ChartDataCommand, chart, [
                {"col": "id_customer", "op": "IN", "val": [CUSTOMER_ID]},
                {"col": "nm_measure", "op": "IN", "val": ["unidade"]},
            ])
            if any(response.get("data") for response in responses):
                raise AssertionError(f"{chart.slice_name}: guest RLS leaked data")
            if not all("id_customer = -1" in response.get("query", "") for response in responses):
                raise AssertionError(f"{chart.slice_name}: guest RLS missing from generated SQL")
            rls_checks += 1
        if rls_checks != 8:
            raise AssertionError(f"Expected eight inventory charts, got {rls_checks}")
        print(json.dumps({"tenant": CUSTOMER_ID, "checks": report, "guest_rls_checks": rls_checks},
                         ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
