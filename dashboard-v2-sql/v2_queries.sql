-- =====================================================================
-- Supplier's Basket -> Customer's Home — TRACKING SYSTEM V2
-- Full query set. Scope: 2026 onwards only.
-- Live source: order_management_copy @ 149.28.134.54:5435
-- No reuse of V1 SQL, joins, or business logic.
-- =====================================================================
--
-- VERIFIED RELATIONSHIPS (discovered from the live DB, 2026-07-28)
--
--   supplier.order_items.order_id (bigint)        = supplier.orders.id (bigint)
--        !! NOT orders.order_id — that is the human PO text, e.g. 'BBS032026-02'
--   supplier.orders.supplier_id                   = supplier.suppliers.id
--   supplier.order_items.assigned_container_id    = supplier.containers.id
--        (double precision -> ::bigint cast required; 316/4029 are NULL -> LEFT JOIN)
--   supplier.orders.container_id (TEXT)           = supplier.containers.id::text
--        (alternate path; 83 rows disagree with assigned_container_id — we use
--         assigned_container_id because it is per-ITEM, not per-PO)
--   supplier.containers.main_container            = 'UK' | 'GERMAN' | 'US'
--
--   inv_product_combo.product                     = the COMBO's inv_products.id
--   inv_product_combo.inventory                   = the COMPONENT's inv_products.id
--        always filter inventory <> product (excludes self-mapped singles)
--   Component = sku NOT LIKE '%+%'   |   Combo = sku LIKE '%+%'
--
--   listing_data -> product: COALESCE(NULLIF(TRIM(mapped_sku),''),TRIM(sku)),
--        falling back to regexp_replace(...,'[_-][A-Za-z]{2,4}$','')
--        always filter COALESCE(is_parent,0)=0 AND wrong_sku=0 AND TRIM(sku)<>''
--   traffic_data / ppc_performance -> listing_data via ref_id
--   order_transaction -> sku (suffix-stripped), order_status='Completed'
--   amazon_returns -> sku direct.  ebay/shopify_returns -> order_transaction.order_id
--
-- KNOWN DATA LIMITS (documented, not worked around)
--   * NO true receipt/arrival date exists. status_arrived is a date-less 0/1 flag;
--     orders.updated_at is a generic row-edit timestamp that also moves on
--     never-arrived POs. Received Date below is therefore the PO order_date PROXY.
--   * NO reviews/ratings table exists -> Customer Reviews column removed.
--   * Return reason: amazon 100% populated, ebay ~11%, shopify has NO reason column.
-- =====================================================================


-- ---------------------------------------------------------------------
-- Q1. SCOPE STEP 1 — NEW COMPONENTS
--     inv_products created 2026+, not deleted, component (no '+'),
--     AND actually purchased from a supplier.        --> 178 rows
-- ---------------------------------------------------------------------
CREATE TEMP TABLE comp AS
SELECT DISTINCT p.id AS comp_id, p.sku AS comp_sku,
       p.created_at::date::text AS comp_created,
       COALESCE(NULLIF(p.eng_desc,''),NULLIF(p.description,''),NULLIF(p.title,''),'') AS comp_desc
FROM public.inv_products p
JOIN supplier.order_items oi ON oi.sku = p.sku
WHERE p.created_at >= '2026-01-01'
  AND COALESCE(p.isdeleted,0) = 0
  AND COALESCE(TRIM(p.sku),'') <> ''
  AND p.sku NOT LIKE '%+%';


-- ---------------------------------------------------------------------
-- Q2. SUPPLIER / CONTAINER / RECEIVED DATE  (cols 1-3)
--     DISTINCT ON keeps the component's MOST RECENT PO.
--     received_proxy = o.order_date  (see KNOWN DATA LIMITS above)
-- ---------------------------------------------------------------------
CREATE TEMP TABLE sup AS
SELECT DISTINCT ON (oi.sku)
       oi.sku                                            AS comp_sku,
       COALESCE(s.name,'')                               AS supplier,
       COALESCE(ct.name, NULLIF(o.container_id,''), '')  AS container,
       COALESCE(ct.main_container,'')                    AS destination,
       o.order_date::text                                AS received_proxy,
       COALESCE(o.order_id,'')                           AS po,
       COALESCE(oi.pcs,0)                                AS qty,
       COALESCE(o.status_arrived,0)                      AS arrived
FROM supplier.order_items oi
JOIN comp c                      ON c.comp_sku = oi.sku
JOIN supplier.orders     o       ON o.id  = oi.order_id
LEFT JOIN supplier.suppliers  s  ON s.id  = o.supplier_id
LEFT JOIN supplier.containers ct ON ct.id = oi.assigned_container_id::bigint
ORDER BY oi.sku, o.order_date DESC NULLS LAST, o.id DESC;

