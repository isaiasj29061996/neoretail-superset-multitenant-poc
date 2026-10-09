"""Validate compact defaults and detailed fallbacks for interactive marts."""
from __future__ import annotations

import os

import json

from flask import g
from flask_login import login_user
from superset.app import create_app

from profile_dashboard_performance import build_queries


CUSTOMER_ID = int(os.getenv("NEORETAIL_VALIDATION_CUSTOMER", "142"))
TEST_FILTER = {"col": "rede", "op": "IN", "val": ["AKKIATACADO"]}
EXPORT_DETAIL_FILTER = {"col": "bandeira", "op": "IN", "val": ["DELTAMAX"]}
CASES = (
    (
        "neoretail-v9-panorama-industria",
        "[Panorama] Evolutivo de vendas — Valor semanal",
        "nr_panorama_weekly_summary",
        "nr_panorama_weekly",
    ),
    (
        "neoretail-v9-visao-geral-quantidade",
        "[Visão quantidade] Distribuição e sortimento",
        "nr_overview_distinct_summary",
        "nr_overview_history",
    ),
    (
        "neoretail-v9-osa-industria",
        "[OSA Indústria] Visão geral mensal — Perdas",
        "nr_osa_causes_summary",
        "nr_osa_industry_causes",
    ),
)


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
    response = result.get("queries", [])[0]
    if response.get("error"):
        raise AssertionError(response["error"])
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
        factory = QueryContextFactory()

        for slug, chart_name, summary_table, detail_table in CASES:
            dashboard = db.session.query(Dashboard).filter(Dashboard.slug == slug).one()
            chart = next(item for item in dashboard.slices if item.slice_name == chart_name)

            compact = execute(factory, ChartDataCommand, chart, [])
            compact_sql = compact.get("query") or compact.get("sql") or ""
            if summary_table not in compact_sql:
                raise AssertionError(f"{chart_name} não usou {summary_table}")

            filtered = execute(factory, ChartDataCommand, chart, [TEST_FILTER])
            filtered_sql = filtered.get("query") or filtered.get("sql") or ""
            if detail_table not in filtered_sql or summary_table in filtered_sql:
                raise AssertionError(f"{chart_name} não usou {detail_table} com filtro")
            if not (filtered.get("data") or []):
                raise AssertionError(f"{chart_name} não retornou dados filtrados")

            print(json.dumps({
                "chart": chart_name,
                "compact_rows": len(compact.get("data", []) or []),
                "filtered_rows": len(filtered.get("data", []) or []),
                "compact_source": summary_table,
                "filtered_source": detail_table,
            }, ensure_ascii=False))

        export_cases = (
            (
                "neoretail-v9-exportacao-historico-dia",
                "[Exportação dia] Varejo",
                "nr_export_daily_retail_summary",
                "nr_export_daily",
            ),
            (
                "neoretail-v9-exportacao-historico-mes",
                "[Exportação mês] Varejo",
                "nr_export_monthly_retail_summary",
                "nr_export_monthly",
            ),
        )
        for slug, chart_name, summary_table, detail_table in export_cases:
            dashboard = db.session.query(Dashboard).filter(Dashboard.slug == slug).one()
            chart = next(item for item in dashboard.slices if item.slice_name == chart_name)

            compact = execute(factory, ChartDataCommand, chart, [])
            compact_sql = compact.get("query") or compact.get("sql") or ""
            if summary_table not in compact_sql:
                raise AssertionError(f"{chart_name} não usou {summary_table}")

            supported = execute(factory, ChartDataCommand, chart, [TEST_FILTER])
            supported_sql = supported.get("query") or supported.get("sql") or ""
            if summary_table not in supported_sql:
                raise AssertionError(f"{chart_name} abandonou o resumo para filtro de rede")

            detailed = execute(factory, ChartDataCommand, chart, [EXPORT_DETAIL_FILTER])
            detailed_sql = detailed.get("query") or detailed.get("sql") or ""
            if detail_table not in detailed_sql or summary_table in detailed_sql:
                raise AssertionError(f"{chart_name} não usou {detail_table} com bandeira")
            if not (detailed.get("data") or []):
                raise AssertionError(f"{chart_name} não retornou dados por bandeira")

            print(json.dumps({
                "chart": chart_name,
                "compact_rows": len(compact.get("data", []) or []),
                "retail_filtered_rows": len(supported.get("data", []) or []),
                "detail_filtered_rows": len(detailed.get("data", []) or []),
                "compact_source": summary_table,
                "filtered_source": detail_table,
            }, ensure_ascii=False))


if __name__ == "__main__":
    main()
