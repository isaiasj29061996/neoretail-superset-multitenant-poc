"""Build the isolated Power BI-aligned OSA Industry dashboard.

This dashboard intentionally lives beside the legacy OSA dashboard while the
new semantics are certified.  It does not mutate the legacy dashboard.

Power BI contracts reproduced here:
* monthly value: sellout, exact VL_PERDA_OSA, % loss, % OSA;
* monthly quantity: converted volume/loss, % loss, % OSA;
* weekly value/quantity counterparts;
* MTD/M-1/U3M/current-year loss-by-motive/cause views;
* three hierarchical matrices (region, retail, item hierarchy);
* tenant RLS through id_customer on every virtual dataset.
"""
from __future__ import annotations

import json

from superset.app import create_app

from neoretail_bootstrap.overview.filters import overview_native_filters
from neoretail_bootstrap.panorama.filters import WEEKLY_FILTER_COLUMNS
from neoretail_bootstrap.osa_certified.matrices import (
    MATRIX_SCOPES,
    TABLE_OSA as MATRIX_OSA,
    TABLE_PROBLEMS as MATRIX_PROBLEMS,
    TABLE_QTY as MATRIX_QTY,
    TABLE_VALUE as MATRIX_VALUE,
    matrix_period_sql,
)


from neoretail_bootstrap.core.chart_params import comparison_pivot_params, custom_params
from neoretail_bootstrap.core.filters import _jinja_filter_predicates
from neoretail_bootstrap.core.layout import Layout
from neoretail_bootstrap.core.metadata import upsert_dataset, upsert_chart
from neoretail_bootstrap.core.metrics import metric, formatted_metric


DASHBOARD_TITLE = "NeoRetail V9 — OSA Indústria — Certificada"
DASHBOARD_SLUG = "neoretail-v9-osa-industria-certified"
PREFIX = "[OSA Certificada]"

from neoretail_bootstrap.osa_certified.semantics import (
    PERIODS, monthly_overview_sql, weekly_overview_sql, cause_period_sql, period_options_sql, TOP_VALUE_METRICS, TOP_QTY_METRICS, CAUSE_VALUE, CAUSE_QTY
)
from neoretail_bootstrap.osa_certified.filters import (
    DIMENSION_OVERRIDES, _dimension_nulls, _measure_filter, _period_filter, native_filters
)
from neoretail_bootstrap.osa_certified.presentation import (
    _top_params, _cause_params, _matrix_params, chart_specs, position_json, CSS
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

        monthly = upsert_dataset(
            db.session,SqlaTable,database,"nr_osa_monthly_certified",
            sql=monthly_overview_sql(),
        )
        weekly = upsert_dataset(
            db.session,SqlaTable,database,"nr_osa_weekly_certified",
            sql=weekly_overview_sql(),
        )
        causes = upsert_dataset(
            db.session,SqlaTable,database,"nr_osa_causes_certified",
            sql=cause_period_sql(),
        )
        matrix_datasets = {
            key: upsert_dataset(
                db.session,SqlaTable,database,f"nr_osa_matrix_{key}_certified",
                sql=matrix_period_sql(group_column),
            )
            for key,(_,group_column) in MATRIX_SCOPES.items()
        }
        period_options = upsert_dataset(
            db.session,SqlaTable,database,"nr_osa_period_options",
            sql=period_options_sql(),
        )
        filter_options = upsert_dataset(
            db.session,SqlaTable,database,"nr_filter_options",
            table_name="nr_filter_options",
        )

        charts = {}
        for key, dataset, title, params, viz in chart_specs(monthly, weekly, causes, matrix_datasets):
            charts[key] = upsert_chart(db.session, Slice, dataset, f"{PREFIX} {title}", params, viz)

        dashboard = db.session.query(Dashboard).filter(
            Dashboard.slug == DASHBOARD_SLUG
        ).one_or_none()
        if dashboard is None:
            dashboard = Dashboard(
                dashboard_title=DASHBOARD_TITLE,
                slug=DASHBOARD_SLUG,
                published=True,
            )
            db.session.add(dashboard)
        dashboard.dashboard_title = DASHBOARD_TITLE
        dashboard.published = True
        dashboard.position_json = json.dumps(position_json(charts),ensure_ascii=False)
        dashboard.css = CSS

        # Common slicers mirror the PBI location/activity/brand/category/item/
        # measure selectors. The period control applies only to cause/matrix
        # charts because the top timeline needs its full temporal window.
        native = native_filters(monthly, weekly, causes, matrix_datasets, filter_options, period_options, charts)

        dashboard.json_metadata = json.dumps({
            "timed_refresh_immune_slices": [],
            "expanded_slices": {},
            "refresh_frequency": 0,
            "color_scheme": "supersetColors",
            "native_filter_configuration": native,
            "filter_bar_orientation": "HORIZONTAL",
        },ensure_ascii=False)
        dashboard.slices = list(charts.values())
        db.session.commit()

        print(json.dumps({
            "dashboard_id": dashboard.id,
            "slug": dashboard.slug,
            "industry": {"id_customer":142,"label":"AMBEV"},
            "datasets": {
                "monthly":monthly.id,
                "weekly":weekly.id,
                "causes":causes.id,
                "matrices":{key:dataset.id for key,dataset in matrix_datasets.items()},
                "period_options":period_options.id,
            },
            "charts": {key:chart.id for key,chart in charts.items()},
        },ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