-- PO count per component (56% of components are restocked more than once)
SELECT oi.sku, count(*) AS po_count
FROM supplier.order_items oi JOIN comp c ON c.comp_sku = oi.sku
GROUP BY 1;


-- ---------------------------------------------------------------------
-- Q3. SCOPE STEP 2 — COMBOS built from those new components (cols 7-9)
--     --> 223 distinct combos, 261 component x combo pairs
-- ---------------------------------------------------------------------
CREATE TEMP TABLE pair AS
SELECT c.comp_sku, c.comp_created, c.comp_desc,
       cp.id  AS combo_id,
       cp.sku AS combo_sku,
       cp.created_at::date::text AS combo_created,
       pc.pack_count
FROM comp c
JOIN public.inv_product_combo pc ON pc.inventory = c.comp_id
                                AND pc.inventory <> pc.product
JOIN public.inv_products cp      ON cp.id = pc.product
WHERE cp.created_at >= '2026-01-01'
  AND COALESCE(cp.isdeleted,0) = 0
  AND COALESCE(TRIM(cp.sku),'') <> '';


-- ---------------------------------------------------------------------
-- Q4. LISTINGS for the combo SKUs (cols 10-12)
--     Listed Date = MIN(created_at) per (sku, platform)
-- ---------------------------------------------------------------------
CREATE TEMP TABLE lst AS
SELECT COALESCE(a.sku,b.sku) AS sku, ld.ref_id,
       CASE WHEN lower(ld.which_channel_name) LIKE '%amazon%'  THEN 'amazon'
            WHEN lower(ld.which_channel_name) LIKE '%ebay%'    THEN 'ebay'
            WHEN lower(ld.which_channel_name) LIKE '%shopify%' THEN 'shopify'
            WHEN lower(ld.which_channel_name) LIKE '%b&q%'     THEN 'b&q'
            WHEN lower(ld.which_channel_name) LIKE '%wayfair%' THEN 'wayfair'
            ELSE 'other' END AS platform,
       ld.created_at::date AS listed_on,
       ld.listing_url, ld.main_image_url, ld.market_place
FROM public.listing_data ld
LEFT JOIN public.inv_products a
       ON a.sku = COALESCE(NULLIF(TRIM(ld.mapped_sku),''),TRIM(ld.sku))
LEFT JOIN public.inv_products b
       ON b.sku = regexp_replace(COALESCE(NULLIF(TRIM(ld.mapped_sku),''),TRIM(ld.sku)),
                                 '[_-][A-Za-z]{2,4}$','')
WHERE COALESCE(ld.is_parent,0) = 0
  AND ld.wrong_sku = 0
  AND COALESCE(TRIM(ld.sku),'') <> ''
  AND COALESCE(a.sku,b.sku) IN (SELECT combo_sku FROM pair);

SELECT sku, platform,
       MIN(listed_on)::text                                        AS listed_date,
       (array_agg(listing_url ORDER BY listed_on, ref_id))[1]       AS listing_url,
       (array_agg(market_place ORDER BY listed_on, ref_id))[1]      AS marketplace
FROM lst GROUP BY sku, platform;


-- ---------------------------------------------------------------------
-- Q5. IMAGES (cols 5, 8) — newest listing image per SKU, components AND combos
-- ---------------------------------------------------------------------
SELECT DISTINCT ON (resolved) resolved AS sku, main_image_url
FROM (
  SELECT COALESCE(NULLIF(TRIM(mapped_sku),''),TRIM(sku)) AS resolved,
         main_image_url, created_at, ref_id
  FROM public.listing_data
  WHERE COALESCE(main_image_url,'') <> ''
    AND COALESCE(NULLIF(TRIM(mapped_sku),''),TRIM(sku)) IN (
        SELECT comp_sku FROM comp UNION SELECT combo_sku FROM pair)) z
ORDER BY resolved, created_at DESC, ref_id;


-- ---------------------------------------------------------------------
-- Q6. TRAFFIC (cols 13-14)
--     *** Counted from each listing's OWN Listed Date to today, NOT from
--         2026-01-01 — this is the V2 traffic rule. ***
-- ---------------------------------------------------------------------
SELECT l.sku, l.platform,
       SUM(t.i)::bigint AS impressions,
       SUM(t.c)::bigint AS clicks
FROM lst l
JOIN (
  SELECT ref_id, date, COALESCE(impression,0)  AS i, COALESCE(click,0)  AS c
  FROM public.traffic_data
  UNION ALL
  SELECT ref_id, date, COALESCE(impressions,0), COALESCE(clicks,0)
  FROM public.ppc_performance
) t ON t.ref_id = l.ref_id
   AND t.date  >= l.listed_on            -- <== Listed Date -> today
GROUP BY 1,2;


