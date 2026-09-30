-- Certified serving marts for Panorama > Evolutivo de estoque.
-- Covers Estoque, Giro x ROI, OSA and the weekly single-card TVD/IVD contract.
--
-- Business rules mirror the Power BI TMDL:
-- * monthly Giro = AVERAGE(GIRO) only where GIRO > 0;
-- * weekly Giro = AVERAGE(GIRO), but the tenant's latest CD_WEEK is BLANK;
-- * ROI = (Sell Out - Venda Custo) / Estoque Custo;
-- * OSA = 1 - Problemas / Ativos;
-- * Ruptura = RUP / STATUS_ITEM_GERAL;
-- * ISV = EST_VIRTUAL / STATUS_ITEM_GERAL;
-- * stock quantity follows the selected conversion factor;
-- * weekly timelines expose TOP 13 CD_WEEK and monthly rows for MTD/U3M cards.

BEGIN;

DROP MATERIALIZED VIEW IF EXISTS gold.nr_panorama_gap_weekly_card_default;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_panorama_gap_monthly_default;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_panorama_inventory_weekly_card_default;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_panorama_inventory_monthly_default;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_panorama_kpi_dimension_gap_default;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_panorama_kpi_dimension_history_default;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_panorama_comparison_gap_daily;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_panorama_comparison_history_detail;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_panorama_inventory_weekly_detail;

-- Supports the filtered fallback used by comparison matrices.  The base mart
-- already has a retail index, but adding the date makes the current-year
-- predicate selective before the daily aggregation.
CREATE INDEX IF NOT EXISTS ix_nr_panorama_opportunities_customer_rede_data
    ON gold.nr_panorama_opportunities (id_customer, rede, data);

CREATE MATERIALIZED VIEW gold.nr_panorama_comparison_history_detail AS
SELECT
    f.mes_ano::date AS data,
    f.id_customer,
    f.id_item,
    f.id_location,
    f.volume_unidades::double precision AS volume_unidades,
    f.faturamento::double precision AS faturamento,
    f.estoque_unidades::double precision AS estoque_unidades,
    f.estoque_medio::double precision AS estoque_medio,
    f.demanda_media::double precision AS demanda_media,
    f.qtd_perda_osa::double precision AS qtd_perda_osa,
    f.qtd_problemas_osa::double precision AS qtd_problemas_osa,
    f.qtd_item_ativo_osa::double precision AS qtd_item_ativo_osa,
    f.rup::double precision AS rup,
    f.est_virtual::double precision AS est_virtual,
    f.giro::double precision AS giro,
    f.avg_sales_price::double precision AS avg_sales_price,
    f.avg_price_cost::double precision AS avg_price_cost,
    f.status_item_geral::double precision AS status_item_geral,
    f.tp_activity_level,
    CASE f.tp_activity_level
      WHEN 'F' THEN 'Fast Mover'
      WHEN 'S' THEN 'Slow Mover'
      WHEN 'US' THEN 'Ultra Slow Mover'
      WHEN 'N' THEN 'New Mover'
      ELSE COALESCE(f.tp_activity_level, 'Outros')
    END AS activity_level,
    l.rede,
    l.bandeira,
    l.uf,
    l.cidade,
    l.tipo_local,
    l.loja,
    l.regiao,
    i.item,
    i.descricao_marca,
    i.hierarquia_1,
    i.hierarquia_2,
    i.hierarquia_3
FROM gold.fato_historico f
LEFT JOIN gold.dim_local l
  ON l.id_customer=f.id_customer AND l.id_location=f.id_location
LEFT JOIN gold.dim_itens i
  ON i.id_customer=f.id_customer AND i.id_item=f.id_item;

CREATE INDEX ix_nr_panorama_comparison_history_customer_data
    ON gold.nr_panorama_comparison_history_detail (id_customer, data);
CREATE INDEX ix_nr_panorama_comparison_history_item
    ON gold.nr_panorama_comparison_history_detail (id_customer, id_item, data);
CREATE INDEX ix_nr_panorama_comparison_history_retail
    ON gold.nr_panorama_comparison_history_detail (id_customer, rede, bandeira, loja);
CREATE INDEX ix_nr_panorama_comparison_history_place
    ON gold.nr_panorama_comparison_history_detail (id_customer, regiao, uf, cidade, tipo_local);
CREATE INDEX ix_nr_panorama_comparison_history_product
    ON gold.nr_panorama_comparison_history_detail (
        id_customer, descricao_marca, hierarquia_1, hierarquia_2, hierarquia_3, item
    );

