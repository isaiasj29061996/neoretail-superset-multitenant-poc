-- Dedicated PBIP serving objects; base Gold and all legacy marts remain untouched.

BEGIN;

CREATE MATERIALIZED VIEW IF NOT EXISTS gold.nr_pbip_overview_history AS
WITH latest_opportunity AS (
         SELECT DISTINCT ON (calculo_oportunidades.id_customer, calculo_oportunidades.id_location, calculo_oportunidades.id_item) calculo_oportunidades.id_customer,
            calculo_oportunidades.id_location,
            calculo_oportunidades.id_item,
            calculo_oportunidades.qtd_problemas_osa_m0,
            calculo_oportunidades.max_tp_activity_level
           FROM gold.calculo_oportunidades
          ORDER BY calculo_oportunidades.id_customer, calculo_oportunidades.id_location, calculo_oportunidades.id_item, calculo_oportunidades._silver_refreshed_at DESC NULLS LAST
        )
 SELECT f.mes_ano AS data,
    f.id_customer,
    f.id_item,
    f.id_location,
    f.volume_unidades,
    f.faturamento,
    f.estoque_unidades,
    f.expectativa_vendas,
    f.qtd_perda_osa,
    f.rup,
    f.est_virtual,
    f.giro,
    f.qtd_problemas_osa,
    f.qtd_item_ativo_osa,
    f.avg_sales_price,
    f.avg_price_cost,
    f.estoque_medio,
    f.demanda_media,
    f.tp_activity_level,
        CASE f.tp_activity_level
            WHEN 'F'::text THEN 'Fast Mover'::text
            WHEN 'S'::text THEN 'Slow Mover'::text
            WHEN 'US'::text THEN 'Ultra Slow Mover'::text
            WHEN 'N'::text THEN 'New Mover'::text
            ELSE COALESCE(f.tp_activity_level, 'Outros'::text)
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
    i.hierarquia_3,
    concat_ws('|'::text, f.id_customer::text, f.id_location, f.id_item) AS opportunity_key,
    o.qtd_problemas_osa_m0,
    o.max_tp_activity_level
   FROM gold.fato_historico f
     LEFT JOIN gold.dim_local l ON l.id_customer = f.id_customer AND l.id_location = f.id_location
     LEFT JOIN gold.dim_itens i ON i.id_customer = f.id_customer AND i.id_item = f.id_item
     LEFT JOIN latest_opportunity o ON o.id_customer = f.id_customer AND o.id_location = f.id_location AND o.id_item = f.id_item
WHERE EXISTS (
 SELECT 1 FROM gold.dim_local pl
 WHERE pl.id_customer=f.id_customer AND pl.id_location=f.id_location
   AND pl.rede IS NOT NULL
   AND EXISTS (
     SELECT 1 FROM gold.dim_catalogo_local pc
     WHERE pc.id_customer=pl.id_customer AND pc.cnpj IS NOT DISTINCT FROM pl.cnpj
       AND pc.rede <> 'GPA'
       AND EXISTS (SELECT 1 FROM gold.dim_local ac
                   WHERE ac.id_customer=pc.id_customer AND ac.id_retailer=pc.id_retailer)
   )
) AND f.id_customer=290;

CREATE INDEX IF NOT EXISTS ix_nr_pbip_overview_history_customer_data ON gold.nr_pbip_overview_history(id_customer,data);

CREATE INDEX IF NOT EXISTS ix_nr_pbip_overview_history_customer_keys ON gold.nr_pbip_overview_history(id_customer,id_location,id_item);

