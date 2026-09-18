"""Create/update the NeoRetail overview datasets, charts and dashboard.

Only Superset metadata is changed. Charts use physical serving marts created by
``create-superset-kpi-views.ps1``.
"""
from __future__ import annotations

import json
import uuid

from sqlalchemy import text
from superset.app import create_app


DASHBOARD_TITLE = "NeoRetail V9 — Visão geral da indústria"
HISTORY_SQL = """
SELECT
  f.mes_ano AS data,
  f.id_customer,
  f.id_item,
  f.id_location,
  f.volume_unidades,
  f.faturamento,
  f.estoque_unidades,
  f.expectativa_vendas,
  f.qtd_perda_osa,
  f.rup,
  f.est_virtual,
  f.giro,
  f.qtd_problemas_osa,
  f.qtd_item_ativo_osa,
  f.avg_sales_price,
  f.avg_price_cost,
  f.estoque_medio,
  f.demanda_media,
  f.tp_activity_level,
  CASE f.tp_activity_level
    WHEN 'F' THEN 'Fast Mover'
    WHEN 'S' THEN 'Slow Mover'
    WHEN 'US' THEN 'Ultra Slow Mover'
    WHEN 'N' THEN 'New Mover'
    ELSE COALESCE(f.tp_activity_level, 'Outros')
  END AS activity_level,
  l.rede, l.bandeira, l.uf, l.cidade, l.tipo_local, l.loja, l.regiao,
  i.item, i.descricao_marca, i.hierarquia_1, i.hierarquia_2, i.hierarquia_3,
  CONCAT_WS('|', f.id_customer::text, f.id_location, f.id_item) AS opportunity_key,
  o.qtd_problemas_osa_m0,
  o.max_tp_activity_level
FROM gold.fato_historico f
LEFT JOIN gold.dim_local l
  ON l.id_customer = f.id_customer AND l.id_location = f.id_location
LEFT JOIN gold.dim_itens i
  ON i.id_customer = f.id_customer AND i.id_item = f.id_item
LEFT JOIN (
  SELECT DISTINCT ON (id_customer, id_location, id_item)
    id_customer, id_location, id_item, qtd_problemas_osa_m0, max_tp_activity_level
  FROM gold.calculo_oportunidades
  ORDER BY id_customer, id_location, id_item, _silver_refreshed_at DESC NULLS LAST
) o ON o.id_customer = f.id_customer AND o.id_location = f.id_location AND o.id_item = f.id_item
""".strip()


def sql_filter(expression: str, name: str = "filter_recent_period") -> dict:
    return {
        "clause": "WHERE",
        "comparator": "",
        "expressionType": "SQL",
        "filterOptionName": name,
        "fromFormData": True,
        "sqlExpression": expression,
    }


def metric(label: str, expression: str) -> dict:
    return {
        "expressionType": "SQL",
        "sqlExpression": expression,
        "label": label,
        "optionName": f"metric_{uuid.uuid5(uuid.NAMESPACE_DNS, label).hex[:12]}",
    }


