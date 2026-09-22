-- Physical serving layer for the four NeoRetail dashboards.
--
-- These materialized views preserve the row-level grain required by native
-- filters and RLS while moving joins, latest-row selection and window
-- calculations out of interactive dashboard queries.

BEGIN;

-- These summaries depend on the daily marts and are recreated by
-- the later numbered scripts in the ordered refresh.
-- Drop semantic marts first because they depend on the compact summaries.
DROP MATERIALIZED VIEW IF EXISTS gold.nr_osa_semantic_default;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_overview_semantic_default;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_conversion_options;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_tvd_daily_summary;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_ivd_daily_summary;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_panorama_weekly_summary;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_panorama_gap_periodic;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_overview_distinct_summary;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_overview_default_summary;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_osa_causes_summary;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_panorama_opportunities_latest;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_panorama_latest;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_stock_tasks;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_osa_industry_causes;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_tvd_daily;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_panorama_opportunities;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_panorama_weekly;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_overview_history;

CREATE MATERIALIZED VIEW gold.nr_overview_history AS
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
    f.id_item,
    f.id_location,
    f.volume_unidades,
    f.faturamento,
    f.estoque_unidades,
    f.expectativa_vendas,
    f.qtd_perda_osa,
    f.rup,
    f.est_virtual,
    f.giro,
    f.qtd_problemas_osa,
    f.qtd_item_ativo_osa,
    f.avg_sales_price,
    f.avg_price_cost,
    f.estoque_medio,
    f.demanda_media,
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
    CONCAT_WS('|', f.id_customer::text, f.id_location, f.id_item) AS opportunity_key,
    o.qtd_problemas_osa_m0,
    o.max_tp_activity_level
FROM gold.fato_historico f
LEFT JOIN gold.dim_local l
  ON l.id_customer = f.id_customer AND l.id_location = f.id_location
LEFT JOIN gold.dim_itens i
  ON i.id_customer = f.id_customer AND i.id_item = f.id_item
LEFT JOIN latest_opportunity o
  ON o.id_customer = f.id_customer
 AND o.id_location = f.id_location
 AND o.id_item = f.id_item;

CREATE INDEX ix_nr_overview_history_customer_data
    ON gold.nr_overview_history (id_customer, data);
CREATE INDEX ix_nr_overview_history_customer_retail
    ON gold.nr_overview_history (id_customer, rede, bandeira);
CREATE INDEX ix_nr_overview_history_customer_place
    ON gold.nr_overview_history (id_customer, uf, cidade, tipo_local);
CREATE INDEX ix_nr_overview_history_customer_activity
    ON gold.nr_overview_history (id_customer, tp_activity_level);
CREATE INDEX ix_nr_overview_history_customer_product
    ON gold.nr_overview_history (id_customer, descricao_marca, hierarquia_1, hierarquia_2, hierarquia_3);
CREATE INDEX ix_nr_overview_history_customer_item
    ON gold.nr_overview_history (id_customer, item);

CREATE MATERIALIZED VIEW gold.nr_panorama_latest AS
SELECT h.*
FROM gold.nr_overview_history h
JOIN (
    SELECT id_customer, MAX(data) AS max_data
    FROM gold.nr_overview_history
    GROUP BY id_customer
) d ON d.id_customer = h.id_customer AND d.max_data = h.data;

CREATE INDEX ix_nr_panorama_latest_customer
    ON gold.nr_panorama_latest (id_customer);
CREATE INDEX ix_nr_panorama_latest_customer_retail
    ON gold.nr_panorama_latest (id_customer, rede, bandeira);
CREATE INDEX ix_nr_panorama_latest_customer_place
    ON gold.nr_panorama_latest (id_customer, uf, cidade, tipo_local);
CREATE INDEX ix_nr_panorama_latest_customer_product
    ON gold.nr_panorama_latest (id_customer, descricao_marca, hierarquia_1, hierarquia_2, hierarquia_3, item);

CREATE MATERIALIZED VIEW gold.nr_panorama_weekly AS
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
    i.hierarquia_3
FROM gold.fato_semanal f
LEFT JOIN gold.dim_local l
  ON l.id_customer = f.id_customer AND l.id_location = f.id_location
LEFT JOIN gold.dim_itens i
  ON i.id_customer = f.id_customer AND i.id_item = f.id_item;

CREATE INDEX ix_nr_panorama_weekly_customer_data
    ON gold.nr_panorama_weekly (id_customer, data);
CREATE INDEX ix_nr_panorama_weekly_customer_retail
    ON gold.nr_panorama_weekly (id_customer, rede, bandeira);
CREATE INDEX ix_nr_panorama_weekly_customer_place
    ON gold.nr_panorama_weekly (id_customer, uf, cidade, tipo_local);
