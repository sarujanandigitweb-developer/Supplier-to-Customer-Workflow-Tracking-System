#!/usr/bin/env python3
"""
build_listing_driven.py — rebuild the dashboard-v1 master tracking payload so that
EVERY row is a product with a real Listing Date (listing_data.created_at) on/after
2026-01-01. Products without an in-window listing are EXCLUDED entirely.

This replaces the activity-union model (which also emitted "Not Listed" rows that
had orders but no listing date). Per the manager's requirement:
  "fetch only the products whose Listing Date (created_at in listing_data) is from
   2026-01-01 up to the present. Display all the details for those products only."

Row grain  : one (combo SKU x marketplace-platform) that HAS >=1 in-window,
             child, non-wrong listing. Listing Date = earliest such created_at.
Lineage    : identical to the original dashboard —
             nc       = component SKUs first received on/after 2026-01-01
                        (supplier schema; cached in component_meta.psv)
             universe = every '+'-combo SKU in listing_data or order_transaction
             qc       = combos containing >=1 new component
Attach     : orders/traffic/returns matched by (combo, platform); image + URL from
             the same listing row (so the link always matches the row).
Sources    : public.listing_data (DRIVER), public.order_transaction,
             public.traffic_data, public.ppc_performance, public.amazon/ebay/
             shopify_returns. Component attrs from component_meta.psv.
Self-contained + idempotent: never reads the current PAYLOAD; only splices into HTML.
"""
import re, json
from pathlib import Path
from datetime import date
import psycopg2

BASE  = Path(__file__).resolve().parent
PAGE  = BASE.parent / "dashboard-v1" / "index.html"
META  = BASE / "component_meta.psv"
START = "2026-01-01"
DB = dict(host="149.28.134.54", port="5435", dbname="order_management_copy",
          user="temp_user", password="12we34rt")

# ---- component metadata (sku|descr|supplier|container|po|qty|recv|arrived|expected)
comp = {}
for line in META.read_text(encoding="utf-8").splitlines():
    if not line.strip() or line.startswith(">"):
        continue
    f = (line.split("|") + [""] * 9)[:9]
    comp[f[0]] = dict(desc=f[1], supplier=f[2], container=f[3], po=f[4],
                      qty=f[5], recv=f[6], arrived=f[7] == "1", expected=f[8])
nc = sorted(comp)
print(f"component metadata: {len(nc)} new components")

conn = psycopg2.connect(connect_timeout=30, **DB); conn.autocommit = True
cur = conn.cursor()

# ---- lineage (public tables only; nc seeded from the cached list) -------------
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

PLATSQL = """CASE WHEN lower({c}) LIKE '%%amazon%%'  THEN 'amazon'
                  WHEN lower({c}) LIKE '%%ebay%%'    THEN 'ebay'
                  WHEN lower({c}) LIKE '%%shopify%%' THEN 'shopify'
                  WHEN lower({c}) LIKE '%%b&q%%'     THEN 'b&q'
                  WHEN lower({c}) LIKE '%%wayfair%%' THEN 'wayfair'
                  ELSE 'other' END"""

# ---- DRIVER: (combo, platform) that HAS an in-window child listing -------------
# Listing Date business rule = earliest in-window created_at; carry that row's
# ref_id / url / image / title / marketplace / status flags.
cur.execute(f"""
WITH lw AS (
  SELECT sku AS combo, {PLATSQL.format(c='which_channel_name')} AS platform,
         created_at, ref_id, listing_url, main_image_url, title, market_place,
         COALESCE(is_deleted,0)::int AS is_deleted, COALESCE(is_ended,0)::int AS is_ended,
         ROW_NUMBER() OVER (PARTITION BY sku, {PLATSQL.format(c='which_channel_name')}
                            ORDER BY created_at ASC, ref_id) AS rn
  FROM public.listing_data
  WHERE sku IN (SELECT sku FROM t_qc)
    AND created_at >= %(start)s      -- THE listing-date filter (created_at = "Listing Date")
    AND is_child = 1 AND wrong_sku = 0
)
SELECT combo, platform,
       MIN(created_at)::date::text                              AS listing_date,
       MAX(ref_id)         FILTER (WHERE rn=1)                  AS ref_id,
       MAX(listing_url)    FILTER (WHERE rn=1)                  AS url,
       MAX(main_image_url) FILTER (WHERE rn=1)                  AS img,
       MAX(title)          FILTER (WHERE rn=1)                  AS title,
       MAX(market_place)   FILTER (WHERE rn=1)                  AS market_place,
       MAX(is_deleted)     FILTER (WHERE rn=1)                  AS is_deleted,
       MAX(is_ended)       FILTER (WHERE rn=1)                  AS is_ended,
       COUNT(DISTINCT market_place)                             AS regions
FROM lw GROUP BY combo, platform;""", {"start": START})
rows_src = cur.fetchall()
listed = {(r[0], r[1]): dict(ld=r[2], ref=r[3] or "", url=r[4] or "", img=r[5] or "",
                             title=r[6] or "", mkt=r[7] or "", del_=r[8], end=r[9], reg=r[10])
          for r in rows_src}
