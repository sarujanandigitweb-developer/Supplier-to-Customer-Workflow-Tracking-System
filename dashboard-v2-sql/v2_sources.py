"""
v2_sources.py — Dashboard V2 DATA-SOURCE LAYER for the LEDSone database.

build_v2.py's business SQL was written against the old order_management_copy
tables (public.inv_products, public.inv_product_combo, public.listing_data,
public.traffic_data, public.ppc_performance, public.order_transaction,
public.*_returns, supplier.*). LEDSone stores the same data under different
schemas/columns. This module recreates the OLD table shapes as session-only
TEMP VIEWS / TEMP TABLES (pg_temp.*) on top of LEDSone, so every V2 filter,
join, aggregation and fan-out guard runs UNCHANGED.

Nothing here writes to the database: TEMP objects live only in this session
and vanish on disconnect. Every mapping below was verified old-vs-new
(2026-09-14) before use; the verification numbers are noted inline.

The OLD database is used for exactly two things LEDSone does not carry:
  1. the inv_products.isdeleted flag (product ids are identical in both
     databases; 51/51 deleted ids carry the same sku);
  2. order lines of the sources listed in FALLBACK_ORDER_SOURCES, which exist
     nowhere in LEDSone. Guarded against double counting (see below).
"""

# LEDSone listings.* and suppliers.* timestamps are stored 5h30 behind the old
# copy (UTC vs local). Shifting restores the old calendar dates exactly
# (listings: 860/860 Listed Dates; suppliers: received dates 258/260, the two
# differences being a PO that exists only in LEDSone).
TZ = "interval '5 hours 30 minutes'"

# numeric text -> numeric, anything else -> NULL (order_item_info stores text)
NUM = "CASE WHEN {c} ~ '^\\s*-?[0-9]+(\\.[0-9]+)?\\s*$' THEN {c}::numeric END"

SOURCE_MAP = [
    ("public.inv_products",      "inventory.products (+ isdeleted from the old DB, by product id)"),
    ("public.inv_product_combo", "inventory.products.sku_original tokens (component sku, or sku + pack suffix)"),
    ("supplier.*",               "suppliers.* (final_containers.updated_at +5h30, status_arrived bool->int)"),
    ("public.listing_data",      "listings.amazon_listings(asin) / ebay_listings(item_id, is_ended=0) / "
                                 "shopify_listings(item_id) / bandq_listings(ean); created_at +5h30; market_place=site"),
    ("public.traffic_data",      "business_reports.amz_catalog_performance_data(asin, end_date) + "
                                 "business_reports.ebay_traffic_data(item_id, click=ebay_views)"),
    ("public.ppc_performance",   "amazon_campaigns.performance_data(asin) + ebay_campaigns.performance_data"
                                 "(ebay_listing_id, ad_id<>'0') + google_ads.product_performance(parent_id, "
                                 "latest version per id)"),
    ("public.order_transaction", "order_management.orders+order_item_info+sub_source+source (MFN) + "
                                 "amazon_fba_orders+amazon_fba_order_items (FBA) + OLD-DB fallback for "
                                 "sources absent from LEDSone (REPLACEMENT, ETSY, MANUAL OM, MANUALORDER, "
                                 "AVASAM, BOL, MANOMANO, FAIRE, RESEND, ONBUY)"),
    ("public.amazon_returns",    "customer_service.amazon_returns"),
    ("public.ebay_returns",      "customer_service.ebay_returns"),
    ("public.shopify_returns",   "accounting.shopify_transactions WHERE type='refund'"),
]


# ---------------------------------------------------------------------------
# ORDER-SOURCE FALLBACK (isolated). LEDSone's order tables carry ONLY the
# AMAZON / EBAY / SHOPIFY / B&Q / WAYFAIR sources (+ FBA). These old
# order_transaction sources do not exist anywhere in LEDSone -- verified
# 2026-09-14: 0 LEDSone orders on their sub_sources, 0 hits for their order ids
# across all 846 text columns of every schema. They are therefore read from the
# old DB, and ONLY these sources.
FALLBACK_ORDER_SOURCES = ["REPLACEMENT", "ETSY", "MANUAL OM", "MANUALORDER", "AVASAM",
                          "BOL", "MANOMANO", "FAIRE", "RESEND", "ONBUY"]


def load_fallback_orders(ref_conn):
    """Old order_transaction lines for the sources LEDSone does not carry (all dates,
    because build_v2's returns step looks up orders of any date)."""
    with ref_conn.cursor() as c:
        c.execute("""SELECT order_item_info, order_id, sku, quantity, order_status,
                            order_date, order_total, source_name
                     FROM public.order_transaction
                     WHERE NOT COALESCE(fba_sales, false) AND source_name = ANY(%s)""",
                  (FALLBACK_ORDER_SOURCES,))
        return c.fetchall()


