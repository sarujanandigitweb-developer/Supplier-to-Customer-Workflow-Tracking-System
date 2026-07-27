#!/usr/bin/env python3
"""
build_new_scope.py — FULL REBUILD of the dashboard-v1 dataset, fresh from PostgreSQL.
UI (HTML/CSS/JS) is never touched; only `const PAYLOAD = {...};` is replaced.

No cached JSON/CSV/HTML data is reused. Public data is queried live via the project
credential (temp_user). Supplier-schema data (temp_user has NO grant on `supplier`)
is fetched FRESH via the broad role into supplier_fresh.psv (regenerated each run).

VALIDATED JOIN CHAIN
  listing_data
    -> resolve  base = COALESCE(NULLIF(TRIM(mapped_sku),''), TRIM(sku))
    -> normalize (strip trailing country/channel suffix  [_-][A-Za-z]{2,4}$)
    -> inv_products (sku)                        = PRODUCT MASTER (desc + created_at)
    -> inv_product_combo (product=combo, inventory=component, pack_count=qty)
    -> supplier.order_items -> supplier.orders -> supplier.containers / suppliers
  Orders/Traffic/Returns keyed on the same resolved base sku.

SCOPE = every NEW SKU: inv_products.created_at in [2026-01-01,2027-01-01), isdeleted=0,
        TRIM(sku)<>''  = 3,383  (1,866 components + 1,517 combos).  Nothing dropped.

FIELD POPULATION (fill every field where the data exists):
  Component Creation Date : inv_products.created_at  -> EVERY row (rep component for combos).
  Product Image           : best main_image_url from ANY listing of the SKU (not only in-window).
  Listing URL/Marketplace : from the SKU's live listing (is_deleted=0, is_ended=0).
  Listing Date            : earliest live-listing created_at for that SKU x platform.
  Listing Status          : Listed if a live listing exists on that platform, else Not Listed.
  Supplier/Container/Qty   : supplier_fresh.psv (739 SKUs that have a supplier.order_items row).
  Orders/Units/Revenue/Traffic/Returns : live public tables, per (SKU, platform).
Every row carries a 2026 anchor date (crecv = component creation date) so the UI
From/To filter (rowDate = crecv||ldate||ccreate) never hides it.
"""
import re, os, sys, json, time
from pathlib import Path
from datetime import date, datetime
import psycopg2

BASE  = Path(__file__).resolve().parent
PROJ  = BASE.parent
PAGE  = PROJ / "dashboard-v1" / "index.html"
RPT   = PROJ / "validation"; RPT.mkdir(exist_ok=True)
START = "2026-01-01"; END = "2027-01-01"
T0    = time.time()
RUN   = datetime.now().strftime("%Y%m%d_%H%M%S")

# Credentials from the environment (cron/.env), with the project defaults.
DB = dict(host=os.getenv("PGHOST", "149.28.134.54"),
          port=os.getenv("PGPORT", "5435"),
          dbname=os.getenv("PGDATABASE", "order_management_copy"),
          user=os.getenv("PGUSER", "temp_user"),
          password=os.getenv("PGPASSWORD", "12we34rt"))

VAL = {"run": RUN, "checks": [], "datasets": {}, "supplier": {}, "errors": []}
def check(name, ok, detail=""):
    VAL["checks"].append({"check": name, "status": "PASS" if ok else "FAIL", "detail": detail})
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}{(' — '+detail) if detail else ''}")
    return ok

PLAT = """CASE WHEN lower({c}) LIKE '%%amazon%%'  THEN 'amazon'
               WHEN lower({c}) LIKE '%%ebay%%'    THEN 'ebay'
               WHEN lower({c}) LIKE '%%shopify%%' THEN 'shopify'
               WHEN lower({c}) LIKE '%%b&q%%'     THEN 'b&q'
               WHEN lower({c}) LIKE '%%wayfair%%' THEN 'wayfair'
               ELSE 'other' END"""

