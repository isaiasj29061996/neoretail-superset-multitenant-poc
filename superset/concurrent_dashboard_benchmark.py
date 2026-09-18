"""Concurrent NeoRetail dashboard benchmark.

This benchmark reuses persisted Superset chart definitions and executes
multiple simulated dashboard openings at the same time. It is focused on
backend/query concurrency: Superset query engine, cache behavior and the
analytics database. Browser rendering is intentionally out of scope.

Environment variables:
- LOAD_TEST_USERS: concurrent simulated users (default: 1)
- LOAD_TEST_DASHBOARD_SLUGS: comma-separated slugs or "all"
- LOAD_TEST_CUSTOMER_ID: tenant id used by queries (default: 142)
- LOAD_TEST_ROW_LIMIT_CAP: maximum chart row limit (default: 20000)
- LOAD_TEST_MAX_WORKERS: concurrent chart workers (default: 40)
- LOAD_TEST_ITERATIONS: dashboard openings per user (default: 1)
- LOAD_TEST_FORCE: bypass Superset result cache when true (default: false)
- LOAD_TEST_OUTPUT: JSON output path
"""
from __future__ import annotations

import json
import os
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from time import perf_counter

from flask import g
from flask_login import login_user
from superset.app import create_app

import profile_dashboard_performance as profile


USERS = max(1, int(os.getenv("LOAD_TEST_USERS", "1")))
CUSTOMER_ID = int(os.getenv("LOAD_TEST_CUSTOMER_ID", "142"))
ROW_LIMIT_CAP = max(1, int(os.getenv("LOAD_TEST_ROW_LIMIT_CAP", "20000")))
MAX_WORKERS = max(1, int(os.getenv("LOAD_TEST_MAX_WORKERS", "40")))
ITERATIONS = max(1, int(os.getenv("LOAD_TEST_ITERATIONS", "1")))
FORCE = os.getenv("LOAD_TEST_FORCE", "false").strip().lower() in {"1", "true", "yes", "on"}
OUTPUT = Path(os.getenv("LOAD_TEST_OUTPUT", f"/generated/load-tests/users-{USERS}.json"))

raw_slugs = os.getenv(
    "LOAD_TEST_DASHBOARD_SLUGS",
    "neoretail-v9-visao-geral-industria",
).strip()
if raw_slugs.casefold() == "all":
    DASHBOARD_SLUGS = profile.DASHBOARDS
else:
    DASHBOARD_SLUGS = tuple(item.strip() for item in raw_slugs.split(",") if item.strip())


def percentile(values, quantile):
    if not values:
        return 0.0
    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * quantile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def summarize(values):
    values = list(values)
    if not values:
        return {"count": 0, "p50": 0.0, "p95": 0.0, "max": 0.0}
    return {
        "count": len(values),
        "p50": round(percentile(values, 0.50), 4),
        "p95": round(percentile(values, 0.95), 4),
        "max": round(max(values), 4),
    }


def load_chart_specs(app):
    profile.CUSTOMER_ID = CUSTOMER_ID
    profile.ROW_LIMIT_CAP = ROW_LIMIT_CAP
    with app.app_context():
        from superset import db
        from superset.models.dashboard import Dashboard

        specs = []
        missing = []
        for slug in DASHBOARD_SLUGS:
            dashboard = db.session.query(Dashboard).filter(Dashboard.slug == slug).one_or_none()
            if dashboard is None:
                missing.append(slug)
                continue
            for chart in sorted(dashboard.slices, key=lambda item: item.id):
                form = json.loads(chart.params)
                default_filters = profile._dashboard_default_filters(
                    dashboard, chart.datasource_id
                )
                queries, configured_limit = profile.build_queries(
                    form,
                    dashboard_default_filters=default_filters,
                )
                specs.append({
                    "dashboard": slug,
                    "chart": chart.slice_name,
                    "chart_id": chart.id,
                    "datasource_id": chart.datasource_id,
                    "form": form,
                    "queries": queries,
                    "configured_row_limit": configured_limit,
                })
        db.session.remove()
        return specs, missing


def execute_chart(app, spec, user_id, iteration, suite_started):
    started = perf_counter()
    details = []
    errors = []

    with app.app_context():
        try:
            with app.test_request_context("/"):
                from superset import db, security_manager
                from superset.commands.chart.data.get_data_command import ChartDataCommand
                from superset.common.query_context_factory import QueryContextFactory

                admin = security_manager.find_user(username="admin") or db.session.query(
                    security_manager.user_model
                ).first()
                if admin is None:
                    raise RuntimeError("Nenhum usuario Superset disponivel para o benchmark.")

                login_user(admin)
                g.user = admin
                context = QueryContextFactory().create(
                    datasource={"id": spec["datasource_id"], "type": "table"},
                    queries=spec["queries"],
                    form_data={**spec["form"], "force": FORCE},
                )
                result = ChartDataCommand(context).run()
                details = profile._query_details(result)
                errors = [item["error"] for item in details if item.get("error")]
        except Exception as exc:
            errors = [f"{type(exc).__name__}: {exc}"]
        finally:
            from superset import db
            db.session.remove()

    finished = perf_counter()
    return {
        "user_id": user_id,
        "iteration": iteration,
        "dashboard": spec["dashboard"],
        "chart": spec["chart"],
        "chart_id": spec["chart_id"],
        "seconds": round(finished - started, 4),
        "started_offset": round(started - suite_started, 4),
        "finished_offset": round(finished - suite_started, 4),
        "rows": sum(item.get("rows", 0) for item in details),
        "query_count": len(spec["queries"]),
        "errors": errors,
    }


