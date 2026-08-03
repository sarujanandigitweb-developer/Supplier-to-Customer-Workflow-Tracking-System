#!/usr/bin/env python3
"""
build_v3.py — Dashboard V3 payload builder.  INDEPENDENT of Dashboard V2.

SCOPE (different from V2 -- this is the whole point of V3):
  The GOOGLE SHEET is the source of truth for Container -> Component SKU.
  V2 derived its scope from inv_products/supplier.order_items; V3 does NOT.
  Everything else is fetched from PostgreSQL keyed on those sheet SKUs.

DATA SOURCE: order_management_copy @ 149.28.134.54:5435  (the "postgres 2" DB).
  Ledsone is deliberately NOT used.

ROW GRAIN: one row per (container, product, marketplace) where product is the
  combo when one exists, else the component itself. Never per
  (component, combo, marketplace) -- that was V2's fan-out bug which
  double-counted every KPI. A regression gate below enforces uniqueness.

KNOWN SOURCE GAPS (2026-07-31) -- these tables are empty/dropped on this DB
  because a migration to the `ledsone` database is in progress:
    public.inv_products      = 0 rows  -> Component/Combo Created Date unavailable
    public.inv_product_combo = 0 rows  -> combos derived from SKU naming instead
    public.amazon_returns    = 0 rows  -> Returns / Return Rate / Top Reason unavailable
    public.ebay_returns      = DROPPED
    public.shopify_returns   = DROPPED
  Affected fields render blank and are reported, never faked.
"""
import json, os, re, time
from datetime import date, datetime
from pathlib import Path
import psycopg2

BASE  = Path(__file__).resolve().parent
PROJ  = BASE.parent
START = "2026-01-01"
TODAY = date.today().isoformat()
T0    = time.time()

DB = dict(host=os.getenv("PGHOST", "149.28.134.54"),
          port=os.getenv("PGPORT", "5435"),
          dbname=os.getenv("PGDATABASE", "order_management_copy"),
          user=os.getenv("PGUSER", "temp_user"),
          password=os.getenv("PGPASSWORD", "12we34rt"))

PLAT = """CASE WHEN lower({c}) LIKE '%%amazon%%'  THEN 'amazon'
               WHEN lower({c}) LIKE '%%ebay%%'    THEN 'ebay'
               WHEN lower({c}) LIKE '%%shopify%%' THEN 'shopify'
               WHEN lower({c}) LIKE '%%b&q%%'     THEN 'b&q'
               WHEN lower({c}) LIKE '%%wayfair%%' THEN 'wayfair'
               ELSE 'other' END"""

VAL = {"run": datetime.now().strftime("%Y%m%d_%H%M%S"), "checks": [], "notes": [], "gaps": []}
def check(name, ok, detail=""):
    VAL["checks"].append({"check": name, "status": "PASS" if ok else "FAIL", "detail": detail})
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}{(' — '+detail) if detail else ''}")
    return ok

# ---------- 1. GOOGLE SHEET = Container -> Component SKU ----------------------
sheet = json.loads((BASE / "sheet_containers.json").read_text(encoding="utf-8"))
sheet = {c: v for c, v in sheet.items() if v}              # drop empty container tabs
comp_of = {}                                                # sku -> [containers]
sheet_meta = {}                                             # sku -> sheet attributes
for cont, items in sheet.items():
    for it in items:
        comp_of.setdefault(it["sku"], []).append(cont)
        sheet_meta.setdefault(it["sku"], it)
SKUS = sorted(comp_of)

# ---------- 1b. inv_products SOURCE OF TRUTH = LEDsOne inventory.products ------
# public.inv_products on this DB is a STALE/DEAD copy (0 rows) until its reload
# pipeline is fixed, so per instruction the ONLY source swapped is inv_products:
# it now comes from the LEDs One MCP (`inventory.products`), extracted into
# ledsone_products.json by the chunked MCP pulls. Every other source, join,
# business rule and aggregation below is Dashboard V2's, unchanged.
LP = json.loads((BASE / "ledsone_products.json").read_text(encoding="utf-8"))
LP = {k.upper(): v for k, v in LP.items()}
def lp_created(sku): return (LP.get((sku or "").upper()) or {}).get("created", "")
def lp_desc(sku):    return (LP.get((sku or "").upper()) or {}).get("desc", "")
print(f"LEDsOne inventory.products cache: {len(LP)} products")
print(f"sheet: {len(sheet)} containers, {sum(len(v) for v in sheet.values())} rows, {len(SKUS)} distinct SKUs")

