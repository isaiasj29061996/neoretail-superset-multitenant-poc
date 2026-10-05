"""Create the NeoRetail OSA Industria dashboard (Valor view only).

Only Superset metadata is changed. All analytics sources are physical serving
marts created before this script runs.
"""
from __future__ import annotations

import json

from superset.app import create_app

from neoretail_bootstrap.overview.semantics import HISTORY_SQL, M, OVERVIEW_M
from neoretail_bootstrap.overview.filters import native_filters


from neoretail_bootstrap.core.chart_params import custom_params, table_params
from neoretail_bootstrap.core.layout import Layout
from neoretail_bootstrap.core.metadata import upsert_dataset, upsert_chart
from neoretail_bootstrap.core.metrics import metric


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
""".strip()

LATEST_SQL = f"""
SELECT h.*
FROM ({HISTORY_SQL}) h
JOIN (
  SELECT id_customer, MAX(mes_ano) AS max_data
  FROM gold.fato_historico
  GROUP BY id_customer
) d ON d.id_customer = h.id_customer AND d.max_data = h.data
""".strip()

LOSS_VALUE = metric("Perda R$ OSA", "SUM(loss_value_sum)")
LOSS_PERCENT = metric("% Perda", "100.0 * SUM(qtd_perda_osa) * AVG(avg_sales_price) / NULLIF(CASE WHEN SUM(faturamento) > 0 THEN SUM(faturamento) ELSE SUM(volume_unidades * avg_sales_price) END, 0)")
LOSS_PERCENT_SUMMARY = metric(
    "% Perda",
    "100.0 * SUM(osa_loss_qty_sum) * "
    "(SUM(avg_sales_price_sum) / NULLIF(SUM(avg_sales_price_count), 0)) / "
    "NULLIF(CASE WHEN SUM(faturamento_sum) > 0 "
    "THEN SUM(faturamento_sum) ELSE SUM(fallback_sellout_sum) END, 0)",
)
PROBLEM_COUNT = metric("Qtd Problema OSA", "SUM(qtd_problemas_osa)")
CAUSE_OSA = metric("% OSA Numérico", "100.0 * (1 - SUM(qtd_problemas_osa) / NULLIF(SUM(qtd_itens_ativos), 0))")


def motive_percent(label):
    patterns = {"Estoque Virtual": "%virtual%", "Falta de Exposição": "%exposi%", "Falta de Performance": "%performance%", "Ruptura na loja": "%ruptura%"}
    pattern = patterns[label]
    value = "COALESCE(loss_value_sum, 0)"
    return metric(label, f"100.0 * SUM(CASE WHEN LOWER(COALESCE(motivo_osa, '')) LIKE '{pattern}' THEN {value} ELSE 0 END) / NULLIF(SUM({value}), 0)")


CAUSE_FILTER_COLUMNS = (
    "rede", "bandeira", "uf", "cidade", "tipo_local", "loja", "regiao",
    "item", "descricao_marca",
    "hierarquia_1", "hierarquia_2", "hierarquia_3",
)


def causes_semantic_sql() -> str:
    checks = " or ".join(
        f"get_filters('{column}')" for column in CAUSE_FILTER_COLUMNS
    )
    detail = """
SELECT
    id_customer, data, motivo_osa, causa_osa,
    rede, bandeira, uf, cidade, tipo_local, loja, regiao,
    item, descricao_marca, hierarquia_1, hierarquia_2, hierarquia_3,
    COALESCE(qtd_perda_osa * NULLIF(preco_medio, 0), 0)::double precision
        AS loss_value_sum
FROM gold.nr_osa_industry_causes
""".strip()
    summary = """
SELECT
    id_customer, data, motivo_osa, causa_osa,
    NULL::text AS rede,
    NULL::text AS bandeira,
    NULL::text AS uf,
    NULL::text AS cidade,
    NULL::text AS tipo_local,
    NULL::text AS loja,
    NULL::text AS regiao,
    NULL::text AS item,
    NULL::text AS descricao_marca,
    NULL::text AS hierarquia_1,
    NULL::text AS hierarquia_2,
    NULL::text AS hierarquia_3,
    loss_value_sum
