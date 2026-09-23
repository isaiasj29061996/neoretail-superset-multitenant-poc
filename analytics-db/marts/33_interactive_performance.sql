-- Additional serving objects focused on interactive dashboard latency.
--
-- The gap charts previously scanned every daily row from
-- nr_panorama_opportunities and evaluated CASE expressions to keep only the
-- month/week closing dates. This mart materializes only those closing
-- snapshots while preserving every native-filter dimension.

BEGIN;

DROP MATERIALIZED VIEW IF EXISTS gold.nr_panorama_gap_periodic;

CREATE MATERIALIZED VIEW gold.nr_panorama_gap_periodic AS
SELECT
    o.id_customer,
    o.data,
    'mensal'::text AS period_type,
    o.rede,
    o.bandeira,
    o.uf,
    o.cidade,
    o.tipo_local,
    o.loja,
    o.regiao,
    o.deposito,
    o.tp_activity_level,
    o.item,
    o.descricao_marca,
    o.hierarquia_1,
    o.hierarquia_2,
    o.hierarquia_3,
    o.hierarquia_4,
    o.unidade_medida,
    SUM(COALESCE(o.tvd_simplificado, 0)) AS tvd,
    SUM(COALESCE(o.ivd_simplificado, 0)) AS ivd
FROM gold.nr_panorama_opportunities o
WHERE o.data = o.month_end_data
GROUP BY
    o.id_customer, o.data, o.rede, o.bandeira, o.uf, o.cidade,
    o.tipo_local, o.loja, o.regiao, o.deposito, o.tp_activity_level,
    o.item, o.descricao_marca, o.hierarquia_1, o.hierarquia_2,
    o.hierarquia_3, o.hierarquia_4, o.unidade_medida

UNION ALL

SELECT
    o.id_customer,
    o.data,
    'semanal'::text AS period_type,
    o.rede,
    o.bandeira,
    o.uf,
    o.cidade,
    o.tipo_local,
    o.loja,
    o.regiao,
    o.deposito,
    o.tp_activity_level,
    o.item,
    o.descricao_marca,
    o.hierarquia_1,
    o.hierarquia_2,
    o.hierarquia_3,
    o.hierarquia_4,
    o.unidade_medida,
    SUM(COALESCE(o.tvd_simplificado, 0)) AS tvd,
    SUM(COALESCE(o.ivd_simplificado, 0)) AS ivd
FROM gold.nr_panorama_opportunities o
WHERE o.data = o.week_end_data
GROUP BY
    o.id_customer, o.data, o.rede, o.bandeira, o.uf, o.cidade,
    o.tipo_local, o.loja, o.regiao, o.deposito, o.tp_activity_level,
    o.item, o.descricao_marca, o.hierarquia_1, o.hierarquia_2,
    o.hierarquia_3, o.hierarquia_4, o.unidade_medida;

CREATE INDEX ix_nr_panorama_gap_customer_period_data
    ON gold.nr_panorama_gap_periodic (id_customer, period_type, data);
CREATE INDEX ix_nr_panorama_gap_customer_retail
    ON gold.nr_panorama_gap_periodic (id_customer, period_type, rede, bandeira);
CREATE INDEX ix_nr_panorama_gap_customer_place
    ON gold.nr_panorama_gap_periodic (
        id_customer, period_type, uf, cidade, tipo_local, loja
    );
CREATE INDEX ix_nr_panorama_gap_customer_product
    ON gold.nr_panorama_gap_periodic (
        id_customer, period_type, descricao_marca, hierarquia_1,
        hierarquia_2, hierarquia_3, item
    );

COMMENT ON MATERIALIZED VIEW gold.nr_panorama_gap_periodic IS
'Month/week closing TVD-IVD snapshots for Panorama; avoids scanning every daily opportunity row interactively.';

ANALYZE gold.nr_panorama_gap_periodic;

COMMIT;