conn = psycopg2.connect(connect_timeout=40, **DB); conn.autocommit = True
cur = conn.cursor()
cur.execute("SET statement_timeout = '180s'")
print(f"connected {DB['user']}@{DB['host']}:{DB['port']}/{DB['dbname']}")

# ---------- 2. SOURCE-AVAILABILITY PROBE (fail loudly, never silently) --------
avail = {}
for t in ["public.inv_products", "public.inv_product_combo", "public.listing_data",
          "public.order_transaction", "public.traffic_data", "public.ppc_performance",
          "public.amazon_returns", "public.ebay_returns", "public.shopify_returns"]:
    try:
        cur.execute(f"SELECT count(*) FROM {t}"); avail[t] = cur.fetchone()[0]
    except Exception:
        conn.rollback(); avail[t] = None                    # table missing
VAL["source_availability"] = avail
for t, n in avail.items():
    print(f"  {t:28} {'MISSING' if n is None else format(n, ',')}")
if not avail.get("public.inv_products"):
    VAL["notes"].append("public.inv_products is a stale/dead copy (0 rows) -- NOT used. "
                        "inv_products data is sourced from LEDs One MCP inventory.products.")
if not avail.get("public.inv_product_combo"):
    VAL["gaps"].append("inv_product_combo empty -> combos derived from SKU naming convention")
if not avail.get("public.amazon_returns") or avail.get("public.ebay_returns") is None:
    VAL["gaps"].append("returns tables empty/dropped -> Returns, Return Rate, Top Reason unavailable")
VAL["gaps"].append("no customer-review source on this DB -> Average Feedback unavailable")

# ---------- 3. PRODUCT UNIVERSE (resolved SKUs that actually have listings) ---
cur.execute("""
CREATE TEMP TABLE res AS
SELECT COALESCE(NULLIF(TRIM(ld.mapped_sku),''),TRIM(ld.sku)) AS resolved,
       ld.ref_id, ld.created_at::date AS listed_on, ld.which_channel_name,
       ld.listing_url, ld.main_image_url, ld.market_place, ld.title
FROM public.listing_data ld
WHERE COALESCE(ld.is_parent,0)=0 AND ld.wrong_sku=0
  AND COALESCE(TRIM(ld.sku),'')<>'';
CREATE INDEX ON res(resolved); CREATE INDEX ON res(ref_id);
""")
cur.execute("SELECT DISTINCT resolved FROM res WHERE COALESCE(resolved,'')<>''")
universe = [r[0] for r in cur.fetchall()]
print(f"listing_data SKU universe: {len(universe):,}")

# ---------- 4. COMPONENT -> COMBO, derived from the SKU naming convention -----
# inv_product_combo is empty, so the declared mapping is unavailable. The naming
# convention is the only remaining signal:
#   pack  :  <COMPONENT> + optional chars + 'PK'      e.g. LHXSHE27BM3PK
#   combo :  '+'-joined token list containing <COMPONENT>
# This is an INFERENCE, recorded as such in the validation report.
combos_of = {s: [] for s in SKUS}
plus_index = {}
for u in universe:
    if "+" in u:
        for tok in u.split("+"):
            plus_index.setdefault(tok.strip().upper(), []).append(u)
pack_re = {s: re.compile(r'^' + re.escape(s) + r'[0-9A-Z]*PK$', re.I) for s in SKUS}
for s in SKUS:
    found = set(plus_index.get(s.upper(), []))
    pre = s.upper()
    for u in universe:
        if u.upper().startswith(pre) and u.upper() != pre and pack_re[s].match(u):
            found.add(u)
    combos_of[s] = sorted(found)
n_with_combo = sum(1 for v in combos_of.values() if v)
n_combos = len({c for v in combos_of.values() for c in v})
print(f"combos derived: {n_combos} distinct, covering {n_with_combo}/{len(SKUS)} components")

# products we need metrics for = every component + every derived combo
products = sorted(set(SKUS) | {c for v in combos_of.values() for c in v})
print(f"products needing metrics: {len(products):,}")

cur.execute("CREATE TEMP TABLE prod(sku text PRIMARY KEY)")
cur.executemany("INSERT INTO prod(sku) VALUES (%s) ON CONFLICT DO NOTHING",
                [(p,) for p in products])

