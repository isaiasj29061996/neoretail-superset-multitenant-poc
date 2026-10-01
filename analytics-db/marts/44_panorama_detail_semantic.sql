-- Compact serving mart for Panorama > Analise detalhada.
--
-- The interactive table needs DAX-like semantics that are expensive to rebuild
-- five times inside Superset metadata discovery.  This mart computes the
-- unfiltered/default path once during the serving refresh and leaves filtered
-- requests to the virtual dataset fallback.
--
-- Semantics preserved:
-- * latest snapshot per tenant;
-- * trailing 12-month ROI = SUM(monthly ROI);
-- * Markup = Sell Out / Venda Custo;
-- * OSA = 1 - problems / active;
-- * Ruptura and ISV use STATUS_ITEM_GERAL;
-- * quantity/price/stock/loss honor the selected conversion measure.

BEGIN;

DROP MATERIALIZED VIEW IF EXISTS gold.nr_panorama_detail_default;

CREATE MATERIALIZED VIEW gold.nr_panorama_detail_default AS
WITH customer_latest AS (
    SELECT id_customer, MAX(data)::date AS latest_data
    FROM gold.nr_panorama_comparison_history_detail
    GROUP BY id_customer
), raw AS (
    SELECT
        h.data::date AS data,
        h.id_customer,
        h.id_item::text AS id_item,
        h.volume_unidades,
        h.faturamento,
        h.estoque_unidades,
        h.qtd_perda_osa,
        h.rup,
        h.est_virtual,
        h.giro,
        h.qtd_problemas_osa,
        h.qtd_item_ativo_osa,
        h.status_item_geral,
        h.avg_sales_price,
        h.avg_price_cost,
        h.estoque_medio,
        h.regiao::text AS regiao,
        h.rede::text AS rede,
        h.hierarquia_1::text AS hierarquia_1,
        h.item::text AS item,
        CASE h.tp_activity_level
          WHEN 'F' THEN 'Fast Mover'
          WHEN 'S' THEN 'Slow Mover'
          WHEN 'US' THEN 'Ultra Slow Mover'
          WHEN 'U' THEN 'Ultra Slow Mover'
          WHEN 'N' THEN 'New Mover'
          ELSE COALESCE(h.tp_activity_level, 'Outros')
        END::text AS activity_level
    FROM gold.nr_panorama_comparison_history_detail h
    JOIN customer_latest d
      ON d.id_customer=h.id_customer
     AND h.data::date > d.latest_data - INTERVAL '12 months'
     AND h.data::date <= d.latest_data
), measures AS (
    SELECT DISTINCT id_customer,nm_measure
    FROM gold.nr_conversion_options
), expanded AS (
    SELECT
        r.*,
        m.nm_measure,
        c.conversion_rate::double precision AS conversion_rate
    FROM raw r
    JOIN measures m
      ON m.id_customer=r.id_customer
    LEFT JOIN gold.dim_conversao c
      ON c.id_customer=r.id_customer
     AND c.id_item::text=r.id_item
     AND c.nm_measure=m.nm_measure
), monthly AS (
    SELECT
        data,
        id_customer,
        nm_measure,
        CASE
          WHEN GROUPING(regiao)=0 THEN 'regiao'
          WHEN GROUPING(rede)=0 THEN 'rede'
          WHEN GROUPING(hierarquia_1)=0 THEN 'hierarquia_1'
          WHEN GROUPING(item)=0 THEN 'item'
          WHEN GROUPING(activity_level)=0 THEN 'activity_level'
        END::text AS detail_scope,
        CASE
          WHEN GROUPING(regiao)=0 THEN regiao
          WHEN GROUPING(rede)=0 THEN rede
          WHEN GROUPING(hierarquia_1)=0 THEN hierarquia_1
          WHEN GROUPING(item)=0 THEN item
          WHEN GROUPING(activity_level)=0 THEN activity_level
        END::text AS dimension_value,
        MAX(conversion_rate)::double precision AS month_conversion_factor,
        SUM(COALESCE(faturamento,0))::double precision AS faturamento_sum,
        SUM(COALESCE(volume_unidades,0))::double precision AS volume_sum,
        SUM(COALESCE(volume_unidades,0)*COALESCE(avg_price_cost,0))::double precision AS sales_cost_sum,
        SUM(COALESCE(estoque_medio,0)*COALESCE(avg_price_cost,0))::double precision AS stock_cost_sum,
        SUM(COALESCE(estoque_unidades,0))::double precision AS stock_units_sum,
        SUM(COALESCE(qtd_perda_osa,0))::double precision AS loss_qty_sum,
        SUM(COALESCE(avg_sales_price,0)) FILTER (WHERE faturamento>0)::double precision AS price_sum,
        COUNT(avg_sales_price) FILTER (WHERE faturamento>0)::bigint AS price_count,
        SUM(COALESCE(giro,0)) FILTER (WHERE giro>0)::double precision AS giro_sum,
        COUNT(giro) FILTER (WHERE giro>0)::bigint AS giro_count,
        SUM(COALESCE(qtd_problemas_osa,0))::double precision AS osa_problem_sum,
        SUM(COALESCE(qtd_item_ativo_osa,0))::double precision AS osa_active_sum,
        SUM(COALESCE(rup,0))::double precision AS rupture_sum,
        SUM(COALESCE(status_item_geral,0))::double precision AS status_sum,
        SUM(COALESCE(est_virtual,0))::double precision AS isv_sum
    FROM expanded
    GROUP BY data,id_customer,nm_measure,GROUPING SETS (
        (regiao),
        (rede),
        (hierarquia_1),
        (item),
        (activity_level)
    )
), factorized AS (
    SELECT
        m.*,
        COALESCE(
            MAX(month_conversion_factor) OVER (
                PARTITION BY id_customer,detail_scope,dimension_value,nm_measure
            ),
            CASE WHEN nm_measure='valor' THEN 1.0 END
        )::double precision AS conversion_factor
    FROM monthly m
), calculated AS (
    SELECT
        m.*,
        CASE
          WHEN faturamento_sum>0 THEN faturamento_sum
          WHEN conversion_factor IS NOT NULL AND price_count>0
          THEN (volume_sum*conversion_factor)
             * ((price_sum/price_count)*conversion_factor)
          ELSE NULL
        END::double precision AS sellout_value,
        CASE
          WHEN nm_measure='valor' THEN faturamento_sum
          WHEN conversion_factor IS NULL THEN NULL
          ELSE volume_sum*conversion_factor
        END::double precision AS sales_qty_value,
        CASE
          WHEN conversion_factor IS NULL OR price_count=0 THEN NULL
          ELSE (price_sum/price_count)*conversion_factor
        END::double precision AS price_value,
        CASE
          WHEN conversion_factor IS NULL THEN NULL
          ELSE stock_units_sum*conversion_factor
        END::double precision AS stock_qty_value,
        CASE
          WHEN conversion_factor IS NULL THEN NULL
          ELSE loss_qty_sum*conversion_factor
        END::double precision AS osa_loss_value
    FROM factorized m
), ratios AS (
    SELECT
        c.*,
        CASE WHEN sellout_value IS NULL OR sales_cost_sum=0 THEN 0
             ELSE sellout_value/sales_cost_sum END::double precision AS markup_value,
        CASE WHEN sellout_value IS NULL OR sales_cost_sum=0 THEN 0
             ELSE (sellout_value-sales_cost_sum)/NULLIF(stock_cost_sum,0)
        END::double precision AS roi_value,
        (giro_sum/NULLIF(giro_count,0))::double precision AS giro_value,
        (1-osa_problem_sum/NULLIF(osa_active_sum,0))::double precision AS osa_value,
        (rupture_sum/NULLIF(status_sum,0))::double precision AS rupture_value,
        (isv_sum/NULLIF(status_sum,0))::double precision AS isv_value,
        MAX(data) OVER (PARTITION BY id_customer,nm_measure)::date AS latest_data
    FROM calculated c
), final_rows AS (
    SELECT
        r.*,
        SUM(roi_value) OVER (
            PARTITION BY id_customer,detail_scope,dimension_value,nm_measure
        )::double precision AS roi_annual_value
    FROM ratios r
)
SELECT
    id_customer,
    detail_scope,
    dimension_value,
    nm_measure,
    sales_qty_value,
    sellout_value,
    sales_cost_sum::double precision AS sales_cost_value,
    markup_value,
    price_value,
    stock_cost_sum::double precision AS stock_cost_value,
    stock_qty_value,
    roi_value,
    roi_annual_value,
    giro_value,
    osa_value,
    rupture_value,
    isv_value,
    osa_loss_value
FROM final_rows
WHERE data=latest_data;

CREATE INDEX ix_nr_panorama_detail_default_lookup
    ON gold.nr_panorama_detail_default (
        id_customer, detail_scope, nm_measure, dimension_value
    );

COMMENT ON MATERIALIZED VIEW gold.nr_panorama_detail_default IS
'Compact default serving path for Panorama detailed analysis; filtered contexts fall back to the detailed history mart.';

ANALYZE gold.nr_panorama_detail_default;

COMMIT;
