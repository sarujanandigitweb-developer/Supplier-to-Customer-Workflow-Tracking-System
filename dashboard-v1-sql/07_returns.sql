-- 07_returns.sql — returned units per (combo, platform), across the 3 return
-- systems. eBay/Shopify key by order_id → resolved to a combo via order_transaction.
-- eBay deduped per return_id; Shopify has no qty column, so 1 unit per return.
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
co AS (
  SELECT order_id, MAX(sku) AS combo FROM public.order_transaction
  WHERE sku IN (SELECT sku FROM qc) GROUP BY order_id),
amz AS (
  SELECT sku AS combo, 'amazon'::text AS platform, SUM(qty)::int AS ret
  FROM public.amazon_returns
  WHERE sku IN (SELECT sku FROM qc) AND request_date >= DATE '2026-01-01' GROUP BY sku),
eb AS (
  SELECT co.combo, 'ebay'::text AS platform, SUM(x.qty)::int AS ret FROM (
    SELECT return_id, MAX(order_id) AS order_id, MAX(return_qty) AS qty
    FROM public.ebay_returns WHERE request_date >= DATE '2026-01-01' GROUP BY return_id) x
  JOIN co ON co.order_id = x.order_id GROUP BY co.combo),
sh AS (
  SELECT co.combo, 'shopify'::text AS platform, count(*)::int AS ret
  FROM public.shopify_returns sr JOIN co ON co.order_id = sr.order_id
  WHERE sr.date >= DATE '2026-01-01' GROUP BY co.combo)
SELECT combo AS combo_sku, platform, ret AS returns
FROM (SELECT * FROM amz UNION ALL SELECT * FROM eb UNION ALL SELECT * FROM sh) z
WHERE combo IS NOT NULL ORDER BY 1,2;
