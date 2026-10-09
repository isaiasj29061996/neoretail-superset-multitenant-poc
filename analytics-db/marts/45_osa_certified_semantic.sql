-- Compact default serving paths for the certified OSA Industry dashboard.
--
-- Dimensional requests continue to use the detailed virtual SQL so filters are
-- applied before aggregation.  These marts preserve the same additive bases
-- and MAX conversion-factor semantics for the unfiltered dashboard path.

BEGIN;

-- Step 06 republishes the fact tables, so the serving refresh restores the
-- composite access paths required by filtered fallback queries.
CREATE INDEX IF NOT EXISTS ix_osa_hist_customer_location_time
  ON gold.fato_historico (id_customer,id_location,mes_ano);
CREATE INDEX IF NOT EXISTS ix_osa_hist_customer_item_time
  ON gold.fato_historico (id_customer,id_item,mes_ano);
CREATE INDEX IF NOT EXISTS ix_osa_cause_customer_location_time
  ON gold.fato_mensal_causa_osa (id_customer,id_location,data);
CREATE INDEX IF NOT EXISTS ix_osa_cause_customer_item_time
  ON gold.fato_mensal_causa_osa (id_customer,id_item,data);
CREATE INDEX IF NOT EXISTS ix_osa_week_customer_location_time
  ON gold.fato_semanal (id_customer,id_location,id_time);
CREATE INDEX IF NOT EXISTS ix_osa_week_customer_item_time
  ON gold.fato_semanal (id_customer,id_item,id_time);
CREATE INDEX IF NOT EXISTS ix_osa_opportunity_customer_location_item
  ON gold.calculo_oportunidades (id_customer,id_location,id_item);
CREATE INDEX IF NOT EXISTS ix_osa_conversion_customer_measure_item
  ON gold.dim_conversao (id_customer,nm_measure,id_item);

CREATE INDEX IF NOT EXISTS ix_osa_local_customer_rede
  ON gold.dim_local (id_customer,rede,id_location);
CREATE INDEX IF NOT EXISTS ix_osa_local_customer_bandeira
  ON gold.dim_local (id_customer,bandeira,id_location);
CREATE INDEX IF NOT EXISTS ix_osa_local_customer_uf
  ON gold.dim_local (id_customer,uf,id_location);
CREATE INDEX IF NOT EXISTS ix_osa_local_customer_cidade
  ON gold.dim_local (id_customer,cidade,id_location);
CREATE INDEX IF NOT EXISTS ix_osa_local_customer_tipo
  ON gold.dim_local (id_customer,tipo_local,id_location);
CREATE INDEX IF NOT EXISTS ix_osa_local_customer_loja
  ON gold.dim_local (id_customer,loja,id_location);
CREATE INDEX IF NOT EXISTS ix_osa_local_customer_regiao
  ON gold.dim_local (id_customer,regiao,id_location);

CREATE INDEX IF NOT EXISTS ix_osa_item_customer_name
  ON gold.dim_itens (id_customer,item,id_item);
CREATE INDEX IF NOT EXISTS ix_osa_item_customer_brand
  ON gold.dim_itens (id_customer,descricao_marca,id_item);
CREATE INDEX IF NOT EXISTS ix_osa_item_customer_h1
  ON gold.dim_itens (id_customer,hierarquia_1,id_item);
CREATE INDEX IF NOT EXISTS ix_osa_item_customer_h2
  ON gold.dim_itens (id_customer,hierarquia_2,id_item);
CREATE INDEX IF NOT EXISTS ix_osa_item_customer_h3
  ON gold.dim_itens (id_customer,hierarquia_3,id_item);

DROP MATERIALIZED VIEW IF EXISTS gold.nr_osa_matrix_default;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_osa_causes_default;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_osa_weekly_default;
DROP MATERIALIZED VIEW IF EXISTS gold.nr_osa_monthly_default;

