"""Create the NeoRetail Panorama Industria dashboard in Superset metadata.

The script creates physical-dataset metadata, charts and dashboard layout. The
serving marts are materialized before this script runs.
"""
from __future__ import annotations

import json
import uuid

from sqlalchemy import text
from superset.app import create_app

from neoretail_bootstrap.overview.semantics import HISTORY_SQL, M
from neoretail_bootstrap.overview.filters import overview_native_filters
from bootstrap_overview_quantity import Q, quantity_semantic_sql


from neoretail_bootstrap.core.chart_params import custom_params, table_params, comparison_pivot_params
from neoretail_bootstrap.core.filters import _jinja_filter_predicates
from neoretail_bootstrap.core.layout import Layout
from neoretail_bootstrap.core.metadata import upsert_dataset, upsert_chart
from neoretail_bootstrap.core.metrics import metric, formatted_metric


# Compatibility reexports: implementations live in their owning Panorama module.
from neoretail_bootstrap.panorama.sources import (
    WEEKLY_SQL,
    OPPORTUNITIES_SQL,
    OPPORTUNITIES_LATEST_SQL,
    _WEEKLY_SELLOUT,
    WEEKLY_P,
    weekly_semantic_sql,
)
from neoretail_bootstrap.panorama.sales import (
    weekly_sales_semantic_sql,
    monthly_sales_semantic_sql,
    weekly_sales_card_semantic_sql,
    register_sales_charts,
)
from neoretail_bootstrap.panorama.inventory import (
    monthly_inventory_semantic_sql,
    weekly_inventory_card_semantic_sql,
    register_inventory_charts,
)
from neoretail_bootstrap.panorama.gaps import (
    GAP_TVD,
    GAP_IVD,
    monthly_gap_semantic_sql,
    weekly_gap_card_semantic_sql,
    register_gap_charts,
)
from neoretail_bootstrap.panorama.comparisons import (
    COMPARISON_SCOPES,
    _COMPARISON_SELLOUT,
    _COMPARISON_SALES_QTY,
    _COMPARISON_LOSS_QTY,
    _COMPARISON_PRICE,
    _COMPARISON_STOCK_QTY,
    COMPARISON_METRICS,
    COMPARISON_GAP_METRICS,
    _comparison_dimension_projection,
    comparison_history_sql,
    comparison_gap_sql,
    register_comparison_charts,
)
from neoretail_bootstrap.panorama.kpis import (
    KPI_DIMENSION_SCOPES,
    KPI_INDUSTRY_OPTIONS,
    KPI_DIMENSION_VALUE,
    _kpi_dimension_projection,
    _kpi_default_projection,
    kpi_dimension_sql,
    kpi_filter_options_sql,
    kpi_dimension_params,
    kpi_filter_bar_params,
    register_kpi_charts,
    ensure_order_metrics,
)
from neoretail_bootstrap.panorama.filters import (
    WEEKLY_FILTER_COLUMNS,
    KPI_ORDER_METRIC_NAME,
    KPI_MONTH_ORDER_METRIC_NAME,
    kpi_native_filters,
    sql_filter,
    panorama_native_filters,
)
from neoretail_bootstrap.panorama.details import (
    DETAIL_DIMENSIONS,
    detail_semantic_sql,
    DETAIL_METRICS,
    detail_table_params,
    register_detail_charts,
)
from neoretail_bootstrap.panorama.osa import (
    register_osa_charts,
)
from neoretail_bootstrap.panorama.layout import (
    build_layout,
)


DASHBOARD_TITLE = "NeoRetail V9 — Panorama Indústria"


LATEST_SQL = f"""
SELECT h.*
FROM ({HISTORY_SQL}) h
WHERE h.data = (SELECT MAX(mes_ano) FROM gold.fato_historico)
""".strip()


P = {
    **M,
    "loss_qty": metric("Perda OSA qtd", "SUM(qtd_perda_osa)"),
    "price": metric("Preço médio", "SUM(faturamento) / NULLIF(SUM(volume_unidades), 0)"),
    "coverage": metric("Cobertura de estoque", "SUM(estoque_unidades) / NULLIF(SUM(volume_unidades) / 4.33, 0)"),
    "rup": metric("Ruptura", "100.0 * SUM(rup) / NULLIF(SUM(qtd_item_ativo_osa), 0)"),
    "isv": metric("Item sem venda", "100.0 * SUM(est_virtual) / NULLIF(SUM(qtd_item_ativo_osa), 0)"),
    "roi_annual": metric("ROI anual", "1200.0 * ((CASE WHEN SUM(faturamento) > 0 THEN SUM(faturamento) ELSE SUM(volume_unidades * avg_sales_price) END) - SUM(volume_unidades * avg_price_cost)) / NULLIF(SUM(estoque_medio * avg_price_cost), 0)"),
}


