-- =============================================================================
-- component_combo_mapping.sql  —  RAW export: Component -> Combo mapping
-- =============================================================================
-- Purpose      : One row per (NEW component, Combo SKU) pair. Lets the dashboard
--                derive, in JS, which combos belong to which new components and
--                recompute the qualifying-combo set for any sub-period.
-- Source tables: supplier.order_items          (new components)
--                public.listing_data           (combo SKUs, channel-listed)
--                public.order_transaction       (combo SKUs seen in sales)
-- Join logic   : split each combo SKU on '+' -> component parts ;
--                keep parts that are NEW components (first-seen in window).
-- Filters      : new component MIN(created_at) >= :start_date ('2026-01-01') ;
--                combo contains '+' ; listing_data.wrong_sku = 0.
-- Output       : component_sku, combo_sku
-- Grain        : one row per (component_sku, combo_sku) pair.
-- =============================================================================
WITH nc AS (
  SELECT sku FROM supplier.order_items
  WHERE sku <> ''
  GROUP BY sku
  HAVING MIN(created_at) >= '2026-01-01'         -- :start_date
),
combo_universe AS (
  SELECT DISTINCT sku FROM public.listing_data     WHERE wrong_sku = 0 AND sku LIKE '%+%'
  UNION
  SELECT DISTINCT sku FROM public.order_transaction WHERE sku LIKE '%+%'
),
parts AS (
  SELECT c.sku AS combo_sku, TRIM(x) AS component_sku
  FROM combo_universe c
  CROSS JOIN LATERAL unnest(string_to_array(c.sku, '+')) AS x
)
SELECT DISTINCT p.component_sku, p.combo_sku
FROM parts p
JOIN nc ON nc.sku = p.component_sku
ORDER BY p.component_sku, p.combo_sku;
