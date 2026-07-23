-- =============================================================================
-- orders.sql  —  RAW export: Orders & Sales for qualifying combos
-- =============================================================================
-- Purpose      : Every order line for the qualifying combo SKUs. This single raw
--                dataset powers BOTH Orders (count) and Sales (SUM order_total),
--                Units, AOV, trend and Top Sellers — all computed in JS. Per the
--                business rule, orders are scoped by the COMBO SET (not by an
--                independent transaction-date filter); order_date is exported so
--                the client date range can further subset if desired.
-- Source tables: public.order_transaction ot (+ lineage CTEs)
-- Join logic   : ot.sku IN (qualifying combos)
-- Filters      : new component first-seen >= :start_date ('2026-01-01') ;
--                ot.order_date >= :start_date (export window bound).
--                order_status kept RAW (all statuses) so JS can filter
--                'Completed' for revenue and analyse cancellations/refunds.
-- Output       : order_item_info, order_id, sku, asin, item_id, source_name,
--                market_place, order_status, order_date, quantity, order_total,
--                fba_sales
-- Grain        : one row per order line item.
-- =============================================================================
WITH nc AS (
  SELECT sku FROM supplier.order_items
  WHERE sku <> '' GROUP BY sku HAVING MIN(created_at) >= '2026-01-01'   -- :start_date
),
combo_universe AS (
  SELECT DISTINCT sku FROM public.listing_data     WHERE wrong_sku = 0 AND sku LIKE '%+%'
  UNION
  SELECT DISTINCT sku FROM public.order_transaction WHERE sku LIKE '%+%'
),
qc AS (
  SELECT DISTINCT c.sku
  FROM combo_universe c
  CROSS JOIN LATERAL (SELECT TRIM(x) AS part FROM unnest(string_to_array(c.sku,'+')) x) p
  WHERE p.part IN (SELECT sku FROM nc)
)
SELECT
  ot.order_item_info,
  ot.order_id,
  ot.sku,
  ot.asin,
  ot.item_id,
  ot.source_name,
  ot.market_place,
  ot.order_status,
  ot.order_date::date       AS order_date,
  ot.quantity,
  ot.order_total,
  ot.fba_sales
FROM public.order_transaction ot
WHERE ot.sku IN (SELECT sku FROM qc)
  AND ot.order_date >= '2026-01-01'       -- :start_date
ORDER BY ot.order_date DESC;
