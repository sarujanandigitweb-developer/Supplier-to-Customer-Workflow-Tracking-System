-- ============================================================================
-- Title:            Dashboard Data Queries
-- Purpose:          Read-only SQL that produces each metric rendered by the
--                   dashboard (captured into dashboard/data.js snapshot).
-- Business Question: Which query generates each KPI / table / chart value?
-- Source:           public.* and supplier.* (verified mapping); period 2026-03-01 -> CURRENT_DATE
-- Evidence:         dashboard/data.js (snapshot 2026-07-21); documentation/postgres_data_mapping.md
-- Status:           IN USE — reconstructed to match the metrics the dashboard renders
-- Owner:            Dashboard Development Team
-- Reviewer:         Varmen
-- Next Step:        Add impressions/clicks aggregate once the snapshot includes traffic/ppc
-- Pass/Fail Rule:   PASS when each query reproduces the corresponding data.js value
-- Known Limitations: Reporting period fixed to snapshot window; traffic/ppc deferred;
--                    Warehouse Receive Date has no source (arrival via status_arrived only)
-- NOTE: Queries are grounded in the verified table/column mapping and the dashboard's
--       metric definitions (script.js). They are read-only; they never modify data.
-- ============================================================================

-- KPI: Suppliers / Purchase Orders / Containers -------------------------------
SELECT
  (SELECT COUNT(*) FROM supplier.suppliers)                                   AS suppliers,          -- 47
  (SELECT COUNT(*) FROM supplier.orders)                                      AS purchase_orders,    -- 250
  (SELECT COUNT(*) FROM supplier.orders WHERE order_date >= DATE '2026-03-01') AS pos_since_march,    -- 99
  (SELECT COUNT(*) FROM supplier.containers)                                  AS containers,         -- 24
  (SELECT COUNT(*) FROM supplier.final_containers)                            AS final_containers;   -- 16

-- KPI: New Components since March (supplier order lines + distinct SKUs) -------
SELECT COUNT(DISTINCT sku) AS new_component_skus,          -- component count
       COUNT(*)            AS component_order_lines         -- 1,390 order lines
FROM supplier.order_items oi
JOIN supplier.orders o ON o.id = oi.order_id
WHERE o.order_date >= DATE '2026-03-01';

-- KPI: Combo SKUs created since March + listed / non-listed -------------------
-- Combo = SKU containing '+'. Listed = present in listing_data with wrong_sku=0.
SELECT COUNT(DISTINCT sku) AS combos_all
FROM public.listing_data WHERE sku LIKE '%+%' AND wrong_sku = 0;                -- listed combos universe (16,015)

-- KPI: Orders / Units / Sales / AOV (Completed, period) -----------------------
SELECT
  COUNT(DISTINCT order_id)                                   AS orders,      -- 97,050
  SUM(COALESCE(quantity,0))                                  AS units,       -- 158,685
  SUM(COALESCE(order_total,0))                               AS sales,       -- 2,304,870.01
  SUM(COALESCE(order_total,0)) / NULLIF(COUNT(DISTINCT order_id),0) AS aov    -- 23.75
FROM public.order_transaction
WHERE order_status = 'Completed'
  AND order_date::date >= DATE '2026-03-01';

-- Marketplace Distribution (listings + combo listings per channel) ------------
SELECT which_channel_name AS channel,
       COUNT(*)                                   AS listings,
       COUNT(*) FILTER (WHERE sku LIKE '%+%')     AS combo_listings
FROM public.listing_data
WHERE wrong_sku = 0
GROUP BY which_channel_name
ORDER BY listings DESC;   -- shopify 52,659 / amazon 40,734 / ebay 13,946 / B&Q 3,843

-- Sales Trend (monthly revenue) ----------------------------------------------
SELECT DATE_TRUNC('month', order_date) AS month,
       SUM(COALESCE(order_total,0))    AS sales,
       COUNT(DISTINCT order_id)        AS orders
FROM public.order_transaction
WHERE order_status = 'Completed'
  AND order_date::date >= DATE '2026-03-01'
GROUP BY 1 ORDER BY 1;

-- Returns by channel (lines + qty) -------------------------------------------
SELECT 'amazon' channel, COUNT(*) lines, SUM(COALESCE(qty,0)) qty
  FROM public.amazon_returns WHERE request_date >= DATE '2026-03-01'
UNION ALL SELECT 'ebay',  COUNT(*), 0 FROM public.ebay_returns
UNION ALL SELECT 'shopify', COUNT(*), 0 FROM public.shopify_returns;   -- Amazon 3,297/4,258; eBay 906; Shopify 366

-- Component Journey (supplier -> PO -> container -> component) -----------------
SELECT oi.sku, oi.english_description AS description,
       s.name AS supplier, o.order_id AS po,
       c.name AS container, oi.created_at::date AS created,
       CASE WHEN o.status_arrived = 1 THEN 'Arrived' ELSE 'In Transit' END AS arrival
FROM supplier.order_items oi
JOIN supplier.orders o     ON o.id = oi.order_id
JOIN supplier.suppliers s  ON s.id = o.supplier_id
LEFT JOIN supplier.containers c ON c.id::text = o.container_id
WHERE o.order_date >= DATE '2026-03-01'
ORDER BY oi.created_at DESC;

-- Purchase Orders (supplier & container view) ---------------------------------
SELECT s.name AS supplier, o.order_id AS po, c.name AS container,
       CASE WHEN o.status_arrived = 1 THEN 'Arrived' ELSE 'In Transit' END AS arrived,
       o.order_date, o.expected_completion_date, o.finished_date
FROM supplier.orders o
JOIN supplier.suppliers s ON s.id = o.supplier_id
LEFT JOIN supplier.containers c ON c.id::text = o.container_id
WHERE o.order_date >= DATE '2026-03-01'
ORDER BY o.order_date DESC;
-- NOTE: Warehouse Receive Date is intentionally absent — no such column exists.

-- Impressions / Clicks (DEFERRED — data exists but not in current snapshot) ---
-- SELECT SUM(impression) AS organic_impressions, SUM(click) AS organic_clicks FROM public.traffic_data WHERE date >= DATE '2026-03-01';
-- SELECT SUM(impressions) AS paid_impressions, SUM(clicks) AS paid_clicks FROM public.ppc_performance WHERE date >= DATE '2026-03-01';
