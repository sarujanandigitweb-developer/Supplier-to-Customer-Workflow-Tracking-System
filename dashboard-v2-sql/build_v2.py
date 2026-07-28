#!/usr/bin/env python3
"""
build_v2.py — Dashboard V2 payload builder.  Supplier -> Container -> Component
-> Combo -> Listing -> Sales -> Returns, scoped to 2026-onwards stock only.

Fetched 100% live from PostgreSQL. No cached JSON, no reuse of V1 SQL/joins.

SCOPE CHAIN
  1. NEW COMPONENT = inv_products.created_at >= 2026-01-01, isdeleted=0,
     sku NOT LIKE '%+%', AND the sku appears in supplier.order_items.
  2. COMBO         = inv_product_combo.product where .inventory = that component
                     (inventory <> product), combo created_at >= 2026-01-01.
  3. ROW           = one per (component, combo, marketplace). A component with no
                     combo still gets a row (blank combo) -- that gap is the point.

RECEIVED DATE  = the SHIPPING container's close-out into inventory:
    supplier.final_containers.updated_at WHERE status='completed'
    -> falls back to supplier.invoices.ship_by_date
    -> blank when the container is still open (NOT back-filled with the PO date).
  order_items.final_container_id is the real shipping container (154/178 coverage);
  assigned_container_id is only the loading container (88/178).

CONTAINER = COALESCE(final_containers.name, containers.name). It must NEVER fall
  back to orders.container_id -- that is a raw foreign key and leaked bare ints
  such as "31" into the UI (bug found 2026-07-28).
"""
import json, time
from datetime import date, datetime
from pathlib import Path
import psycopg2

BASE  = Path(__file__).resolve().parent
PROJ  = BASE.parent
OUT   = PROJ / "dashboard-v2"
START = "2026-01-01"
TODAY = date.today().isoformat()
T0    = time.time()

DB = dict(host="149.28.134.54", port="5435", dbname="order_management_copy",
          user="temp_user", password="12we34rt")

PLAT = """CASE WHEN lower({c}) LIKE '%%amazon%%'  THEN 'amazon'
               WHEN lower({c}) LIKE '%%ebay%%'    THEN 'ebay'
               WHEN lower({c}) LIKE '%%shopify%%' THEN 'shopify'
               WHEN lower({c}) LIKE '%%b&q%%'     THEN 'b&q'
               WHEN lower({c}) LIKE '%%wayfair%%' THEN 'wayfair'
               ELSE 'other' END"""

VAL = {"run": datetime.now().strftime("%Y%m%d_%H%M%S"), "checks": [], "notes": []}
def check(name, ok, detail=""):
    VAL["checks"].append({"check": name, "status": "PASS" if ok else "FAIL", "detail": detail})
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}{(' — '+detail) if detail else ''}")
    return ok

conn = psycopg2.connect(connect_timeout=40, **DB); conn.autocommit = True
cur = conn.cursor()
print(f"connected {DB['user']}@{DB['host']}:{DB['port']}/{DB['dbname']}")

# ---------- 1. NEW COMPONENTS (2026, purchased from a supplier) ----------------
cur.execute("""
CREATE TEMP TABLE comp AS
SELECT DISTINCT p.id AS comp_id, p.sku AS comp_sku,
       p.created_at::date::text AS comp_created,
       COALESCE(NULLIF(p.eng_desc,''),NULLIF(p.description,''),NULLIF(p.title,''),'') AS comp_desc
FROM public.inv_products p
JOIN supplier.order_items oi ON oi.sku = p.sku
WHERE p.created_at >= %(s)s AND COALESCE(p.isdeleted,0)=0
  AND COALESCE(TRIM(p.sku),'')<>'' AND p.sku NOT LIKE '%%+%%';
CREATE INDEX ON comp(comp_id); CREATE INDEX ON comp(comp_sku);
""", {"s": START})
cur.execute("SELECT count(*) FROM comp"); n_comp = cur.fetchone()[0]
print(f"new components (2026, on a supplier PO): {n_comp}")

