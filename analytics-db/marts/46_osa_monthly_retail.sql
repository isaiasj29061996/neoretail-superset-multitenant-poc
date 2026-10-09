-- Exact monthly OSA context for ONE selected retail network. Multiple networks,
-- NOT IN and additional dimensions keep the detailed virtual SQL: averaging
-- already-calculated percentages across networks would change the formula.
BEGIN;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_osa_monthly_retail;
CREATE MATERIALIZED VIEW gold.nr_osa_monthly_retail AS
WITH measures AS (
    SELECT DISTINCT id_customer,nm_measure FROM gold.nr_conversion_options
), hist_month AS (
    SELECT h.mes_ano::date AS data,h.id_customer,l.rede,
        SUM(COALESCE(h.faturamento,0))::float8 AS faturamento_sum,
        SUM(COALESCE(h.volume_unidades,0))::float8 AS volume_sum,
        SUM(COALESCE(h.qtd_perda_osa,0))::float8 AS loss_qty_sum,
        SUM(COALESCE(h.qtd_problemas_osa,0))::float8 AS problem_sum,
        SUM(COALESCE(h.qtd_item_ativo_osa,0))::float8 AS active_sum,
        SUM(h.avg_sales_price)::float8 AS sales_price_sum,
        COUNT(h.avg_sales_price)::bigint AS sales_price_count
    FROM gold.fato_historico h
    JOIN gold.dim_local l ON l.id_customer=h.id_customer AND l.id_location=h.id_location
    GROUP BY h.mes_ano::date,h.id_customer,l.rede
), cause_month AS (
    SELECT c.data::date AS data,c.id_customer,l.rede,
        SUM(COALESCE(c.qtd_perda_osa,0))::float8 AS loss_qty_sum,
        SUM(COALESCE(c.vl_perda_osa,0))::float8 AS loss_value_sum,
        SUM(COALESCE(c.qtd_problemas_osa,0))::float8 AS problem_sum,
        SUM(COALESCE(c.qtd_itens_ativos,0))::float8 AS active_sum,
        SUM(COALESCE(c.volume_unidades,0))::float8 AS volume_sum,
        SUM(COALESCE(c.faturamento,0))::float8 AS faturamento_sum,
        SUM(COALESCE(c.preco_medio,0))::float8 AS price_sum
    FROM gold.fato_mensal_causa_osa c
    JOIN gold.dim_local l ON l.id_customer=c.id_customer AND l.id_location=c.id_location
    GROUP BY c.data::date,c.id_customer,l.rede
), hist_keys AS (
    SELECT DISTINCT h.mes_ano::date AS data,h.id_customer,l.rede,h.id_item
    FROM gold.fato_historico h
    JOIN gold.dim_local l ON l.id_customer=h.id_customer AND l.id_location=h.id_location
), cause_keys AS (
    SELECT DISTINCT c.data::date AS data,c.id_customer,l.rede,c.id_item
    FROM gold.fato_mensal_causa_osa c
    JOIN gold.dim_local l ON l.id_customer=c.id_customer AND l.id_location=c.id_location
), hist_factor AS (
    SELECT h.data,h.id_customer,h.rede,m.nm_measure,
        COALESCE(MAX(cv.conversion_rate),CASE WHEN m.nm_measure='valor' THEN 1.0 END)::float8 AS conversion_factor
    FROM hist_keys h JOIN measures m ON m.id_customer=h.id_customer
    LEFT JOIN gold.dim_conversao cv ON cv.id_customer=h.id_customer
      AND cv.id_item::text=h.id_item::text AND cv.nm_measure=m.nm_measure
    GROUP BY h.data,h.id_customer,h.rede,m.nm_measure
), cause_factor AS (
    SELECT c.data,c.id_customer,c.rede,m.nm_measure,
        COALESCE(MAX(cv.conversion_rate),CASE WHEN m.nm_measure='valor' THEN 1.0 END)::float8 AS conversion_factor
    FROM cause_keys c JOIN measures m ON m.id_customer=c.id_customer
    LEFT JOIN gold.dim_conversao cv ON cv.id_customer=c.id_customer
      AND cv.id_item::text=c.id_item::text AND cv.nm_measure=m.nm_measure
    GROUP BY c.data,c.id_customer,c.rede,m.nm_measure
)
SELECT h.data,h.id_customer,hf.nm_measure,
    CASE WHEN h.faturamento_sum>0 THEN h.faturamento_sum
      WHEN hf.conversion_factor IS NOT NULL AND h.sales_price_count>0
      THEN (h.volume_sum*hf.conversion_factor)*((h.sales_price_sum/h.sales_price_count)*hf.conversion_factor)
      ELSE NULL END::float8 AS sellout_value,
    c.loss_value_sum::float8 AS loss_value,
    CASE WHEN c.faturamento_sum>0 THEN 100.0*c.loss_value_sum/NULLIF(c.faturamento_sum,0)
      ELSE 100.0*c.loss_value_sum/NULLIF(c.volume_sum*c.price_sum,0) END::float8 AS loss_value_percent,
    (100.0*(1-h.problem_sum/NULLIF(h.active_sum,0)))::float8 AS osa_percent,
    (c.volume_sum*cf.conversion_factor)::float8 AS sales_qty,
    (c.loss_qty_sum*cf.conversion_factor)::float8 AS loss_qty,
    CASE WHEN hf.conversion_factor IS NULL THEN NULL
      ELSE 100.0*(h.loss_qty_sum*hf.conversion_factor)/NULLIF(h.volume_sum*hf.conversion_factor,0)
      END::float8 AS loss_qty_percent,
    h.rede,NULL::text AS bandeira,NULL::text AS uf,NULL::text AS cidade,
    NULL::text AS tipo_local,NULL::text AS loja,NULL::text AS regiao,
    NULL::text AS tp_activity_level,NULL::text AS activity_level,NULL::text AS item,
    NULL::text AS descricao_marca,NULL::text AS hierarquia_1,
    NULL::text AS hierarquia_2,NULL::text AS hierarquia_3
FROM hist_month h JOIN hist_factor hf USING(data,id_customer,rede)
LEFT JOIN cause_month c USING(data,id_customer,rede)
LEFT JOIN cause_factor cf ON cf.data=h.data AND cf.id_customer=h.id_customer
  AND cf.rede=h.rede AND cf.nm_measure=hf.nm_measure;
CREATE UNIQUE INDEX ix_nr_osa_monthly_retail ON gold.nr_osa_monthly_retail (id_customer,rede,nm_measure,data);
ANALYZE gold.nr_osa_monthly_retail;
COMMIT;
