"""Profile NeoRetail dashboard and serving performance end to end.

This utility executes the persisted chart queries through Superset, probes the
native-filter sources and records PostgreSQL mart statistics. It is intentionally
read-only and is meant for the local AMBEV POC.

Environment variables:
- PROFILE_CUSTOMER_ID: tenant used by the benchmark (default: 142)
- PROFILE_DASHBOARD_SLUG: optional single dashboard slug
- PROFILE_CHART_MATCH: optional case-insensitive chart-name fragment
- PROFILE_ROW_LIMIT_CAP: caps chart row_limit during profiling (default: 20000)
- PROFILE_OUTPUT: JSON output path (default: /generated/performance_profile.json)
"""
from __future__ import annotations

import json
import os
import re
from collections import defaultdict
from pathlib import Path
from time import perf_counter

from flask import g
from flask_login import login_user
from sqlalchemy import text
from superset.app import create_app


CUSTOMER_ID = int(os.getenv("PROFILE_CUSTOMER_ID", "142"))
DASHBOARD_SLUG = os.getenv("PROFILE_DASHBOARD_SLUG", "").strip()
CHART_MATCH = os.getenv("PROFILE_CHART_MATCH", "").strip().casefold()
ROW_LIMIT_CAP = max(1, int(os.getenv("PROFILE_ROW_LIMIT_CAP", "20000")))
OUTPUT = Path(os.getenv("PROFILE_OUTPUT", "/generated/performance_profile.json"))

DASHBOARDS = (
    "neoretail-v9-visao-geral-industria",
    "neoretail-v9-visao-geral-quantidade",
    "neoretail-v9-panorama-industria",
    "neoretail-v9-osa-industria",
    "neoretail-v9-tarefas-otimizacao-estoque",
    "neoretail-v9-exportacao-historico-dia",
    "neoretail-v9-exportacao-historico-mes",
)

_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _metric_key(metric):
    if isinstance(metric, str):
        return metric
    if isinstance(metric, dict):
        return metric.get("label") or metric.get("sqlExpression") or json.dumps(metric, sort_keys=True)
    return str(metric)


def _dedupe_metrics(metrics):
    result = []
    seen = set()
    for metric in metrics:
        if not metric:
            continue
        key = _metric_key(metric)
        if key in seen:
            continue
        seen.add(key)
        result.append(metric)
    return result


def _sql_where(form):
    expressions = [
        item.get("sqlExpression")
        for item in form.get("adhoc_filters", [])
        if item.get("expressionType") == "SQL" and item.get("sqlExpression")
    ]
    return " AND ".join(f"({value})" for value in expressions)


def _time_column(axis, grain):
    return {
        "timeGrain": grain,
        "columnType": "BASE_AXIS",
        "sqlExpression": axis,
        "label": axis,
        "expressionType": "SQL",
        "isColumnReference": True,
    }


def _row_limit(form, fallback):
    configured = int(form.get("row_limit") or fallback)
    return min(configured, ROW_LIMIT_CAP), configured


def build_queries(form, dashboard_default_filters=None):
    """Approximate the persisted visual query shape used by the POC."""
    viz = form.get("viz_type")
    metrics = _dedupe_metrics([
        *form.get("metrics", []),
        form.get("metric"),
        form.get("critical_metric"),
        form.get("risk_metric"),
    ])
    filters = [{"col": "id_customer", "op": "IN", "val": [CUSTOMER_ID]}]
    filters.extend(dashboard_default_filters or [])
    where = _sql_where(form)
    extras = {"where": where} if where else {}

    if viz == "neoretail-kpi-card":
        variant = form.get("card_variant", "area")
        groupby = form.get("groupby") or []
        limit, configured = _row_limit(form, 10000)
        common = {
            "metrics": metrics,
            "filters": filters,
            "extras": extras,
            "time_range": form.get("time_range", "No filter"),
            "row_limit": limit,
        }
        if variant in {"rankbars", "verticalbars", "stackedrank"} and groupby:
            query = {
                **common,
                "columns": groupby,
                "orderby": [[metrics[0], False]] if metrics else [],
                "granularity": form.get("x_axis"),
            }
            return [query], configured

        axis = form["x_axis"]
        grain = form.get("time_grain_sqla", "P1M")
        common["extras"] = {**extras, "time_grain_sqla": grain}
        common["orderby"] = [[axis, True]]
        queries = [{**common, "columns": [_time_column(axis, grain)]}]
        if variant == "bars" and groupby:
            queries.append({
                **common,
                "columns": [_time_column(axis, grain), *groupby],
            })
        return queries, configured

    if viz == "table":
        limit, configured = _row_limit(form, 1000)
        return [{
            "columns": form.get("groupby", []),
            "metrics": metrics,
            "filters": filters,
            "extras": extras,
            "time_range": form.get("time_range", "No filter"),
            "row_limit": limit,
        }], configured

    if viz == "pivot_table_v2":
        limit, configured = _row_limit(form, 10000)
        columns = [
            *(form.get("groupbyRows") or []),
            *(form.get("groupbyColumns") or []),
        ]
        return [{
            "columns": columns,
            "metrics": metrics,
            "filters": filters,
            "extras": extras,
            "time_range": form.get("time_range", "No filter"),
            "row_limit": limit,
        }], configured

    limit, configured = _row_limit(form, 10000)
    return [{
        "columns": form.get("groupby", []),
        "metrics": metrics,
        "filters": filters,
        "extras": extras,
        "time_range": form.get("time_range", "No filter"),
        "row_limit": limit,
    }], configured