CREATE MATERIALIZED VIEW gold.nr_osa_monthly_default AS
WITH measures AS (
    SELECT DISTINCT id_customer,nm_measure
    FROM gold.nr_conversion_options
), hist_month AS (
    SELECT
        h.mes_ano::date AS data,
        h.id_customer,
        SUM(COALESCE(h.faturamento,0))::double precision AS faturamento_sum,
        SUM(COALESCE(h.volume_unidades,0))::double precision AS volume_sum,
        SUM(COALESCE(h.qtd_perda_osa,0))::double precision AS loss_qty_sum,
        SUM(COALESCE(h.qtd_problemas_osa,0))::double precision AS problem_sum,
        SUM(COALESCE(h.qtd_item_ativo_osa,0))::double precision AS active_sum,
        SUM(h.avg_sales_price)::double precision AS sales_price_sum,
        COUNT(h.avg_sales_price)::bigint AS sales_price_count
    FROM gold.fato_historico h
    GROUP BY h.mes_ano::date,h.id_customer
), cause_month AS (
    SELECT
        c.data::date AS data,
        c.id_customer,
        SUM(COALESCE(c.qtd_perda_osa,0))::double precision AS loss_qty_sum,
        SUM(COALESCE(c.vl_perda_osa,0))::double precision AS loss_value_sum,
        SUM(COALESCE(c.qtd_problemas_osa,0))::double precision AS problem_sum,
        SUM(COALESCE(c.qtd_itens_ativos,0))::double precision AS active_sum,
        SUM(COALESCE(c.volume_unidades,0))::double precision AS volume_sum,
        SUM(COALESCE(c.faturamento,0))::double precision AS faturamento_sum,
        SUM(COALESCE(c.preco_medio,0))::double precision AS price_sum
    FROM gold.fato_mensal_causa_osa c
    GROUP BY c.data::date,c.id_customer
), hist_factor AS (
    SELECT
        h.data,h.id_customer,m.nm_measure,
        COALESCE(MAX(cv.conversion_rate),
          CASE WHEN m.nm_measure='valor' THEN 1.0 END)::double precision AS conversion_factor
    FROM (
        SELECT DISTINCT mes_ano::date AS data,id_customer,id_item
        FROM gold.fato_historico
    ) h
    JOIN measures m ON m.id_customer=h.id_customer
    LEFT JOIN gold.dim_conversao cv
      ON cv.id_customer=h.id_customer
     AND cv.id_item::text=h.id_item::text
     AND cv.nm_measure=m.nm_measure
    GROUP BY h.data,h.id_customer,m.nm_measure
), cause_factor AS (
    SELECT
        c.data,c.id_customer,m.nm_measure,
        COALESCE(MAX(cv.conversion_rate),
          CASE WHEN m.nm_measure='valor' THEN 1.0 END)::double precision AS conversion_factor
    FROM (
        SELECT DISTINCT data::date AS data,id_customer,id_item
        FROM gold.fato_mensal_causa_osa
    ) c
    JOIN measures m ON m.id_customer=c.id_customer
    LEFT JOIN gold.dim_conversao cv
      ON cv.id_customer=c.id_customer
     AND cv.id_item::text=c.id_item::text
     AND cv.nm_measure=m.nm_measure
    GROUP BY c.data,c.id_customer,m.nm_measure
)
SELECT
    h.data,h.id_customer,hf.nm_measure,
    CASE
      WHEN h.faturamento_sum>0 THEN h.faturamento_sum
      WHEN hf.conversion_factor IS NOT NULL AND h.sales_price_count>0
        THEN (h.volume_sum*hf.conversion_factor)
           *((h.sales_price_sum/h.sales_price_count)*hf.conversion_factor)
      ELSE NULL
    END::double precision AS sellout_value,
    c.loss_value_sum::double precision AS loss_value,
    CASE
      WHEN c.faturamento_sum>0
        THEN 100.0*c.loss_value_sum/NULLIF(c.faturamento_sum,0)
      ELSE 100.0*c.loss_value_sum/NULLIF(c.volume_sum*c.price_sum,0)
    END::double precision AS loss_value_percent,
    (100.0*(1-h.problem_sum/NULLIF(h.active_sum,0)))::double precision AS osa_percent,
    (c.volume_sum*cf.conversion_factor)::double precision AS sales_qty,
    (c.loss_qty_sum*cf.conversion_factor)::double precision AS loss_qty,
    CASE
      WHEN hf.conversion_factor IS NULL THEN NULL
      ELSE 100.0*(h.loss_qty_sum*hf.conversion_factor)
        / NULLIF(h.volume_sum*hf.conversion_factor,0)
    END::double precision AS loss_qty_percent,
    NULL::text AS rede,NULL::text AS bandeira,NULL::text AS uf,
    NULL::text AS cidade,NULL::text AS tipo_local,NULL::text AS loja,
    NULL::text AS regiao,NULL::text AS tp_activity_level,
    NULL::text AS activity_level,NULL::text AS item,
    NULL::text AS descricao_marca,NULL::text AS hierarquia_1,
    NULL::text AS hierarquia_2,NULL::text AS hierarquia_3