FROM gold.nr_osa_causes_summary
""".strip()
    return (
        f"{{% set has_dimension_filter = {checks} %}}\n"
        "{% if has_dimension_filter %}\n"
        f"{detail}\n"
        "{% else %}\n"
        f"{summary}\n"
        "{% endif %}"
    )


def main():
    app = create_app()
    with app.app_context():
        from superset import db
        from superset.connectors.sqla.models import SqlaTable
        from superset.models.core import Database
        from superset.models.dashboard import Dashboard
        from superset.models.slice import Slice

        database = db.session.query(Database).filter(Database.database_name == "NeoRetail Gold - PostgreSQL Local").one()
        summary = upsert_dataset(db.session, SqlaTable, database, "nr_overview_summary", table_name="nr_overview_summary")
        causes = upsert_dataset(
            db.session, SqlaTable, database, "nr_osa_causes_interactive",
            sql=causes_semantic_sql(),
        )
        latest = upsert_dataset(db.session, SqlaTable, database, "nr_panorama_latest", table_name="nr_panorama_latest")
        filter_options = upsert_dataset(db.session, SqlaTable, database, "nr_filter_options", table_name="nr_filter_options")

        charts = {}
        def add(key, dataset, title, params, viz="neoretail-kpi-card"):
            charts[key] = upsert_chart(db.session, Slice, dataset, f"[OSA Indústria] {title}", params, viz)

        top_metrics = [
            OVERVIEW_M["osa"],
            OVERVIEW_M["sellout"],
            OVERVIEW_M["osa_loss"],
            LOSS_PERCENT_SUMMARY,
        ]
        top = custom_params(
            summary,
            "Visão geral mensal",
            top_metrics,
            grain="P1M",
            styles="line|bar|hidden|line",
            formats="percent|currency|currency|percent",
        )
        top.update({
            "summary_count": "3",
            "metric_labels": "%OSA|Sell Out Venda|Perda R$ OSA|% Perda",
            "row_limit": 10000,
        })
        add("overview", summary, "Visão geral mensal — Valor", top)

        motive_metrics = [motive_percent(label) for label in ("Estoque Virtual", "Falta de Exposição", "Falta de Performance", "Ruptura na loja")]
        stacked = custom_params(causes, "Perdas por motivo", motive_metrics, grain="P1M", styles="bar|bar|bar|bar", formats="percent|percent|percent|percent", variant="stacked")
        add("stacked", causes, "Visão geral mensal — Perdas", stacked)

        motive = custom_params(causes, "Perda OSA", [LOSS_VALUE], groupby=["motivo_osa"], variant="verticalbars", formats="currency", row_limit=10)
        cause = custom_params(causes, "Perda por causa OSA", [LOSS_VALUE], groupby=["causa_osa"], variant="verticalbars", formats="currency", row_limit=15)
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
        dashboard.css = ".dashboard-content { background: #e7f0f5 !important; } .dashboard-component-chart-holder { border-radius: 8px; background: #fff; } .dashboard-component-chart-holder > .header { display: none !important; }"
        dashboard.json_metadata = json.dumps({"timed_refresh_immune_slices": [], "expanded_slices": {}, "refresh_frequency": 0, "color_scheme": "supersetColors", "native_filter_configuration": native_filters(summary.id, filter_options.id), "filter_bar_orientation": "HORIZONTAL"}, ensure_ascii=False)
        dashboard.slices = list(charts.values())
        db.session.commit()
        print(json.dumps({"dashboard_id": dashboard.id, "slug": dashboard.slug, "industry": {"id_customer": 142, "label": "AMBEV"}, "datasets": {"summary": summary.id, "causes": causes.id, "latest": latest.id}, "charts": {key: chart.id for key, chart in charts.items()}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
