-- Read-only audit snapshot, 2026-10-06. Not a migration; do not execute.
-- PostgreSQL has no reliable built-in creation/modification timestamps for these objects.

CREATE MATERIALIZED VIEW gold.nr_osa_causes_default AS
 WITH measures AS (
         SELECT DISTINCT nr_conversion_options.id_customer,
            nr_conversion_options.nm_measure
           FROM gold.nr_conversion_options
        ), converted AS (
         SELECT c.data,
            c.id_customer,
            c.motivo_osa,
            c.causa_osa,
            c.qtd_perda_osa,
            c.vl_perda_osa,
            m.nm_measure,
            COALESCE(cv.conversion_rate,
                CASE
                    WHEN m.nm_measure = 'valor'::text THEN 1.0
                    ELSE NULL::numeric
                END)::double precision AS conversion_rate
           FROM gold.fato_mensal_causa_osa c
             JOIN measures m ON m.id_customer = c.id_customer
             LEFT JOIN gold.dim_conversao cv ON cv.id_customer = c.id_customer AND cv.id_item::text = c.id_item AND cv.nm_measure = m.nm_measure
        )
 SELECT data,
    id_customer,
    nm_measure,
    motivo_osa,
    causa_osa,
    sum(COALESCE(qtd_perda_osa, 0::double precision)) AS qtd_perda_osa,
    sum(COALESCE(vl_perda_osa, 0::double precision)) AS vl_perda_osa,
    max(conversion_rate) AS conversion_rate,
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
   FROM converted
  GROUP BY data, id_customer, nm_measure, motivo_osa, causa_osa;
CREATE INDEX ix_nr_osa_causes_default ON gold.nr_osa_causes_default USING btree (id_customer, nm_measure, data, motivo_osa, causa_osa);

