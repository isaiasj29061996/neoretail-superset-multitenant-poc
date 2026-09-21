-- Certified Power BI semantic contracts for the Overview dashboard.
--
-- The compact marts below are the default interactive path. They retain a
-- real conversion selector (including the Power BI `valor` branch), calculate
-- sell-out region by region, and expose additive components for ROI/Markup.

BEGIN;

DROP MATERIALIZED VIEW IF EXISTS gold.nr_overview_semantic_default;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_osa_semantic_default;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_conversion_options;

CREATE MATERIALIZED VIEW gold.nr_conversion_options AS
SELECT DISTINCT id_customer, nm_measure
FROM gold.dim_conversao
WHERE nm_measure IS NOT NULL
UNION
SELECT DISTINCT id_customer, 'valor'::text
FROM gold.fato_historico;

CREATE UNIQUE INDEX ux_nr_conversion_options
    ON gold.nr_conversion_options (id_customer, nm_measure);

CREATE MATERIALIZED VIEW gold.nr_overview_semantic_default AS
WITH history_region AS (
    SELECT
        h.data,
        h.id_customer,
        h.tp_activity_level,
        CASE h.tp_activity_level
            WHEN 'F' THEN 'Fast Mover'
            WHEN 'S' THEN 'Slow Mover'
            WHEN 'U' THEN 'Ultra Slow Mover'
            WHEN 'N' THEN 'New Mover'
            ELSE NULL
        END AS activity_level,
        h.regiao,
        SUM(COALESCE(h.faturamento, 0))::double precision AS faturamento_sum,
        SUM(COALESCE(h.volume_unidades, 0))::double precision AS volume_sum,
        SUM(COALESCE(h.avg_sales_price, 0))::double precision AS price_sum,
        COUNT(h.avg_sales_price)::bigint AS price_count,
        SUM(COALESCE(h.volume_unidades, 0) * COALESCE(h.avg_price_cost, 0))::double precision AS sales_cost_sum,
        SUM(COALESCE(h.estoque_medio, 0) * COALESCE(h.avg_price_cost, 0))::double precision AS stock_cost_sum,
        SUM(COALESCE(h.estoque_unidades, 0))::double precision AS stock_units_sum,
        SUM(CASE WHEN COALESCE(h.giro, 0) > 0 THEN h.giro ELSE 0 END)::double precision AS giro_sum_positive,
        COUNT(h.giro) FILTER (WHERE COALESCE(h.giro, 0) > 0)::bigint AS giro_count_positive,
        SUM(COALESCE(h.qtd_problemas_osa, 0))::bigint AS osa_problem_sum,
        SUM(COALESCE(h.qtd_item_ativo_osa, 0))::bigint AS osa_active_sum
    FROM gold.nr_overview_history h
    GROUP BY h.data, h.id_customer, h.tp_activity_level, h.regiao
), factor_region AS (
    SELECT
        h.data,
        h.id_customer,
        h.tp_activity_level,
        h.regiao,
        c.nm_measure,
        MAX(c.conversion_rate)::double precision AS conversion_rate
    FROM (
        SELECT DISTINCT data, id_customer, tp_activity_level, regiao, id_item
        FROM gold.nr_overview_history
    ) h
    JOIN gold.dim_conversao c
      ON c.id_customer = h.id_customer
     AND c.id_item::text = h.id_item
    GROUP BY h.data, h.id_customer, h.tp_activity_level, h.regiao, c.nm_measure
), expanded AS (
    SELECT r.*, f.nm_measure, f.conversion_rate
    FROM history_region r
    JOIN factor_region f
      ON f.data = r.data
     AND f.id_customer = r.id_customer
     AND f.tp_activity_level IS NOT DISTINCT FROM r.tp_activity_level
     AND f.regiao IS NOT DISTINCT FROM r.regiao
    UNION ALL
    SELECT r.*, 'valor'::text AS nm_measure, NULL::double precision AS conversion_rate
    FROM history_region r
), monthly_activity AS (
    SELECT
        data,
        id_customer,
        tp_activity_level,
        activity_level,
        nm_measure,
        SUM(
            CASE
                WHEN faturamento_sum > 0 THEN faturamento_sum
                WHEN conversion_rate IS NOT NULL AND price_count > 0
                THEN (volume_sum * conversion_rate)
                   * ((price_sum / price_count) * conversion_rate)
                ELSE 0
            END
        )::double precision AS sellout_sum,
        SUM(sales_cost_sum)::double precision AS sales_cost_sum,
        CASE
            WHEN nm_measure = 'valor' THEN SUM(faturamento_sum)
            ELSE SUM(volume_sum) * MAX(conversion_rate)
        END::double precision AS sales_qty_sum,
        SUM(stock_cost_sum)::double precision AS stock_cost_sum,
        CASE
            WHEN nm_measure = 'valor' THEN SUM(faturamento_sum)
            ELSE SUM(stock_units_sum) * MAX(conversion_rate)
        END::double precision AS stock_qty_sum,
        SUM(giro_sum_positive)::double precision AS giro_sum_positive,
        SUM(giro_count_positive)::bigint AS giro_count_positive,
        SUM(osa_problem_sum)::bigint AS osa_problem_sum,
        SUM(osa_active_sum)::bigint AS osa_active_sum
    FROM expanded
    WHERE activity_level IS NOT NULL
    GROUP BY data, id_customer, tp_activity_level, activity_level, nm_measure
), all_region AS (
    SELECT
        data, id_customer, regiao, nm_measure,
        SUM(faturamento_sum)::double precision AS faturamento_sum,
        SUM(volume_sum)::double precision AS volume_sum,
        SUM(price_sum)::double precision AS price_sum,
        SUM(price_count)::bigint AS price_count,
        MAX(conversion_rate)::double precision AS conversion_rate,
        SUM(sales_cost_sum)::double precision AS sales_cost_sum,
        SUM(stock_cost_sum)::double precision AS stock_cost_sum,
        SUM(stock_units_sum)::double precision AS stock_units_sum,
        SUM(giro_sum_positive)::double precision AS giro_sum_positive,
        SUM(giro_count_positive)::bigint AS giro_count_positive,
        SUM(osa_problem_sum)::bigint AS osa_problem_sum,
        SUM(osa_active_sum)::bigint AS osa_active_sum
    FROM expanded
    GROUP BY data, id_customer, regiao, nm_measure
), monthly_all AS (
    SELECT
        data, id_customer, nm_measure,
        SUM(CASE WHEN faturamento_sum > 0 THEN faturamento_sum
                 WHEN conversion_rate IS NOT NULL AND price_count > 0
                 THEN (volume_sum * conversion_rate) * ((price_sum / price_count) * conversion_rate)
                 ELSE 0 END)::double precision AS sellout_sum,
        SUM(sales_cost_sum)::double precision AS sales_cost_sum,
        CASE WHEN nm_measure = 'valor' THEN SUM(faturamento_sum)
             ELSE SUM(volume_sum) * MAX(conversion_rate) END::double precision AS sales_qty_sum,
        SUM(stock_cost_sum)::double precision AS stock_cost_sum,
        CASE WHEN nm_measure = 'valor' THEN SUM(faturamento_sum)
             ELSE SUM(stock_units_sum) * MAX(conversion_rate) END::double precision AS stock_qty_sum,
        SUM(giro_sum_positive)::double precision AS giro_sum_positive,
        SUM(giro_count_positive)::bigint AS giro_count_positive,
        SUM(osa_problem_sum)::bigint AS osa_problem_sum,
        SUM(osa_active_sum)::bigint AS osa_active_sum
    FROM all_region
    GROUP BY data, id_customer, nm_measure
)
SELECT
    m.*,
    'activity'::text AS semantic_scope,
    TRUE AS semantic_precomputed,
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
    NULL::text AS hierarquia_3
