"""Certified OSA chart specs and layout; no persistence."""
from __future__ import annotations
from neoretail_bootstrap.core.chart_params import custom_params, comparison_pivot_params
from neoretail_bootstrap.core.layout import Layout
from .semantics import TOP_VALUE_METRICS, TOP_QTY_METRICS, CAUSE_VALUE, CAUSE_QTY
from .matrices import MATRIX_SCOPES, TABLE_VALUE as MATRIX_VALUE, TABLE_QTY as MATRIX_QTY, TABLE_PROBLEMS as MATRIX_PROBLEMS, TABLE_OSA as MATRIX_OSA

def _top_params(dataset, title: str, metrics: list[dict], *, weekly: bool, quantity: bool):
    params = custom_params(
        dataset,
        title,
        metrics,
        grain="P1D" if weekly else "P1M",
        # Power BI uses a line+clustered-column combo here: Venda is the
        # column, % Perda and %OSA are lines. Perda OSA remains available as
        # the KPI summary value, but is not an extra timeline series.
        styles="bar|hidden|line|line",
        formats=(
            "quantity|quantity|percent|percent"
            if quantity else
            "currency|currency|percent|percent"
        ),
        variant="panorama",
        row_limit=1000,
    )
    params.update({
        "summary_count": "4",
        "summary_labels": "U3M|U3M|U3M|U3M",
        "timeline_limit": "13" if weekly else "0",
    })
    return params


def _cause_params(dataset, title: str, metric_def: dict, groupby: str, fmt: str):
    return custom_params(
        dataset,
        title,
        [metric_def],
        groupby=[groupby],
        variant="verticalbars",
        formats=fmt,
        row_limit=20,
    )


def _matrix_params(dataset, rows: tuple[str, ...], metrics: list[dict]):
    params = comparison_pivot_params(dataset, rows, metrics)
    params["time_range"] = "No filter"
    params["row_limit"] = 10000
    return params


CSS = '.dashboard-content { background:#e7f0f5 !important; } .dashboard-component-chart-holder { border-radius:8px; background:#fff; } .dashboard-component-chart-holder > .header { display:none !important; }'

def chart_specs(monthly, weekly, causes, matrix_datasets):
    specs = []
    def add(key, dataset, title, params, viz="neoretail-kpi-card"):
        specs.append((key, dataset, title, params, viz))

    add(
        "value_month",monthly,"Visão geral — Valor mensal",
        _top_params(monthly,"Visão geral — Valor mensal",TOP_VALUE_METRICS,
                    weekly=False,quantity=False),
    )
    add(
        "value_week",weekly,"Visão geral — Valor semanal",
        _top_params(weekly,"Visão geral — Valor semanal",TOP_VALUE_METRICS,
                    weekly=True,quantity=False),
    )
    add(
        "qty_month",monthly,"Visão geral — Quantidade mensal",
        _top_params(monthly,"Visão geral — Quantidade mensal",TOP_QTY_METRICS,
                    weekly=False,quantity=True),
    )
    add(
        "qty_week",weekly,"Visão geral — Quantidade semanal",
        _top_params(weekly,"Visão geral — Quantidade semanal",TOP_QTY_METRICS,
                    weekly=True,quantity=True),
    )

    for mode, metric_def, fmt in (
        ("value",CAUSE_VALUE,"currency"),
        ("qty",CAUSE_QTY,"quantity"),
    ):
        label = "Valor" if mode=="value" else "Quantidade"
        add(
            f"{mode}_motive",causes,f"Perda OSA por motivo — {label}",
            _cause_params(
                causes,f"Perda OSA por motivo — {label}",
                metric_def,"motivo_osa",fmt,
            ),
        )
        add(
            f"{mode}_cause",causes,f"Perda OSA por causa — {label}",
            _cause_params(
                causes,f"Perda OSA por causa — {label}",
                metric_def,"causa_osa",fmt,
            ),
        )

    for mode, loss_metric in (("value",MATRIX_VALUE),("qty",MATRIX_QTY)):
        label = "Valor" if mode=="value" else "Quantidade"
        for key,(title,group_column) in MATRIX_SCOPES.items():
            dataset = matrix_datasets[key]
            add(
                f"{mode}_matrix_{key}",dataset,f"{title} — {label}",
                _matrix_params(
                    dataset,(group_column,),
                    [loss_metric,MATRIX_PROBLEMS,MATRIX_OSA],
                ),
                "pivot_table_v2",
            )

    return specs

def position_json(charts):
    # The Power BI implementation has separate Valor and Quantidade pages.
    # In Superset we keep one dashboard, but the mode selector owns the
    # whole analytical canvas. This prevents mixed states such as a Valor
    # timeline with Quantidade cause/matrix visuals.
    layout = Layout()
    parents = ["ROOT_ID","GRID_ID"]
    mode_tabs_id = layout._id("TABS")
    mode_tab_ids = []
    layout.nodes[mode_tabs_id] = {
        "id": mode_tabs_id,
        "type": "TABS",
        "parents": parents,
        "children": mode_tab_ids,
        "meta": {"defaultText": "Visão OSA"},
    }
    layout.nodes["GRID_ID"]["children"].append(mode_tabs_id)

    mode_specs = (
        (
            "Valor",
            charts["value_month"], charts["value_week"],
            charts["value_motive"], charts["value_cause"],
            charts["value_matrix_region"], charts["value_matrix_retail"],
            charts["value_matrix_item"],
        ),
        (
            "Quantidade",
            charts["qty_month"], charts["qty_week"],
            charts["qty_motive"], charts["qty_cause"],
            charts["qty_matrix_region"], charts["qty_matrix_retail"],
            charts["qty_matrix_item"],
        ),
    )
    for (
        mode_label, monthly_chart, weekly_chart, motive_chart, cause_chart,
        region_chart, retail_chart, item_chart,
    ) in mode_specs:
        tab_id = layout._id("TAB")
        mode_tab_ids.append(tab_id)
        tab_parents = [*parents, mode_tabs_id]
        layout.nodes[tab_id] = {
            "id": tab_id,
            "type": "TAB",
            "parents": tab_parents,
            "children": [],
            "meta": {"text": mode_label},
        }
        content_parents = [*tab_parents, tab_id]
        layout.tabs(
            tab_id,
            content_parents,
            f"Período de {mode_label}",
            [
                ("Mensal", [[monthly_chart]]),
                ("Semanal", [[weekly_chart]]),
            ],
            height=58,
        )
        layout.row(tab_id, content_parents, [motive_chart], 44)
        layout.row(tab_id, content_parents, [cause_chart], 48)
        layout.row(
            tab_id,
            content_parents,
            [region_chart, retail_chart, item_chart],
            52,
        )

    return layout.nodes
