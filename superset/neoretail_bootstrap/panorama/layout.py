"""Panorama layout: existing certified contracts and chart composition."""
from __future__ import annotations

from neoretail_bootstrap.core.layout import Layout


def build_layout(charts, kpi_dimension_labels, comparison_dimensions, comparison_tabs, detail_dims):
    layout = Layout()
    grid_parents = ["ROOT_ID", "GRID_ID"]
    layout.period_tabs("GRID_ID", grid_parents, "Evolutivo de vendas", [
        ("Valor", [(period, charts[f"sales_value_{period}"]) for period in ("mensal", "semanal")]),
        ("Quantidade", [(period, charts[f"sales_quantity_{period}"]) for period in ("mensal", "semanal")]),
    ], 58)
    layout.period_tabs("GRID_ID", grid_parents, "Evolutivo de estoque", [
        (section, [(period, charts[f"{key}_{period}"]) for period in ("mensal", "semanal")])
        for section, key in (("Estoque", "stock"), ("Giro x ROI", "giro_roi"), ("OSA", "osa"), ("Falta x Excesso", "gap"))
    ], 58)
    layout.tabs("GRID_ID", grid_parents, "Comparativo de KPIs por dimensão", [
        (
            "KPIs",
            [
                {"charts": [charts["kpi_control_bar"]], "height": 15},
                [charts[f"kpi_dimension_{scope}"] for scope, _ in kpi_dimension_labels],
            ],
        )
    ], 52)
    layout.tabs("GRID_ID", grid_parents, "Comparativos", [
        (
            tab_label,
            [[charts[f"compare_{tab_key}_{scope}"] for scope, _ in comparison_dimensions]],
        )
        for tab_label, tab_key, _ in comparison_tabs
    ], 48)
    layout.tabs("GRID_ID", grid_parents, "Análise detalhada", [
        (label, [[charts[f"detail_{column}"]]]) for column, label in detail_dims
    ], 55)
    return layout