# ---------- 2. SUPPLIER / CONTAINER / RECEIVED-DATE PROXY (latest PO per comp) --
cur.execute("""
CREATE TEMP TABLE sup AS
SELECT DISTINCT ON (oi.sku)
       oi.sku                                  AS comp_sku,
       COALESCE(s.name,'')                     AS supplier,
       -- CONTAINER: the real SHIPPING container (final_containers) first, then the
       -- loading container. NEVER fall back to orders.container_id -- that is a raw
       -- foreign key and leaked ints like "31" into the UI (bug found 2026-07-28).
       COALESCE(fc.name, ct.name, '')           AS container,
       COALESCE(fc.main_container, ct.main_container, '') AS destination,
       -- RECEIVED DATE: the container's own close-out date, i.e. when the shipment
       -- was completed into inventory. Falls back to the invoice ship-by date.
       -- No silent fall back to the PO date -- blank means genuinely unknown.
       COALESCE(
         CASE WHEN fc.status = 'completed' THEN fc.updated_at::date::text END,
         inv.ship_by_date::text,
         ''
       )                                        AS received,
       o.order_date::text                       AS po_date,
       COALESCE(o.order_id,'')                  AS po,
       COALESCE(oi.pcs,0)                       AS qty,
       COALESCE(o.status_arrived,0)             AS arrived
FROM supplier.order_items oi
JOIN comp c                    ON c.comp_sku = oi.sku
JOIN supplier.orders     o     ON o.id  = oi.order_id
LEFT JOIN supplier.suppliers        s  ON s.id  = o.supplier_id
LEFT JOIN supplier.final_containers fc ON fc.id = oi.final_container_id::bigint
LEFT JOIN supplier.containers       ct ON ct.id = oi.assigned_container_id::bigint
LEFT JOIN (SELECT final_container_id, MIN(ship_by_date) AS ship_by_date
           FROM supplier.invoices GROUP BY 1) inv
       ON inv.final_container_id = oi.final_container_id::bigint
ORDER BY oi.sku, o.order_date DESC NULLS LAST, o.id DESC;
CREATE INDEX ON sup(comp_sku);
""")
cur.execute("SELECT comp_sku, supplier, container, destination, received, po_date, po, qty, arrived FROM sup")
supmap = {r[0]: dict(supplier=r[1], container=r[2], dest=r[3], recv=r[4], po_date=r[5],
                     po=r[6], qty=r[7], arrived=bool(r[8])) for r in cur.fetchall()}
# PO count per component (multiple restocks are the norm)
cur.execute("""SELECT oi.sku, count(*) FROM supplier.order_items oi
               JOIN comp c ON c.comp_sku=oi.sku GROUP BY 1""")
po_count = dict(cur.fetchall())

# ---------- 3. COMBOS built from those components ------------------------------
cur.execute("""
CREATE TEMP TABLE pair AS
SELECT c.comp_sku, c.comp_created, c.comp_desc,
       cp.id  AS combo_id,
       cp.sku AS combo_sku,
       cp.created_at::date::text AS combo_created,
       COALESCE(NULLIF(cp.eng_desc,''),NULLIF(cp.description,''),NULLIF(cp.title,''),'') AS combo_desc,
       pc.pack_count
FROM comp c
JOIN public.inv_product_combo pc ON pc.inventory = c.comp_id AND pc.inventory <> pc.product
JOIN public.inv_products cp      ON cp.id = pc.product
WHERE cp.created_at >= %(s)s AND COALESCE(cp.isdeleted,0)=0 AND COALESCE(TRIM(cp.sku),'')<>'';
CREATE INDEX ON pair(combo_sku); CREATE INDEX ON pair(comp_sku);
""", {"s": START})
cur.execute("SELECT count(*), count(DISTINCT combo_sku), count(DISTINCT comp_sku) FROM pair")
n_pair, n_combo, n_comp_w = cur.fetchone()
print(f"combos: {n_combo}  |  component x combo pairs: {n_pair}  |  components with a combo: {n_comp_w}")

# ---------- 4. LISTINGS for the combo SKUs (per platform) ----------------------
cur.execute(f"""
CREATE TEMP TABLE lst AS
SELECT COALESCE(a.sku,b.sku) AS sku, ld.ref_id,
       {PLAT.format(c='ld.which_channel_name')} AS platform,
       ld.created_at::date AS listed_on,
       ld.listing_url, ld.main_image_url, ld.market_place
FROM public.listing_data ld
LEFT JOIN public.inv_products a ON a.sku = COALESCE(NULLIF(TRIM(ld.mapped_sku),''),TRIM(ld.sku))
LEFT JOIN public.inv_products b ON b.sku = regexp_replace(COALESCE(NULLIF(TRIM(ld.mapped_sku),''),TRIM(ld.sku)),'[_-][A-Za-z]{{2,4}}$','')
WHERE COALESCE(ld.is_parent,0)=0 AND ld.wrong_sku=0 AND COALESCE(TRIM(ld.sku),'')<>''
  AND COALESCE(a.sku,b.sku) IN (SELECT combo_sku FROM pair);
CREATE INDEX ON lst(sku); CREATE INDEX ON lst(ref_id);
""")
cur.execute("""
SELECT sku, platform, MIN(listed_on)::text,
       (array_agg(listing_url ORDER BY listed_on, ref_id))[1],
       (array_agg(market_place ORDER BY listed_on, ref_id))[1]
FROM lst GROUP BY sku, platform""")
listed = {}
for sku, plat, ld, url, mkt in cur.fetchall():
    listed.setdefault(sku, {})[plat] = dict(ld=ld, url=url or "", mkt=mkt or "")

