CREATE OR REPLACE VIEW gold.vw_kpi_card_tvd AS
WITH daily_tvd AS (
    SELECT
        id_customer,
        id_time::date AS snapshot_date,
        SUM(COALESCE(tvd_simplificado, 0))::numeric AS tvd_value
    FROM gold.fato_ivd_tvd
    GROUP BY id_customer, id_time::date
),
month_ranked AS (
    SELECT
        id_customer,
        snapshot_date,
        date_trunc('month', snapshot_date)::date AS month_start,
        tvd_value,
        row_number() OVER (
            PARTITION BY id_customer, date_trunc('month', snapshot_date)
            ORDER BY snapshot_date DESC
        ) AS month_position
    FROM daily_tvd
),
month_end AS (
    SELECT id_customer, month_start, snapshot_date, tvd_value
    FROM month_ranked
    WHERE month_position = 1
),
anchors AS (
    SELECT id_customer, MAX(month_start) AS current_month
    FROM month_end
    GROUP BY id_customer
),
history AS (
    SELECT
        a.id_customer,
        MAX(m.snapshot_date) FILTER (
            WHERE m.month_start = a.current_month
        ) AS data_ultima_movimentacao,
        COALESCE(MAX(m.tvd_value) FILTER (
            WHERE m.month_start = a.current_month
        ), 0)::numeric AS tvd_mtd,
        COALESCE(MAX(m.tvd_value) FILTER (
            WHERE m.month_start = (a.current_month - interval '1 month')::date
        ), 0)::numeric AS tvd_mes_anterior,
        COALESCE(AVG(m.tvd_value) FILTER (
            WHERE m.month_start BETWEEN
                (a.current_month - interval '3 months')::date
                AND (a.current_month - interval '1 month')::date
        ), 0)::numeric AS tvd_media_u3m
    FROM anchors a
    JOIN month_end m ON m.id_customer = a.id_customer
    GROUP BY a.id_customer, a.current_month
),
tasks AS (
    SELECT
        id_customer,
        COUNT(id_item) FILTER (
            WHERE regra_critico = 'CRITICO' AND COALESCE(tvd, 0) > 0
        )::bigint AS itens_criticos,
        COUNT(id_item) FILTER (
            WHERE regra_critico = 'F' AND COALESCE(tvd, 0) > 0
        )::bigint AS itens_risco
    FROM gold.calculo_oportunidades
    GROUP BY id_customer
),
base AS (
    SELECT
        COALESCE(h.id_customer, t.id_customer) AS id_customer,
        h.data_ultima_movimentacao,
        COALESCE(h.tvd_mtd, 0) AS tvd_mtd,
        COALESCE(h.tvd_mes_anterior, 0) AS tvd_mes_anterior,
        COALESCE(h.tvd_media_u3m, 0) AS tvd_media_u3m,
        COALESCE(t.itens_criticos, 0) AS itens_criticos,
        COALESCE(t.itens_risco, 0) AS itens_risco
    FROM history h
    FULL JOIN tasks t ON t.id_customer = h.id_customer
),
scaled AS (
    SELECT
        b.*,
        GREATEST(tvd_mtd, tvd_mes_anterior, tvd_media_u3m, 1) AS scale_max
    FROM base b
)
SELECT
    id_customer,
    data_ultima_movimentacao,
    tvd_mtd,
    tvd_mes_anterior,
    tvd_media_u3m,
    itens_criticos,
    itens_risco,
    CASE
        WHEN abs(tvd_mtd) >= 1000000000 THEN 'R$ ' || replace(to_char(tvd_mtd / 1000000000, 'FM999999990.00'), '.', ',') || 'B'
        WHEN abs(tvd_mtd) >= 1000000 THEN 'R$ ' || replace(to_char(tvd_mtd / 1000000, 'FM999999990.00'), '.', ',') || 'M'
        WHEN abs(tvd_mtd) >= 1000 THEN 'R$ ' || replace(to_char(tvd_mtd / 1000, 'FM999999990.00'), '.', ',') || 'K'
        ELSE 'R$ ' || replace(to_char(tvd_mtd, 'FM999999990.00'), '.', ',')
    END AS tvd_mtd_label,
    CASE
        WHEN abs(tvd_mes_anterior) >= 1000000000 THEN 'R$ ' || replace(to_char(tvd_mes_anterior / 1000000000, 'FM999999990.00'), '.', ',') || 'B'
        WHEN abs(tvd_mes_anterior) >= 1000000 THEN 'R$ ' || replace(to_char(tvd_mes_anterior / 1000000, 'FM999999990.00'), '.', ',') || 'M'
        WHEN abs(tvd_mes_anterior) >= 1000 THEN 'R$ ' || replace(to_char(tvd_mes_anterior / 1000, 'FM999999990.00'), '.', ',') || 'K'
        ELSE 'R$ ' || replace(to_char(tvd_mes_anterior, 'FM999999990.00'), '.', ',')
    END AS tvd_mes_anterior_label,
    CASE
        WHEN abs(tvd_media_u3m) >= 1000000000 THEN 'R$ ' || replace(to_char(tvd_media_u3m / 1000000000, 'FM999999990.00'), '.', ',') || 'B'
        WHEN abs(tvd_media_u3m) >= 1000000 THEN 'R$ ' || replace(to_char(tvd_media_u3m / 1000000, 'FM999999990.00'), '.', ',') || 'M'
        WHEN abs(tvd_media_u3m) >= 1000 THEN 'R$ ' || replace(to_char(tvd_media_u3m / 1000, 'FM999999990.00'), '.', ',') || 'K'
        ELSE 'R$ ' || replace(to_char(tvd_media_u3m, 'FM999999990.00'), '.', ',')
    END AS tvd_media_u3m_label,
    CASE WHEN tvd_mtd < tvd_mes_anterior THEN '↓' WHEN tvd_mtd > tvd_mes_anterior THEN '↑' ELSE '•' END AS mtd_arrow,
    CASE WHEN tvd_mtd < tvd_mes_anterior THEN 'good' WHEN tvd_mtd > tvd_mes_anterior THEN 'bad' ELSE 'neutral' END AS mtd_status,
    CASE WHEN tvd_mes_anterior < tvd_media_u3m THEN '↓' WHEN tvd_mes_anterior > tvd_media_u3m THEN '↑' ELSE '•' END AS anterior_arrow,
    CASE WHEN tvd_mes_anterior < tvd_media_u3m THEN 'good' WHEN tvd_mes_anterior > tvd_media_u3m THEN 'bad' ELSE 'neutral' END AS anterior_status,
    round(90 - (75 * tvd_mtd / scale_max), 2) AS tvd_mtd_y,
    round(90 - (75 * tvd_mes_anterior / scale_max), 2) AS tvd_mes_anterior_y,
    round(90 - (75 * tvd_media_u3m / scale_max), 2) AS tvd_media_u3m_y
FROM scaled;

COMMENT ON VIEW gold.vw_kpi_card_tvd IS
'Fonte semantica do visual unico Handlebars TVD - Pre-ruptura.';
