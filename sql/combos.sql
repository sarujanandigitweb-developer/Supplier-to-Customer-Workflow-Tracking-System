-- =============================================================================
-- combos.sql  —  RAW export: Combo SKUs created from new components
-- =============================================================================
-- Purpose      : One row per QUALIFYING combo SKU (a combo that contains at least
--                one NEW component). Carries the combo's first-listed date and part
--                count so the dashboard can build the Combo Creation view and the
--                Listed/Non-Listed split (listed flag derived from listings.sql).
-- Source tables: supplier.order_items       (new components)
--                public.listing_data        (combo listing + created_at)
--                public.order_transaction    (combo universe from sales)
-- Join logic   : qualifying = combo whose '+'-split parts intersect new components.
--                first_listed = MIN(listing_data.created_at) for that combo.
-- Filters      : new component MIN(created_at) >= :start_date ('2026-01-01') ;
--                sku LIKE '%+%' ; wrong_sku = 0.
-- Output       : combo_sku, part_count, first_listed, is_listed
-- Grain        : one row per qualifying combo SKU.
-- =============================================================================
WITH nc AS (
  SELECT sku FROM supplier.order_items
  WHERE sku <> '' GROUP BY sku HAVING MIN(created_at) >= '2026-01-01'   -- :start_date
),
combo_universe AS (
  SELECT DISTINCT sku FROM public.listing_data     WHERE wrong_sku = 0 AND sku LIKE '%+%'
  UNION
  SELECT DISTINCT sku FROM public.order_transaction WHERE sku LIKE '%+%'
),
qc AS (
  SELECT DISTINCT c.sku
  FROM combo_universe c
  CROSS JOIN LATERAL (SELECT TRIM(x) AS part FROM unnest(string_to_array(c.sku,'+')) x) p
  WHERE p.part IN (SELECT sku FROM nc)
)
SELECT
  qc.sku                                                   AS combo_sku,
  array_length(string_to_array(qc.sku,'+'),1)             AS part_count,
  (SELECT MIN(l.created_at)::date FROM public.listing_data l
     WHERE l.sku = qc.sku AND l.wrong_sku = 0)             AS first_listed,
  CASE WHEN EXISTS (SELECT 1 FROM public.listing_data l
                     WHERE l.sku = qc.sku AND l.wrong_sku = 0)
       THEN 1 ELSE 0 END                                   AS is_listed
FROM qc
ORDER BY qc.sku;
