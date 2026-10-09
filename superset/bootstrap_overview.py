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

from neoretail_bootstrap.pbip_overview.semantics import (overview_semantic_sql as pbip_overview_semantic_sql, osa_semantic_sql as pbip_osa_semantic_sql, sellout_u3m_semantic_sql as pbip_sellout_u3m_semantic_sql)
from neoretail_bootstrap.pbip_overview.presentation import chart_specs as pbip_chart_specs
from neoretail_bootstrap.pbip_overview.headlines import (headline_semantic_sql as pbip_headline_semantic_sql, giro_semantic_sql as pbip_giro_semantic_sql)
from neoretail_bootstrap.pbip_overview.filter_context import selector_options_sql as pbip_selector_options_sql
from neoretail_bootstrap.pbip_overview.metadata import upsert_serving_dataset
from neoretail_bootstrap.pbip_overview.selectors import (COLUMNS as PBIP_SELECTOR_COLUMNS, option_sql as pbip_option_sql, native_filters as pbip_native_filters)

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
        from superset.connectors.sqla.models import SqlaTable, TableColumn
        from superset.models.core import Database
        from superset.models.dashboard import Dashboard
        from superset.models.slice import Slice

        database = db.session.query(Database).filter(
            Database.database_name == "NeoRetail Gold - PostgreSQL Local"
        ).one()
        tvd_daily = upsert_serving_dataset(
            db.session, SqlaTable, database, "nr_tvd_daily_interactive",
            sql=pbip_headline_semantic_sql("tvd"),
            probe_source='nr_pbip_daily_headlines',
        )
        ivd_daily = upsert_serving_dataset(
            db.session, SqlaTable, database, "nr_ivd_daily_interactive",
            sql=pbip_headline_semantic_sql("ivd"),
            probe_source='nr_pbip_daily_headlines',
        )
        summary = upsert_serving_dataset(
            db.session, SqlaTable, database, "nr_overview_interactive",
            sql=pbip_overview_semantic_sql(),
            probe_source='nr_pbip_overview_semantic_v3',
        )
        c05_summary = upsert_serving_dataset(
            db.session, SqlaTable, database, 'nr_pbip_sellout_u3m_interactive',
            sql=pbip_sellout_u3m_semantic_sql(), probe_source='nr_pbip_overview_semantic_v3',
        )
        if not any(c.column_name == 'row_scope' for c in c05_summary.columns):
            c05_summary.columns.append(TableColumn(column_name='row_scope', type='TEXT', groupby=True, filterable=True))
        osa_summary = upsert_serving_dataset(
            db.session, SqlaTable, database, "nr_osa_interactive",
            sql=pbip_osa_semantic_sql(),
            probe_source='nr_pbip_osa_semantic_v3',
        )
        giro_summary = upsert_serving_dataset(
            db.session, SqlaTable, database, "nr_pbip_giro_interactive",
            sql=pbip_giro_semantic_sql(),
            probe_source='nr_pbip_giro_v3',
        )
        filter_options = upsert_dataset(
            db.session, SqlaTable, database, "nr_pbip_filter_options", sql=pbip_selector_options_sql()
        )
        conversion_options = upsert_dataset(
            db.session, SqlaTable, database, "nr_pbip_conversion_options",
            sql="SELECT id_customer,nm_measure FROM gold.dim_conversao WHERE id_customer=290 AND nm_measure <> 'valor' GROUP BY id_customer,nm_measure",
        )
        selector_datasets = {
            column: upsert_dataset(
                db.session, SqlaTable, database, 'nr_pbip_options_' + column,
                sql=pbip_option_sql(column),
            )
            for column in PBIP_SELECTOR_COLUMNS
        }
        with database.get_sqla_engine() as engine:
            with engine.connect() as connection:
                tvd_max_date = connection.execute(
                    text("SELECT MAX(data) FROM gold.nr_tvd_daily")
                ).scalar_one()
                ivd_max_date = connection.execute(
                    text("SELECT MAX(data) FROM gold.nr_ivd_daily")
                ).scalar_one()

        with database.get_sqla_engine() as engine:
            with engine.connect() as connection:
                calendar = connection.execute(text(
                    "SELECT MIN(data),MAX(data),MAX(data_at) FROM gold.nr_pbip_calendar WHERE id_customer=290"
                )).one()
                activity_rows = connection.execute(text(
                    'SELECT tp_activity_level,nm_activity_level FROM gold.dim_nivel_atividade '
                    'WHERE id_customer=290 AND nm_activity_level IS NOT NULL'
                )).all()
                activity_labels = {str(row[0]): row[1] for row in activity_rows}
                if len(activity_labels) != len(set((str(row[0]), row[1]) for row in activity_rows)):
                    raise ValueError('PBIP activity codes do not have unique display labels')
        specs = pbip_chart_specs(tvd_daily, ivd_daily, summary, osa_summary, tvd_max_date, ivd_max_date)
        specs = [(giro_summary if title == 'Giro' else c05_summary if title in ('Vendas','ROI','MARKUP') else dataset, title, params) for dataset, title, params in specs]
        for dataset, _, params in specs:
            params['datasource'] = f'{dataset.id}__table'
            params['semantic_anchor_date'] = calendar[2].isoformat()
            params['adhoc_filters'].append(sql_filter(
                f"data BETWEEN DATE '{calendar[0].isoformat()}' AND DATE '{calendar[1].isoformat()}'",
                'pbip_calendar_domain',
            ))
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
            "native_filter_configuration": pbip_native_filters({
                column: dataset.id for column, dataset in selector_datasets.items()
            }, activity_labels),
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
