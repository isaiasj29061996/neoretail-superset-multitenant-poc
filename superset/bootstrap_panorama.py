"""Create the NeoRetail Panorama Industria dashboard in Superset metadata.

The script creates physical-dataset metadata, charts and dashboard layout. The
serving marts are materialized before this script runs.
"""
from __future__ import annotations

import json
import uuid

from superset.app import create_app

from bootstrap_overview import HISTORY_SQL, M, metric, native_filters, upsert_dataset


DASHBOARD_TITLE = "NeoRetail V9 — Panorama Indústria"

WEEKLY_SQL = """
SELECT
  f.id_time AS data,
  f.id_customer,
  f.id_item,
  f.id_location,
  f.volume_unidade AS volume_unidades,
  f.faturamento,
  f.estoque_unidades,
  f.estoque_medio,
  f.qtd_perda_osa,
  f.qtd_problemas_osa,
  f.qtd_item_ativo_osa,
  f.qtd_itens_validos,
  f.rup,
  f.est_virtual,
  f.giro,
  f.avg_sales_price,
  f.avg_price_cost,
  f.status_item_geral::text AS tp_activity_level,
  NULL::numeric AS demanda_media,
  COALESCE(f.status_item_geral::text, 'Outros') AS activity_level,
  l.rede, l.bandeira, l.uf, l.cidade, l.tipo_local, l.loja, l.regiao,
  i.item, i.descricao_marca, i.hierarquia_1, i.hierarquia_2, i.hierarquia_3
FROM gold.fato_semanal f
LEFT JOIN gold.dim_local l
  ON l.id_customer = f.id_customer AND l.id_location = f.id_location
LEFT JOIN gold.dim_itens i
  ON i.id_customer = f.id_customer AND i.id_item = f.id_item
""".strip()

LATEST_SQL = f"""
SELECT h.*
FROM ({HISTORY_SQL}) h
WHERE h.data = (SELECT MAX(mes_ano) FROM gold.fato_historico)
""".strip()

OPPORTUNITIES_SQL = """
SELECT
  m.*,
  l.regiao,
  MAX(m.data) OVER (PARTITION BY m.id_customer, DATE_TRUNC('month', m.data)) AS month_end_data,
  MAX(m.data) OVER (PARTITION BY m.id_customer, DATE_TRUNC('week', m.data)) AS week_end_data,
  MAX(m.data) OVER (PARTITION BY m.id_customer) AS customer_latest_data
FROM gold.vw_mart_visao_industria m
LEFT JOIN gold.dim_local l
  ON l.id_customer = m.id_customer AND l.id_location = m.id_location
""".strip()

OPPORTUNITIES_LATEST_SQL = f"""
SELECT o.*
FROM ({OPPORTUNITIES_SQL}) o
WHERE o.data = o.customer_latest_data
""".strip()

P = {
    **M,
    "loss_qty": metric("Perda OSA qtd", "SUM(qtd_perda_osa)"),
    "price": metric("Preço médio", "SUM(faturamento) / NULLIF(SUM(volume_unidades), 0)"),
    "coverage": metric("Cobertura de estoque", "SUM(estoque_unidades) / NULLIF(SUM(volume_unidades) / 4.33, 0)"),
    "rup": metric("Ruptura", "100.0 * SUM(rup) / NULLIF(SUM(qtd_item_ativo_osa), 0)"),
    "isv": metric("Item sem venda", "100.0 * SUM(est_virtual) / NULLIF(SUM(qtd_item_ativo_osa), 0)"),
    "roi_annual": metric("ROI anual", "1200.0 * ((CASE WHEN SUM(faturamento) > 0 THEN SUM(faturamento) ELSE SUM(volume_unidades * avg_sales_price) END) - SUM(volume_unidades * avg_price_cost)) / NULLIF(SUM(estoque_medio * avg_price_cost), 0)"),
}

GAP_TVD = metric("TVD", "SUM(COALESCE(tvd, 0))")
GAP_IVD = metric("IVD", "SUM(COALESCE(ivd, 0))")


def sql_filter(expression):
    return {
        "clause": "WHERE",
        "comparator": "",
        "expressionType": "SQL",
        "filterOptionName": "filter_panorama_gap_period",
        "fromFormData": True,
        "sqlExpression": expression,
    }


