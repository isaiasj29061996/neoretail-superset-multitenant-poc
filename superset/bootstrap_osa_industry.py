"""Create the NeoRetail OSA Industria dashboard (Valor view only).

Only Superset metadata is changed. All analytics sources are virtual/read-only.
"""
from __future__ import annotations

import json
from datetime import date

from sqlalchemy import text

from superset.app import create_app

from bootstrap_overview import HISTORY_SQL, M, metric, native_filters, upsert_dataset
from bootstrap_panorama import Layout, custom_params, table_params, upsert_chart


DASHBOARD_TITLE = "NeoRetail V9 — OSA Indústria"

CAUSE_SQL = """
SELECT
  f.*,
  COALESCE(f.qtd_perda_osa * NULLIF(f.preco_medio, 0), 0) AS perda_osa_valor,
  CASE
    WHEN LOWER(COALESCE(f.motivo_osa, '')) LIKE '%performance%' THEN 'Falta de Performance'
    WHEN LOWER(COALESCE(f.motivo_osa, '')) LIKE '%exposi%' THEN 'Falta de Exposição'
    WHEN LOWER(COALESCE(f.motivo_osa, '')) LIKE '%virtual%' THEN 'Estoque Virtual'
    WHEN LOWER(COALESCE(f.motivo_osa, '')) LIKE '%ruptura%' THEN 'Ruptura na loja'
    ELSE COALESCE(f.motivo_osa, 'Não identificado')
  END AS motivo,
  COALESCE(f.causa_osa, 'Não identificado') AS causa,
  l.rede, l.bandeira, l.uf, l.cidade, l.tipo_local, l.loja, l.regiao,
  i.item, i.descricao_marca, i.hierarquia_1, i.hierarquia_2, i.hierarquia_3
FROM gold.fato_mensal_causa_osa f
LEFT JOIN gold.dim_local l
  ON l.id_customer = f.id_customer AND l.id_location = f.id_location
LEFT JOIN gold.dim_itens i
  ON i.id_customer = f.id_customer AND i.id_item = f.id_item
WHERE f.id_customer = 259
""".strip()

LOSS_VALUE = metric("Perda R$ OSA", "SUM(COALESCE(qtd_perda_osa * NULLIF(preco_medio, 0), 0))")
LOSS_PERCENT = metric("% Perda", "100.0 * SUM(qtd_perda_osa) * AVG(avg_sales_price) / NULLIF(CASE WHEN SUM(faturamento) > 0 THEN SUM(faturamento) ELSE SUM(volume_unidades * avg_sales_price) END, 0)")
PROBLEM_COUNT = metric("Qtd Problema OSA", "SUM(qtd_problemas_osa)")
CAUSE_OSA = metric("% OSA Numérico", "100.0 * (1 - SUM(qtd_problemas_osa) / NULLIF(SUM(qtd_itens_ativos), 0))")


def motive_percent(label):
    patterns = {"Estoque Virtual": "%virtual%", "Falta de Exposição": "%exposi%", "Falta de Performance": "%performance%", "Ruptura na loja": "%ruptura%"}
    pattern = patterns[label]
    value = "COALESCE(qtd_perda_osa * NULLIF(preco_medio, 0), 0)"
    return metric(label, f"100.0 * SUM(CASE WHEN LOWER(COALESCE(motivo_osa, '')) LIKE '{pattern}' THEN {value} ELSE 0 END) / NULLIF(SUM({value}), 0)")


