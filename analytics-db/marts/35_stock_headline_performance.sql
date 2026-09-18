-- Daily headline paths for TVD/IVD when no dimensional filter is active.
-- Detailed marts remain available and are selected dynamically by Superset as
-- soon as a location, activity, product, or unit filter is applied.

BEGIN;

DROP MATERIALIZED VIEW IF EXISTS gold.nr_tvd_daily_summary;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_ivd_daily_summary;

CREATE MATERIALIZED VIEW gold.nr_tvd_daily_summary AS
SELECT
    id_customer,
    data,
    NULL::text AS rede,
    NULL::text AS bandeira,
    NULL::text AS uf,
    NULL::text AS cidade,
    NULL::text AS tipo_local,
    NULL::text AS loja,
    NULL::text AS regiao,
    NULL::text AS deposito,
    NULL::text AS tp_activity_level,
    NULL::text AS item,
    NULL::text AS descricao_marca,
    NULL::text AS hierarquia_1,
    NULL::text AS hierarquia_2,
    NULL::text AS hierarquia_3,
    NULL::text AS hierarquia_4,
    NULL::text AS unidade_medida,
    SUM(tvd)::double precision AS tvd,
    SUM(itens_criticos_tvd)::bigint AS itens_criticos_tvd,
    SUM(itens_risco_tvd)::bigint AS itens_risco_tvd
FROM gold.nr_tvd_daily
GROUP BY id_customer, data;

CREATE UNIQUE INDEX ux_nr_tvd_daily_summary_customer_data
    ON gold.nr_tvd_daily_summary (id_customer, data);

CREATE MATERIALIZED VIEW gold.nr_ivd_daily_summary AS
SELECT
    id_customer,
    data,
    NULL::text AS rede,
    NULL::text AS bandeira,
    NULL::text AS uf,
    NULL::text AS cidade,
    NULL::text AS tipo_local,
    NULL::text AS loja,
    NULL::text AS regiao,
    NULL::text AS deposito,
    NULL::text AS tp_activity_level,
    NULL::text AS item,
    NULL::text AS descricao_marca,
    NULL::text AS hierarquia_1,
    NULL::text AS hierarquia_2,
    NULL::text AS hierarquia_3,
    NULL::text AS hierarquia_4,
    NULL::text AS unidade_medida,
    SUM(ivd)::double precision AS ivd,
    SUM(itens_criticos_ivd)::bigint AS itens_criticos_ivd,
    SUM(itens_risco_ivd)::bigint AS itens_risco_ivd
FROM gold.nr_ivd_daily
GROUP BY id_customer, data;

CREATE UNIQUE INDEX ux_nr_ivd_daily_summary_customer_data
    ON gold.nr_ivd_daily_summary (id_customer, data);

COMMENT ON MATERIALIZED VIEW gold.nr_tvd_daily_summary IS
'Tenant/day additive TVD headline totals; detailed filters use nr_tvd_daily.';
COMMENT ON MATERIALIZED VIEW gold.nr_ivd_daily_summary IS
'Tenant/day additive IVD headline totals; detailed filters use nr_ivd_daily.';

ANALYZE gold.nr_tvd_daily_summary;
ANALYZE gold.nr_ivd_daily_summary;

COMMIT;