CREATE INDEX ix_nr_panorama_weekly_customer_product
    ON gold.nr_panorama_weekly (id_customer, descricao_marca, hierarquia_1, hierarquia_2, hierarquia_3, item);

CREATE MATERIALIZED VIEW gold.nr_panorama_opportunities AS
WITH latest_opportunity AS (
    SELECT DISTINCT ON (id_customer, id_location, id_item)
        id_customer,
        id_location,
        id_item,
        regra_critico,
        tvd AS oportunidade_tvd,
        ivd AS oportunidade_ivd
    FROM gold.calculo_oportunidades
    ORDER BY id_customer, id_location, id_item, _silver_refreshed_at DESC NULLS LAST
)
SELECT
    f.id_customer,
    f.id_time,
    f.id_time::date AS data,
    f.id_item,
    f.id_location,
    f.tp_activity_level,
    f.tvd_simplificado,
    f.ivd_simplificado,
    l.id_retailer,
    l.rede,
    l.bandeira,
    l.uf,
    l.cidade,
    l.tipo_local,
    l.loja,
    l.regiao,
    COALESCE(l.loja, l.nome_da_loja, f.id_location) AS deposito,
    i.item,
    i.descricao_marca,
    i.hierarquia_1,
    i.hierarquia_2,
    i.hierarquia_3,
    i.hierarquia_4,
    'unidade'::text AS unidade_medida,
    CONCAT_WS('|', f.id_customer::text, f.id_location, f.id_item) AS opportunity_key,
    o.regra_critico,
    o.oportunidade_tvd,
    o.oportunidade_ivd,
    MAX(f.id_time::date) OVER (
        PARTITION BY f.id_customer, DATE_TRUNC('month', f.id_time)
    ) AS month_end_data,
    MAX(f.id_time::date) OVER (
        PARTITION BY f.id_customer, DATE_TRUNC('week', f.id_time)
    ) AS week_end_data,
    MAX(f.id_time::date) OVER (PARTITION BY f.id_customer) AS customer_latest_data
FROM gold.fato_ivd_tvd f
LEFT JOIN gold.dim_local l
  ON l.id_customer = f.id_customer AND l.id_location = f.id_location
LEFT JOIN gold.dim_itens i
  ON i.id_customer = f.id_customer AND i.id_item = f.id_item
LEFT JOIN latest_opportunity o
  ON o.id_customer = f.id_customer
 AND o.id_location = f.id_location
 AND o.id_item = f.id_item;

CREATE INDEX ix_nr_panorama_opportunities_customer_data
    ON gold.nr_panorama_opportunities (id_customer, data);
CREATE INDEX ix_nr_panorama_opportunities_customer_period_ends
    ON gold.nr_panorama_opportunities (id_customer, month_end_data, week_end_data);
CREATE INDEX ix_nr_panorama_opportunities_customer_retail
    ON gold.nr_panorama_opportunities (id_customer, rede, bandeira);
CREATE INDEX ix_nr_panorama_opportunities_customer_place
    ON gold.nr_panorama_opportunities (id_customer, uf, cidade, tipo_local, deposito);
CREATE INDEX ix_nr_panorama_opportunities_customer_product
    ON gold.nr_panorama_opportunities (id_customer, descricao_marca, hierarquia_1, hierarquia_2, hierarquia_3, item);

