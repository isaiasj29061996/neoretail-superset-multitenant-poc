"""Create/update the semantically certified quantity overview dashboard."""
from __future__ import annotations

import json

from superset.app import create_app

from bootstrap_overview import (
    _jinja_filter_predicates,
    chart_params,
    metric,
    overview_native_filters,
    position_json,
    upsert_chart,
    upsert_dataset,
)

DASHBOARD_TITLE = "NeoRetail V9 — Visão geral quantidade"
DASHBOARD_SLUG = "neoretail-v9-visao-geral-quantidade"

Q = {
    "sales": metric("Venda quantidade", "SUM(sales_sum)"),
    "loss": metric("Perda OSA quantidade", "SUM(loss_sum)"),
    "price_num": metric("Preço soma elegível", "SUM(price_numerator)"),
    "price_count": metric("Preço linhas elegíveis", "SUM(price_count)"),
    "osa_problem": metric("OSA problemas", "SUM(osa_problem_sum)"),
    "osa_active": metric("OSA ativos", "SUM(osa_active_sum)"),
    "rupture_num": metric("Ruptura numerador", "SUM(rupture_sum)"),
    "status_den": metric("Status item denominador", "SUM(status_sum)"),
    "isv_num": metric("ISV numerador", "SUM(isv_sum)"),
    "stock": metric("Estoque unidades", "SUM(stock_sum)"),
    "demand": metric("Demanda média", "SUM(demand_sum)"),
    "stores": metric("Quantidade de lojas", "MAX(store_count)"),
    "items": metric("Quantidade de itens", "MAX(item_count)"),
    "stores_u3m": metric("Lojas U3M", "MAX(store_count_u3m)"),
    "items_u3m": metric("Itens U3M", "MAX(item_count_u3m)"),
    "osa_critical": metric("Itens críticos OSA", "SUM(osa_critical_count)"),
    "osa_risk": metric("Itens risco OSA", "SUM(osa_risk_count)"),
    "rup_critical": metric("Itens críticos Ruptura", "SUM(rupture_critical_count)"),
    "rup_risk": metric("Itens risco Ruptura", "SUM(rupture_risk_count)"),
    "isv_critical": metric("Itens críticos ISV", "SUM(isv_critical_count)"),
    "isv_risk": metric("Itens risco ISV", "SUM(isv_risk_count)"),
}

FILTER_COLUMNS = (
    "rede", "bandeira", "uf", "cidade", "tipo_local", "loja", "regiao",
    "tp_activity_level", "item", "descricao_marca", "hierarquia_1",
    "hierarquia_2", "hierarquia_3",
)


