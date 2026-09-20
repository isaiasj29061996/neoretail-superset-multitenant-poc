-- Compact default paths for the remaining P1 interactive workloads.
-- Virtual datasets retain the detailed source whenever a dimensional filter
-- is active, preserving exact distinct counts and filtered OSA semantics.

BEGIN;

DROP MATERIALIZED VIEW IF EXISTS gold.nr_overview_distinct_summary;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_overview_default_summary;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_osa_causes_summary;

-- Default Overview queries do not need product, store or geography grain.
-- Keep the activity level because Giro, ROI and Markup render that breakdown.
-- NULL dimension columns retain the same dataset contract; the virtual dataset
-- switches back to nr_overview_summary before Superset applies any such filter.
CREATE MATERIALIZED VIEW gold.nr_overview_default_summary AS
SELECT
    data,
    id_customer,
    tp_activity_level,
    activity_level,
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
    SUM(faturamento_sum)::double precision AS faturamento_sum,
    SUM(fallback_sellout_sum)::double precision AS fallback_sellout_sum,
    SUM(sales_cost_sum)::double precision AS sales_cost_sum,
    SUM(sales_qty_sum)::double precision AS sales_qty_sum,
    SUM(stock_cost_sum)::double precision AS stock_cost_sum,
    SUM(stock_qty_sum)::double precision AS stock_qty_sum,
    SUM(rupture_sum) AS rupture_sum,
    SUM(isv_sum) AS isv_sum,
    SUM(giro_sum_positive)::double precision AS giro_sum_positive,
    SUM(giro_count_positive)::bigint AS giro_count_positive,
    SUM(osa_problem_sum) AS osa_problem_sum,
    SUM(osa_active_sum) AS osa_active_sum,
    SUM(osa_loss_qty_sum)::double precision AS osa_loss_qty_sum,
    SUM(avg_sales_price_sum)::double precision AS avg_sales_price_sum,
    SUM(avg_sales_price_count)::bigint AS avg_sales_price_count,
    SUM(osa_critical_count)::bigint AS osa_critical_count,
    SUM(osa_risk_count)::bigint AS osa_risk_count,
    SUM(rupture_critical_count)::bigint AS rupture_critical_count,
    SUM(rupture_risk_count)::bigint AS rupture_risk_count,
    SUM(isv_critical_count)::bigint AS isv_critical_count,
    SUM(isv_risk_count)::bigint AS isv_risk_count
FROM gold.nr_overview_summary
GROUP BY data, id_customer, tp_activity_level, activity_level;

CREATE UNIQUE INDEX ux_nr_overview_default_summary_grain
    ON gold.nr_overview_default_summary (
        id_customer, data, tp_activity_level, activity_level
    );

CREATE MATERIALIZED VIEW gold.nr_overview_distinct_summary AS
SELECT
    id_customer,
    data,
    COUNT(DISTINCT id_location)::bigint AS store_count,
    COUNT(DISTINCT id_item)::bigint AS item_count
FROM gold.nr_overview_history
GROUP BY id_customer, data;

CREATE UNIQUE INDEX ux_nr_overview_distinct_summary_customer_data
    ON gold.nr_overview_distinct_summary (id_customer, data);

CREATE MATERIALIZED VIEW gold.nr_osa_causes_summary AS
SELECT
    id_customer,
    data,
    motivo_osa,
    causa_osa,
    SUM(COALESCE(qtd_perda_osa * NULLIF(preco_medio, 0), 0))::double precision
        AS loss_value_sum
FROM gold.nr_osa_industry_causes
GROUP BY id_customer, data, motivo_osa, causa_osa;

CREATE INDEX ix_nr_osa_causes_summary_customer_data
    ON gold.nr_osa_causes_summary (id_customer, data);
CREATE INDEX ix_nr_osa_causes_summary_customer_reason
    ON gold.nr_osa_causes_summary (id_customer, motivo_osa, causa_osa);

COMMENT ON MATERIALIZED VIEW gold.nr_overview_distinct_summary IS
'Exact unfiltered monthly store/item cardinalities by tenant.';
COMMENT ON MATERIALIZED VIEW gold.nr_overview_default_summary IS
'Additive Overview metrics at tenant/month/activity grain for unfiltered charts.';
COMMENT ON MATERIALIZED VIEW gold.nr_osa_causes_summary IS
'Tenant/month/reason additive OSA loss value for unfiltered OSA visuals.';

ANALYZE gold.nr_overview_distinct_summary;
ANALYZE gold.nr_overview_default_summary;
ANALYZE gold.nr_osa_causes_summary;

COMMIT;