CREATE MATERIALIZED VIEW gold.nr_tvd_daily AS
WITH fact_daily AS (
    SELECT
        o.id_customer, o.data, o.opportunity_key, o.rede, o.bandeira,
        o.uf, o.cidade, o.tipo_local, o.loja, o.regiao, o.deposito,
        o.tp_activity_level, o.item, o.descricao_marca, o.hierarquia_1,
        o.hierarquia_2, o.hierarquia_3, o.hierarquia_4, o.unidade_medida,
        SUM(COALESCE(o.tvd_simplificado, 0)) AS tvd,
        0::bigint AS itens_criticos_tvd,
        0::bigint AS itens_risco_tvd
    FROM gold.nr_panorama_opportunities o
    LEFT JOIN gold.dim_catalogo_local catalogo
      ON catalogo.id_customer = o.id_customer
     AND catalogo.id_location = o.id_location
    WHERE UPPER(TRIM(COALESCE(o.tipo_local, ''))) NOT IN (
        U&'DEP\00D3SITO', 'DEPOSITO', 'CD', 'LOJA VIRTUAL'
    )
      AND UPPER(TRIM(COALESCE(catalogo.tipo_local, ''))) NOT IN (
        U&'DEP\00D3SITO', 'DEPOSITO', 'CD', 'LOJA VIRTUAL'
      )
    GROUP BY
        o.id_customer, o.data, o.opportunity_key, o.rede, o.bandeira,
        o.uf, o.cidade, o.tipo_local, o.loja, o.regiao, o.deposito,
        o.tp_activity_level, o.item, o.descricao_marca, o.hierarquia_1,
        o.hierarquia_2, o.hierarquia_3, o.hierarquia_4, o.unidade_medida
), customer_latest_date AS (
    SELECT id_customer, MAX(id_time::date) AS data
    FROM gold.fato_ivd_tvd
    GROUP BY id_customer
), task_snapshot AS (
    SELECT
        c.id_customer,
        d.data,
        CONCAT_WS('|', c.id_customer::text, c.id_location, c.id_item) AS opportunity_key,
        l.rede,
        l.bandeira,
        l.uf,
        l.cidade,
        l.tipo_local,
        l.loja,
        l.regiao,
        COALESCE(l.loja, l.nome_da_loja, c.id_location) AS deposito,
        c.max_tp_activity_level AS tp_activity_level,
        i.item,
        i.descricao_marca,
        i.hierarquia_1,
        i.hierarquia_2,
        i.hierarquia_3,
        i.hierarquia_4,
        'unidade'::text AS unidade_medida,
        0::double precision AS tvd,
        CASE
            WHEN c.id_item IS NOT NULL
             AND c.regra_critico = 'CRITICO'
             AND COALESCE(c.tvd, 0) > 0
            THEN 1 ELSE 0
        END::bigint AS itens_criticos_tvd,
        CASE
            WHEN c.id_item IS NOT NULL
             AND c.regra_critico = 'F'
             AND COALESCE(c.tvd, 0) > 0
            THEN 1 ELSE 0
        END::bigint AS itens_risco_tvd
    FROM gold.calculo_oportunidades c
    JOIN customer_latest_date d
      ON d.id_customer = c.id_customer
    LEFT JOIN gold.dim_local l
      ON l.id_customer = c.id_customer
     AND l.id_location = c.id_location
    LEFT JOIN gold.dim_catalogo_local catalogo
      ON catalogo.id_customer = c.id_customer
     AND catalogo.id_location = c.id_location
    LEFT JOIN gold.dim_itens i
      ON i.id_customer = c.id_customer
     AND i.id_item = c.id_item
    WHERE UPPER(TRIM(COALESCE(l.tipo_local, ''))) NOT IN (
        U&'DEP\00D3SITO', 'DEPOSITO', 'CD', 'LOJA VIRTUAL'
    )
      AND UPPER(TRIM(COALESCE(catalogo.tipo_local, ''))) NOT IN (
        U&'DEP\00D3SITO', 'DEPOSITO', 'CD', 'LOJA VIRTUAL'
      )
), opportunity_daily AS (
    SELECT * FROM fact_daily
    UNION ALL
    SELECT * FROM task_snapshot
)
SELECT
    id_customer, data, rede, bandeira, uf, cidade, tipo_local, loja,
    regiao, deposito, tp_activity_level, item, descricao_marca,
    hierarquia_1, hierarquia_2, hierarquia_3, hierarquia_4, unidade_medida,
    SUM(tvd) AS tvd,
    SUM(itens_criticos_tvd)::bigint AS itens_criticos_tvd,
    SUM(itens_risco_tvd)::bigint AS itens_risco_tvd
FROM opportunity_daily
GROUP BY
    id_customer, data, rede, bandeira, uf, cidade, tipo_local, loja,
    regiao, deposito, tp_activity_level, item, descricao_marca,
    hierarquia_1, hierarquia_2, hierarquia_3, hierarquia_4, unidade_medida;

CREATE INDEX ix_nr_tvd_daily_customer_data
    ON gold.nr_tvd_daily (id_customer, data);
CREATE INDEX ix_nr_tvd_daily_customer_retail
    ON gold.nr_tvd_daily (id_customer, rede, bandeira);
CREATE INDEX ix_nr_tvd_daily_customer_place
    ON gold.nr_tvd_daily (id_customer, uf, cidade, tipo_local, deposito);
CREATE INDEX ix_nr_tvd_daily_customer_product
    ON gold.nr_tvd_daily (id_customer, descricao_marca, hierarquia_1, hierarquia_2, hierarquia_3, item);

CREATE MATERIALIZED VIEW gold.nr_panorama_opportunities_latest AS
SELECT o.*
FROM gold.nr_panorama_opportunities o
WHERE o.data = o.customer_latest_data;

CREATE INDEX ix_nr_panorama_opportunities_latest_customer
    ON gold.nr_panorama_opportunities_latest (id_customer);
CREATE INDEX ix_nr_panorama_opportunities_latest_customer_dimensions
    ON gold.nr_panorama_opportunities_latest (id_customer, rede, regiao, hierarquia_1, item);