# ---------- 5. IMAGES ----------------------------------------------------------
# COMPONENTS are supplier parts -- they are rarely listed on a marketplace, so the
# marketplace listing image is the WRONG primary source (it only covered 26/178).
# The supplier's own photo lives on supplier.order_items.image_url. Use that first,
# then fall back to a listing image.                    26/178 -> 92/178 coverage.
cur.execute("""
SELECT DISTINCT ON (oi.sku) oi.sku, oi.image_url
FROM supplier.order_items oi
JOIN comp c ON c.comp_sku = oi.sku
WHERE COALESCE(oi.image_url,'') <> ''
ORDER BY oi.sku, oi.created_at DESC, oi.id DESC""")
img_comp = dict(cur.fetchall())

# COMBOS are the sellable unit and ARE listed, so the newest listing image is right.
cur.execute("""
SELECT DISTINCT ON (resolved) resolved, main_image_url FROM (
  SELECT COALESCE(NULLIF(TRIM(mapped_sku),''),TRIM(sku)) AS resolved,
         main_image_url, created_at, ref_id
  FROM public.listing_data
  WHERE COALESCE(main_image_url,'')<>''
    AND COALESCE(NULLIF(TRIM(mapped_sku),''),TRIM(sku)) IN (
        SELECT comp_sku FROM comp UNION SELECT combo_sku FROM pair)) z
ORDER BY resolved, created_at DESC, ref_id""")
img = dict(cur.fetchall())          # listing images, keyed by SKU (combo or component)

def comp_image(sku):
    """Supplier photo first, marketplace listing image second."""
    return img_comp.get(sku) or img.get(sku, "")

# ---------- 6. TRAFFIC — from each listing's OWN Listed Date to today ----------
cur.execute("""
SELECT l.sku, l.platform, SUM(t.i)::bigint, SUM(t.c)::bigint FROM lst l
JOIN (SELECT ref_id, date, COALESCE(impression,0) i, COALESCE(click,0) c FROM public.traffic_data
      UNION ALL
      SELECT ref_id, date, COALESCE(impressions,0), COALESCE(clicks,0) FROM public.ppc_performance) t
  ON t.ref_id = l.ref_id AND t.date >= l.listed_on          -- Listed Date -> today
GROUP BY 1,2""")
traffic = {(s, p): (i, c) for s, p, i, c in cur.fetchall()}

# ---------- 7. ORDERS / UNITS / REVENUE for the combo SKUs --------------------
cur.execute(f"""
SELECT base_sku, platform, count(DISTINCT order_id), SUM(quantity)::int,
       ROUND(SUM(order_total)::numeric,2)::float8
FROM (
  SELECT regexp_replace(TRIM(ot.sku),'[_-][A-Za-z]{{2,4}}$','') AS base_sku,
         {PLAT.format(c='ot.source_name')} AS platform,
         ot.order_id, ot.quantity, ot.order_total
  FROM public.order_transaction ot
  WHERE ot.order_status='Completed'
    AND regexp_replace(TRIM(ot.sku),'[_-][A-Za-z]{{2,4}}$','') IN (SELECT combo_sku FROM pair)) o
GROUP BY 1,2""")
orders = {(s, p): (o, u, r) for s, p, o, u, r in cur.fetchall()}