CREATE MATERIALIZED VIEW gold.nr_panorama_comparison_gap_daily AS
SELECT
    o.data,
    o.id_customer,
    'region'::text AS comparison_scope,
    o.regiao,
    o.uf,
    o.cidade,
    NULL::text AS rede,
    NULL::text AS bandeira,
    NULL::text AS loja,
    NULL::text AS hierarquia_1,
    NULL::text AS hierarquia_2,
    NULL::text AS item,
    SUM(o.tvd_simplificado)::double precision AS tvd,
    SUM(o.ivd_simplificado)::double precision AS ivd
FROM gold.nr_panorama_opportunities o
GROUP BY o.data,o.id_customer,o.regiao,o.uf,o.cidade
UNION ALL
SELECT
    o.data,o.id_customer,'retail'::text,
    NULL::text,NULL::text,NULL::text,
    o.rede,o.bandeira,o.loja,
    NULL::text,NULL::text,NULL::text,
    SUM(o.tvd_simplificado)::double precision,
    SUM(o.ivd_simplificado)::double precision
FROM gold.nr_panorama_opportunities o
GROUP BY o.data,o.id_customer,o.rede,o.bandeira,o.loja
UNION ALL
SELECT
    o.data,o.id_customer,'hierarchy'::text,
    NULL::text,NULL::text,NULL::text,
    NULL::text,NULL::text,NULL::text,
    o.hierarquia_1,o.hierarquia_2,o.item,
    SUM(o.tvd_simplificado)::double precision,
    SUM(o.ivd_simplificado)::double precision
FROM gold.nr_panorama_opportunities o
GROUP BY o.data,o.id_customer,o.hierarquia_1,o.hierarquia_2,o.item;

CREATE INDEX ix_nr_panorama_comparison_gap_customer_scope_data
    ON gold.nr_panorama_comparison_gap_daily (id_customer, comparison_scope, data);
CREATE INDEX ix_nr_panorama_comparison_gap_region
    ON gold.nr_panorama_comparison_gap_daily (id_customer, comparison_scope, regiao, uf, cidade);
CREATE INDEX ix_nr_panorama_comparison_gap_retail
    ON gold.nr_panorama_comparison_gap_daily (id_customer, comparison_scope, rede, bandeira, loja);
CREATE INDEX ix_nr_panorama_comparison_gap_product
    ON gold.nr_panorama_comparison_gap_daily (
        id_customer, comparison_scope, hierarquia_1, hierarquia_2, item
    );