# Base semantic metrics retained because Panorama and other bootstraps import M.
M = {
    "tvd": metric("TVD", "SUM(tvd_simplificado)"),
    "ivd": metric("IVD", "SUM(ivd_simplificado)"),
    "tvd_critical": metric("Itens críticos TVD", "COUNT(DISTINCT CASE WHEN regra_critico = 'CRITICO' AND COALESCE(oportunidade_tvd,0) > 0 THEN opportunity_key END)"),
    "tvd_risk": metric("Itens risco TVD", "COUNT(DISTINCT CASE WHEN regra_critico = 'F' AND COALESCE(oportunidade_tvd,0) > 0 THEN opportunity_key END)"),
    "ivd_critical": metric("Itens críticos IVD", "COUNT(DISTINCT CASE WHEN regra_critico = 'CRITICO' AND COALESCE(oportunidade_ivd,0) > 0 THEN opportunity_key END)"),
    "ivd_risk": metric("Itens risco IVD", "COUNT(DISTINCT CASE WHEN regra_critico = 'F' AND COALESCE(oportunidade_ivd,0) > 0 THEN opportunity_key END)"),
    "sellout": metric("Venda sell out", "CASE WHEN SUM(faturamento) > 0 THEN SUM(faturamento) ELSE SUM(volume_unidades * avg_sales_price) END"),
    "cost": metric("Venda custo", "SUM(volume_unidades * avg_price_cost)"),
    "sales_qty": metric("Venda qtd", "SUM(volume_unidades)"),
    "stock_cost": metric("Estoque custo", "SUM(estoque_medio * avg_price_cost)"),
    "stock_qty": metric("Estoque qtd", "SUM(estoque_unidades)"),
    "giro": metric("Giro", "AVG(giro) FILTER (WHERE giro > 0)"),
    "osa": metric("OSA", "100.0 * (1 - SUM(qtd_problemas_osa) / NULLIF(SUM(qtd_item_ativo_osa), 0))"),
    "osa_loss": metric("Perda OSA", "SUM(qtd_perda_osa) * AVG(avg_sales_price)"),
    "osa_critical": metric("Itens críticos OSA", "COUNT(DISTINCT CASE WHEN qtd_problemas_osa_m0 > 0 AND max_tp_activity_level = 'F' THEN opportunity_key END)"),
    "osa_risk": metric("Itens risco OSA", "COUNT(DISTINCT CASE WHEN qtd_problemas_osa_m0 > 0 AND max_tp_activity_level = 'S' THEN opportunity_key END)"),
    "roi": metric("ROI", "100.0 * ((CASE WHEN SUM(faturamento) > 0 THEN SUM(faturamento) ELSE SUM(volume_unidades * avg_sales_price) END) - SUM(volume_unidades * avg_price_cost)) / NULLIF(SUM(estoque_medio * avg_price_cost), 0)"),
    "markup": metric("Markup", "100.0 * (CASE WHEN SUM(faturamento) > 0 THEN SUM(faturamento) ELSE SUM(volume_unidades * avg_sales_price) END) / NULLIF(SUM(volume_unidades * avg_price_cost), 0)"),
}

_OVERVIEW_SELLOUT = (
    "CASE WHEN SUM(faturamento_sum) > 0 "
    "THEN SUM(faturamento_sum) ELSE SUM(fallback_sellout_sum) END"
)
OVERVIEW_M = {
    "sellout": metric("Venda sell out", _OVERVIEW_SELLOUT),
    "cost": metric("Venda custo", "SUM(sales_cost_sum)"),
    "sales_qty": metric("Venda qtd", "SUM(sales_qty_sum)"),
    "stock_cost": metric("Estoque custo", "SUM(stock_cost_sum)"),
    "stock_qty": metric("Estoque qtd", "SUM(stock_qty_sum)"),
    "giro": metric("Giro", "SUM(giro_sum_positive) / NULLIF(SUM(giro_count_positive), 0)"),
    "osa": metric("OSA", "100.0 * (1 - SUM(osa_problem_sum) / NULLIF(SUM(osa_active_sum), 0))"),
    "osa_loss": metric(
        "Perda OSA",
        "SUM(osa_loss_qty_sum) * SUM(avg_sales_price_sum) / NULLIF(SUM(avg_sales_price_count), 0)",
    ),
    "osa_critical": metric("Itens críticos OSA", "SUM(osa_critical_count)"),
    "osa_risk": metric("Itens risco OSA", "SUM(osa_risk_count)"),
    "roi": metric(
        "ROI",
        f"100.0 * (({_OVERVIEW_SELLOUT}) - SUM(sales_cost_sum)) / NULLIF(SUM(stock_cost_sum), 0)",
    ),
    "markup": metric(
        "Markup",
        f"100.0 * ({_OVERVIEW_SELLOUT}) / NULLIF(SUM(sales_cost_sum), 0)",
    ),
}

