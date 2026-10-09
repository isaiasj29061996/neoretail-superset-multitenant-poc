"""Panorama inventory: existing certified contracts and chart composition."""
from __future__ import annotations

from neoretail_bootstrap.core.metrics import metric
from neoretail_bootstrap.core.chart_params import custom_params
from neoretail_bootstrap.core.filters import _jinja_filter_predicates
from .filters import WEEKLY_FILTER_COLUMNS


def monthly_inventory_semantic_sql() -> str:
    """Certified monthly Stock/Giro/ROI/OSA components over the serving mart."""
    checks = " or ".join(f"get_filters('{column}')" for column in WEEKLY_FILTER_COLUMNS)
    predicates = _jinja_filter_predicates("f", "tp_activity_level", {
        "rede": "l.rede", "bandeira": "l.bandeira", "uf": "l.uf",
        "cidade": "l.cidade", "tipo_local": "l.tipo_local",
        "loja": "l.loja", "regiao": "l.regiao", "item": "i.item",
        "descricao_marca": "i.descricao_marca", "hierarquia_1": "i.hierarquia_1",
        "hierarquia_2": "i.hierarquia_2", "hierarquia_3": "i.hierarquia_3",
    })
    detail = f"""
WITH filtered AS (
  SELECT
    f.mes_ano::date AS data,
    f.id_customer,
    f.id_item,
    f.id_location,
    f.volume_unidades,
    f.faturamento,
    f.estoque_unidades,
    f.estoque_medio,
    f.qtd_problemas_osa,
    f.qtd_item_ativo_osa,
    f.rup,
    f.est_virtual,
    f.giro,
    f.avg_sales_price,
    f.avg_price_cost,
    f.status_item_geral,
    f.tp_activity_level,
    CASE f.tp_activity_level
      WHEN 'F' THEN 'Fast Mover'
      WHEN 'S' THEN 'Slow Mover'
      WHEN 'US' THEN 'Ultra Slow Mover'
      WHEN 'N' THEN 'New Mover'
      ELSE COALESCE(f.tp_activity_level,'Outros')
    END AS activity_level,
    l.rede,l.bandeira,l.uf,l.cidade,l.tipo_local,l.loja,l.regiao,
    i.item,i.descricao_marca,i.hierarquia_1,i.hierarquia_2,i.hierarquia_3
  FROM gold.fato_historico f
  LEFT JOIN gold.dim_local l
    ON l.id_customer=f.id_customer AND l.id_location=f.id_location
  LEFT JOIN gold.dim_itens i
    ON i.id_customer=f.id_customer AND i.id_item=f.id_item
  WHERE 1=1
{predicates}
), monthly AS (
  SELECT
    data,id_customer,
    SUM(COALESCE(faturamento,0))::float8 AS faturamento_sum,
    SUM(COALESCE(volume_unidades,0))::float8 AS volume_sum,
    SUM(COALESCE(avg_sales_price,0))::float8 AS fallback_price_sum,
    COUNT(avg_sales_price)::bigint AS fallback_price_count,
    SUM(COALESCE(volume_unidades,0)*COALESCE(avg_price_cost,0))::float8 AS sales_cost_sum,
    SUM(COALESCE(estoque_medio,0)*COALESCE(avg_price_cost,0))::float8 AS stock_cost_sum,
    SUM(COALESCE(estoque_unidades,0))::float8 AS stock_qty_base,
    SUM(giro) FILTER (WHERE giro>0)::float8 AS giro_num,
    COUNT(giro) FILTER (WHERE giro>0)::bigint AS giro_den,
    SUM(COALESCE(qtd_problemas_osa,0))::float8 AS osa_problem_sum,
    SUM(COALESCE(qtd_item_ativo_osa,0))::float8 AS osa_active_sum,
    SUM(COALESCE(rup,0))::float8 AS rupture_sum,
    SUM(COALESCE(status_item_geral,0))::float8 AS status_sum,
    SUM(COALESCE(est_virtual,0))::float8 AS isv_sum
  FROM filtered
  GROUP BY data,id_customer
), factors AS (
  SELECT f.data,f.id_customer,c.nm_measure,MAX(c.conversion_rate)::float8 AS conversion_factor
  FROM (SELECT DISTINCT data,id_customer,id_item FROM filtered) f
  JOIN gold.dim_conversao c
    ON c.id_customer=f.id_customer AND c.id_item::text=f.id_item::text
  GROUP BY f.data,f.id_customer,c.nm_measure
)
SELECT
  m.data,m.id_customer,f.nm_measure,
  CASE WHEN m.faturamento_sum>0 THEN m.faturamento_sum
       WHEN f.conversion_factor IS NOT NULL AND m.fallback_price_count>0
       THEN (m.volume_sum*f.conversion_factor)
          *((m.fallback_price_sum/m.fallback_price_count)*f.conversion_factor)
       ELSE NULL END::float8 AS sellout_sum,
  m.sales_cost_sum,m.stock_cost_sum,
  (m.stock_qty_base*f.conversion_factor)::float8 AS stock_qty_sum,
  m.giro_num,m.giro_den,
  m.osa_problem_sum,m.osa_active_sum,m.rupture_sum,m.status_sum,m.isv_sum,
  NULL::text rede,NULL::text bandeira,NULL::text uf,NULL::text cidade,
  NULL::text tipo_local,NULL::text loja,NULL::text regiao,
  NULL::text tp_activity_level,NULL::text activity_level,NULL::text item,
  NULL::text descricao_marca,NULL::text hierarquia_1,NULL::text hierarquia_2,
  NULL::text hierarquia_3
FROM monthly m
JOIN factors f USING(data,id_customer)
""".strip()
    return (
        f"{{% set has_dimension_filter = {checks} %}}\n"
        "{% if has_dimension_filter %}\n" + detail + "\n"
        "{% else %}\nSELECT * FROM gold.nr_panorama_inventory_monthly_default\n{% endif %}"
    )


