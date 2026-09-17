"""Create the NeoRetail stock-optimization task dashboard in Superset.

Only Superset metadata is changed. The Analytics database is queried through
physical serving marts; tenant isolation is enforced by the embedded RLS layer.
"""
from __future__ import annotations

import json

from sqlalchemy import text
from superset.app import create_app

from bootstrap_overview import metric, upsert_dataset
from bootstrap_panorama import Layout, custom_params, upsert_chart


DASHBOARD_TITLE = "NeoRetail V9 — Tarefas de Otimização — Estoque"

HISTORY_SQL = """
SELECT
  m.*,
  m.loja AS deposito,
  'unidade'::text AS unidade_medida
FROM gold.vw_mart_visao_industria m
""".strip()

TASKS_SQL = """
WITH last_dates AS (
  SELECT id_customer, MAX(id_time)::date AS data
  FROM gold.fato_ivd_tvd
  GROUP BY id_customer
)
SELECT
  c.*,
  d.data,
  l.rede,
  l.bandeira,
  l.uf,
  l.cidade,
  l.tipo_local,
  l.loja,
  l.regiao,
  COALESCE(l.loja, l.nome_da_loja, c.id_location) AS deposito,
  c.max_tp_activity_level AS tp_activity_level,
  i.item,
  i.descricao_marca,
  i.hierarquia_1,
  i.hierarquia_2,
  i.hierarquia_3,
  'unidade'::text AS unidade_medida
FROM gold.calculo_oportunidades c
JOIN last_dates d ON d.id_customer = c.id_customer
LEFT JOIN gold.dim_local l
  ON l.id_customer = c.id_customer AND l.id_location = c.id_location
LEFT JOIN gold.dim_itens i
  ON i.id_customer = c.id_customer AND i.id_item = c.id_item
""".strip()

TVD = metric("TVD - Pré-Ruptura", "SUM(COALESCE(tvd, 0))")
IVD = metric("IVD - Excesso de estoque", "SUM(COALESCE(ivd, 0))")
TVD_HISTORY = metric("TVD - Pré-Ruptura", "SUM(COALESCE(tvd_simplificado, 0))")
TVD_DAILY = metric("TVD - Pré-Ruptura", "SUM(COALESCE(tvd, 0))")
IVD_HISTORY = metric("IVD - Excesso de estoque", "SUM(COALESCE(ivd_simplificado, 0))")
STOCK = metric("Qtd Estoque atual", "SUM(COALESCE(estoque_unidades, 0))")
STOCK_MIN = metric("Qtd Estoque mínimo", "SUM(COALESCE(estoque_min, 0))")
STOCK_MAX = metric("Qtd Estoque máximo", "SUM(COALESCE(estoque_max, 0))")

# Regras de negócio já definidas para as tabelas de incidência:
# - excesso = estoque atual - estoque máximo, preservando resultados negativos;
# - falta = estoque mínimo quando estoque atual <= 0; caso contrário,
#   estoque mínimo - estoque atual, também sem truncar resultados negativos.
ITEMS_EXCESS = metric(
    "Qtd itens em excesso",
    "SUM(COALESCE(estoque_unidades, 0) - COALESCE(estoque_max, 0))",
)
ITEMS_MISSING = metric(
    "Qtd itens em falta",
    "SUM(CASE WHEN COALESCE(estoque_unidades, 0) <= 0 "
    "THEN COALESCE(estoque_min, 0) "
    "ELSE COALESCE(estoque_min, 0) - COALESCE(estoque_unidades, 0) END)",
)


def sql_filter(expression):
    return {
        "clause": "WHERE", "comparator": "", "expressionType": "SQL",
        "filterOptionName": "filter_stock_tasks", "fromFormData": True,
        "sqlExpression": expression,
    }


def detail_table_params(dataset, metrics, expression):
    return {
        "datasource": f"{dataset.id}__table", "viz_type": "table",
        "query_mode": "aggregate", "groupby": ["rede", "deposito", "item"],
        "metrics": metrics, "adhoc_filters": [sql_filter(expression)],
        "time_range": "No filter", "row_limit": 1000, "page_length": 12,
        "include_search": True, "server_pagination": False,
        "order_desc": True, "table_timestamp_format": "%d/%m/%Y",
        "percent_metrics": [], "align_pn": False, "color_pn": False,
        "show_cell_bars": False,
    }


