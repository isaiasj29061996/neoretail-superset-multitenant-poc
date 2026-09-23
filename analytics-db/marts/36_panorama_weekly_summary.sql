-- Additive weekly components for the unfiltered Panorama timeline.
-- Dimensional selections keep using nr_panorama_weekly through a virtual
-- dataset, so the dashboard preserves its full filtering behavior.

BEGIN;

DROP MATERIALIZED VIEW IF EXISTS gold.nr_panorama_weekly_summary;

CREATE MATERIALIZED VIEW gold.nr_panorama_weekly_summary AS
SELECT
    id_customer,
    data,
    NULL::text AS tp_activity_level,
    NULL::text AS activity_level,
    NULL::text AS rede,
    NULL::text AS bandeira,
    NULL::text AS uf,
    NULL::text AS cidade,
    NULL::text AS tipo_local,
    NULL::text AS loja,
    NULL::text AS regiao,
    NULL::text AS item,
    NULL::text AS descricao_marca,
    NULL::text AS hierarquia_1,
    NULL::text AS hierarquia_2,
    NULL::text AS hierarquia_3,
    SUM(COALESCE(faturamento, 0))::double precision AS faturamento_sum,
    SUM(COALESCE(volume_unidades, 0) * COALESCE(avg_sales_price, 0))::double precision AS fallback_sellout_sum,
    SUM(COALESCE(volume_unidades, 0) * COALESCE(avg_price_cost, 0))::double precision AS sales_cost_sum,
    SUM(COALESCE(volume_unidades, 0))::double precision AS sales_qty_sum,
    SUM(COALESCE(estoque_medio, 0) * COALESCE(avg_price_cost, 0))::double precision AS stock_cost_sum,
    SUM(COALESCE(estoque_unidades, 0))::double precision AS stock_qty_sum,
    SUM(CASE WHEN COALESCE(giro, 0) > 0 THEN giro ELSE 0 END)::double precision AS giro_sum_positive,
    COUNT(giro) FILTER (WHERE COALESCE(giro, 0) > 0)::bigint AS giro_count_positive,
    SUM(COALESCE(qtd_problemas_osa, 0))::double precision AS osa_problem_sum,
    SUM(COALESCE(qtd_item_ativo_osa, 0))::double precision AS osa_active_sum,
    SUM(COALESCE(rup, 0))::double precision AS rupture_sum,
    SUM(COALESCE(est_virtual, 0))::double precision AS isv_sum
FROM gold.nr_panorama_weekly
GROUP BY id_customer, data;

CREATE UNIQUE INDEX ux_nr_panorama_weekly_summary_customer_data
    ON gold.nr_panorama_weekly_summary (id_customer, data);

COMMENT ON MATERIALIZED VIEW gold.nr_panorama_weekly_summary IS
'Tenant/week additive components for unfiltered Panorama timelines.';

ANALYZE gold.nr_panorama_weekly_summary;

COMMIT;