-- ---------------------------------------------------------------------
-- Q7. ORDERS / UNITS / REVENUE (cols 15-17) for the combo SKUs
-- ---------------------------------------------------------------------
SELECT base_sku AS sku, platform,
       count(DISTINCT order_id)                    AS orders,
       SUM(quantity)::int                          AS units_sold,
       ROUND(SUM(order_total)::numeric,2)::float8  AS revenue
FROM (
  SELECT regexp_replace(TRIM(ot.sku),'[_-][A-Za-z]{2,4}$','') AS base_sku,
         CASE WHEN lower(ot.source_name) LIKE '%amazon%'  THEN 'amazon'
              WHEN lower(ot.source_name) LIKE '%ebay%'    THEN 'ebay'
              WHEN lower(ot.source_name) LIKE '%shopify%' THEN 'shopify'
              WHEN lower(ot.source_name) LIKE '%b&q%'     THEN 'b&q'
              WHEN lower(ot.source_name) LIKE '%wayfair%' THEN 'wayfair'
              ELSE 'other' END AS platform,
         ot.order_id, ot.quantity, ot.order_total
  FROM public.order_transaction ot
  WHERE ot.order_status = 'Completed'
    AND regexp_replace(TRIM(ot.sku),'[_-][A-Za-z]{2,4}$','')
        IN (SELECT combo_sku FROM pair)
) o
GROUP BY 1,2;


-- ---------------------------------------------------------------------
-- Q8. RETURNS (cols 18-20) — Total Returns, Return Rate %, Top Reason
--     3-way union. amazon = sku direct + reason.
--                  ebay   = via order_transaction + reason.
--                  shopify= via order_transaction, NO reason column exists.
-- ---------------------------------------------------------------------
CREATE TEMP TABLE ret AS
WITH co AS (
  SELECT ot.order_id,
         regexp_replace(TRIM(ot.sku),'[_-][A-Za-z]{2,4}$','') AS base_sku,
         SUM(ot.quantity)::int AS oqty
  FROM public.order_transaction ot GROUP BY 1,2)
SELECT regexp_replace(TRIM(ar.sku),'[_-][A-Za-z]{2,4}$','') AS sku,
       'amazon'::text AS platform, ar.qty::int AS qty,
       NULLIF(TRIM(ar.reason),'') AS reason
FROM public.amazon_returns ar
WHERE regexp_replace(TRIM(ar.sku),'[_-][A-Za-z]{2,4}$','') IN (SELECT combo_sku FROM pair)
UNION ALL
SELECT co.base_sku, 'ebay', e.qty, e.reason
FROM (SELECT return_id, MIN(order_id) AS order_id, MAX(return_qty)::int AS qty,
             NULLIF(TRIM(MAX(reason)),'') AS reason
      FROM public.ebay_returns GROUP BY return_id) e
JOIN co ON co.order_id = e.order_id
WHERE co.base_sku IN (SELECT combo_sku FROM pair)
UNION ALL
SELECT co.base_sku, 'shopify', co.oqty, NULL
FROM (SELECT DISTINCT ON (id) id, order_id FROM public.shopify_returns ORDER BY id) sh
JOIN co ON co.order_id = sh.order_id
WHERE co.base_sku IN (SELECT combo_sku FROM pair);

-- Total Returns per (sku, platform)
SELECT sku, platform, SUM(COALESCE(qty,0))::int AS total_returns
FROM ret GROUP BY 1,2;

-- Top Reason per (sku, platform) — most frequent, ties broken alphabetically
SELECT sku, platform, reason AS top_reason FROM (
  SELECT sku, platform, reason,
         ROW_NUMBER() OVER (PARTITION BY sku, platform ORDER BY count(*) DESC, reason) rn
  FROM ret WHERE reason IS NOT NULL
  GROUP BY sku, platform, reason) z
WHERE rn = 1;

-- Return Rate % is computed in the payload builder, not SQL:
--     return_rate = CASE WHEN units_sold > 0
--                        THEN (total_returns::numeric / units_sold) * 100
--                        ELSE 0 END


-- ---------------------------------------------------------------------
-- Q9. SCOPE VERIFICATION — run this to confirm the anchors
--     Expected: 178 components / 223 combos / 261 pairs / 126 with no combo
-- ---------------------------------------------------------------------
SELECT (SELECT count(*) FROM comp)                              AS new_components,
       (SELECT count(DISTINCT combo_sku) FROM pair)             AS combos,
       (SELECT count(*) FROM pair)                              AS component_combo_pairs,
       (SELECT count(DISTINCT comp_sku) FROM pair)              AS components_with_combo,
       (SELECT count(*) FROM comp
         WHERE comp_sku NOT IN (SELECT comp_sku FROM pair))     AS components_without_combo;
