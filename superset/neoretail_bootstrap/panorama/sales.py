"""Panorama sales: existing certified contracts and chart composition."""
from __future__ import annotations

from neoretail_bootstrap.core.metrics import metric
from neoretail_bootstrap.core.chart_params import custom_params
from neoretail_bootstrap.core.filters import _jinja_filter_predicates
from .filters import WEEKLY_FILTER_COLUMNS


def weekly_sales_semantic_sql() -> str:
    """Real weekly fact, with dimensional filters applied before TOP 13."""
    checks = " or ".join(f"get_filters('{c}')" for c in WEEKLY_FILTER_COLUMNS)
    predicates = _jinja_filter_predicates("w", "status_item_geral", {
        "rede": "l.rede", "bandeira": "l.bandeira", "uf": "l.uf",
        "cidade": "l.cidade", "tipo_local": "l.tipo_local",
        "loja": "l.loja", "regiao": "l.regiao", "item": "i.item",
        "descricao_marca": "i.descricao_marca", "hierarquia_1": "i.hierarquia_1",
        "hierarquia_2": "i.hierarquia_2", "hierarquia_3": "i.hierarquia_3",
    })
    detail = f"""
WITH filtered AS (
  SELECT
    w.id_time AS data,w.cd_week,w.id_customer,w.id_item,w.id_location,
    w.volume_unidade AS volume_unidades,w.faturamento,w.qtd_perda_osa,
    w.avg_sales_price,w.avg_price_cost,w.status_item_geral::text AS tp_activity_level,
    COALESCE(w.status_item_geral::text,'Outros') AS activity_level,
    l.rede,l.bandeira,l.uf,l.cidade,l.tipo_local,l.loja,l.regiao,
    i.item,i.descricao_marca,i.hierarquia_1,i.hierarquia_2,i.hierarquia_3
  FROM gold.fato_semanal w
  LEFT JOIN gold.dim_local l ON l.id_customer=w.id_customer AND l.id_location=w.id_location
  LEFT JOIN gold.dim_itens i ON i.id_customer=w.id_customer AND i.id_item=w.id_item
  WHERE 1=1
{predicates}
), ranked_weeks AS (
  SELECT id_customer,data,cd_week,DENSE_RANK() OVER (
    PARTITION BY id_customer ORDER BY cd_week DESC
  ) week_rank
  FROM (SELECT DISTINCT id_customer,data,cd_week FROM filtered) x
), scoped AS (
  SELECT f.* FROM filtered f JOIN ranked_weeks r USING(id_customer,data,cd_week)
  WHERE r.week_rank<=13
), weekly AS (
  SELECT data,id_customer,MAX(cd_week) cd_week,
    SUM(COALESCE(faturamento,0))::float8 faturamento_sum,
    SUM(COALESCE(volume_unidades,0))::float8 volume_sum,
    SUM(COALESCE(avg_sales_price,0))::float8 fallback_price_sum,
    COUNT(avg_sales_price)::bigint fallback_price_count,
    SUM(COALESCE(volume_unidades,0)*COALESCE(avg_price_cost,0))::float8 cost_sum,
    SUM(COALESCE(qtd_perda_osa,0))::float8 loss_sum,
    SUM(COALESCE(avg_sales_price,0)) FILTER (WHERE faturamento>0)::float8 price_sum,
    COUNT(avg_sales_price) FILTER (WHERE faturamento>0)::bigint price_count
  FROM scoped GROUP BY data,id_customer
), factors AS (
  SELECT s.data,s.id_customer,c.nm_measure,MAX(c.conversion_rate)::float8 conversion_factor
  FROM (SELECT DISTINCT data,id_customer,id_item FROM scoped) s
  JOIN gold.dim_conversao c ON c.id_customer=s.id_customer AND c.id_item::text=s.id_item
  GROUP BY s.data,s.id_customer,c.nm_measure
)
SELECT w.data,w.cd_week,w.id_customer,f.nm_measure,
  CASE WHEN w.faturamento_sum>0 THEN w.faturamento_sum
       WHEN f.conversion_factor IS NOT NULL AND w.fallback_price_count>0
       THEN (w.volume_sum*f.conversion_factor)
          *((w.fallback_price_sum/w.fallback_price_count)*f.conversion_factor)
       ELSE NULL END::float8 sellout_sum,
  w.cost_sum,(w.volume_sum*f.conversion_factor)::float8 sales_sum,
  (w.loss_sum*f.conversion_factor)::float8 loss_sum,
  (w.price_sum*f.conversion_factor)::float8 price_numerator,w.price_count,
  NULL::text rede,NULL::text bandeira,NULL::text uf,NULL::text cidade,
  NULL::text tipo_local,NULL::text loja,NULL::text regiao,NULL::text tp_activity_level,
  NULL::text activity_level,NULL::text item,NULL::text descricao_marca,
  NULL::text hierarquia_1,NULL::text hierarquia_2,NULL::text hierarquia_3
FROM weekly w JOIN factors f USING(data,id_customer)
""".strip()
    default = """
WITH ranked AS (
  SELECT d.*,DENSE_RANK() OVER (
    PARTITION BY id_customer,nm_measure ORDER BY cd_week DESC
  ) week_rank
  FROM gold.nr_panorama_sales_weekly_default d
)
SELECT * FROM ranked WHERE week_rank<=13
""".strip()
    return (
        f"{{% set has_dimension_filter = {checks} %}}\n"
        "{% if has_dimension_filter %}\n" + detail + "\n"
        "{% else %}\n" + default + "\n{% endif %}"
    )