def quantity_semantic_sql() -> str:
    checks = " or ".join(f"get_filters('{column}')" for column in FILTER_COLUMNS)
    fact_filters = _jinja_filter_predicates("h")
    task_filters = _jinja_filter_predicates(
        "o", "max_tp_activity_level", {
            "rede": "l.rede", "bandeira": "l.bandeira", "uf": "l.uf",
            "cidade": "l.cidade", "tipo_local": "l.tipo_local",
            "loja": "l.loja", "regiao": "l.regiao", "item": "i.item",
            "descricao_marca": "i.descricao_marca", "hierarquia_1": "i.hierarquia_1",
            "hierarquia_2": "i.hierarquia_2", "hierarquia_3": "i.hierarquia_3",
        },
    )
    detail = f"""
WITH filtered AS (
  SELECT h.* FROM gold.nr_overview_quantity_detail h WHERE 1=1
{fact_filters}
), monthly AS (
  SELECT data,id_customer,
    SUM(COALESCE(volume_unidades,0))::float8 volume_sum,
    SUM(COALESCE(faturamento,0))::float8 faturamento_sum,
    SUM(COALESCE(qtd_perda_osa,0))::float8 loss_qty_sum,
    SUM(COALESCE(avg_sales_price,0)) FILTER (WHERE faturamento>0)::float8 price_sum,
    COUNT(avg_sales_price) FILTER (WHERE faturamento>0)::bigint price_count,
    SUM(COALESCE(qtd_problemas_osa,0))::float8 osa_problem_sum,
    SUM(COALESCE(qtd_item_ativo_osa,0))::float8 osa_active_sum,
    SUM(COALESCE(rup,0))::float8 rupture_sum,
    SUM(COALESCE(status_item_geral,0))::float8 status_sum,
    SUM(COALESCE(est_virtual,0))::float8 isv_sum,
    SUM(COALESCE(estoque_unidades,0))::float8 stock_sum,
    SUM(COALESCE(demanda_media,0))::float8 demand_sum,
    COUNT(DISTINCT cnpj) FILTER (WHERE positivacao=1)::bigint store_count,
    COUNT(DISTINCT ean) FILTER (WHERE positivacao=1)::bigint item_count
  FROM filtered GROUP BY data,id_customer
), factors AS (
  SELECT f.data,f.id_customer,c.nm_measure,MAX(c.conversion_rate)::float8 conversion_factor
  FROM (SELECT DISTINCT data,id_customer,id_item FROM filtered) f
  JOIN gold.dim_conversao c ON c.id_customer=f.id_customer AND c.id_item::text=f.id_item
  GROUP BY f.data,f.id_customer,c.nm_measure
), distribution_u3m AS (
  SELECT a.id_customer,a.data,
    COUNT(DISTINCT f.cnpj) FILTER (WHERE f.positivacao=1)::bigint store_count_u3m,
    COUNT(DISTINCT f.ean) FILTER (WHERE f.positivacao=1)::bigint item_count_u3m
  FROM (SELECT DISTINCT id_customer,data FROM filtered) a
  JOIN filtered f ON f.id_customer=a.id_customer
    AND f.data>=a.data-INTERVAL '2 months' AND f.data<=a.data
  GROUP BY a.id_customer,a.data
), expanded AS (
  SELECT m.*,f.nm_measure,f.conversion_factor FROM monthly m JOIN factors f USING(data,id_customer)
  UNION ALL SELECT m.*,'valor'::text,NULL::float8 FROM monthly m
), latest AS (SELECT id_customer,MAX(data) data FROM filtered GROUP BY id_customer),
tasks AS (
  SELECT o.id_customer,
    COUNT(o.id_item) FILTER (WHERE COALESCE(o.qtd_problemas_osa_m0,0)>0 AND a.nm_activity_level='Fast Mover')::bigint osa_critical_count,
    COUNT(o.id_item) FILTER (WHERE COALESCE(o.qtd_problemas_osa_m0,0)>0 AND o.max_tp_activity_level='S')::bigint osa_risk_count,
    COUNT(o.id_item) FILTER (WHERE COALESCE(o.rup,0)>0 AND o.max_tp_activity_level='F')::bigint rupture_critical_count,
    COUNT(o.id_item) FILTER (WHERE COALESCE(o.rup,0)>0 AND o.max_tp_activity_level='S')::bigint rupture_risk_count,
    COUNT(o.id_item) FILTER (WHERE COALESCE(o.est_virtual,0)>0 AND o.max_tp_activity_level='F')::bigint isv_critical_count,
    COUNT(o.id_item) FILTER (WHERE COALESCE(o.est_virtual,0)>0 AND o.max_tp_activity_level='S')::bigint isv_risk_count
  FROM gold.calculo_oportunidades o
  LEFT JOIN gold.dim_local l ON l.id_customer=o.id_customer AND l.id_location=o.id_location
  LEFT JOIN gold.dim_itens i ON i.id_customer=o.id_customer AND i.id_item=o.id_item
  LEFT JOIN gold.dim_nivel_atividade a ON a.id_customer=o.id_customer AND a.tp_activity_level=o.max_tp_activity_level
  WHERE 1=1
{task_filters}
  GROUP BY o.id_customer
)
SELECT e.data,e.id_customer,e.nm_measure,
  CASE WHEN e.nm_measure='valor' THEN e.faturamento_sum ELSE e.volume_sum*e.conversion_factor END::float8 sales_sum,
  CASE WHEN e.nm_measure='valor' THEN NULL ELSE e.loss_qty_sum*e.conversion_factor END::float8 loss_sum,
  (e.price_sum*e.conversion_factor)::float8 price_numerator,e.price_count,
  e.osa_problem_sum,e.osa_active_sum,e.rupture_sum,e.status_sum,e.isv_sum,e.stock_sum,e.demand_sum,
  e.store_count,e.item_count,COALESCE(d.store_count_u3m,0) store_count_u3m,COALESCE(d.item_count_u3m,0) item_count_u3m,
  CASE WHEN e.data=x.data THEN COALESCE(t.osa_critical_count,0) ELSE 0 END osa_critical_count,
  CASE WHEN e.data=x.data THEN COALESCE(t.osa_risk_count,0) ELSE 0 END osa_risk_count,
  CASE WHEN e.data=x.data THEN COALESCE(t.rupture_critical_count,0) ELSE 0 END rupture_critical_count,
  CASE WHEN e.data=x.data THEN COALESCE(t.rupture_risk_count,0) ELSE 0 END rupture_risk_count,
  CASE WHEN e.data=x.data THEN COALESCE(t.isv_critical_count,0) ELSE 0 END isv_critical_count,
  CASE WHEN e.data=x.data THEN COALESCE(t.isv_risk_count,0) ELSE 0 END isv_risk_count,
  NULL::text rede,NULL::text bandeira,NULL::text uf,NULL::text cidade,NULL::text tipo_local,NULL::text loja,NULL::text regiao,
  NULL::text tp_activity_level,NULL::text item,NULL::text descricao_marca,NULL::text hierarquia_1,NULL::text hierarquia_2,NULL::text hierarquia_3
FROM expanded e JOIN latest x ON x.id_customer=e.id_customer
LEFT JOIN distribution_u3m d ON d.id_customer=e.id_customer AND d.data=e.data
LEFT JOIN tasks t ON t.id_customer=e.id_customer
""".strip()
    return (
        f"{{% set has_dimension_filter = {checks} %}}\n"
        "{% if has_dimension_filter %}\n" + detail + "\n"
        "{% else %}\nSELECT * FROM gold.nr_overview_quantity_default\n{% endif %}"
    )


