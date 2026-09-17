"""Create/update NeoRetail export dashboards for daily and monthly history."""
from __future__ import annotations

import json

from superset.app import create_app

from bootstrap_overview import metric, upsert_dataset
from bootstrap_panorama import Layout, upsert_chart


DATABASE_NAME = "NeoRetail Gold - PostgreSQL Local"
EXPORT_VALUE = metric("Venda", "SUM(COALESCE(venda_qtd, 0))")


def pivot_params(dataset, rows, *, daily: bool):
    return {
        "datasource": f"{dataset.id}__table",
        "viz_type": "pivot_table_v2",
        "groupbyRows": rows,
        "groupbyColumns": ["data"],
        "metrics": [EXPORT_VALUE],
        "adhoc_filters": [],
        "time_range": "No filter",
        "row_limit": 150000,
        "order_desc": False,
        "aggregateFunction": "Sum",
        "rowOrder": "key_a_to_z",
        "colOrder": "key_a_to_z",
        "transposePivot": False,
        "combineMetric": True,
        "showRowTotals": True,
        "showColTotals": False,
        "valueFormat": "SMART_NUMBER",
        "date_format": "%d/%m/%Y" if daily else "%m/%Y",
    }


def export_filters(dataset_id: int, *, daily: bool):
    definitions = [
        ("rede", "Rede", []),
        ("bandeira", "Bandeira", ["rede"]),
        ("uf", "UF", []),
        ("cidade", "Cidade", ["uf"]),
        ("tipo_local", "Tipo local", []),
        ("loja", "Loja", ["tipo_local"]),
        ("nivel_atividade", "Nível de atividade", []),
        ("descricao_marca", "Descrição marca", []),
        ("hierarquia_1", "Hierarquia 1", ["descricao_marca"]),
        ("hierarquia_2", "Hierarquia 2", ["hierarquia_1"]),
        ("hierarquia_3", "Hierarquia 3", ["hierarquia_2"]),
        ("item", "Item", ["hierarquia_3"]),
        ("unidade_medida", "Unidade de medida", []),
        ("indicador", "Indicador", []),
        ("ano", "Ano", []),
        ("mes", "Mês", ["ano"]),
    ]
    if daily:
        definitions.append(("dia", "Dia", ["mes"]))

    ids = {column: f"NATIVE_FILTER-export-{'dia' if daily else 'mes'}-{column}" for column, _, _ in definitions}
    return [{
        "id": ids[column],
        "controlValues": {
            "enableEmptyFilter": False,
            "defaultToFirstItem": False,
            "creatable": False,
            "multiSelect": True,
            "searchAllOptions": True,
            "inverseSelection": False,
        },
        "name": label,
        "filterType": "filter_select",
        "targets": [{"datasetId": dataset_id, "column": {"name": column}}],
        "defaultDataMask": {"extraFormData": {}, "filterState": {}, "ownState": {}},
        "cascadeParentIds": [ids[parent] for parent in parents],
        "scope": {"excluded": [], "rootPath": ["ROOT_ID"]},
        "type": "NATIVE_FILTER",
        "description": "",
    } for column, label, parents in definitions]


def add_markdown(layout: Layout, text: str, height: int = 5):
    node_id = layout._id("MARKDOWN")
    layout.nodes[node_id] = {
        "id": node_id,
        "type": "MARKDOWN",
        "parents": ["ROOT_ID", "GRID_ID"],
        "children": [],
        "meta": {"code": text, "height": height, "width": 12},
    }
    layout.nodes["GRID_ID"]["children"].append(node_id)


