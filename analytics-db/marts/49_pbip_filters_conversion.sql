-- PBIP filter/conversion serving only. Frozen calendar, activity recut, loss and OSA formula are untouched.
BEGIN;
CREATE MATERIALIZED VIEW IF NOT EXISTS gold.nr_pbip_overview_semantic_v2 AS
WITH pbip_quantity_by_activity AS (SELECT h.data,h.id_customer,h.tp_activity_level,f.nm_measure,SUM(h.volume_unidades*f.conversion_rate)::float8 AS quantity_sum FROM gold.nr_pbip_overview_history h JOIN (SELECT c.id_customer,c.nm_measure,MAX(c.conversion_rate) AS conversion_rate
 FROM gold.dim_conversao c
 LEFT JOIN gold.dim_itens i ON i.id_customer=c.id_customer AND CAST(i.id_item AS TEXT)=CAST(c.id_item AS TEXT)
 WHERE c.id_customer=290 
 GROUP BY c.id_customer,c.nm_measure) f ON f.id_customer=h.id_customer WHERE h.id_customer=290   GROUP BY h.data,h.id_customer,h.tp_activity_level,f.nm_measure) SELECT b.data,b.id_customer,b.tp_activity_level,b.activity_level,b.nm_measure,b.semantic_scope,b.semantic_precomputed,b.sellout_sum,b.sales_cost_sum,CASE WHEN b.nm_measure='valor' THEN b.sales_qty_sum ELSE (SELECT SUM(q.quantity_sum) FROM pbip_quantity_by_activity q WHERE q.data=b.data AND q.id_customer=b.id_customer AND q.nm_measure=b.nm_measure AND (b.semantic_scope='all' OR q.tp_activity_level IS NOT DISTINCT FROM b.tp_activity_level)) END AS sales_qty_sum,b.stock_cost_sum,b.stock_qty_sum,b.giro_sum_positive,b.giro_count_positive,b.osa_problem_sum,b.osa_active_sum,b.rede,b.bandeira,b.uf,b.cidade,b.tipo_local,b.loja,b.regiao,b.item,b.descricao_marca,b.hierarquia_1,b.hierarquia_2,b.hierarquia_3 FROM (WITH history_region AS (
         SELECT h.data,
            h.id_customer,
            h.tp_activity_level,
                CASE h.tp_activity_level
                    WHEN 'F'::text THEN 'Fast Mover'::text
                    WHEN 'S'::text THEN 'Slow Mover'::text
                    WHEN 'U'::text THEN 'Ultra Slow Mover'::text
                    WHEN 'N'::text THEN 'New Mover'::text
                    ELSE NULL::text
                END AS activity_level,
            h.regiao,
            sum(COALESCE(h.faturamento, 0::double precision)) AS faturamento_sum,
            sum(h.volume_unidades) AS volume_sum,
            sum(COALESCE(h.avg_sales_price, 0::double precision)) AS price_sum,
            count(h.avg_sales_price) AS price_count,
            sum(h.volume_unidades * h.avg_price_cost) AS sales_cost_sum,
            sum(h.estoque_medio * h.avg_price_cost) AS stock_cost_sum,
            sum(h.estoque_unidades) AS stock_units_sum,
            sum(
                CASE
                    WHEN COALESCE(h.giro, 0::double precision) > 0::double precision THEN h.giro
                    ELSE 0::double precision
                END) AS giro_sum_positive,
            count(h.giro) FILTER (WHERE COALESCE(h.giro, 0::double precision) > 0::double precision) AS giro_count_positive,
            sum(COALESCE(h.qtd_problemas_osa, 0::bigint))::bigint AS osa_problem_sum,
            sum(COALESCE(h.qtd_item_ativo_osa, 0::bigint))::bigint AS osa_active_sum
           FROM gold.nr_pbip_overview_history h
          GROUP BY h.data, h.id_customer, h.tp_activity_level, h.regiao
        ), factor_region AS (
 SELECT h.data,h.id_customer,h.tp_activity_level,h.regiao,f.nm_measure,f.conversion_rate
 FROM (SELECT DISTINCT data,id_customer,tp_activity_level,regiao FROM gold.nr_pbip_overview_history) h
 JOIN (SELECT c.id_customer,c.nm_measure,MAX(c.conversion_rate) AS conversion_rate
 FROM gold.dim_conversao c
 LEFT JOIN gold.dim_itens i ON i.id_customer=c.id_customer AND CAST(i.id_item AS TEXT)=CAST(c.id_item AS TEXT)
 WHERE c.id_customer=290 
 GROUP BY c.id_customer,c.nm_measure ) f ON f.id_customer=h.id_customer
 ), expanded AS (
         SELECT r.data,
            r.id_customer,
            r.tp_activity_level,
            r.activity_level,
            r.regiao,
            r.faturamento_sum,
            r.volume_sum,
            r.price_sum,
            r.price_count,
            r.sales_cost_sum,
            r.stock_cost_sum,
            r.stock_units_sum,
            r.giro_sum_positive,
            r.giro_count_positive,
            r.osa_problem_sum,
            r.osa_active_sum,
            f.nm_measure,
            f.conversion_rate
           FROM history_region r
             JOIN factor_region f ON f.data = r.data AND f.id_customer = r.id_customer AND NOT f.tp_activity_level IS DISTINCT FROM r.tp_activity_level AND NOT f.regiao IS DISTINCT FROM r.regiao
        UNION ALL
         SELECT r.data,
            r.id_customer,
            r.tp_activity_level,
            r.activity_level,
            r.regiao,
            r.faturamento_sum,
            r.volume_sum,
            r.price_sum,
            r.price_count,
            r.sales_cost_sum,
            r.stock_cost_sum,
            r.stock_units_sum,
            r.giro_sum_positive,
            r.giro_count_positive,
            r.osa_problem_sum,
            r.osa_active_sum,
            'valor'::text AS nm_measure,
            NULL::double precision AS conversion_rate
           FROM history_region r
        ), monthly_activity AS (
         SELECT expanded.data,
            expanded.id_customer,
            expanded.tp_activity_level,
            expanded.activity_level,
            expanded.nm_measure,
            sum(
                CASE
                    WHEN expanded.faturamento_sum > 0::double precision THEN expanded.faturamento_sum
                    WHEN expanded.conversion_rate IS NOT NULL AND expanded.price_count > 0 THEN expanded.volume_sum * expanded.conversion_rate * (expanded.price_sum / expanded.price_count::double precision * expanded.conversion_rate)
                    ELSE NULL::double precision
                END) AS sellout_sum,
            sum(expanded.sales_cost_sum) AS sales_cost_sum,
                CASE
                    WHEN expanded.nm_measure = 'valor'::text THEN sum(expanded.faturamento_sum)
                    ELSE sum(expanded.volume_sum) * max(expanded.conversion_rate)
                END AS sales_qty_sum,
            sum(expanded.stock_cost_sum) AS stock_cost_sum,
                CASE
                    WHEN expanded.nm_measure = 'valor'::text THEN sum(expanded.faturamento_sum)
                    ELSE sum(expanded.stock_units_sum) * max(expanded.conversion_rate)
                END AS stock_qty_sum,
            sum(expanded.giro_sum_positive) AS giro_sum_positive,
            sum(expanded.giro_count_positive)::bigint AS giro_count_positive,
            sum(expanded.osa_problem_sum)::bigint AS osa_problem_sum,
            sum(expanded.osa_active_sum)::bigint AS osa_active_sum
           FROM expanded
          WHERE expanded.activity_level IS NOT NULL
          GROUP BY expanded.data, expanded.id_customer, expanded.tp_activity_level, expanded.activity_level, expanded.nm_measure
        ), all_region AS (
         SELECT expanded.data,
            expanded.id_customer,
            expanded.regiao,
            expanded.nm_measure,
            sum(expanded.faturamento_sum) AS faturamento_sum,
            sum(expanded.volume_sum) AS volume_sum,
            sum(expanded.price_sum) AS price_sum,
            sum(expanded.price_count)::bigint AS price_count,
            max(expanded.conversion_rate) AS conversion_rate,
            sum(expanded.sales_cost_sum) AS sales_cost_sum,
            sum(expanded.stock_cost_sum) AS stock_cost_sum,
            sum(expanded.stock_units_sum) AS stock_units_sum,
            sum(expanded.giro_sum_positive) AS giro_sum_positive,
            sum(expanded.giro_count_positive)::bigint AS giro_count_positive,
            sum(expanded.osa_problem_sum)::bigint AS osa_problem_sum,
            sum(expanded.osa_active_sum)::bigint AS osa_active_sum
           FROM expanded
          GROUP BY expanded.data, expanded.id_customer, expanded.regiao, expanded.nm_measure
        ), monthly_all AS (
         SELECT all_region.data,
            all_region.id_customer,
            all_region.nm_measure,
            sum(
                CASE
                    WHEN all_region.faturamento_sum > 0::double precision THEN all_region.faturamento_sum
                    WHEN all_region.conversion_rate IS NOT NULL AND all_region.price_count > 0 THEN all_region.volume_sum * all_region.conversion_rate * (all_region.price_sum / all_region.price_count::double precision * all_region.conversion_rate)
                    ELSE NULL::double precision
                END) AS sellout_sum,
            sum(all_region.sales_cost_sum) AS sales_cost_sum,
                CASE
                    WHEN all_region.nm_measure = 'valor'::text THEN sum(all_region.faturamento_sum)
                    ELSE sum(all_region.volume_sum) * max(all_region.conversion_rate)
                END AS sales_qty_sum,
            sum(all_region.stock_cost_sum) AS stock_cost_sum,
                CASE
                    WHEN all_region.nm_measure = 'valor'::text THEN sum(all_region.faturamento_sum)
                    ELSE sum(all_region.stock_units_sum) * max(all_region.conversion_rate)
                END AS stock_qty_sum,
            sum(all_region.giro_sum_positive) AS giro_sum_positive,
            sum(all_region.giro_count_positive)::bigint AS giro_count_positive,
            sum(all_region.osa_problem_sum)::bigint AS osa_problem_sum,
            sum(all_region.osa_active_sum)::bigint AS osa_active_sum
           FROM all_region
          GROUP BY all_region.data, all_region.id_customer, all_region.nm_measure
        )
 SELECT m.data,
    m.id_customer,
    m.tp_activity_level,
    m.activity_level,
    m.nm_measure,
    m.sellout_sum,
    m.sales_cost_sum,
    m.sales_qty_sum,
    m.stock_cost_sum,
    m.stock_qty_sum,
    m.giro_sum_positive,
    m.giro_count_positive,
    m.osa_problem_sum,
    m.osa_active_sum,
    'activity'::text AS semantic_scope,
    true AS semantic_precomputed,
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
 SELECT m.data,
    m.id_customer,
    NULL::text AS tp_activity_level,
    NULL::text AS activity_level,
    m.nm_measure,
    m.sellout_sum,
    m.sales_cost_sum,
    m.sales_qty_sum,
    m.stock_cost_sum,
    m.stock_qty_sum,
    m.giro_sum_positive,
    m.giro_count_positive,
    m.osa_problem_sum,
    m.osa_active_sum,
    'all'::text AS semantic_scope,
    true AS semantic_precomputed,
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
   FROM monthly_all m) b;