def load_deleted_reference(ref_conn):
    """Product ids flagged deleted in the old inv_products (the only old-DB read)."""
    with ref_conn.cursor() as c:
        c.execute("SELECT id FROM public.inv_products WHERE COALESCE(isdeleted,0) <> 0")
        return [r[0] for r in c.fetchall()]


def create_source_views(cur, deleted_ids, fallback_orders):
    """Returns stats about the order fallback (used by build_v2 validation)."""
    # ---- deletion reference (old DB) ----------------------------------------
    cur.execute("CREATE TEMP TABLE ref_deleted_products (id bigint PRIMARY KEY)")
    if deleted_ids:
        cur.execute("INSERT INTO ref_deleted_products SELECT unnest(%s::bigint[])", (deleted_ids,))

    # ---- order fallback (old DB, only sources absent from LEDSone) ----------
    # Guard 1: if LEDSone ever starts carrying one of these sources, stop --
    # reading it from both databases would double-count those orders.
    cur.execute("""SELECT s.source_name, count(*) FROM order_management.orders o
                   JOIN order_management.sub_source ss ON ss.id = o.sub_source_id
                   JOIN order_management.source s      ON s.id  = ss.source_id
                   WHERE s.source_name = ANY(%s) GROUP BY 1""", (FALLBACK_ORDER_SOURCES,))
    overlap = cur.fetchall()
    if overlap:
        raise RuntimeError("LEDSone now carries fallback order sources " + str(overlap)
                           + " -- remove them from FALLBACK_ORDER_SOURCES to avoid double counting")
    cur.execute("""CREATE TEMP TABLE fallback_order_lines (
        line_id bigint PRIMARY KEY, order_id text, sku text, quantity numeric,
        order_status text, order_date timestamp, order_total numeric, source_name text)""")
    from psycopg2.extras import execute_values
    execute_values(cur, "INSERT INTO fallback_order_lines VALUES %s", fallback_orders, page_size=5000)
    # Guard 2: drop any line whose id already exists in LEDSone (never both).
    cur.execute("""DELETE FROM fallback_order_lines f USING order_management.order_item_info i
                   WHERE i.id = f.line_id""")
    dup_removed = cur.rowcount
    cur.execute("""SELECT count(*), count(*) FILTER (WHERE order_date >= '2026-01-01'),
                          count(DISTINCT order_id) FROM fallback_order_lines""")
    fb_lines, fb_2026, fb_orders = cur.fetchone()

    # ---- public.inv_products -------------------------------------------------
    # id / sku / created_at are identical to the old table (44,496 shared ids;
    # 260/260 component created dates). eng_desc was renamed eng_description.
    cur.execute("""
    CREATE TEMP VIEW inv_products AS
    SELECT p.id, p.sku, p.title, p.description, p.eng_description AS eng_desc,
           p.created_at,
           CASE WHEN d.id IS NOT NULL THEN 1 ELSE 0 END AS isdeleted
    FROM inventory.products p
    LEFT JOIN ref_deleted_products d ON d.id = p.id""")

    # ---- public.inv_product_combo -------------------------------------------
    # LEDSone has no combo table. A combo's inventory.products.sku_original lists
    # its parts joined by '+' (ENC10065 -> CRSFM110080BM+LHNSE27YB+...). A part is
    # a product when the token equals its sku, or its sku followed by a pack
    # suffix ([A-Z]?[0-9]*PK: 2PK, 3PK, CPK, FPK ...). Reproduces 366/366 of the
    # old V2 component->combo links; the only extras are combos flagged deleted,
    # which build_v2's existing isdeleted=0 filter removes.
    cur.execute("""
    CREATE TEMP TABLE inv_product_combo AS
    WITH tok AS (
      SELECT DISTINCT p.id AS product, TRIM(t) AS token
      FROM inventory.products p
      CROSS JOIN LATERAL unnest(string_to_array(p.sku_original, '+')) AS t
      WHERE COALESCE(p.sku_original,'') <> '' AND TRIM(t) <> ''),
    cand AS (
      SELECT product, token, left(token, n) AS part_sku, substr(token, n+1) AS suffix
      FROM tok CROSS JOIN LATERAL generate_series(1, length(token)) AS n)
    SELECT DISTINCT c.product, i.id AS inventory, NULL::text AS pack_count
    FROM cand c
    JOIN inventory.products i ON i.sku = c.part_sku
    WHERE c.suffix = '' OR c.suffix ~ '^[A-Z]?[0-9]*PK$'""")
    cur.execute("CREATE INDEX ON inv_product_combo(inventory)")
    cur.execute("ANALYZE inv_product_combo")

    # ---- supplier.* ----------------------------------------------------------
    cur.execute("CREATE TEMP VIEW supplier_suppliers AS SELECT id, name FROM suppliers.suppliers")
    cur.execute("""CREATE TEMP VIEW supplier_orders AS
        SELECT id, order_id, supplier_id, order_date, status_arrived::int AS status_arrived
        FROM suppliers.orders""")
    cur.execute("""CREATE TEMP VIEW supplier_order_items AS
        SELECT id, order_id, sku, pcs, image_url, final_container_id, assigned_container_id,
               created_at + %s AS created_at
        FROM suppliers.order_items""" % TZ)
    cur.execute("""CREATE TEMP VIEW supplier_final_containers AS
        SELECT id, name, main_container, status, updated_at + %s AS updated_at
        FROM suppliers.final_containers""" % TZ)
    cur.execute("CREATE TEMP VIEW supplier_containers AS SELECT id, name, main_container FROM suppliers.containers")

    # ---- product change history (warehouse stock-in log, free text) ---------
    cur.execute("""CREATE TEMP VIEW product_history AS
        SELECT p.sku, h.history FROM inventory.product_history h
        JOIN inventory.products p ON p.id = h.inventory_id""")

    # ---- product catalogue photos (LEDSone inventory app image) -------------
    cur.execute("""CREATE TEMP VIEW product_catalog_images AS
        SELECT pi.id, p.sku, pi.image_url, pi.image_ordering, 1 AS src_rank
        FROM inventory.product_images pi JOIN inventory.products p ON p.id = pi.product_id
        WHERE COALESCE(pi.image_url,'') <> ''
        UNION ALL
        SELECT pm.id, p.sku, pm.image_url, NULL::int, 2
        FROM inventory.product_media pm JOIN inventory.products p ON p.id = pm.product_id
        WHERE pm.type = 'main-image' AND COALESCE(pm.image_url,'') <> ''""")
    cur.execute("CREATE TEMP VIEW supplier_invoices AS SELECT final_container_id, ship_by_date FROM suppliers.invoices")

    # ---- public.listing_data -------------------------------------------------
    # Row ids are shared with the old table. The old table never carried ended
    # eBay listings (is_ended=1: 0 old rows vs 137,239 in LEDSone).
    cur.execute(f"""
    CREATE TEMP VIEW listing_data AS
    SELECT id, asin::text AS ref_id, sku, mapped_sku, 'amazon'::text AS which_channel_name,
           is_parent, wrong_sku, created_at + {TZ} AS created_at,
           listing_url, main_image_url, site AS market_place
    FROM listings.amazon_listings
    UNION ALL
    SELECT id, item_id::text, sku, NULL::varchar, 'ebay',
           is_parent, wrong_sku, created_at + {TZ}, listing_url, main_image_url, site
    FROM listings.ebay_listings WHERE COALESCE(is_ended,0) = 0
    UNION ALL
    SELECT id, item_id::text, sku, mapped_sku, 'shopify',
           is_parent, wrong_sku, created_at + {TZ}, listing_url, main_image_url, site
    FROM listings.shopify_listings
    UNION ALL
    SELECT id, ean::text, sku, mapped_sku, 'B&Q',
           0, wrong_sku, created_at + {TZ}, listing_url, main_image_url, site
    FROM listings.bandq_listings""")

    # ---- public.traffic_data (organic) --------------------------------------
    # Amazon: weekly report, old date = end_date (row-for-row identical).
    # eBay: old click = ebay_views (row-for-row identical).
    cur.execute("""
    CREATE TEMP VIEW traffic_data AS
    SELECT asin::text AS ref_id, end_date AS date,
           impression_count AS impression, click_count AS click
    FROM business_reports.amz_catalog_performance_data
    UNION ALL
    SELECT item_id::text, date, impressions, ebay_views
    FROM business_reports.ebay_traffic_data""")

    # ---- public.ppc_performance ---------------------------------------------
    # eBay ad_id='0' rows are campaign-level; the old table stored them with
    # ref_id '0' so they never matched a listing -- excluded here for the same effect.
    # google_ads.product_performance holds superseded copies of some records (same
    # id, an older version with ad_group_id=0 next to the re-synced version; 10,632
    # ids in 2026). The old table kept one version per record, so only the latest
    # version per id is used: reproduces the old table on 802,585/802,585
    # (date, product, campaign) cells for Jul-Sep 2026 (raw copies: 99.40%).
    cur.execute("""
    CREATE TEMP TABLE gads_product_perf_latest AS
    SELECT DISTINCT ON (id) id, parent_id, date, impressions, clicks
    FROM google_ads.product_performance
    WHERE id IN (SELECT id FROM google_ads.product_performance GROUP BY id HAVING count(*) > 1)
    ORDER BY id, updated_at DESC NULLS LAST""")
    cur.execute("CREATE UNIQUE INDEX ON gads_product_perf_latest(id)")
    cur.execute("ANALYZE gads_product_perf_latest")
    cur.execute("""
    CREATE TEMP VIEW ppc_performance AS
    SELECT asin::text AS ref_id, date, impressions, clicks FROM amazon_campaigns.performance_data
    UNION ALL
    SELECT ebay_listing_id::text, date, impressions, clicks
    FROM ebay_campaigns.performance_data WHERE ad_id::text <> '0'
    UNION ALL
    SELECT p.parent_id::text, p.date, p.impressions, p.clicks FROM google_ads.product_performance p
    WHERE NOT EXISTS (SELECT 1 FROM gads_product_perf_latest d WHERE d.id = p.id)
    UNION ALL
    SELECT parent_id::text, date, impressions, clicks FROM gads_product_perf_latest""")

    # ---- public.order_transaction -------------------------------------------
    # MFN: sku = item_sku, status = orders.status (2036/2036 lines). Line total =
    # orders.total for a single-line order, else item_price * item_quantity
    # (2032/2036; the 4 others have NULL price, old = 0).
    # FBA: Shipped -> Completed; seller-sku suffix cut at the first separator,
    # amzn.gr.* kept raw (1,992/2,015 distinct skus; none of the 23 others in V2 scope).
    q, p = NUM.format(c="i.item_quantity"), NUM.format(c="i.item_price")
    cur.execute(f"""
    CREATE TEMP VIEW order_transaction AS
    SELECT o.order_id, i.item_sku AS sku, ({q}) AS quantity, o.status AS order_status,
           o.order_date, s.source_name,
           CASE WHEN count(*) OVER (PARTITION BY o.id) = 1 THEN o.total
                ELSE ROUND(COALESCE({p},0) * COALESCE({q},0), 2) END AS order_total
    FROM order_management.orders o
    JOIN order_management.order_item_info i ON i.order_id = o.id
    LEFT JOIN order_management.sub_source ss ON ss.id = o.sub_source_id
    LEFT JOIN order_management.source s      ON s.id  = ss.source_id
    UNION ALL
    SELECT o.order_id,
           CASE WHEN i.item_sku LIKE 'amzn.gr.%' THEN i.item_sku
                ELSE split_part(regexp_replace(i.item_sku, '[ _-]', chr(1)), chr(1), 1) END,
           ({q}), CASE WHEN o.status = 'Shipped' THEN 'Completed' ELSE o.status END,
           o.order_date, 'AMAZON',
           CASE WHEN count(*) OVER (PARTITION BY o.id) = 1 THEN o.total
                ELSE ROUND(COALESCE({p},0) * COALESCE({q},0), 2) END
    FROM order_management.amazon_fba_orders o
    JOIN order_management.amazon_fba_order_items i ON i.order_id = o.id
    UNION ALL
    -- old-DB fallback: only the sources LEDSone does not carry (see above)
    SELECT order_id, sku, quantity, order_status, order_date, source_name, order_total
    FROM fallback_order_lines""")

    # ---- returns -------------------------------------------------------------
    cur.execute("""CREATE TEMP VIEW amazon_returns AS
        SELECT sku, qty, reason, request_date FROM customer_service.amazon_returns""")
    cur.execute("""CREATE TEMP VIEW ebay_returns AS
        SELECT return_id, order_id, return_qty, reason, request_date FROM customer_service.ebay_returns""")
    # 679/679 refund rows and 675/675 orders identical to the old shopify_returns.
    cur.execute("""CREATE TEMP VIEW shopify_returns AS
        SELECT id, order_id, processed_at AS date FROM accounting.shopify_transactions
        WHERE type = 'refund'""")

    return {"sources": FALLBACK_ORDER_SOURCES, "lines_loaded": len(fallback_orders),
            "lines_dropped_already_in_ledsone": dup_removed, "lines_used": fb_lines,
            "lines_used_2026": fb_2026, "orders_used": fb_orders}