CREATE MATERIALIZED VIEW IF NOT EXISTS gold.nr_pbip_osa_industry_causes AS
SELECT f.id_customer,
    f.id_item,
    f.id_location,
    f.causa_osa,
    f.qtd_perda_osa,
    f.vl_perda_osa,
    f.qtd_problemas_osa,
    f.qtd_itens_ativos,
    f.volume_unidades,
    f.faturamento,
    f.preco_medio,
    f.motivo_osa,
    f.data,
    COALESCE(f.qtd_perda_osa * NULLIF(f.preco_medio, 0::double precision), 0::double precision) AS perda_osa_valor,
        CASE
            WHEN lower(COALESCE(f.motivo_osa, ''::text)) ~~ '%performance%'::text THEN 'Falta de Performance'::text
            WHEN lower(COALESCE(f.motivo_osa, ''::text)) ~~ '%exposi%'::text THEN 'Falta de Exposição'::text
            WHEN lower(COALESCE(f.motivo_osa, ''::text)) ~~ '%virtual%'::text THEN 'Estoque Virtual'::text
            WHEN lower(COALESCE(f.motivo_osa, ''::text)) ~~ '%ruptura%'::text THEN 'Ruptura na loja'::text
            ELSE COALESCE(f.motivo_osa, 'Não identificado'::text)
        END AS motivo,
    COALESCE(f.causa_osa, 'Não identificado'::text) AS causa,
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
   FROM gold.fato_mensal_causa_osa f
     LEFT JOIN gold.dim_local l ON l.id_customer = f.id_customer AND l.id_location = f.id_location
     LEFT JOIN gold.dim_itens i ON i.id_customer = f.id_customer AND i.id_item = f.id_item
WHERE EXISTS (
 SELECT 1 FROM gold.dim_local pl
 WHERE pl.id_customer=f.id_customer AND pl.id_location=f.id_location
   AND pl.rede IS NOT NULL
   AND EXISTS (
     SELECT 1 FROM gold.dim_catalogo_local pc
     WHERE pc.id_customer=pl.id_customer AND pc.cnpj IS NOT DISTINCT FROM pl.cnpj
       AND pc.rede <> 'GPA'
       AND EXISTS (SELECT 1 FROM gold.dim_local ac
                   WHERE ac.id_customer=pc.id_customer AND ac.id_retailer=pc.id_retailer)
   )
) AND f.id_customer=290;

CREATE INDEX IF NOT EXISTS ix_nr_pbip_osa_industry_causes_customer_data ON gold.nr_pbip_osa_industry_causes(id_customer,data);

CREATE INDEX IF NOT EXISTS ix_nr_pbip_osa_industry_causes_customer_keys ON gold.nr_pbip_osa_industry_causes(id_customer,id_location,id_item);