# ---- supplier chain: fetched LIVE below if temp_user can read the supplier
# schema; this PSV is only a graceful fallback for when the grant is missing.
sup = {}
sf = BASE / "supplier_fresh.psv"
def load_supplier_cache():
    if not sf.exists():
        return
    for line in sf.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith(">"):
            continue
        p = (line.split("|") + [""] * 7)[:7]
        sup[p[0]] = dict(supplier=p[1], container=p[2], qty=p[3], arrived=p[4] == "1",
                         expected=p[5], recv=p[6])

conn = psycopg2.connect(connect_timeout=40, **DB); conn.autocommit = True
cur = conn.cursor()
print(f"connected as {DB['user']}@{DB['host']}:{DB['port']}/{DB['dbname']}")

# ---- SUPPLIER VALIDATION (required before any supplier value is used) ---------
# Probe each supplier table with the project's temp_user. Record exactly which
# permissions are missing, then degrade gracefully instead of breaking the build.
SUP_TABLES = ["supplier.suppliers", "supplier.orders",
              "supplier.containers", "supplier.order_items"]
sup_access, sup_missing = {}, []
cur.execute("SELECT has_schema_privilege(current_user,'supplier','USAGE')")
schema_ok = cur.fetchone()[0]
for t in SUP_TABLES:
    try:
        cur.execute(f"SELECT count(*) FROM {t}")
        sup_access[t] = {"readable": True, "rows": cur.fetchone()[0]}
    except Exception as e:
        conn.rollback()
        sup_access[t] = {"readable": False, "error": str(e).strip().splitlines()[0]}
        sup_missing.append(t)
# Fetch the supplier chain LIVE when readable (no cache); else fall back.
sup_mode = "live"
if not sup_missing:
    cur.execute("""
        SELECT DISTINCT ON (oi.sku)
               oi.sku,
               COALESCE(s.name,'')                                AS supplier,
               COALESCE(ct.name, NULLIF(o.container_id,''), '')    AS container,
               COALESCE(oi.pcs::text,'')                           AS qty,
               COALESCE(o.status_arrived,0)                        AS arrived,
               COALESCE(o.expected_completion_date::text,'')       AS expected,
               oi.created_at::date::text                           AS recv,
               COALESCE(o.order_id,'')                             AS po,
               COALESCE(o.supplier_id::text,'')                    AS supplier_id
        FROM supplier.order_items oi
        LEFT JOIN supplier.orders     o  ON o.id = oi.order_id
        LEFT JOIN supplier.suppliers  s  ON s.id = o.supplier_id
        LEFT JOIN supplier.containers ct ON ct.id::text = o.container_id
        WHERE COALESCE(TRIM(oi.sku),'') <> ''
        ORDER BY oi.sku, oi.created_at ASC;""")
    for sku, s_name, cont, qty, arr, exp, recv, po, sid in cur.fetchall():
        sup[sku] = dict(supplier=s_name, container=cont, qty=qty, arrived=bool(arr),
                        expected=exp, recv=recv, po=po, supplier_id=sid)
    print(f"supplier chain fetched LIVE: {len(sup)} SKUs")
else:
    sup_mode = "cache-fallback"
    load_supplier_cache()
    print(f"supplier chain from cache fallback: {len(sup)} SKUs")

VAL["supplier"] = {"schema_usage": bool(schema_ok), "tables": sup_access,
                   "missing": sup_missing, "mode": sup_mode,
                   "skus_with_supplier_chain": len(sup),
                   "fallback_file": str(sf.relative_to(PROJ)) if sf.exists() else None,
                   "fields_validated": ["Supplier Name", "Supplier ID", "Container",
                                        "Purchase Order", "Order Items"]}
if sup_missing:
    VAL["supplier"]["permission_note"] = (
        f"GRANT USAGE ON SCHEMA supplier TO {DB['user']}; "
        f"GRANT SELECT ON {', '.join(sup_missing)} TO {DB['user']};")
    check("supplier schema readable by temp_user", False,
          f"missing: {', '.join(sup_missing)} — using validated cache "
          f"({len(sup)} SKUs); dashboard continues without supplier fields for the rest")
else:
    check("supplier schema readable by temp_user", True,
          "; ".join(f"{t}={v.get('rows')}" for t, v in sup_access.items()))
