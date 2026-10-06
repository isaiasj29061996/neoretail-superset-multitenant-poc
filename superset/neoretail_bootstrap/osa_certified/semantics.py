"""Certified OSA SQL and metrics, preserved without formula changes."""
from __future__ import annotations
from neoretail_bootstrap.core.filters import _jinja_filter_predicates
from neoretail_bootstrap.core.metrics import metric
from .filters import DIMENSION_OVERRIDES, _dimension_nulls, _measure_filter

PERIODS = (
    ("MTD", 1),
    ("Mês Anterior", 2),
    ("U3M", 3),
    ("YTD", 5),
)


def monthly_overview_sql() -> str:
    """Monthly OSA timeline using the exact Power BI fact families."""
    history_predicates = _jinja_filter_predicates(
        "h", "tp_activity_level", DIMENSION_OVERRIDES,
    )
    cause_overrides = {
        **DIMENSION_OVERRIDES,
        "tp_activity_level": "o.max_tp_activity_level",
    }
    cause_predicates = _jinja_filter_predicates(
        "c", "o.max_tp_activity_level", cause_overrides,
    )
    dims = _dimension_nulls()
    measure_filter = _measure_filter("m")
    return f"""
WITH history_filtered AS (
  SELECT
    h.mes_ano::date AS data,h.id_customer,h.id_item,h.id_location,
    h.volume_unidades,h.faturamento,h.qtd_perda_osa,
    h.qtd_problemas_osa,h.qtd_item_ativo_osa,h.avg_sales_price,
    h.tp_activity_level
  FROM gold.fato_historico h
  LEFT JOIN gold.dim_local l
    ON l.id_customer=h.id_customer AND l.id_location=h.id_location
  LEFT JOIN gold.dim_itens i
    ON i.id_customer=h.id_customer AND i.id_item=h.id_item
  WHERE 1=1
{history_predicates}
), cause_filtered AS (
  SELECT
    c.data,c.id_customer,c.id_item,c.id_location,
    c.qtd_perda_osa,c.vl_perda_osa,c.qtd_problemas_osa,
    c.qtd_itens_ativos,c.volume_unidades,c.faturamento,c.preco_medio
  FROM gold.fato_mensal_causa_osa c
  LEFT JOIN gold.dim_local l
    ON l.id_customer=c.id_customer AND l.id_location=c.id_location
  LEFT JOIN gold.dim_itens i
    ON i.id_customer=c.id_customer AND i.id_item=c.id_item
  LEFT JOIN gold.calculo_oportunidades o
    ON o.id_customer=c.id_customer
   AND o.id_location::text=c.id_location::text
   AND o.id_item::text=c.id_item::text
  WHERE 1=1
{cause_predicates}
), measures AS (
  SELECT DISTINCT id_customer,nm_measure
  FROM gold.nr_conversion_options m
  WHERE 1=1
{measure_filter}
), hist_month AS (
  SELECT
    h.data,h.id_customer,
    SUM(COALESCE(h.faturamento,0))::float8 AS faturamento_sum,
    SUM(COALESCE(h.volume_unidades,0))::float8 AS volume_sum,
    SUM(COALESCE(h.qtd_perda_osa,0))::float8 AS loss_qty_sum,
    SUM(COALESCE(h.qtd_problemas_osa,0))::float8 AS problem_sum,
    SUM(COALESCE(h.qtd_item_ativo_osa,0))::float8 AS active_sum,
    SUM(h.avg_sales_price)::float8 AS sales_price_sum,
    COUNT(h.avg_sales_price)::bigint AS sales_price_count
  FROM history_filtered h
  GROUP BY h.data,h.id_customer
), cause_month AS (
  SELECT
    c.data,c.id_customer,
    SUM(COALESCE(c.qtd_perda_osa,0))::float8 AS loss_qty_sum,
    SUM(COALESCE(c.vl_perda_osa,0))::float8 AS loss_value_sum,
    SUM(COALESCE(c.qtd_problemas_osa,0))::float8 AS problem_sum,
    SUM(COALESCE(c.qtd_itens_ativos,0))::float8 AS active_sum,
    SUM(COALESCE(c.volume_unidades,0))::float8 AS volume_sum,
    SUM(COALESCE(c.faturamento,0))::float8 AS faturamento_sum,
    SUM(COALESCE(c.preco_medio,0))::float8 AS price_sum
  FROM cause_filtered c
  GROUP BY c.data,c.id_customer
), hist_factor AS (
  SELECT
    h.data,h.id_customer,m.nm_measure,
    COALESCE(MAX(cv.conversion_rate),
      CASE WHEN m.nm_measure='valor' THEN 1.0 END)::float8 AS conversion_factor
  FROM (SELECT DISTINCT data,id_customer,id_item FROM history_filtered) h
  JOIN measures m ON m.id_customer=h.id_customer
  LEFT JOIN gold.dim_conversao cv
    ON cv.id_customer=h.id_customer
   AND cv.id_item::text=h.id_item::text
   AND cv.nm_measure=m.nm_measure
  GROUP BY h.data,h.id_customer,m.nm_measure
), cause_factor AS (
  SELECT
    c.data,c.id_customer,m.nm_measure,
    COALESCE(MAX(cv.conversion_rate),
      CASE WHEN m.nm_measure='valor' THEN 1.0 END)::float8 AS conversion_factor
  FROM (SELECT DISTINCT data,id_customer,id_item FROM cause_filtered) c
  JOIN measures m ON m.id_customer=c.id_customer
  LEFT JOIN gold.dim_conversao cv
    ON cv.id_customer=c.id_customer
   AND cv.id_item::text=c.id_item::text
   AND cv.nm_measure=m.nm_measure
  GROUP BY c.data,c.id_customer,m.nm_measure
)
SELECT
  h.data,h.id_customer,hf.nm_measure,
  CASE
    WHEN h.faturamento_sum>0 THEN h.faturamento_sum
    WHEN hf.conversion_factor IS NOT NULL AND h.sales_price_count>0
      THEN (h.volume_sum*hf.conversion_factor)
         *((h.sales_price_sum/h.sales_price_count)*hf.conversion_factor)
    ELSE NULL
  END::float8 AS sellout_value,
  c.loss_value_sum::float8 AS loss_value,
  CASE
    WHEN c.faturamento_sum>0
      THEN 100.0*c.loss_value_sum/NULLIF(c.faturamento_sum,0)
    ELSE 100.0*c.loss_value_sum
      / NULLIF(c.volume_sum*c.price_sum,0)
  END::float8 AS loss_value_percent,
  (100.0*(1-h.problem_sum/NULLIF(h.active_sum,0)))::float8 AS osa_percent,
  (c.volume_sum*cf.conversion_factor)::float8 AS sales_qty,
  (c.loss_qty_sum*cf.conversion_factor)::float8 AS loss_qty,
  CASE
    WHEN hf.conversion_factor IS NULL THEN NULL
    ELSE 100.0*(h.loss_qty_sum*hf.conversion_factor)
      / NULLIF(h.volume_sum*hf.conversion_factor,0)
  END::float8 AS loss_qty_percent,
  {dims}
FROM hist_month h
JOIN hist_factor hf USING(data,id_customer)
LEFT JOIN cause_month c USING(data,id_customer)
LEFT JOIN cause_factor cf
  ON cf.data=h.data AND cf.id_customer=h.id_customer
 AND cf.nm_measure=hf.nm_measure
""".strip()


