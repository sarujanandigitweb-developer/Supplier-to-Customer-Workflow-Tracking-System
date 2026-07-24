#!/usr/bin/env python3
"""
fix_tracking_data.py — rebuild the dashboard-v1 master tracking payload using the
ORIGINAL dashboard's proven extraction logic (sql/listings.sql, orders.sql,
traffic.sql, returns.sql), and add real product image + product URL.

Corrects four data defects introduced by dashboard-v1-sql/*.sql:
  D1 LISTING SCOPE   04_listings.sql had NO created_at filter -> 12,880 of 14,977
                     listing rows (86%) predated the window, back to 2019-06-26.
                     Original listings.sql scopes: created_at >= :start AND is_child=1.
  D2 LISTING DATE    followed from D1 (dates from 2019-2025 shown as Listing Date).
  D3 ARRIVAL DATE    01_components.sql used COALESCE(expected_completion_date,...)
                     -> a FORECAST (max 2026-08-31) rendered as an actual arrival,
                     hence "04-Aug-2026". No arrival-date column exists in
                     supplier.containers or supplier.orders at all.
  D4 URL / IMAGE     the URL column held a bare ref_id ("314148529895"), not a
                     link, and there was no image at all. listing_data carries
                     listing_url (100% populated) and main_image_url (99.6%).

Lineage (identical to the original dashboard):
  nc       = component SKUs first received on/after 2026-01-01  (supplier schema)
  universe = every '+'-joined combo SKU in listing_data or order_transaction
  qc       = combos containing >=1 nc component
The `supplier` schema is NOT readable by this role, so nc + the arrival facts are
read from nc_arrival.csv (exported via MCP with a supplier-capable role).
"""
import re, json, csv, sys
from pathlib import Path
from decimal import Decimal
import psycopg2

BASE   = Path(__file__).resolve().parent
PAGE   = BASE.parent / "dashboard-v1" / "index.html"
NCFILE = BASE / "nc_arrival.csv"
START  = "2026-01-01"

DB = dict(host="149.28.134.54", port="5435", dbname="order_management_copy",
          user="temp_user", password="12we34rt")

# ---------------------------------------------------------------- nc + arrival
nc, arrival = [], {}
raw = [l for l in NCFILE.read_text(encoding="utf-8").splitlines() if l and not l.startswith(">")]
for rec in "".join(raw).split(";"):
    if not rec.strip():
        continue
    sku, arr, exp = (rec.split(",") + ["", ""])[:3]
    nc.append(sku)
    arrival[sku] = (arr == "1", exp or "")
print(f"nc components: {len(nc)}  (arrived={sum(1 for v in arrival.values() if v[0])})")

conn = psycopg2.connect(connect_timeout=30, **DB); conn.autocommit = True
cur = conn.cursor()

# Rebuild the lineage server-side from the nc list.
cur.execute("CREATE TEMP TABLE t_nc(sku text PRIMARY KEY);")
cur.executemany("INSERT INTO t_nc VALUES (%s) ON CONFLICT DO NOTHING;", [(s,) for s in nc])
cur.execute("""CREATE TEMP TABLE t_qc AS
  WITH universe AS (
    SELECT DISTINCT sku FROM public.listing_data      WHERE wrong_sku=0 AND sku LIKE '%%+%%'
    UNION SELECT DISTINCT sku FROM public.order_transaction WHERE sku LIKE '%%+%%')
  SELECT DISTINCT u.sku FROM universe u
  CROSS JOIN LATERAL (SELECT trim(x) AS part FROM unnest(string_to_array(u.sku,'+')) x) p
  WHERE p.part IN (SELECT sku FROM t_nc);""")
cur.execute("CREATE INDEX ON t_qc(sku); SELECT count(*) FROM t_qc;")
print("qualifying combos:", cur.fetchone()[0])