def upsert_chart(session, Slice, dataset, title, params, viz_type="neoretail-kpi-card"):
    chart = session.query(Slice).filter(Slice.slice_name == title).one_or_none()
    if chart is None:
        chart = Slice(slice_name=title)
        session.add(chart)
    chart.datasource_type = "table"
    chart.datasource_id = dataset.id
    chart.viz_type = viz_type
    chart.params = json.dumps(params, ensure_ascii=False)
    chart.description = "Panorama da indústria NeoRetail V9 baseado no PBIX de referência."
    session.flush()
    return chart


def custom_params(dataset, title, metrics, *, grain="P1M", styles="bar|bar|line", formats="number", groupby=None, variant="panorama", row_limit=10000, time_range=None):
    if time_range is None:
        time_range = {
            "P1D": "Last 4 months",
            "P1W": "Last 12 weeks",
            "P1M": "Last 12 months",
        }.get(grain, "Last 12 months")
    return {
        "datasource": f"{dataset.id}__table", "viz_type": "neoretail-kpi-card",
        "x_axis": "data", "time_grain_sqla": grain, "time_range": time_range,
        "metrics": metrics, "row_limit": row_limit, "card_title": title,
        "card_variant": variant, "help_text": title, "metric_labels": "|".join(m["label"] for m in metrics),
        "metric_formats": formats, "metric_directions": "higher", "chart_styles": styles,
        "accent_color": "#7C4AD9", "show_tasks": False, "adhoc_filters": [], "groupby": groupby or [],
    }


def table_params(dataset, groupby, metrics, page_length=12):
    return {
        "datasource": f"{dataset.id}__table", "viz_type": "table", "query_mode": "aggregate",
        "groupby": [groupby], "metrics": metrics, "adhoc_filters": [], "time_range": "No filter",
        "row_limit": 1000, "page_length": page_length, "include_search": True,
        "server_pagination": False, "order_desc": True, "table_timestamp_format": "%d/%m/%Y",
        "percent_metrics": [], "align_pn": False, "color_pn": False, "show_cell_bars": False,
    }