def build_export_dashboard(
    session,
    Dashboard,
    Slice,
    dataset,
    *,
    daily: bool,
):
    period_key = "dia" if daily else "mes"
    period_label = "dia" if daily else "mês"
    title = f"NeoRetail V9 — Exportação — Histórico {period_label}"
    slug = f"neoretail-v9-exportacao-historico-{period_key}"

    definitions = {
        "varejo": ("Varejo", ["rede"]),
        "produto": ("Produto", ["hierarquia_1"]),
        "geral": (
            "Geral",
            [
                "rede", "bandeira", "regiao", "uf", "cidade", "tipo_local",
                "cnpj_formatado", "cod_loja", "loja", "descricao_marca",
                "hierarquia_1", "hierarquia_2", "hierarquia_3", "item",
            ],
        ),
        "resumo": (
            "Resumo",
            ["rede", "cnpj_formatado", "item", "unidade_medida"],
        ),
    }

    charts = {}
    for key, (label, rows) in definitions.items():
        charts[key] = upsert_chart(
            session,
            Slice,
            dataset,
            f"[Exportação {period_label}] {label}",
            pivot_params(dataset, rows, daily=daily),
            "pivot_table_v2",
        )

    layout = Layout()
    add_markdown(
        layout,
        "É possível exportar até **150.000 registros por vez**. Use os filtros para reduzir o volume quando necessário.\n\n"
        "Para exportar, use o menu do visual e escolha **Download CSV**.",
        height=7,
    )
    layout.tabs(
        "GRID_ID",
        ["ROOT_ID", "GRID_ID"],
        "Exportação de dados",
        [
            ("Varejo", [[charts["varejo"]]]),
            ("Produto", [[charts["produto"]]]),
            ("Geral", [[charts["geral"]]]),
            ("Resumo", [[charts["resumo"]]]),
        ],
        height=72,
    )

    dashboard = session.query(Dashboard).filter(
        Dashboard.dashboard_title == title
    ).one_or_none()
    if dashboard is None:
        dashboard = Dashboard(dashboard_title=title, slug=slug, published=True)
        session.add(dashboard)
    dashboard.slug = slug
    dashboard.published = True
    dashboard.position_json = json.dumps(layout.nodes, ensure_ascii=False)
    dashboard.css = (
        ".dashboard-content { background: #e7f0f5 !important; } "
        ".dashboard-component-chart-holder { border-radius: 8px; background: #fff; } "
        ".dashboard-component-tabs { background: #fff; border-radius: 8px; }"
    )
    dashboard.json_metadata = json.dumps({
        "timed_refresh_immune_slices": [],
        "expanded_slices": {},
        "refresh_frequency": 0,
        "color_scheme": "supersetColors",
        "native_filter_configuration": export_filters(dataset.id, daily=daily),
        "filter_bar_orientation": "HORIZONTAL",
    }, ensure_ascii=False)
    dashboard.slices = list(charts.values())
    session.flush()
    return dashboard, charts


def main():
    app = create_app()
    with app.app_context():
        from superset import db
        from superset.connectors.sqla.models import SqlaTable
        from superset.models.core import Database
        from superset.models.dashboard import Dashboard
        from superset.models.slice import Slice

        database = db.session.query(Database).filter(
            Database.database_name == DATABASE_NAME
        ).one()
        daily = upsert_dataset(
            db.session,
            SqlaTable,
            database,
            "nr_export_daily",
            table_name="nr_export_daily",
        )
        monthly = upsert_dataset(
            db.session,
            SqlaTable,
            database,
            "nr_export_monthly",
            table_name="nr_export_monthly",
        )

        daily_dashboard, daily_charts = build_export_dashboard(
            db.session, Dashboard, Slice, daily, daily=True
        )
        monthly_dashboard, monthly_charts = build_export_dashboard(
            db.session, Dashboard, Slice, monthly, daily=False
        )
        db.session.commit()

        print(json.dumps({
            "daily": {
                "dashboard_id": daily_dashboard.id,
                "slug": daily_dashboard.slug,
                "dataset": daily.id,
                "charts": {key: chart.id for key, chart in daily_charts.items()},
            },
            "monthly": {
                "dashboard_id": monthly_dashboard.id,
                "slug": monthly_dashboard.slug,
                "dataset": monthly.id,
                "charts": {key: chart.id for key, chart in monthly_charts.items()},
            },
        }, ensure_ascii=False))


if __name__ == "__main__":
    main()