CREATE UNIQUE INDEX IF NOT EXISTS ux_nr_pbip_overview_semantic_v2_key ON gold.nr_pbip_overview_semantic_v2(id_customer,data,nm_measure,semantic_scope,tp_activity_level);
CREATE MATERIALIZED VIEW IF NOT EXISTS gold.nr_pbip_giro_default AS
WITH filtered AS (SELECT h.* FROM gold.nr_pbip_overview_history h WHERE h.id_customer=290 AND EXISTS (
 SELECT 1 FROM gold.dim_local pl
 WHERE pl.id_customer=h.id_customer AND pl.id_location=h.id_location
   AND pl.rede IS NOT NULL 
   AND EXISTS (
     SELECT 1 FROM gold.dim_catalogo_local pc
     WHERE pc.id_customer=pl.id_customer AND pc.cnpj IS NOT DISTINCT FROM pl.cnpj
       AND pc.rede <> 'GPA' 
       AND EXISTS (SELECT 1 FROM gold.dim_local ac
                   WHERE ac.id_customer=pc.id_customer AND ac.id_retailer=pc.id_retailer)
   )
))
 SELECT h.data,h.id_customer,'unidade'::text AS nm_measure,'all'::text AS semantic_scope,NULL::text AS activity_level,SUM(h.giro) FILTER(WHERE h.giro>0)::float8 AS giro_sum_positive,COUNT(h.giro) FILTER(WHERE h.giro>0)::bigint AS giro_count_positive,NULL::text AS rede,NULL::text AS bandeira,NULL::text AS uf,NULL::text AS cidade,NULL::text AS tipo_local,NULL::text AS loja,NULL::text AS regiao,NULL::text AS item,NULL::text AS descricao_marca,NULL::text AS hierarquia_1,NULL::text AS hierarquia_2,NULL::text AS hierarquia_3,NULL::text AS tp_activity_level
 FROM filtered h GROUP BY h.data,h.id_customer
 UNION ALL
 SELECT h.data,h.id_customer,'unidade'::text,'activity'::text,CASE h.tp_activity_level WHEN 'F' THEN 'Fast Mover' WHEN 'S' THEN 'Slow Mover' WHEN 'U' THEN 'Ultra Slow Mover' WHEN 'N' THEN 'New Mover' ELSE NULL END,SUM(h.giro) FILTER(WHERE h.giro>0)::float8 AS giro_sum_positive,COUNT(h.giro) FILTER(WHERE h.giro>0)::bigint AS giro_count_positive,NULL::text AS rede,NULL::text AS bandeira,NULL::text AS uf,NULL::text AS cidade,NULL::text AS tipo_local,NULL::text AS loja,NULL::text AS regiao,NULL::text AS item,NULL::text AS descricao_marca,NULL::text AS hierarquia_1,NULL::text AS hierarquia_2,NULL::text AS hierarquia_3,NULL::text AS tp_activity_level
 FROM filtered h WHERE CASE h.tp_activity_level WHEN 'F' THEN 'Fast Mover' WHEN 'S' THEN 'Slow Mover' WHEN 'U' THEN 'Ultra Slow Mover' WHEN 'N' THEN 'New Mover' ELSE NULL END IS NOT NULL GROUP BY h.data,h.id_customer,CASE h.tp_activity_level WHEN 'F' THEN 'Fast Mover' WHEN 'S' THEN 'Slow Mover' WHEN 'U' THEN 'Ultra Slow Mover' WHEN 'N' THEN 'New Mover' ELSE NULL END;