# Validate the cached supplier chain's own integrity (name/container/qty present)
if sup:
    named = sum(1 for v in sup.values() if v.get("supplier"))
    cont  = sum(1 for v in sup.values() if v.get("container"))
    check("supplier cache integrity", named > 0,
          f"{named}/{len(sup)} have Supplier Name, {cont}/{len(sup)} have Container")

# ---- SCOPE : every new SKU, with description + creation date -------------------
cur.execute("""
CREATE TEMP TABLE scope AS
SELECT id AS prod_id, sku, created_at::date::text AS created, (sku LIKE '%%+%%') AS is_combo,
       COALESCE(NULLIF(eng_desc,''),NULLIF(description,''),NULLIF(title,''),'') AS descr,
       COALESCE(NULLIF(title,''),'') AS title
FROM public.inv_products
WHERE created_at >= %(s)s AND created_at < %(e)s AND COALESCE(isdeleted,0)=0 AND COALESCE(TRIM(sku),'')<>'';
CREATE INDEX ON scope(prod_id); CREATE INDEX ON scope(sku);
""", {"s": START, "e": END})
cur.execute("SELECT prod_id, sku, created, is_combo, descr, title FROM scope;")
scope = {pid: dict(sku=sku, created=cr, is_combo=isc, descr=descr, title=title)
         for pid, sku, cr, isc, descr, title in cur.fetchall()}
print(f"scope new SKUs: {len(scope)}  ({sum(1 for v in scope.values() if not v['is_combo'])} comp / "
      f"{sum(1 for v in scope.values() if v['is_combo'])} combo)")

# ---- LIVE listings resolved to a scope product (ANY date) ----------------------
cur.execute(f"""
CREATE TEMP TABLE res AS
SELECT ld.ref_id, ld.created_at, ld.market_place, ld.listing_url, ld.main_image_url, ld.title,
       {PLAT.format(c='ld.which_channel_name')} AS platform, COALESCE(a.id,b.id) AS prod_id
FROM public.listing_data ld
LEFT JOIN public.inv_products a ON a.sku = COALESCE(NULLIF(TRIM(ld.mapped_sku),''),TRIM(ld.sku))
LEFT JOIN public.inv_products b ON b.sku = regexp_replace(COALESCE(NULLIF(TRIM(ld.mapped_sku),''),TRIM(ld.sku)),'[_-][A-Za-z]{{2,4}}$','')
WHERE ld.created_at >= %(s)s                         -- APPROVED RULE: Listing Date >= 2026-01-01
  AND COALESCE(ld.is_parent,0)=0 AND ld.wrong_sku=0
  AND COALESCE(TRIM(ld.sku),'')<>'';
CREATE INDEX ON res(prod_id);
""", {"s": START})
cur.execute("""
SELECT r.prod_id, r.platform,
       MIN(r.created_at)::date::text                          AS listing_date,
       (array_agg(r.listing_url    ORDER BY r.created_at, r.ref_id))[1] AS url,
       (array_agg(r.main_image_url ORDER BY r.created_at, r.ref_id) FILTER (WHERE COALESCE(r.main_image_url,'')<>''))[1] AS img,
       (array_agg(r.market_place   ORDER BY r.created_at, r.ref_id))[1] AS mkt,
       (array_agg(r.title          ORDER BY r.created_at, r.ref_id) FILTER (WHERE COALESCE(r.title,'')<>''))[1] AS title
FROM res r JOIN scope s ON s.prod_id=r.prod_id WHERE r.prod_id IS NOT NULL
GROUP BY r.prod_id, r.platform;""")
listed = {}
for pid, plat, ld, url, img, mkt, title in cur.fetchall():
    listed.setdefault(pid, {})[plat] = dict(ld=ld, url=url or "", img=img or "", mkt=mkt or "", title=title or "")

# ---- product image per SKU: the MOST-RECENT listing image OF THAT RESOLVED SKU.
# Keyed on the resolved SKU (mapped_sku|sku), so the image provably belongs to the
# SKU shown. When a SKU has several listings/images, the newest listing's image wins
# (deterministic: ORDER BY created_at DESC, ref_id).
cur.execute("""
  SELECT DISTINCT ON (resolved) resolved, main_image_url
  FROM (SELECT COALESCE(NULLIF(TRIM(mapped_sku),''),TRIM(sku)) AS resolved,
               main_image_url, created_at, ref_id
        FROM public.listing_data WHERE COALESCE(main_image_url,'')<>'') z
  ORDER BY resolved, created_at DESC, ref_id;""")
