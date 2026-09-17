"""Create/update the NeoRetail quantity overview dashboard.

The dashboard reproduces the Power BI page "Visão geral - visão indústria quantidade"
using the existing Gold serving mart and the NeoRetail KPI plugin. Only Superset
metadata is changed here; no source data is mutated.
"""
from __future__ import annotations

import json

from superset.app import create_app

from bootstrap_overview import (
    M,
    chart_params,
    metric,
    native_filters,
    position_json,
    upsert_chart,
    upsert_dataset,
)


DASHBOARD_TITLE = "NeoRetail V9 — Visão geral quantidade"
DASHBOARD_SLUG = "neoretail-v9-visao-geral-quantidade"

Q = {
    "sales_qty": M["sales_qty"],
    "loss_qty": metric("Perda OSA qtd", "SUM(qtd_perda_osa)"),
    "price": metric("Preço médio", "SUM(faturamento) / NULLIF(SUM(volume_unidades), 0)"),
    "stores": metric("Quantidade de lojas", "COUNT(DISTINCT id_location)"),
    "items": metric("Quantidade de itens", "COUNT(DISTINCT id_item)"),
    "osa": M["osa"],
    "rupture": metric("Ruptura", "100.0 * SUM(rup) / NULLIF(SUM(qtd_item_ativo_osa), 0)"),
    "isv": metric("Item sem venda", "100.0 * SUM(est_virtual) / NULLIF(SUM(qtd_item_ativo_osa), 0)"),
    "coverage": metric("Cobertura de estoque", "SUM(estoque_unidades) / NULLIF(SUM(volume_unidades) / 4.33, 0)"),
    "rup_critical": metric(
        "Itens críticos Ruptura",
        "COUNT(DISTINCT CASE WHEN COALESCE(rup, 0) > 0 AND tp_activity_level = 'F' THEN opportunity_key END)",
    ),
    "rup_risk": metric(
        "Itens risco Ruptura",
        "COUNT(DISTINCT CASE WHEN COALESCE(rup, 0) > 0 AND tp_activity_level = 'S' THEN opportunity_key END)",
    ),
    "isv_critical": metric(
        "Itens críticos ISV",
        "COUNT(DISTINCT CASE WHEN COALESCE(est_virtual, 0) > 0 AND tp_activity_level = 'F' THEN opportunity_key END)",
    ),
    "isv_risk": metric(
        "Itens risco ISV",
        "COUNT(DISTINCT CASE WHEN COALESCE(est_virtual, 0) > 0 AND tp_activity_level = 'S' THEN opportunity_key END)",
    ),
}


def comparison_params(dataset, title, measure, *, fmt="number", direction="higher", show_tasks=False, critical_metric=None, risk_metric=None, plain=False):
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
        history = upsert_dataset(
            db.session,
            SqlaTable,
            database,
            "nr_overview_history",
            table_name="nr_overview_history",
        )

        specs = [
            (
                "Vendas",
                comparison_params(history, "Vendas", Q["sales_qty"], fmt="number", direction="higher"),
            ),
            (
                "Perda de vendas OSA",
                comparison_params(history, "Perda de vendas OSA", Q["loss_qty"], fmt="number", direction="lower"),
            ),
            (
                "Preço médio",
                comparison_params(history, "Preço médio", Q["price"], fmt="currency", direction="higher", plain=True),
            ),
            (
                "Distribuição e sortimento",
                chart_params(
                    history,
                    "Distribuição e sortimento",
                    "multi",
                    [Q["stores"], Q["items"]],
                    metric_labels="Quantidade de lojas|Quantidade de itens",
                    metric_formats="number|number",
                    metric_directions="higher|higher",
                    show_tasks=False,
                    help_text="Quantidade de lojas e itens com dados no período selecionado.",
                ),
            ),
            (
                "% OSA",
                comparison_params(
                    history,
                    "% OSA",
                    Q["osa"],
                    fmt="percent",
                    direction="higher",
                    show_tasks=True,
                    critical_metric=M["osa_critical"],
                    risk_metric=M["osa_risk"],
                ),
            ),
            (
                "Ruptura",
                comparison_params(
                    history,
                    "Ruptura",
                    Q["rupture"],
                    fmt="percent",
                    direction="lower",
                    show_tasks=True,
                    critical_metric=Q["rup_critical"],
                    risk_metric=Q["rup_risk"],
                ),
            ),
            (
                "Item sem venda",
                comparison_params(
                    history,
                    "Item sem venda",
                    Q["isv"],
                    fmt="percent",
                    direction="lower",
                    show_tasks=True,
                    critical_metric=Q["isv_critical"],
                    risk_metric=Q["isv_risk"],
                ),
            ),
            (
                "Cobertura de estoque",
                comparison_params(history, "Cobertura de estoque", Q["coverage"], fmt="number", direction="lower"),
            ),
        ]

        charts = [
            upsert_chart(db.session, Slice, history, f"[Visão quantidade] {title}", params)
            for title, params in specs
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
                "native_filter_configuration": native_filters(history.id),
                "filter_bar_orientation": "HORIZONTAL",
            }
        )
        dashboard.slices = charts
        db.session.commit()
        print(
            json.dumps(
                {
                    "dashboard_id": dashboard.id,
                    "slug": dashboard.slug,
                    "dataset": history.id,
                    "charts": {chart.slice_name: chart.id for chart in charts},
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()
