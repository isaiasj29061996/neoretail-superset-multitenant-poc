"""Create the NeoRetail Panorama Industria dashboard in Superset metadata.

The script creates physical-dataset metadata, charts and dashboard layout. The
serving marts are materialized before this script runs.
"""
from __future__ import annotations

import json
import uuid

from sqlalchemy import text
from superset.app import create_app

from bootstrap_overview import (
    HISTORY_SQL, M, _jinja_filter_predicates, metric, overview_native_filters,
    upsert_dataset,
)
from bootstrap_overview_quantity import Q, quantity_semantic_sql


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

WEEKLY_FILTER_COLUMNS = (
    "rede", "bandeira", "uf", "cidade", "tipo_local", "loja", "regiao",
    "tp_activity_level", "activity_level", "item", "descricao_marca",
    "hierarquia_1", "hierarquia_2", "hierarquia_3",
)


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
  SELECT h.* FROM gold.nr_overview_history h WHERE 1=1
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



def monthly_inventory_semantic_sql() -> str:
    """Certified monthly Stock/Giro/ROI/OSA components over the serving mart."""
    checks = " or ".join(f"get_filters('{column}')" for column in WEEKLY_FILTER_COLUMNS)
    predicates = _jinja_filter_predicates("h")
    detail = f"""
WITH filtered AS (
  SELECT h.* FROM gold.nr_overview_history h WHERE 1=1
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
    monthly_predicates = _jinja_filter_predicates("h")
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
  SELECT h.* FROM gold.nr_overview_history h WHERE 1=1
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


def monthly_gap_semantic_sql() -> str:
    """Power BI LASTNONBLANK TVD/IVD at monthly grain."""
    checks = " or ".join(f"get_filters('{column}')" for column in WEEKLY_FILTER_COLUMNS)
    predicates = _jinja_filter_predicates("o")
    detail = f"""
WITH filtered AS (
  SELECT o.* FROM gold.nr_panorama_opportunities o WHERE 1=1
{predicates}
), daily AS (
  SELECT
    id_customer,data,
    SUM(tvd_simplificado)::float8 AS tvd,
    SUM(ivd_simplificado)::float8 AS ivd
  FROM filtered
  GROUP BY id_customer,data
), tagged AS (
  SELECT d.*,DATE_TRUNC('month',data)::date AS period_start
  FROM daily d
), anchors AS (
  SELECT
    id_customer,period_start,
    MAX(data) FILTER (WHERE tvd IS NOT NULL) AS tvd_date,
    MAX(data) FILTER (WHERE ivd IS NOT NULL) AS ivd_date
  FROM tagged
  GROUP BY id_customer,period_start
)
SELECT
  a.period_start AS data,a.id_customer,
  tvd.tvd,ivd.ivd,
  NULL::text rede,NULL::text bandeira,NULL::text uf,NULL::text cidade,
  NULL::text tipo_local,NULL::text loja,NULL::text regiao,
  NULL::text tp_activity_level,NULL::text activity_level,NULL::text item,
  NULL::text descricao_marca,NULL::text hierarquia_1,NULL::text hierarquia_2,
  NULL::text hierarquia_3
FROM anchors a
LEFT JOIN daily tvd ON tvd.id_customer=a.id_customer AND tvd.data=a.tvd_date
LEFT JOIN daily ivd ON ivd.id_customer=a.id_customer AND ivd.data=a.ivd_date
""".strip()
    return (
        f"{{% set has_dimension_filter = {checks} %}}\n"
        "{% if has_dimension_filter %}\n" + detail + "\n"
        "{% else %}\nSELECT * FROM gold.nr_panorama_gap_monthly_default\n{% endif %}"
    )


def weekly_gap_card_semantic_sql() -> str:
    """TOP-13 weekly LASTNONBLANK TVD/IVD plus monthly summary rows."""
    checks = " or ".join(f"get_filters('{column}')" for column in WEEKLY_FILTER_COLUMNS)
    predicates = _jinja_filter_predicates("o")
    detail = f"""