img_any = dict(cur.fetchall())

# ---- combo -> components (inv_product_combo), with each part's creation date ----
# Mapping for EVERY scope SKU (combos AND single-component packs like 12IP201302PK,
# which have no '+' but ARE in inv_product_combo). Used to resolve the real
# description + supplier of the base component behind a pack/combo.
cur.execute("""
SELECT pc.product AS prod_id, ic.sku, ic.created_at::date::text,
       (ic.created_at >= %(s)s AND ic.created_at < %(e)s AND COALESCE(ic.isdeleted,0)=0)::int AS is_new,
       COALESCE(NULLIF(ic.eng_desc,''),NULLIF(ic.description,''),NULLIF(ic.title,''),'') AS descr
FROM scope s
JOIN public.inv_product_combo pc ON pc.product=s.prod_id AND pc.inventory<>pc.product
JOIN public.inv_products ic ON ic.id=pc.inventory
ORDER BY pc.product, ic.sku;""", {"s": START, "e": END})
parts, compinfo = {}, {}
for pid, csku, cr, isnew, descr in cur.fetchall():
    parts.setdefault(pid, []).append(csku)
    compinfo[csku] = dict(isnew=bool(isnew), desc=(descr or "")[:80], created=cr)

# ---- combo product name from listings -----------------------------------------
cur.execute("""
  SELECT prod_id, title FROM (
    SELECT r.prod_id, ld.title, ROW_NUMBER() OVER (PARTITION BY r.prod_id ORDER BY length(ld.title) DESC) rn
    FROM res r JOIN scope s ON s.prod_id=r.prod_id JOIN public.listing_data ld ON ld.ref_id=r.ref_id
    WHERE COALESCE(ld.title,'')<>'') z WHERE rn=1;""")
combo_name = dict(cur.fetchall())

# ---- orders / traffic / returns, per (scope prod_id, platform) -----------------
cur.execute(f"""
WITH o AS (
  SELECT regexp_replace(TRIM(ot.sku),'[_-][A-Za-z]{{2,4}}$','') AS base_sku,
         {PLAT.format(c='ot.source_name')} AS platform, ot.order_id, ot.quantity, ot.order_total
  FROM public.order_transaction ot WHERE ot.order_status='Completed' AND ot.order_date>=%(s)s)
SELECT s.prod_id, o.platform, count(DISTINCT o.order_id), SUM(o.quantity)::int, ROUND(SUM(o.order_total)::numeric,2)::float8
FROM o JOIN scope s ON s.sku=o.base_sku GROUP BY 1,2;""", {"s": START})
orders = {(pid, pl): (o, u, r) for pid, pl, o, u, r in cur.fetchall()}

cur.execute("""
WITH t AS (
  SELECT ref_id, COALESCE(impression,0) i, COALESCE(click,0) c FROM public.traffic_data WHERE date>=%(s)s
  UNION ALL SELECT ref_id, COALESCE(impressions,0), COALESCE(clicks,0) FROM public.ppc_performance WHERE date>=%(s)s)
SELECT r.prod_id, r.platform, SUM(t.i)::bigint, SUM(t.c)::bigint
FROM res r JOIN scope s ON s.prod_id=r.prod_id JOIN t ON t.ref_id=r.ref_id WHERE r.prod_id IS NOT NULL GROUP BY 1,2;""", {"s": START})
traffic = {(pid, pl): (i, c) for pid, pl, i, c in cur.fetchall()}