CREATE MATERIALIZED VIEW gold.nr_osa_matrix_default AS
 WITH latest AS (
         SELECT fato_historico.id_customer,
            max(fato_historico.mes_ano) AS latest_data
           FROM gold.fato_historico
          GROUP BY fato_historico.id_customer
        ), measures AS (
         SELECT DISTINCT nr_conversion_options.id_customer,
            nr_conversion_options.nm_measure
           FROM gold.nr_conversion_options
        ), history_enriched AS (
         SELECT h_1.mes_ano AS data,
            h_1.id_customer,
            h_1.id_item,
            l.regiao,
            l.rede,
            i.hierarquia_1,
            h_1.qtd_perda_osa,
            h_1.qtd_problemas_osa,
            h_1.qtd_item_ativo_osa
           FROM gold.fato_historico h_1
             LEFT JOIN gold.dim_local l ON l.id_customer = h_1.id_customer AND l.id_location = h_1.id_location
             LEFT JOIN gold.dim_itens i ON i.id_customer = h_1.id_customer AND i.id_item = h_1.id_item
        ), history_scopes AS (
         SELECT history_enriched.data,
            history_enriched.id_customer,
            history_enriched.id_item,
            'region'::text AS scope,
            history_enriched.regiao AS group_value,
            history_enriched.qtd_perda_osa,
            history_enriched.qtd_problemas_osa,
            history_enriched.qtd_item_ativo_osa
           FROM history_enriched
        UNION ALL
         SELECT history_enriched.data,
            history_enriched.id_customer,
            history_enriched.id_item,
            'retail'::text,
            history_enriched.rede,
            history_enriched.qtd_perda_osa,
            history_enriched.qtd_problemas_osa,
            history_enriched.qtd_item_ativo_osa
           FROM history_enriched
        UNION ALL
         SELECT history_enriched.data,
            history_enriched.id_customer,
            history_enriched.id_item,
            'item'::text,
            history_enriched.hierarquia_1,
            history_enriched.qtd_perda_osa,
            history_enriched.qtd_problemas_osa,
            history_enriched.qtd_item_ativo_osa
           FROM history_enriched
        ), history_month AS (
         SELECT h_1.data,
            h_1.id_customer,
            h_1.scope,
            h_1.group_value,
            m.nm_measure,
            sum(COALESCE(h_1.qtd_perda_osa, 0::double precision)) AS loss_base,
            sum(COALESCE(h_1.qtd_problemas_osa, 0::bigint))::double precision AS problem_base,
            sum(COALESCE(h_1.qtd_item_ativo_osa, 0::bigint))::double precision AS active_base,
            COALESCE(max(cv.conversion_rate),
                CASE
                    WHEN m.nm_measure = 'valor'::text THEN 1.0
                    ELSE NULL::numeric
                END)::double precision AS conversion_factor
           FROM history_scopes h_1
             JOIN measures m ON m.id_customer = h_1.id_customer
             LEFT JOIN gold.dim_conversao cv ON cv.id_customer = h_1.id_customer AND cv.id_item::text = h_1.id_item AND cv.nm_measure = m.nm_measure
          GROUP BY h_1.data, h_1.id_customer, h_1.scope, h_1.group_value, m.nm_measure
        ), history_period AS (
         SELECT h_1.data,
            h_1.id_customer,
            h_1.scope,
            h_1.group_value,
            h_1.nm_measure,
            h_1.loss_base,
            h_1.problem_base,
            h_1.active_base,
            h_1.conversion_factor,
            p.osa_period,
            p.osa_period_order
           FROM history_month h_1
             JOIN latest x USING (id_customer)
             CROSS JOIN LATERAL ( SELECT 'MTD'::text AS text,
                    1 AS int4
                  WHERE date_trunc('month'::text, h_1.data::timestamp with time zone) = date_trunc('month'::text, x.latest_data::timestamp with time zone)
                UNION ALL
                 SELECT 'Mês Anterior'::text,
                    2
                  WHERE date_trunc('month'::text, h_1.data::timestamp with time zone) = date_trunc('month'::text, x.latest_data - '1 mon'::interval)
                UNION ALL
                 SELECT 'U3M'::text,
                    3
                  WHERE h_1.data >= (date_trunc('month'::text, x.latest_data::timestamp with time zone) - '2 mons'::interval) AND h_1.data <= x.latest_data
                UNION ALL
                 SELECT 'YTD'::text,
                    5
                  WHERE EXTRACT(year FROM h_1.data) = EXTRACT(year FROM x.latest_data)) p(osa_period, osa_period_order)
        ), history_final AS (
         SELECT history_period.id_customer,
            history_period.nm_measure,
            history_period.scope,
            history_period.group_value,
            history_period.osa_period,
            history_period.osa_period_order,
            sum(history_period.loss_base) AS loss_base,
            sum(history_period.problem_base) AS problem_base,
            sum(history_period.active_base) AS active_base,
            max(history_period.conversion_factor) AS conversion_factor
           FROM history_period
          GROUP BY history_period.id_customer, history_period.nm_measure, history_period.scope, history_period.group_value, history_period.osa_period, history_period.osa_period_order
        ), cause_enriched AS (
         SELECT c_1.data,
            c_1.id_customer,
            l.regiao,
            l.rede,
            i.hierarquia_1,
            c_1.vl_perda_osa
           FROM gold.fato_mensal_causa_osa c_1
             LEFT JOIN gold.dim_local l ON l.id_customer = c_1.id_customer AND l.id_location = c_1.id_location
             LEFT JOIN gold.dim_itens i ON i.id_customer = c_1.id_customer AND i.id_item = c_1.id_item
        ), cause_scopes AS (
         SELECT cause_enriched.data,
            cause_enriched.id_customer,
            'region'::text AS scope,
            cause_enriched.regiao AS group_value,
            cause_enriched.vl_perda_osa
           FROM cause_enriched
        UNION ALL
         SELECT cause_enriched.data,
            cause_enriched.id_customer,
            'retail'::text,
            cause_enriched.rede,
            cause_enriched.vl_perda_osa
           FROM cause_enriched
        UNION ALL
         SELECT cause_enriched.data,
            cause_enriched.id_customer,
            'item'::text,
            cause_enriched.hierarquia_1,
            cause_enriched.vl_perda_osa
           FROM cause_enriched
        ), cause_month AS (
         SELECT cause_scopes.data,
            cause_scopes.id_customer,
            cause_scopes.scope,
            cause_scopes.group_value,
            sum(COALESCE(cause_scopes.vl_perda_osa, 0::double precision)) AS loss_value
           FROM cause_scopes
          GROUP BY cause_scopes.data, cause_scopes.id_customer, cause_scopes.scope, cause_scopes.group_value
        ), cause_period AS (
         SELECT c_1.data,
            c_1.id_customer,
            c_1.scope,
            c_1.group_value,
            c_1.loss_value,
            p.osa_period,
            p.osa_period_order
           FROM cause_month c_1
             JOIN latest x USING (id_customer)
             CROSS JOIN LATERAL ( SELECT 'MTD'::text AS text,
                    1 AS int4
                  WHERE date_trunc('month'::text, c_1.data::timestamp with time zone) = date_trunc('month'::text, x.latest_data::timestamp with time zone)
                UNION ALL
                 SELECT 'Mês Anterior'::text,
                    2
                  WHERE date_trunc('month'::text, c_1.data::timestamp with time zone) = date_trunc('month'::text, x.latest_data - '1 mon'::interval)
                UNION ALL
                 SELECT 'U3M'::text,
                    3
                  WHERE c_1.data >= (date_trunc('month'::text, x.latest_data::timestamp with time zone) - '2 mons'::interval) AND c_1.data <= x.latest_data
                UNION ALL
                 SELECT 'YTD'::text,
                    5
                  WHERE EXTRACT(year FROM c_1.data) = EXTRACT(year FROM x.latest_data)) p(osa_period, osa_period_order)
        ), cause_final AS (
         SELECT cause_period.id_customer,
            cause_period.scope,
            cause_period.group_value,
            cause_period.osa_period,
            cause_period.osa_period_order,
            sum(cause_period.loss_value) AS loss_value
           FROM cause_period
          GROUP BY cause_period.id_customer, cause_period.scope, cause_period.group_value, cause_period.osa_period, cause_period.osa_period_order
        )
 SELECT h.id_customer,
    h.nm_measure,
    h.scope,
    h.osa_period,
    h.osa_period_order,
        CASE
            WHEN h.scope = 'region'::text THEN h.group_value
            ELSE NULL::text
        END AS regiao,
        CASE
            WHEN h.scope = 'retail'::text THEN h.group_value
            ELSE NULL::text
        END AS rede,
        CASE
            WHEN h.scope = 'item'::text THEN h.group_value
            ELSE NULL::text
        END AS hierarquia_1,
    NULL::text AS bandeira,
    NULL::text AS uf,
    NULL::text AS cidade,
    NULL::text AS tipo_local,
    NULL::text AS loja,
    NULL::text AS tp_activity_level,
    NULL::text AS activity_level,
    NULL::text AS item,
    NULL::text AS descricao_marca,
    NULL::text AS hierarquia_2,
    NULL::text AS hierarquia_3,
    c.loss_value,
    h.loss_base * h.conversion_factor AS loss_qty,
    h.problem_base * h.conversion_factor AS problem_qty,
    h.problem_base,
    h.active_base
   FROM history_final h
     LEFT JOIN cause_final c ON c.id_customer = h.id_customer AND c.scope = h.scope AND c.osa_period = h.osa_period AND NOT c.group_value IS DISTINCT FROM h.group_value;
