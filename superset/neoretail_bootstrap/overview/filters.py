"""Overview filters: existing certified contracts."""
from __future__ import annotations



HEADLINE_FILTER_COLUMNS = (
    "rede", "bandeira", "uf", "cidade", "tipo_local", "loja", "regiao",
    "deposito", "tp_activity_level", "item", "descricao_marca",
    "hierarquia_1", "hierarquia_2", "hierarquia_3", "hierarquia_4",
    "unidade_medida",
)


def sql_filter(expression: str, name: str = "filter_recent_period") -> dict:
    return {
        "clause": "WHERE",
        "comparator": "",
        "expressionType": "SQL",
        "filterOptionName": name,
        "fromFormData": True,
        "sqlExpression": expression,
    }


def _filter_definitions():
    return [
        ("nm_measure", "Medida", []),
        ("rede", "Rede", []),
        ("bandeira", "Bandeira", ["rede"]),
        ("uf", "UF", []),
        ("cidade", "Cidade", ["uf"]),
        ("tipo_local", "Tipo de local", []),
        ("loja", "Loja", ["tipo_local"]),
        ("tp_activity_level", "Nível de atividade", []),
        ("descricao_marca", "Marca", []),
        ("hierarquia_1", "Hierarquia 1", ["descricao_marca"]),
        ("hierarquia_2", "Hierarquia 2", ["hierarquia_1"]),
        ("hierarquia_3", "Hierarquia 3", ["hierarquia_2"]),
        ("item", "Item", ["hierarquia_3"]),
    ]


def _native_filters_for_targets(targets_by_column):
    definitions = _filter_definitions()
    ids = {column: f"NATIVE_FILTER-neoretail-{column}" for column, _, _ in definitions}
    return [{
        "id": ids[column],
        "controlValues": {
            "enableEmptyFilter": False,
            "defaultToFirstItem": False,
            "creatable": False,
            "multiSelect": column != "nm_measure",
            "searchAllOptions": True,
            "inverseSelection": False,
        },
        "name": label,
        "filterType": "filter_select",
        "targets": targets_by_column(column),
        "defaultDataMask": ({
            "extraFormData": {"filters": [{"col": "nm_measure", "op": "IN", "val": ["unidade"]}]},
            "filterState": {"label": "unidade", "value": ["unidade"]},
            "ownState": {},
        } if column == "nm_measure" else {
            "extraFormData": {}, "filterState": {}, "ownState": {},
        }),
        "cascadeParentIds": [ids[parent] for parent in parents],
        "scope": {"excluded": [], "rootPath": ["ROOT_ID"]},
        "type": "NATIVE_FILTER",
        "description": "",
    } for column, label, parents in definitions]


def native_filters(dataset_id, filter_dataset_id=None):
    target_id = filter_dataset_id or dataset_id
    return _native_filters_for_targets(
        lambda column: [{"datasetId": target_id, "column": {"name": column}}]
    )


def overview_native_filters(dataset_ids, filter_dataset_id=None):
    ids = list(dict.fromkeys(int(dataset_id) for dataset_id in dataset_ids))
    return _native_filters_for_targets(
        lambda column: [{
            "datasetId": (
                filter_dataset_id.get(column)
                if isinstance(filter_dataset_id, dict)
                else filter_dataset_id
            ) or ids[0],
            "column": {"name": column},
        }]
    )