TVD_DAILY = {
    "tvd": metric("TVD", "SUM(tvd)"),
    "critical": metric("Itens críticos TVD", "SUM(itens_criticos_tvd)"),
    "risk": metric("Itens risco TVD", "SUM(itens_risco_tvd)"),
}
IVD_DAILY = {
    "ivd": metric("IVD", "SUM(ivd)"),
    "critical": metric("Itens críticos IVD", "SUM(itens_criticos_ivd)"),
    "risk": metric("Itens risco IVD", "SUM(itens_risco_ivd)"),
}

HEADLINE_FILTER_COLUMNS = (
    "rede", "bandeira", "uf", "cidade", "tipo_local", "loja", "regiao",
    "deposito", "tp_activity_level", "item", "descricao_marca",
    "hierarquia_1", "hierarquia_2", "hierarquia_3", "hierarquia_4",
    "unidade_medida",
)


def headline_semantic_sql(detail_table: str, summary_table: str) -> str:
    """Use daily totals by default and retain detail for dimensional filters."""
    checks = " or ".join(
        f"get_filters('{column}')" for column in HEADLINE_FILTER_COLUMNS
    )
    return (
        f"{{% set has_dimension_filter = {checks} %}}\n"
        "{% if has_dimension_filter %}\n"
        f"SELECT * FROM gold.{detail_table}\n"
        "{% else %}\n"
        f"SELECT * FROM gold.{summary_table}\n"
        "{% endif %}"
    )


def upsert_dataset(session, model, database, name, *, table_name=None, sql=None):
    dataset = session.query(model).filter(model.table_name == name).one_or_none()
    needs_metadata = dataset is None
    if dataset is None:
        dataset = model(table_name=name, schema="gold", database=database)
        session.add(dataset)
    else:
        needs_metadata = (
            dataset.sql != sql
            or (table_name is not None and dataset.table_name != table_name)
            or not dataset.columns
        )
    dataset.database = database
    dataset.schema = "gold"
    dataset.sql = sql
    if table_name:
        dataset.table_name = table_name
    session.flush()
    if needs_metadata:
        dataset.fetch_metadata()
        session.flush()
    return dataset


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


def upsert_chart(session, Slice, dataset, title, params):
    chart = session.query(Slice).filter(Slice.slice_name == title).one_or_none()
    if chart is None:
        chart = Slice(slice_name=title)
        session.add(chart)
    chart.datasource_type = "table"
    chart.datasource_id = dataset.id
    chart.viz_type = "neoretail-kpi-card"
    chart.params = json.dumps(params, ensure_ascii=False)
    chart.description = "Visão geral NeoRetail V9 baseada no PBIX de referência."
    session.flush()
    return chart


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


