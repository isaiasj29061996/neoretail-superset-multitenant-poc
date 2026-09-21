"""Validate fast and filtered TVD/IVD headline paths through Superset."""
from __future__ import annotations

import json

from flask import g
from flask_login import login_user
from sqlalchemy import text
from superset.app import create_app

from profile_dashboard_performance import build_queries


CUSTOMER_ID = 142
CASES = (
    {
        "chart": "TVD - Pré-ruptura",
        "summary": "nr_tvd_daily_summary",
        "detail": "nr_tvd_daily",
        "value": "tvd",
        "risk_code": "F",
        "critical_metric": "Itens críticos TVD",
        "risk_metric": "Itens risco TVD",
        "critical_column": "itens_criticos_tvd",
        "risk_column": "itens_risco_tvd",
    },
    {
        "chart": "IVD - Excesso",
        "summary": "nr_ivd_daily_summary",
        "detail": "nr_ivd_daily",
        "value": "ivd",
        "risk_code": "U",
        "critical_metric": "Itens críticos IVD",
        "risk_metric": "Itens risco IVD",
        "critical_column": "itens_criticos_ivd",
        "risk_column": "itens_risco_ivd",
    },
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


def independent_counts(connection, case):
    # This is intentionally independent of the serving marts. It reproduces
    # COUNT(ID_ITEM), the two location exclusions and the literal DAX codes
    # directly over CALCULO_OPORTUNIDADES.
    sql = text(f"""
        SELECT
            MAX(f.latest_date) AS assigned_date,
            COUNT(c.id_item) FILTER (
                WHERE c.regra_critico = 'CRITICO'
                  AND COALESCE(c.{case['value']}, 0) > 0
            )::bigint AS critical_count,
            COUNT(c.id_item) FILTER (
                WHERE c.regra_critico = :risk_code
                  AND COALESCE(c.{case['value']}, 0) > 0
            )::bigint AS risk_count
        FROM gold.calculo_oportunidades c
        CROSS JOIN (
            SELECT MAX(id_time)::date AS latest_date
            FROM gold.fato_ivd_tvd
            WHERE id_customer = :customer_id
        ) f
        LEFT JOIN gold.dim_local l
          ON l.id_customer = c.id_customer
         AND l.id_location = c.id_location
        LEFT JOIN gold.dim_catalogo_local catalogo
          ON catalogo.id_customer = c.id_customer
         AND catalogo.id_location = c.id_location
        WHERE c.id_customer = :customer_id
          AND UPPER(TRIM(COALESCE(l.tipo_local, ''))) NOT IN (
              U&'DEP\\00D3SITO', 'DEPOSITO', 'CD', 'LOJA VIRTUAL'
          )
          AND UPPER(TRIM(COALESCE(catalogo.tipo_local, ''))) NOT IN (
              U&'DEP\\00D3SITO', 'DEPOSITO', 'CD', 'LOJA VIRTUAL'
          )
    """)
    return connection.execute(sql, {
        "customer_id": CUSTOMER_ID,
        "risk_code": case["risk_code"],
    }).mappings().one()


def mart_counts(connection, case):
    sql = text(f"""
        SELECT
            MAX(data) AS assigned_date,
            COALESCE(SUM({case['critical_column']}) FILTER (
                WHERE data = (SELECT MAX(data) FROM gold.{case['summary']}
                              WHERE id_customer = :customer_id)
            ), 0)::bigint AS critical_count,
            COALESCE(SUM({case['risk_column']}) FILTER (
                WHERE data = (SELECT MAX(data) FROM gold.{case['summary']}
                              WHERE id_customer = :customer_id)
            ), 0)::bigint AS risk_count
        FROM gold.{case['summary']}
        WHERE id_customer = :customer_id
    """)
    return connection.execute(sql, {"customer_id": CUSTOMER_ID}).mappings().one()


def latest_chart_counts(response, case):
    rows = response.get("data") or []
    if not rows:
        raise AssertionError(f"{case['chart']} não retornou linhas")
    latest = max(rows, key=lambda row: str(row.get("data") or ""))
    return {
        "assigned_date": str(latest["data"])[:10],
        "critical_count": int(latest[case["critical_metric"]]),
        "risk_count": int(latest[case["risk_metric"]]),
    }


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

        database = next(iter(charts.values())).table.database
        with database.get_sqla_engine() as engine, engine.connect() as connection:
            source_audit = connection.execute(text("""
                SELECT
                    COUNT(*)::bigint AS source_rows,
                    COUNT(*) FILTER (WHERE regra_critico = 'CRITICO')::bigint
                        AS literal_critical_rows,
                    STRING_AGG(DISTINCT COALESCE(regra_critico, '<NULL>'), ','
                               ORDER BY COALESCE(regra_critico, '<NULL>')) AS rule_domain,
                    MIN(_silver_refreshed_at) AS min_refresh,
                    MAX(_silver_refreshed_at) AS max_refresh
                FROM gold.calculo_oportunidades
                WHERE id_customer = :customer_id
            """), {"customer_id": CUSTOMER_ID}).mappings().one()
            print(json.dumps({
                "source_audit": {
                    key: str(value) if "refresh" in key else value
                    for key, value in source_audit.items()
                },
                "note": "source_rows is inventory, not a critical-item count",
            }, ensure_ascii=False))

            for case in CASES:
                chart_name = case["chart"]
                summary_table = case["summary"]
                detail_table = case["detail"]
                chart = charts[chart_name]
                tenant_filter = [{
                    "col": "id_customer", "op": "IN", "val": [CUSTOMER_ID],
                }]
                fast = run_chart(factory, ChartDataCommand, chart, tenant_filter)
                fast_sql = fast.get("query") or fast.get("sql") or ""
                if summary_table not in fast_sql or detail_table + " " in fast_sql:
                    raise AssertionError(
                        f"{chart_name} não usou o caminho compacto sem filtros"
                    )

                filtered = run_chart(factory, ChartDataCommand, chart, [
                    *tenant_filter,
                    {"col": "rede", "op": "IN", "val": ["AKKIATACADO"]},
                ])
                filtered_sql = filtered.get("query") or filtered.get("sql") or ""
                if detail_table not in filtered_sql or summary_table in filtered_sql:
                    raise AssertionError(
                        f"{chart_name} não usou o detalhe com filtro: {filtered_sql}"
                    )
                if not (filtered.get("data") or []):
                    raise AssertionError(
                        f"{chart_name} não retornou dados para a rede de teste"
                    )

                independent = independent_counts(connection, case)
                mart = mart_counts(connection, case)
                superset = latest_chart_counts(fast, case)
                paths = {
                    "independent": {
                        "assigned_date": str(independent["assigned_date"]),
                        "critical_count": int(independent["critical_count"]),
                        "risk_count": int(independent["risk_count"]),
                    },
                    "mart": {
                        "assigned_date": str(mart["assigned_date"]),
                        "critical_count": int(mart["critical_count"]),
                        "risk_count": int(mart["risk_count"]),
                    },
                    "superset": superset,
                }
                if len({json.dumps(value, sort_keys=True) for value in paths.values()}) != 1:
                    raise AssertionError(f"Reconciliação divergente em {chart_name}: {paths}")

                print(json.dumps({
                    "chart": chart_name,
                    "fast_rows": len(fast.get("data", []) or []),
                    "filtered_rows": len(filtered.get("data", []) or []),
                    "fast_source": summary_table,
                    "filtered_source": detail_table,
                    "reconciliation": paths,
                }, ensure_ascii=False))


if __name__ == "__main__":
    main()
