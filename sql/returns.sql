-- =============================================================================
-- returns.sql  —  RAW export: Returns for qualifying combos (Amazon/eBay/Shopify)
-- =============================================================================
-- Purpose      : Every return that belongs to a qualifying combo SKU, across all
--                three channels, in one dataset. Drives the Returns page + KPI.
-- Source tables: public.amazon_returns   (sku, qty, reason, refunded_amount)
--                public.ebay_returns     (return_qty, reason, buyer_refund_amount;
--                                         NO sku -> bridge via order_id; the table
--                                         logs ~9 ACTIVITY rows per return, so it
--                                         MUST be collapsed to one row per return_id)
--                public.shopify_returns  (refund_amount only — NO qty/reason/sku;
--                                         qty derived from the order line, refund
--                                         from refund_amount, bridge via order_id)
--                public.order_transaction (order_id -> combo sku + ordered qty)
-- Join logic   : Amazon : ar.sku IN (qualifying combos).
--                eBay   : er.order_id = ot.order_id AND ot.sku IN combos ;
--                         GROUP BY return_id (MAX qty, non-null reason, MAX refund).
--                         **Do NOT group by reason/date** — that splits one return
--                         into many rows (the original defect: 47 real returns
--                         appeared as ~268).
--                Shopify: sr.order_id = ot.order_id ; qty = order-line quantity ;
--                         DISTINCT ON (sr.id) so one row per refund record.
-- Filters      : new component first-seen >= :start_date ; request/date >= :start_date.
-- Output       : channel, order_id, sku, request_date, reason, qty, refund
-- Grain        : Amazon = per return line ; eBay = per return_id ; Shopify = per refund.
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
combo_orders AS (   -- order_id -> combo sku + ordered quantity (for eBay/Shopify bridge)
  SELECT order_id, sku, SUM(quantity)::int AS oqty
  FROM public.order_transaction WHERE sku IN (SELECT sku FROM qc) GROUP BY order_id, sku
)
-- AMAZON (sku, qty, reason, refund present)
SELECT 'amazon'::text AS channel, ar.order_id, ar.sku, ar.request_date::date AS request_date,
       ar.reason, ar.qty::int AS qty, ROUND(ar.refunded_amount::numeric,2) AS refund
FROM public.amazon_returns ar
WHERE ar.sku IN (SELECT sku FROM qc) AND ar.request_date >= '2026-01-01'   -- :start_date
UNION ALL
-- EBAY (one row per return_id)
SELECT 'ebay', eb.order_id, eb.sku, eb.rdate, eb.reason, eb.qty, eb.refund FROM (
  SELECT er.return_id, MIN(er.order_id) AS order_id, MIN(co.sku) AS sku, MIN(er.request_date::date) AS rdate,
         MAX(er.reason) FILTER (WHERE er.reason IS NOT NULL AND er.reason<>'') AS reason,
         MAX(er.return_qty)::int AS qty, ROUND(MAX(er.buyer_refund_amount)::numeric,2) AS refund
  FROM public.ebay_returns er JOIN combo_orders co ON co.order_id = er.order_id
  WHERE er.request_date >= '2026-01-01'                                     -- :start_date
  GROUP BY er.return_id) eb
UNION ALL
-- SHOPIFY (refund event; qty from order line; no reason at source)
SELECT 'shopify', s.order_id, s.sku, s.sdate, NULL::text, s.oqty, s.refund FROM (
  SELECT DISTINCT ON (sr.id) sr.id, sr.order_id, co.sku, sr.date::date AS sdate, co.oqty,
         ROUND(sr.refund_amount::numeric,2) AS refund
  FROM public.shopify_returns sr JOIN combo_orders co ON co.order_id = sr.order_id
  WHERE sr.date >= '2026-01-01'                                            -- :start_date
  ORDER BY sr.id, co.oqty DESC) s
ORDER BY channel, request_date DESC;