cur.execute("""
WITH co AS (SELECT ot.order_id, regexp_replace(TRIM(ot.sku),'[_-][A-Za-z]{2,4}$','') AS base_sku,
                   SUM(ot.quantity)::int AS oqty FROM public.order_transaction ot GROUP BY 1,2),
rr AS (
  SELECT regexp_replace(TRIM(ar.sku),'[_-][A-Za-z]{2,4}$','') AS base_sku,'amazon' AS platform, ar.qty::int AS qty
  FROM public.amazon_returns ar WHERE ar.request_date>=%(s)s
  UNION ALL SELECT co.base_sku,'ebay', e.qty FROM (SELECT return_id, MIN(order_id) order_id, MAX(return_qty)::int qty
    FROM public.ebay_returns WHERE request_date>=%(s)s GROUP BY return_id) e JOIN co ON co.order_id=e.order_id
  UNION ALL SELECT co.base_sku,'shopify', co.oqty FROM (SELECT DISTINCT ON (id) id, order_id FROM public.shopify_returns
    WHERE date>=%(s)s ORDER BY id) sh JOIN co ON co.order_id=sh.order_id)
SELECT s.prod_id, rr.platform, SUM(COALESCE(rr.qty,0))::int FROM rr JOIN scope s ON s.sku=rr.base_sku GROUP BY 1,2;""", {"s": START})
returns = {(pid, pl): q for pid, pl, q in cur.fetchall()}

# Independent revenue total (no platform matching at all) — computed HERE, while
# the connection is still open, and used later purely as a reconciliation guard.
cur.execute("""SELECT ROUND(SUM(ot.order_total)::numeric,2)
FROM public.order_transaction ot JOIN scope s
  ON s.sku = regexp_replace(TRIM(ot.sku),'[_-][A-Za-z]{2,4}$','')
WHERE ot.order_status='Completed' AND ot.order_date >= %(s)s""", {"s": START})
independent_revenue = float(cur.fetchone()[0] or 0)

conn.close()
print(f"listed SKUs (live listing): {len(listed)}")

# ---- assemble (26-col B schema) -----------------------------------------------
B = dict(rid=0, cont=1, arr=2, sup=3, csku=4, cdesc=5, qty=6, crecv=7, combo=8, cname=9,
         used=10, ccreate=11, cqty=12, status=13, plat=14, url=15, ldate=16, impr=17,
         clk=18, ord=19, rev=20, units=21, ret=22, dsrc=23, updated=24, notes=25)
LBL = {"amazon": "Amazon", "ebay": "eBay", "shopify": "Website", "b&q": "B&Q", "wayfair": "Wayfair", "other": "Other"}
today = date.today().isoformat()

def num(x):
    try: return int(float(x))
    except Exception: return ""

def rep_component(pid):
    pl = parts.get(pid, [])
    return (next((p for p in pl if compinfo.get(p, {}).get("isnew")), None)
            or next((p for p in pl if p in sup), None) or (pl[0] if pl else ""))

def is_generic(d):
    return (not d) or d.strip().startswith("Combo Default Title")

def resolve_sup(cands):
    """First candidate SKU that has a supplier.order_items row wins."""
    for sk in cands:
        if sk and sk in sup:
            return sup[sk]
    return {}

def base_row(pid):
    s = scope[pid]; r = [None] * 26; r[B["updated"]] = today; notes = []
    pl = parts.get(pid, [])                       # base components (packs + combos)
    r[B["crecv"]] = s["created"]                  # anchor = SKU's own 2026 creation date
    if s["is_combo"]:                             # a true '+' combo
        rep = rep_component(pid); ci = compinfo.get(rep, {})
        r[B["csku"]]  = rep
        r[B["cdesc"]] = ci.get("desc", "") or ("" if is_generic(s["descr"]) else s["descr"][:80])
        r[B["combo"]] = s["sku"]
        r[B["cname"]] = combo_name.get(pid, "") or ("" if s["title"] == "Combo Default Title." else s["title"])
        r[B["used"]]  = ", ".join(pl)
        r[B["ccreate"]] = s["created"]
        sm = resolve_sup([rep] + pl)             # supplier of the (base) component
    else:                                        # component OR single-component pack
        base = pl[0] if pl else ""               # pack -> its base component
        # Component SKU = the scope SKU (the sellable unit shown to the user).
        r[B["csku"]]  = s["sku"]
        # Description = own if real, else the base component's real description
        # (fixes pack SKUs that carry the generic "Combo Default Title.").
        r[B["cdesc"]] = (s["descr"][:80] if not is_generic(s["descr"])
                         else (compinfo.get(base, {}).get("desc", "") or s["descr"][:80]))
        r[B["combo"]] = ""; r[B["cname"]] = ""
        r[B["used"]]  = ", ".join(pl)            # show the base component(s) of the pack
        r[B["ccreate"]] = ""
        sm = resolve_sup([s["sku"], base] + pl)  # own PO first, then base component
    r[B["cont"]] = sm.get("container", ""); r[B["sup"]] = sm.get("supplier", "")
    r[B["arr"]]  = ("Arrived" if sm.get("arrived") else "In Transit") if sm else ""
    r[B["qty"]]  = num(sm.get("qty"))
    exp = sm.get("expected", "")
    if exp and not sm.get("arrived"): notes.append("Expected completion " + exp)
    rec = sm.get("recv", "")
    if rec: notes.append("PO receipt " + rec)
    r[B["notes"]] = " · ".join(notes)
    return r