PLAT = """CASE WHEN lower({c}) LIKE '%%amazon%%'  THEN 'amazon'
               WHEN lower({c}) LIKE '%%ebay%%'    THEN 'ebay'
               WHEN lower({c}) LIKE '%%shopify%%' THEN 'shopify'
               WHEN lower({c}) LIKE '%%b&q%%'     THEN 'b&q'
               WHEN lower({c}) LIKE '%%wayfair%%' THEN 'wayfair'
               ELSE 'other' END"""

# ---- D1/D2/D4: listings — ORIGINAL scope (created_at >= START AND is_child=1) --
# Listing Date business rule (original): l.created_at::date. At the (combo,
# platform) grain the earliest in-window listing wins, and its ref_id/url/image
# are carried, so the link always matches the date shown.
cur.execute(f"""
WITH s AS (
  SELECT sku,
         {PLAT.format(c='which_channel_name')} AS platform,
         created_at, ref_id, listing_url, main_image_url, market_place,
         ROW_NUMBER() OVER (PARTITION BY sku, {PLAT.format(c='which_channel_name')}
                            ORDER BY created_at ASC, ref_id) AS rn
  FROM public.listing_data
  WHERE sku IN (SELECT sku FROM t_qc)
    AND created_at >= %(start)s          -- D1: the filter dashboard-v1 was missing
    AND is_child = 1                     -- D1: sellable variant, as in listings.sql
)
SELECT s.sku, s.platform,
       MIN(s.created_at)::date::text                                   AS listing_date,
       MAX(s.ref_id)        FILTER (WHERE s.rn=1)                      AS ref_id,
       MAX(s.listing_url)   FILTER (WHERE s.rn=1)                      AS url,
       MAX(s.main_image_url)FILTER (WHERE s.rn=1)                      AS img,
       COUNT(DISTINCT s.market_place)                                  AS regions
FROM s GROUP BY 1,2;""", {"start": START})
listings = {}
for sku, plat, ld, ref, url, img, reg in cur.fetchall():
    listings[(sku, plat)] = dict(ld=ld, ref=ref or "", url=url or "", img=img or "", reg=reg)
print(f"in-window listings (combo x platform): {len(listings)}"
      f"  urls={sum(1 for v in listings.values() if v['url'].startswith('http'))}"
      f"  imgs={sum(1 for v in listings.values() if v['img'].startswith('http'))}")

# ---- orders / traffic / returns — unchanged original logic (revenue must match) --
cur.execute(f"""SELECT sku, {PLAT.format(c='source_name')} AS platform,
  count(DISTINCT order_id), SUM(quantity)::int, ROUND(SUM(order_total)::numeric,2)::float8
  FROM public.order_transaction
  WHERE sku IN (SELECT sku FROM t_qc) AND order_status='Completed' AND order_date >= %(start)s
  GROUP BY 1,2;""", {"start": START})
orders = {(s, p): (o, u, r) for s, p, o, u, r in cur.fetchall()}

cur.execute(f"""
WITH refids AS (   -- one row per ref_id: no join fan-out (same fix as sql/traffic.sql)
  SELECT ref_id, MAX(sku) AS sku, MAX({PLAT.format(c='which_channel_name')}) AS platform
  FROM public.listing_data
  WHERE wrong_sku=0 AND sku IN (SELECT sku FROM t_qc) GROUP BY ref_id)
SELECT r.sku, r.platform, SUM(t.impr)::bigint, SUM(t.clk)::bigint FROM (
  SELECT ref_id, COALESCE(impression,0) AS impr, COALESCE(click,0) AS clk
  FROM public.traffic_data WHERE date >= %(start)s
  UNION ALL
  SELECT ref_id, COALESCE(impressions,0), COALESCE(clicks,0)
  FROM public.ppc_performance WHERE date >= %(start)s) t
JOIN refids r ON r.ref_id = t.ref_id GROUP BY 1,2;""", {"start": START})
traffic = {(s, p): (i, c) for s, p, i, c in cur.fetchall()}