WITH filtered AS (
  SELECT o.* FROM gold.nr_panorama_opportunities o WHERE 1=1
{predicates}
), daily AS (
  SELECT
    id_customer,data,
    SUM(tvd_simplificado)::float8 AS tvd,
    SUM(ivd_simplificado)::float8 AS ivd
  FROM filtered
  GROUP BY id_customer,data
), weekly_tagged AS (
  SELECT d.*,DATE_TRUNC('week',data)::date AS period_start FROM daily d
), weekly_anchors AS (
  SELECT
    id_customer,period_start,
    MAX(data) FILTER (WHERE tvd IS NOT NULL) AS tvd_date,
    MAX(data) FILTER (WHERE ivd IS NOT NULL) AS ivd_date
  FROM weekly_tagged
  GROUP BY id_customer,period_start
), weekly_values AS (
  SELECT
    a.id_customer,a.period_start AS data,tvd.tvd,ivd.ivd,
    DENSE_RANK() OVER (
      PARTITION BY a.id_customer ORDER BY a.period_start DESC
    ) AS week_rank
  FROM weekly_anchors a
  LEFT JOIN daily tvd ON tvd.id_customer=a.id_customer AND tvd.data=a.tvd_date
  LEFT JOIN daily ivd ON ivd.id_customer=a.id_customer AND ivd.data=a.ivd_date
), monthly_tagged AS (
  SELECT d.*,DATE_TRUNC('month',data)::date AS period_start FROM daily d
), monthly_anchors AS (
  SELECT
    id_customer,period_start,
    MAX(data) FILTER (WHERE tvd IS NOT NULL) AS tvd_date,
    MAX(data) FILTER (WHERE ivd IS NOT NULL) AS ivd_date
  FROM monthly_tagged
  GROUP BY id_customer,period_start
)
SELECT
  'timeline'::text AS row_scope,
  w.data,w.id_customer,w.tvd,w.ivd,
  NULL::text rede,NULL::text bandeira,NULL::text uf,NULL::text cidade,
  NULL::text tipo_local,NULL::text loja,NULL::text regiao,
  NULL::text tp_activity_level,NULL::text activity_level,NULL::text item,
  NULL::text descricao_marca,NULL::text hierarquia_1,NULL::text hierarquia_2,
  NULL::text hierarquia_3
FROM weekly_values w
WHERE w.week_rank<=13

UNION ALL

SELECT
  'summary'::text AS row_scope,
  a.period_start AS data,a.id_customer,tvd.tvd,ivd.ivd,
  NULL::text rede,NULL::text bandeira,NULL::text uf,NULL::text cidade,
  NULL::text tipo_local,NULL::text loja,NULL::text regiao,
  NULL::text tp_activity_level,NULL::text activity_level,NULL::text item,
  NULL::text descricao_marca,NULL::text hierarquia_1,NULL::text hierarquia_2,
  NULL::text hierarquia_3