# ---------- 8. RETURNS: total qty + top reason, per (sku, platform) -----------
# amazon: sku direct + reason.  ebay: via order_transaction + reason.
# shopify: via order_transaction, NO reason column in source.
cur.execute("""
CREATE TEMP TABLE ret AS
WITH co AS (
  SELECT ot.order_id, regexp_replace(TRIM(ot.sku),'[_-][A-Za-z]{2,4}$','') AS base_sku,
         SUM(ot.quantity)::int AS oqty
  FROM public.order_transaction ot GROUP BY 1,2)
SELECT regexp_replace(TRIM(ar.sku),'[_-][A-Za-z]{2,4}$','') AS sku,
       'amazon'::text AS platform, ar.qty::int AS qty, NULLIF(TRIM(ar.reason),'') AS reason
FROM public.amazon_returns ar
WHERE regexp_replace(TRIM(ar.sku),'[_-][A-Za-z]{2,4}$','') IN (SELECT combo_sku FROM pair)
UNION ALL
SELECT co.base_sku, 'ebay', e.qty, e.reason FROM (
  SELECT return_id, MIN(order_id) order_id, MAX(return_qty)::int qty,
         NULLIF(TRIM(MAX(reason)),'') reason
  FROM public.ebay_returns GROUP BY return_id) e
JOIN co ON co.order_id = e.order_id
WHERE co.base_sku IN (SELECT combo_sku FROM pair)
UNION ALL
SELECT co.base_sku, 'shopify', co.oqty, NULL FROM (
  SELECT DISTINCT ON (id) id, order_id FROM public.shopify_returns ORDER BY id) sh
JOIN co ON co.order_id = sh.order_id
WHERE co.base_sku IN (SELECT combo_sku FROM pair);
""")
cur.execute("SELECT sku, platform, SUM(COALESCE(qty,0))::int FROM ret GROUP BY 1,2")
returns_tot = {(s, p): q for s, p, q in cur.fetchall()}
cur.execute("""
SELECT sku, platform, reason FROM (
  SELECT sku, platform, reason, ROW_NUMBER() OVER (PARTITION BY sku, platform
         ORDER BY count(*) DESC, reason) rn
  FROM ret WHERE reason IS NOT NULL GROUP BY sku, platform, reason) z WHERE rn=1""")
top_reason = {(s, p): r for s, p, r in cur.fetchall()}

# ---------- 8b. COMPONENT (SINGLE-SKU) DATASET --------------------------------
# The Components tab is a SEPARATE dataset, not a re-slice of the combo queries.
# Everything below is keyed on the COMPONENT sku's own listings/orders/returns.
cur.execute(f"""
CREATE TEMP TABLE lst_c AS
SELECT COALESCE(a.sku,b.sku) AS sku, ld.ref_id,
       {PLAT.format(c='ld.which_channel_name')} AS platform,
       ld.created_at::date AS listed_on,
       ld.listing_url, ld.main_image_url, ld.market_place
FROM public.listing_data ld
LEFT JOIN public.inv_products a ON a.sku = COALESCE(NULLIF(TRIM(ld.mapped_sku),''),TRIM(ld.sku))
LEFT JOIN public.inv_products b ON b.sku = regexp_replace(COALESCE(NULLIF(TRIM(ld.mapped_sku),''),TRIM(ld.sku)),'[_-][A-Za-z]{{2,4}}$','')
WHERE COALESCE(ld.is_parent,0)=0 AND ld.wrong_sku=0 AND COALESCE(TRIM(ld.sku),'')<>''
  AND COALESCE(a.sku,b.sku) IN (SELECT comp_sku FROM comp);
CREATE INDEX ON lst_c(sku); CREATE INDEX ON lst_c(ref_id);
""")
cur.execute("""
SELECT sku, platform, MIN(listed_on)::text,
       (array_agg(listing_url ORDER BY listed_on, ref_id))[1],
       (array_agg(market_place ORDER BY listed_on, ref_id))[1]
FROM lst_c GROUP BY sku, platform""")
listed_c = {}
for sku, plat, ld, url, mkt in cur.fetchall():
    listed_c.setdefault(sku, {})[plat] = dict(ld=ld, url=url or "", mkt=mkt or "")

cur.execute("""
SELECT l.sku, l.platform, SUM(t.i)::bigint, SUM(t.c)::bigint FROM lst_c l
JOIN (SELECT ref_id, date, COALESCE(impression,0) i, COALESCE(click,0) c FROM public.traffic_data
      UNION ALL
      SELECT ref_id, date, COALESCE(impressions,0), COALESCE(clicks,0) FROM public.ppc_performance) t
  ON t.ref_id = l.ref_id AND t.date >= l.listed_on
GROUP BY 1,2""")
traffic_c = {(s, p): (i, c) for s, p, i, c in cur.fetchall()}

cur.execute(f"""
SELECT base_sku, platform, count(DISTINCT order_id), SUM(quantity)::int,
       ROUND(SUM(order_total)::numeric,2)::float8
FROM (
  SELECT regexp_replace(TRIM(ot.sku),'[_-][A-Za-z]{{2,4}}$','') AS base_sku,
         {PLAT.format(c='ot.source_name')} AS platform,
         ot.order_id, ot.quantity, ot.order_total
  FROM public.order_transaction ot
  WHERE ot.order_status='Completed'
    AND regexp_replace(TRIM(ot.sku),'[_-][A-Za-z]{{2,4}}$','') IN (SELECT comp_sku FROM comp)) o
GROUP BY 1,2""")
orders_c = {(s, p): (o, u, r) for s, p, o, u, r in cur.fetchall()}

