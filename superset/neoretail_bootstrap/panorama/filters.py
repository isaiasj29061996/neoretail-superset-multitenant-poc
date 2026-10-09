"""Panorama filters: existing certified contracts and chart composition."""
from __future__ import annotations



KPI_ORDER_METRIC_NAME = "AP KPI ordem"


KPI_MONTH_ORDER_METRIC_NAME = "AP Mês ordem"


WEEKLY_FILTER_COLUMNS = (
    "rede", "bandeira", "uf", "cidade", "tipo_local", "loja", "regiao",
    "tp_activity_level", "activity_level", "item", "descricao_marca",
    "hierarquia_1", "hierarquia_2", "hierarquia_3",
)


def kpi_native_filters(filter_dataset_id: int) -> list[dict]:
    common = {"enableEmptyFilter": False, "defaultToFirstItem": False, "creatable": False, "multiSelect": False, "searchAllOptions": True, "inverseSelection": False}
    return [
        {"id": "NATIVE_FILTER-panorama-kpi-year", "controlValues": common, "name": "Ano", "filterType": "filter_select", "targets": [{"datasetId": filter_dataset_id, "column": {"name": "comparison_year"}}], "defaultDataMask": {"extraFormData": {"filters": [{"col": "comparison_year", "op": "IN", "val": [2026]}]}, "filterState": {"label": "2026", "value": [2026]}, "ownState": {}}, "cascadeParentIds": [], "scope": {"excluded": [], "rootPath": ["ROOT_ID"]}, "type": "NATIVE_FILTER", "description": ""},
        {"id": "NATIVE_FILTER-panorama-kpi-month", "controlValues": {**common, "multiSelect": True, "sortAscending": True, "sortMetric": KPI_MONTH_ORDER_METRIC_NAME}, "sortMetric": KPI_MONTH_ORDER_METRIC_NAME, "name": "Mês", "filterType": "filter_select", "targets": [{"datasetId": filter_dataset_id, "column": {"name": "comparison_year_month"}}], "defaultDataMask": {"extraFormData": {}, "filterState": {}, "ownState": {}}, "cascadeParentIds": ["NATIVE_FILTER-panorama-kpi-year"], "scope": {"excluded": [], "rootPath": ["ROOT_ID"]}, "type": "NATIVE_FILTER", "description": "Selecione meses específicos dentro do ano. Sem seleção, considera todos os meses."},
        {"id": "NATIVE_FILTER-panorama-kpi-selector", "controlValues": {**common, "sortAscending": True, "sortMetric": KPI_ORDER_METRIC_NAME}, "sortMetric": KPI_ORDER_METRIC_NAME, "name": "Visualização por", "filterType": "filter_select", "targets": [{"datasetId": filter_dataset_id, "column": {"name": "comparison_kpi"}}], "defaultDataMask": {"extraFormData": {"filters": [{"col": "comparison_kpi", "op": "IN", "val": ["Venda R$"]}]}, "filterState": {"label": "Venda R$", "value": ["Venda R$"]}, "ownState": {}}, "cascadeParentIds": [], "scope": {"excluded": [], "rootPath": ["ROOT_ID"]}, "type": "NATIVE_FILTER", "description": ""},
    ]


def sql_filter(expression):
    return {
        "clause": "WHERE",
        "comparator": "",
        "expressionType": "SQL",
        "filterOptionName": "filter_panorama_gap_period",
        "fromFormData": True,
        "sqlExpression": expression,
    }


def panorama_native_filters(dataset_ids, filter_options, conversion_options, kpi_filter_options, charts, kpi_dimension_labels, overview_native_filters):
    filter_targets = {column: filter_options.id for column in WEEKLY_FILTER_COLUMNS}
    filter_targets["nm_measure"] = conversion_options.id
    native_filters = overview_native_filters(
        dataset_ids,
        filter_targets,
    )
    toolbar_id = charts["kpi_control_bar"].id
    for nf in native_filters:
        nf["scope"]["excluded"] = [
            *nf["scope"].get("excluded", []), toolbar_id,
        ]
    native_filters.extend(kpi_native_filters(kpi_filter_options.id))
    kpi_targets = {
        charts[f"kpi_dimension_{scope}"].id
        for scope, _ in kpi_dimension_labels
    }
    kpi_excluded = [
        chart.id for chart in charts.values()
        if chart.id not in kpi_targets
    ]
    for nf in native_filters[-3:]:
        nf["scope"] = {"rootPath": ["ROOT_ID"], "excluded": kpi_excluded}
    return native_filters
