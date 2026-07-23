-- =============================================================================
-- components.sql  —  RAW export: NEW components
-- =============================================================================
-- Purpose      : One row per NEW component SKU (first-ever appearance within the
--                reporting window). This is the ROOT of the dashboard lineage:
--                New Component -> Combo -> Listing -> Orders -> Sales -> Returns.
-- Source tables: supplier.order_items oi  (component line items)
--                supplier.orders o        (purchase order + container ref)
--                supplier.suppliers s     (supplier master)
--                supplier.containers c    (container name)
-- Join logic   : oi.order_id = o.id ; o.supplier_id = s.id ;
--                c.id::text = o.container_id  (container_id is text, may be 'mixed')
-- Filters      : "new" = MIN(created_at) >= :start_date  (first-seen in window)
--                :start_date = '2026-01-01' , :end_date = CURRENT_DATE
-- Output       : sku, description, supplier, po, container, created_date,
--                first_created, status_arrived, cbm
-- Grain        : one row per new component SKU (latest order_item row per sku)
-- NOTE         : No aggregation of metrics — combo/market/orders are derived in JS.
-- =============================================================================
WITH nc AS (
  SELECT sku, MIN(created_at) AS first_created
  FROM supplier.order_items
  WHERE sku <> ''
  GROUP BY sku
  HAVING MIN(created_at) >= '2026-01-01'        -- :start_date
     AND MIN(created_at) <  CURRENT_DATE + 1     -- :end_date (inclusive of today)
)
-- FIXED (2026-07-23): the date exposed to the dashboard is nc.first_created
-- (MIN created_at = first-seen), NOT the latest re-order date. Using the latest
-- date shifted components into later months and skewed sub-range date filtering.
SELECT DISTINCT ON (oi.sku)
  oi.sku,
  LEFT(COALESCE(oi.english_description,''), 80)             AS description,
  s.name                                                    AS supplier,
  o.order_id                                                AS po,
  COALESCE(c.name, o.container_id)                          AS container,
  nc.first_created::date                                    AS created_date,   -- first-seen (was: latest re-order)
  CASE WHEN o.status_arrived = 1 THEN 1 ELSE 0 END          AS status_arrived
FROM nc
JOIN supplier.order_items oi ON oi.sku = nc.sku
LEFT JOIN supplier.orders     o ON oi.order_id  = o.id
LEFT JOIN supplier.suppliers  s ON o.supplier_id = s.id
LEFT JOIN supplier.containers c ON c.id::text    = o.container_id
ORDER BY oi.sku, oi.created_at DESC;
