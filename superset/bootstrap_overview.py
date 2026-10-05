"""Create/update the NeoRetail overview datasets, charts and dashboard.

Only Superset metadata is changed. Charts use physical serving marts created by
``create-superset-kpi-views.ps1``.
"""

from __future__ import annotations

import json
import uuid

from sqlalchemy import text
from superset.app import create_app

from neoretail_bootstrap.core.chart_params import chart_params
from neoretail_bootstrap.core.filters import _jinja_filter_predicates
from neoretail_bootstrap.core.metadata import upsert_dataset, upsert_overview_chart as upsert_chart
from neoretail_bootstrap.core.metrics import metric

DASHBOARD_TITLE = "NeoRetail V9 — Visão geral da indústria"

# Compatibility reexports preserve the original public and private symbols.

from neoretail_bootstrap.overview.semantics import (
    HISTORY_SQL,
    M,
    OVERVIEW_M,
    ROI_COMPONENTS,
    MARKUP_COMPONENTS,
    TVD_DAILY,
    IVD_DAILY,
    headline_semantic_sql,
    overview_semantic_sql,
    osa_semantic_sql,
)

from neoretail_bootstrap.overview.filters import (
    HEADLINE_FILTER_COLUMNS,
    sql_filter,
    _filter_definitions,
    _native_filters_for_targets,
    native_filters,
    overview_native_filters,
)

from neoretail_bootstrap.overview.presentation import (
    position_json,
    chart_specs,
)

def main():
    app = create_app()
    with app.app_context():
        from superset import db
        from superset.connectors.sqla.models import SqlaTable
        from superset.models.core import Database
        from superset.models.dashboard import Dashboard
        from superset.models.slice import Slice

        database = db.session.query(Database).filter(
            Database.database_name == "NeoRetail Gold - PostgreSQL Local"
        ).one()
        tvd_daily = upsert_dataset(
            db.session, SqlaTable, database, "nr_tvd_daily_interactive",
            sql=headline_semantic_sql("nr_tvd_daily", "nr_tvd_daily_summary"),
        )
        ivd_daily = upsert_dataset(
            db.session, SqlaTable, database, "nr_ivd_daily_interactive",
            sql=headline_semantic_sql("nr_ivd_daily", "nr_ivd_daily_summary"),
        )
        summary = upsert_dataset(
            db.session, SqlaTable, database, "nr_overview_interactive",
            sql=overview_semantic_sql(),
        )
        osa_summary = upsert_dataset(
            db.session, SqlaTable, database, "nr_osa_interactive",
            sql=osa_semantic_sql(),
        )
        filter_options = upsert_dataset(
            db.session, SqlaTable, database, "nr_filter_options", table_name="nr_filter_options"
        )
        conversion_options = upsert_dataset(
            db.session, SqlaTable, database, "nr_conversion_options",
            table_name="nr_conversion_options",
        )
        with database.get_sqla_engine() as engine:
            with engine.connect() as connection:
                tvd_max_date = connection.execute(
                    text("SELECT MAX(data) FROM gold.nr_tvd_daily")
                ).scalar_one()
                ivd_max_date = connection.execute(
                    text("SELECT MAX(data) FROM gold.nr_ivd_daily")
                ).scalar_one()

        specs = chart_specs(tvd_daily, ivd_daily, summary, osa_summary, tvd_max_date, ivd_max_date)
        charts = [upsert_chart(db.session, Slice, dataset, title, params) for dataset, title, params in specs]

        dashboard = db.session.query(Dashboard).filter(
            Dashboard.dashboard_title == DASHBOARD_TITLE
        ).one_or_none()
        if dashboard is None:
            dashboard = Dashboard(
                dashboard_title=DASHBOARD_TITLE,
                slug="neoretail-v9-visao-geral-industria",
                published=True,
            )
            db.session.add(dashboard)
        dashboard.published = True
        dashboard.position_json = position_json(charts)
        dashboard.css = (
            ".dashboard-content { background: #e7f0f5 !important; } "
            ".dashboard-component-chart-holder { border-radius: 8px; } "
            ".dashboard-component-chart-holder > .header { display: none !important; }"
        )
        dashboard.json_metadata = json.dumps({
            "timed_refresh_immune_slices": [],
            "expanded_slices": {},
            "refresh_frequency": 0,
            "color_scheme": "supersetColors",
            "native_filter_configuration": overview_native_filters(
                [summary.id, osa_summary.id, tvd_daily.id, ivd_daily.id],
                {
                    "nm_measure": conversion_options.id,
                    **{
                        column: filter_options.id
                        for column, _, _ in _filter_definitions()
                        if column != "nm_measure"
                    },
                },
            ),
            "filter_bar_orientation": "HORIZONTAL",
        })
        dashboard.slices = charts
        db.session.commit()
        print(json.dumps({
            "dashboard_id": dashboard.id,
            "slug": dashboard.slug,
            "datasets": {"summary": summary.id, "osa": osa_summary.id, "tvd_daily": tvd_daily.id, "ivd_daily": ivd_daily.id},
            "charts": {chart.slice_name: chart.id for chart in charts},
        }, ensure_ascii=False))

if __name__ == "__main__":
    main()