-- Compact default path for AP_KPI_INDUSTRIA.  It preserves every hierarchy
-- level, but intentionally excludes the optional dashboard dimensions.  When
-- one of those dimensions is filtered the virtual dataset falls back to the
-- detailed mart so the predicate is applied before aggregation.
CREATE MATERIALIZED VIEW gold.nr_panorama_kpi_dimension_history_default AS
WITH monthly_nodes AS (
    SELECT h.data,EXTRACT(YEAR FROM h.data)::int AS comparison_year,h.id_customer,
           'region'::text AS comparison_scope,
           h.regiao::text AS dimension_1,h.uf::text AS dimension_2,h.cidade::text AS dimension_3,
           CASE WHEN GROUPING(h.uf)=1 THEN 0 WHEN GROUPING(h.cidade)=1 THEN 1 ELSE 2 END::int AS drill_level,
           SUM(COALESCE(h.faturamento,0))::float8 AS sellout_sum,
           SUM(COALESCE(h.volume_unidades,0))::float8 AS volume_sum,
           SUM(h.avg_sales_price)::float8 AS price_sum,COUNT(h.avg_sales_price)::bigint AS price_count,
           SUM(COALESCE(h.volume_unidades,0)*COALESCE(h.avg_price_cost,0))::float8 AS sales_cost_sum,
           SUM(COALESCE(h.estoque_medio,0)*COALESCE(h.avg_price_cost,0))::float8 AS stock_cost_sum,
           SUM(COALESCE(h.estoque_unidades,0))::float8 AS stock_qty_sum,
           SUM(COALESCE(h.demanda_media,0))::float8 AS demand_sum,
           SUM(h.giro) FILTER (WHERE h.giro>0)::float8 AS giro_sum,
           COUNT(h.giro) FILTER (WHERE h.giro>0)::bigint AS giro_count,
           SUM(COALESCE(h.qtd_problemas_osa,0))::float8 AS osa_problem_sum,
           SUM(COALESCE(h.qtd_item_ativo_osa,0))::float8 AS osa_active_sum,
           SUM(COALESCE(h.rup,0))::float8 AS rupture_sum,
           SUM(COALESCE(h.status_item_geral,0))::float8 AS status_sum,
           SUM(COALESCE(h.est_virtual,0))::float8 AS isv_sum
    FROM gold.nr_panorama_comparison_history_detail h
    GROUP BY h.data,EXTRACT(YEAR FROM h.data),h.id_customer,GROUPING SETS (
        (h.regiao),(h.regiao,h.uf),(h.regiao,h.uf,h.cidade)
    )
    UNION ALL
    SELECT h.data,EXTRACT(YEAR FROM h.data)::int,h.id_customer,'retail'::text,
           h.rede::text,h.bandeira::text,h.loja::text,
           CASE WHEN GROUPING(h.bandeira)=1 THEN 0 WHEN GROUPING(h.loja)=1 THEN 1 ELSE 2 END::int,
           SUM(COALESCE(h.faturamento,0))::float8,SUM(COALESCE(h.volume_unidades,0))::float8,
           SUM(h.avg_sales_price)::float8,COUNT(h.avg_sales_price)::bigint,
           SUM(COALESCE(h.volume_unidades,0)*COALESCE(h.avg_price_cost,0))::float8,
           SUM(COALESCE(h.estoque_medio,0)*COALESCE(h.avg_price_cost,0))::float8,
           SUM(COALESCE(h.estoque_unidades,0))::float8,SUM(COALESCE(h.demanda_media,0))::float8,
           SUM(h.giro) FILTER (WHERE h.giro>0)::float8,COUNT(h.giro) FILTER (WHERE h.giro>0)::bigint,
           SUM(COALESCE(h.qtd_problemas_osa,0))::float8,SUM(COALESCE(h.qtd_item_ativo_osa,0))::float8,
           SUM(COALESCE(h.rup,0))::float8,SUM(COALESCE(h.status_item_geral,0))::float8,
           SUM(COALESCE(h.est_virtual,0))::float8
    FROM gold.nr_panorama_comparison_history_detail h
    GROUP BY h.data,EXTRACT(YEAR FROM h.data),h.id_customer,GROUPING SETS (
        (h.rede),(h.rede,h.bandeira),(h.rede,h.bandeira,h.loja)
    )
    UNION ALL
    SELECT h.data,EXTRACT(YEAR FROM h.data)::int,h.id_customer,'hierarchy'::text,
           h.hierarquia_1::text,h.descricao_marca::text,h.item::text,
           CASE WHEN GROUPING(h.descricao_marca)=1 THEN 0 WHEN GROUPING(h.item)=1 THEN 1 ELSE 2 END::int,
           SUM(COALESCE(h.faturamento,0))::float8,SUM(COALESCE(h.volume_unidades,0))::float8,
           SUM(h.avg_sales_price)::float8,COUNT(h.avg_sales_price)::bigint,
           SUM(COALESCE(h.volume_unidades,0)*COALESCE(h.avg_price_cost,0))::float8,
           SUM(COALESCE(h.estoque_medio,0)*COALESCE(h.avg_price_cost,0))::float8,
           SUM(COALESCE(h.estoque_unidades,0))::float8,SUM(COALESCE(h.demanda_media,0))::float8,
           SUM(h.giro) FILTER (WHERE h.giro>0)::float8,COUNT(h.giro) FILTER (WHERE h.giro>0)::bigint,
           SUM(COALESCE(h.qtd_problemas_osa,0))::float8,SUM(COALESCE(h.qtd_item_ativo_osa,0))::float8,
           SUM(COALESCE(h.rup,0))::float8,SUM(COALESCE(h.status_item_geral,0))::float8,
           SUM(COALESCE(h.est_virtual,0))::float8
    FROM gold.nr_panorama_comparison_history_detail h
    GROUP BY h.data,EXTRACT(YEAR FROM h.data),h.id_customer,GROUPING SETS (
        (h.hierarquia_1),(h.hierarquia_1,h.descricao_marca),(h.hierarquia_1,h.descricao_marca,h.item)
    )
), annual_nodes AS (
    SELECT comparison_year,id_customer,comparison_scope,dimension_1,dimension_2,dimension_3,drill_level,
           SUM(sellout_sum)::float8 AS sellout_sum,SUM(volume_sum)::float8 AS volume_sum,
           SUM(price_sum)::float8 AS price_sum,SUM(price_count)::bigint AS price_count,
           SUM(sales_cost_sum)::float8 AS sales_cost_sum,SUM(stock_cost_sum)::float8 AS stock_cost_sum,
           SUM(stock_qty_sum)::float8 AS stock_qty_period_sum,SUM(demand_sum)::float8 AS demand_sum,
           SUM(giro_sum)::float8 AS giro_sum,SUM(giro_count)::bigint AS giro_count,
           SUM(osa_problem_sum)::float8 AS osa_problem_sum,SUM(osa_active_sum)::float8 AS osa_active_sum,
           SUM(rupture_sum)::float8 AS rupture_sum,SUM(status_sum)::float8 AS status_sum,
           SUM(isv_sum)::float8 AS isv_sum,
           (ARRAY_AGG(stock_qty_sum ORDER BY data DESC))[1]::float8 AS latest_stock_qty
    FROM monthly_nodes
    GROUP BY comparison_year,id_customer,comparison_scope,dimension_1,dimension_2,dimension_3,drill_level
)
SELECT MAKE_DATE(comparison_year,1,1) AS data,a.*,
       CASE WHEN sellout_sum>0 THEN sellout_sum
            WHEN price_count>0 THEN volume_sum*(price_sum/price_count) END::float8 AS sales_value,
       latest_stock_qty::float8 AS stock_quantity,
       (100.0*(1-osa_problem_sum/NULLIF(osa_active_sum,0)))::float8 AS osa_percent,
       (100.0*rupture_sum/NULLIF(status_sum,0))::float8 AS rupture_percent,
       (100.0*isv_sum/NULLIF(status_sum,0))::float8 AS no_sales_percent,
       (stock_qty_period_sum/NULLIF(demand_sum,0))::float8 AS coverage,
       (giro_sum/NULLIF(giro_count,0))::float8 AS inventory_turnover,
       (CASE WHEN sellout_sum=0 OR sales_cost_sum=0 THEN 0
             ELSE 100.0*(sellout_sum-sales_cost_sum)/NULLIF(stock_cost_sum,0) END)::float8 AS roi_percent