CREATE UNIQUE INDEX IF NOT EXISTS ux_nr_pbip_giro_default_key ON gold.nr_pbip_giro_default(id_customer,data,semantic_scope,activity_level);
CREATE MATERIALIZED VIEW IF NOT EXISTS gold.nr_pbip_daily_headlines AS
WITH fact_filtered AS (
 SELECT f.* FROM gold.fato_ivd_tvd f
 LEFT JOIN gold.dim_itens i ON i.id_customer=f.id_customer AND CAST(i.id_item AS TEXT)=CAST(f.id_item AS TEXT)
 WHERE f.id_customer=290 AND EXISTS (
 SELECT 1 FROM gold.dim_local pl
 WHERE pl.id_customer=f.id_customer AND pl.id_location=f.id_location
   AND pl.rede IS NOT NULL  AND (pl.tipo_local IS NULL OR pl.tipo_local NOT IN ('DEPÓSITO','CD','LOJA VIRTUAL'))
   AND EXISTS (
     SELECT 1 FROM gold.dim_catalogo_local pc
     WHERE pc.id_customer=pl.id_customer AND pc.cnpj IS NOT DISTINCT FROM pl.cnpj
       AND pc.rede <> 'GPA'  AND (pc.tipo_local IS NULL OR pc.tipo_local NOT IN ('DEPÓSITO','CD','LOJA VIRTUAL'))
       AND EXISTS (SELECT 1 FROM gold.dim_local ac
                   WHERE ac.id_customer=pc.id_customer AND ac.id_retailer=pc.id_retailer)
   )
)
), daily AS (
 SELECT id_time::date AS data,id_customer,SUM(COALESCE(tvd_simplificado,0))::float8 AS tvd,SUM(COALESCE(ivd_simplificado,0))::float8 AS ivd
 FROM fact_filtered GROUP BY id_time::date,id_customer
), latest AS (SELECT id_customer,MAX(data) AS data FROM daily GROUP BY id_customer), tasks AS (
 SELECT o.id_customer,
 COUNT(o.id_item) FILTER(WHERE o.regra_critico='CRITICO' AND COALESCE(o.tvd,0)>0)::bigint AS itens_criticos_tvd,
 COUNT(o.id_item) FILTER(WHERE o.regra_critico='F' AND COALESCE(o.tvd,0)>0)::bigint AS itens_risco_tvd,
 COUNT(o.id_item) FILTER(WHERE o.regra_critico='CRITICO' AND COALESCE(o.ivd,0)>0)::bigint AS itens_criticos_ivd,
 COUNT(o.id_item) FILTER(WHERE o.regra_critico='F' AND COALESCE(o.ivd,0)>0)::bigint AS itens_risco_ivd
 FROM gold.calculo_oportunidades o
 LEFT JOIN gold.dim_itens i ON i.id_customer=o.id_customer AND i.id_item=o.id_item
 WHERE o.id_customer=290 AND EXISTS (
 SELECT 1 FROM gold.dim_local pl
 WHERE pl.id_customer=o.id_customer AND pl.id_location=o.id_location
   AND pl.rede IS NOT NULL  AND (pl.tipo_local IS NULL OR pl.tipo_local NOT IN ('DEPÓSITO','CD','LOJA VIRTUAL'))
   AND EXISTS (
     SELECT 1 FROM gold.dim_catalogo_local pc
     WHERE pc.id_customer=pl.id_customer AND pc.cnpj IS NOT DISTINCT FROM pl.cnpj
       AND pc.rede <> 'GPA'  AND (pc.tipo_local IS NULL OR pc.tipo_local NOT IN ('DEPÓSITO','CD','LOJA VIRTUAL'))
       AND EXISTS (SELECT 1 FROM gold.dim_local ac
                   WHERE ac.id_customer=pc.id_customer AND ac.id_retailer=pc.id_retailer)
   )
) GROUP BY o.id_customer
)
 SELECT d.data,d.id_customer,d.tvd,d.ivd,
 CASE WHEN d.data=l.data THEN COALESCE(t.itens_criticos_tvd,0) ELSE 0 END AS itens_criticos_tvd,
 CASE WHEN d.data=l.data THEN COALESCE(t.itens_risco_tvd,0) ELSE 0 END AS itens_risco_tvd,
 CASE WHEN d.data=l.data THEN COALESCE(t.itens_criticos_ivd,0) ELSE 0 END AS itens_criticos_ivd,
 CASE WHEN d.data=l.data THEN COALESCE(t.itens_risco_ivd,0) ELSE 0 END AS itens_risco_ivd,
 NULL::text AS rede,NULL::text AS bandeira,NULL::text AS uf,NULL::text AS cidade,NULL::text AS tipo_local,NULL::text AS loja,NULL::text AS regiao,NULL::text AS item,NULL::text AS descricao_marca,NULL::text AS hierarquia_1,NULL::text AS hierarquia_2,NULL::text AS hierarquia_3,NULL::text AS tp_activity_level
 FROM daily d JOIN latest l ON l.id_customer=d.id_customer LEFT JOIN tasks t ON t.id_customer=d.id_customer;
CREATE UNIQUE INDEX IF NOT EXISTS ux_nr_pbip_daily_headlines_key ON gold.nr_pbip_daily_headlines(id_customer,data);
COMMIT;
