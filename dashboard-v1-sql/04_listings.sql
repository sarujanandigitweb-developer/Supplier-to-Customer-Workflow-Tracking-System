-- 04_listings.sql — active listings aggregated per (combo, platform).
-- A row means the combo has a live (not deleted / not ended) listing on that
-- platform. Grain: one row per (combo_sku, platform).
WITH nc AS (
  SELECT sku FROM supplier.order_items
  WHERE sku <> '' GROUP BY sku HAVING MIN(created_at) >= DATE '2026-01-01'),
universe AS (
  SELECT DISTINCT sku FROM public.listing_data      WHERE wrong_sku=0 AND sku LIKE '%+%'
  UNION SELECT DISTINCT sku FROM public.order_transaction WHERE sku LIKE '%+%'),
qc AS (
  SELECT DISTINCT u.sku FROM universe u
  CROSS JOIN LATERAL (SELECT trim(x) AS part FROM unnest(string_to_array(u.sku,'+')) x) p
  WHERE p.part IN (SELECT sku FROM nc))
SELECT sku AS combo_sku,
       CASE WHEN lower(which_channel_name) LIKE '%amazon%'  THEN 'amazon'
            WHEN lower(which_channel_name) LIKE '%ebay%'    THEN 'ebay'
            WHEN lower(which_channel_name) LIKE '%shopify%' THEN 'shopify'
            ELSE lower(which_channel_name) END               AS platform,
       MIN(created_at)::date::text                           AS listing_date,
       (array_agg(ref_id ORDER BY created_at))[1]            AS listing_ref,
       count(DISTINCT market_place)                          AS regions
FROM public.listing_data
WHERE sku IN (SELECT sku FROM qc) AND wrong_sku=0 AND is_deleted=0 AND is_ended=0
GROUP BY 1,2 ORDER BY 1,2;
