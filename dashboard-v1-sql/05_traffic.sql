-- 05_traffic.sql — impressions/clicks per (combo, platform), organic + paid.
-- refmap dedups to ONE row per ref_id (no join fan-out); the window is applied
-- on the TRAFFIC date, not on the listing date. Grain: one row per (combo, platform).
WITH nc AS (
  SELECT sku FROM supplier.order_items
  WHERE sku <> '' GROUP BY sku HAVING MIN(created_at) >= DATE '2026-01-01'),
universe AS (
  SELECT DISTINCT sku FROM public.listing_data      WHERE wrong_sku=0 AND sku LIKE '%+%'
  UNION SELECT DISTINCT sku FROM public.order_transaction WHERE sku LIKE '%+%'),
qc AS (
  SELECT DISTINCT u.sku FROM universe u
  CROSS JOIN LATERAL (SELECT trim(x) AS part FROM unnest(string_to_array(u.sku,'+')) x) p
  WHERE p.part IN (SELECT sku FROM nc)),
refmap AS (
  SELECT ref_id, MAX(sku) AS combo,
         MAX(CASE WHEN lower(which_channel_name) LIKE '%amazon%'  THEN 'amazon'
                  WHEN lower(which_channel_name) LIKE '%ebay%'    THEN 'ebay'
                  WHEN lower(which_channel_name) LIKE '%shopify%' THEN 'shopify'
                  ELSE lower(which_channel_name) END) AS platform
  FROM public.listing_data
  WHERE wrong_sku=0 AND sku IN (SELECT sku FROM qc)
  GROUP BY ref_id),
t AS (
  SELECT ref_id, COALESCE(impression,0) AS imp, COALESCE(click,0) AS clk
  FROM public.traffic_data   WHERE date >= DATE '2026-01-01'
  UNION ALL
  SELECT ref_id, COALESCE(impressions,0), COALESCE(clicks,0)
  FROM public.ppc_performance WHERE date >= DATE '2026-01-01')
SELECT rm.combo AS combo_sku, rm.platform,
       SUM(t.imp)::bigint AS impressions, SUM(t.clk)::bigint AS clicks
FROM t JOIN refmap rm ON rm.ref_id = t.ref_id
GROUP BY 1,2 ORDER BY 1,2;