cur.execute(f"""
WITH co AS (SELECT order_id, sku, SUM(quantity)::int AS oqty FROM public.order_transaction
            WHERE sku IN (SELECT sku FROM t_qc) GROUP BY 1,2),
r AS (
  SELECT ar.sku, 'amazon' AS platform, ar.qty::int AS qty
  FROM public.amazon_returns ar
  WHERE ar.sku IN (SELECT sku FROM t_qc) AND ar.request_date >= %(start)s
  UNION ALL
  SELECT co.sku, 'ebay', e.qty FROM (
    SELECT return_id, MIN(order_id) AS order_id, MAX(return_qty)::int AS qty
    FROM public.ebay_returns WHERE request_date >= %(start)s GROUP BY return_id) e
  JOIN co ON co.order_id = e.order_id
  UNION ALL
  SELECT co.sku, 'shopify', co.oqty FROM (
    SELECT DISTINCT ON (id) id, order_id FROM public.shopify_returns
    WHERE date >= %(start)s ORDER BY id) s
  JOIN co ON co.order_id = s.order_id)
SELECT sku, platform, SUM(COALESCE(qty,0))::int FROM r GROUP BY 1,2;""", {"start": START})
returns = {(s, p): q for s, p, q in cur.fetchall()}
print(f"orders keys={len(orders)}  traffic keys={len(traffic)}  returns keys={len(returns)}")

# ------------------------------------------------------------------ rebuild rows
# Descriptive (non-metric) attributes -- supplier, container, PO, qty received,
# combo name/parts -- are carried from the pristine payload; only the defective
# fields are recomputed. orig_payload.json is the pre-fix snapshot so this script
# stays idempotent (re-running never compounds edits).
html = PAGE.read_text(encoding="utf-8")
m = re.search(r'(const PAYLOAD\s*=\s*)(\{.*?\})(;\s*\n)', html, re.S)
P = json.loads(m.group(2))
B = dict(rid=0, cont=1, arr=2, sup=3, csku=4, cdesc=5, qty=6, crecv=7, combo=8, cname=9,
         used=10, ccreate=11, cqty=12, status=13, plat=14, url=15, ldate=16, impr=17,
         clk=18, ord=19, rev=20, units=21, ret=22, dsrc=23, updated=24, notes=25)

old = json.loads((BASE / "orig_payload.json").read_text(encoding="utf-8"))["rows"]
PLATLBL = {"amazon": "Amazon", "ebay": "eBay", "shopify": "Website",
           "b&q": "B&Q", "wayfair": "Wayfair", "other": "Other"}

combo_meta, comp_meta = {}, {}
for r in old:
    if r[B["combo"]]:
        combo_meta.setdefault(r[B["combo"]], r)
    if r[B["csku"]]:
        comp_meta.setdefault(r[B["csku"]], r)

# Representative new component per combo, taken from the combo SKU itself
# (parts INTERSECT nc) rather than from the old payload -- this is the same
# component->combo rule the original dashboard's mapping query uses.
ncset = set(nc)
cur.execute("SELECT sku FROM t_qc;")
combo_parts, used_comps = {}, set()
for (csku,) in cur.fetchall():
    parts = [p.strip() for p in csku.split("+") if p.strip() in ncset]
    if parts:
        combo_parts[csku] = sorted(parts)
        used_comps.update(parts)

# Row key set = in-window listings UNION all commercial activity, plus every
# qualifying combo (so unlisted combos still appear as a Visibility Gap).
keys = set(listings) | set(orders) | set(traffic) | set(returns)
keys |= {(c, "") for c in combo_parts if not any(k[0] == c for k in keys)}
# ...plus the orphan rows: new components used in NO qualifying combo. The
# original page had 273 of these; dropping them under-counted the Components KPI.
orphans = sorted(s for s in ncset if s not in used_comps)
print(f"combos with new parts={len(combo_parts)}  components used={len(used_comps)}"
      f"  orphan components={len(orphans)}")

