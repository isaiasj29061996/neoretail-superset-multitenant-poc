"""Validate fast and filtered TVD/IVD headline paths through Superset."""
from __future__ import annotations

import json

from flask import g
from flask_login import login_user
from superset.app import create_app

from profile_dashboard_performance import build_queries


CUSTOMER_ID = 142
CASES = (
    ("TVD - Pré-ruptura", "nr_tvd_daily_summary", "nr_tvd_daily"),
    ("IVD - Excesso", "nr_ivd_daily_summary", "nr_ivd_daily"),
)


def run_chart(factory, command, chart, extra_filters):
    form = json.loads(chart.params)
    queries, _ = build_queries(form)
    for query in queries:
        query["filters"] = [*query.get("filters", []), *extra_filters]
    g.form_data = {"extra_filters": extra_filters}
    context = factory.create(
        datasource={"id": chart.datasource_id, "type": "table"},
        queries=queries,
        form_data={**form, "force": True, "extra_filters": extra_filters},
    )
    result = command(context).run()
    g.form_data = {}
    response = result.get("queries", [])[0]
    error = response.get("error")
    if error:
        raise AssertionError(error)
    return response


def main() -> None:
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

        dashboard = db.session.query(Dashboard).filter(
            Dashboard.slug == "neoretail-v9-visao-geral-industria"
        ).one()
        charts = {chart.slice_name: chart for chart in dashboard.slices}
        factory = QueryContextFactory()

        for chart_name, summary_table, detail_table in CASES:
            chart = charts[chart_name]
            fast = run_chart(factory, ChartDataCommand, chart, [])
            fast_sql = fast.get("query") or fast.get("sql") or ""
            if summary_table not in fast_sql or detail_table + " " in fast_sql:
                raise AssertionError(f"{chart_name} não usou o caminho compacto sem filtros")

            filtered = run_chart(factory, ChartDataCommand, chart, [{
                "col": "rede", "op": "IN", "val": ["AKKIATACADO"],
            }])
            filtered_sql = filtered.get("query") or filtered.get("sql") or ""
            if detail_table not in filtered_sql or summary_table in filtered_sql:
                raise AssertionError(
                    f"{chart_name} não usou o detalhe com filtro: {filtered_sql}"
                )
            if not (filtered.get("data") or []):
                raise AssertionError(f"{chart_name} não retornou dados para a rede de teste")

            print(json.dumps({
                "chart": chart_name,
                "fast_rows": len(fast.get("data", []) or []),
                "filtered_rows": len(filtered.get("data", []) or []),
                "fast_source": summary_table,
                "filtered_source": detail_table,
            }, ensure_ascii=False))


if __name__ == "__main__":
    main()
