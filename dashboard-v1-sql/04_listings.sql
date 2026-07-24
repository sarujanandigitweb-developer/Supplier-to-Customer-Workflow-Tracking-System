-- =============================================================================
-- 04_listings.sql  —  THE DRIVER of the master tracking table.
-- =============================================================================
-- BUSINESS RULE (manager, 2026-07-24):
--   "Fetch ONLY the products whose Listing Date (created_at in listing_data) is
--    from 2026-01-01 up to the present. Display all details for those only."
--   => Every master-table row MUST have a real Listing Date >= 2026-01-01.
--      Products with NO in-window listing are EXCLUDED (no more 'Not Listed'
--      rows that had orders but no listing date).
--
-- BUG THIS FIXES: the previous version (below) had NO date filter —
--     WHERE sku IN (qc) AND wrong_sku=0 AND is_deleted=0 AND is_ended=0
--   so it returned listings created as far back as 2019-06-26 and showed their
--   old created_at as "Listing Date". 86% of rows were out-of-window.
--
-- Listing Date = public.listing_data.created_at  (there is NO separate
--                'created_date' column — created_at IS the listing creation
--                timestamp, verified via information_schema).
-- Row grain    = one (combo_sku, platform); Listing Date = EARLIEST in-window
--                created_at for that combo on that platform; that same row's
--                ref_id / listing_url / main_image_url are carried so the URL
--                and image always match the date shown.
-- Filters      = created_at >= 2026-01-01  (THE listing-date filter)
--                AND is_child = 1  AND wrong_sku = 0.
-- Lineage      = sku IN qc (qualifying combos: contain >=1 new component).
-- Source       = public.listing_data.
-- =============================================================================
WITH nc AS (
  SELECT sku FROM supplier.order_items
  WHERE sku <> '' GROUP BY sku HAVING MIN(created_at) >= DATE '2026-01-01'
),
universe AS (
  SELECT DISTINCT sku FROM public.listing_data      WHERE wrong_sku=0 AND sku LIKE '%+%'
  UNION SELECT DISTINCT sku FROM public.order_transaction WHERE sku LIKE '%+%'
),
qc AS (
  SELECT DISTINCT u.sku FROM universe u
  CROSS JOIN LATERAL (SELECT trim(x) AS part FROM unnest(string_to_array(u.sku,'+')) x) p
  WHERE p.part IN (SELECT sku FROM nc)
),
plat AS (   -- normalise channel -> platform key once
  SELECT sku, created_at, ref_id, listing_url, main_image_url, title, market_place,
         CASE WHEN lower(which_channel_name) LIKE '%amazon%'  THEN 'amazon'
              WHEN lower(which_channel_name) LIKE '%ebay%'    THEN 'ebay'
              WHEN lower(which_channel_name) LIKE '%shopify%' THEN 'shopify'
              WHEN lower(which_channel_name) LIKE '%b&q%'     THEN 'b&q'
              WHEN lower(which_channel_name) LIKE '%wayfair%' THEN 'wayfair'
              ELSE 'other' END AS platform
  FROM public.listing_data
  WHERE sku IN (SELECT sku FROM qc)
    AND created_at >= DATE '2026-01-01'   -- :start_date  <<< THE listing-date filter
    AND is_child = 1
    AND wrong_sku = 0
),
lw AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY sku, platform
                               ORDER BY created_at ASC, ref_id) AS rn
  FROM plat
)
SELECT sku AS combo_sku,
       platform,
       MIN(created_at)::date::text                      AS listing_date,   -- >= 2026-01-01
       MAX(ref_id)         FILTER (WHERE rn=1)           AS listing_ref,
       MAX(listing_url)    FILTER (WHERE rn=1)           AS listing_url,    -- real clickable URL
       MAX(main_image_url) FILTER (WHERE rn=1)           AS image_url,      -- real product image
       MAX(title)          FILTER (WHERE rn=1)           AS product_name,
       COUNT(DISTINCT market_place)                      AS regions
FROM lw
GROUP BY sku, platform
ORDER BY sku, platform;
