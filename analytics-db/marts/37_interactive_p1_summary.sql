-- Compact default paths for the remaining P1 interactive workloads.
-- Virtual datasets retain the detailed source whenever a dimensional filter
-- is active, preserving exact distinct counts and filtered OSA semantics.

BEGIN;

DROP MATERIALIZED VIEW IF EXISTS gold.nr_overview_distinct_summary;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_osa_causes_summary;

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
COMMENT ON MATERIALIZED VIEW gold.nr_osa_causes_summary IS
'Tenant/month/reason additive OSA loss value for unfiltered OSA visuals.';

ANALYZE gold.nr_overview_distinct_summary;
ANALYZE gold.nr_osa_causes_summary;

COMMIT;
