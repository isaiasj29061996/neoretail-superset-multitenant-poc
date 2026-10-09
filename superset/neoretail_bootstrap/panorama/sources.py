"""Panorama sources: existing certified contracts and chart composition."""
from __future__ import annotations

from neoretail_bootstrap.core.metrics import metric
from .filters import WEEKLY_FILTER_COLUMNS


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


_WEEKLY_SELLOUT = (
    "CASE WHEN SUM(faturamento_sum) > 0 "
    "THEN SUM(faturamento_sum) ELSE SUM(fallback_sellout_sum) END"
)


WEEKLY_P = {
    "sellout": metric("Venda sell out", _WEEKLY_SELLOUT),
    "cost": metric("Venda custo", "SUM(sales_cost_sum)"),
    "markup": metric(
        "Markup", f"100.0 * ({_WEEKLY_SELLOUT}) / NULLIF(SUM(sales_cost_sum), 0)"
    ),
    "stock_cost": metric("Estoque custo", "SUM(stock_cost_sum)"),
    "stock_qty": metric("Estoque qtd", "SUM(stock_qty_sum)"),
    "roi": metric(
        "ROI",
        f"100.0 * (({_WEEKLY_SELLOUT}) - SUM(sales_cost_sum)) "
        "/ NULLIF(SUM(stock_cost_sum), 0)",
    ),
    "coverage": metric(
        "Cobertura de estoque",
        "SUM(stock_qty_sum) / NULLIF(SUM(sales_qty_sum) / 4.33, 0)",
    ),
    "giro": metric(
        "Giro", "SUM(giro_sum_positive) / NULLIF(SUM(giro_count_positive), 0)"
    ),
    "osa": metric(
        "OSA",
        "100.0 * (1 - SUM(osa_problem_sum) / NULLIF(SUM(osa_active_sum), 0))",
    ),
    "rup": metric(
        "Ruptura", "100.0 * SUM(rupture_sum) / NULLIF(SUM(osa_active_sum), 0)"
    ),
    "isv": metric(
        "Item sem venda", "100.0 * SUM(isv_sum) / NULLIF(SUM(osa_active_sum), 0)"
    ),
}


def weekly_semantic_sql() -> str:
    checks = " or ".join(
        f"get_filters('{column}')" for column in WEEKLY_FILTER_COLUMNS
    )
    detail = """
SELECT
    id_customer, data, tp_activity_level, activity_level,
    rede, bandeira, uf, cidade, tipo_local, loja, regiao,
    item, descricao_marca, hierarquia_1, hierarquia_2, hierarquia_3,
    COALESCE(faturamento, 0)::double precision AS faturamento_sum,
    (COALESCE(volume_unidades, 0) * COALESCE(avg_sales_price, 0))::double precision AS fallback_sellout_sum,
    (COALESCE(volume_unidades, 0) * COALESCE(avg_price_cost, 0))::double precision AS sales_cost_sum,
    COALESCE(volume_unidades, 0)::double precision AS sales_qty_sum,
    (COALESCE(estoque_medio, 0) * COALESCE(avg_price_cost, 0))::double precision AS stock_cost_sum,
    COALESCE(estoque_unidades, 0)::double precision AS stock_qty_sum,
    CASE WHEN COALESCE(giro, 0) > 0 THEN giro ELSE 0 END::double precision AS giro_sum_positive,
    CASE WHEN COALESCE(giro, 0) > 0 THEN 1 ELSE 0 END::bigint AS giro_count_positive,
    COALESCE(qtd_problemas_osa, 0)::double precision AS osa_problem_sum,
    COALESCE(qtd_item_ativo_osa, 0)::double precision AS osa_active_sum,
    COALESCE(rup, 0)::double precision AS rupture_sum,
    COALESCE(est_virtual, 0)::double precision AS isv_sum
FROM gold.nr_panorama_weekly
""".strip()
    return (
        f"{{% set has_dimension_filter = {checks} %}}\n"
        "{% if has_dimension_filter %}\n"
        f"{detail}\n"
        "{% else %}\n"
        "SELECT * FROM gold.nr_panorama_weekly_summary\n"
        "{% endif %}"
    )