def task_filters(dataset_id):
    definitions = [
        ("rede", "Rede", []),
        ("bandeira", "Bandeira", ["rede"]),
        ("uf", "UF", []),
        ("cidade", "Cidade", ["uf"]),
        ("tipo_local", "Tipo local", []),
        ("loja", "Loja", ["tipo_local"]),
        ("tp_activity_level", "Nível de atividade", []),
        ("descricao_marca", "Descrição marca", []),
        ("hierarquia_1", "Hierarquia 1", ["descricao_marca"]),
        ("hierarquia_2", "Hierarquia 2", ["hierarquia_1"]),
        ("hierarquia_3", "Hierarquia 3", ["hierarquia_2"]),
        ("item", "Item", ["hierarquia_3"]),
        ("unidade_medida", "Unidade de medida", []),
    ]
    ids = {column: f"NATIVE_FILTER-stock-{column}" for column, _, _ in definitions}
    return [{
        "id": ids[column],
        "controlValues": {
            "enableEmptyFilter": False, "defaultToFirstItem": False,
            "creatable": False, "multiSelect": True,
            "searchAllOptions": True, "inverseSelection": False,
        },
        "name": label, "filterType": "filter_select",
        "targets": [{"datasetId": dataset_id, "column": {"name": column}}],
        "defaultDataMask": {"extraFormData": {}, "filterState": {}, "ownState": {}},
        "cascadeParentIds": [ids[parent] for parent in parents],
        "scope": {"excluded": [], "rootPath": ["ROOT_ID"]},
        "type": "NATIVE_FILTER", "description": "",
    } for column, label, parents in definitions]


