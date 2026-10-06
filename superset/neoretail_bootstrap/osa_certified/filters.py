"""Certified OSA dimensional and native-filter contracts."""
from __future__ import annotations
from neoretail_bootstrap.panorama.filters import WEEKLY_FILTER_COLUMNS
from neoretail_bootstrap.overview.filters import overview_native_filters

DIMENSION_OVERRIDES = {
    "rede": "l.rede",
    "bandeira": "l.bandeira",
    "uf": "l.uf",
    "cidade": "l.cidade",
    "tipo_local": "l.tipo_local",
    "loja": "l.loja",
    "regiao": "l.regiao",
    "item": "i.item",
    "descricao_marca": "i.descricao_marca",
    "hierarquia_1": "i.hierarquia_1",
    "hierarquia_2": "i.hierarquia_2",
    "hierarquia_3": "i.hierarquia_3",
}


def _dimension_nulls() -> str:
    return ",".join(f"NULL::text AS {column}" for column in WEEKLY_FILTER_COLUMNS)


def _measure_filter(alias: str = "o") -> str:
    return f"""
{{% set measure_filters = get_filters('nm_measure', remove_filter=True) %}}
{{% if measure_filters|length == 0 %}}
  AND {alias}.nm_measure='unidade'
{{% else %}}
  {{% for filter in measure_filters %}}
    {{% if filter.get('op') == 'IN' %}}
      AND {alias}.nm_measure IN {{{{ filter.get('val') | where_in }}}}
    {{% elif filter.get('op') == 'NOT IN' %}}
      AND {alias}.nm_measure NOT IN {{{{ filter.get('val') | where_in }}}}
    {{% endif %}}
  {{% endfor %}}
{{% endif %}}
""".strip()


def _period_filter(period_dataset_id: int, excluded: list[int]) -> dict:
    return {
        "id": "NATIVE_FILTER-osa-certified-period",
        "controlValues": {
            "enableEmptyFilter": False,
            "defaultToFirstItem": False,
            "creatable": False,
            "multiSelect": False,
            "searchAllOptions": False,
            "inverseSelection": False,
            "sortAscending": True,
        },
        "name": "Período",
        "filterType": "filter_select",
        "targets": [{
            "datasetId": period_dataset_id,
            "column": {"name": "osa_period"},
        }],
        "defaultDataMask": {
            "extraFormData": {
                "filters": [{"col": "osa_period", "op": "IN", "val": ["Mês Anterior"]}],
            },
            "filterState": {"label": "Mês Anterior", "value": ["Mês Anterior"]},
            "ownState": {},
        },
        "cascadeParentIds": [],
        "scope": {"excluded": excluded, "rootPath": ["ROOT_ID"]},
        "type": "NATIVE_FILTER",
        "description": "MTD, Mês Anterior, U3M ou YTD. O padrão reproduz o estado observado no Power BI.",
    }


def native_filters(monthly, weekly, causes, matrix_datasets, filter_options, period_options, charts):
    dataset_ids = [
        monthly.id,weekly.id,causes.id,
        *[dataset.id for dataset in matrix_datasets.values()],
    ]
    native = overview_native_filters(dataset_ids,filter_options.id)
    top_ids = {
        charts["value_month"].id,charts["value_week"].id,
        charts["qty_month"].id,charts["qty_week"].id,
    }
    period_excluded = list(top_ids)
    native.append(_period_filter(period_options.id,period_excluded))

    return native