def main():
    app = create_app()
    with app.app_context():
        from superset import db
        from superset.connectors.sqla.models import SqlaTable
        from superset.models.core import Database
        from superset.models.dashboard import Dashboard
        from superset.models.slice import Slice

        database = db.session.query(Database).filter(Database.database_name == "NeoRetail Gold - PostgreSQL Local").one()
        with database.get_sqla_engine() as engine:
            with engine.connect() as connection:
                latest_cause_date = connection.execute(text("SELECT MAX(data) FROM gold.fato_mensal_causa_osa")).scalar_one()
        next_month = date(latest_cause_date.year + (latest_cause_date.month == 12), 1 if latest_cause_date.month == 12 else latest_cause_date.month + 1, 1)
        latest_cause_range = f"{latest_cause_date.isoformat()} : {next_month.isoformat()}"
        history = upsert_dataset(db.session, SqlaTable, database, "nr_overview_history", sql=HISTORY_SQL)
        causes = upsert_dataset(db.session, SqlaTable, database, "nr_osa_industry_causes_259", sql=CAUSE_SQL)
        latest = upsert_dataset(db.session, SqlaTable, database, "nr_panorama_latest", sql=f"SELECT h.* FROM ({HISTORY_SQL}) h WHERE h.data = (SELECT MAX(mes_ano) FROM gold.fato_historico)")

        charts = {}
        def add(key, dataset, title, params, viz="neoretail-kpi-card"):
            charts[key] = upsert_chart(db.session, Slice, dataset, f"[OSA Indústria] {title}", params, viz)

        top_metrics = [M["osa"], M["sellout"], M["osa_loss"], LOSS_PERCENT]
        top = custom_params(history, "Visão geral mensal", top_metrics, grain="P1M", styles="line|bar|hidden|line", formats="percent|currency|currency|percent")
        top.update({"summary_count": "3", "metric_labels": "%OSA|Sell Out Venda|Perda R$ OSA|% Perda", "row_limit": 10000})
        add("overview", history, "Visão geral mensal — Valor", top)

        motive_metrics = [motive_percent(label) for label in ("Estoque Virtual", "Falta de Exposição", "Falta de Performance", "Ruptura na loja")]
        stacked = custom_params(causes, "Perdas por motivo", motive_metrics, grain="P1M", styles="bar|bar|bar|bar", formats="percent|percent|percent|percent", variant="stacked")
        add("stacked", causes, "Visão geral mensal — Perdas", stacked)

        motive = custom_params(causes, "Perda OSA", [LOSS_VALUE], groupby=["motivo_osa"], variant="verticalbars", formats="currency", row_limit=10)
        cause = custom_params(causes, "Perda por causa OSA", [LOSS_VALUE], groupby=["causa_osa"], variant="verticalbars", formats="currency", row_limit=15)
        motive["time_range"] = latest_cause_range
        cause["time_range"] = latest_cause_range
        add("motive", causes, "Perda OSA por motivo", motive)
        add("cause", causes, "Perda por causa OSA", cause)

        for column, label in (("regiao", "Região"), ("rede", "Varejo"), ("hierarquia_1", "Hierarquia de item")):
            add(f"table_{column}", latest, label, table_params(latest, column, [M["osa_loss"], PROBLEM_COUNT, M["osa"]]), "table")

        layout = Layout()
        parents = ["ROOT_ID", "GRID_ID"]
        layout.tabs("GRID_ID", parents, "VisÃ£o geral mensal", [
            ("Valor", [[charts["overview"]]]),
            ("Perdas", [[charts["stacked"]]]),
        ], height=58)
        layout.row("GRID_ID", parents, [charts["motive"]], 44)
        layout.row("GRID_ID", parents, [charts["cause"]], 52)
        layout.row("GRID_ID", parents, [charts["table_regiao"], charts["table_rede"], charts["table_hierarquia_1"]], 48)

        dashboard = db.session.query(Dashboard).filter(Dashboard.dashboard_title == DASHBOARD_TITLE).one_or_none()
        if dashboard is None:
            dashboard = Dashboard(dashboard_title=DASHBOARD_TITLE, slug="neoretail-v9-osa-industria", published=True)
            db.session.add(dashboard)
        dashboard.published = True
        dashboard.position_json = json.dumps(layout.nodes, ensure_ascii=False)
        dashboard.css = ".dashboard-content { background: #e7f0f5 !important; } .dashboard-component-chart-holder { border-radius: 8px; background: #fff; }"
        dashboard.json_metadata = json.dumps({"timed_refresh_immune_slices": [], "expanded_slices": {}, "refresh_frequency": 0, "color_scheme": "supersetColors", "native_filter_configuration": native_filters(history.id), "filter_bar_orientation": "HORIZONTAL"}, ensure_ascii=False)
        dashboard.slices = list(charts.values())
        db.session.commit()
        print(json.dumps({"dashboard_id": dashboard.id, "slug": dashboard.slug, "industry": {"id_customer": 259, "label": "3CORACOES"}, "datasets": {"history": history.id, "causes": causes.id, "latest": latest.id}, "charts": {key: chart.id for key, chart in charts.items()}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