print(f"in-window listed rows (combo x platform): {len(listed)}"
      f"  urls={sum(1 for v in listed.values() if v['url'].startswith('http'))}"
      f"  imgs={sum(1 for v in listed.values() if v['img'].startswith('http'))}")

# ---- combo creation date = earliest listing over ALL history (separate from ldate)
cur.execute("""SELECT sku, MIN(created_at)::date::text FROM public.listing_data
               WHERE sku IN (SELECT sku FROM t_qc) AND sku LIKE '%+%' GROUP BY sku;""")
combo_created = dict(cur.fetchall())

# ---- combo product name: best (longest non-empty) title for the combo across ALL
# its listing rows. eBay rows are frequently title-less while the Shopify row for
# the same combo carries the real name — so a per-(combo,platform) title is often
# blank. This combo-level fallback fills those blanks.
cur.execute("""
  SELECT sku, title FROM (
    SELECT sku, title,
           ROW_NUMBER() OVER (PARTITION BY sku ORDER BY length(title) DESC) AS rn
    FROM public.listing_data
    WHERE sku IN (SELECT sku FROM t_qc) AND COALESCE(title,'') <> ''
  ) z WHERE rn = 1;""")
combo_name = dict(cur.fetchall())

# ---- orders per (combo, platform) --------------------------------------------
cur.execute(f"""SELECT sku, {PLATSQL.format(c='source_name')},
  count(DISTINCT order_id), SUM(quantity)::int, ROUND(SUM(order_total)::numeric,2)::float8
  FROM public.order_transaction
  WHERE sku IN (SELECT sku FROM t_qc) AND order_status='Completed' AND order_date >= %(start)s
  GROUP BY 1,2;""", {"start": START})
orders = {(s, p): (o, u, r) for s, p, o, u, r in cur.fetchall()}

# ---- traffic per (combo, platform): sum over the combo/platform's in-window ref_ids
cur.execute(f"""
WITH refmap AS (
  SELECT DISTINCT ref_id, sku AS combo, {PLATSQL.format(c='which_channel_name')} AS platform
  FROM public.listing_data
  WHERE sku IN (SELECT sku FROM t_qc) AND created_at >= %(start)s AND is_child=1 AND wrong_sku=0),
t AS (
  SELECT ref_id, COALESCE(impression,0) AS impr, COALESCE(click,0) AS clk
  FROM public.traffic_data WHERE date >= %(start)s
  UNION ALL
  SELECT ref_id, COALESCE(impressions,0), COALESCE(clicks,0)
  FROM public.ppc_performance WHERE date >= %(start)s)
SELECT m.combo, m.platform, SUM(t.impr)::bigint, SUM(t.clk)::bigint
FROM refmap m JOIN t ON t.ref_id = m.ref_id GROUP BY 1,2;""", {"start": START})
traffic = {(s, p): (i, c) for s, p, i, c in cur.fetchall()}

# ---- returns per (combo, platform) -------------------------------------------
cur.execute(f"""
WITH co AS (SELECT order_id, sku, SUM(quantity)::int AS oqty FROM public.order_transaction
            WHERE sku IN (SELECT sku FROM t_qc) GROUP BY 1,2),
r AS (
  SELECT ar.sku AS combo, 'amazon' AS platform, ar.qty::int AS qty
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
SELECT combo, platform, SUM(COALESCE(qty,0))::int FROM r GROUP BY 1,2;""", {"start": START})
returns = {(s, p): q for s, p, q in cur.fetchall()}
print(f"orders keys={len(orders)}  traffic keys={len(traffic)}  returns keys={len(returns)}")

# ---- representative new component per combo (parts INTERSECT nc, first sorted) --
ncset = set(nc)
def parts_of(combo):
    return sorted(p.strip() for p in combo.split("+") if p.strip() in ncset)

