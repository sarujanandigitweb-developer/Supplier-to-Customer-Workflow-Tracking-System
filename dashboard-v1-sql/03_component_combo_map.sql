-- 03_component_combo_map.sql — mapping of NEW component → qualifying combo.
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
SELECT DISTINCT p.part AS component_sku, q.sku AS combo_sku
FROM qc q CROSS JOIN LATERAL (SELECT trim(x) AS part FROM unnest(string_to_array(q.sku,'+')) x) p
WHERE p.part IN (SELECT sku FROM nc)
ORDER BY 1,2;