def weekly_overview_sql() -> str:
    """Weekly OSA timeline; the latest 13 filtered CD_WEEK values are returned."""
    weekly_overrides = {
        **DIMENSION_OVERRIDES,
        "tp_activity_level": "o.max_tp_activity_level",
    }
    weekly_predicates = _jinja_filter_predicates(
        "w", "o.max_tp_activity_level", weekly_overrides,
    )
    opportunity_overrides = {
        **DIMENSION_OVERRIDES,
        "tp_activity_level": "o.max_tp_activity_level",
    }
    opportunity_predicates = _jinja_filter_predicates(
        "o", "o.max_tp_activity_level", opportunity_overrides,
    )
    dims = _dimension_nulls()
    measure_filter = _measure_filter("m")
    return f"""
WITH weekly_filtered AS (
  SELECT
    w.id_time::date AS data,w.cd_week,w.id_customer,w.id_item,w.id_location,
    w.volume_unidade,w.faturamento,w.qtd_perda_osa,w.qtd_problemas_osa,
    w.qtd_item_ativo_osa,w.avg_sales_price,w.avg_price_cost
  FROM gold.fato_semanal w
  LEFT JOIN gold.dim_local l
    ON l.id_customer=w.id_customer AND l.id_location=w.id_location
  LEFT JOIN gold.dim_itens i
    ON i.id_customer=w.id_customer AND i.id_item=w.id_item
  LEFT JOIN gold.calculo_oportunidades o
    ON o.id_customer=w.id_customer
   AND o.id_location::text=w.id_location::text
   AND o.id_item::text=w.id_item::text
  WHERE 1=1
{weekly_predicates}
), ranked_weeks AS (
  SELECT id_customer,cd_week,MAX(data) AS data,
    DENSE_RANK() OVER (
      PARTITION BY id_customer ORDER BY cd_week DESC
    ) AS week_rank
  FROM weekly_filtered
  GROUP BY id_customer,cd_week
), scoped AS (
  SELECT w.*
  FROM weekly_filtered w
  JOIN ranked_weeks r USING(id_customer,cd_week)
  WHERE r.week_rank<=13
), opportunities_filtered AS (
  SELECT o.id_customer,o.id_item,o.id_location,o.demanda_media
  FROM gold.calculo_oportunidades o
  LEFT JOIN gold.dim_local l
    ON l.id_customer=o.id_customer AND l.id_location=o.id_location
  LEFT JOIN gold.dim_itens i
    ON i.id_customer=o.id_customer AND i.id_item=o.id_item
  WHERE COALESCE(o.qtd_item_ativo_osa_m0,0)>0
{opportunity_predicates}
), measures AS (
  SELECT DISTINCT id_customer,nm_measure
  FROM gold.nr_conversion_options m
  WHERE 1=1
{measure_filter}
), weekly AS (
  SELECT
    s.data,s.cd_week,s.id_customer,
    SUM(COALESCE(s.faturamento,0))::float8 AS faturamento_sum,
    SUM(COALESCE(s.volume_unidade,0))::float8 AS volume_sum,
    SUM(COALESCE(s.qtd_perda_osa,0))::float8 AS loss_qty_sum,
    SUM(COALESCE(s.qtd_problemas_osa,0))::float8 AS problem_sum,
    SUM(COALESCE(s.qtd_item_ativo_osa,0))::float8 AS active_sum,
    AVG(s.avg_sales_price)::float8 AS avg_sales_price,
    AVG(s.avg_price_cost)::float8 AS avg_price_cost
  FROM scoped s
  GROUP BY s.data,s.cd_week,s.id_customer
), factor AS (
  SELECT
    s.data,s.id_customer,m.nm_measure,
    COALESCE(MAX(cv.conversion_rate),
      CASE WHEN m.nm_measure='valor' THEN 1.0 END)::float8 AS conversion_factor
  FROM (SELECT DISTINCT data,id_customer,id_item FROM scoped) s
  JOIN measures m ON m.id_customer=s.id_customer
  LEFT JOIN gold.dim_conversao cv
    ON cv.id_customer=s.id_customer
   AND cv.id_item::text=s.id_item::text
   AND cv.nm_measure=m.nm_measure
  GROUP BY s.data,s.id_customer,m.nm_measure
), week_locations AS (
  SELECT DISTINCT data,id_customer,id_location
  FROM scoped
), demand AS (
  SELECT
    wl.data,wl.id_customer,
    SUM(COALESCE(o.demanda_media,0))::float8 AS demand_sum
  FROM week_locations wl
  JOIN opportunities_filtered o
    ON o.id_customer=wl.id_customer
   AND o.id_location::text=wl.id_location::text
  GROUP BY wl.data,wl.id_customer
)
SELECT
  w.data,w.cd_week,w.id_customer,f.nm_measure,
  CASE
    WHEN w.faturamento_sum>0 THEN w.faturamento_sum
    WHEN f.conversion_factor IS NOT NULL AND w.avg_sales_price IS NOT NULL
      THEN (w.volume_sum*f.conversion_factor)
         *(w.avg_sales_price*f.conversion_factor)
    ELSE NULL
  END::float8 AS sellout_value,
  (w.loss_qty_sum*w.avg_price_cost)::float8 AS loss_value,
  CASE
    WHEN w.faturamento_sum>0
      THEN 100.0*(w.loss_qty_sum*w.avg_price_cost)
        / NULLIF(w.faturamento_sum,0)
    ELSE 100.0*(w.loss_qty_sum*w.avg_price_cost)
      / NULLIF(w.volume_sum*w.avg_price_cost,0)
  END::float8 AS loss_value_percent,
  (100.0*(1-w.problem_sum/NULLIF(w.active_sum,0)))::float8 AS osa_percent,
  (w.volume_sum*f.conversion_factor)::float8 AS sales_qty,
  (w.loss_qty_sum*f.conversion_factor)::float8 AS loss_qty,
  (100.0*w.loss_qty_sum/NULLIF(d.demand_sum*30.0,0))::float8 AS loss_qty_percent,
  {dims}
FROM weekly w
JOIN factor f USING(data,id_customer)
LEFT JOIN demand d USING(data,id_customer)
ORDER BY w.data
""".strip()