def add_markdown(layout, parent, parents, code, height=5):
    node_id = layout._id("MARKDOWN")
    layout.nodes[node_id] = {
        "id": node_id, "type": "MARKDOWN", "parents": parents, "children": [],
        "meta": {"code": code, "height": height, "width": 12},
    }
    layout.nodes[parent]["children"].append(node_id)


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
        with database.get_sqla_engine() as engine:
            with engine.connect() as connection:
                last_date = connection.execute(text(
                    "SELECT MAX(id_time)::date FROM gold.fato_ivd_tvd"
                )).scalar_one()

        history = upsert_dataset(
            db.session, SqlaTable, database, "nr_panorama_opportunities", table_name="nr_panorama_opportunities"
        )
        tvd_daily = upsert_dataset(
            db.session, SqlaTable, database, "nr_tvd_daily", table_name="nr_tvd_daily"
        )
        tasks = upsert_dataset(
            db.session, SqlaTable, database, "nr_stock_tasks", table_name="nr_stock_tasks"
        )

        charts = {}

        def add(key, dataset, title, params, viz="neoretail-kpi-card"):
            charts[key] = upsert_chart(
                db.session, Slice, dataset, f"[Tarefas Estoque] {title}", params, viz
            )

        tvd_card = custom_params(
            tvd_daily, "TVD - Pré-ruptura", [TVD_DAILY], grain="P1D",
            formats="currency", variant="headlinearea",
        )
        tvd_card["accent_color"] = "#7C43DF"
        add("tvd_card", tvd_daily, "TVD - Pré-ruptura", tvd_card)

        ivd_card = custom_params(
            history, "IVD - Excesso de estoque", [IVD_HISTORY], grain="P1D",
            formats="currency", variant="headlinearea",
        )
        ivd_card["accent_color"] = "#C91878"
        add("ivd_card", history, "IVD - Excesso de estoque", ivd_card)

        for dimension, label in (("rede", "Redes"), ("item", "Itens")):
            pre = custom_params(
                tasks, f"Ranking de {label} — Pré-ruptura", [TVD],
                groupby=[dimension], variant="verticalbars", formats="number", row_limit=10,
            )
            pre["adhoc_filters"] = [sql_filter("COALESCE(tvd, 0) > 0")]
            add(f"pre_{dimension}", tasks, f"Ranking de {label} — Pré-ruptura", pre)

            excess = custom_params(
                tasks, f"Ranking de {label} — Excesso", [IVD],
                groupby=[dimension], variant="verticalbars", formats="number", row_limit=10,
            )
            excess["adhoc_filters"] = [sql_filter("COALESCE(ivd, 0) > 0")]
            add(f"excess_{dimension}", tasks, f"Ranking de {label} — Excesso", excess)

            combined = custom_params(
                tasks, f"{label} com maiores incidências", [TVD, IVD],
                groupby=[dimension], variant="stackedrank", formats="number|number", row_limit=10,
            )
            combined["metric_labels"] = "TVD - Pré-Ruptura|IVD - Excesso de estoque"
            combined["adhoc_filters"] = [sql_filter("COALESCE(tvd, 0) > 0 OR COALESCE(ivd, 0) > 0")]
            add(f"combined_{dimension}", tasks, f"{label} com maiores incidências", combined)

        add(
            "table_excess", tasks, "Incidência de Excesso",
            detail_table_params(
                tasks,
                [ITEMS_EXCESS, STOCK, STOCK_MAX],
                "COALESCE(ivd, 0) > 0",
            ),
            "table",
        )
        add(
            "table_pre", tasks, "Incidência de Pré-ruptura",
            detail_table_params(
                tasks,
                [ITEMS_MISSING, STOCK, STOCK_MIN],
                "COALESCE(tvd, 0) > 0",
            ),
            "table",
        )

        layout = Layout()
        parents = ["ROOT_ID", "GRID_ID"]
        add_markdown(
            layout, "GRID_ID", parents,
            f"**Data do último movimento:** {last_date.strftime('%d/%m/%Y')} &nbsp;&nbsp;&nbsp; `VERSÃO BETA`",
            height=4,
        )
        layout.row("GRID_ID", parents, [charts["tvd_card"], charts["ivd_card"]], 34)
        add_markdown(
            layout, "GRID_ID", parents,
            "## Otimização de estoque - Incidências de excesso e pré-ruptura", height=6,
        )
        layout.tabs("GRID_ID", parents, "Análise de otimização", [
            ("Pré-ruptura", [[charts["pre_rede"], charts["pre_item"]]]),
            ("Excesso", [[charts["excess_rede"], charts["excess_item"]]]),
            ("Otimização de estoque", [[charts["combined_rede"], charts["combined_item"]]]),
        ], height=50)
        layout.row("GRID_ID", parents, [charts["table_excess"], charts["table_pre"]], 54)

        dashboard = db.session.query(Dashboard).filter(
            Dashboard.dashboard_title == DASHBOARD_TITLE
        ).one_or_none()
        if dashboard is None:
            dashboard = Dashboard(
                dashboard_title=DASHBOARD_TITLE,
                slug="neoretail-v9-tarefas-otimizacao-estoque",
                published=True,
            )
            db.session.add(dashboard)
        dashboard.published = True
        dashboard.position_json = json.dumps(layout.nodes, ensure_ascii=False)
        dashboard.css = (
            ".dashboard-content { background: #e7f0f5 !important; } "
            ".dashboard-component-chart-holder { border-radius: 8px; background: #fff; } "
            ".dashboard-component-chart-holder > .header { display: none !important; } "
            ".dashboard-component-tabs { background: #fff; border-radius: 8px; }"
        )
        dashboard.json_metadata = json.dumps({
            "timed_refresh_immune_slices": [], "expanded_slices": {},
            "refresh_frequency": 0, "color_scheme": "supersetColors",
            "native_filter_configuration": task_filters(tasks.id),
            "filter_bar_orientation": "HORIZONTAL",
        }, ensure_ascii=False)
        dashboard.slices = list(charts.values())
        db.session.commit()
        print(json.dumps({
            "dashboard_id": dashboard.id, "slug": dashboard.slug,
            "last_movement": last_date.isoformat(),
            "datasets": {"history": history.id, "tvd_daily": tvd_daily.id, "tasks": tasks.id},
            "charts": {key: chart.id for key, chart in charts.items()},
        }, ensure_ascii=False))


if __name__ == "__main__":
    main()
