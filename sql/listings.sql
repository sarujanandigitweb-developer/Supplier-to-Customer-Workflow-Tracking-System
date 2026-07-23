-- =============================================================================
-- listings.sql  —  RAW export: Marketplace listings for qualifying combos
-- =============================================================================
-- Purpose      : Every marketplace listing row for the qualifying combo SKUs.
--                Drives Marketplace Status: Listed / Non-Listed, Listing Date,
--                Marketplace, Wrong SKU, Ended.
-- Source tables: public.listing_data l  (+ lineage CTEs on supplier.order_items,
--                public.order_transaction to build the qualifying set)
-- Join logic   : l.sku IN (qualifying combos)  (combo present as a listing SKU)
-- Filters      : new component first-seen >= :start_date ('2026-01-01') ;
--                l.created_at >= :start_date ; wrong_sku 0 AND 1 both kept so the
--                Wrong-SKU flag can be shown ; is_child = 1 (sellable variant).
-- Output       : ref_id, sku, mapped_sku, channel, market_place, status,
--                is_deleted, is_ended, wrong_sku, listing_date, price, currency
-- Grain        : one row per listing (ref_id + channel + marketplace + sku).
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
  l.ref_id,
  l.sku,
  NULLIF(l.mapped_sku,'')                 AS mapped_sku,
  l.which_channel_name                    AS channel,
  l.market_place,
  l.status,
  COALESCE(l.is_deleted,0)::int           AS is_deleted,
  COALESCE(l.is_ended,0)::int             AS is_ended,
  l.wrong_sku::int                        AS wrong_sku,
  l.created_at::date                      AS listing_date,
  l.price,
  l.currency
FROM public.listing_data l
WHERE l.sku IN (SELECT sku FROM qc)
  AND l.created_at >= '2026-01-01'        -- :start_date
  AND l.is_child = 1
ORDER BY l.created_at DESC, l.ref_id;
