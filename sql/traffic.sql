-- =============================================================================
-- traffic.sql  —  Traffic (Impressions / Clicks / CTR) for qualifying combos
-- =============================================================================
-- Purpose      : Impressions/Clicks per listing for the qualifying combos, from
--                traffic_data (organic) + ppc_performance (paid), reconnected to
--                combos THROUGH listing_data (traffic tables carry ref_id, not SKU).
-- FIXED (2026-07-23):
--   DOUBLE-COUNT BUG: the old `refids` CTE was DISTINCT (ref_id, channel,
--   market_place) but joined on ref_id ONLY, so a ref_id listed in >1
--   marketplace fanned out and its impressions were summed multiple times
--   (measured ~+5% inflation: 127.1M vs true 120.8M organic impressions).
--   -> refids is now ONE ROW PER ref_id (GROUP BY ref_id), so no fan-out.
--   Verified organic total after fix = 120.77M impressions.
-- DO NOT gate `refids` on listing created_at or is_child: a qualifying combo
--   listed BEFORE the window still earns in-window impressions. The reporting
--   window is applied on the TRAFFIC date (td.date / pp.date), not on when the
--   listing was created. (An earlier revision added created_at >= :start here and
--   wrongly dropped 6,394 of 7,630 ref_ids, collapsing organic to 6.96M.)
-- Source tables: public.traffic_data, public.ppc_performance, public.listing_data
-- Output       : source ('organic'|'paid'), ref_id, channel, market_place,
--                impressions, clicks   (one row per source+ref_id+market_place)
-- =============================================================================
WITH nc AS (
  SELECT sku FROM supplier.order_items
  WHERE sku <> '' GROUP BY sku HAVING MIN(created_at) >= '2026-01-01'   -- :start_date
),
combo_universe AS (
  SELECT DISTINCT sku FROM public.listing_data     WHERE wrong_sku = 0 AND sku LIKE '%+%'
  UNION SELECT DISTINCT sku FROM public.order_transaction WHERE sku LIKE '%+%'
),
qc AS (
  SELECT DISTINCT c.sku FROM combo_universe c
  CROSS JOIN LATERAL (SELECT TRIM(x) AS part FROM unnest(string_to_array(c.sku,'+')) x) p
  WHERE p.part IN (SELECT sku FROM nc)
),
refids AS (                              -- ONE row per ref_id -> no join fan-out
  SELECT ref_id, MAX(which_channel_name) AS channel
  FROM public.listing_data
  WHERE wrong_sku = 0 AND sku IN (SELECT sku FROM qc)   -- window applied on traffic date, not listing date
  GROUP BY ref_id
)
SELECT 'organic'::text AS source, td.ref_id, MAX(r.channel) AS channel, td.market_place,
       SUM(COALESCE(td.impression,0))::bigint AS impressions,
       SUM(COALESCE(td.click,0))::bigint       AS clicks
FROM public.traffic_data td JOIN refids r ON r.ref_id = td.ref_id
WHERE td.date >= '2026-01-01'                 -- :start_date
GROUP BY td.ref_id, td.market_place
UNION ALL
SELECT 'paid'::text AS source, pp.ref_id, MAX(r.channel) AS channel, pp.marketplace AS market_place,
       SUM(COALESCE(pp.impressions,0))::bigint AS impressions,
       SUM(COALESCE(pp.clicks,0))::bigint       AS clicks
FROM public.ppc_performance pp JOIN refids r ON r.ref_id = pp.ref_id
WHERE pp.date >= '2026-01-01'                  -- :start_date
GROUP BY pp.ref_id, pp.marketplace;