CREATE INDEX ix_nr_osa_matrix_default ON gold.nr_osa_matrix_default USING btree (id_customer, nm_measure, scope, osa_period, osa_period_order);

CREATE MATERIALIZED VIEW gold.nr_osa_monthly_default AS
 WITH measures AS (
         SELECT DISTINCT nr_conversion_options.id_customer,
            nr_conversion_options.nm_measure
           FROM gold.nr_conversion_options
        ), hist_month AS (
         SELECT h_1.mes_ano AS data,
            h_1.id_customer,
            sum(COALESCE(h_1.faturamento, 0::double precision)) AS faturamento_sum,
            sum(COALESCE(h_1.volume_unidades, 0::double precision)) AS volume_sum,
            sum(COALESCE(h_1.qtd_perda_osa, 0::double precision)) AS loss_qty_sum,
            sum(COALESCE(h_1.qtd_problemas_osa, 0::bigint))::double precision AS problem_sum,
            sum(COALESCE(h_1.qtd_item_ativo_osa, 0::bigint))::double precision AS active_sum,
            sum(h_1.avg_sales_price) AS sales_price_sum,
            count(h_1.avg_sales_price) AS sales_price_count
           FROM gold.fato_historico h_1
          GROUP BY h_1.mes_ano, h_1.id_customer
        ), cause_month AS (
         SELECT c_1.data,
            c_1.id_customer,
            sum(COALESCE(c_1.qtd_perda_osa, 0::double precision)) AS loss_qty_sum,
            sum(COALESCE(c_1.vl_perda_osa, 0::double precision)) AS loss_value_sum,
            sum(COALESCE(c_1.qtd_problemas_osa, 0::bigint))::double precision AS problem_sum,
            sum(COALESCE(c_1.qtd_itens_ativos, 0::bigint))::double precision AS active_sum,
            sum(COALESCE(c_1.volume_unidades, 0::double precision)) AS volume_sum,
            sum(COALESCE(c_1.faturamento, 0::double precision)) AS faturamento_sum,
            sum(COALESCE(c_1.preco_medio, 0::double precision)) AS price_sum
           FROM gold.fato_mensal_causa_osa c_1
          GROUP BY c_1.data, c_1.id_customer
        ), hist_factor AS (
         SELECT h_1.data,
            h_1.id_customer,
            m.nm_measure,
            COALESCE(max(cv.conversion_rate),
                CASE
                    WHEN m.nm_measure = 'valor'::text THEN 1.0
                    ELSE NULL::numeric
                END)::double precision AS conversion_factor
           FROM ( SELECT DISTINCT fato_historico.mes_ano AS data,
                    fato_historico.id_customer,
                    fato_historico.id_item
                   FROM gold.fato_historico) h_1
             JOIN measures m ON m.id_customer = h_1.id_customer
             LEFT JOIN gold.dim_conversao cv ON cv.id_customer = h_1.id_customer AND cv.id_item::text = h_1.id_item AND cv.nm_measure = m.nm_measure
          GROUP BY h_1.data, h_1.id_customer, m.nm_measure
        ), cause_factor AS (
         SELECT c_1.data,
            c_1.id_customer,
            m.nm_measure,
            COALESCE(max(cv.conversion_rate),
                CASE
                    WHEN m.nm_measure = 'valor'::text THEN 1.0
                    ELSE NULL::numeric
                END)::double precision AS conversion_factor
           FROM ( SELECT DISTINCT fato_mensal_causa_osa.data,
                    fato_mensal_causa_osa.id_customer,
                    fato_mensal_causa_osa.id_item
                   FROM gold.fato_mensal_causa_osa) c_1
             JOIN measures m ON m.id_customer = c_1.id_customer
             LEFT JOIN gold.dim_conversao cv ON cv.id_customer = c_1.id_customer AND cv.id_item::text = c_1.id_item AND cv.nm_measure = m.nm_measure
          GROUP BY c_1.data, c_1.id_customer, m.nm_measure
        )
 SELECT h.data,
    h.id_customer,
    hf.nm_measure,
        CASE
            WHEN h.faturamento_sum > 0::double precision THEN h.faturamento_sum
            WHEN hf.conversion_factor IS NOT NULL AND h.sales_price_count > 0 THEN h.volume_sum * hf.conversion_factor * (h.sales_price_sum / h.sales_price_count::double precision * hf.conversion_factor)
            ELSE NULL::double precision
        END AS sellout_value,
    c.loss_value_sum AS loss_value,
        CASE
            WHEN c.faturamento_sum > 0::double precision THEN 100.0::double precision * c.loss_value_sum / NULLIF(c.faturamento_sum, 0::double precision)
            ELSE 100.0::double precision * c.loss_value_sum / NULLIF(c.volume_sum * c.price_sum, 0::double precision)
        END AS loss_value_percent,
    100.0::double precision * (1::double precision - h.problem_sum / NULLIF(h.active_sum, 0::double precision)) AS osa_percent,
    c.volume_sum * cf.conversion_factor AS sales_qty,
    c.loss_qty_sum * cf.conversion_factor AS loss_qty,
        CASE
            WHEN hf.conversion_factor IS NULL THEN NULL::double precision
            ELSE 100.0::double precision * (h.loss_qty_sum * hf.conversion_factor) / NULLIF(h.volume_sum * hf.conversion_factor, 0::double precision)
        END AS loss_qty_percent,
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
   FROM hist_month h
     JOIN hist_factor hf USING (data, id_customer)
     LEFT JOIN cause_month c USING (data, id_customer)
     LEFT JOIN cause_factor cf ON cf.data = h.data AND cf.id_customer = h.id_customer AND cf.nm_measure = hf.nm_measure;