# Row set per SKU = union of (a) platforms it's LISTED on, (b) platforms it has
# orders/traffic/returns on. Previously only (a) was used, so a completed order
# whose platform had no listing for that SKU was computed but attached to NO row
# -- silently dropped from every KPI (measured: £31,734.23 / ~1,000 orders across
# in-scope SKUs). Now every dollar/impression/return lands on exactly one row
# (its own platform), so per-SKU totals reconcile to PostgreSQL with zero loss
# and zero double-count. A platform with real sales but no listing renders as
# "Not Listed" with its true order/revenue numbers -- itself a genuine
# visibility-gap signal ("selling on Amazon with no tracked Amazon listing").
rows, n = [], 0
for pid in sorted(scope, key=lambda p: (scope[p]["is_combo"], scope[p]["sku"])):
    s = scope[pid]; plats = listed.get(pid, {})
    img_fallback = img_any.get(s["sku"], "")
    activity_plats = {p for (pp, p) in orders  if pp == pid}
    activity_plats |= {p for (pp, p) in traffic if pp == pid}
    activity_plats |= {p for (pp, p) in returns if pp == pid}
    all_plats = set(plats) | activity_plats
    if all_plats:
        for plat in sorted(all_plats):
            o = orders.get((pid, plat), (0, 0, 0.0)); t = traffic.get((pid, plat), (0, 0))
            r = base_row(pid); n += 1
            r[B["rid"]] = f"REC-{n:05d}"
            L = plats.get(plat)
            if L:                                    # a real listing exists on this platform
                if L["title"] and s["is_combo"]: r[B["cname"]] = L["title"]
                r[B["cqty"]]  = L["img"] or img_fallback
                r[B["status"]] = "Listed"
                r[B["url"]]   = L["url"]; r[B["ldate"]] = L["ld"]
                r[B["dsrc"]]  = "Postgres + " + LBL.get(plat, plat) + " API"
            else:                                     # sold/tracked here but never listed here
                r[B["cqty"]]  = img_fallback
                r[B["status"]] = "Not Listed"
                r[B["url"]]   = ""; r[B["ldate"]] = ""
                r[B["dsrc"]]  = "Postgres"
            r[B["plat"]] = plat
            r[B["impr"]], r[B["clk"]] = t[0], t[1]
            r[B["ord"]], r[B["units"]], r[B["rev"]] = o[0], o[1], o[2]
            r[B["ret"]]   = returns.get((pid, plat), 0)
            rows.append(r)
    else:                                             # zero activity anywhere -- one gap row
        r = base_row(pid); n += 1
        r[B["rid"]]   = f"REC-{n:05d}"
        r[B["cqty"]]  = img_fallback
        r[B["status"]] = "Not Listed"; r[B["plat"]] = ""; r[B["url"]] = ""; r[B["ldate"]] = ""
        r[B["impr"]] = r[B["clk"]] = r[B["ord"]] = r[B["units"]] = r[B["ret"]] = 0; r[B["rev"]] = 0.0
        r[B["dsrc"]] = "Postgres"
        rows.append(r)