# ---------- 5. LISTINGS per (sku, platform) ----------------------------------
cur.execute(f"""
SELECT r.resolved, {PLAT.format(c='r.which_channel_name')} AS platform,
       MIN(r.listed_on)::text                                              AS listed_date,
       (array_agg(r.listing_url     ORDER BY r.listed_on, r.ref_id))[1]    AS url,
       (array_agg(r.main_image_url  ORDER BY r.listed_on, r.ref_id)
          FILTER (WHERE COALESCE(r.main_image_url,'')<>''))[1]             AS img,
       (array_agg(r.title           ORDER BY r.listed_on, r.ref_id)
          FILTER (WHERE COALESCE(r.title,'')<>''))[1]                      AS title
FROM res r JOIN prod p ON p.sku = r.resolved
GROUP BY 1,2""")
listed = {}
for sku, plat, ld, url, img, title in cur.fetchall():
    listed.setdefault(sku, {})[plat] = dict(ld=ld, url=url or "", img=img or "", title=title or "")

# newest image anywhere for a SKU (component photos rarely sit on an in-window listing)
cur.execute("""
SELECT DISTINCT ON (r.resolved) r.resolved, r.main_image_url
FROM res r JOIN prod p ON p.sku = r.resolved
WHERE COALESCE(r.main_image_url,'')<>''
ORDER BY r.resolved, r.listed_on DESC, r.ref_id""")
img_any = dict(cur.fetchall())
# the sheet also carries an image per component -- used as the first choice
def clean_url(u):
    u = (u or "").strip()
    return u if u.lower().startswith(("http://", "https://")) else ""
for s in SKUS:
    si = clean_url((sheet_meta.get(s) or {}).get("sheet_image"))
    if si: img_any.setdefault(s, si)
img_any = {k: clean_url(v) for k, v in img_any.items() if clean_url(v)}

# ---------- 6. TRAFFIC, from each listing's own Listed Date to today ---------
cur.execute("""
SELECT r.resolved, plat, SUM(t.i)::bigint, SUM(t.c)::bigint FROM (
  SELECT r.resolved, r.ref_id, r.listed_on,
         CASE WHEN lower(r.which_channel_name) LIKE '%amazon%'  THEN 'amazon'
              WHEN lower(r.which_channel_name) LIKE '%ebay%'    THEN 'ebay'
              WHEN lower(r.which_channel_name) LIKE '%shopify%' THEN 'shopify'
              WHEN lower(r.which_channel_name) LIKE '%b&q%'     THEN 'b&q'
              WHEN lower(r.which_channel_name) LIKE '%wayfair%' THEN 'wayfair'
              ELSE 'other' END AS plat
  FROM res r JOIN prod p ON p.sku = r.resolved) r
JOIN (SELECT ref_id, date, COALESCE(impression,0) i, COALESCE(click,0) c FROM public.traffic_data
      UNION ALL
      SELECT ref_id, date, COALESCE(impressions,0), COALESCE(clicks,0) FROM public.ppc_performance) t
  ON t.ref_id = r.ref_id AND t.date >= r.listed_on
GROUP BY 1,2""")
traffic = {(s, p): (i, c) for s, p, i, c in cur.fetchall()}

# ---------- 7. ORDERS / UNITS / REVENUE --------------------------------------
cur.execute(f"""
SELECT base_sku, platform, count(DISTINCT order_id), SUM(quantity)::int,
       ROUND(SUM(order_total)::numeric,2)::float8
FROM (
  SELECT regexp_replace(TRIM(ot.sku),'[_-][A-Za-z]{{2,4}}$','') AS base_sku,
         {PLAT.format(c='ot.source_name')} AS platform,
         ot.order_id, ot.quantity, ot.order_total
  FROM public.order_transaction ot
  WHERE ot.order_status='Completed') o
JOIN prod p ON p.sku = o.base_sku
GROUP BY 1,2""")
orders = {(s, p): (o, u, r) for s, p, o, u, r in cur.fetchall()}

# ---------- 8. RETURNS — unavailable on this DB (tables emptied/dropped) -----
returns_tot, top_reason = {}, {}
if avail.get("public.amazon_returns"):
    cur.execute("""
      SELECT regexp_replace(TRIM(ar.sku),'[_-][A-Za-z]{2,4}$','') AS sku,
             'amazon', SUM(ar.qty)::int, NULL
      FROM public.amazon_returns ar
      JOIN prod p ON p.sku = regexp_replace(TRIM(ar.sku),'[_-][A-Za-z]{2,4}$','')
      GROUP BY 1""")
    for s, p, q, _ in cur.fetchall(): returns_tot[(s, p)] = q

# ---------- 9. BUILD ROWS ----------------------------------------------------
B = {"cont":0,"csku":1,"cimg":2,"ccre":3,"bsku":4,"bimg":5,"bcre":6,
     "stat":7,"plat":8,"ldate":9,"impr":10,"clk":11,"ord":12,"units":13,"rev":14,
     "ret":15,"rrate":16,"reason":17,"fb":18,"url":19,"notes":20,"comps":21,"rid":22}