def weekly_inventory_card_semantic_sql() -> str:
    """TOP-13 weekly inventory timeline plus monthly summary in one dataset."""
    checks = " or ".join(f"get_filters('{column}')" for column in WEEKLY_FILTER_COLUMNS)
    weekly_predicates = _jinja_filter_predicates("w")
    # This governed detail already includes dimensions and STATUS_ITEM_GERAL.
    # The overview history omits that certified Ruptura/ISV denominator.
    monthly_predicates = _jinja_filter_predicates("f")
    detail = f"""
WITH weekly_filtered AS (
  SELECT w.* FROM gold.nr_panorama_inventory_weekly_detail w WHERE 1=1
{weekly_predicates}
), ranked_weeks AS (
  SELECT id_customer,data,cd_week,DENSE_RANK() OVER (
    PARTITION BY id_customer ORDER BY cd_week DESC
  ) AS week_rank
  FROM (SELECT DISTINCT id_customer,data,cd_week FROM weekly_filtered) x
), tenant_latest AS (
  SELECT id_customer,MAX(cd_week) AS latest_cd_week
  FROM gold.nr_panorama_inventory_weekly_detail
  GROUP BY id_customer
), weekly_scoped AS (
  SELECT f.*,l.latest_cd_week
  FROM weekly_filtered f
  JOIN ranked_weeks r USING(id_customer,data,cd_week)
  JOIN tenant_latest l USING(id_customer)
  WHERE r.week_rank<=13
), weekly AS (
  SELECT
    data,cd_week,id_customer,MAX(latest_cd_week) AS latest_cd_week,
    SUM(COALESCE(faturamento,0))::float8 AS faturamento_sum,
    SUM(COALESCE(volume_unidades,0))::float8 AS volume_sum,
    SUM(COALESCE(avg_sales_price,0))::float8 AS fallback_price_sum,
    COUNT(avg_sales_price)::bigint AS fallback_price_count,
    SUM(COALESCE(volume_unidades,0)*COALESCE(avg_price_cost,0))::float8 AS sales_cost_sum,
    SUM(COALESCE(estoque_medio,0)*COALESCE(avg_price_cost,0))::float8 AS stock_cost_sum,
    SUM(COALESCE(estoque_unidades,0))::float8 AS stock_qty_base,
    SUM(giro) FILTER (WHERE giro IS NOT NULL)::float8 AS giro_num_raw,
    COUNT(giro)::bigint AS giro_den_raw,
    SUM(COALESCE(qtd_problemas_osa,0))::float8 AS osa_problem_sum,
    SUM(COALESCE(qtd_item_ativo_osa,0))::float8 AS osa_active_sum,
    SUM(COALESCE(rup,0))::float8 AS rupture_sum,
    SUM(COALESCE(status_item_geral,0))::float8 AS status_sum,
    SUM(COALESCE(est_virtual,0))::float8 AS isv_sum
  FROM weekly_scoped
  GROUP BY data,cd_week,id_customer
), weekly_factors AS (
  SELECT s.data,s.id_customer,c.nm_measure,MAX(c.conversion_rate)::float8 AS conversion_factor
  FROM (SELECT DISTINCT data,id_customer,id_item FROM weekly_scoped) s
  JOIN gold.dim_conversao c
    ON c.id_customer=s.id_customer AND c.id_item::text=s.id_item::text
  GROUP BY s.data,s.id_customer,c.nm_measure
), monthly_filtered AS (
  SELECT f.* FROM gold.nr_panorama_comparison_history_detail f WHERE 1=1
{monthly_predicates}
), monthly AS (
  SELECT
    data,id_customer,
    SUM(COALESCE(faturamento,0))::float8 AS faturamento_sum,
    SUM(COALESCE(volume_unidades,0))::float8 AS volume_sum,
    SUM(COALESCE(avg_sales_price,0))::float8 AS fallback_price_sum,
    COUNT(avg_sales_price)::bigint AS fallback_price_count,
    SUM(COALESCE(volume_unidades,0)*COALESCE(avg_price_cost,0))::float8 AS sales_cost_sum,
    SUM(COALESCE(estoque_medio,0)*COALESCE(avg_price_cost,0))::float8 AS stock_cost_sum,
    SUM(COALESCE(estoque_unidades,0))::float8 AS stock_qty_base,
    SUM(giro) FILTER (WHERE giro>0)::float8 AS giro_num,
    COUNT(giro) FILTER (WHERE giro>0)::bigint AS giro_den,
    SUM(COALESCE(qtd_problemas_osa,0))::float8 AS osa_problem_sum,
    SUM(COALESCE(qtd_item_ativo_osa,0))::float8 AS osa_active_sum,
    SUM(COALESCE(rup,0))::float8 AS rupture_sum,
    SUM(COALESCE(status_item_geral,0))::float8 AS status_sum,
    SUM(COALESCE(est_virtual,0))::float8 AS isv_sum
  FROM monthly_filtered
  GROUP BY data,id_customer
), monthly_factors AS (
  SELECT f.data,f.id_customer,c.nm_measure,MAX(c.conversion_rate)::float8 AS conversion_factor
  FROM (SELECT DISTINCT data,id_customer,id_item FROM monthly_filtered) f
  JOIN gold.dim_conversao c
    ON c.id_customer=f.id_customer AND c.id_item::text=f.id_item::text
  GROUP BY f.data,f.id_customer,c.nm_measure
)
SELECT
  'timeline'::text AS row_scope,
  w.data,w.cd_week,w.id_customer,f.nm_measure,
  CASE WHEN w.faturamento_sum>0 THEN w.faturamento_sum
       WHEN f.conversion_factor IS NOT NULL AND w.fallback_price_count>0
       THEN (w.volume_sum*f.conversion_factor)
          *((w.fallback_price_sum/w.fallback_price_count)*f.conversion_factor)
       ELSE NULL END::float8 AS sellout_sum,
  w.sales_cost_sum,w.stock_cost_sum,
  (w.stock_qty_base*f.conversion_factor)::float8 AS stock_qty_sum,
  CASE WHEN w.cd_week=w.latest_cd_week THEN NULL ELSE w.giro_num_raw END::float8 AS giro_num,
  CASE WHEN w.cd_week=w.latest_cd_week THEN NULL ELSE w.giro_den_raw END::bigint AS giro_den,
  w.osa_problem_sum,w.osa_active_sum,w.rupture_sum,w.status_sum,w.isv_sum,
  NULL::text rede,NULL::text bandeira,NULL::text uf,NULL::text cidade,
  NULL::text tipo_local,NULL::text loja,NULL::text regiao,
  NULL::text tp_activity_level,NULL::text activity_level,NULL::text item,
  NULL::text descricao_marca,NULL::text hierarquia_1,NULL::text hierarquia_2,
  NULL::text hierarquia_3
FROM weekly w
JOIN weekly_factors f USING(data,id_customer)

UNION ALL

SELECT
  'summary'::text AS row_scope,
  m.data,NULL::text AS cd_week,m.id_customer,f.nm_measure,
  CASE WHEN m.faturamento_sum>0 THEN m.faturamento_sum
       WHEN f.conversion_factor IS NOT NULL AND m.fallback_price_count>0
       THEN (m.volume_sum*f.conversion_factor)
          *((m.fallback_price_sum/m.fallback_price_count)*f.conversion_factor)
       ELSE NULL END::float8 AS sellout_sum,
  m.sales_cost_sum,m.stock_cost_sum,
  (m.stock_qty_base*f.conversion_factor)::float8 AS stock_qty_sum,
  m.giro_num,m.giro_den,
  m.osa_problem_sum,m.osa_active_sum,m.rupture_sum,m.status_sum,m.isv_sum,
  NULL::text rede,NULL::text bandeira,NULL::text uf,NULL::text cidade,
  NULL::text tipo_local,NULL::text loja,NULL::text regiao,
  NULL::text tp_activity_level,NULL::text activity_level,NULL::text item,
  NULL::text descricao_marca,NULL::text hierarquia_1,NULL::text hierarquia_2,
  NULL::text hierarquia_3
FROM monthly m
JOIN monthly_factors f USING(data,id_customer)
""".strip()
    return (
        f"{{% set has_dimension_filter = {checks} %}}\n"
        "{% if has_dimension_filter %}\n" + detail + "\n"
        "{% else %}\nSELECT * FROM gold.nr_panorama_inventory_weekly_card_default\n{% endif %}"
    )


