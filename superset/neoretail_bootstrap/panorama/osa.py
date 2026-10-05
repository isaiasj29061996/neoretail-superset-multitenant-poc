"""Panorama osa: existing certified contracts and chart composition."""
from __future__ import annotations

from neoretail_bootstrap.core.metrics import metric
from neoretail_bootstrap.core.chart_params import custom_params


def register_osa_charts(add, monthly_inventory, weekly_inventory_card):
    osa_measures = [
        metric("OSA problemas", "SUM(osa_problem_sum)"),
        metric("OSA ativos", "SUM(osa_active_sum)"),
        metric("Ruptura numerador", "SUM(rupture_sum)"),
        metric("Ruptura denominador", "SUM(status_sum)"),
        metric("ISV numerador", "SUM(isv_sum)"),
        metric("ISV denominador", "SUM(status_sum)"),
    ]
    osa_semantics = "one_minus_ratio:0:2|ratio_percent:2:2|ratio_percent:4:2"
    params = custom_params(
        monthly_inventory,
        "Evolutivo de estoque",
        osa_measures,
        grain="P1M",
        styles="line|line|line",
        formats="percent|percent|percent",
        labels="% OSA|% Ruptura|% ISV",
        metric_semantics=osa_semantics,
        summary_count=3,
        timeline_limit=13,
    )
    add("osa_mensal", monthly_inventory, "Evolutivo de estoque — OSA mensal", params)

    params = custom_params(
        weekly_inventory_card,
        "Evolutivo de estoque",
        osa_measures,
        grain="P1W",
        styles="line|line|line",
        formats="percent|percent|percent",
        labels="% OSA|% Ruptura|% ISV",
        metric_semantics=osa_semantics,
        summary_count=3,
        timeline_limit=13,
        summary_query_scope="summary",
        timeline_query_scope="timeline",
    )
    add("osa_semanal", weekly_inventory_card, "Evolutivo de estoque — OSA semanal", params)