FROM hist_month h
JOIN hist_factor hf USING(data,id_customer)
LEFT JOIN cause_month c USING(data,id_customer)
LEFT JOIN cause_factor cf
  ON cf.data=h.data AND cf.id_customer=h.id_customer
 AND cf.nm_measure=hf.nm_measure;

CREATE INDEX ix_nr_osa_monthly_default
  ON gold.nr_osa_monthly_default (id_customer,nm_measure,data);

CREATE MATERIALIZED VIEW gold.nr_osa_weekly_default AS
WITH weekly_base AS (
    SELECT
        w.id_time::date AS data,w.cd_week,w.id_customer,w.id_item,w.id_location,
        w.volume_unidade,w.faturamento,w.qtd_perda_osa,w.qtd_problemas_osa,
        w.qtd_item_ativo_osa,w.avg_sales_price,w.avg_price_cost
    FROM gold.fato_semanal w
), ranked_weeks AS (
    SELECT
        id_customer,cd_week,MAX(data) AS data,
        DENSE_RANK() OVER (PARTITION BY id_customer ORDER BY cd_week DESC) AS week_rank
    FROM weekly_base
    GROUP BY id_customer,cd_week
), scoped AS (
    SELECT w.*
    FROM weekly_base w
    JOIN ranked_weeks r USING(id_customer,cd_week)
    WHERE r.week_rank<=13
), measures AS (
    SELECT DISTINCT id_customer,nm_measure
    FROM gold.nr_conversion_options
), weekly AS (
    SELECT
        s.data,s.cd_week,s.id_customer,
        SUM(COALESCE(s.faturamento,0))::double precision AS faturamento_sum,
        SUM(COALESCE(s.volume_unidade,0))::double precision AS volume_sum,
        SUM(COALESCE(s.qtd_perda_osa,0))::double precision AS loss_qty_sum,
        SUM(COALESCE(s.qtd_problemas_osa,0))::double precision AS problem_sum,
        SUM(COALESCE(s.qtd_item_ativo_osa,0))::double precision AS active_sum,
        AVG(s.avg_sales_price)::double precision AS avg_sales_price,
        AVG(s.avg_price_cost)::double precision AS avg_price_cost
    FROM scoped s
    GROUP BY s.data,s.cd_week,s.id_customer
), factor AS (
    SELECT
        s.data,s.id_customer,m.nm_measure,
        COALESCE(MAX(cv.conversion_rate),
          CASE WHEN m.nm_measure='valor' THEN 1.0 END)::double precision AS conversion_factor
    FROM (SELECT DISTINCT data,id_customer,id_item FROM scoped) s
    JOIN measures m ON m.id_customer=s.id_customer
    LEFT JOIN gold.dim_conversao cv
      ON cv.id_customer=s.id_customer
     AND cv.id_item::text=s.id_item::text
     AND cv.nm_measure=m.nm_measure
    GROUP BY s.data,s.id_customer,m.nm_measure
), week_locations AS (
    SELECT DISTINCT data,id_customer,id_location
    FROM scoped
), opportunities AS (
    SELECT id_customer,id_location,demanda_media
    FROM gold.calculo_oportunidades
    WHERE COALESCE(qtd_item_ativo_osa_m0,0)>0
), demand AS (
    SELECT
        wl.data,wl.id_customer,
        SUM(COALESCE(o.demanda_media,0))::double precision AS demand_sum
    FROM week_locations wl
    JOIN opportunities o
      ON o.id_customer=wl.id_customer
     AND o.id_location::text=wl.id_location::text
    GROUP BY wl.data,wl.id_customer
)
SELECT
    w.data,w.cd_week,w.id_customer,f.nm_measure,
    CASE
      WHEN w.faturamento_sum>0 THEN w.faturamento_sum
      WHEN f.conversion_factor IS NOT NULL AND w.avg_sales_price IS NOT NULL
        THEN (w.volume_sum*f.conversion_factor)
           *(w.avg_sales_price*f.conversion_factor)
      ELSE NULL
    END::double precision AS sellout_value,
    (w.loss_qty_sum*w.avg_price_cost)::double precision AS loss_value,
    CASE
      WHEN w.faturamento_sum>0
        THEN 100.0*(w.loss_qty_sum*w.avg_price_cost)/NULLIF(w.faturamento_sum,0)
      ELSE 100.0*(w.loss_qty_sum*w.avg_price_cost)
        / NULLIF(w.volume_sum*w.avg_price_cost,0)
    END::double precision AS loss_value_percent,
    (100.0*(1-w.problem_sum/NULLIF(w.active_sum,0)))::double precision AS osa_percent,
    (w.volume_sum*f.conversion_factor)::double precision AS sales_qty,
    (w.loss_qty_sum*f.conversion_factor)::double precision AS loss_qty,
    (100.0*w.loss_qty_sum/NULLIF(d.demand_sum*30.0,0))::double precision AS loss_qty_percent,
    NULL::text AS rede,NULL::text AS bandeira,NULL::text AS uf,
    NULL::text AS cidade,NULL::text AS tipo_local,NULL::text AS loja,
    NULL::text AS regiao,NULL::text AS tp_activity_level,
    NULL::text AS activity_level,NULL::text AS item,
    NULL::text AS descricao_marca,NULL::text AS hierarquia_1,
    NULL::text AS hierarquia_2,NULL::text AS hierarquia_3