CREATE MATERIALIZED VIEW IF NOT EXISTS gold.nr_pbip_overview_semantic_default AS
WITH history_region AS (
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
            sum(COALESCE(h.volume_unidades, 0::double precision)) AS volume_sum,
            sum(COALESCE(h.avg_sales_price, 0::double precision)) AS price_sum,
            count(h.avg_sales_price) AS price_count,
            sum(h.volume_unidades * h.avg_price_cost) AS sales_cost_sum,
            sum(h.estoque_medio * h.avg_price_cost) AS stock_cost_sum,
            sum(COALESCE(h.estoque_unidades, 0::double precision)) AS stock_units_sum,
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
         SELECT h.data,
            h.id_customer,
            h.tp_activity_level,
            h.regiao,
            c.nm_measure,
            max(c.conversion_rate)::double precision AS conversion_rate
           FROM ( SELECT DISTINCT nr_pbip_overview_history.data,
                    nr_pbip_overview_history.id_customer,
                    nr_pbip_overview_history.tp_activity_level,
                    nr_pbip_overview_history.regiao,
                    nr_pbip_overview_history.id_item
                   FROM gold.nr_pbip_overview_history) h
             JOIN gold.dim_conversao c ON c.id_customer = h.id_customer AND c.id_item::text = h.id_item
          GROUP BY h.data, h.id_customer, h.tp_activity_level, h.regiao, c.nm_measure
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
                    ELSE 0::double precision
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
                    ELSE 0::double precision
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
   FROM monthly_all m;

CREATE UNIQUE INDEX IF NOT EXISTS ux_nr_pbip_overview_semantic_default_key ON gold.nr_pbip_overview_semantic_default(id_customer,data,nm_measure,semantic_scope,tp_activity_level);

CREATE MATERIALIZED VIEW IF NOT EXISTS gold.nr_pbip_osa_semantic_default AS
WITH loss_base AS (
         SELECT f.data,
            f.id_customer,
            sum(f.qtd_perda_osa) AS loss_qty_sum,
            sum(f.preco_medio) AS price_sum,
            count(f.preco_medio) AS price_count
           FROM gold.nr_pbip_osa_industry_causes f
          GROUP BY f.data, f.id_customer
        ), loss_factor AS (
         SELECT f.data,f.id_customer,c.nm_measure,MAX(c.conversion_rate)::float8 conversion_rate
         FROM (SELECT DISTINCT data,id_customer FROM gold.nr_pbip_osa_industry_causes) f
         JOIN gold.dim_conversao c ON c.id_customer=f.id_customer
         GROUP BY f.data,f.id_customer,c.nm_measure
        ), loss AS (
         SELECT b.data,
            b.id_customer,
            f.nm_measure,
                CASE
                    WHEN b.price_count > 0 THEN b.loss_qty_sum * f.conversion_rate * (b.price_sum / b.price_count::double precision)
                    ELSE NULL::double precision
                END AS osa_loss_sum, b.loss_qty_sum,b.price_sum,b.price_count,f.conversion_rate
           FROM loss_base b
             JOIN loss_factor f USING (data, id_customer)
        UNION ALL
         SELECT loss_base.data,
            loss_base.id_customer,
            'valor'::text AS text,
            NULL::double precision AS float8,loss_base.loss_qty_sum,loss_base.price_sum,loss_base.price_count,NULL::float8
           FROM loss_base
        ), osa_ratio AS (
         SELECT nr_overview_default_summary.data,
            nr_overview_default_summary.id_customer,
            sum(nr_overview_default_summary.osa_problem_sum)::bigint AS osa_problem_sum,
            sum(nr_overview_default_summary.osa_active_sum)::bigint AS osa_active_sum
           FROM (SELECT data,id_customer,SUM(qtd_problemas_osa) AS osa_problem_sum,SUM(qtd_item_ativo_osa) AS osa_active_sum FROM gold.nr_pbip_overview_history GROUP BY data,id_customer) nr_overview_default_summary
          GROUP BY nr_overview_default_summary.data, nr_overview_default_summary.id_customer
        ), latest_month AS (
         SELECT nr_pbip_overview_history.id_customer,
            max(nr_pbip_overview_history.data) AS data
           FROM gold.nr_pbip_overview_history
          GROUP BY nr_pbip_overview_history.id_customer
        ), tasks AS (
         SELECT o.id_customer,
            count(o.id_item) FILTER (WHERE COALESCE(o.qtd_problemas_osa_m0, 0::bigint) > 0 AND a.nm_activity_level = 'Fast Mover'::text) AS osa_critical_count,
            count(o.id_item) FILTER (WHERE COALESCE(o.qtd_problemas_osa_m0, 0::bigint) > 0 AND o.max_tp_activity_level = 'S'::text) AS osa_risk_count
           FROM gold.calculo_oportunidades o
             LEFT JOIN gold.dim_nivel_atividade a ON a.id_customer = o.id_customer AND a.tp_activity_level = o.max_tp_activity_level
          GROUP BY o.id_customer
        )
 SELECT r.data,
    r.id_customer,
    selected_measure.nm_measure,
    r.osa_problem_sum,
    r.osa_active_sum,
    l.osa_loss_sum,l.loss_qty_sum,l.price_sum,l.price_count,l.conversion_rate,
        CASE
            WHEN r.data = d.data THEN COALESCE(t.osa_critical_count, 0::bigint)
            ELSE 0::bigint
        END AS osa_critical_count,
        CASE
            WHEN r.data = d.data THEN COALESCE(t.osa_risk_count, 0::bigint)
            ELSE 0::bigint
        END AS osa_risk_count
   FROM osa_ratio r
     CROSS JOIN LATERAL (SELECT DISTINCT nm_measure FROM gold.dim_conversao WHERE id_customer=r.id_customer) selected_measure
     LEFT JOIN loss l ON l.data=r.data AND l.id_customer=r.id_customer AND l.nm_measure=selected_measure.nm_measure
     JOIN latest_month d ON d.id_customer=r.id_customer
     LEFT JOIN tasks t ON t.id_customer=r.id_customer;

CREATE UNIQUE INDEX IF NOT EXISTS ux_nr_pbip_osa_semantic_default_key ON gold.nr_pbip_osa_semantic_default(id_customer,data,nm_measure);

COMMIT;