class Layout:
    def __init__(self):
        self.nodes = {
            "ROOT_ID": {"id": "ROOT_ID", "type": "ROOT", "children": ["GRID_ID"]},
            "GRID_ID": {"id": "GRID_ID", "type": "GRID", "parents": ["ROOT_ID"], "children": []},
        }
        self.counter = 0

    def _id(self, prefix):
        self.counter += 1
        return f"{prefix}-{self.counter}"

    def tabs(self, parent, parents, title, entries, height=52):
        tabs_id = self._id("TABS")
        tab_ids = []
        self.nodes[tabs_id] = {"id": tabs_id, "type": "TABS", "parents": parents, "children": tab_ids, "meta": {"defaultText": title}}
        self.nodes[parent]["children"].append(tabs_id)
        for label, chart_rows in entries:
            tab_id = self._id("TAB")
            tab_ids.append(tab_id)
            self.nodes[tab_id] = {"id": tab_id, "type": "TAB", "parents": [*parents, tabs_id], "children": [], "meta": {"text": label}}
            for row_charts in chart_rows:
                self.row(tab_id, [*parents, tabs_id, tab_id], row_charts, height)
        return tabs_id

    def period_tabs(self, parent, parents, title, entries, height=52):
        """Render business views with an inner Mensal/Semanal selector."""
        outer_id = self._id("TABS")
        outer_tabs = []
        self.nodes[outer_id] = {"id": outer_id, "type": "TABS", "parents": parents, "children": outer_tabs, "meta": {"defaultText": title}}
        self.nodes[parent]["children"].append(outer_id)
        for label, periods in entries:
            tab_id = self._id("TAB")
            outer_tabs.append(tab_id)
            tab_parents = [*parents, outer_id]
            self.nodes[tab_id] = {"id": tab_id, "type": "TAB", "parents": tab_parents, "children": [], "meta": {"text": label}}
            self.tabs(tab_id, [*tab_parents, tab_id], f"Período de {label}", [
                (period.title(), [[chart]]) for period, chart in periods
            ], height)
        return outer_id

    def row(self, parent, parents, charts, height):
        row_id = self._id("ROW")
        children = []
        self.nodes[row_id] = {"id": row_id, "type": "ROW", "parents": parents, "children": children, "meta": {"background": "BACKGROUND_TRANSPARENT"}}
        self.nodes[parent]["children"].append(row_id)
        width = max(1, 12 // len(charts))
        for chart in charts:
            chart_id = f"CHART-{chart.id}"
            children.append(chart_id)
            self.nodes[chart_id] = {"id": chart_id, "type": "CHART", "parents": [*parents, row_id], "children": [], "meta": {"chartId": chart.id, "height": height, "width": width, "sliceName": chart.slice_name, "uuid": str(chart.uuid)}}


def main():
    app = create_app()
    with app.app_context():
        from superset import db
        from superset.connectors.sqla.models import SqlaTable
        from superset.models.core import Database
        from superset.models.dashboard import Dashboard
        from superset.models.slice import Slice

        database = db.session.query(Database).filter(Database.database_name == "NeoRetail Gold - PostgreSQL Local").one()
        history = upsert_dataset(db.session, SqlaTable, database, "nr_overview_history", table_name="nr_overview_history")
        weekly = upsert_dataset(db.session, SqlaTable, database, "nr_panorama_weekly", table_name="nr_panorama_weekly")
        latest = upsert_dataset(db.session, SqlaTable, database, "nr_panorama_latest", table_name="nr_panorama_latest")
        mart = upsert_dataset(db.session, SqlaTable, database, "nr_panorama_opportunities", table_name="nr_panorama_opportunities")
        opportunities = mart
        opportunities_latest = upsert_dataset(db.session, SqlaTable, database, "nr_panorama_opportunities_latest", table_name="nr_panorama_opportunities_latest")
        gap_periodic = upsert_dataset(
            db.session,
            SqlaTable,
            database,
            "nr_panorama_gap_periodic",
            table_name="nr_panorama_gap_periodic",
        )

        charts = {}
        def add(key, dataset, title, params, viz="neoretail-kpi-card"):
            charts[key] = upsert_chart(db.session, Slice, dataset, f"[Panorama] {title}", params, viz)

        sales = [P["sellout"], P["cost"], P["markup"]]
        stock = [P["stock_cost"], P["stock_qty"]]
        giro_roi = [P["roi"], P["coverage"], P["giro"]]
        osa = [P["osa"], P["rup"], P["isv"]]
        periods = (("mensal", history, "P1M"), ("semanal", weekly, "P1W"))
        for period, dataset, grain in periods:
            add(f"sales_value_{period}", dataset, f"Evolutivo de vendas — Valor {period}", custom_params(dataset, "Evolutivo de vendas", sales, grain=grain, styles="bar|bar|line", formats="currency|currency|percent"))
            add(f"stock_{period}", dataset, f"Evolutivo de estoque — Estoque {period}", custom_params(dataset, "Evolutivo de estoque", stock, grain=grain, styles="bar|bar", formats="currency|number"))
            add(f"giro_roi_{period}", dataset, f"Evolutivo de estoque — Giro e ROI {period}", custom_params(dataset, "Evolutivo de estoque", giro_roi, grain=grain, styles="bar|line|line", formats="percent|number|number"))
            add(f"osa_{period}", dataset, f"Evolutivo de estoque — OSA {period}", custom_params(dataset, "Evolutivo de estoque", osa, grain=grain, styles="line|line|line", formats="percent|percent|percent"))
        for period, grain in (("mensal", "P1M"), ("semanal", "P1W")):
            params = custom_params(
                gap_periodic,
                "Evolutivo de estoque",
                [GAP_TVD, GAP_IVD],
                grain=grain,
                styles="line|line",
                formats="currency|currency",
            )
            params["adhoc_filters"] = [sql_filter(f"period_type = '{period}'")]
            add(
                f"gap_{period}",
                gap_periodic,
                f"Evolutivo de estoque — Falta e Excesso {period}",
                params,
            )

        dimensions = (("regiao", "Região"), ("rede", "Varejo"), ("hierarquia_1", "Hierarquia de item"))
        for column, label in dimensions:
            add(f"compare_{column}", latest, f"Comparativo — {label}", custom_params(latest, label, [P["sellout"]], groupby=[column], variant="rankbars", formats="currency", row_limit=10))

        ranking_sets = {
            "Valor": [P["sellout"], P["cost"], P["markup"]],
            "Quantidade": [P["sales_qty"], P["loss_qty"], P["price"]],
            "R$ Estoque": [P["stock_cost"], P["stock_qty"], P["roi"], P["giro"]],
            "OSA": [P["osa"], P["rup"], P["isv"]],
            "Falta x Excesso": [P["tvd"], P["ivd"]],
        }
        for tab, metrics in ranking_sets.items():
            for column, label in dimensions:
                key = f"rank_{tab}_{column}"
                source = opportunities_latest if tab == "Falta x Excesso" else latest
                add(key, source, f"Ranking {tab} — {label}", table_params(source, column, metrics), "table")

        detail_metrics = [P["sales_qty"], P["sellout"], P["cost"], P["markup"], P["price"], P["stock_cost"], P["stock_qty"], P["roi"], P["roi_annual"], P["giro"], P["osa"], P["rup"], P["isv"], P["osa_loss"]]
        detail_dims = (("regiao", "Região"), ("rede", "Rede"), ("hierarquia_1", "Categoria"), ("item", "Produto"), ("activity_level", "Nível de atividade"))
        for column, label in detail_dims:
            add(f"detail_{column}", latest, f"Análise detalhada — {label}", table_params(latest, column, detail_metrics, 20), "table")

        layout = Layout()
        grid_parents = ["ROOT_ID", "GRID_ID"]
        layout.period_tabs("GRID_ID", grid_parents, "Evolutivo de vendas", [
            ("Valor", [(period, charts[f"sales_value_{period}"]) for period in ("mensal", "semanal")]),
        ], 58)
        layout.period_tabs("GRID_ID", grid_parents, "Evolutivo de estoque", [
            (section, [(period, charts[f"{key}_{period}"]) for period in ("mensal", "semanal")])
            for section, key in (("Estoque", "stock"), ("Giro x ROI", "giro_roi"), ("OSA", "osa"), ("Falta x Excesso", "gap"))
        ], 58)
        layout.row("GRID_ID", grid_parents, [charts[f"compare_{column}"] for column, _ in dimensions], 48)
        layout.tabs("GRID_ID", grid_parents, "Ranking de oportunidades", [
            (tab, [[charts[f"rank_{tab}_{column}"] for column, _ in dimensions]]) for tab in ranking_sets
        ], 48)
        layout.tabs("GRID_ID", grid_parents, "Análise detalhada", [
            (label, [[charts[f"detail_{column}"]]]) for column, label in detail_dims
        ], 55)

        dashboard = db.session.query(Dashboard).filter(Dashboard.dashboard_title == DASHBOARD_TITLE).one_or_none()
        if dashboard is None:
            dashboard = Dashboard(dashboard_title=DASHBOARD_TITLE, slug="neoretail-v9-panorama-industria", published=True)
            db.session.add(dashboard)
        dashboard.published = True
        dashboard.position_json = json.dumps(layout.nodes, ensure_ascii=False)
        dashboard.css = ".dashboard-content { background: #e7f0f5 !important; } .dashboard-component-chart-holder { border-radius: 8px; background: #fff; } .dashboard-component-chart-holder > .header { display: none !important; } .dashboard-component-tabs .dashboard-component-tabs .ant-tabs-nav-list { margin-left: auto !important; }"
        dashboard.json_metadata = json.dumps({"timed_refresh_immune_slices": [], "expanded_slices": {}, "refresh_frequency": 0, "color_scheme": "supersetColors", "native_filter_configuration": native_filters(history.id), "filter_bar_orientation": "HORIZONTAL"}, ensure_ascii=False)
        dashboard.slices = list(charts.values())
        db.session.commit()
        print(json.dumps({"dashboard_id": dashboard.id, "slug": dashboard.slug, "industry": {"id_customer": 142, "label": "AMBEV"}, "datasets": {"history": history.id, "weekly": weekly.id, "latest": latest.id, "mart": mart.id, "opportunities": opportunities.id, "opportunities_latest": opportunities_latest.id, "gap_periodic": gap_periodic.id}, "chart_count": len(charts)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