FROM annual_nodes a;

CREATE INDEX ix_nr_panorama_kpi_history_customer_scope_year
    ON gold.nr_panorama_kpi_dimension_history_default (id_customer,comparison_scope,comparison_year,drill_level);

CREATE MATERIALIZED VIEW gold.nr_panorama_kpi_dimension_gap_default AS
WITH daily_nodes AS (
    SELECT o.data,EXTRACT(YEAR FROM o.data)::int AS comparison_year,o.id_customer,
           'region'::text AS comparison_scope,o.regiao::text AS dimension_1,o.uf::text AS dimension_2,o.cidade::text AS dimension_3,
           CASE WHEN GROUPING(o.uf)=1 THEN 0 WHEN GROUPING(o.cidade)=1 THEN 1 ELSE 2 END::int AS drill_level,
           SUM(o.tvd_simplificado)::float8 AS tvd,SUM(o.ivd_simplificado)::float8 AS ivd
    FROM gold.nr_panorama_opportunities o
    GROUP BY o.data,EXTRACT(YEAR FROM o.data),o.id_customer,GROUPING SETS ((o.regiao),(o.regiao,o.uf),(o.regiao,o.uf,o.cidade))
    UNION ALL
    SELECT o.data,EXTRACT(YEAR FROM o.data)::int,o.id_customer,'retail'::text,
           o.rede::text,o.bandeira::text,o.loja::text,
           CASE WHEN GROUPING(o.bandeira)=1 THEN 0 WHEN GROUPING(o.loja)=1 THEN 1 ELSE 2 END::int,
           SUM(o.tvd_simplificado)::float8,SUM(o.ivd_simplificado)::float8
    FROM gold.nr_panorama_opportunities o
    GROUP BY o.data,EXTRACT(YEAR FROM o.data),o.id_customer,GROUPING SETS ((o.rede),(o.rede,o.bandeira),(o.rede,o.bandeira,o.loja))
    UNION ALL
    SELECT o.data,EXTRACT(YEAR FROM o.data)::int,o.id_customer,'hierarchy'::text,
           o.hierarquia_1::text,o.descricao_marca::text,o.item::text,
           CASE WHEN GROUPING(o.descricao_marca)=1 THEN 0 WHEN GROUPING(o.item)=1 THEN 1 ELSE 2 END::int,
           SUM(o.tvd_simplificado)::float8,SUM(o.ivd_simplificado)::float8
    FROM gold.nr_panorama_opportunities o
    GROUP BY o.data,EXTRACT(YEAR FROM o.data),o.id_customer,GROUPING SETS ((o.hierarquia_1),(o.hierarquia_1,o.descricao_marca),(o.hierarquia_1,o.descricao_marca,o.item))
)
SELECT DISTINCT ON (comparison_year,id_customer,comparison_scope,drill_level,dimension_1,dimension_2,dimension_3)
       data,comparison_year,id_customer,comparison_scope,dimension_1,dimension_2,dimension_3,drill_level,tvd,ivd
FROM daily_nodes
ORDER BY comparison_year,id_customer,comparison_scope,drill_level,dimension_1,dimension_2,dimension_3,data DESC;

