-- Compact retailer timeline for the Export dashboards.
-- The detailed export mart remains the filtered fallback in Superset.

BEGIN;

DROP MATERIALIZED VIEW IF EXISTS gold.nr_export_daily_retail_summary;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_export_monthly_retail_summary;

CREATE MATERIALIZED VIEW gold.nr_export_daily_retail_summary AS
SELECT
    id_customer,
    data,
    ano,
    mes_num,
    mes,
    dia,
    rede,
    SUM(venda_qtd)::double precision AS venda_qtd,
    SUM(venda_valor)::double precision AS venda_valor,
    SUM(estoque_qtd)::double precision AS estoque_qtd,
    SUM(estoque_transito_qtd)::double precision AS estoque_transito_qtd,
    SUM(perda_osa_qtd)::double precision AS perda_osa_qtd,
    SUM(osa_problemas)::double precision AS osa_problemas,
    SUM(osa_itens_ativos)::double precision AS osa_itens_ativos,
    SUM(ruptura)::double precision AS ruptura,
    SUM(item_sem_venda)::double precision AS item_sem_venda,
    SUM(CASE WHEN preco_referencia <> 0 THEN preco_referencia ELSE 0 END)::double precision
        AS price_reference_sum,
    COUNT(preco_referencia) FILTER (WHERE preco_referencia <> 0)::bigint
        AS price_reference_count
FROM gold.nr_export_daily
GROUP BY id_customer, data, ano, mes_num, mes, dia, rede;

CREATE INDEX ix_nr_export_daily_retail_customer_data
    ON gold.nr_export_daily_retail_summary (id_customer, data, rede);

CREATE MATERIALIZED VIEW gold.nr_export_monthly_retail_summary AS
SELECT
    id_customer,
    data,
    ano,
    mes_num,
    mes,
    NULL::integer AS dia,
    rede,
    SUM(venda_qtd)::double precision AS venda_qtd,
    SUM(venda_valor)::double precision AS venda_valor,
    SUM(estoque_qtd)::double precision AS estoque_qtd,
    SUM(estoque_transito_qtd)::double precision AS estoque_transito_qtd,
    SUM(perda_osa_qtd)::double precision AS perda_osa_qtd,
    SUM(osa_problemas)::double precision AS osa_problemas,
    SUM(osa_itens_ativos)::double precision AS osa_itens_ativos,
    SUM(ruptura)::double precision AS ruptura,
    SUM(item_sem_venda)::double precision AS item_sem_venda,
    SUM(CASE WHEN preco_referencia <> 0 THEN preco_referencia ELSE 0 END)::double precision
        AS price_reference_sum,
    COUNT(preco_referencia) FILTER (WHERE preco_referencia <> 0)::bigint
        AS price_reference_count
FROM gold.nr_export_monthly
GROUP BY id_customer, data, ano, mes_num, mes, rede;

CREATE INDEX ix_nr_export_monthly_retail_customer_data
    ON gold.nr_export_monthly_retail_summary (id_customer, data, rede);

ANALYZE gold.nr_export_daily_retail_summary;
ANALYZE gold.nr_export_monthly_retail_summary;

COMMIT;
