-- Dedicated serving marts for NeoRetail export dashboards.
--
-- The daily export reads from a narrow, rolling PostgreSQL source published by
-- the local PySpark serving step. The complete fato_diaria remains in the lake
-- so the local POC does not replicate hundreds of millions of rows into
-- PostgreSQL. Monthly export uses the already-windowed fato_historico serving.

BEGIN;

DROP MATERIALIZED VIEW IF EXISTS gold.nr_export_daily;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_export_monthly;

CREATE MATERIALIZED VIEW gold.nr_export_daily AS
SELECT
    f.data::date AS data,
    f.id_customer,
    EXTRACT(YEAR FROM f.data)::int AS ano,
    EXTRACT(MONTH FROM f.data)::int AS mes_num,
    CASE EXTRACT(MONTH FROM f.data)::int
        WHEN 1 THEN 'janeiro' WHEN 2 THEN 'fevereiro' WHEN 3 THEN 'março'
        WHEN 4 THEN 'abril' WHEN 5 THEN 'maio' WHEN 6 THEN 'junho'
        WHEN 7 THEN 'julho' WHEN 8 THEN 'agosto' WHEN 9 THEN 'setembro'
        WHEN 10 THEN 'outubro' WHEN 11 THEN 'novembro' WHEN 12 THEN 'dezembro'
    END AS mes,
    EXTRACT(DAY FROM f.data)::int AS dia,
    f.id_location,
    f.id_item,
    l.rede,
    l.bandeira,
    l.regiao,
    l.uf,
    l.cidade,
    l.tipo_local,
    l.cod_loja,
    l.loja,
    l.cnpj,
    l.cnpj_formatado,
    i.cd_ean,
    i.desc_produto AS descricao_item,
    i.item,
    i.descricao_marca,
    i.hierarquia_1,
    i.hierarquia_2,
    i.hierarquia_3,
    i.hierarquia_4,
    COALESCE(f.nivel_atividade::text, f.status_item_geral::text, 'I') AS nivel_atividade,
    'unidade'::text AS unidade_medida,
    COALESCE(f.volume_unidades, 0)::double precision AS venda_qtd,
    COALESCE(f.faturamento, 0)::double precision AS venda_valor,
    COALESCE(f.estoque_unidades, 0)::double precision AS estoque_qtd,
    COALESCE(f.estoque_transito, 0)::double precision AS estoque_transito_qtd,
    COALESCE(f.qtd_perda_osa, 0)::double precision AS perda_osa_qtd,
    COALESCE(f.qtd_problemas_osa, 0)::double precision AS osa_problemas,
    COALESCE(f.qtd_item_ativo_osa, 0)::double precision AS osa_itens_ativos,
    COALESCE(f.preco_medio_ref, 0)::double precision AS preco_referencia,
    COALESCE(f.rup, 0)::double precision AS ruptura,
    COALESCE(f.est_virtual, 0)::double precision AS item_sem_venda
FROM gold.nr_export_daily_source f
LEFT JOIN gold.dim_local l
  ON l.id_customer = f.id_customer
 AND l.id_location = f.id_location
LEFT JOIN gold.dim_itens i
  ON i.id_customer = f.id_customer
 AND i.id_item = f.id_item;

CREATE INDEX ix_nr_export_daily_customer_data
    ON gold.nr_export_daily (id_customer, data);
CREATE INDEX ix_nr_export_daily_customer_period
    ON gold.nr_export_daily (id_customer, ano, mes, data);
CREATE INDEX ix_nr_export_daily_customer_retail
    ON gold.nr_export_daily (id_customer, rede, bandeira);
CREATE INDEX ix_nr_export_daily_customer_place
    ON gold.nr_export_daily (id_customer, uf, cidade, tipo_local, loja);
CREATE INDEX ix_nr_export_daily_customer_product
    ON gold.nr_export_daily (
        id_customer, descricao_marca, hierarquia_1, hierarquia_2, hierarquia_3, item
    );