CREATE INDEX ix_nr_panorama_kpi_gap_customer_scope_year
    ON gold.nr_panorama_kpi_dimension_gap_default (id_customer,comparison_scope,comparison_year,drill_level);

CREATE MATERIALIZED VIEW gold.nr_panorama_inventory_weekly_detail AS
SELECT
    f.id_time::date AS data,
    f.cd_week,
    f.id_customer,
    f.id_item,
    f.id_location,
    f.volume_unidade::double precision AS volume_unidades,
    f.faturamento::double precision AS faturamento,
    f.estoque_unidades::double precision AS estoque_unidades,
    f.estoque_medio::double precision AS estoque_medio,
    f.qtd_problemas_osa::double precision AS qtd_problemas_osa,
    f.qtd_item_ativo_osa::double precision AS qtd_item_ativo_osa,
    f.rup::double precision AS rup,
    f.est_virtual::double precision AS est_virtual,
    f.giro::double precision AS giro,
    f.avg_sales_price::double precision AS avg_sales_price,
    f.avg_price_cost::double precision AS avg_price_cost,
    f.status_item_geral::double precision AS status_item_geral,
    f.status_item_geral::text AS tp_activity_level,
    COALESCE(f.status_item_geral::text, 'Outros') AS activity_level,
    l.rede,
    l.bandeira,
    l.uf,
    l.cidade,
    l.tipo_local,
    l.loja,
    l.regiao,
    i.item,
    i.descricao_marca,
    i.hierarquia_1,
    i.hierarquia_2,
    i.hierarquia_3
FROM gold.fato_semanal f
LEFT JOIN gold.dim_local l
  ON l.id_customer=f.id_customer AND l.id_location=f.id_location
LEFT JOIN gold.dim_itens i
  ON i.id_customer=f.id_customer AND i.id_item=f.id_item;

CREATE INDEX ix_nr_panorama_inventory_weekly_detail_customer_week
    ON gold.nr_panorama_inventory_weekly_detail (id_customer, cd_week, data);
CREATE INDEX ix_nr_panorama_inventory_weekly_detail_retail
    ON gold.nr_panorama_inventory_weekly_detail (id_customer, rede, bandeira);
CREATE INDEX ix_nr_panorama_inventory_weekly_detail_place
    ON gold.nr_panorama_inventory_weekly_detail (id_customer, uf, cidade, tipo_local, loja);
CREATE INDEX ix_nr_panorama_inventory_weekly_detail_product
    ON gold.nr_panorama_inventory_weekly_detail (
        id_customer, descricao_marca, hierarquia_1, hierarquia_2, hierarquia_3, item
    );

CREATE MATERIALIZED VIEW gold.nr_panorama_inventory_monthly_default AS
WITH monthly AS (
    SELECT
        f.mes_ano::date AS data,
        f.id_customer,
        SUM(COALESCE(f.faturamento,0))::double precision AS faturamento_sum,
        SUM(COALESCE(f.volume_unidades,0))::double precision AS volume_sum,
        SUM(COALESCE(f.avg_sales_price,0))::double precision AS fallback_price_sum,
        COUNT(f.avg_sales_price)::bigint AS fallback_price_count,
        SUM(COALESCE(f.volume_unidades,0) * COALESCE(f.avg_price_cost,0))::double precision AS sales_cost_sum,
        SUM(COALESCE(f.estoque_medio,0) * COALESCE(f.avg_price_cost,0))::double precision AS stock_cost_sum,
        SUM(COALESCE(f.estoque_unidades,0))::double precision AS stock_qty_base,
        SUM(f.giro) FILTER (WHERE f.giro > 0)::double precision AS giro_num,
        COUNT(f.giro) FILTER (WHERE f.giro > 0)::bigint AS giro_den,
        SUM(COALESCE(f.qtd_problemas_osa,0))::double precision AS osa_problem_sum,
        SUM(COALESCE(f.qtd_item_ativo_osa,0))::double precision AS osa_active_sum,
        SUM(COALESCE(f.rup,0))::double precision AS rupture_sum,
        SUM(COALESCE(f.status_item_geral,0))::double precision AS status_sum,
        SUM(COALESCE(f.est_virtual,0))::double precision AS isv_sum
    FROM gold.fato_historico f
    GROUP BY f.mes_ano,f.id_customer
), factors AS (
    SELECT
        f.mes_ano::date AS data,
        f.id_customer,
        c.nm_measure,
        MAX(c.conversion_rate)::double precision AS conversion_factor
    FROM gold.fato_historico f
    JOIN gold.dim_conversao c
      ON c.id_customer=f.id_customer
     AND c.id_item::text=f.id_item::text
    GROUP BY f.mes_ano,f.id_customer,c.nm_measure
)
SELECT
    m.data,
    m.id_customer,
    f.nm_measure,
    CASE
        WHEN m.faturamento_sum > 0 THEN m.faturamento_sum
        WHEN f.conversion_factor IS NOT NULL AND m.fallback_price_count > 0
        THEN (m.volume_sum * f.conversion_factor)
           * ((m.fallback_price_sum / m.fallback_price_count) * f.conversion_factor)
        ELSE NULL
    END::double precision AS sellout_sum,
    m.sales_cost_sum,
    m.stock_cost_sum,
    (m.stock_qty_base * f.conversion_factor)::double precision AS stock_qty_sum,
    m.giro_num,
    m.giro_den,
    m.osa_problem_sum,
    m.osa_active_sum,
    m.rupture_sum,
    m.status_sum,
    m.isv_sum,
    NULL::text AS rede,
    NULL::text AS bandeira,
    NULL::text AS uf,
    NULL::text AS cidade,
    NULL::text AS tipo_local,
    NULL::text AS loja,
    NULL::text AS regiao,
    NULL::text AS tp_activity_level,
    NULL::text AS activity_level,
    NULL::text AS item,
    NULL::text AS descricao_marca,
    NULL::text AS hierarquia_1,
    NULL::text AS hierarquia_2,
    NULL::text AS hierarquia_3