work = [(c, p, False) for c, p in sorted(keys)] + [(o, "", True) for o in orphans]
rows, n = [], 0
for combo, plat, is_orphan in work:
    if is_orphan:
        src = comp_meta.get(combo)          # `combo` holds the component SKU here
        if src is None:
            continue
        r = list(src)
        r[B["combo"]] = ""; r[B["cname"]] = ""; r[B["used"]] = ""; r[B["ccreate"]] = ""
        combo, plat = "", ""
    else:
        src = combo_meta.get(combo)
        if src is None:
            continue
        r = list(src)
        parts = combo_parts.get(combo) or []
        rep = parts[0] if parts else r[B["csku"]]
        cm = comp_meta.get(rep)
        if cm:   # re-point the component columns at the combo's real new component
            for f in ("csku", "cdesc", "sup", "cont", "qty", "crecv"):
                r[B[f]] = cm[B[f]]
        r[B["used"]] = ", ".join(parts) if parts else r[B["used"]]
    n += 1
    r[B["rid"]] = f"REC-{n:05d}"
    csku = r[B["csku"]]
    arrived, expected = arrival.get(csku, (False, ""))

    # D3: never present a forecast as an actual arrival. No arrival date exists in
    # the DB, so show the status; the forecast goes in its own labelled column.
    r[B["arr"]] = "Arrived" if arrived else "In Transit"
    r[B["notes"]] = ("Expected completion " + expected) if (expected and not arrived) else ""

    L = listings.get((combo, plat))
    r[B["status"]] = "Listed" if L else "Not Listed"
    r[B["plat"]]   = plat
    r[B["ldate"]]  = L["ld"] if L else ""          # D2: in-window listing date only
    r[B["url"]]    = L["url"] if L else ""         # D4: real clickable marketplace URL
    r[B["cqty"]]   = L["img"] if L else ""         # D4: reuse slot -> product image URL

    o = orders.get((combo, plat), (0, 0, 0.0))
    r[B["ord"]], r[B["units"]], r[B["rev"]] = o[0], o[1], o[2]
    t = traffic.get((combo, plat), (0, 0))
    r[B["impr"]], r[B["clk"]] = t[0], t[1]
    r[B["ret"]] = returns.get((combo, plat), 0)

    cc = r[B["ccreate"]] or ""
    r[B["ccreate"]] = cc if re.match(r"^(19|20)\d\d-", cc) else ""   # drop corrupt '0025'
    r[B["dsrc"]] = "Postgres" + (f" + {PLATLBL.get(plat, plat)} API" if plat else "")
    r[B["updated"]] = P.get("capturedAt", "")
    rows.append(r)

P["rows"] = rows
P["capturedAt"] = __import__("datetime").date.today().isoformat()
P["window"] = {"start": START, "end": P["capturedAt"]}
html = html[:m.start(2)] + json.dumps(P, separators=(",", ":")) + html[m.end(2):]
PAGE.write_text(html, encoding="utf-8")

listed = sum(1 for r in rows if r[B["status"]] == "Listed")
print(f"\nrows {len(old)} -> {len(rows)}   listed={listed}")
print("revenue  ", round(sum(float(r[B['rev']] or 0) for r in rows), 2))
print("orders   ", sum(int(r[B['ord']] or 0) for r in rows))
print("units    ", sum(int(r[B['units']] or 0) for r in rows))
print("returns  ", sum(int(r[B['ret']] or 0) for r in rows))
print("impress  ", sum(int(r[B['impr']] or 0) for r in rows))
print("urls     ", sum(1 for r in rows if str(r[B['url']]).startswith('http')))
print("images   ", sum(1 for r in rows if str(r[B['cqty']]).startswith('http')))
bad = [r[B['ldate']] for r in rows if r[B['ldate']] and r[B['ldate']] < START]
fut = [r[B['arr']] for r in rows if re.match(r'^\d{4}-', str(r[B['arr']] or ''))]
print("listing dates before window:", len(bad), " | raw dates left in arrival col:", len(fut))
conn.close()