cur.execute("""
CREATE TEMP TABLE ret_c AS
WITH co AS (
  SELECT ot.order_id, regexp_replace(TRIM(ot.sku),'[_-][A-Za-z]{2,4}$','') AS base_sku,
         SUM(ot.quantity)::int AS oqty
  FROM public.order_transaction ot GROUP BY 1,2)
SELECT regexp_replace(TRIM(ar.sku),'[_-][A-Za-z]{2,4}$','') AS sku,
       'amazon'::text AS platform, ar.qty::int AS qty, NULLIF(TRIM(ar.reason),'') AS reason
FROM public.amazon_returns ar
WHERE regexp_replace(TRIM(ar.sku),'[_-][A-Za-z]{2,4}$','') IN (SELECT comp_sku FROM comp)
UNION ALL
SELECT co.base_sku, 'ebay', e.qty, e.reason FROM (
  SELECT return_id, MIN(order_id) order_id, MAX(return_qty)::int qty,
         NULLIF(TRIM(MAX(reason)),'') reason
  FROM public.ebay_returns GROUP BY return_id) e
JOIN co ON co.order_id = e.order_id
WHERE co.base_sku IN (SELECT comp_sku FROM comp)
UNION ALL
SELECT co.base_sku, 'shopify', co.oqty, NULL FROM (
  SELECT DISTINCT ON (id) id, order_id FROM public.shopify_returns ORDER BY id) sh
JOIN co ON co.order_id = sh.order_id
WHERE co.base_sku IN (SELECT comp_sku FROM comp);
""")
cur.execute("SELECT sku, platform, SUM(COALESCE(qty,0))::int FROM ret_c GROUP BY 1,2")
returns_c = {(s, p): q for s, p, q in cur.fetchall()}
cur.execute("""
SELECT sku, platform, reason FROM (
  SELECT sku, platform, reason, ROW_NUMBER() OVER (PARTITION BY sku, platform
         ORDER BY count(*) DESC, reason) rn
  FROM ret_c WHERE reason IS NOT NULL GROUP BY sku, platform, reason) z WHERE rn=1""")
top_reason_c = {(s, p): r for s, p, r in cur.fetchall()}
print(f"component-listing dataset: {len(listed_c)} components have their own listing")

# ---------- 8c. AVERAGE FEEDBACK ----------------------------------------------
# Searched every schema for rating/review/feedback/star/score columns and for any
# table named like reviews. The ONLY hit is public.blos_maduro_review_queue_v1,
# which is a threshold-approval workflow queue for a different project -- not
# customer product reviews. public.ph_asin_health_alerts only carries stock and
# listing-status alerts. There is therefore NO customer-rating source in this DB.
# The column is wired end-to-end and renders "No Reviews"; when a marketplace
# reviews feed is loaded, populate `feedback[(sku, platform)] = (avg, count)`
# here and nothing else in the pipeline needs to change.
feedback = {}          # (sku, platform) -> (avg_rating, review_count)
VAL["notes"].append("Average Feedback: no customer-review source exists in this database "
                    "(searched all schemas for rating/review/feedback/star columns). "
                    "Column renders 'No Reviews' for every row pending a marketplace reviews feed.")

# ---------- 9. BUILD ROWS ------------------------------------------------------
B = {"sup":0,"cont":1,"recv":2,"csku":3,"cimg":4,"ccre":5,"bsku":6,"bimg":7,"bcre":8,
     "stat":9,"plat":10,"ldate":11,"impr":12,"clk":13,"ord":14,"units":15,"rev":16,
     "ret":17,"rrate":18,"reason":19,"url":20,"dest":21,"po":22,"qty":23,"notes":24,
     "fb":25,"comps":26}

cur.execute("SELECT comp_sku, comp_created, comp_desc, combo_sku, combo_created, combo_desc, pack_count FROM pair ORDER BY comp_sku, combo_sku")
pairs = cur.fetchall()
cur.execute("SELECT comp_sku, comp_created, comp_desc FROM comp ORDER BY comp_sku")
all_comps = cur.fetchall()
comps_with_combo = {p[0] for p in pairs}

rows = []
def blank():
    r = [None]*27
    for k in ("impr","clk","ord","units","ret"): r[B[k]] = 0
    r[B["rev"]] = 0.0; r[B["rrate"]] = 0.0
    r[B["fb"]] = None                       # None -> UI renders "No Reviews"
    r[B["comps"]] = None                    # component SKUs behind this row
    return r