def main():
    app = create_app()
    specs, missing = load_chart_specs(app)
    if missing:
        raise SystemExit(f"Dashboards ausentes: {', '.join(missing)}")
    if not specs:
        raise SystemExit("Nenhum grafico encontrado para o benchmark.")

    total_tasks = USERS * ITERATIONS * len(specs)
    worker_count = min(MAX_WORKERS, total_tasks)

    print(json.dumps({
        "event": "load_test_start",
        "users": USERS,
        "iterations": ITERATIONS,
        "dashboards": list(DASHBOARD_SLUGS),
        "charts_per_user": len(specs),
        "tasks": total_tasks,
        "max_workers": worker_count,
        "force_cache_bypass": FORCE,
        "row_limit_cap": ROW_LIMIT_CAP,
    }, ensure_ascii=False), flush=True)

    suite_started = perf_counter()
    results = []
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = []
        for iteration in range(1, ITERATIONS + 1):
            for spec in specs:
                for user_id in range(1, USERS + 1):
                    futures.append(executor.submit(
                        execute_chart,
                        app,
                        spec,
                        user_id,
                        iteration,
                        suite_started,
                    ))
        for future in as_completed(futures):
            item = future.result()
            results.append(item)
            if item["errors"]:
                print(json.dumps({
                    "event": "chart_error",
                    "user": item["user_id"],
                    "dashboard": item["dashboard"],
                    "chart": item["chart"],
                    "errors": item["errors"],
                }, ensure_ascii=False), flush=True)

    wall_seconds = perf_counter() - suite_started
    chart_latencies = [item["seconds"] for item in results]
    error_tasks = [item for item in results if item["errors"]]

    user_completion = defaultdict(float)
    for item in results:
        key = (item["user_id"], item["iteration"])
        user_completion[key] = max(user_completion[key], item["finished_offset"])

    by_chart = defaultdict(list)
    by_chart_errors = defaultdict(int)
    for item in results:
        key = f'{item["dashboard"]} :: {item["chart"]}'
        by_chart[key].append(item["seconds"])
        by_chart_errors[key] += int(bool(item["errors"]))

    chart_summary = {
        key: {**summarize(values), "errors": by_chart_errors[key]}
        for key, values in sorted(by_chart.items())
    }

    payload = {
        "customer_id": CUSTOMER_ID,
        "users": USERS,
        "iterations": ITERATIONS,
        "dashboards": list(DASHBOARD_SLUGS),
        "charts_per_user": len(specs),
        "total_chart_requests": total_tasks,
        "max_workers": worker_count,
        "force_cache_bypass": FORCE,
        "row_limit_cap": ROW_LIMIT_CAP,
        "wall_seconds": round(wall_seconds, 4),
        "throughput_chart_requests_per_second": round(
            total_tasks / wall_seconds if wall_seconds else 0.0, 4
        ),
        "errors": len(error_tasks),
        "error_rate_percent": round(
            100.0 * len(error_tasks) / total_tasks if total_tasks else 0.0, 4
        ),
        "chart_latency_seconds": summarize(chart_latencies),
        "user_page_completion_seconds": summarize(user_completion.values()),
        "per_chart": chart_summary,
        "requests": sorted(
            results,
            key=lambda item: (
                item["user_id"],
                item["iteration"],
                item["dashboard"],
                item["chart_id"],
            ),
        ),
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\\n=== CONCURRENT USER BENCHMARK ===")
    print(f"Users: {USERS}")
    print(f"Dashboards: {', '.join(DASHBOARD_SLUGS)}")
    print(f"Charts/user: {len(specs)}")
    print(f"Total requests: {total_tasks}")
    print(f"Wall time: {wall_seconds:.3f}s")
    print(
        "Chart latency: "
        f'p50={payload["chart_latency_seconds"]["p50"]:.3f}s '
        f'p95={payload["chart_latency_seconds"]["p95"]:.3f}s '
        f'max={payload["chart_latency_seconds"]["max"]:.3f}s'
    )
    print(
        "User page completion: "
        f'p50={payload["user_page_completion_seconds"]["p50"]:.3f}s '
        f'p95={payload["user_page_completion_seconds"]["p95"]:.3f}s '
        f'max={payload["user_page_completion_seconds"]["max"]:.3f}s'
    )
    print(
        f'Errors: {payload["errors"]}/{total_tasks} '
        f'({payload["error_rate_percent"]:.2f}%)'
    )
    print(
        "Throughput: "
        f'{payload["throughput_chart_requests_per_second"]:.2f} chart req/s'
    )
    print(f"JSON: {OUTPUT}")


if __name__ == "__main__":
    main()