def _query_details(result):
    details = []
    for query in result.get("queries", []):
        sql = query.get("query") or query.get("sql") or ""
        details.append({
            "rows": len(query.get("data", []) or []),
            "db_duration_ms": query.get("duration"),
            "is_cached": bool(query.get("is_cached", False)),
            "sql": sql[:1500] if isinstance(sql, str) else "",
            "error": query.get("error"),
        })
    return details


def _dashboard_default_filters(dashboard, dataset_id):
    metadata = json.loads(dashboard.json_metadata or "{}")
    result = []
    for native_filter in metadata.get("native_filter_configuration", []):
        targets = native_filter.get("targets", [])
        target_ids = {
            int(target.get("datasetId"))
            for target in targets
            if target.get("datasetId") is not None
        }
        if target_ids and int(dataset_id) not in target_ids:
            continue
        extra = (
            native_filter.get("defaultDataMask", {})
            .get("extraFormData", {})
        )
        for item in extra.get("filters", []) or []:
            if item and item not in result:
                result.append(item)
    return result


def _dataset_columns(dataset):
    return {
        getattr(column, "column_name", None)
        for column in (dataset.columns or [])
        if getattr(column, "column_name", None)
    }


def _probe_filter(connection, dataset, column):
    if dataset.sql:
        return {"status": "skipped_virtual_dataset"}
    if not _SAFE_IDENTIFIER.match(dataset.schema or ""):
        return {"status": "skipped_unsafe_schema"}
    if not _SAFE_IDENTIFIER.match(dataset.table_name or ""):
        return {"status": "skipped_unsafe_table"}
    if not _SAFE_IDENTIFIER.match(column):
        return {"status": "skipped_unsafe_column"}

    columns = _dataset_columns(dataset)
    if column not in columns:
        return {"status": "skipped_missing_column"}

    customer_filter = ""
    params = {}
    if "id_customer" in columns:
        customer_filter = "WHERE id_customer = :customer_id"
        params["customer_id"] = CUSTOMER_ID

    sql = (
        f'SELECT DISTINCT "{column}" '
        f'FROM "{dataset.schema}"."{dataset.table_name}" '
        f'{customer_filter} ORDER BY 1 NULLS LAST LIMIT 1000'
    )
    started = perf_counter()
    rows = connection.execute(text(sql), params).fetchall()
    return {
        "status": "ok",
        "seconds": round(perf_counter() - started, 4),
        "rows": len(rows),
        "sql": sql,
    }


def _mart_stats(connection):
    rows = connection.execute(text("""
        SELECT
            s.relname,
            s.n_live_tup,
            s.seq_scan,
            s.seq_tup_read,
            s.idx_scan,
            pg_total_relation_size(('gold.' || quote_ident(s.relname))::regclass) AS total_bytes,
            pg_relation_size(('gold.' || quote_ident(s.relname))::regclass) AS heap_bytes,
            pg_indexes_size(('gold.' || quote_ident(s.relname))::regclass) AS index_bytes
        FROM pg_stat_user_tables s
        WHERE s.schemaname = 'gold'
          AND s.relname LIKE 'nr_%'
        ORDER BY total_bytes DESC, s.relname
    """)).mappings().all()
    return [dict(row) for row in rows]


