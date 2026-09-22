-- Semantic serving contract for "Visao geral quantidade".
-- Additive components stay separate so MTD/U3M/LY ratios are recomputed in
-- the chart instead of averaging monthly percentages.

BEGIN;

DROP MATERIALIZED VIEW IF EXISTS gold.nr_overview_quantity_default;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_overview_quantity_detail;

CREATE MATERIALIZED VIEW gold.nr_overview_quantity_detail AS
SELECT
    f.mes_ano AS data,
    f.id_customer,
    f.id_item,
    f.id_location,
    COALESCE(f.cnpj, l.cnpj) AS cnpj,
    COALESCE(f.ean, i.cd_ean) AS ean,
    f.positivacao,
    f.volume_unidades,
    f.faturamento,
    f.qtd_perda_osa,
    f.avg_sales_price,
    f.qtd_problemas_osa,
    f.qtd_item_ativo_osa,
    f.rup,
    f.status_item_geral,
    f.est_virtual,
    f.estoque_unidades,
    f.demanda_media,
    f.tp_activity_level,
    l.rede, l.bandeira, l.uf, l.cidade, l.tipo_local, l.loja, l.regiao,
    i.item, i.descricao_marca, i.hierarquia_1, i.hierarquia_2, i.hierarquia_3
FROM gold.fato_historico f
LEFT JOIN gold.dim_local l
  ON l.id_customer = f.id_customer AND l.id_location = f.id_location
LEFT JOIN gold.dim_itens i
  ON i.id_customer = f.id_customer AND i.id_item = f.id_item;

CREATE INDEX ix_nr_overview_quantity_detail_customer_data
    ON gold.nr_overview_quantity_detail (id_customer, data);
CREATE INDEX ix_nr_overview_quantity_detail_retail
    ON gold.nr_overview_quantity_detail (id_customer, rede, bandeira);
CREATE INDEX ix_nr_overview_quantity_detail_place
    ON gold.nr_overview_quantity_detail (id_customer, uf, cidade, tipo_local, loja);
CREATE INDEX ix_nr_overview_quantity_detail_activity
    ON gold.nr_overview_quantity_detail (id_customer, tp_activity_level);
CREATE INDEX ix_nr_overview_quantity_detail_product
    ON gold.nr_overview_quantity_detail
       (id_customer, descricao_marca, hierarquia_1, hierarquia_2, hierarquia_3, item);

