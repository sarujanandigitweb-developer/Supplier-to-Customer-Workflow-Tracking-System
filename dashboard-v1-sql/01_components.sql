-- 01_components.sql — NEW components received in the window, with supplier,
-- container, quantity received (order_items.pcs) and receive date.
-- Grain: one row per new component SKU (its earliest receipt = the container it
-- arrived in). Fills the gaps the modified data.js had (real qty/container/supplier).
WITH nc AS (
  SELECT sku FROM supplier.order_items
  WHERE sku <> '' GROUP BY sku HAVING MIN(created_at) >= DATE '2026-01-01'
)
SELECT DISTINCT ON (oi.sku)
  oi.sku                                                       AS component_sku,
  NULLIF(oi.english_description,'')                            AS description,
  s.name                                                       AS supplier,
  COALESCE(c.name, NULLIF(o.container_id,''))                  AS container,
  COALESCE(o.expected_completion_date, o.finished_date, o.confirmed_date)::text AS container_arrival,
  oi.pcs                                                       AS qty_received,
  oi.created_at::date::text                                   AS received_date,
  o.order_id                                                   AS po,
  o.status_arrived                                             AS arrived
FROM nc
JOIN supplier.order_items oi ON oi.sku = nc.sku
JOIN supplier.orders      o  ON o.id  = oi.order_id
LEFT JOIN supplier.suppliers  s ON s.id = o.supplier_id
LEFT JOIN supplier.containers c ON c.id::text = o.container_id
ORDER BY oi.sku, oi.created_at ASC;