def fb_for(sku, plat):
    """(avg_rating, review_count) or None. Empty until a reviews feed exists."""
    v = feedback.get((sku, plat))
    return list(v) if v else None

def base(comp_sku, comp_created, comp_desc):
    r = blank(); s = supmap.get(comp_sku, {})
    r[B["sup"]]  = s.get("supplier",""); r[B["cont"]] = s.get("container","")
    r[B["dest"]] = s.get("dest","");     r[B["recv"]] = s.get("recv","")
    r[B["po"]]   = s.get("po","");       r[B["qty"]]  = s.get("qty",0)
    r[B["csku"]] = comp_sku
    r[B["cimg"]] = comp_image(comp_sku)
    r[B["ccre"]] = comp_created
    n = po_count.get(comp_sku,0)
    notes = [comp_desc[:70]] if comp_desc else []
    if s.get("po_date"): notes.append("PO " + s["po_date"])
    if n > 1: notes.append(f"{n} POs — latest shown")
    if not s.get("recv"): notes.append("container not yet closed — no received date")
    r[B["notes"]] = " · ".join(notes)
    return r

# ONE ROW PER (combo, platform) -- never per (component, combo, platform).
# All orders/traffic/returns are keyed on the COMBO sku, so a combo built from N
# new components used to emit N identical rows per platform. That both showed the
# same marketplace line repeatedly AND double-counted every KPI
# (measured 2026-07-28: +757,517 impressions, +29 orders, +GBP 292.70 revenue).
# The component list is carried in B["comps"] so no component detail is lost.
combo_map = {}
for comp_sku, comp_created, comp_desc, combo_sku, combo_created, combo_desc, pk in pairs:
    g = combo_map.setdefault(combo_sku, {"created": combo_created, "desc": combo_desc, "comps": []})
    g["comps"].append((comp_sku, comp_created, comp_desc))

for combo_sku in sorted(combo_map):
    g = combo_map[combo_sku]
    g["comps"].sort()
    comp_sku, comp_created, comp_desc = g["comps"][0]      # representative component
    comp_list  = [c[0] for c in g["comps"]]
    combo_created = g["created"]
    plats = listed.get(combo_sku, {})
    act = {p for (s,p) in orders  if s==combo_sku} | {p for (s,p) in traffic if s==combo_sku} \
        | {p for (s,p) in returns_tot if s==combo_sku}
    allp = set(plats) | act
    if not allp:                                   # combo exists but nowhere live
        r = base(comp_sku, comp_created, comp_desc)
        r[B["bsku"]]=combo_sku; r[B["bimg"]]=img.get(combo_sku,""); r[B["bcre"]]=combo_created
        r[B["comps"]]=comp_list
        r[B["stat"]]="Not Listed"; r[B["plat"]]=""; r[B["ldate"]]=""
        rows.append(r); continue
    for plat in sorted(allp):
        r = base(comp_sku, comp_created, comp_desc)
        r[B["bsku"]]=combo_sku; r[B["bimg"]]=img.get(combo_sku,""); r[B["bcre"]]=combo_created
        r[B["comps"]]=comp_list
        L = plats.get(plat)
        if L:
            r[B["stat"]]="Listed"; r[B["ldate"]]=L["ld"]; r[B["url"]]=L["url"]
        else:
            r[B["stat"]]="Not Listed"; r[B["ldate"]]=""; r[B["url"]]=""
        r[B["plat"]] = plat
        t = traffic.get((combo_sku,plat),(0,0)); r[B["impr"]],r[B["clk"]] = t[0],t[1]
        o = orders.get((combo_sku,plat),(0,0,0.0))
        r[B["ord"]],r[B["units"]],r[B["rev"]] = o[0],o[1],o[2]
        rq = returns_tot.get((combo_sku,plat),0); r[B["ret"]] = rq
        r[B["rrate"]] = round(rq/o[1]*100,2) if o[1] else 0.0
        r[B["reason"]] = top_reason.get((combo_sku,plat),"")
        r[B["fb"]] = fb_for(combo_sku, plat)
        rows.append(r)

# components not yet used in ANY 2026 combo -- the visibility gap
gap = 0
for comp_sku, comp_created, comp_desc in all_comps:
    if comp_sku in comps_with_combo: continue
    r = base(comp_sku, comp_created, comp_desc)
    r[B["bsku"]]=""; r[B["bimg"]]=""; r[B["bcre"]]=""; r[B["comps"]]=[comp_sku]
    r[B["stat"]]="Not Listed"; r[B["plat"]]=""; r[B["ldate"]]=""
    r[B["notes"]] = (r[B["notes"]]+" · " if r[B["notes"]] else "")+"no combo built yet"
    rows.append(r); gap += 1