def main():
    app = create_app()
    with app.app_context():
        from superset import db
        from superset.connectors.sqla.models import SqlaTable, SqlMetric
        from superset.models.core import Database
        from superset.models.dashboard import Dashboard
        from superset.models.slice import Slice

        database = db.session.query(Database).filter(Database.database_name == "NeoRetail Gold - PostgreSQL Local").one()
        history = upsert_dataset(db.session, SqlaTable, database, "nr_overview_history", table_name="nr_overview_history")
        weekly = upsert_dataset(
            db.session, SqlaTable, database, "nr_panorama_weekly_interactive",
            sql=weekly_semantic_sql(),
        )
        weekly_sales = upsert_dataset(
            db.session, SqlaTable, database, "nr_panorama_sales_weekly_interactive",
            sql=weekly_sales_semantic_sql(),
        )
        weekly_sales_card = upsert_dataset(
            db.session, SqlaTable, database, "nr_panorama_sales_weekly_card_interactive",
            sql=weekly_sales_card_semantic_sql(),
        )
        monthly_sales = upsert_dataset(
            db.session, SqlaTable, database, "nr_panorama_sales_monthly_interactive",
            sql=monthly_sales_semantic_sql(),
        )
        monthly_quantity = upsert_dataset(
            db.session, SqlaTable, database, "nr_overview_quantity_interactive",
            sql=quantity_semantic_sql(),
        )
        monthly_inventory = upsert_dataset(
            db.session, SqlaTable, database, "nr_panorama_inventory_monthly_interactive",
            sql=monthly_inventory_semantic_sql(),
        )
        weekly_inventory_card = upsert_dataset(
            db.session, SqlaTable, database, "nr_panorama_inventory_weekly_card_interactive",
            sql=weekly_inventory_card_semantic_sql(),
        )
        gap_monthly = upsert_dataset(
            db.session, SqlaTable, database, "nr_panorama_gap_monthly_interactive",
            sql=monthly_gap_semantic_sql(),
        )
        gap_weekly_card = upsert_dataset(
            db.session, SqlaTable, database, "nr_panorama_gap_weekly_card_interactive",
            sql=weekly_gap_card_semantic_sql(),
        )
        comparison_history = {
            scope: upsert_dataset(
                db.session,
                SqlaTable,
                database,
                f"nr_panorama_comparison_{scope}_history",
                sql=comparison_history_sql(scope),
            )
            for scope in COMPARISON_SCOPES
        }
        comparison_gap = {
            scope: upsert_dataset(
                db.session,
                SqlaTable,
                database,
                f"nr_panorama_comparison_{scope}_gap",
                sql=comparison_gap_sql(scope),
            )
            for scope in COMPARISON_SCOPES
        }
        kpi_dimensions = {
            scope: upsert_dataset(
                db.session, SqlaTable, database,
                f"nr_panorama_kpi_dimension_{scope}",
                sql=kpi_dimension_sql(scope),
            )
            for scope in KPI_DIMENSION_SCOPES
        }
        kpi_filter_options = upsert_dataset(
            db.session, SqlaTable, database,
            "nr_panorama_kpi_filter_options",
            sql=kpi_filter_options_sql(),
        )
        ensure_order_metrics(db.session, SqlMetric, kpi_filter_options)
        latest = upsert_dataset(db.session, SqlaTable, database, "nr_panorama_latest", table_name="nr_panorama_latest")
        detail_datasets = {
            column: upsert_dataset(
                db.session, SqlaTable, database,
                f"nr_panorama_detail_{column}",
                sql=detail_semantic_sql(column),
            )
            for column in DETAIL_DIMENSIONS
        }
        mart = upsert_dataset(db.session, SqlaTable, database, "nr_panorama_opportunities", table_name="nr_panorama_opportunities")
        opportunities = mart
        opportunities_latest = upsert_dataset(db.session, SqlaTable, database, "nr_panorama_opportunities_latest", table_name="nr_panorama_opportunities_latest")
        gap_periodic = upsert_dataset(
            db.session,
            SqlaTable,
            database,
            "nr_panorama_gap_periodic",
            table_name="nr_panorama_gap_periodic",
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
                weekly_max_date = connection.execute(
                    text("SELECT MAX(data) FROM gold.nr_panorama_weekly")
                ).scalar_one()
        weekly_recent = [sql_filter(
            f"data >= DATE '{weekly_max_date.isoformat()}' - INTERVAL '12 weeks'"
        )] if weekly_max_date else []

        charts = {}
        def add(
            key, dataset, title, params, viz="neoretail-kpi-card", legacy_titles=(),
        ):
            charts[key] = upsert_chart(
                db.session,
                Slice,
                dataset,
                f"[Panorama] {title}",
                params,
                viz,
                tuple(f"[Panorama] {item}" for item in legacy_titles),
            )

        register_sales_charts(add, monthly_sales, weekly_sales_card, monthly_quantity, Q)

        # Panorama > Evolutivo de estoque.
        # The Report definition uses four outer views over the same business block:
        # Estoque, Giro x ROI, OSA and Falta x Excesso.

        # ESTOQUE
        register_inventory_charts(add, monthly_inventory, weekly_inventory_card)

        # OSA
        # %OSA = 1 - problems/active; Ruptura and ISV use STATUS_ITEM_GERAL as denominator.
        register_osa_charts(add, monthly_inventory, weekly_inventory_card)

        # FALTA x EXCESSO (Power BI selector TVD x IVD).
        register_gap_charts(add, gap_monthly, gap_weekly_card)

        kpi_dimension_labels = register_kpi_charts(add, kpi_filter_options, kpi_dimensions)

        comparison_dimensions, comparison_tabs = register_comparison_charts(add, comparison_history, comparison_gap)

        detail_dims = register_detail_charts(add, detail_datasets)

        layout = build_layout(charts, kpi_dimension_labels, comparison_dimensions, comparison_tabs, detail_dims)

        dashboard = db.session.query(Dashboard).filter(Dashboard.dashboard_title == DASHBOARD_TITLE).one_or_none()
        if dashboard is None:
            dashboard = Dashboard(dashboard_title=DASHBOARD_TITLE, slug="neoretail-v9-panorama-industria", published=True)
            db.session.add(dashboard)
        dashboard.published = True
        dashboard.position_json = json.dumps(layout.nodes, ensure_ascii=False)
        dashboard.css = (
            ".dashboard-content { background: #e7f0f5 !important; } "
            ".dashboard-component-chart-holder { border-radius: 8px; background: #fff; } "
            ".dashboard-component-chart-holder > .header { display: none !important; } "
            ".dashboard-component-tabs .dashboard-component-tabs .ant-tabs-nav-list { margin-left: auto !important; } "
            # The local selector chart has its own business heading; only
            # suppress Superset's duplicate outer chart title for this variant.
            ".dashboard-component-chart-holder:has([data-neoretail-variant='kpifilters']) .chart-header "
            "{ display: none !important; }"
        )
        comparison_dataset_ids = [
            dataset.id
            for dataset in (*comparison_history.values(), *comparison_gap.values())
        ]

        kpi_dimension_dataset_ids = [dataset.id for dataset in kpi_dimensions.values()]

        native_filters = panorama_native_filters(
            [history.id, weekly.id, weekly_sales.id, weekly_sales_card.id,
             monthly_sales.id, monthly_quantity.id, monthly_inventory.id,
             weekly_inventory_card.id, gap_monthly.id, gap_weekly_card.id,
             *comparison_dataset_ids, *kpi_dimension_dataset_ids,
             *[dataset.id for dataset in detail_datasets.values()]],
            filter_options, conversion_options, kpi_filter_options, charts,
            kpi_dimension_labels, overview_native_filters,
        )

        dashboard.json_metadata = json.dumps({"timed_refresh_immune_slices": [], "expanded_slices": {}, "refresh_frequency": 0, "color_scheme": "supersetColors", "native_filter_configuration": native_filters, "filter_bar_orientation": "HORIZONTAL"}, ensure_ascii=False)
        dashboard.slices = list(charts.values())
        db.session.commit()
        print(json.dumps({"dashboard_id": dashboard.id, "slug": dashboard.slug, "industry": {"id_customer": 142, "label": "AMBEV"}, "datasets": {"history": history.id, "weekly": weekly.id, "monthly_inventory": monthly_inventory.id, "weekly_inventory_card": weekly_inventory_card.id, "gap_monthly": gap_monthly.id, "gap_weekly_card": gap_weekly_card.id, "comparison_history": {key: value.id for key, value in comparison_history.items()}, "comparison_gap": {key: value.id for key, value in comparison_gap.items()}, "kpi_dimensions": {key: value.id for key, value in kpi_dimensions.items()}, "kpi_filter_options": kpi_filter_options.id, "latest": latest.id, "mart": mart.id, "opportunities": opportunities.id, "opportunities_latest": opportunities_latest.id, "gap_periodic": gap_periodic.id}, "chart_count": len(charts)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