FROM monthly m
JOIN factors f USING(data,id_customer);

CREATE UNIQUE INDEX ux_nr_panorama_inventory_monthly_default
    ON gold.nr_panorama_inventory_monthly_default (id_customer, data, nm_measure);

CREATE MATERIALIZED VIEW gold.nr_panorama_inventory_weekly_card_default AS
WITH ranked_weeks AS (
    SELECT
        d.id_customer,
        d.data,
        d.cd_week,
        DENSE_RANK() OVER (
            PARTITION BY d.id_customer
            ORDER BY d.cd_week DESC
        ) AS week_rank,
        MAX(d.cd_week) OVER (PARTITION BY d.id_customer) AS latest_cd_week
    FROM (
        SELECT DISTINCT id_customer,data,cd_week
        FROM gold.nr_panorama_inventory_weekly_detail
    ) d
), scoped AS (
    SELECT d.*,r.latest_cd_week
    FROM gold.nr_panorama_inventory_weekly_detail d
    JOIN ranked_weeks r USING(id_customer,data,cd_week)
    WHERE r.week_rank <= 13
), weekly AS (
    SELECT
        data,
        cd_week,
        id_customer,
        MAX(latest_cd_week) AS latest_cd_week,
        SUM(COALESCE(faturamento,0))::double precision AS faturamento_sum,
        SUM(COALESCE(volume_unidades,0))::double precision AS volume_sum,
        SUM(COALESCE(avg_sales_price,0))::double precision AS fallback_price_sum,
        COUNT(avg_sales_price)::bigint AS fallback_price_count,
        SUM(COALESCE(volume_unidades,0) * COALESCE(avg_price_cost,0))::double precision AS sales_cost_sum,
        SUM(COALESCE(estoque_medio,0) * COALESCE(avg_price_cost,0))::double precision AS stock_cost_sum,
        SUM(COALESCE(estoque_unidades,0))::double precision AS stock_qty_base,
        SUM(giro) FILTER (WHERE giro IS NOT NULL)::double precision AS giro_num_raw,
        COUNT(giro)::bigint AS giro_den_raw,
        SUM(COALESCE(qtd_problemas_osa,0))::double precision AS osa_problem_sum,
        SUM(COALESCE(qtd_item_ativo_osa,0))::double precision AS osa_active_sum,
        SUM(COALESCE(rup,0))::double precision AS rupture_sum,
        SUM(COALESCE(status_item_geral,0))::double precision AS status_sum,
        SUM(COALESCE(est_virtual,0))::double precision AS isv_sum
    FROM scoped
    GROUP BY data,cd_week,id_customer
), factors AS (
    SELECT
        s.data,
        s.id_customer,
        c.nm_measure,
        MAX(c.conversion_rate)::double precision AS conversion_factor
    FROM (
        SELECT DISTINCT data,id_customer,id_item
        FROM scoped
    ) s
    JOIN gold.dim_conversao c
      ON c.id_customer=s.id_customer
     AND c.id_item::text=s.id_item::text
    GROUP BY s.data,s.id_customer,c.nm_measure
)
SELECT
    'timeline'::text AS row_scope,
    w.data,
    w.cd_week,
    w.id_customer,
    f.nm_measure,
    CASE
        WHEN w.faturamento_sum > 0 THEN w.faturamento_sum
        WHEN f.conversion_factor IS NOT NULL AND w.fallback_price_count > 0
        THEN (w.volume_sum * f.conversion_factor)
           * ((w.fallback_price_sum / w.fallback_price_count) * f.conversion_factor)
        ELSE NULL
    END::double precision AS sellout_sum,
    w.sales_cost_sum,
    w.stock_cost_sum,
    (w.stock_qty_base * f.conversion_factor)::double precision AS stock_qty_sum,
    CASE WHEN w.cd_week = w.latest_cd_week THEN NULL ELSE w.giro_num_raw END::double precision AS giro_num,
    CASE WHEN w.cd_week = w.latest_cd_week THEN NULL ELSE w.giro_den_raw END::bigint AS giro_den,
    w.osa_problem_sum,
    w.osa_active_sum,
    w.rupture_sum,
    w.status_sum,
    w.isv_sum,
    NULL::text AS rede,
    NULL::text AS bandeira,
    NULL::text AS uf,
    NULL::text AS cidade,
    NULL::text AS tipo_local,
    NULL::text AS loja,
    NULL::text AS regiao,
    NULL::text AS tp_activity_level,
    NULL::text AS activity_level,
    NULL::text AS item,
    NULL::text AS descricao_marca,
    NULL::text AS hierarquia_1,
    NULL::text AS hierarquia_2,
    NULL::text AS hierarquia_3