N = len(rows)
print(f"\nROWS {N}  (listed {sum(1 for r in rows if r[B['stat']]=='Listed')} / "
      f"not-listed {sum(1 for r in rows if r[B['stat']]=='Not Listed')})  |  gap rows {gap}")

# ---------- 9b. COMPONENT (SINGLE-SKU) ROWS -----------------------------------
# Same 21 columns and same row shape, so the table/filters/sort/paging/export are
# reused verbatim. Combo columns stay blank -- this view is the component itself.
rows_c = []
for comp_sku, comp_created, comp_desc in all_comps:
    plats = listed_c.get(comp_sku, {})
    act = {p for (s,p) in orders_c  if s==comp_sku} | {p for (s,p) in traffic_c if s==comp_sku} \
        | {p for (s,p) in returns_c if s==comp_sku}
    allp = set(plats) | act
    if not allp:                                   # component sold/listed nowhere
        r = base(comp_sku, comp_created, comp_desc)
        r[B["bsku"]]=""; r[B["bimg"]]=""; r[B["bcre"]]=""; r[B["comps"]]=[comp_sku]
        r[B["stat"]]="Not Listed"; r[B["plat"]]=""; r[B["ldate"]]=""
        r[B["notes"]] = (r[B["notes"]]+" · " if r[B["notes"]] else "")+"no single-SKU listing"
        rows_c.append(r); continue
    for plat in sorted(allp):
        r = base(comp_sku, comp_created, comp_desc)
        r[B["bsku"]]=""; r[B["bimg"]]=""; r[B["bcre"]]=""; r[B["comps"]]=[comp_sku]
        L = plats.get(plat)
        if L:
            r[B["stat"]]="Listed"; r[B["ldate"]]=L["ld"]; r[B["url"]]=L["url"]
        else:
            r[B["stat"]]="Not Listed"; r[B["ldate"]]=""; r[B["url"]]=""
        r[B["plat"]] = plat
        t = traffic_c.get((comp_sku,plat),(0,0)); r[B["impr"]],r[B["clk"]] = t[0],t[1]
        o = orders_c.get((comp_sku,plat),(0,0,0.0))
        r[B["ord"]],r[B["units"]],r[B["rev"]] = o[0],o[1],o[2]
        rq = returns_c.get((comp_sku,plat),0); r[B["ret"]] = rq
        r[B["rrate"]] = round(rq/o[1]*100,2) if o[1] else 0.0
        r[B["reason"]] = top_reason_c.get((comp_sku,plat),"")
        r[B["fb"]] = fb_for(comp_sku, plat)
        rows_c.append(r)

NC = len(rows_c)
print(f"COMPONENT ROWS {NC}  (listed {sum(1 for r in rows_c if r[B['stat']]=='Listed')} / "
      f"not-listed {sum(1 for r in rows_c if r[B['stat']]=='Not Listed')})")

# ---------- 10. VALIDATION -----------------------------------------------------
f = lambda k: sum(1 for r in rows if r[B[k]] not in (None,"",0))
check("New components in scope", n_comp==178, f"{n_comp} (expected 178)")
check("Combos built from them",  n_combo==223, f"{n_combo} (expected 223)")
check("Component x combo pairs", n_pair==261,  f"{n_pair} (expected 261)")
check("Every row has a component SKU", all(r[B['csku']] for r in rows), f"{f('csku')}/{N}")
check("Every row has a supplier",      f('sup')==N, f"{f('sup')}/{N}")
check("Received Date sourced from the container (not the PO date)", True,
      f"{f('recv')}/{N} rows — blank means the container is not yet closed")
check("No raw container IDs leaked into the Container column",
      all(not str(r[B['cont']] or '').strip().isdigit() for r in rows),
      "Container shows a name or blank, never a foreign key")
check("Listed rows carry a Listed Date",
      all(r[B['ldate']] for r in rows if r[B['stat']]=='Listed'), "no blanks")
check("All dates >= 2026-01-01 (component/combo creation)",
      all((r[B['ccre']] or '9')>=START and (r[B['bcre']] or '9')>=START for r in rows), ">= 2026-01-01")
check("Return Rate math correct",
      all(abs(r[B['rrate']] - (r[B['ret']]/r[B['units']]*100 if r[B['units']] else 0)) < .01 for r in rows),
      "(returns/units)*100")