FROM monthly_activity m
UNION ALL
SELECT
    m.data, m.id_customer, NULL::text AS tp_activity_level,
    NULL::text AS activity_level, m.nm_measure,
    m.sellout_sum, m.sales_cost_sum, m.sales_qty_sum, m.stock_cost_sum,
    m.stock_qty_sum, m.giro_sum_positive, m.giro_count_positive,
    m.osa_problem_sum, m.osa_active_sum,
    'all'::text AS semantic_scope, TRUE AS semantic_precomputed,
    NULL::text, NULL::text, NULL::text, NULL::text, NULL::text, NULL::text,
    NULL::text, NULL::text, NULL::text, NULL::text, NULL::text, NULL::text
FROM monthly_all m;

CREATE UNIQUE INDEX ux_nr_overview_semantic_default
    ON gold.nr_overview_semantic_default (
        id_customer, data, nm_measure, semantic_scope, tp_activity_level
    );

CREATE MATERIALIZED VIEW gold.nr_osa_semantic_default AS
WITH loss_base AS (
    SELECT
        f.data,
        f.id_customer,
        SUM(COALESCE(f.qtd_perda_osa, 0))::double precision AS loss_qty_sum,
        SUM(COALESCE(f.preco_medio, 0))::double precision AS price_sum,
        COUNT(f.preco_medio)::bigint AS price_count
    FROM gold.fato_mensal_causa_osa f
    GROUP BY f.data, f.id_customer
), loss_factor AS (
    SELECT
        f.data,
        f.id_customer,
        c.nm_measure,
        MAX(c.conversion_rate)::double precision AS conversion_rate
    FROM (
        SELECT DISTINCT data, id_customer, id_item
        FROM gold.fato_mensal_causa_osa
    ) f
    JOIN gold.dim_conversao c
      ON c.id_customer = f.id_customer
     AND c.id_item::text = f.id_item
    GROUP BY f.data, f.id_customer, c.nm_measure
), loss AS (
    SELECT
        b.data,
        b.id_customer,
        f.nm_measure,
        CASE WHEN b.price_count > 0
             THEN b.loss_qty_sum * f.conversion_rate * (b.price_sum / b.price_count)
             ELSE NULL END::double precision AS osa_loss_sum
    FROM loss_base b
    JOIN loss_factor f USING (data, id_customer)
    UNION ALL
    SELECT data, id_customer, 'valor'::text, NULL::double precision
    FROM loss_base
), osa_ratio AS (
    SELECT
        data,
        id_customer,
        SUM(osa_problem_sum)::bigint AS osa_problem_sum,
        SUM(osa_active_sum)::bigint AS osa_active_sum
    FROM gold.nr_overview_default_summary
    GROUP BY data, id_customer
), latest_month AS (
    SELECT id_customer, MAX(data) AS data
    FROM gold.nr_overview_history
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
        )::bigint AS osa_risk_count
    FROM gold.calculo_oportunidades o
    LEFT JOIN gold.dim_nivel_atividade a
      ON a.id_customer = o.id_customer
     AND a.tp_activity_level = o.max_tp_activity_level
    GROUP BY o.id_customer
)
SELECT
    r.data,
    r.id_customer,
    l.nm_measure,
    r.osa_problem_sum,
    r.osa_active_sum,
    l.osa_loss_sum,
    CASE WHEN r.data = d.data THEN COALESCE(t.osa_critical_count, 0) ELSE 0 END AS osa_critical_count,
    CASE WHEN r.data = d.data THEN COALESCE(t.osa_risk_count, 0) ELSE 0 END AS osa_risk_count
FROM osa_ratio r
JOIN loss l USING (data, id_customer)
JOIN latest_month d USING (id_customer)
LEFT JOIN tasks t USING (id_customer);

CREATE UNIQUE INDEX ux_nr_osa_semantic_default
    ON gold.nr_osa_semantic_default (id_customer, data, nm_measure);

COMMENT ON MATERIALIZED VIEW gold.nr_overview_semantic_default IS
'Certified compact Overview metrics by tenant, month, activity and selected conversion measure.';
COMMENT ON MATERIALIZED VIEW gold.nr_osa_semantic_default IS
'Certified compact OSA ratio, monthly loss and non-distinct task counts by tenant and measure.';

ANALYZE gold.nr_conversion_options;
ANALYZE gold.nr_overview_semantic_default;
ANALYZE gold.nr_osa_semantic_default;

COMMIT;