FROM weekly w
JOIN factors f USING(data,id_customer)

UNION ALL

SELECT
    'summary'::text AS row_scope,
    m.data,
    NULL::text AS cd_week,
    m.id_customer,
    m.nm_measure,
    m.sellout_sum,
    m.sales_cost_sum,
    m.stock_cost_sum,
    m.stock_qty_sum,
    m.giro_num,
    m.giro_den,
    m.osa_problem_sum,
    m.osa_active_sum,
    m.rupture_sum,
    m.status_sum,
    m.isv_sum,
    m.rede,
    m.bandeira,
    m.uf,
    m.cidade,
    m.tipo_local,
    m.loja,
    m.regiao,
    m.tp_activity_level,
    m.activity_level,
    m.item,
    m.descricao_marca,
    m.hierarquia_1,
    m.hierarquia_2,
    m.hierarquia_3
FROM gold.nr_panorama_inventory_monthly_default m;

CREATE INDEX ix_nr_panorama_inventory_weekly_card_default
    ON gold.nr_panorama_inventory_weekly_card_default (
        id_customer, nm_measure, row_scope, data
    );

CREATE MATERIALIZED VIEW gold.nr_panorama_gap_monthly_default AS
WITH daily AS (
    SELECT
        o.id_customer,
        o.data,
        SUM(o.tvd_simplificado)::double precision AS tvd,
        SUM(o.ivd_simplificado)::double precision AS ivd
    FROM gold.nr_panorama_opportunities o
    GROUP BY o.id_customer,o.data
), tagged AS (
    SELECT
        d.*,
        DATE_TRUNC('month',d.data)::date AS period_start
    FROM daily d
), anchors AS (
    SELECT
        id_customer,
        period_start,
        MAX(data) FILTER (WHERE tvd IS NOT NULL) AS tvd_date,
        MAX(data) FILTER (WHERE ivd IS NOT NULL) AS ivd_date
    FROM tagged
    GROUP BY id_customer,period_start
)
SELECT
    a.period_start AS data,
    a.id_customer,
    tvd.tvd,
    ivd.ivd,
    NULL::text AS rede,
    NULL::text AS bandeira,
    NULL::text AS uf,
    NULL::text AS cidade,
    NULL::text AS tipo_local,
    NULL::text AS loja,
    NULL::text AS regiao,
    NULL::text AS tp_activity_level,
    NULL::text AS activity_level,
    NULL::text AS item,
    NULL::text AS descricao_marca,
    NULL::text AS hierarquia_1,
    NULL::text AS hierarquia_2,
    NULL::text AS hierarquia_3
FROM anchors a
LEFT JOIN daily tvd
  ON tvd.id_customer=a.id_customer AND tvd.data=a.tvd_date
LEFT JOIN daily ivd
  ON ivd.id_customer=a.id_customer AND ivd.data=a.ivd_date;

CREATE UNIQUE INDEX ux_nr_panorama_gap_monthly_default
    ON gold.nr_panorama_gap_monthly_default (id_customer,data);

