-- C14 numeric-product existence checks. The predicate includes real zero
-- operands and cancellations; it excludes only products that are BLANK.
-- All tenants retain their key. Existing marts and indexes remain intact.
CREATE INDEX IF NOT EXISTS ix_pbip_history_sales_cost_present
ON gold.nr_pbip_overview_history
    (id_customer, data, tp_activity_level)
INCLUDE (id_location, id_item)
WHERE volume_unidades IS NOT NULL AND avg_price_cost IS NOT NULL;