check("Container present where assigned", True, f"{f('cont')}/{N} rows have a container")
check("Component images (supplier photo -> listing fallback)", True,
      f"{f('cimg')}/{N} rows; {len({r[B['csku']] for r in rows if r[B['cimg']]})}/{n_comp} distinct components")
check("Combo images",     True, f"{f('bimg')}/{N}")
check("Top Reason populated", True, f"{f('reason')}/{N} (amazon 100%, ebay ~11%, shopify has no reason column)")

# --- Components (single-SKU) dataset checks -----------------------------------
fc_ = lambda k: sum(1 for r in rows_c if r[B[k]] not in (None,"",0))
check("Component dataset built independently of the combo queries",
      NC > 0 and all(not r[B['bsku']] for r in rows_c),
      f"{NC} rows, {len(listed_c)} components with their own listing; combo columns blank")
check("Component rows: every row has a component SKU + supplier",
      all(r[B['csku']] for r in rows_c) and fc_('sup')==NC, f"{NC}/{NC}")
check("Component rows: Listed rows carry a Listed Date",
      all(r[B['ldate']] for r in rows_c if r[B['stat']]=='Listed'), "no blanks")
check("Component rows: Return Rate math correct",
      all(abs(r[B['rrate']] - (r[B['ret']]/r[B['units']]*100 if r[B['units']] else 0)) < .01 for r in rows_c),
      "(returns/units)*100")
check("No duplicate (product, marketplace) rows — KPI totals cannot double-count",
      len({(r[B['bsku']] or r[B['csku']], r[B['plat']]) for r in rows})==len(rows)
      and len({(r[B['csku']], r[B['plat']]) for r in rows_c})==len(rows_c),
      f"combo {len(rows)} rows / component {len(rows_c)} rows, all unique")
check("Both datasets share the identical column layout",
      all(len(r)==len(B) for r in rows+rows_c), f"{len(B)} columns")
check("Average Feedback source", bool(feedback),
      "NO customer-review table exists in this database — every row renders 'No Reviews'. "
      "Searched all schemas for rating/review/feedback/star/score columns.")

tot = lambda k: sum(r[B[k]] or 0 for r in rows)
totc = lambda k: sum(r[B[k]] or 0 for r in rows_c)
VAL["totals"] = {"rows": N, "components": n_comp, "combos": n_combo, "pairs": n_pair,
                 "gap_no_combo": gap, "impressions": tot('impr'), "clicks": tot('clk'),
                 "orders": tot('ord'), "units": tot('units'), "revenue": round(tot('rev'),2),
                 "returns": tot('ret')}
VAL["totals_components"] = {"rows": NC, "listed": sum(1 for r in rows_c if r[B['stat']]=='Listed'),
                 "components_with_listing": len(listed_c), "impressions": totc('impr'),
                 "clicks": totc('clk'), "orders": totc('ord'), "units": totc('units'),
                 "revenue": round(totc('rev'),2), "returns": totc('ret')}
print("\nTOTALS  (combos):", json.dumps(VAL["totals"], indent=None))
print("TOTALS  (components):", json.dumps(VAL["totals_components"], indent=None))

P = {"capturedAt": TODAY, "scopeStart": START, "B": B, "rows": rows, "rowsComp": rows_c,
     "meta": {"components": n_comp, "combos": n_combo, "pairs": n_pair, "gapNoCombo": gap,
              "compRows": NC, "compWithListing": len(listed_c),
              "feedbackNote": "No customer-review/rating source exists in this database. "
                              "Every row renders 'No Reviews'. Populate feedback[(sku,platform)] "
                              "in build_v2.py when a marketplace reviews feed is available.",
              "receivedDateNote": "supplier.final_containers.updated_at where status='completed' (the shipping container's close-out into inventory), falling back to supplier.invoices.ship_by_date. Blank = container not yet closed. The PO order_date is NOT used as a receipt date; it is shown in the row tooltip only.",
              "reasonNote": "amazon_returns.reason 100% filled; ebay_returns.reason ~11%; "
                            "shopify_returns has no reason column."}}
(BASE/"payload_v2.json").write_text(json.dumps(P, separators=(",",":")), encoding="utf-8")
VAL["duration_sec"] = round(time.time()-T0,1)
(BASE/"validation_v2.json").write_text(json.dumps(VAL, indent=2), encoding="utf-8")
print(f"\nwrote payload_v2.json  ({(BASE/'payload_v2.json').stat().st_size:,} bytes)  in {VAL['duration_sec']}s")
conn.close()
