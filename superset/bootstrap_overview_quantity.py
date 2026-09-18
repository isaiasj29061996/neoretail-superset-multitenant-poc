"""Create/update the NeoRetail quantity overview dashboard.

Most quantity KPIs use the additive overview summary mart. Only the
"Distribuição e sortimento" card stays on the detailed monthly mart because
exact distinct counts of stores/items are not additive across arbitrary native
filters.
"""
from __future__ import annotations

import json

from sqlalchemy import text
from superset.app import create_app

from bootstrap_overview import (
    chart_params,
    metric,
    overview_native_filters,
    position_json,
    upsert_chart,
    upsert_dataset,
)


DASHBOARD_TITLE = "NeoRetail V9 — Visão geral quantidade"
DASHBOARD_SLUG = "neoretail-v9-visao-geral-quantidade"

Q_SUM = {
    "sales_qty": metric("Venda qtd", "SUM(sales_qty_sum)"),
    "loss_qty": metric("Perda OSA qtd", "SUM(osa_loss_qty_sum)"),
    "price": metric(
        "Preço médio",
        "SUM(faturamento_sum) / NULLIF(SUM(sales_qty_sum), 0)",
    ),
    "osa": metric(
        "OSA",
        "100.0 * (1 - SUM(osa_problem_sum) / NULLIF(SUM(osa_active_sum), 0))",
    ),
    "rupture": metric(
        "Ruptura",
        "100.0 * SUM(rupture_sum) / NULLIF(SUM(osa_active_sum), 0)",
    ),
    "isv": metric(
        "Item sem venda",
        "100.0 * SUM(isv_sum) / NULLIF(SUM(osa_active_sum), 0)",
    ),
    "coverage": metric(
        "Cobertura de estoque",
        "SUM(stock_qty_sum) / NULLIF(SUM(sales_qty_sum) / 4.33, 0)",
    ),
    "osa_critical": metric("Itens críticos OSA", "SUM(osa_critical_count)"),
    "osa_risk": metric("Itens risco OSA", "SUM(osa_risk_count)"),
    "rup_critical": metric("Itens críticos Ruptura", "SUM(rupture_critical_count)"),
    "rup_risk": metric("Itens risco Ruptura", "SUM(rupture_risk_count)"),
    "isv_critical": metric("Itens críticos ISV", "SUM(isv_critical_count)"),
    "isv_risk": metric("Itens risco ISV", "SUM(isv_risk_count)"),
}

Q_DETAIL = {
    "stores": metric("Quantidade de lojas", "COUNT(DISTINCT id_location)"),
    "items": metric("Quantidade de itens", "COUNT(DISTINCT id_item)"),
}