FROM weekly w
JOIN factor f USING(data,id_customer)
LEFT JOIN demand d USING(data,id_customer);

CREATE INDEX ix_nr_osa_weekly_default
  ON gold.nr_osa_weekly_default (id_customer,nm_measure,cd_week,data);

CREATE MATERIALIZED VIEW gold.nr_osa_causes_default AS
WITH measures AS (
    SELECT DISTINCT id_customer,nm_measure
    FROM gold.nr_conversion_options
), converted AS (
    SELECT
        c.data::date AS data,c.id_customer,c.motivo_osa,c.causa_osa,
        c.qtd_perda_osa,c.vl_perda_osa,m.nm_measure,
        COALESCE(cv.conversion_rate,
          CASE WHEN m.nm_measure='valor' THEN 1.0 END)::double precision AS conversion_rate
    FROM gold.fato_mensal_causa_osa c
    JOIN measures m ON m.id_customer=c.id_customer
    LEFT JOIN gold.dim_conversao cv
      ON cv.id_customer=c.id_customer
     AND cv.id_item::text=c.id_item::text
     AND cv.nm_measure=m.nm_measure
)
SELECT
    data,id_customer,nm_measure,motivo_osa,causa_osa,
    SUM(COALESCE(qtd_perda_osa,0))::double precision AS qtd_perda_osa,
    SUM(COALESCE(vl_perda_osa,0))::double precision AS vl_perda_osa,
    MAX(conversion_rate)::double precision AS conversion_rate,
    NULL::text AS rede,NULL::text AS bandeira,NULL::text AS uf,
    NULL::text AS cidade,NULL::text AS tipo_local,NULL::text AS loja,
    NULL::text AS regiao,NULL::text AS tp_activity_level,
    NULL::text AS activity_level,NULL::text AS item,
    NULL::text AS descricao_marca,NULL::text AS hierarquia_1,
    NULL::text AS hierarquia_2,NULL::text AS hierarquia_3
FROM converted
GROUP BY data,id_customer,nm_measure,motivo_osa,causa_osa;

CREATE INDEX ix_nr_osa_causes_default
  ON gold.nr_osa_causes_default (id_customer,nm_measure,data,motivo_osa,causa_osa);