# ---- assemble rows in the exact 26-column B schema ---------------------------
B = dict(rid=0, cont=1, arr=2, sup=3, csku=4, cdesc=5, qty=6, crecv=7, combo=8, cname=9,
         used=10, ccreate=11, cqty=12, status=13, plat=14, url=15, ldate=16, impr=17,
         clk=18, ord=19, rev=20, units=21, ret=22, dsrc=23, updated=24, notes=25)
PLATLBL = {"amazon": "Amazon", "ebay": "eBay", "shopify": "Website",
           "b&q": "B&Q", "wayfair": "Wayfair", "other": "Other"}
today = date.today().isoformat()

rows, n = [], 0
for (combo, plat) in sorted(listed):
    L = listed[(combo, plat)]
    parts = parts_of(combo)
    rep = parts[0] if parts else ""
    cm = comp.get(rep, {})
    o = orders.get((combo, plat), (0, 0, 0.0))
    t = traffic.get((combo, plat), (0, 0))
    def num(x):
        try: return int(x)
        except Exception: return ""
    r = [None] * 26
    n += 1
    r[B["rid"]]     = f"REC-{n:05d}"
    r[B["cont"]]    = cm.get("container", "")
    r[B["arr"]]     = "Arrived" if cm.get("arrived") else "In Transit"
    r[B["sup"]]     = cm.get("supplier", "")
    r[B["csku"]]    = rep
    r[B["cdesc"]]   = cm.get("desc", "")
    r[B["qty"]]     = num(cm.get("qty"))
    r[B["crecv"]]   = cm.get("recv", "")
    r[B["combo"]]   = combo
    r[B["cname"]]   = L["title"] or combo_name.get(combo, "")   # fallback to combo-level best title
    r[B["used"]]    = ", ".join(parts)
    r[B["ccreate"]] = combo_created.get(combo, "") or ""
    r[B["cqty"]]    = L["img"]                       # Product Image URL
    r[B["status"]]  = "Listed"                       # every row is listed by construction
    r[B["plat"]]    = plat
    r[B["url"]]     = L["url"]                        # clickable marketplace URL
    r[B["ldate"]]   = L["ld"]                         # in-window listing date (2026-01-01+)
    r[B["impr"]]    = t[0]
    r[B["clk"]]     = t[1]
    r[B["ord"]]     = o[0]
    r[B["rev"]]     = o[2]
    r[B["units"]]   = o[1]
    r[B["ret"]]     = returns.get((combo, plat), 0)
    r[B["dsrc"]]    = "Postgres + " + PLATLBL.get(plat, plat) + " API"
    r[B["updated"]] = today
    exp = cm.get("expected", "")
    r[B["notes"]]   = ("Expected completion " + exp) if (exp and not cm.get("arrived")) else ""
    rows.append(r)

P = {"capturedAt": today,
     "window": {"start": START, "end": today},
     "note": "Only products with a Listing Date (listing_data.created_at) >= 2026-01-01.",
     "rows": rows}

html = PAGE.read_text(encoding="utf-8")
m = re.search(r'(const PAYLOAD\s*=\s*)(\{.*?\})(;\s*\n)', html, re.S)
html = html[:m.start(2)] + json.dumps(P, separators=(",", ":")) + html[m.end(2):]
PAGE.write_text(html, encoding="utf-8")

# ---- report ------------------------------------------------------------------
print(f"\nROWS = {len(rows)}   (every row has a Listing Date >= {START})")
print("distinct combos :", len({r[B['combo']] for r in rows}))
print("distinct comps  :", len({r[B['csku']] for r in rows if r[B['csku']]}))
print("revenue         :", round(sum(float(r[B['rev']] or 0) for r in rows), 2))
print("orders          :", sum(int(r[B['ord']] or 0) for r in rows))
print("units           :", sum(int(r[B['units']] or 0) for r in rows))
print("returns         :", sum(int(r[B['ret']] or 0) for r in rows))
print("impressions     :", sum(int(r[B['impr']] or 0) for r in rows))
print("urls (http)     :", sum(1 for r in rows if str(r[B['url']]).startswith('http')))
print("images (http)   :", sum(1 for r in rows if str(r[B['cqty']]).startswith('http')))
ld = [r[B['ldate']] for r in rows]
print("listing date min/max:", min(ld), "/", max(ld))
print("rows with ldate < window:", sum(1 for x in ld if x < START))
print("rows with blank ldate  :", sum(1 for x in ld if not x))
print("rows NOT 'Listed'      :", sum(1 for r in rows if r[B['status']] != 'Listed'))
conn.close()
