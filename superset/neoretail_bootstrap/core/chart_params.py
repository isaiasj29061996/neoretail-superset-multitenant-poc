"""Shared chart params helpers extracted without changing defaults."""
from __future__ import annotations


def chart_params(dataset, title, variant, metrics, **extra):
    params = {
        "datasource": f"{dataset.id}__table",
        "viz_type": "neoretail-kpi-card",
        "x_axis": "data",
        "time_grain_sqla": "P1M",
        "time_range": extra.pop("time_range", "No filter"),
        "metrics": metrics,
        "row_limit": 10000,
        "card_title": title,
        "card_variant": variant,
        "help_text": extra.pop("help_text", title),
        "metric_labels": extra.pop("metric_labels", "|".join(m["label"] for m in metrics)),
        "metric_formats": extra.pop("metric_formats", "number"),
        "metric_directions": extra.pop("metric_directions", "higher"),
        "accent_color": "#7C4AD9",
        "analysis_url": "",
        "show_tasks": extra.pop("show_tasks", False),
        "adhoc_filters": [],
        "groupby": extra.pop("groupby", []),
        **extra,
    }
    return params


def custom_params(dataset, title, metrics, *, grain="P1M", styles="bar|bar|line", formats="number", groupby=None, variant="panorama", row_limit=10000, labels=None, **extra):
    params = {
        "datasource": f"{dataset.id}__table", "viz_type": "neoretail-kpi-card",
        "x_axis": "data", "time_grain_sqla": grain, "time_range": "No filter",
        "metrics": metrics, "row_limit": row_limit, "card_title": title,
        "card_variant": variant, "help_text": title, "metric_labels": labels or "|".join(m["label"] for m in metrics),
        "metric_formats": formats, "metric_directions": "higher", "chart_styles": styles,
        "accent_color": "#7C4AD9", "show_tasks": False, "adhoc_filters": [], "groupby": groupby or [],
    }
    params.update(extra)
    return params


def table_params(dataset, groupby, metrics, page_length=12):
    return {
        "datasource": f"{dataset.id}__table", "viz_type": "table", "query_mode": "aggregate",
        "groupby": [groupby], "metrics": metrics, "adhoc_filters": [], "time_range": "No filter",
        "row_limit": 1000, "page_length": page_length, "include_search": True,
        "server_pagination": False, "order_desc": True, "table_timestamp_format": "%d/%m/%Y",
        "percent_metrics": [], "align_pn": False, "color_pn": False, "show_cell_bars": False,
    }


def comparison_pivot_params(dataset, rows, metrics):
    """Power BI matrix equivalent: hierarchy rows and mixed semantic metrics."""
    return {
        "datasource": f"{dataset.id}__table",
        "viz_type": "pivot_table_v2",
        "groupbyRows": list(rows),
        "groupbyColumns": [],
        "metrics": metrics,
        "adhoc_filters": [],
        "time_range": "Current year",
        # The AMBEV retail hierarchy has more than 2,000 leaf rows.  The PBIP
        # matrix has no Top N filter, so the Superset contract must not silently
        # truncate it at the former 1,000-row default.
        "row_limit": 10000,
        "order_desc": True,
        "aggregateFunction": "Sum",
        "rowOrder": "value_z_to_a",
        "colOrder": "key_a_to_z",
        "transposePivot": False,
        "combineMetric": False,
        "showRowTotals": True,
        "showColTotals": False,
        "expandRows": False,
        # Pivot v2 accepts per-metric columnFormats. Keep SMART_NUMBER as
        # fallback, but preserve the Power BI percentage/currency formats for
        # mixed matrices such as Sell out + Markup and Estoque + ROI.
        "columnFormats": {
            item["label"]: item.get("d3Format")
            for item in metrics
            if isinstance(item, dict) and item.get("label") and item.get("d3Format")
        },
        "valueFormat": "SMART_NUMBER",
        "date_format": "%m/%Y",
    }