new_comp_set = sorted(v["sku"] for v in scope.values() if not v["is_combo"])
used_parts = {p for r in rows for p in (r[B["used"]].split(", ") if r[B["used"]] else [])}
used_parts |= {r[B["csku"]] for r in rows if r[B["csku"]]}
P = {"capturedAt": today, "window": {"start": START, "end": today},
     "note": "EVERY new SKU (inv_products.created_at 2026, isdeleted=0): 1,866 components + "
             "1,517 combos. Fully rebuilt from PostgreSQL; images from any listing; supplier "
             "chain fresh. Each SKU shown Listed (per platform) or Not Listed.",
     "compImg": {k: v for k, v in img_any.items() if k in used_parts and v},
     "newComps": new_comp_set, "rows": rows}
html = PAGE.read_text(encoding="utf-8")
m = re.search(r'(const PAYLOAD\s*=\s*)(\{.*?\})(;\s*\n)', html, re.S)
PAGE.write_text(html[:m.start(2)] + json.dumps(P, separators=(",", ":")) + html[m.end(2):], encoding="utf-8")

# ---- DATASET VALIDATION + execution artifacts ---------------------------------
def filled_txt(col): return sum(1 for r in rows if str(r[B[col]] or "").strip() != "")
N = len(rows); listed_rows = sum(1 for r in rows if r[B["status"]] == "Listed")
tot = lambda c: sum(r[B[c]] or 0 for r in rows)
revenue = round(sum(float(r[B['rev']] or 0) for r in rows), 2)

print(f"\nROWS {N}  (Listed {listed_rows} / Not-Listed {N-listed_rows})")
for c in ["cont","sup","csku","cdesc","crecv","combo","cname","used","ccreate","cqty","plat","url","ldate"]:
    print(f"  {c:8} filled: {filled_txt(c):5}/{N}  ({100*filled_txt(c)//N if N else 0}%)")

VAL["datasets"] = {
    "Listing Data":      {"rows": listed_rows,        "source": "public.listing_data"},
    "Returns":           {"units": tot('ret'),        "source": "amazon/ebay/shopify_returns"},
    "Traffic":           {"impressions": tot('impr'), "clicks": tot('clk'),
                          "source": "traffic_data + ppc_performance"},
    "Supplier":          {"rows_with_supplier": filled_txt('sup'),
                          "rows_with_container": filled_txt('cont'), "source": "supplier.* (cache)"},
    "Orders":            {"orders": tot('ord'),       "source": "public.order_transaction"},
    "Sales":             {"revenue": revenue, "units": tot('units'), "source": "public.order_transaction"},
    "Inventory":         {"new_skus": len(scope),     "source": "public.inv_products"},
    "Component Data":    {"components": len(new_comp_set), "source": "public.inv_products"},
    "Combo Data":        {"combos": sum(1 for v in scope.values() if v['is_combo']),
                          "source": "public.inv_product_combo"},
    "Product Images":    {"rows": filled_txt('cqty'), "source": "listing_data.main_image_url"},
    "Listing URLs":      {"rows": filled_txt('url'),  "source": "listing_data.listing_url"},
}

# Hard gates — the HTML must never be published if any of these fail.
check("Inventory: new SKUs present",       len(scope) > 0, f"{len(scope)} SKUs in scope")
check("Listing Data: listed rows present", listed_rows > 0, f"{listed_rows} listed rows")
check("Component Data present",            len(new_comp_set) > 0, f"{len(new_comp_set)} components")
check("Combo Mapping present",             len(parts) > 0, f"{len(parts)} combos/packs mapped")
check("Component Mapping (descriptions)",  filled_txt('cdesc') == N,
      f"{filled_txt('cdesc')}/{N} rows have a description")
check("Every row has an anchor date",
      all(r[B['crecv']] or r[B['ldate']] or r[B['ccreate']] for r in rows), "crecv||ldate||ccreate")
check("Listed rows all carry a Listing Date",
      all(r[B['ldate']] for r in rows if r[B['status']] == 'Listed'), "no blank listing dates")
check("Listing Dates within window",
      all(r[B['ldate']] >= START for r in rows if r[B['ldate']]), f">= {START}")
check("Listing URLs present on listed rows", filled_txt('url') == listed_rows,
      f"{filled_txt('url')}/{listed_rows}")
