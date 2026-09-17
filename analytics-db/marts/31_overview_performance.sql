-- Dedicated serving marts for the NeoRetail Overview dashboard.
--
-- These marts are intentionally independent from 30_neoretail_serving_marts.sql
-- so the base serving layer can still be recreated without dependency-order
-- problems. Heavy ratios and distinct task counts are decomposed into additive
-- components during refresh, keeping interactive queries cheap and filter-safe.

BEGIN;

DROP MATERIALIZED VIEW IF EXISTS gold.nr_overview_summary;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_ivd_daily;

CREATE MATERIALIZED VIEW gold.nr_overview_summary AS
WITH latest_opportunity AS (
    SELECT DISTINCT ON (id_customer, id_location, id_item)
        id_customer,
        id_location,
        id_item,
        qtd_problemas_osa_m0,
        max_tp_activity_level
    FROM gold.calculo_oportunidades
    ORDER BY id_customer, id_location, id_item, _silver_refreshed_at DESC NULLS LAST
)
SELECT
    f.mes_ano AS data,
    f.id_customer,
    f.tp_activity_level,
    CASE f.tp_activity_level
        WHEN 'F' THEN 'Fast Mover'
        WHEN 'S' THEN 'Slow Mover'
        WHEN 'US' THEN 'Ultra Slow Mover'
        WHEN 'N' THEN 'New Mover'
        ELSE COALESCE(f.tp_activity_level, 'Outros')
    END AS activity_level,
    l.rede,
    l.bandeira,
    l.uf,
    l.cidade,
    l.tipo_local,
    l.loja,
    l.regiao,
    i.item,
    i.descricao_marca,
    i.hierarquia_1,
    i.hierarquia_2,
    i.hierarquia_3,
    SUM(COALESCE(f.faturamento, 0)) AS faturamento_sum,
    SUM(COALESCE(f.volume_unidades, 0) * COALESCE(f.avg_sales_price, 0)) AS fallback_sellout_sum,
    SUM(COALESCE(f.volume_unidades, 0) * COALESCE(f.avg_price_cost, 0)) AS sales_cost_sum,
    SUM(COALESCE(f.volume_unidades, 0)) AS sales_qty_sum,
    SUM(COALESCE(f.estoque_medio, 0) * COALESCE(f.avg_price_cost, 0)) AS stock_cost_sum,
    SUM(COALESCE(f.estoque_unidades, 0)) AS stock_qty_sum,
    SUM(CASE WHEN COALESCE(f.giro, 0) > 0 THEN f.giro ELSE 0 END) AS giro_sum_positive,
    COUNT(f.giro) FILTER (WHERE COALESCE(f.giro, 0) > 0)::bigint AS giro_count_positive,
    SUM(COALESCE(f.qtd_problemas_osa, 0)) AS osa_problem_sum,
    SUM(COALESCE(f.qtd_item_ativo_osa, 0)) AS osa_active_sum,
    SUM(COALESCE(f.qtd_perda_osa, 0)) AS osa_loss_qty_sum,
    SUM(COALESCE(f.avg_sales_price, 0)) AS avg_sales_price_sum,
    COUNT(f.avg_sales_price)::bigint AS avg_sales_price_count,
    COUNT(DISTINCT CASE
        WHEN COALESCE(o.qtd_problemas_osa_m0, 0) > 0
         AND o.max_tp_activity_level = 'F'
        THEN CONCAT_WS('|', f.id_customer::text, f.id_location, f.id_item)
    END)::bigint AS osa_critical_count,
    COUNT(DISTINCT CASE
        WHEN COALESCE(o.qtd_problemas_osa_m0, 0) > 0
         AND o.max_tp_activity_level = 'S'
        THEN CONCAT_WS('|', f.id_customer::text, f.id_location, f.id_item)
    END)::bigint AS osa_risk_count
FROM gold.fato_historico f
LEFT JOIN gold.dim_local l
  ON l.id_customer = f.id_customer
 AND l.id_location = f.id_location
LEFT JOIN gold.dim_itens i
  ON i.id_customer = f.id_customer
 AND i.id_item = f.id_item
LEFT JOIN latest_opportunity o
  ON o.id_customer = f.id_customer
 AND o.id_location = f.id_location
 AND o.id_item = f.id_item
GROUP BY
    f.mes_ano,
    f.id_customer,
    f.tp_activity_level,
    l.rede,
    l.bandeira,
    l.uf,
    l.cidade,
    l.tipo_local,
    l.loja,
    l.regiao,
    i.item,
    i.descricao_marca,
    i.hierarquia_1,
    i.hierarquia_2,
    i.hierarquia_3;

CREATE INDEX ix_nr_overview_summary_customer_data
    ON gold.nr_overview_summary (id_customer, data);
CREATE INDEX ix_nr_overview_summary_customer_retail
    ON gold.nr_overview_summary (id_customer, rede, bandeira);
CREATE INDEX ix_nr_overview_summary_customer_place
    ON gold.nr_overview_summary (id_customer, uf, cidade, tipo_local, loja);