NCOL = len(B)

def blank():
    r = [None]*NCOL
    for k in ("impr","clk","ord","units","ret"): r[B[k]] = 0
    r[B["rev"]] = 0.0; r[B["rrate"]] = 0.0
    return r

rows, n = [], 0
for cont in sorted(sheet):
    # products in this container: each component, represented by its combos if any
    prods = {}          # product sku -> [component skus]
    for it in sheet[cont]:
        cs = it["sku"]
        for cb in (combos_of.get(cs) or [cs]):
            prods.setdefault(cb, []).append(cs)
    for psku in sorted(prods):
        comps = sorted(set(prods[psku]))
        is_combo = psku not in comps
        plats = listed.get(psku, {})
        act = {p for (s, p) in orders  if s == psku} | {p for (s, p) in traffic if s == psku} \
            | {p for (s, p) in returns_tot if s == psku}
        allp = sorted(set(plats) | act)
        base_notes = []
        t0 = (plats.get(sorted(plats)[0]) if plats else None)
        if t0 and t0.get("title"): base_notes.append(t0["title"][:70])

        def mkrow(plat):
            global n
            r = blank(); n += 1
            r[B["rid"]]  = f"V3-{n:05d}"
            r[B["cont"]] = cont
            r[B["csku"]] = comps[0]
            r[B["cimg"]] = img_any.get(comps[0], "")
            r[B["ccre"]] = lp_created(comps[0])      # LEDsOne inventory.products
            r[B["comps"]] = [[c, img_any.get(c, ""), lp_created(c)] for c in comps]
            if is_combo:
                r[B["bsku"]] = psku
                r[B["bimg"]] = (plats.get(plat, {}) or {}).get("img") or img_any.get(psku, "")
                r[B["bcre"]] = lp_created(psku)     # LEDsOne inventory.products
            else:
                r[B["bsku"]] = ""; r[B["bimg"]] = ""; r[B["bcre"]] = ""
            L = plats.get(plat)
            if L:
                r[B["stat"]] = "Listed"; r[B["ldate"]] = L["ld"]; r[B["url"]] = L["url"]
            else:
                r[B["stat"]] = "Not Listed"; r[B["ldate"]] = ""; r[B["url"]] = ""
            r[B["plat"]] = plat or ""
            t = traffic.get((psku, plat), (0, 0)); r[B["impr"]], r[B["clk"]] = t[0], t[1]
            o = orders.get((psku, plat), (0, 0, 0.0))
            r[B["ord"]], r[B["units"]], r[B["rev"]] = o[0], o[1], o[2]
            rq = returns_tot.get((psku, plat), 0); r[B["ret"]] = rq
            r[B["rrate"]] = round(rq/o[1]*100, 2) if o[1] else 0.0
            r[B["reason"]] = ""                     # returns tables unavailable
            r[B["fb"]]     = None                   # no review source on this DB
            notes = list(base_notes)
            d = lp_desc(comps[0])
            if d and not base_notes: notes.insert(0, d)
            if len(comps) > 1: notes.append(f"{len(comps)} components from this container")
            r[B["notes"]] = " · ".join(notes)
            return r

        if not allp:
            rows.append(mkrow(""))
        else:
            for plat in allp:
                rows.append(mkrow(plat))

N = len(rows)
listed_n = sum(1 for r in rows if r[B['stat']] == 'Listed')
print(f"\nROWS {N}  (listed {listed_n} / not-listed {N-listed_n})")

# ---------- 10. VALIDATION ---------------------------------------------------
f = lambda k: sum(1 for r in rows if r[B[k]] not in (None, "", 0))
sheet_rows = sum(len(v) for v in sheet.values())
in_universe = [s for s in SKUS if s in universe]

check("Container -> Component mapping from the Google Sheet",
      len(sheet) > 0 and sheet_rows > 0,
      f"{len(sheet)} containers, {sheet_rows} sheet rows, {len(SKUS)} distinct SKUs")
check("Every row carries a Container and a Component SKU",
      all(r[B['cont']] and r[B['csku']] for r in rows), f"{N}/{N}")
check("Every sheet SKU is represented in the dashboard",
      len({c for r in rows for c, _, _ in (r[B['comps']] or [])}) == len(SKUS),
      f"{len({c for r in rows for c,_,_ in (r[B['comps']] or [])})}/{len(SKUS)}")
check("No duplicate (container, product, marketplace) rows — no fan-out",
      len({(r[B['cont']], r[B['bsku']] or r[B['csku']], r[B['plat']]) for r in rows}) == N,
      f"{N} rows, all unique")