CREATE MATERIALIZED VIEW gold.nr_osa_matrix_default AS
WITH latest AS (
    SELECT id_customer,MAX(mes_ano)::date AS latest_data
    FROM gold.fato_historico
    GROUP BY id_customer
), measures AS (
    SELECT DISTINCT id_customer,nm_measure
    FROM gold.nr_conversion_options
), history_enriched AS (
    SELECT
        h.mes_ano::date AS data,h.id_customer,h.id_item,
        l.regiao::text AS regiao,l.rede::text AS rede,
        i.hierarquia_1::text AS hierarquia_1,
        h.qtd_perda_osa,h.qtd_problemas_osa,h.qtd_item_ativo_osa
    FROM gold.fato_historico h
    LEFT JOIN gold.dim_local l
      ON l.id_customer=h.id_customer AND l.id_location=h.id_location
    LEFT JOIN gold.dim_itens i
      ON i.id_customer=h.id_customer AND i.id_item=h.id_item
), history_scopes AS (
    SELECT data,id_customer,id_item,'region'::text AS scope,
           regiao AS group_value,qtd_perda_osa,qtd_problemas_osa,qtd_item_ativo_osa
    FROM history_enriched
    UNION ALL
    SELECT data,id_customer,id_item,'retail',rede,
           qtd_perda_osa,qtd_problemas_osa,qtd_item_ativo_osa
    FROM history_enriched
    UNION ALL
    SELECT data,id_customer,id_item,'item',hierarquia_1,
           qtd_perda_osa,qtd_problemas_osa,qtd_item_ativo_osa
    FROM history_enriched
), history_month AS (
    SELECT
        h.data,h.id_customer,h.scope,h.group_value,m.nm_measure,
        SUM(COALESCE(h.qtd_perda_osa,0))::double precision AS loss_base,
        SUM(COALESCE(h.qtd_problemas_osa,0))::double precision AS problem_base,
        SUM(COALESCE(h.qtd_item_ativo_osa,0))::double precision AS active_base,
        COALESCE(MAX(cv.conversion_rate),
          CASE WHEN m.nm_measure='valor' THEN 1.0 END)::double precision AS conversion_factor
    FROM history_scopes h
    JOIN measures m ON m.id_customer=h.id_customer
    LEFT JOIN gold.dim_conversao cv
      ON cv.id_customer=h.id_customer
     AND cv.id_item::text=h.id_item::text
     AND cv.nm_measure=m.nm_measure
    GROUP BY h.data,h.id_customer,h.scope,h.group_value,m.nm_measure
), history_period AS (
    SELECT h.*,p.osa_period,p.osa_period_order
    FROM history_month h
    JOIN latest x USING(id_customer)
    CROSS JOIN LATERAL (
      SELECT 'MTD'::text,1::int
        WHERE DATE_TRUNC('month',h.data)=DATE_TRUNC('month',x.latest_data)
      UNION ALL
      SELECT 'Mês Anterior',2
        WHERE DATE_TRUNC('month',h.data)=DATE_TRUNC('month',x.latest_data-INTERVAL '1 month')
      UNION ALL
      SELECT 'U3M',3
        WHERE h.data>=DATE_TRUNC('month',x.latest_data)-INTERVAL '2 months'
          AND h.data<=x.latest_data
      UNION ALL
      SELECT 'YTD',5
        WHERE EXTRACT(YEAR FROM h.data)=EXTRACT(YEAR FROM x.latest_data)
    ) p(osa_period,osa_period_order)
), history_final AS (
    SELECT
        id_customer,nm_measure,scope,group_value,osa_period,osa_period_order,
        SUM(loss_base)::double precision AS loss_base,
        SUM(problem_base)::double precision AS problem_base,
        SUM(active_base)::double precision AS active_base,
        MAX(conversion_factor)::double precision AS conversion_factor
    FROM history_period
    GROUP BY id_customer,nm_measure,scope,group_value,osa_period,osa_period_order
), cause_enriched AS (
    SELECT
        c.data::date AS data,c.id_customer,
        l.regiao::text AS regiao,l.rede::text AS rede,
        i.hierarquia_1::text AS hierarquia_1,c.vl_perda_osa
    FROM gold.fato_mensal_causa_osa c
    LEFT JOIN gold.dim_local l
      ON l.id_customer=c.id_customer AND l.id_location=c.id_location
    LEFT JOIN gold.dim_itens i
      ON i.id_customer=c.id_customer AND i.id_item=c.id_item
), cause_scopes AS (
    SELECT data,id_customer,'region'::text AS scope,regiao AS group_value,vl_perda_osa
    FROM cause_enriched
    UNION ALL
    SELECT data,id_customer,'retail',rede,vl_perda_osa FROM cause_enriched
    UNION ALL
    SELECT data,id_customer,'item',hierarquia_1,vl_perda_osa FROM cause_enriched
), cause_month AS (
    SELECT data,id_customer,scope,group_value,
           SUM(COALESCE(vl_perda_osa,0))::double precision AS loss_value
    FROM cause_scopes
    GROUP BY data,id_customer,scope,group_value
), cause_period AS (
    SELECT c.*,p.osa_period,p.osa_period_order
    FROM cause_month c
    JOIN latest x USING(id_customer)
    CROSS JOIN LATERAL (
      SELECT 'MTD'::text,1::int
        WHERE DATE_TRUNC('month',c.data)=DATE_TRUNC('month',x.latest_data)
      UNION ALL
      SELECT 'Mês Anterior',2
        WHERE DATE_TRUNC('month',c.data)=DATE_TRUNC('month',x.latest_data-INTERVAL '1 month')
      UNION ALL
      SELECT 'U3M',3
        WHERE c.data>=DATE_TRUNC('month',x.latest_data)-INTERVAL '2 months'
          AND c.data<=x.latest_data
      UNION ALL
      SELECT 'YTD',5
        WHERE EXTRACT(YEAR FROM c.data)=EXTRACT(YEAR FROM x.latest_data)
    ) p(osa_period,osa_period_order)
), cause_final AS (
    SELECT id_customer,scope,group_value,osa_period,osa_period_order,
           SUM(loss_value)::double precision AS loss_value
    FROM cause_period
    GROUP BY id_customer,scope,group_value,osa_period,osa_period_order
)
SELECT
    h.id_customer,h.nm_measure,h.scope,h.osa_period,h.osa_period_order,
    CASE WHEN h.scope='region' THEN h.group_value END::text AS regiao,
    CASE WHEN h.scope='retail' THEN h.group_value END::text AS rede,
    CASE WHEN h.scope='item' THEN h.group_value END::text AS hierarquia_1,
    NULL::text AS bandeira,NULL::text AS uf,NULL::text AS cidade,
    NULL::text AS tipo_local,NULL::text AS loja,
    NULL::text AS tp_activity_level,NULL::text AS activity_level,
    NULL::text AS item,NULL::text AS descricao_marca,
    NULL::text AS hierarquia_2,NULL::text AS hierarquia_3,
    c.loss_value,
    (h.loss_base*h.conversion_factor)::double precision AS loss_qty,
    (h.problem_base*h.conversion_factor)::double precision AS problem_qty,
    h.problem_base,h.active_base
