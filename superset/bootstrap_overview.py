"""Create/update the NeoRetail overview datasets, charts and dashboard.

Only Superset metadata is changed. Charts use physical serving marts created by
``create-superset-kpi-views.ps1``.
"""
from __future__ import annotations

import json
import uuid

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


def metric(label: str, expression: str) -> dict:
    return {"expressionType": "SQL", "sqlExpression": expression, "label": label, "optionName": f"metric_{uuid.uuid5(uuid.NAMESPACE_DNS, label).hex[:12]}"}


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

TVD_DAILY = {
    "tvd": metric("TVD", "SUM(tvd)"),
    "critical": metric("Itens críticos TVD", "SUM(itens_criticos_tvd)"),
    "risk": metric("Itens risco TVD", "SUM(itens_risco_tvd)"),
}


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
        "datasource": f"{dataset.id}__table", "viz_type": "neoretail-kpi-card",
        "x_axis": "data", "time_grain_sqla": "P1M", "time_range": "No filter",
        "metrics": metrics, "row_limit": 10000, "card_title": title,
        "card_variant": variant, "help_text": extra.pop("help_text", title),
        "metric_labels": extra.pop("metric_labels", "|".join(m["label"] for m in metrics)),
        "metric_formats": extra.pop("metric_formats", "number"),
        "metric_directions": extra.pop("metric_directions", "higher"),
        "accent_color": "#7C4AD9", "analysis_url": "", "show_tasks": extra.pop("show_tasks", False),
        "adhoc_filters": [], "groupby": extra.pop("groupby", []), **extra,
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
    grid = {"GRID_ID": {"id": "GRID_ID", "type": "GRID", "parents": ["ROOT_ID"], "children": ["ROW-1", "ROW-2"]}}
    layout = {**root, **grid}
    for row_index, row_charts in enumerate((charts[:4], charts[4:]), 1):
        row_id = f"ROW-{row_index}"
        children = []
        for chart in row_charts:
            chart_id = f"CHART-{chart.id}"
            children.append(chart_id)
            layout[chart_id] = {"id": chart_id, "type": "CHART", "parents": ["ROOT_ID", "GRID_ID", row_id], "children": [], "meta": {"chartId": chart.id, "height": 50, "width": 3, "sliceName": chart.slice_name, "uuid": str(chart.uuid)}}
        layout[row_id] = {"id": row_id, "type": "ROW", "parents": ["ROOT_ID", "GRID_ID"], "children": children, "meta": {"background": "BACKGROUND_TRANSPARENT"}}
    return json.dumps(layout)


def native_filters(dataset_id):
    definitions = [
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
    ids = {column: f"NATIVE_FILTER-neoretail-{column}" for column, _, _ in definitions}
    return [{
        "id": ids[column], "controlValues": {"enableEmptyFilter": False, "defaultToFirstItem": False, "creatable": False, "multiSelect": True, "searchAllOptions": True, "inverseSelection": False},
        "name": label, "filterType": "filter_select", "targets": [{"datasetId": dataset_id, "column": {"name": column}}],
        "defaultDataMask": {"extraFormData": {}, "filterState": {}, "ownState": {}},
        "cascadeParentIds": [ids[parent] for parent in parents], "scope": {"excluded": [], "rootPath": ["ROOT_ID"]},
        "type": "NATIVE_FILTER", "description": "",
    } for column, label, parents in definitions]


def main():
    app = create_app()
    with app.app_context():
        from superset import db
        from superset.connectors.sqla.models import SqlaTable
        from superset.models.core import Database
        from superset.models.dashboard import Dashboard
        from superset.models.slice import Slice

        database = db.session.query(Database).filter(Database.database_name == "NeoRetail Gold - PostgreSQL Local").one()
        mart = upsert_dataset(db.session, SqlaTable, database, "nr_panorama_opportunities", table_name="nr_panorama_opportunities")
        tvd_daily = upsert_dataset(db.session, SqlaTable, database, "nr_tvd_daily", table_name="nr_tvd_daily")
        history = upsert_dataset(db.session, SqlaTable, database, "nr_overview_history", table_name="nr_overview_history")
        specs = [
            (tvd_daily, "TVD - Pré-ruptura", chart_params(tvd_daily, "TVD - Pré-ruptura", "area", [TVD_DAILY["tvd"]], show_tasks=True, critical_metric=TVD_DAILY["critical"], risk_metric=TVD_DAILY["risk"], metric_formats="currency", metric_directions="lower", task_labels="itens críticos|itens com risco", time_grain_sqla="P1D")),
            (mart, "IVD - Excesso", chart_params(mart, "IVD - Excesso", "area", [M["ivd"]], show_tasks=True, critical_metric=M["ivd_critical"], risk_metric=M["ivd_risk"], metric_formats="currency", metric_directions="lower", task_labels="itens críticos|itens com risco", time_grain_sqla="P1D")),
            (history, "Giro", chart_params(history, "Giro", "bars", [M["giro"]], groupby=["activity_level"], metric_formats="number", metric_directions="lower")),
            (history, "OSA", chart_params(history, "OSA", "osa", [M["osa"], M["osa_loss"]], show_tasks=True, critical_metric=M["osa_critical"], risk_metric=M["osa_risk"], metric_labels="% Numérico|Perda R$", metric_formats="percent|currency", metric_directions="higher|lower", task_labels="itens críticos|itens em risco")),
            (history, "Vendas", chart_params(history, "Vendas", "multi", [M["sellout"], M["cost"], M["sales_qty"]], metric_labels="Venda sell out|Venda custo|Venda qtd", metric_formats="currency|currency|number", metric_directions="higher|lower|higher")),
            (history, "Estoque", chart_params(history, "Estoque", "multi", [M["stock_cost"], M["stock_qty"]], metric_labels="Estoque custo|Estoque qtd", metric_formats="currency|number", metric_directions="lower|lower")),
            (history, "ROI", chart_params(history, "ROI", "bars", [M["roi"]], groupby=["activity_level"], metric_formats="percent", metric_directions="higher")),
            (history, "MARKUP", chart_params(history, "MARKUP", "bars", [M["markup"]], groupby=["activity_level"], metric_formats="percent", metric_directions="higher")),
        ]
        charts = [upsert_chart(db.session, Slice, dataset, title, params) for dataset, title, params in specs]
        dashboard = db.session.query(Dashboard).filter(Dashboard.dashboard_title == DASHBOARD_TITLE).one_or_none()
        if dashboard is None:
            dashboard = Dashboard(dashboard_title=DASHBOARD_TITLE, slug="neoretail-v9-visao-geral-industria", published=True)
            db.session.add(dashboard)
        dashboard.published = True
        dashboard.position_json = position_json(charts)
        dashboard.css = ".dashboard-content { background: #e7f0f5 !important; } .dashboard-component-chart-holder { border-radius: 8px; } .dashboard-component-chart-holder > .header { display: none !important; }"
        dashboard.json_metadata = json.dumps({"timed_refresh_immune_slices": [], "expanded_slices": {}, "refresh_frequency": 0, "color_scheme": "supersetColors", "native_filter_configuration": native_filters(history.id), "filter_bar_orientation": "HORIZONTAL"})
        dashboard.slices = charts
        db.session.commit()
        print(json.dumps({"dashboard_id": dashboard.id, "slug": dashboard.slug, "datasets": [mart.id, tvd_daily.id, history.id], "charts": {c.slice_name: c.id for c in charts}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