def _filter_definitions():
    return [
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
            "multiSelect": True,
            "searchAllOptions": True,
            "inverseSelection": False,
        },
        "name": label,
        "filterType": "filter_select",
        "targets": targets_by_column(column),
        "defaultDataMask": {"extraFormData": {}, "filterState": {}, "ownState": {}},
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
            "datasetId": filter_dataset_id or ids[0],
            "column": {"name": column},
        }]
    )


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
        tvd_daily = upsert_dataset(
            db.session, SqlaTable, database, "nr_tvd_daily_interactive",
            sql=headline_semantic_sql("nr_tvd_daily", "nr_tvd_daily_summary"),
        )
        ivd_daily = upsert_dataset(
            db.session, SqlaTable, database, "nr_ivd_daily_interactive",
            sql=headline_semantic_sql("nr_ivd_daily", "nr_ivd_daily_summary"),
        )
        summary = upsert_dataset(
            db.session, SqlaTable, database, "nr_overview_summary", table_name="nr_overview_summary"
        )
        filter_options = upsert_dataset(
            db.session, SqlaTable, database, "nr_filter_options", table_name="nr_filter_options"
        )
        with database.get_sqla_engine() as engine:
            with engine.connect() as connection:
                tvd_max_date = connection.execute(
                    text("SELECT MAX(data) FROM gold.nr_tvd_daily")
                ).scalar_one()
                ivd_max_date = connection.execute(
                    text("SELECT MAX(data) FROM gold.nr_ivd_daily")
                ).scalar_one()

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
                task_labels="itens críticos|itens com risco", time_grain_sqla="P1D",
                adhoc_filters=tvd_recent,
            )),
            (ivd_daily, "IVD - Excesso", chart_params(
                ivd_daily, "IVD - Excesso", "area", [IVD_DAILY["ivd"]],
                show_tasks=True, critical_metric=IVD_DAILY["critical"], risk_metric=IVD_DAILY["risk"],
                metric_formats="currency", metric_directions="lower",
                task_labels="itens críticos|itens com risco", time_grain_sqla="P1D",
                adhoc_filters=ivd_recent,
            )),
            (summary, "Giro", chart_params(summary, "Giro", "bars", [OVERVIEW_M["giro"]], groupby=["activity_level"], metric_formats="number", metric_directions="lower")),
            (summary, "OSA", chart_params(summary, "OSA", "osa", [OVERVIEW_M["osa"], OVERVIEW_M["osa_loss"]], show_tasks=True, critical_metric=OVERVIEW_M["osa_critical"], risk_metric=OVERVIEW_M["osa_risk"], metric_labels="% Numérico|Perda R$", metric_formats="percent|currency", metric_directions="higher|lower", task_labels="itens críticos|itens em risco")),
            (summary, "Vendas", chart_params(summary, "Vendas", "multi", [OVERVIEW_M["sellout"], OVERVIEW_M["cost"], OVERVIEW_M["sales_qty"]], metric_labels="Venda sell out|Venda custo|Venda qtd", metric_formats="currency|currency|number", metric_directions="higher|lower|higher")),
            (summary, "Estoque", chart_params(summary, "Estoque", "multi", [OVERVIEW_M["stock_cost"], OVERVIEW_M["stock_qty"]], metric_labels="Estoque custo|Estoque qtd", metric_formats="currency|number", metric_directions="lower|lower")),
            (summary, "ROI", chart_params(summary, "ROI", "bars", [OVERVIEW_M["roi"]], groupby=["activity_level"], metric_formats="percent", metric_directions="higher")),
            (summary, "MARKUP", chart_params(summary, "MARKUP", "bars", [OVERVIEW_M["markup"]], groupby=["activity_level"], metric_formats="percent", metric_directions="higher")),
        ]
        charts = [upsert_chart(db.session, Slice, dataset, title, params) for dataset, title, params in specs]

        dashboard = db.session.query(Dashboard).filter(
            Dashboard.dashboard_title == DASHBOARD_TITLE
        ).one_or_none()
        if dashboard is None:
            dashboard = Dashboard(
                dashboard_title=DASHBOARD_TITLE,
                slug="neoretail-v9-visao-geral-industria",
                published=True,
            )
            db.session.add(dashboard)
        dashboard.published = True
        dashboard.position_json = position_json(charts)
        dashboard.css = (
            ".dashboard-content { background: #e7f0f5 !important; } "
            ".dashboard-component-chart-holder { border-radius: 8px; } "
            ".dashboard-component-chart-holder > .header { display: none !important; }"
        )
        dashboard.json_metadata = json.dumps({
            "timed_refresh_immune_slices": [],
            "expanded_slices": {},
            "refresh_frequency": 0,
            "color_scheme": "supersetColors",
            "native_filter_configuration": overview_native_filters(
                [summary.id, tvd_daily.id, ivd_daily.id], filter_options.id
            ),
            "filter_bar_orientation": "HORIZONTAL",
        })
        dashboard.slices = charts
        db.session.commit()
        print(json.dumps({
            "dashboard_id": dashboard.id,
            "slug": dashboard.slug,
            "datasets": {"summary": summary.id, "tvd_daily": tvd_daily.id, "ivd_daily": ivd_daily.id},
            "charts": {chart.slice_name: chart.id for chart in charts},
        }, ensure_ascii=False))


if __name__ == "__main__":
    main()