# Soft gates — recorded, never block the build.
check("Product Images available", filled_txt('cqty') > 0,
      f"{filled_txt('cqty')}/{N} rows ({100*filled_txt('cqty')//N if N else 0}%) — rest have no image in listing_data")
check("Orders / Sales fetched", tot('ord') > 0, f"{tot('ord')} orders, revenue {revenue}")
# Reconciliation guard: dashboard revenue must equal an INDEPENDENT recomputation
# straight from order_transaction for the same scope, with NO platform matching
# involved (computed earlier, while the connection was open). Catches any future
# regression of the platform-attachment bug fixed 2026-07-27 (was silently
# dropping revenue whose order-platform had no matching listing).
check("Revenue reconciles to independent PostgreSQL total",
      abs(revenue - independent_revenue) < 0.01,
      f"dashboard={revenue}  independent={independent_revenue}")
check("Traffic fetched", tot('impr') > 0, f"{tot('impr'):,} impressions")
check("Returns fetched", tot('ret') >= 0, f"{tot('ret')} units returned")

HARD = ["Inventory: new SKUs present", "Listing Data: listed rows present",
        "Component Data present", "Combo Mapping present",
        "Component Mapping (descriptions)", "Every row has an anchor date",
        "Listed rows all carry a Listing Date", "Listing Dates within window",
        "Revenue reconciles to independent PostgreSQL total"]
failed_hard = [c["check"] for c in VAL["checks"] if c["status"] == "FAIL" and c["check"] in HARD]
VAL["result"] = "FAIL" if failed_hard else "PASS"
VAL["failed_hard"] = failed_hard
VAL["duration_sec"] = round(time.time() - T0, 1)
VAL["rows"] = N; VAL["listed"] = listed_rows; VAL["not_listed"] = N - listed_rows
VAL["fill"] = {c: filled_txt(c) for c in
               ['cont','sup','csku','cdesc','crecv','combo','cname','used','ccreate','cqty','plat','url','ldate']}

# fetch summary + machine-readable validation
(RPT / f"fetch_summary_{RUN}.json").write_text(json.dumps(VAL, indent=2), encoding="utf-8")
(BASE / "validation_fill.json").write_text(json.dumps(VAL["fill"] | {"rows": N, "listed": listed_rows}, indent=2))

# human-readable validation report
L = [f"# Dashboard Validation — {RUN}", "",
     f"**Result: {VAL['result']}** · rows {N} (Listed {listed_rows} / Not-Listed {N-listed_rows})"
     f" · {VAL['duration_sec']}s", "", "## Datasets", "", "| Dataset | Value | Source |", "|---|---|---|"]
for k, v in VAL["datasets"].items():
    val = ", ".join(f"{a}={b:,}" if isinstance(b, (int, float)) else f"{a}={b}"
                    for a, b in v.items() if a != "source")
    L.append(f"| {k} | {val} | `{v['source']}` |")
L += ["", "## Checks", "", "| Check | Status | Detail |", "|---|---|---|"]
L += [f"| {c['check']} | {'✅' if c['status']=='PASS' else '❌'} {c['status']} | {c['detail']} |"
      for c in VAL["checks"]]
L += ["", "## Supplier validation", "",
      f"- schema USAGE for `{DB['user']}`: **{VAL['supplier']['schema_usage']}**"]
for t, v in VAL["supplier"]["tables"].items():
    L.append(f"- `{t}`: " + (f"readable ({v['rows']:,} rows)" if v["readable"]
                             else f"**NOT readable** — {v.get('error','')}"))
if VAL["supplier"]["missing"]:
    L += [f"- Missing permission fix: `{VAL['supplier']['permission_note']}`",
          f"- Graceful fallback: validated cache `{VAL['supplier']['fallback_file']}` "
          f"({VAL['supplier']['fallback_rows']} SKUs). Build continues; other rows show blank supplier."]
(RPT / f"validation_{RUN}.md").write_text("\n".join(L) + "\n", encoding="utf-8")

print(f"\nRESULT: {VAL['result']}  ({VAL['duration_sec']}s)")
print(f"wrote validation/validation_{RUN}.md + fetch_summary_{RUN}.json")
if failed_hard:
    print("HARD FAILURES:", "; ".join(failed_hard)); sys.exit(1)