def comparison_params(dataset, title, measures, *, profile, fmt="number", direction="higher",
                      show_tasks=False, critical_metric=None, risk_metric=None, plain=True,
                      labels=None, help_text=None, **extra):
    return chart_params(
        dataset, title, "quantitycompareplain" if plain else "quantitycompare", measures,
        metric_labels=labels or title, metric_formats=fmt, metric_directions=direction,
        semantic_profile=profile, show_tasks=show_tasks,
        critical_metric=critical_metric, risk_metric=risk_metric,
        task_labels="itens críticos|itens em risco", help_text=help_text or title,
        **extra,
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
        semantic = upsert_dataset(
            db.session, SqlaTable, database, "nr_overview_quantity_interactive",
            sql=quantity_semantic_sql(),
        )
        filter_options = upsert_dataset(
            db.session, SqlaTable, database, "nr_filter_options", table_name="nr_filter_options"
        )
        conversion_options = upsert_dataset(
            db.session, SqlaTable, database, "nr_conversion_options",
            table_name="nr_conversion_options",
        )

        specs = [
            ("Vendas", comparison_params(semantic, "Vendas", [Q["sales"]], profile="direct_average")),
            ("Perda de vendas OSA", comparison_params(semantic, "Perda de vendas OSA", [Q["loss"]], profile="direct_sum", direction="lower")),
            ("Preço médio", comparison_params(
                semantic, "Preço médio", [Q["price_num"], Q["price_count"]],
                profile="weighted_average", fmt="currency", plain=True,
                semantic_disable_ly=True,
            )),
            ("Distribuição e sortimento", comparison_params(
                semantic, "Distribuição e sortimento",
                [Q["stores"], Q["items"], Q["stores_u3m"], Q["items_u3m"]],
                profile="distribution_bundle", labels="Quantidade de lojas|Quantidade de itens",
                help_text="PENDENTE_DADOS: positivacao está ausente no snapshot AMBEV; regra DAX preservada sem substituição por IDs.",
            )),
            ("% OSA", comparison_params(semantic, "% OSA", [Q["osa_problem"], Q["osa_active"]], profile="one_minus_ratio", fmt="percent", show_tasks=True, critical_metric=Q["osa_critical"], risk_metric=Q["osa_risk"])),
            ("Ruptura", comparison_params(semantic, "Ruptura", [Q["rupture_num"], Q["status_den"]], profile="ratio_percent", fmt="percent", direction="lower", show_tasks=True, critical_metric=Q["rup_critical"], risk_metric=Q["rup_risk"])),
            ("Item sem venda", comparison_params(semantic, "Item sem venda", [Q["isv_num"], Q["status_den"]], profile="ratio_percent", fmt="percent", direction="lower", show_tasks=True, critical_metric=Q["isv_critical"], risk_metric=Q["isv_risk"])),
            ("Cobertura de estoque", comparison_params(semantic, "Cobertura de estoque", [Q["stock"], Q["demand"]], profile="ratio", direction="lower")),
        ]
        charts = [upsert_chart(db.session, Slice, semantic, f"[Visão quantidade] {title}", params) for title, params in specs]

        dashboard = db.session.query(Dashboard).filter(Dashboard.dashboard_title == DASHBOARD_TITLE).one_or_none()
        if dashboard is None:
            dashboard = Dashboard(dashboard_title=DASHBOARD_TITLE, slug=DASHBOARD_SLUG, published=True)
            db.session.add(dashboard)
        dashboard.slug = DASHBOARD_SLUG
        dashboard.published = True
        dashboard.position_json = position_json(charts)
        dashboard.css = ".dashboard-content { background: #e7f0f5 !important; } .dashboard-component-chart-holder { border-radius: 8px; } .dashboard-component-chart-holder > .header { display: none !important; }"
        dashboard.json_metadata = json.dumps({
            "timed_refresh_immune_slices": [], "expanded_slices": {}, "refresh_frequency": 0,
            "color_scheme": "supersetColors",
            "native_filter_configuration": overview_native_filters(
                [semantic.id],
                {
                    "nm_measure": conversion_options.id,
                    **{column: filter_options.id for column in FILTER_COLUMNS},
                },
            ),
            "filter_bar_orientation": "HORIZONTAL",
        }, ensure_ascii=False)
        dashboard.slices = charts
        db.session.commit()
        print(json.dumps({"dashboard_id": dashboard.id, "slug": dashboard.slug,
                          "dataset": semantic.id,
                          "charts": {chart.slice_name: chart.id for chart in charts}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