FROM monthly_anchors a
LEFT JOIN daily tvd ON tvd.id_customer=a.id_customer AND tvd.data=a.tvd_date
LEFT JOIN daily ivd ON ivd.id_customer=a.id_customer AND ivd.data=a.ivd_date
""".strip()
    return (
        f"{{% set has_dimension_filter = {checks} %}}\n"
        "{% if has_dimension_filter %}\n" + detail + "\n"
        "{% else %}\nSELECT * FROM gold.nr_panorama_gap_weekly_card_default\n{% endif %}"
    )


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


def custom_params(dataset, title, metrics, *, grain="P1M", styles="bar|bar|line", formats="number", groupby=None, variant="panorama", row_limit=10000, labels=None, **extra):
    params = {
        "datasource": f"{dataset.id}__table", "viz_type": "neoretail-kpi-card",
        "x_axis": "data", "time_grain_sqla": grain, "time_range": "No filter",
        "metrics": metrics, "row_limit": row_limit, "card_title": title,
        "card_variant": variant, "help_text": title, "metric_labels": labels or "|".join(m["label"] for m in metrics),
        "metric_formats": formats, "metric_directions": "higher", "chart_styles": styles,
        "accent_color": "#7C4AD9", "show_tasks": False, "adhoc_filters": [], "groupby": groupby or [],
    }
    params.update(extra)
    return params


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
                (period.title(), [[*chart] if isinstance(chart, (list, tuple)) else [chart]])
                for period, chart in periods
            ], height)
        return outer_id

    def row(self, parent, parents, charts, height):
        row_id = self._id("ROW")
        children = []
        self.nodes[row_id] = {"id": row_id, "type": "ROW", "parents": parents, "children": children, "meta": {"background": "BACKGROUND_TRANSPARENT"}}
        self.nodes[parent]["children"].append(row_id)
        widths = [3, 9] if len(charts) == 2 and "Resumo" in charts[0].slice_name else [max(1, 12 // len(charts))] * len(charts)
        for chart, width in zip(charts, widths):
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
        weekly = upsert_dataset(
            db.session, SqlaTable, database, "nr_panorama_weekly_interactive",
            sql=weekly_semantic_sql(),
        )
        weekly_sales = upsert_dataset(
            db.session, SqlaTable, database, "nr_panorama_sales_weekly_interactive",
            sql=weekly_sales_semantic_sql(),
        )
        weekly_sales_card = upsert_dataset(
            db.session, SqlaTable, database, "nr_panorama_sales_weekly_card_interactive",
            sql=weekly_sales_card_semantic_sql(),
        )
        monthly_sales = upsert_dataset(
            db.session, SqlaTable, database, "nr_panorama_sales_monthly_interactive",
            sql=monthly_sales_semantic_sql(),
        )
        monthly_quantity = upsert_dataset(
            db.session, SqlaTable, database, "nr_overview_quantity_interactive",
            sql=quantity_semantic_sql(),
        )
        monthly_stock = upsert_dataset(
            db.session, SqlaTable, database, "nr_panorama_stock_monthly_interactive",
            sql=monthly_stock_semantic_sql(),
        )
        weekly_stock_card = upsert_dataset(
            db.session, SqlaTable, database, "nr_panorama_stock_weekly_card_interactive",
            sql=weekly_stock_card_semantic_sql(),
        )
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
        filter_options = upsert_dataset(
            db.session, SqlaTable, database, "nr_filter_options", table_name="nr_filter_options"
        )
        conversion_options = upsert_dataset(
            db.session, SqlaTable, database, "nr_conversion_options",
            table_name="nr_conversion_options",
        )
        with database.get_sqla_engine() as engine:
            with engine.connect() as connection:
                weekly_max_date = connection.execute(
                    text("SELECT MAX(data) FROM gold.nr_panorama_weekly")
                ).scalar_one()
        weekly_recent = [sql_filter(
            f"data >= DATE '{weekly_max_date.isoformat()}' - INTERVAL '12 weeks'"
        )] if weekly_max_date else []

        charts = {}
        def add(key, dataset, title, params, viz="neoretail-kpi-card"):
            charts[key] = upsert_chart(db.session, Slice, dataset, f"[Panorama] {title}", params, viz)

        periods = (("mensal", history, "P1M"), ("semanal", weekly, "P1W"))
        for period, dataset, grain in periods:
            metrics = WEEKLY_P if period == "semanal" else P
            giro_roi = [metrics["roi"], metrics["coverage"], metrics["giro"]]
            osa = [metrics["osa"], metrics["rup"], metrics["isv"]]
            giro_params = custom_params(dataset, "Evolutivo de estoque", giro_roi, grain=grain, styles="bar|line|line", formats="percent|number|number")
            osa_params = custom_params(dataset, "Evolutivo de estoque", osa, grain=grain, styles="line|line|line", formats="percent|percent|percent")
            for params in (giro_params, osa_params):
                params["adhoc_filters"] = list(weekly_recent if period == "semanal" else [])
            add(f"giro_roi_{period}", dataset, f"Evolutivo de estoque — Giro e ROI {period}", giro_params)
            add(f"osa_{period}", dataset, f"Evolutivo de estoque — OSA {period}", osa_params)

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

        # Panorama > Evolutivo de estoque > Estoque.
        # Power BI contract:
        #   Estoque Preço Custo = SUMX(ESTOQUE_MEDIO * AVG_PRICE_COST)
        #   Estoque Quantidade = SUM(ESTOQUE_UNIDADES) * selected conversion factor
        #   Cost U3M averages the three-month context; quantity U3M preserves
        #   [Estoque qtd]'s MaxDataMes behavior and divides that last month by 3.
        # stock_bundle mirrors the literal DAX asymmetry:
        # cost U3M = SUM(three months) / 3, while [Estoque qtd] first keeps
        # only MaxDataMes inside U3M and the BN measure then divides it by 3.
        stock_measures = [
            metric("Estoque preço custo", "SUM(stock_cost_sum)"),
            metric("Estoque quantidade", "SUM(stock_qty_sum)"),
        ]

        params = custom_params(
            monthly_stock,
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
        add("stock_mensal", monthly_stock, "Evolutivo de estoque — Estoque mensal", params)

        params = custom_params(
            weekly_stock_card,
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
        add("stock_semanal", weekly_stock_card, "Evolutivo de estoque — Estoque semanal", params)

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
            ("Quantidade", [(period, charts[f"sales_quantity_{period}"]) for period in ("mensal", "semanal")]),
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
        filter_targets = {column: filter_options.id for column in WEEKLY_FILTER_COLUMNS}
        filter_targets["nm_measure"] = conversion_options.id
        dashboard.json_metadata = json.dumps({"timed_refresh_immune_slices": [], "expanded_slices": {}, "refresh_frequency": 0, "color_scheme": "supersetColors", "native_filter_configuration": overview_native_filters([history.id, weekly.id, weekly_sales.id, weekly_sales_card.id, monthly_sales.id, monthly_quantity.id, monthly_stock.id, weekly_stock_card.id], filter_targets), "filter_bar_orientation": "HORIZONTAL"}, ensure_ascii=False)
        dashboard.slices = list(charts.values())
        db.session.commit()
        print(json.dumps({"dashboard_id": dashboard.id, "slug": dashboard.slug, "industry": {"id_customer": 142, "label": "AMBEV"}, "datasets": {"history": history.id, "weekly": weekly.id, "monthly_stock": monthly_stock.id, "weekly_stock_card": weekly_stock_card.id, "latest": latest.id, "mart": mart.id, "opportunities": opportunities.id, "opportunities_latest": opportunities_latest.id, "gap_periodic": gap_periodic.id}, "chart_count": len(charts)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
