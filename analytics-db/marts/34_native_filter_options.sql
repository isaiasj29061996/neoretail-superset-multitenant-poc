-- Small tenant-aware source for Superset native-filter option lists.
--
-- Filters still apply to every scoped chart by column name. This mart only
-- replaces the expensive SELECT DISTINCT used to populate dropdowns from
-- multi-gigabyte serving marts.

BEGIN;

DROP MATERIALIZED VIEW IF EXISTS gold.nr_filter_options;

CREATE MATERIALIZED VIEW gold.nr_filter_options AS
SELECT
    id_customer,
    rede::text AS rede,
    bandeira::text AS bandeira,
    uf::text AS uf,
    cidade::text AS cidade,
    tipo_local::text AS tipo_local,
    loja::text AS loja,
    regiao::text AS regiao,
    COALESCE(loja, nome_da_loja, id_location)::text AS deposito,
    NULL::text AS tp_activity_level,
    NULL::text AS activity_level,
    NULL::text AS nivel_atividade,
    NULL::text AS descricao_marca,
    NULL::text AS hierarquia_1,
    NULL::text AS hierarquia_2,
    NULL::text AS hierarquia_3,
    NULL::text AS hierarquia_4,
    NULL::text AS item,
    NULL::text AS unidade_medida
FROM gold.dim_local

UNION ALL

SELECT
    id_customer,
    NULL::text, NULL::text, NULL::text, NULL::text, NULL::text, NULL::text,
    NULL::text, NULL::text, NULL::text, NULL::text, NULL::text,
    descricao_marca::text,
    hierarquia_1::text,
    hierarquia_2::text,
    hierarquia_3::text,
    hierarquia_4::text,
    item::text,
    NULL::text
FROM gold.dim_itens

UNION ALL

SELECT
    id_customer,
    NULL::text, NULL::text, NULL::text, NULL::text, NULL::text, NULL::text,
    NULL::text, NULL::text,
    tp_activity_level::text,
    nm_activity_level::text,
    tp_activity_level::text,
    NULL::text, NULL::text, NULL::text, NULL::text, NULL::text, NULL::text,
    NULL::text
FROM gold.dim_nivel_atividade

UNION ALL

SELECT DISTINCT
    id_customer,
    NULL::text, NULL::text, NULL::text, NULL::text, NULL::text, NULL::text,
    NULL::text, NULL::text, NULL::text, NULL::text, NULL::text,
    NULL::text, NULL::text, NULL::text, NULL::text, NULL::text, NULL::text,
    'unidade'::text
FROM gold.dim_customer;

CREATE INDEX ix_nr_filter_options_customer
    ON gold.nr_filter_options (id_customer);
CREATE INDEX ix_nr_filter_options_customer_location
    ON gold.nr_filter_options (id_customer, rede, bandeira, uf, cidade, tipo_local, loja);
CREATE INDEX ix_nr_filter_options_customer_product
    ON gold.nr_filter_options (
        id_customer, descricao_marca, hierarquia_1, hierarquia_2,
        hierarquia_3, hierarquia_4, item
    );
CREATE INDEX ix_nr_filter_options_customer_activity
    ON gold.nr_filter_options (id_customer, tp_activity_level, nivel_atividade);

COMMENT ON MATERIALIZED VIEW gold.nr_filter_options IS
'Tenant-aware location, product, activity and unit options for Superset native filters.';

ANALYZE gold.nr_filter_options;

COMMIT;
