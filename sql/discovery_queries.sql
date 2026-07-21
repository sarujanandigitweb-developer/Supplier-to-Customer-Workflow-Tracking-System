-- ============================================================================
-- Title:            PostgreSQL Discovery Queries
-- Purpose:          The read-only queries used to discover and verify the data
--                   sources behind the Supplier-to-Customer Workflow dashboard.
-- Business Question: Which schemas/tables/keys hold each of the 14 required data
--                   points, and which are usable?
-- Source:           claude_ai_postgres MCP (read-only), discovery date 2026-07-21
-- Evidence:         evidence/postgres_discovery_evidence.md
-- Status:           EXECUTED — 13 usable, 1 NOT FOUND (Warehouse Receive Date)
-- Owner:            Dashboard Development Team
-- Reviewer:         Varmen; purchasing gap -> Tamilchelvan
-- Next Step:        Re-run after purchasing backend replication
-- Pass/Fail Rule:   PASS when each requirement resolves to a table+count or NOT FOUND
-- Known Limitations: Read-only; supplier.* availability is connection-dependent
-- ============================================================================

-- 1) Enumerate user schemas ---------------------------------------------------
SELECT schema_name FROM information_schema.schemata
WHERE schema_name NOT LIKE 'pg_%' AND schema_name <> 'information_schema'
ORDER BY schema_name;

-- 2) Table count + estimated rows per user schema -----------------------------
SELECT n.nspname AS schema, COUNT(*) AS tables, SUM(c.reltuples)::bigint AS est_rows
FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE c.relkind='r' AND n.nspname NOT IN ('pg_catalog','information_schema')
  AND n.nspname NOT LIKE 'pg_temp%' AND n.nspname NOT LIKE 'pg_toast%'
GROUP BY n.nspname ORDER BY est_rows DESC NULLS LAST;

-- 3) Hunt for date/receive/container columns across the key tables ------------
SELECT table_schema, table_name, column_name, data_type
FROM information_schema.columns
WHERE (table_schema='public' AND table_name IN ('listing_data','inv_final_stock','location_wise_inv_stock'))
   OR (table_schema='supplier' AND table_name IN ('orders','order_items','containers','final_containers'))
ORDER BY table_schema, table_name, ordinal_position;

-- 4) Supplier schema live row counts (connection-dependent — always re-check) --
SELECT 'suppliers' t, COUNT(*) n FROM supplier.suppliers
UNION ALL SELECT 'orders', COUNT(*) FROM supplier.orders
UNION ALL SELECT 'order_items', COUNT(*) FROM supplier.order_items
UNION ALL SELECT 'containers', COUNT(*) FROM supplier.containers
UNION ALL SELECT 'final_containers', COUNT(*) FROM supplier.final_containers
UNION ALL SELECT 'child_item_products', COUNT(*) FROM supplier.child_item_products;

-- 5) Component master (source-of-truth, EAV) ----------------------------------
SELECT 'components_sot_skus' t, COUNT(*) n FROM public.components_sot_skus
UNION ALL SELECT 'components_sot_attributes', COUNT(*) FROM public.components_sot_attributes
UNION ALL SELECT 'components_sot_attribute_values', COUNT(*) FROM public.components_sot_attribute_values;

-- Attribute keys available on the component master
SELECT id, key, label, sort_order FROM public.components_sot_attributes ORDER BY sort_order, id;

-- 6) Combo SKU presence (combo = sku containing '+') --------------------------
SELECT 'inv_final_stock combos'  t, COUNT(DISTINCT sku) n FROM public.inv_final_stock  WHERE sku LIKE '%+%'
UNION ALL SELECT 'listing_data combos', COUNT(DISTINCT sku) FROM public.listing_data WHERE sku LIKE '%+%' AND wrong_sku=0
UNION ALL SELECT 'order_transaction combos', COUNT(DISTINCT sku) FROM public.order_transaction WHERE sku LIKE '%+%';

-- 7) Component -> Combo relationship (split '+' and match component master) ----
WITH parts AS (
  SELECT DISTINCT TRIM(unnest(string_to_array(sku,'+'))) AS part_sku
  FROM public.order_transaction WHERE sku LIKE '%+%'
)
SELECT
  (SELECT COUNT(*) FROM parts) AS distinct_combo_parts,
  (SELECT COUNT(*) FROM parts p WHERE EXISTS (SELECT 1 FROM public.components_sot_skus c WHERE c.sku=p.part_sku)) AS parts_matching_master,
  (SELECT COUNT(DISTINCT sku) FROM public.components_sot_skus) AS total_component_skus;

-- 8) Marketplace listing status (listed vs not) + channels --------------------
SELECT
  (SELECT COUNT(DISTINCT c.sku) FROM public.components_sot_skus c
     WHERE EXISTS (SELECT 1 FROM public.listing_data l WHERE l.wrong_sku=0 AND (l.sku=c.sku OR l.mapped_sku=c.sku))) AS components_listed,
  (SELECT COUNT(DISTINCT c.sku) FROM public.components_sot_skus c
     WHERE NOT EXISTS (SELECT 1 FROM public.listing_data l WHERE l.wrong_sku=0 AND (l.sku=c.sku OR l.mapped_sku=c.sku))) AS components_not_listed,
  (SELECT COUNT(DISTINCT which_channel_name) FROM public.listing_data) AS distinct_channels;

-- 9) Fact-table row counts + recency -----------------------------------------
SELECT 'order_transaction' t, COUNT(*) n, MAX(order_date)::text recency FROM public.order_transaction
UNION ALL SELECT 'listing_data', COUNT(*), MAX(row_update)::text FROM public.listing_data
UNION ALL SELECT 'traffic_data', COUNT(*), MAX(date)::text FROM public.traffic_data
UNION ALL SELECT 'ppc_performance', COUNT(*), MAX(date)::text FROM public.ppc_performance
UNION ALL SELECT 'amazon_returns', COUNT(*), MAX(request_date)::text FROM public.amazon_returns
UNION ALL SELECT 'ebay_returns', COUNT(*), NULL FROM public.ebay_returns
UNION ALL SELECT 'shopify_returns', COUNT(*), NULL FROM public.shopify_returns
UNION ALL SELECT 'return_by_cs_team', COUNT(*), NULL FROM public.return_by_cs_team;

-- 10) Warehouse Receive Date = NOT FOUND — authoritative gap register ---------
SELECT gap_id, status, severity, issue_title, required_owner, validator
FROM staging_ai.purchasing_intelligence_source_gaps
WHERE gap_id = 'GAP-PURCH-CBM-2026-06-09-01';