CREATE INDEX ix_nr_overview_summary_customer_activity
    ON gold.nr_overview_summary (id_customer, tp_activity_level, activity_level);
CREATE INDEX ix_nr_overview_summary_customer_product
    ON gold.nr_overview_summary (
        id_customer, descricao_marca, hierarquia_1, hierarquia_2, hierarquia_3, item
    );

CREATE MATERIALIZED VIEW gold.nr_ivd_daily AS
WITH latest_opportunity AS (
    SELECT DISTINCT ON (id_customer, id_location, id_item)
        id_customer,
        id_location,
        id_item,
        regra_critico,
        ivd AS oportunidade_ivd
    FROM gold.calculo_oportunidades
    ORDER BY id_customer, id_location, id_item, _silver_refreshed_at DESC NULLS LAST
), opportunity_daily AS (
    SELECT
        f.id_customer,
        f.id_time::date AS data,
        CONCAT_WS('|', f.id_customer::text, f.id_location, f.id_item) AS opportunity_key,
        l.rede,
        l.bandeira,
        l.uf,
        l.cidade,
        l.tipo_local,
        l.loja,
        l.regiao,
        COALESCE(l.loja, l.nome_da_loja, f.id_location) AS deposito,
        f.tp_activity_level,
        i.item,
        i.descricao_marca,
        i.hierarquia_1,
        i.hierarquia_2,
        i.hierarquia_3,
        i.hierarquia_4,
        'unidade'::text AS unidade_medida,
        SUM(COALESCE(f.ivd_simplificado, 0)) AS ivd,
        MAX(CASE
            WHEN o.regra_critico = 'CRITICO'
             AND COALESCE(o.oportunidade_ivd, 0) > 0
            THEN 1 ELSE 0
        END) AS itens_criticos_ivd,
        MAX(CASE
            WHEN o.regra_critico = 'F'
             AND COALESCE(o.oportunidade_ivd, 0) > 0
            THEN 1 ELSE 0
        END) AS itens_risco_ivd
    FROM gold.fato_ivd_tvd f
    LEFT JOIN gold.dim_local l
      ON l.id_customer = f.id_customer
     AND l.id_location = f.id_location
    LEFT JOIN gold.dim_itens i
      ON i.id_customer = f.id_customer
     AND i.id_item = f.id_item
    LEFT JOIN latest_opportunity o
      ON o.id_customer = f.id_customer
     AND o.id_location = f.id_location
     AND o.id_item = f.id_item
    GROUP BY
        f.id_customer,
        f.id_time::date,
        CONCAT_WS('|', f.id_customer::text, f.id_location, f.id_item),
        l.rede,
        l.bandeira,
        l.uf,
        l.cidade,
        l.tipo_local,
        l.loja,
        l.regiao,
        COALESCE(l.loja, l.nome_da_loja, f.id_location),
        f.tp_activity_level,
        i.item,
        i.descricao_marca,
        i.hierarquia_1,
        i.hierarquia_2,
        i.hierarquia_3,
        i.hierarquia_4
)
SELECT
    id_customer,
    data,
    rede,
    bandeira,
    uf,
    cidade,
    tipo_local,
    loja,
    regiao,
    deposito,
    tp_activity_level,
    item,
    descricao_marca,
    hierarquia_1,
    hierarquia_2,
    hierarquia_3,
    hierarquia_4,
    unidade_medida,
    SUM(ivd) AS ivd,
    SUM(itens_criticos_ivd)::bigint AS itens_criticos_ivd,
    SUM(itens_risco_ivd)::bigint AS itens_risco_ivd
FROM opportunity_daily
GROUP BY
    id_customer,
    data,
    rede,
    bandeira,
    uf,
    cidade,
    tipo_local,
    loja,
    regiao,
    deposito,
    tp_activity_level,
    item,
    descricao_marca,
    hierarquia_1,
    hierarquia_2,
    hierarquia_3,
    hierarquia_4,
    unidade_medida;

CREATE INDEX ix_nr_ivd_daily_customer_data
    ON gold.nr_ivd_daily (id_customer, data);
CREATE INDEX ix_nr_ivd_daily_customer_retail
    ON gold.nr_ivd_daily (id_customer, rede, bandeira);
CREATE INDEX ix_nr_ivd_daily_customer_place
    ON gold.nr_ivd_daily (id_customer, uf, cidade, tipo_local, deposito);
CREATE INDEX ix_nr_ivd_daily_customer_product
    ON gold.nr_ivd_daily (
        id_customer, descricao_marca, hierarquia_1, hierarquia_2, hierarquia_3, item
    );

COMMENT ON MATERIALIZED VIEW gold.nr_overview_summary IS
'Overview serving mart with additive KPI components and id_customer RLS key.';
COMMENT ON MATERIALIZED VIEW gold.nr_ivd_daily IS
'Pre-aggregated daily IVD mart with additive alert counts and native-filter dimensions.';

ANALYZE gold.nr_overview_summary;
ANALYZE gold.nr_ivd_daily;

COMMIT;
