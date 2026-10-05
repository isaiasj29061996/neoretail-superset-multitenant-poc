"""Overview presentation: existing certified contracts."""
from __future__ import annotations

import json
from neoretail_bootstrap.core.chart_params import chart_params
from .filters import sql_filter
from .semantics import OVERVIEW_M, ROI_COMPONENTS, MARKUP_COMPONENTS, TVD_DAILY, IVD_DAILY


def position_json(charts):
    root = {"ROOT_ID": {"id": "ROOT_ID", "type": "ROOT", "children": ["GRID_ID"]}}
    grid = {
        "GRID_ID": {
            "id": "GRID_ID",
            "type": "GRID",
            "parents": ["ROOT_ID"],
            "children": ["ROW-1", "ROW-2"],
        }
    }
    layout = {**root, **grid}
    for row_index, row_charts in enumerate((charts[:4], charts[4:]), 1):
        row_id = f"ROW-{row_index}"
        children = []
        for chart in row_charts:
            chart_id = f"CHART-{chart.id}"
            children.append(chart_id)
            layout[chart_id] = {
                "id": chart_id,
                "type": "CHART",
                "parents": ["ROOT_ID", "GRID_ID", row_id],
                "children": [],
                "meta": {
                    "chartId": chart.id,
                    "height": 50,
                    "width": 3,
                    "sliceName": chart.slice_name,
                    "uuid": str(chart.uuid),
                },
            }
        layout[row_id] = {
            "id": row_id,
            "type": "ROW",
            "parents": ["ROOT_ID", "GRID_ID"],
            "children": children,
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
        }
    return json.dumps(layout)


def chart_specs(tvd_daily, ivd_daily, summary, osa_summary, tvd_max_date, ivd_max_date):
    tvd_recent = [sql_filter(
        f"data >= DATE '{tvd_max_date.isoformat()}' - INTERVAL '4 months'",
        "filter_tvd_recent",
    )] if tvd_max_date else []
    ivd_recent = [sql_filter(
        f"data >= DATE '{ivd_max_date.isoformat()}' - INTERVAL '4 months'",
        "filter_ivd_recent",
    )] if ivd_max_date else []

    specs = [
        (tvd_daily, "TVD - Pré-ruptura", chart_params(
            tvd_daily, "TVD - Pré-ruptura", "area", [TVD_DAILY["tvd"]],
            show_tasks=True, critical_metric=TVD_DAILY["critical"], risk_metric=TVD_DAILY["risk"],
            metric_formats="currency", metric_directions="lower",
            time_grain_sqla="P1D", semantic_period="month_last_nonblank",
            semantic_profile="direct_average",
            task_labels="itens críticos|itens com risco",
            help_text="TVD mensal e tarefas na última data com dado.",
            adhoc_filters=tvd_recent,
        )),
        (ivd_daily, "IVD - Excesso", chart_params(
            ivd_daily, "IVD - Excesso", "area", [IVD_DAILY["ivd"]],
            show_tasks=True, critical_metric=IVD_DAILY["critical"], risk_metric=IVD_DAILY["risk"],
            metric_formats="currency", metric_directions="lower",
            time_grain_sqla="P1D", semantic_period="month_last_nonblank",
            semantic_profile="direct_average",
            task_labels="itens críticos|itens com risco",
            help_text="IVD mensal e tarefas na última data com dado.",
            adhoc_filters=ivd_recent,
        )),
        (summary, "Giro", chart_params(
            summary, "Giro", "bars", [OVERVIEW_M["giro_sum"], OVERVIEW_M["giro_count"]],
            groupby=["activity_level"], metric_labels="Giro", metric_formats="number",
            metric_directions="lower", semantic_profile="weighted_average",
            adhoc_filters=[sql_filter("semantic_scope = 'activity'", "filter_activity_scope")],
        )),
        (osa_summary, "OSA", chart_params(
            osa_summary, "OSA", "osa", [
                OVERVIEW_M["osa_problem"], OVERVIEW_M["osa_active"], OVERVIEW_M["osa_loss"],
            ],
            show_tasks=True, critical_metric=OVERVIEW_M["osa_critical"],
            risk_metric=OVERVIEW_M["osa_risk"],
            metric_labels="% Numerico|Perda OSA", metric_formats="percent|currency",
            metric_directions="higher|lower", semantic_profile="osa_bundle",
            task_labels="itens criticos|itens com risco",
            help_text="OSA por razao dos totais, perda pela fonte mensal de causas e alertas por contagem de linhas.",
        )),
        (summary, "Vendas", chart_params(summary, "Vendas", "multi", [OVERVIEW_M["sellout"], OVERVIEW_M["cost"], OVERVIEW_M["sales_qty"]], metric_labels="Venda sell out|Venda custo|Venda qtd", metric_formats="currency|currency|number", metric_directions="higher|lower|higher", semantic_profile="direct_average", adhoc_filters=[sql_filter("semantic_scope = 'all'", "filter_all_scope")])),
        (summary, "Estoque", chart_params(summary, "Estoque", "multi", [OVERVIEW_M["stock_cost"], OVERVIEW_M["stock_qty"]], metric_labels="Estoque custo|Estoque qtd", metric_formats="currency|number", metric_directions="lower|lower", semantic_profile="stock_bundle", adhoc_filters=[sql_filter("semantic_scope = 'all'", "filter_all_scope")])),
        (summary, "ROI", chart_params(summary, "ROI", "bars", ROI_COMPONENTS, groupby=["activity_level"], metric_labels="ROI", metric_formats="percent", metric_directions="higher", semantic_profile="roi", show_annual=True, adhoc_filters=[sql_filter("semantic_scope = 'activity'", "filter_activity_scope")])),
        (summary, "MARKUP", chart_params(summary, "MARKUP", "bars", MARKUP_COMPONENTS, groupby=["activity_level"], metric_labels="Markup", metric_formats="percent", metric_directions="higher", semantic_profile="markup", adhoc_filters=[sql_filter("semantic_scope = 'activity'", "filter_activity_scope")])),
    ]
    return specs