CREATE MATERIALIZED VIEW gold.nr_export_monthly AS
SELECT
    f.mes_ano::date AS data,
    f.id_customer,
    EXTRACT(YEAR FROM f.mes_ano)::int AS ano,
    EXTRACT(MONTH FROM f.mes_ano)::int AS mes_num,
    CASE EXTRACT(MONTH FROM f.mes_ano)::int
        WHEN 1 THEN 'janeiro' WHEN 2 THEN 'fevereiro' WHEN 3 THEN 'março'
        WHEN 4 THEN 'abril' WHEN 5 THEN 'maio' WHEN 6 THEN 'junho'
        WHEN 7 THEN 'julho' WHEN 8 THEN 'agosto' WHEN 9 THEN 'setembro'
        WHEN 10 THEN 'outubro' WHEN 11 THEN 'novembro' WHEN 12 THEN 'dezembro'
    END AS mes,
    f.id_location,
    f.id_item,
    l.rede,
    l.bandeira,
    l.regiao,
    l.uf,
    l.cidade,
    l.tipo_local,
    l.cod_loja,
    l.loja,
    l.cnpj,
    l.cnpj_formatado,
    i.cd_ean,
    i.desc_produto AS descricao_item,
    i.item,
    i.descricao_marca,
    i.hierarquia_1,
    i.hierarquia_2,
    i.hierarquia_3,
    i.hierarquia_4,
    COALESCE(f.tp_activity_level::text, 'I') AS nivel_atividade,
    'unidade'::text AS unidade_medida,
    COALESCE(f.volume_unidades, 0)::double precision AS venda_qtd,
    COALESCE(f.faturamento, 0)::double precision AS venda_valor,
    COALESCE(f.estoque_unidades, 0)::double precision AS estoque_qtd,
    COALESCE(f.estoque_transito, 0)::double precision AS estoque_transito_qtd,
    COALESCE(f.qtd_perda_osa, 0)::double precision AS perda_osa_qtd,
    COALESCE(f.qtd_problemas_osa, 0)::double precision AS osa_problemas,
    COALESCE(f.qtd_item_ativo_osa, 0)::double precision AS osa_itens_ativos,
    COALESCE(f.avg_sales_price, 0)::double precision AS preco_referencia,
    COALESCE(f.rup, 0)::double precision AS ruptura,
    COALESCE(f.est_virtual, 0)::double precision AS item_sem_venda
FROM gold.fato_historico f
LEFT JOIN gold.dim_local l
  ON l.id_customer = f.id_customer
 AND l.id_location = f.id_location
LEFT JOIN gold.dim_itens i
  ON i.id_customer = f.id_customer
 AND i.id_item = f.id_item;

CREATE INDEX ix_nr_export_monthly_customer_data
    ON gold.nr_export_monthly (id_customer, data);
CREATE INDEX ix_nr_export_monthly_customer_period
    ON gold.nr_export_monthly (id_customer, ano, mes, data);
CREATE INDEX ix_nr_export_monthly_customer_retail
    ON gold.nr_export_monthly (id_customer, rede, bandeira);
CREATE INDEX ix_nr_export_monthly_customer_place
    ON gold.nr_export_monthly (id_customer, uf, cidade, tipo_local, loja);
CREATE INDEX ix_nr_export_monthly_customer_product
    ON gold.nr_export_monthly (
        id_customer, descricao_marca, hierarquia_1, hierarquia_2, hierarquia_3, item
    );

COMMENT ON MATERIALIZED VIEW gold.nr_export_daily IS
'Daily export serving mart over a bounded PostgreSQL source; full daily history remains in the lake.';
COMMENT ON MATERIALIZED VIEW gold.nr_export_monthly IS
'Monthly export serving mart for NeoRetail embedded export grids.';

ANALYZE gold.nr_export_daily;
ANALYZE gold.nr_export_monthly;

COMMIT;
