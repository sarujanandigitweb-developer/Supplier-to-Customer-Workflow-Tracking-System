-- 02_combos.sql — Qualifying combos with product name (listing title), creation
-- date (earliest system appearance) and current listed flag.
-- Grain: one row per combo SKU.
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
meta AS (
  SELECT sku, MAX(NULLIF(title,'')) AS name, MIN(created_at)::date AS first_listed,
         bool_or(is_deleted=0 AND is_ended=0) AS has_live
  FROM public.listing_data WHERE wrong_sku=0 AND sku LIKE '%+%' GROUP BY sku),
firstorder AS (
  SELECT sku, MIN(order_date)::date AS d FROM public.order_transaction WHERE sku LIKE '%+%' GROUP BY sku)
SELECT q.sku                                              AS combo_sku,
       array_length(string_to_array(q.sku,'+'),1)        AS part_count,
       m.name                                            AS combo_name,
       LEAST(m.first_listed, fo.d)::text                 AS combo_created,
       CASE WHEN COALESCE(m.has_live,false) THEN 1 ELSE 0 END AS is_listed
FROM qc q
LEFT JOIN meta m       ON m.sku  = q.sku
LEFT JOIN firstorder fo ON fo.sku = q.sku
ORDER BY q.sku;
