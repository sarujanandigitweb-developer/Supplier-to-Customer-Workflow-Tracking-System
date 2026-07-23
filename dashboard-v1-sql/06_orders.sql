-- 06_orders.sql — completed sales per (combo, platform).
-- Grain: one row per (combo_sku, platform). orders = distinct order_ids.
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
       CASE WHEN lower(source_name) LIKE '%amazon%'  THEN 'amazon'
            WHEN lower(source_name) LIKE '%ebay%'    THEN 'ebay'
            WHEN lower(source_name) LIKE '%shopify%' THEN 'shopify'
            WHEN lower(source_name) LIKE '%b&q%'     THEN 'b&q'
            WHEN lower(source_name) LIKE '%wayfair%' THEN 'wayfair'
            ELSE 'other' END                          AS platform,
       count(DISTINCT order_id)                       AS orders,
       SUM(quantity)::int                             AS units,
       ROUND(SUM(order_total)::numeric,2)::float8     AS revenue
FROM public.order_transaction
WHERE sku IN (SELECT sku FROM qc) AND order_status='Completed' AND order_date >= DATE '2026-01-01'
GROUP BY 1,2 ORDER BY 1,2;