FROM history_final h
LEFT JOIN cause_final c
  ON c.id_customer=h.id_customer
 AND c.scope=h.scope
 AND c.osa_period=h.osa_period
 AND c.group_value IS NOT DISTINCT FROM h.group_value;

CREATE INDEX ix_nr_osa_matrix_default
  ON gold.nr_osa_matrix_default (
    id_customer,nm_measure,scope,osa_period,osa_period_order
  );

COMMENT ON MATERIALIZED VIEW gold.nr_osa_monthly_default IS
'Certified compact monthly OSA timeline for the unfiltered dashboard path.';
COMMENT ON MATERIALIZED VIEW gold.nr_osa_weekly_default IS
'Certified compact TOP-13 weekly OSA timeline for the unfiltered dashboard path.';
COMMENT ON MATERIALIZED VIEW gold.nr_osa_causes_default IS
'Certified compact OSA motive/cause source for the unfiltered dashboard path.';
COMMENT ON MATERIALIZED VIEW gold.nr_osa_matrix_default IS
'Certified period-aware OSA matrix source for Region, Retail and Item hierarchy.';

ANALYZE gold.nr_osa_monthly_default;
ANALYZE gold.nr_osa_weekly_default;
ANALYZE gold.nr_osa_causes_default;
ANALYZE gold.nr_osa_matrix_default;

COMMIT;