CREATE MATERIALIZED VIEW gold.nr_osa_industry_causes AS
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
    i.hierarquia_3
FROM gold.fato_mensal_causa_osa f
LEFT JOIN gold.dim_local l
  ON l.id_customer = f.id_customer AND l.id_location = f.id_location
LEFT JOIN gold.dim_itens i
  ON i.id_customer = f.id_customer AND i.id_item = f.id_item;

CREATE INDEX ix_nr_osa_causes_customer_data
    ON gold.nr_osa_industry_causes (id_customer, data);
CREATE INDEX ix_nr_osa_causes_customer_reason
    ON gold.nr_osa_industry_causes (id_customer, motivo_osa, causa_osa);
CREATE INDEX ix_nr_osa_causes_customer_retail
    ON gold.nr_osa_industry_causes (id_customer, rede, bandeira);
CREATE INDEX ix_nr_osa_causes_customer_place
    ON gold.nr_osa_industry_causes (id_customer, uf, cidade, tipo_local);
CREATE INDEX ix_nr_osa_causes_customer_product
    ON gold.nr_osa_industry_causes (id_customer, descricao_marca, hierarquia_1, hierarquia_2, hierarquia_3, item);

CREATE MATERIALIZED VIEW gold.nr_stock_tasks AS
WITH last_dates AS (
    SELECT id_customer, MAX(id_time)::date AS data
    FROM gold.fato_ivd_tvd
    GROUP BY id_customer
)
SELECT
    c.*,
    d.data,
    l.rede,
    l.bandeira,
    l.uf,
    l.cidade,
    l.tipo_local,
    l.loja,
    l.regiao,
    COALESCE(l.loja, l.nome_da_loja, c.id_location) AS deposito,
    c.max_tp_activity_level AS tp_activity_level,
    i.item,
    i.descricao_marca,
    i.hierarquia_1,
    i.hierarquia_2,
    i.hierarquia_3,
    'unidade'::text AS unidade_medida
FROM gold.calculo_oportunidades c
JOIN last_dates d ON d.id_customer = c.id_customer
LEFT JOIN gold.dim_local l
  ON l.id_customer = c.id_customer AND l.id_location = c.id_location
LEFT JOIN gold.dim_itens i
  ON i.id_customer = c.id_customer AND i.id_item = c.id_item;

CREATE INDEX ix_nr_stock_tasks_customer
    ON gold.nr_stock_tasks (id_customer);
CREATE INDEX ix_nr_stock_tasks_customer_alerts
    ON gold.nr_stock_tasks (id_customer, regra_critico, alerta_tvd, alerta_ivd);
CREATE INDEX ix_nr_stock_tasks_customer_retail
    ON gold.nr_stock_tasks (id_customer, rede, bandeira, deposito);
CREATE INDEX ix_nr_stock_tasks_customer_product
    ON gold.nr_stock_tasks (id_customer, descricao_marca, hierarquia_1, hierarquia_2, hierarquia_3, item);

COMMENT ON MATERIALIZED VIEW gold.nr_overview_history IS
'Physical serving mart for monthly overview, panorama and OSA charts; RLS key: id_customer.';
COMMENT ON MATERIALIZED VIEW gold.nr_panorama_latest IS
'Latest monthly snapshot per customer for rankings and detailed analysis.';
COMMENT ON MATERIALIZED VIEW gold.nr_panorama_weekly IS
'Physical serving mart for weekly panorama charts.';
COMMENT ON MATERIALIZED VIEW gold.nr_panorama_opportunities IS
'Physical daily TVD/IVD mart with reusable period-end markers.';
COMMENT ON MATERIALIZED VIEW gold.nr_tvd_daily IS
'Pre-aggregated daily TVD mart with additive alert counts, native-filter dimensions and id_customer RLS key.';
COMMENT ON MATERIALIZED VIEW gold.nr_panorama_opportunities_latest IS
'Latest daily TVD/IVD snapshot per customer.';
COMMENT ON MATERIALIZED VIEW gold.nr_osa_industry_causes IS
'Physical serving mart for OSA reason and cause analysis.';
COMMENT ON MATERIALIZED VIEW gold.nr_stock_tasks IS
'Physical serving mart for stock optimization task rankings and details.';

ANALYZE gold.nr_overview_history;
ANALYZE gold.nr_panorama_latest;
ANALYZE gold.nr_panorama_weekly;
ANALYZE gold.nr_panorama_opportunities;
ANALYZE gold.nr_tvd_daily;
ANALYZE gold.nr_panorama_opportunities_latest;
ANALYZE gold.nr_osa_industry_causes;
ANALYZE gold.nr_stock_tasks;

COMMIT;
