-- Certified weekly serving contract for Panorama / Evolutivo de vendas.
-- Keeps value metrics independent from the conversion selector and exposes
-- additive quantity components for the exact Power BI measure semantics.

BEGIN;

DROP MATERIALIZED VIEW IF EXISTS gold.nr_panorama_sales_weekly_default;

CREATE MATERIALIZED VIEW gold.nr_panorama_sales_weekly_default AS
WITH weekly AS (
    SELECT
        id_time AS data,
        id_customer,
        MAX(cd_week) AS cd_week,
        SUM(COALESCE(faturamento, 0))::float8 AS faturamento_sum,
        SUM(COALESCE(volume_unidade, 0) * COALESCE(avg_sales_price, 0))::float8 AS fallback_sellout_sum,
        SUM(COALESCE(volume_unidade, 0) * COALESCE(avg_price_cost, 0))::float8 AS cost_sum,
        SUM(COALESCE(volume_unidade, 0))::float8 AS volume_sum,
        SUM(COALESCE(qtd_perda_osa, 0))::float8 AS loss_sum,
        SUM(COALESCE(avg_sales_price, 0)) FILTER (WHERE faturamento > 0)::float8 AS price_sum,
        COUNT(avg_sales_price) FILTER (WHERE faturamento > 0)::bigint AS price_count
    FROM gold.fato_semanal
    GROUP BY id_time, id_customer
), factors AS (
    SELECT
        w.data,
        w.id_customer,
        c.nm_measure,
        MAX(c.conversion_rate)::float8 AS conversion_factor
    FROM (SELECT DISTINCT id_time AS data, id_customer, id_item FROM gold.fato_semanal) w
    JOIN gold.dim_conversao c
      ON c.id_customer = w.id_customer AND c.id_item::text = w.id_item
    GROUP BY w.data, w.id_customer, c.nm_measure
)
SELECT
    w.data,
    w.cd_week,
    w.id_customer,
    f.nm_measure,
    CASE WHEN w.faturamento_sum > 0 THEN w.faturamento_sum
         ELSE w.fallback_sellout_sum END::float8 AS sellout_sum,
    w.cost_sum,
    (w.volume_sum * f.conversion_factor)::float8 AS sales_sum,
    (w.loss_sum * f.conversion_factor)::float8 AS loss_sum,
    (w.price_sum * f.conversion_factor)::float8 AS price_numerator,
    w.price_count,
    NULL::text AS rede, NULL::text AS bandeira, NULL::text AS uf,
    NULL::text AS cidade, NULL::text AS tipo_local, NULL::text AS loja,
    NULL::text AS regiao, NULL::text AS tp_activity_level,
    NULL::text AS activity_level, NULL::text AS item,
    NULL::text AS descricao_marca, NULL::text AS hierarquia_1,
    NULL::text AS hierarquia_2, NULL::text AS hierarquia_3
FROM weekly w
JOIN factors f USING (data, id_customer);

CREATE UNIQUE INDEX ux_nr_panorama_sales_weekly_default
    ON gold.nr_panorama_sales_weekly_default (id_customer, data, nm_measure);

COMMENT ON MATERIALIZED VIEW gold.nr_panorama_sales_weekly_default IS
'Panorama sales components at tenant/week/measure grain; consumed through a TOP-13 semantic dataset.';

ANALYZE gold.nr_panorama_sales_weekly_default;

COMMIT;