def main():
    app = create_app()
    with app.test_request_context("/"):
        from superset import db, security_manager
        from superset.commands.chart.data.get_data_command import ChartDataCommand
        from superset.common.query_context_factory import QueryContextFactory
        from superset.connectors.sqla.models import SqlaTable
        from superset.models.core import Database
        from superset.models.dashboard import Dashboard

        admin = security_manager.find_user(username="admin") or db.session.query(
            security_manager.user_model
        ).first()
        login_user(admin)
        g.user = admin

        database = db.session.query(Database).filter(
            Database.database_name == "NeoRetail Gold - PostgreSQL Local"
        ).one()
        factory = QueryContextFactory()

        selected_slugs = (DASHBOARD_SLUG,) if DASHBOARD_SLUG else DASHBOARDS
        chart_results = []

        for slug in selected_slugs:
            dashboard = db.session.query(Dashboard).filter(Dashboard.slug == slug).one_or_none()
            if dashboard is None:
                chart_results.append({
                    "dashboard": slug,
                    "status": "missing_dashboard",
                    "seconds": 0,
                })
                continue

            for chart in sorted(dashboard.slices, key=lambda item: item.id):
                if CHART_MATCH and CHART_MATCH not in chart.slice_name.casefold():
                    continue
                form = json.loads(chart.params)
                default_filters = _dashboard_default_filters(
                    dashboard, chart.datasource_id
                )
                queries, configured_limit = build_queries(
                    form, dashboard_default_filters=default_filters
                )
                started = perf_counter()
                errors = []
                details = []
                try:
                    context = factory.create(
                        datasource={"id": chart.datasource_id, "type": "table"},
                        queries=queries,
                        form_data={**form, "force": True},
                    )
                    result = ChartDataCommand(context).run()
                    details = _query_details(result)
                    errors = [item["error"] for item in details if item.get("error")]
                except Exception as exc:
                    errors = [f"{type(exc).__name__}: {exc}"]
                seconds = round(perf_counter() - started, 4)
                row_count = sum(item.get("rows", 0) for item in details)
                payload = {
                    "dashboard": slug,
                    "chart": chart.slice_name,
                    "chart_id": chart.id,
                    "dataset_id": chart.datasource_id,
                    "viz_type": form.get("viz_type"),
                    "variant": form.get("card_variant"),
                    "configured_row_limit": configured_limit,
                    "profile_row_limit": min(configured_limit, ROW_LIMIT_CAP),
                    "query_count": len(queries),
                    "seconds": seconds,
                    "rows": row_count,
                    "errors": errors,
                    "queries": details,
                }
                chart_results.append(payload)
                print(json.dumps({
                    "dashboard": slug,
                    "chart": chart.slice_name,
                    "seconds": seconds,
                    "rows": row_count,
                    "queries": len(queries),
                    "errors": errors,
                }, ensure_ascii=False), flush=True)

        filter_results = []
        datasets = {
            item.id: item
            for item in db.session.query(SqlaTable).all()
        }
        seen_filters = set()

        with database.get_sqla_engine() as engine:
            with engine.connect() as connection:
                for slug in selected_slugs:
                    dashboard = db.session.query(Dashboard).filter(Dashboard.slug == slug).one_or_none()
                    if dashboard is None:
                        continue
                    metadata = json.loads(dashboard.json_metadata or "{}")
                    for native_filter in metadata.get("native_filter_configuration", []):
                        name = native_filter.get("name")
                        for target in native_filter.get("targets", []):
                            dataset_id = target.get("datasetId")
                            column = (target.get("column") or {}).get("name")
                            key = (dataset_id, column)
                            if not dataset_id or not column or key in seen_filters:
                                continue
                            seen_filters.add(key)
                            dataset = datasets.get(int(dataset_id))
                            if dataset is None:
                                probe = {"status": "missing_dataset"}
                            else:
                                try:
                                    probe = _probe_filter(connection, dataset, column)
                                except Exception as exc:
                                    probe = {
                                        "status": "error",
                                        "error": f"{type(exc).__name__}: {exc}",
                                    }
                            filter_results.append({
                                "dashboard": slug,
                                "filter": name,
                                "dataset_id": dataset_id,
                                "dataset": dataset.table_name if dataset else None,
                                "column": column,
                                **probe,
                            })

                marts = _mart_stats(connection)

        slowest = sorted(
            [item for item in chart_results if item.get("chart")],
            key=lambda item: item.get("seconds", 0),
            reverse=True,
        )
        slow_filters = sorted(
            [item for item in filter_results if item.get("status") == "ok"],
            key=lambda item: item.get("seconds", 0),
            reverse=True,
        )

        by_dashboard = defaultdict(lambda: {"charts": 0, "seconds": 0.0, "errors": 0})
        for item in chart_results:
            if not item.get("chart"):
                continue
            summary = by_dashboard[item["dashboard"]]
            summary["charts"] += 1
            summary["seconds"] += item["seconds"]
            summary["errors"] += len(item["errors"])
        dashboard_summary = {
            key: {
                **value,
                "seconds": round(value["seconds"], 4),
            }
            for key, value in by_dashboard.items()
        }

        payload = {
            "customer_id": CUSTOMER_ID,
            "row_limit_cap": ROW_LIMIT_CAP,
            "dashboard_filter": DASHBOARD_SLUG or None,
            "chart_match": CHART_MATCH or None,
            "dashboard_summary": dashboard_summary,
            "slowest_charts": slowest[:20],
            "slowest_filter_probes": slow_filters[:20],
            "marts": marts,
            "charts": chart_results,
            "filters": filter_results,
        }
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        print("\n=== SLOWEST CHARTS ===")
        for item in slowest[:15]:
            print(f'{item["seconds"]:>8.3f}s  {item["dashboard"]}  {item["chart"]}')
        print("\n=== SLOWEST FILTER PROBES ===")
        for item in slow_filters[:15]:
            print(f'{item["seconds"]:>8.3f}s  {item["dataset"]}.{item["column"]}')
        print("\n=== LARGEST MARTS ===")
        for item in marts[:15]:
            size_mib = (item["total_bytes"] or 0) / 1024 / 1024
            print(
                f'{size_mib:>10.1f} MiB  {item["relname"]}  '
                f'rows~{item["n_live_tup"]} seq={item["seq_scan"]} idx={item["idx_scan"]}'
            )
        print(f"\nJSON: {OUTPUT}")


if __name__ == "__main__":
    main()