def monthly_sales_semantic_sql() -> str:
    """Monthly Sell Out with filters applied before the literal DAX fallback."""
    checks = " or ".join(f"get_filters('{c}')" for c in WEEKLY_FILTER_COLUMNS)
    predicates = _jinja_filter_predicates("h")
    detail = f"""
WITH filtered AS (
  SELECT h.* FROM gold.nr_overview_history h WHERE 1=1
{predicates}
), monthly AS (
  SELECT data,id_customer,
    SUM(COALESCE(faturamento,0))::float8 faturamento_sum,
    SUM(COALESCE(volume_unidades,0))::float8 volume_sum,
    SUM(COALESCE(avg_sales_price,0))::float8 fallback_price_sum,
    COUNT(avg_sales_price)::bigint fallback_price_count,
    SUM(COALESCE(volume_unidades,0)*COALESCE(avg_price_cost,0))::float8 cost_sum
  FROM filtered GROUP BY data,id_customer
), factors AS (
  SELECT f.data,f.id_customer,c.nm_measure,MAX(c.conversion_rate)::float8 conversion_factor
  FROM (SELECT DISTINCT data,id_customer,id_item FROM filtered) f
  JOIN gold.dim_conversao c ON c.id_customer=f.id_customer AND c.id_item::text=f.id_item
  GROUP BY f.data,f.id_customer,c.nm_measure
)
SELECT m.data,m.id_customer,f.nm_measure,
  CASE WHEN m.faturamento_sum>0 THEN m.faturamento_sum
       WHEN f.conversion_factor IS NOT NULL AND m.fallback_price_count>0
       THEN (m.volume_sum*f.conversion_factor)
          *((m.fallback_price_sum/m.fallback_price_count)*f.conversion_factor)
       ELSE NULL END::float8 sellout_sum,
  m.cost_sum,
  NULL::text rede,NULL::text bandeira,NULL::text uf,NULL::text cidade,
  NULL::text tipo_local,NULL::text loja,NULL::text regiao,NULL::text tp_activity_level,
  NULL::text activity_level,NULL::text item,NULL::text descricao_marca,
  NULL::text hierarquia_1,NULL::text hierarquia_2,NULL::text hierarquia_3
FROM monthly m JOIN factors f USING(data,id_customer)
""".strip()
    return (
        f"{{% set has_dimension_filter = {checks} %}}\n"
        "{% if has_dimension_filter %}\n" + detail + "\n"
        "{% else %}\nSELECT * FROM gold.nr_panorama_sales_monthly_default\n{% endif %}"
    )