CREATE INDEX ix_nr_osa_monthly_default ON gold.nr_osa_monthly_default USING btree (id_customer, nm_measure, data);

CREATE MATERIALIZED VIEW gold.nr_osa_weekly_default AS
 WITH weekly_base AS (
         SELECT w_1.id_time AS data,
            w_1.cd_week,
            w_1.id_customer,
            w_1.id_item,
            w_1.id_location,
            w_1.volume_unidade,
            w_1.faturamento,
            w_1.qtd_perda_osa,
            w_1.qtd_problemas_osa,
            w_1.qtd_item_ativo_osa,
            w_1.avg_sales_price,
            w_1.avg_price_cost
           FROM gold.fato_semanal w_1
        ), ranked_weeks AS (
         SELECT weekly_base.id_customer,
            weekly_base.cd_week,
            max(weekly_base.data) AS data,
            dense_rank() OVER (PARTITION BY weekly_base.id_customer ORDER BY weekly_base.cd_week DESC) AS week_rank
           FROM weekly_base
          GROUP BY weekly_base.id_customer, weekly_base.cd_week
        ), scoped AS (
         SELECT w_1.data,
            w_1.cd_week,
            w_1.id_customer,
            w_1.id_item,
            w_1.id_location,
            w_1.volume_unidade,
            w_1.faturamento,
            w_1.qtd_perda_osa,
            w_1.qtd_problemas_osa,
            w_1.qtd_item_ativo_osa,
            w_1.avg_sales_price,
            w_1.avg_price_cost
           FROM weekly_base w_1
             JOIN ranked_weeks r USING (id_customer, cd_week)
          WHERE r.week_rank <= 13
        ), measures AS (
         SELECT DISTINCT nr_conversion_options.id_customer,
            nr_conversion_options.nm_measure
           FROM gold.nr_conversion_options
        ), weekly AS (
         SELECT s.data,
            s.cd_week,
            s.id_customer,
            sum(COALESCE(s.faturamento, 0::double precision)) AS faturamento_sum,
            sum(COALESCE(s.volume_unidade, 0::double precision)) AS volume_sum,
            sum(COALESCE(s.qtd_perda_osa, 0::double precision)) AS loss_qty_sum,
            sum(COALESCE(s.qtd_problemas_osa, 0::bigint))::double precision AS problem_sum,
            sum(COALESCE(s.qtd_item_ativo_osa, 0::bigint))::double precision AS active_sum,
            avg(s.avg_sales_price) AS avg_sales_price,
            avg(s.avg_price_cost) AS avg_price_cost
           FROM scoped s
          GROUP BY s.data, s.cd_week, s.id_customer
        ), factor AS (
         SELECT s.data,
            s.id_customer,
            m.nm_measure,
            COALESCE(max(cv.conversion_rate),
                CASE
                    WHEN m.nm_measure = 'valor'::text THEN 1.0
                    ELSE NULL::numeric
                END)::double precision AS conversion_factor
           FROM ( SELECT DISTINCT scoped.data,
                    scoped.id_customer,
                    scoped.id_item
                   FROM scoped) s
             JOIN measures m ON m.id_customer = s.id_customer
             LEFT JOIN gold.dim_conversao cv ON cv.id_customer = s.id_customer AND cv.id_item::text = s.id_item AND cv.nm_measure = m.nm_measure
          GROUP BY s.data, s.id_customer, m.nm_measure
        ), week_locations AS (
         SELECT DISTINCT scoped.data,
            scoped.id_customer,
            scoped.id_location
           FROM scoped
        ), opportunities AS (
         SELECT calculo_oportunidades.id_customer,
            calculo_oportunidades.id_location,
            calculo_oportunidades.demanda_media
           FROM gold.calculo_oportunidades
          WHERE COALESCE(calculo_oportunidades.qtd_item_ativo_osa_m0, 0::bigint) > 0
        ), demand AS (
         SELECT wl.data,
            wl.id_customer,
            sum(COALESCE(o.demanda_media, 0::double precision)) AS demand_sum
           FROM week_locations wl
             JOIN opportunities o ON o.id_customer = wl.id_customer AND o.id_location = wl.id_location
          GROUP BY wl.data, wl.id_customer
        )
 SELECT w.data,
    w.cd_week,
    w.id_customer,
    f.nm_measure,
        CASE
            WHEN w.faturamento_sum > 0::double precision THEN w.faturamento_sum
            WHEN f.conversion_factor IS NOT NULL AND w.avg_sales_price IS NOT NULL THEN w.volume_sum * f.conversion_factor * (w.avg_sales_price * f.conversion_factor)
            ELSE NULL::double precision
        END AS sellout_value,
    w.loss_qty_sum * w.avg_price_cost AS loss_value,
        CASE
            WHEN w.faturamento_sum > 0::double precision THEN 100.0::double precision * (w.loss_qty_sum * w.avg_price_cost) / NULLIF(w.faturamento_sum, 0::double precision)
            ELSE 100.0::double precision * (w.loss_qty_sum * w.avg_price_cost) / NULLIF(w.volume_sum * w.avg_price_cost, 0::double precision)
        END AS loss_value_percent,
    100.0::double precision * (1::double precision - w.problem_sum / NULLIF(w.active_sum, 0::double precision)) AS osa_percent,
    w.volume_sum * f.conversion_factor AS sales_qty,
    w.loss_qty_sum * f.conversion_factor AS loss_qty,
    100.0::double precision * w.loss_qty_sum / NULLIF(d.demand_sum * 30.0::double precision, 0::double precision) AS loss_qty_percent,
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
     JOIN factor f USING (data, id_customer)
     LEFT JOIN demand d USING (data, id_customer);
CREATE INDEX ix_nr_osa_weekly_default ON gold.nr_osa_weekly_default USING btree (id_customer, nm_measure, cd_week, data);