def comparison_params(
    dataset,
    title,
    measure,
    *,
    fmt="number",
    direction="higher",
    show_tasks=False,
    critical_metric=None,
    risk_metric=None,
    plain=False,
):
    return chart_params(
        dataset,
        title,
        "quantitycompareplain" if plain else "quantitycompare",
        [measure],
        metric_labels=measure["label"],
        metric_formats=fmt,
        metric_directions=direction,
        show_tasks=show_tasks,
        critical_metric=critical_metric,
        risk_metric=risk_metric,
        task_labels="itens críticos|itens em risco",
        help_text=title,
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
        summary = upsert_dataset(
            db.session,
            SqlaTable,
            database,
            "nr_overview_summary",
            table_name="nr_overview_summary",
        )
        history = upsert_dataset(
            db.session,
            SqlaTable,
            database,
            "nr_overview_history",
            table_name="nr_overview_history",
        )
        with database.get_sqla_engine() as engine:
            with engine.connect() as connection:
                history_max_date = connection.execute(
                    text("SELECT MAX(data) FROM gold.nr_overview_history")
                ).scalar_one()
        recent_history = [{
            "clause": "WHERE",
            "comparator": "",
            "expressionType": "SQL",
            "filterOptionName": "filter_quantity_recent",
            "fromFormData": True,
            "sqlExpression": (
                f"data >= DATE '{history_max_date.isoformat()}' - INTERVAL '4 months'"
            ),
        }] if history_max_date else []

        specs = [
            (
                summary,
                "Vendas",
                comparison_params(
                    summary, "Vendas", Q_SUM["sales_qty"],
                    fmt="number", direction="higher",
                ),
            ),
            (
                summary,
                "Perda de vendas OSA",
                comparison_params(
                    summary, "Perda de vendas OSA", Q_SUM["loss_qty"],
                    fmt="number", direction="lower",
                ),
            ),
            (
                summary,
                "Preço médio",
                comparison_params(
                    summary, "Preço médio", Q_SUM["price"],
                    fmt="currency", direction="higher", plain=True,
                ),
            ),
            (
                history,
                "Distribuição e sortimento",
                chart_params(
                    history,
                    "Distribuição e sortimento",
                    "multi",
                    [Q_DETAIL["stores"], Q_DETAIL["items"]],
                    metric_labels="Quantidade de lojas|Quantidade de itens",
                    metric_formats="number|number",
                    metric_directions="higher|higher",
                    show_tasks=False,
                    help_text="Quantidade de lojas e itens com dados no período selecionado.",
                    adhoc_filters=recent_history,
                ),
            ),
            (
                summary,
                "% OSA",
                comparison_params(
                    summary,
                    "% OSA",
                    Q_SUM["osa"],
                    fmt="percent",
                    direction="higher",
                    show_tasks=True,
                    critical_metric=Q_SUM["osa_critical"],
                    risk_metric=Q_SUM["osa_risk"],
                ),
            ),
            (
                summary,
                "Ruptura",
                comparison_params(
                    summary,
                    "Ruptura",
                    Q_SUM["rupture"],
                    fmt="percent",
                    direction="lower",
                    show_tasks=True,
                    critical_metric=Q_SUM["rup_critical"],
                    risk_metric=Q_SUM["rup_risk"],
                ),
            ),
            (
                summary,
                "Item sem venda",
                comparison_params(
                    summary,
                    "Item sem venda",
                    Q_SUM["isv"],
                    fmt="percent",
                    direction="lower",
                    show_tasks=True,
                    critical_metric=Q_SUM["isv_critical"],
                    risk_metric=Q_SUM["isv_risk"],
                ),
            ),
            (
                summary,
                "Cobertura de estoque",
                comparison_params(
                    summary, "Cobertura de estoque", Q_SUM["coverage"],
                    fmt="number", direction="lower",
                ),
            ),
        ]

        charts = [
            upsert_chart(
                db.session,
                Slice,
                dataset,
                f"[Visão quantidade] {title}",
                params,
            )
            for dataset, title, params in specs
        ]

        dashboard = db.session.query(Dashboard).filter(
            Dashboard.dashboard_title == DASHBOARD_TITLE
        ).one_or_none()
        if dashboard is None:
            dashboard = Dashboard(
                dashboard_title=DASHBOARD_TITLE,
                slug=DASHBOARD_SLUG,
                published=True,
            )
            db.session.add(dashboard)
        dashboard.slug = DASHBOARD_SLUG
        dashboard.published = True
        dashboard.position_json = position_json(charts)
        dashboard.css = (
            ".dashboard-content { background: #e7f0f5 !important; } "
            ".dashboard-component-chart-holder { border-radius: 8px; } "
            ".dashboard-component-chart-holder > .header { display: none !important; }"
        )
        dashboard.json_metadata = json.dumps(
            {
                "timed_refresh_immune_slices": [],
                "expanded_slices": {},
                "refresh_frequency": 0,
                "color_scheme": "supersetColors",
                "native_filter_configuration": overview_native_filters(
                    [summary.id, history.id]
                ),
                "filter_bar_orientation": "HORIZONTAL",
            },
            ensure_ascii=False,
        )
        dashboard.slices = charts
        db.session.commit()
        print(
            json.dumps(
                {
                    "dashboard_id": dashboard.id,
                    "slug": dashboard.slug,
                    "datasets": {
                        "summary": summary.id,
                        "history_distincts": history.id,
                    },
                    "charts": {chart.slice_name: chart.id for chart in charts},
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()
