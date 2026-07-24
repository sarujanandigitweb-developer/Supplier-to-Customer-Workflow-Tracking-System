-- 01_components.sql — NEW components received in the window, with supplier,
-- container, quantity received (order_items.pcs) and receive date.
-- Grain: one row per new component SKU (its earliest receipt = the container it
-- arrived in). Feeds component_meta.psv (supplier/container/qty/desc/arrival).
--
-- BUG THIS FIXES (Container Arrival "04-Aug-2026"):
--   The old column  COALESCE(expected_completion_date, finished_date,
--   confirmed_date) AS container_arrival  exposed a FORECAST
--   (expected_completion_date reaches 2026-08-31) as if it were a real arrival.
--   There is NO actual container-arrival date column in supplier.containers or
--   supplier.orders. So we DO NOT emit a fake arrival date. Instead we expose:
--     status_arrived            -> Arrived (1) / In Transit (0)  [the real flag]
--     expected_completion_date  -> a clearly-labelled FORECAST only (Notes)
WITH nc AS (
  SELECT sku FROM supplier.order_items
  WHERE sku <> '' GROUP BY sku HAVING MIN(created_at) >= DATE '2026-01-01'
)
SELECT DISTINCT ON (oi.sku)
  oi.sku                                                       AS component_sku,
  NULLIF(oi.english_description,'')                            AS description,
  s.name                                                       AS supplier,
  COALESCE(c.name, NULLIF(o.container_id,''))                  AS container,
  oi.pcs                                                       AS qty_received,
  oi.created_at::date::text                                   AS received_date,
  o.order_id                                                   AS po,
  o.status_arrived                                             AS arrived,            -- 1=Arrived, 0=In Transit
  o.expected_completion_date::text                            AS expected_forecast   -- FORECAST only, never "arrival"
FROM nc
JOIN supplier.order_items oi ON oi.sku = nc.sku
JOIN supplier.orders      o  ON o.id  = oi.order_id
LEFT JOIN supplier.suppliers  s ON s.id = o.supplier_id
LEFT JOIN supplier.containers c ON c.id::text = o.container_id
ORDER BY oi.sku, oi.created_at ASC;