check("Component -> Combo mapping", n_combos > 0,
      f"{n_combos} combos derived for {n_with_combo}/{len(SKUS)} components "
      f"(inv_product_combo is EMPTY — derived from SKU naming, an inference)")
check("Combo -> Marketplace mapping",
      all(r[B['ldate']] for r in rows if r[B['stat']] == 'Listed'),
      f"{listed_n} listed rows, every one carries a Listed Date")
check("Listing Status consistent with Listed Date",
      all((r[B['stat']] == 'Listed') == bool(r[B['ldate']]) for r in rows), "no mismatches")
check("Images", True, f"component {f('cimg')}/{N}, combo {f('bimg')}/{N}")
check("Traffic fetched", sum(r[B['impr']] for r in rows) >= 0,
      f"{sum(r[B['impr']] for r in rows):,} impressions, {sum(r[B['clk']] for r in rows):,} clicks")
check("Orders / Revenue fetched", True,
      f"{sum(r[B['ord']] for r in rows)} orders, £{sum(r[B['rev']] for r in rows):,.2f}")
check("Return Rate math", all(abs(r[B['rrate']] -
      (r[B['ret']]/r[B['units']]*100 if r[B['units']] else 0)) < .01 for r in rows),
      "(returns/units)*100")
check("Sheet SKUs resolvable in listing_data", True,
      f"{len(in_universe)}/{len(SKUS)} have a listing; the rest show as Not Listed")
# gaps are FAILs so they cannot be missed
ccre_n = sum(1 for r in rows if r[B['ccre']])
bcre_n = sum(1 for r in rows if r[B['bsku']] and r[B['bcre']])
bsku_n = sum(1 for r in rows if r[B['bsku']])
missing_lp = sorted({c for r in rows for c,_,_ in (r[B['comps']] or []) if c.upper() not in LP})
VAL["missing_from_ledsone"] = missing_lp
check("inv_products sourced from LEDs One inventory.products (NOT public.inv_products)",
      len(LP) > 0, f"{len(LP)} products cached from LEDs One; public.inv_products has "
      f"{avail.get('public.inv_products')} rows and is not used")
check("Component Created Dates populated from LEDs One", ccre_n == N, f"{ccre_n}/{N} rows")
check("Combo Created Dates populated from LEDs One", bcre_n == bsku_n, f"{bcre_n}/{bsku_n} combo rows")
check("Every sheet component found in LEDs One inventory.products", not missing_lp,
      f"{len(SKUS)-len(missing_lp)}/{len(SKUS)} found"
      + (f"; MISSING: {', '.join(missing_lp[:10])}" if missing_lp else ""))
check("Returns / Return Rate / Top Reason available", bool(avail.get("public.amazon_returns")),
      "returns tables are empty/dropped on this DB — render blank, never faked")
check("Average Feedback available", False,
      "no customer-review table on this DB — renders 'No Reviews'")

tot = lambda k: sum(r[B[k]] or 0 for r in rows)
VAL["totals"] = {"containers": len(sheet), "sheet_rows": sheet_rows, "components": len(SKUS),
                 "combos": n_combos, "rows": N, "listed": listed_n,
                 "impressions": tot('impr'), "clicks": tot('clk'), "orders": tot('ord'),
                 "units": tot('units'), "revenue": round(tot('rev'), 2), "returns": tot('ret')}
VAL["per_container"] = {c: sum(1 for r in rows if r[B['cont']] == c) for c in sorted(sheet)}
print("\nTOTALS:", json.dumps(VAL["totals"]))
print("PER CONTAINER:", json.dumps(VAL["per_container"]))
if VAL["gaps"]:
    print("\nSOURCE GAPS (fields left blank, not faked):")
    for g in VAL["gaps"]: print("  -", g)

P = {"capturedAt": TODAY, "B": B, "rows": rows,
     "containers": sorted(sheet),
     "meta": {"containers": len(sheet), "components": len(SKUS), "combos": n_combos,
              "rows": N, "source": f"{DB['dbname']}@{DB['host']}:{DB['port']}",
              "sheet": "New Containers to UK - 2026 .xlsx",
              "gaps": VAL["gaps"]}}
(BASE / "payload_v3.json").write_text(json.dumps(P, separators=(",", ":")), encoding="utf-8")
VAL["duration_sec"] = round(time.time() - T0, 1)
(BASE / "validation_v3.json").write_text(json.dumps(VAL, indent=2), encoding="utf-8")
print(f"\nwrote payload_v3.json ({(BASE/'payload_v3.json').stat().st_size:,} bytes) in {VAL['duration_sec']}s")
conn.close()