CREATE MATERIALIZED VIEW gold.nr_overview_quantity_default AS
WITH monthly AS (
    SELECT
        data,
        id_customer,
        SUM(COALESCE(volume_unidades, 0))::double precision AS volume_sum,
        SUM(COALESCE(faturamento, 0))::double precision AS faturamento_sum,
        SUM(COALESCE(qtd_perda_osa, 0))::double precision AS loss_qty_sum,
        SUM(COALESCE(avg_sales_price, 0)) FILTER (WHERE faturamento > 0)::double precision AS price_sum,
        COUNT(avg_sales_price) FILTER (WHERE faturamento > 0)::bigint AS price_count,
        SUM(COALESCE(qtd_problemas_osa, 0))::double precision AS osa_problem_sum,
        SUM(COALESCE(qtd_item_ativo_osa, 0))::double precision AS osa_active_sum,
        SUM(COALESCE(rup, 0))::double precision AS rupture_sum,
        SUM(COALESCE(status_item_geral, 0))::double precision AS status_sum,
        SUM(COALESCE(est_virtual, 0))::double precision AS isv_sum,
        SUM(COALESCE(estoque_unidades, 0))::double precision AS stock_sum,
        SUM(COALESCE(demanda_media, 0))::double precision AS demand_sum,
        COUNT(DISTINCT cnpj) FILTER (WHERE positivacao = 1)::bigint AS store_count,
        COUNT(DISTINCT ean) FILTER (WHERE positivacao = 1)::bigint AS item_count
    FROM gold.nr_overview_quantity_detail
    GROUP BY data, id_customer
), factors AS (
    SELECT
        d.data,
        d.id_customer,
        c.nm_measure,
        MAX(c.conversion_rate)::double precision AS conversion_factor
    FROM (
        SELECT DISTINCT data, id_customer, id_item
        FROM gold.nr_overview_quantity_detail
    ) d
    JOIN gold.dim_conversao c
      ON c.id_customer = d.id_customer AND c.id_item::text = d.id_item
    GROUP BY d.data, d.id_customer, c.nm_measure
), distribution_u3m AS (
    SELECT
        anchor.id_customer,
        anchor.data,
        COUNT(DISTINCT d.cnpj) FILTER (WHERE d.positivacao = 1)::bigint AS store_count_u3m,
        COUNT(DISTINCT d.ean) FILTER (WHERE d.positivacao = 1)::bigint AS item_count_u3m
    FROM (SELECT DISTINCT id_customer, data FROM gold.nr_overview_quantity_detail) anchor
    JOIN gold.nr_overview_quantity_detail d
      ON d.id_customer = anchor.id_customer
     AND d.data >= anchor.data - INTERVAL '2 months'
     AND d.data <= anchor.data
    GROUP BY anchor.id_customer, anchor.data
), expanded AS (
    SELECT m.*, f.nm_measure, f.conversion_factor
    FROM monthly m JOIN factors f USING (data, id_customer)
    UNION ALL
    SELECT m.*, 'valor'::text, NULL::double precision FROM monthly m
), latest_month AS (
    SELECT id_customer, MAX(data) AS data
    FROM gold.nr_overview_quantity_detail
    GROUP BY id_customer
), tasks AS (
    SELECT
        o.id_customer,
        COUNT(o.id_item) FILTER (
            WHERE COALESCE(o.qtd_problemas_osa_m0, 0) > 0
              AND a.nm_activity_level = 'Fast Mover'
        )::bigint AS osa_critical_count,
        COUNT(o.id_item) FILTER (
            WHERE COALESCE(o.qtd_problemas_osa_m0, 0) > 0
              AND o.max_tp_activity_level = 'S'
        )::bigint AS osa_risk_count,
        COUNT(o.id_item) FILTER (
            WHERE COALESCE(o.rup, 0) > 0 AND o.max_tp_activity_level = 'F'
        )::bigint AS rupture_critical_count,
        COUNT(o.id_item) FILTER (
            WHERE COALESCE(o.rup, 0) > 0 AND o.max_tp_activity_level = 'S'
        )::bigint AS rupture_risk_count,
        COUNT(o.id_item) FILTER (
            WHERE COALESCE(o.est_virtual, 0) > 0 AND o.max_tp_activity_level = 'F'
        )::bigint AS isv_critical_count,
        COUNT(o.id_item) FILTER (
            WHERE COALESCE(o.est_virtual, 0) > 0 AND o.max_tp_activity_level = 'S'
        )::bigint AS isv_risk_count
    FROM gold.calculo_oportunidades o
    LEFT JOIN gold.dim_nivel_atividade a
      ON a.id_customer = o.id_customer
     AND a.tp_activity_level = o.max_tp_activity_level
    GROUP BY o.id_customer
)
SELECT
    e.data,
    e.id_customer,
    e.nm_measure,
    CASE WHEN e.nm_measure = 'valor' THEN e.faturamento_sum
         ELSE e.volume_sum * e.conversion_factor END::double precision AS sales_sum,
    CASE WHEN e.nm_measure = 'valor' THEN NULL
         ELSE e.loss_qty_sum * e.conversion_factor END::double precision AS loss_sum,
    (e.price_sum * e.conversion_factor)::double precision AS price_numerator,
    e.price_count,
    e.osa_problem_sum,
    e.osa_active_sum,
    e.rupture_sum,
    e.status_sum,
    e.isv_sum,
    e.stock_sum,
    e.demand_sum,
    e.store_count,
    e.item_count,
    COALESCE(du.store_count_u3m, 0)::bigint AS store_count_u3m,
    COALESCE(du.item_count_u3m, 0)::bigint AS item_count_u3m,
    CASE WHEN e.data = lm.data THEN COALESCE(t.osa_critical_count, 0) ELSE 0 END AS osa_critical_count,
    CASE WHEN e.data = lm.data THEN COALESCE(t.osa_risk_count, 0) ELSE 0 END AS osa_risk_count,
    CASE WHEN e.data = lm.data THEN COALESCE(t.rupture_critical_count, 0) ELSE 0 END AS rupture_critical_count,
    CASE WHEN e.data = lm.data THEN COALESCE(t.rupture_risk_count, 0) ELSE 0 END AS rupture_risk_count,
    CASE WHEN e.data = lm.data THEN COALESCE(t.isv_critical_count, 0) ELSE 0 END AS isv_critical_count,
    CASE WHEN e.data = lm.data THEN COALESCE(t.isv_risk_count, 0) ELSE 0 END AS isv_risk_count,
    NULL::text AS rede, NULL::text AS bandeira, NULL::text AS uf,
    NULL::text AS cidade, NULL::text AS tipo_local, NULL::text AS loja,
    NULL::text AS regiao, NULL::text AS tp_activity_level,
    NULL::text AS item, NULL::text AS descricao_marca,
    NULL::text AS hierarquia_1, NULL::text AS hierarquia_2, NULL::text AS hierarquia_3
FROM expanded e
JOIN latest_month lm ON lm.id_customer = e.id_customer
LEFT JOIN distribution_u3m du
  ON du.id_customer = e.id_customer AND du.data = e.data
LEFT JOIN tasks t ON t.id_customer = e.id_customer;

CREATE UNIQUE INDEX ux_nr_overview_quantity_default
    ON gold.nr_overview_quantity_default (id_customer, data, nm_measure);

COMMENT ON MATERIALIZED VIEW gold.nr_overview_quantity_default IS
'Quantity overview DAX components at tenant/month/measure grain; distribution remains zero when source positivacao is absent.';

ANALYZE gold.nr_overview_quantity_detail;
ANALYZE gold.nr_overview_quantity_default;

COMMIT;