def register_inventory_charts(add, monthly_inventory, weekly_inventory_card):
    stock_measures = [
        metric("Estoque preço custo", "SUM(stock_cost_sum)"),
        metric("Estoque quantidade", "SUM(stock_qty_sum)"),
    ]
    params = custom_params(
        monthly_inventory,
        "Evolutivo de estoque",
        stock_measures,
        grain="P1M",
        styles="bar|bar",
        formats="currency|quantity",
        labels="Estoque Preço Custo|Estoque Quantidade",
        semantic_profile="stock_bundle",
        summary_count=2,
        timeline_limit=13,
    )
    add("stock_mensal", monthly_inventory, "Evolutivo de estoque — Estoque mensal", params)

    params = custom_params(
        weekly_inventory_card,
        "Evolutivo de estoque",
        stock_measures,
        grain="P1W",
        styles="bar|bar",
        formats="currency|quantity",
        labels="Estoque Preço Custo|Estoque Quantidade",
        semantic_profile="stock_bundle",
        summary_count=2,
        timeline_limit=13,
        summary_query_scope="summary",
        timeline_query_scope="timeline",
    )
    add("stock_semanal", weekly_inventory_card, "Evolutivo de estoque — Estoque semanal", params)

    # GIRO x ROI
    # Report contract: Stock Cost as bar + ROI and Giro as lines.
    # ROI is recomputed from Sell Out / Venda Custo / Estoque Custo.
    # Giro is a weighted average over additive sum/count components.
    giro_roi_measures = [
        metric("Estoque preço custo", "SUM(stock_cost_sum)"),
        metric("Venda sell out", "SUM(sellout_sum)"),
        metric("Venda custo", "SUM(sales_cost_sum)"),
        metric("Estoque custo ROI", "SUM(stock_cost_sum)"),
        metric("Giro soma", "SUM(giro_num)"),
        metric("Giro linhas", "SUM(giro_den)"),
    ]
    giro_roi_semantics = "direct_average:0:1|roi:1:3|weighted_average:4:2"
    params = custom_params(
        monthly_inventory,
        "Evolutivo de estoque",
        giro_roi_measures,
        grain="P1M",
        styles="bar|line|line",
        formats="currency|percent|number",
        labels="Estoque Preço Custo|% ROI|Giro",
        metric_semantics=giro_roi_semantics,
        summary_count=3,
        summary_labels="U3M|Anual|U3M",
        metric_summary_modes="u3m|annual12|u3m",
        timeline_zero_blank_indices="1",
        timeline_limit=13,
    )
    add("giro_roi_mensal", monthly_inventory, "Evolutivo de estoque — Giro x ROI mensal", params)

    params = custom_params(
        weekly_inventory_card,
        "Evolutivo de estoque",
        giro_roi_measures,
        grain="P1W",
        styles="bar|line|line",
        formats="currency|percent|number",
        labels="Estoque Preço Custo|% ROI|Giro",
        metric_semantics=giro_roi_semantics,
        summary_count=3,
        summary_labels="U3M|Anual|U3M",
        metric_summary_modes="u3m|annual12|u3m",
        timeline_zero_blank_indices="1",
        timeline_limit=13,
        summary_query_scope="summary",
        timeline_query_scope="timeline",
    )
    add("giro_roi_semanal", weekly_inventory_card, "Evolutivo de estoque — Giro x ROI semanal", params)