CREATE MATERIALIZED VIEW gold.nr_panorama_gap_weekly_card_default AS
WITH daily AS (
    SELECT
        o.id_customer,
        o.data,
        SUM(o.tvd_simplificado)::double precision AS tvd,
        SUM(o.ivd_simplificado)::double precision AS ivd
    FROM gold.nr_panorama_opportunities o
    GROUP BY o.id_customer,o.data
), weekly_tagged AS (
    SELECT
        d.*,
        DATE_TRUNC('week',d.data)::date AS period_start
    FROM daily d
), weekly_anchors AS (
    SELECT
        id_customer,
        period_start,
        MAX(data) FILTER (WHERE tvd IS NOT NULL) AS tvd_date,
        MAX(data) FILTER (WHERE ivd IS NOT NULL) AS ivd_date
    FROM weekly_tagged
    GROUP BY id_customer,period_start
), weekly_values AS (
    SELECT
        a.id_customer,
        a.period_start AS data,
        tvd.tvd,
        ivd.ivd,
        DENSE_RANK() OVER (
            PARTITION BY a.id_customer
            ORDER BY a.period_start DESC
        ) AS week_rank
    FROM weekly_anchors a
    LEFT JOIN daily tvd
      ON tvd.id_customer=a.id_customer AND tvd.data=a.tvd_date
    LEFT JOIN daily ivd
      ON ivd.id_customer=a.id_customer AND ivd.data=a.ivd_date
)
SELECT
    'timeline'::text AS row_scope,
    w.data,
    w.id_customer,
    w.tvd,
    w.ivd,
    NULL::text AS rede,
    NULL::text AS bandeira,
    NULL::text AS uf,
    NULL::text AS cidade,
    NULL::text AS tipo_local,
    NULL::text AS loja,
    NULL::text AS regiao,
    NULL::text AS tp_activity_level,
    NULL::text AS activity_level,
    NULL::text AS item,
    NULL::text AS descricao_marca,
    NULL::text AS hierarquia_1,
    NULL::text AS hierarquia_2,
    NULL::text AS hierarquia_3
FROM weekly_values w
WHERE w.week_rank <= 13

UNION ALL

SELECT
    'summary'::text AS row_scope,
    m.data,
    m.id_customer,
    m.tvd,
    m.ivd,
    m.rede,
    m.bandeira,
    m.uf,
    m.cidade,
    m.tipo_local,
    m.loja,
    m.regiao,
    m.tp_activity_level,
    m.activity_level,
    m.item,
    m.descricao_marca,
    m.hierarquia_1,
    m.hierarquia_2,
    m.hierarquia_3
FROM gold.nr_panorama_gap_monthly_default m;

CREATE INDEX ix_nr_panorama_gap_weekly_card_default
    ON gold.nr_panorama_gap_weekly_card_default (id_customer,row_scope,data);

COMMENT ON MATERIALIZED VIEW gold.nr_panorama_inventory_monthly_default IS
'Certified monthly serving mart for Panorama stock/Giro/ROI/OSA.';
COMMENT ON MATERIALIZED VIEW gold.nr_panorama_inventory_weekly_card_default IS
'Certified weekly TOP-13 timeline plus monthly summary rows for Panorama stock/Giro/ROI/OSA.';
COMMENT ON MATERIALIZED VIEW gold.nr_panorama_gap_monthly_default IS
'LASTNONBLANK-equivalent monthly TVD/IVD snapshots for Panorama.';
COMMENT ON MATERIALIZED VIEW gold.nr_panorama_gap_weekly_card_default IS
'LASTNONBLANK-equivalent TOP-13 weekly TVD/IVD timeline plus monthly summary rows.';
COMMENT ON MATERIALIZED VIEW gold.nr_panorama_comparison_history_detail IS
'Physical history detail for PBIP-equivalent Panorama comparison matrices.';
COMMENT ON MATERIALIZED VIEW gold.nr_panorama_comparison_gap_daily IS
'Daily TVD/IVD aggregates for the three PBIP Panorama comparison hierarchies.';
COMMENT ON MATERIALIZED VIEW gold.nr_panorama_kpi_dimension_history_default IS
'Compact annual AP_KPI_INDUSTRIA history path for the three drill hierarchies.';
COMMENT ON MATERIALIZED VIEW gold.nr_panorama_kpi_dimension_gap_default IS
'Compact LASTNONBLANK TVD/IVD path for the three AP_KPI_INDUSTRIA hierarchies.';

ANALYZE gold.nr_panorama_comparison_history_detail;
ANALYZE gold.nr_panorama_comparison_gap_daily;
ANALYZE gold.nr_panorama_kpi_dimension_history_default;
ANALYZE gold.nr_panorama_kpi_dimension_gap_default;
ANALYZE gold.nr_panorama_inventory_weekly_detail;
ANALYZE gold.nr_panorama_inventory_monthly_default;
ANALYZE gold.nr_panorama_inventory_weekly_card_default;
ANALYZE gold.nr_panorama_gap_monthly_default;
ANALYZE gold.nr_panorama_gap_weekly_card_default;

COMMIT;
