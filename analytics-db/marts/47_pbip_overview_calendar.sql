-- PBIP import-time calendar, independent of MAX(fact date).
-- Refresh this serving object explicitly alongside the affected overview marts.
BEGIN;
CREATE MATERIALIZED VIEW IF NOT EXISTS gold.nr_pbip_calendar AS
WITH imported AS (
    SELECT (CURRENT_TIMESTAMP AT TIME ZONE 'America/Sao_Paulo')::date AS import_date
), days AS (
    SELECT import_date, import_date - 1 AS data_at, d::date AS data
    FROM imported CROSS JOIN LATERAL generate_series(
        import_date - 730, import_date - 1, INTERVAL '1 day') d
)
SELECT c.id_customer, import_date, data_at, data,
    date_trunc('month', data) = date_trunc('month', data_at) AS m0,
    date_trunc('month', data) = date_trunc('month', data_at) - INTERVAL '1 month' AS m1,
    date_trunc('month', data) = date_trunc('month', data_at) - INTERVAL '2 months' AS m2,
    date_trunc('month', data) = date_trunc('month', data_at) - INTERVAL '3 months' AS m3,
    data < date_trunc('month', data_at) AND data >= date_trunc('month', data_at) - INTERVAL '3 months' AS u3m,
    data < date_trunc('month', data_at) AND data >= date_trunc('month', data_at) - INTERVAL '12 months' AS u12m,
    date_trunc('month', data) = date_trunc('month', data_at) AND EXTRACT(day FROM data) <= EXTRACT(day FROM data_at) AS mtd
FROM days CROSS JOIN gold.dim_customer c WHERE c.id_customer = 290;
CREATE UNIQUE INDEX IF NOT EXISTS ux_nr_pbip_calendar_customer_data
    ON gold.nr_pbip_calendar(id_customer,data);
COMMENT ON MATERIALIZED VIEW gold.nr_pbip_calendar IS
'LACTALIS PBIP calendar: frozen publication/import date, calendar ends one day before import; never uses MAX(fact date).';
COMMIT;