def cause_period_sql() -> str:
    """Monthly cause rows expanded into the Power BI period selector contexts."""
    overrides = {
        **DIMENSION_OVERRIDES,
        "tp_activity_level": "o.max_tp_activity_level",
    }
    predicates = _jinja_filter_predicates(
        "c", "o.max_tp_activity_level", overrides,
    )
    measure_filter = _measure_filter("m")
    return f"""
WITH latest AS (
  SELECT id_customer,MAX(data)::date AS latest_data
  FROM gold.fato_mensal_causa_osa
  GROUP BY id_customer
), measures AS (
  SELECT DISTINCT id_customer,nm_measure
  FROM gold.nr_conversion_options m
  WHERE 1=1
{measure_filter}
), base AS (
  SELECT
    c.data,c.id_customer,c.id_item,c.id_location,
    c.motivo_osa,c.causa_osa,c.qtd_perda_osa,c.vl_perda_osa,
    c.qtd_problemas_osa,c.qtd_itens_ativos,c.volume_unidades,
    c.faturamento,c.preco_medio,
    l.rede,l.bandeira,l.uf,l.cidade,l.tipo_local,l.loja,l.regiao,
    i.item,i.descricao_marca,i.hierarquia_1,i.hierarquia_2,i.hierarquia_3,
    o.max_tp_activity_level::text AS tp_activity_level
  FROM gold.fato_mensal_causa_osa c
  LEFT JOIN gold.dim_local l
    ON l.id_customer=c.id_customer AND l.id_location=c.id_location
  LEFT JOIN gold.dim_itens i
    ON i.id_customer=c.id_customer AND i.id_item=c.id_item
  LEFT JOIN gold.calculo_oportunidades o
    ON o.id_customer=c.id_customer
   AND o.id_location::text=c.id_location::text
   AND o.id_item::text=c.id_item::text
  WHERE 1=1
{predicates}
), expanded AS (
  SELECT b.*,p.osa_period,p.osa_period_order
  FROM base b
  JOIN latest x USING(id_customer)
  CROSS JOIN LATERAL (
    SELECT 'MTD'::text AS osa_period,1::int AS osa_period_order
      WHERE DATE_TRUNC('month',b.data)=DATE_TRUNC('month',x.latest_data)
    UNION ALL
    SELECT 'Mês Anterior',2
      WHERE DATE_TRUNC('month',b.data)=DATE_TRUNC('month',x.latest_data-INTERVAL '1 month')
    UNION ALL
    SELECT 'U3M',3
      WHERE b.data>=DATE_TRUNC('month',x.latest_data)-INTERVAL '2 months'
        AND b.data<=x.latest_data
    UNION ALL
    SELECT 'YTD',5
      WHERE EXTRACT(YEAR FROM b.data)=EXTRACT(YEAR FROM x.latest_data)
  ) p
), converted AS (
  SELECT
    e.*,m.nm_measure,
    COALESCE(cv.conversion_rate,
      CASE WHEN m.nm_measure='valor' THEN 1.0 END)::float8 AS conversion_rate
  FROM expanded e
  JOIN measures m ON m.id_customer=e.id_customer
  LEFT JOIN gold.dim_conversao cv
    ON cv.id_customer=e.id_customer
   AND cv.id_item::text=e.id_item::text
   AND cv.nm_measure=m.nm_measure
)
SELECT * FROM converted
""".strip()


def period_options_sql() -> str:
    rows = ",".join(f"('{label}',{order})" for label,order in PERIODS)
    return f"""
SELECT c.id_customer,p.osa_period,p.osa_period_order
FROM (
  SELECT DISTINCT id_customer FROM gold.nr_filter_options
) c
CROSS JOIN (VALUES {rows}) AS p(osa_period,osa_period_order)
""".strip()


TOP_VALUE_METRICS = [
    metric("Sell Out Venda", "SUM(sellout_value)"),
    metric("Perda R$ OSA", "SUM(loss_value)"),
    metric("% Perda", "AVG(loss_value_percent)"),
    metric("%OSA", "AVG(osa_percent)"),
]


TOP_QTY_METRICS = [
    metric("Venda qtd", "SUM(sales_qty)"),
    metric("Perda OSA qtd", "SUM(loss_qty)"),
    metric("% Perda", "AVG(loss_qty_percent)"),
    metric("%OSA", "AVG(osa_percent)"),
]


CAUSE_VALUE = metric("Perda R$ OSA", "SUM(vl_perda_osa)")


CAUSE_QTY = metric(
    "Perda OSA qtd",
    "SUM(qtd_perda_osa) * MAX(conversion_rate)",
)