def weekly_sales_card_semantic_sql() -> str:
    """Single-card dataset: weekly TOP 13 timeline plus monthly summary rows."""
    checks = " or ".join(f"get_filters('{column}')" for column in WEEKLY_FILTER_COLUMNS)
    weekly_predicates = _jinja_filter_predicates("w", "status_item_geral", {
        "rede": "l.rede", "bandeira": "l.bandeira", "uf": "l.uf",
        "cidade": "l.cidade", "tipo_local": "l.tipo_local",
        "loja": "l.loja", "regiao": "l.regiao", "item": "i.item",
        "descricao_marca": "i.descricao_marca", "hierarquia_1": "i.hierarquia_1",
        "hierarquia_2": "i.hierarquia_2", "hierarquia_3": "i.hierarquia_3",
    })
    monthly_predicates = _jinja_filter_predicates("h")
    detail = f"""
WITH weekly_filtered AS (
  SELECT
    w.id_time AS data,w.cd_week,w.id_customer,w.id_item,w.id_location,
    w.volume_unidade AS volume_unidades,w.faturamento,w.qtd_perda_osa,
    w.avg_sales_price,w.avg_price_cost,w.status_item_geral::text AS tp_activity_level,
    l.rede,l.bandeira,l.uf,l.cidade,l.tipo_local,l.loja,l.regiao,
    i.item,i.descricao_marca,i.hierarquia_1,i.hierarquia_2,i.hierarquia_3
  FROM gold.fato_semanal w
  LEFT JOIN gold.dim_local l ON l.id_customer=w.id_customer AND l.id_location=w.id_location
  LEFT JOIN gold.dim_itens i ON i.id_customer=w.id_customer AND i.id_item=w.id_item
  WHERE 1=1
{weekly_predicates}
), ranked_weeks AS (
  SELECT id_customer,data,cd_week,DENSE_RANK() OVER (
    PARTITION BY id_customer ORDER BY cd_week DESC
  ) week_rank
  FROM (SELECT DISTINCT id_customer,data,cd_week FROM weekly_filtered) x
), weekly_scoped AS (
  SELECT f.* FROM weekly_filtered f JOIN ranked_weeks r USING(id_customer,data,cd_week)
  WHERE r.week_rank<=13
), weekly AS (
  SELECT data,id_customer,MAX(cd_week) cd_week,
    SUM(COALESCE(faturamento,0))::float8 faturamento_sum,
    SUM(COALESCE(volume_unidades,0))::float8 volume_sum,
    SUM(COALESCE(avg_sales_price,0))::float8 fallback_price_sum,
    COUNT(avg_sales_price)::bigint fallback_price_count,
    SUM(COALESCE(volume_unidades,0)*COALESCE(avg_price_cost,0))::float8 cost_sum,
    SUM(COALESCE(qtd_perda_osa,0))::float8 loss_sum,
    SUM(COALESCE(avg_sales_price,0)) FILTER (WHERE faturamento>0)::float8 price_sum,
    COUNT(avg_sales_price) FILTER (WHERE faturamento>0)::bigint price_count
  FROM weekly_scoped GROUP BY data,id_customer
), weekly_factors AS (
  SELECT s.data,s.id_customer,c.nm_measure,MAX(c.conversion_rate)::float8 conversion_factor
  FROM (SELECT DISTINCT data,id_customer,id_item FROM weekly_scoped) s
  JOIN gold.dim_conversao c ON c.id_customer=s.id_customer AND c.id_item::text=s.id_item
  GROUP BY s.data,s.id_customer,c.nm_measure
), monthly_filtered AS (
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
{monthly_predicates}
), monthly AS (
  SELECT data,id_customer,
    SUM(COALESCE(faturamento,0))::float8 faturamento_sum,
    SUM(COALESCE(volume_unidades,0))::float8 volume_sum,
    SUM(COALESCE(avg_sales_price,0))::float8 fallback_price_sum,
    COUNT(avg_sales_price)::bigint fallback_price_count,
    SUM(COALESCE(volume_unidades,0)*COALESCE(avg_price_cost,0))::float8 cost_sum,
    SUM(COALESCE(qtd_perda_osa,0))::float8 loss_sum,
    SUM(COALESCE(avg_sales_price,0)) FILTER (WHERE faturamento>0)::float8 price_sum,
    COUNT(avg_sales_price) FILTER (WHERE faturamento>0)::bigint price_count
  FROM monthly_filtered GROUP BY data,id_customer
), monthly_factors AS (
  SELECT f.data,f.id_customer,c.nm_measure,MAX(c.conversion_rate)::float8 conversion_factor
  FROM (SELECT DISTINCT data,id_customer,id_item FROM monthly_filtered) f
  JOIN gold.dim_conversao c ON c.id_customer=f.id_customer AND c.id_item::text=f.id_item
  GROUP BY f.data,f.id_customer,c.nm_measure
)
SELECT
  'timeline'::text row_scope,w.data,w.cd_week,w.id_customer,f.nm_measure,
  CASE WHEN w.faturamento_sum>0 THEN w.faturamento_sum
       WHEN f.conversion_factor IS NOT NULL AND w.fallback_price_count>0
       THEN (w.volume_sum*f.conversion_factor)
          *((w.fallback_price_sum/w.fallback_price_count)*f.conversion_factor)
       ELSE NULL END::float8 sellout_sum,
  w.cost_sum,(w.volume_sum*f.conversion_factor)::float8 sales_sum,
  (w.loss_sum*f.conversion_factor)::float8 loss_sum,
  (w.price_sum*f.conversion_factor)::float8 price_numerator,w.price_count,
  NULL::text rede,NULL::text bandeira,NULL::text uf,NULL::text cidade,
  NULL::text tipo_local,NULL::text loja,NULL::text regiao,NULL::text tp_activity_level,
  NULL::text activity_level,NULL::text item,NULL::text descricao_marca,
  NULL::text hierarquia_1,NULL::text hierarquia_2,NULL::text hierarquia_3
FROM weekly w JOIN weekly_factors f USING(data,id_customer)
UNION ALL
SELECT
  'summary'::text row_scope,m.data,NULL::text cd_week,m.id_customer,f.nm_measure,
  CASE WHEN m.faturamento_sum>0 THEN m.faturamento_sum
       WHEN f.conversion_factor IS NOT NULL AND m.fallback_price_count>0
       THEN (m.volume_sum*f.conversion_factor)
          *((m.fallback_price_sum/m.fallback_price_count)*f.conversion_factor)
       ELSE NULL END::float8 sellout_sum,
  m.cost_sum,(m.volume_sum*f.conversion_factor)::float8 sales_sum,
  (m.loss_sum*f.conversion_factor)::float8 loss_sum,
  (m.price_sum*f.conversion_factor)::float8 price_numerator,m.price_count,
  NULL::text rede,NULL::text bandeira,NULL::text uf,NULL::text cidade,
  NULL::text tipo_local,NULL::text loja,NULL::text regiao,NULL::text tp_activity_level,
  NULL::text activity_level,NULL::text item,NULL::text descricao_marca,
  NULL::text hierarquia_1,NULL::text hierarquia_2,NULL::text hierarquia_3
FROM monthly m JOIN monthly_factors f USING(data,id_customer)
""".strip()
    return (
        f"{{% set has_dimension_filter = {checks} %}}\n"
        "{% if has_dimension_filter %}\n" + detail + "\n"
        "{% else %}\nSELECT * FROM gold.nr_panorama_sales_weekly_card_default\n{% endif %}"
    )


