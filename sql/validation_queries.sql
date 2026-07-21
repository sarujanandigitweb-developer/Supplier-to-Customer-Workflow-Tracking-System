-- ============================================================================
-- Title:            Dashboard Validation Queries
-- Purpose:          Read-only SQL to validate that dashboard values match live
--                   PostgreSQL for the reporting period.
-- Business Question: Do the dashboard's rendered numbers equal live PostgreSQL?
-- Source:           public.* / supplier.* ; period 2026-03-01 -> CURRENT_DATE
-- Evidence:         evidence/data_validation_results.md ; validation/validation_checklist.md
-- Status:           IN USE — 13 PASS / 2 disclosed FAIL
-- Owner:            Dashboard Development Team
-- Reviewer:         Varmen; receive-date -> Tamilchelvan
-- Next Step:        Re-run after snapshot refresh (traffic/ppc) and backend replication
-- Pass/Fail Rule:   PASS when each result equals the data.js value (± snapshot timing)
-- Known Limitations: "Today" drifts vs snapshot; receive-date absent; traffic/ppc deferred
-- ============================================================================

-- V1: Supplier / PO / Container counts (expect 47 / 250 / 24) -----------------
SELECT
  (SELECT COUNT(*) FROM supplier.suppliers)  AS suppliers,       -- expect 47
  (SELECT COUNT(*) FROM supplier.orders)     AS purchase_orders, -- expect 250
  (SELECT COUNT(*) FROM supplier.containers) AS containers;      -- expect 24

-- V2: Orders / Units / Sales / AOV (expect 97,050 / 158,685 / 2,304,870.01 / 23.75)
SELECT
  COUNT(DISTINCT order_id)                                          AS orders,
  SUM(COALESCE(quantity,0))                                         AS units,
  ROUND(SUM(COALESCE(order_total,0))::numeric, 2)                   AS sales,
  ROUND((SUM(COALESCE(order_total,0)) / NULLIF(COUNT(DISTINCT order_id),0))::numeric, 2) AS aov
FROM public.order_transaction
WHERE order_status = 'Completed' AND order_date::date >= DATE '2026-03-01';

-- V3: Listed combo universe (expect 16,015) ----------------------------------
SELECT COUNT(DISTINCT sku) AS listed_combos
FROM public.listing_data WHERE sku LIKE '%+%' AND wrong_sku = 0;

-- V4: Marketplace distribution (expect shopify 52,659 / amazon 40,734 / ...) --
SELECT which_channel_name AS channel, COUNT(*) AS listings
FROM public.listing_data WHERE wrong_sku = 0
GROUP BY which_channel_name ORDER BY listings DESC;

-- V5: Returns by channel (expect Amazon 3,297 lines / 4,258 qty; eBay 906; Shopify 366)
SELECT 'amazon' channel, COUNT(*) lines, SUM(COALESCE(qty,0)) qty
  FROM public.amazon_returns WHERE request_date >= DATE '2026-03-01'
UNION ALL SELECT 'ebay',    COUNT(*), 0 FROM public.ebay_returns
UNION ALL SELECT 'shopify', COUNT(*), 0 FROM public.shopify_returns;

-- V6: New components since March (expect 1,390 order lines) -------------------
SELECT COUNT(*) AS component_order_lines, COUNT(DISTINCT oi.sku) AS distinct_component_skus
FROM supplier.order_items oi
JOIN supplier.orders o ON o.id = oi.order_id
WHERE o.order_date >= DATE '2026-03-01';

-- V7: Component -> Combo match rate (expect 1,339 of 1,812) -------------------
WITH parts AS (
  SELECT DISTINCT TRIM(unnest(string_to_array(sku,'+'))) AS part_sku
  FROM public.order_transaction WHERE sku LIKE '%+%'
)
SELECT
  (SELECT COUNT(*) FROM parts p WHERE EXISTS (SELECT 1 FROM public.components_sot_skus c WHERE c.sku=p.part_sku)) AS parts_matched,
  (SELECT COUNT(DISTINCT sku) FROM public.components_sot_skus) AS total_components;

-- V8: Warehouse Receive Date = NOT FOUND (validation of the gap) --------------
-- Expect: zero columns matching a receive/received date anywhere.
SELECT COUNT(*) AS receive_date_columns_found
FROM information_schema.columns
WHERE (column_name ILIKE '%receive%' OR column_name ILIKE '%grn%' OR column_name ILIKE '%inward%')
  AND column_name ILIKE '%date%';   -- expect 0

-- V9: Traffic / PPC exist in DB (DEFERRED from snapshot) ----------------------
SELECT 'traffic_data' t, COUNT(*) n FROM public.traffic_data
UNION ALL SELECT 'ppc_performance', COUNT(*) FROM public.ppc_performance;   -- exist (~9.3M / ~25.8M)