def register_sales_charts(add, monthly_sales, weekly_sales_card, monthly_quantity, Q):
    value_semantics = "direct_average:0:1|direct_average:1:1|markup_blank:0:2"
    quantity_semantics = "direct_average:0:1|direct_sum:1:1|weighted_average:2:2"
    value_measures = [
        metric("Venda sell out", "SUM(sellout_sum)"),
        metric("Venda custo", "SUM(cost_sum)"),
    ]
    weekly_value_measures = [
        metric("Venda sell out semanal", "SUM(sellout_sum)"),
        metric("Venda custo semanal", "SUM(cost_sum)"),
    ]
    quantity_measures = [Q["sales"], Q["loss"], Q["price_num"], Q["price_count"]]
    weekly_quantity_measures = [
        metric("Venda quantidade semanal", "SUM(sales_sum)"),
        metric("Perda OSA semanal", "SUM(loss_sum)"),
        metric("Preço soma semanal", "SUM(price_numerator)"),
        metric("Preço linhas semanal", "SUM(price_count)"),
    ]

    params = custom_params(
        monthly_sales, "Evolutivo de vendas", value_measures, grain="P1M",
        styles="bar|bar|line", formats="currency|currency|percent",
        labels="Sell out Venda|Sell out Custo|Markup",
        metric_semantics=value_semantics, summary_count=3, timeline_limit=13,
    )
    add("sales_value_mensal", monthly_sales, "Evolutivo de vendas — Valor mensal", params)

    params = custom_params(
        weekly_sales_card, "Evolutivo de vendas", weekly_value_measures, grain="P1W",
        styles="bar|bar|line", formats="currency|currency|percent",
        labels="Sell out Venda|Sell out Custo|Markup",
        metric_semantics=value_semantics, summary_count=3, timeline_limit=13,
        summary_query_scope="summary", timeline_query_scope="timeline",
    )
    add("sales_value_semanal", weekly_sales_card, "Evolutivo de vendas — Valor semanal", params)

    params = custom_params(
        monthly_quantity, "Evolutivo de vendas", quantity_measures, grain="P1M",
        styles="bar|bar|line", formats="quantity|quantity|currency",
        labels="Sell out Volume|Perda OSA|Preço Médio",
        metric_semantics=quantity_semantics, summary_count=3, timeline_limit=13,
    )
    add("sales_quantity_mensal", monthly_quantity, "Evolutivo de vendas — Quantidade mensal", params)

    params = custom_params(
        weekly_sales_card, "Evolutivo de vendas", weekly_quantity_measures, grain="P1W",
        styles="bar|bar|line", formats="quantity|quantity|currency",
        labels="Sell out Volume|Perda OSA|Preço Médio",
        metric_semantics=quantity_semantics, summary_count=3, timeline_limit=13,
        summary_query_scope="summary", timeline_query_scope="timeline",
    )
    add("sales_quantity_semanal", weekly_sales_card, "Evolutivo de vendas — Quantidade semanal", params)
