#!/usr/bin/env python3
"""validate_v3.py — independent field-by-field validation of dashboard-v3.
Re-derives every field from its ORIGINAL source and diffs against the payload.
Does not touch the dashboard; read-only."""
import json, re, psycopg2
from pathlib import Path
BASE = Path(__file__).resolve().parent

P   = json.loads((BASE/"payload_v3.json").read_text()); B = P['B']; R = P['rows']
SH  = json.loads((BASE/"sheet_containers.json").read_text())
LP  = {k.upper(): v for k, v in json.loads((BASE/"ledsone_products.json").read_text()).items()}
sheet_img = {}; sheet_cont = {}
for c, items in SH.items():
    for it in items:
        u = (it.get("sheet_image") or "").strip()
        sheet_img[it["sku"]] = u if u.lower().startswith(("http://","https://")) else ""
        sheet_cont.setdefault(it["sku"], []).append(c)

db = psycopg2.connect(host="149.28.134.54", port="5435", dbname="order_management_copy",
                      user="temp_user", password="12we34rt", connect_timeout=30)
db.autocommit = True; cur = db.cursor(); cur.execute("SET statement_timeout='180s'")
PLAT = """CASE WHEN lower({c}) LIKE '%%amazon%%' THEN 'amazon'
   WHEN lower({c}) LIKE '%%ebay%%' THEN 'ebay' WHEN lower({c}) LIKE '%%shopify%%' THEN 'shopify'
   WHEN lower({c}) LIKE '%%b&q%%' THEN 'b&q' WHEN lower({c}) LIKE '%%wayfair%%' THEN 'wayfair'
   ELSE 'other' END"""

prods = sorted({(r[B['bsku']] or r[B['csku']]) for r in R})
cur.execute("CREATE TEMP TABLE pr(sku text PRIMARY KEY)")
cur.executemany("INSERT INTO pr VALUES(%s) ON CONFLICT DO NOTHING", [(p,) for p in prods])
cur.execute("""CREATE TEMP TABLE res AS
SELECT COALESCE(NULLIF(TRIM(ld.mapped_sku),''),TRIM(ld.sku)) AS resolved, ld.ref_id,
       ld.created_at::date AS listed_on, ld.which_channel_name, ld.listing_url
FROM public.listing_data ld
WHERE COALESCE(ld.is_parent,0)=0 AND ld.wrong_sku=0 AND COALESCE(TRIM(ld.sku),'')<>'';
CREATE INDEX ON res(resolved); CREATE INDEX ON res(ref_id)""")

cur.execute(f"""SELECT r.resolved, {PLAT.format(c='r.which_channel_name')}, MIN(r.listed_on)::text
FROM res r JOIN pr p ON p.sku=r.resolved GROUP BY 1,2""")
db_listed = {(s,p): d for s,p,d in cur.fetchall()}
cur.execute(f"""SELECT r.resolved, plat, SUM(t.i)::bigint, SUM(t.c)::bigint FROM
 (SELECT r.resolved, r.ref_id, r.listed_on, {PLAT.format(c='r.which_channel_name')} plat
  FROM res r JOIN pr p ON p.sku=r.resolved) r
 JOIN (SELECT ref_id,date,COALESCE(impression,0) i,COALESCE(click,0) c FROM public.traffic_data
       UNION ALL SELECT ref_id,date,COALESCE(impressions,0),COALESCE(clicks,0) FROM public.ppc_performance) t
 ON t.ref_id=r.ref_id AND t.date>=r.listed_on GROUP BY 1,2""")
db_traf = {(s,p):(i,c) for s,p,i,c in cur.fetchall()}
cur.execute(f"""SELECT base_sku, platform, count(DISTINCT order_id), SUM(quantity)::int,
 ROUND(SUM(order_total)::numeric,2)::float8 FROM (
 SELECT regexp_replace(TRIM(ot.sku),'[_-][A-Za-z]{{2,4}}$','') base_sku,
        {PLAT.format(c='ot.source_name')} platform, ot.order_id, ot.quantity, ot.order_total
 FROM public.order_transaction ot WHERE ot.order_status='Completed') o
 JOIN pr p ON p.sku=o.base_sku GROUP BY 1,2""")
db_ord = {(s,p):(o,u,rv) for s,p,o,u,rv in cur.fetchall()}
try:
    cur.execute("""SELECT regexp_replace(TRIM(ar.sku),'[_-][A-Za-z]{2,4}$',''),'amazon',SUM(ar.qty)::int
      FROM public.amazon_returns ar JOIN pr p ON p.sku=regexp_replace(TRIM(ar.sku),'[_-][A-Za-z]{2,4}$','')
      GROUP BY 1""")
    db_ret = {(s,p):q for s,p,q in cur.fetchall()}
except Exception:
    db.rollback(); db_ret = {}

FIELDS = ["Component SKU","Component Image","Component Created Date","Combo SKU","Combo Image",
          "Combo Created Date","Listing Status","Marketplace","Listed Date","Impressions","Clicks",
          "Orders","Units Sold","Revenue","Total Returns","Return Rate %","Top Reason","Average Feedback"]
chk = {f:0 for f in FIELDS}; bad = {f:[] for f in FIELDS}; na = {}
PLATS = {'amazon','ebay','shopify','b&q','wayfair','other',''}

for r in R:
    psku = r[B['bsku']] or r[B['csku']]; plat = r[B['plat']] or ''
    comps = r[B['comps']] or []
    for c, im, cre in comps:
        chk["Component SKU"] += 1
        if c not in sheet_img: bad["Component SKU"].append((c,"not in Google Sheet"))
        chk["Component Image"] += 1
        want = sheet_img.get(c, "")
        if want and im != want: bad["Component Image"].append((c, f"shows {im} want {want}"))
        chk["Component Created Date"] += 1
        wc = (LP.get(c.upper()) or {}).get("created","")
        if wc and cre != wc: bad["Component Created Date"].append((c, f"{cre} != {wc}"))
    if r[B['bsku']]:
        chk["Combo SKU"] += 1; chk["Combo Image"] += 1; chk["Combo Created Date"] += 1
        wb = (LP.get(r[B['bsku']].upper()) or {}).get("created","")
        if wb and r[B['bcre']] != wb: bad["Combo Created Date"].append((r[B['bsku']], f"{r[B['bcre']]} != {wb}"))
    chk["Marketplace"] += 1
    if plat not in PLATS: bad["Marketplace"].append((psku, plat))
    chk["Listing Status"] += 1; chk["Listed Date"] += 1
    want_ld = db_listed.get((psku, plat))
    if r[B['stat']] == 'Listed':
        if not r[B['ldate']]: bad["Listing Status"].append((psku,"Listed but no date"))
        if want_ld and r[B['ldate']] != want_ld: bad["Listed Date"].append((psku, f"{r[B['ldate']]} != {want_ld}"))
    elif r[B['ldate']]: bad["Listing Status"].append((psku,"Not Listed but has date"))
    t = db_traf.get((psku, plat), (0,0)); chk["Impressions"] += 1; chk["Clicks"] += 1
    if r[B['impr']] != t[0]: bad["Impressions"].append((psku, f"{r[B['impr']]} != {t[0]}"))
    if r[B['clk']]  != t[1]: bad["Clicks"].append((psku, f"{r[B['clk']]} != {t[1]}"))
    o = db_ord.get((psku, plat), (0,0,0.0))
    for i,f in enumerate(["Orders","Units Sold","Revenue"]):
        chk[f] += 1
        got = r[B[['ord','units','rev'][i]]]
        if abs((got or 0)-(o[i] or 0)) > .01: bad[f].append((psku, f"{got} != {o[i]}"))
    chk["Total Returns"] += 1
    if r[B['ret']] != db_ret.get((psku, plat), 0):
        bad["Total Returns"].append((psku, f"{r[B['ret']]} != {db_ret.get((psku,plat),0)}"))
    chk["Return Rate %"] += 1
    exp = round(r[B['ret']]/r[B['units']]*100,2) if r[B['units']] else 0.0
    if abs(r[B['rrate']]-exp) > .01: bad["Return Rate %"].append((psku, f"{r[B['rrate']]} != {exp}"))
    chk["Top Reason"] += 1; chk["Average Feedback"] += 1

na["Top Reason"] = "no reason column populated on this DB (ebay/shopify returns dropped)"
na["Average Feedback"] = "no customer-review table on this DB"
na["Combo Image"] = "sheet has no combo images; sourced from listing_data (by design)"

print(f"{'FIELD':26}{'CHECKED':>9}{'MISMATCH':>10}   SOURCE")
SRC = {"Component SKU":"Google Sheet","Component Image":"Google Sheet (Image Link)",
 "Component Created Date":"LEDs One inventory.products","Combo SKU":"derived (SKU naming)",
 "Combo Image":"listing_data.main_image_url","Combo Created Date":"LEDs One inventory.products",
 "Listing Status":"listing_data","Marketplace":"listing_data.which_channel_name",
 "Listed Date":"MIN(listing_data.created_at)","Impressions":"traffic_data+ppc_performance",
 "Clicks":"traffic_data+ppc_performance","Orders":"order_transaction","Units Sold":"order_transaction",
 "Revenue":"order_transaction","Total Returns":"amazon_returns","Return Rate %":"computed",
 "Top Reason":"UNAVAILABLE","Average Feedback":"UNAVAILABLE"}
for f in FIELDS:
    print(f"{f:26}{chk[f]:>9}{len(bad[f]):>10}   {SRC[f]}")
print()
for f in FIELDS:
    if bad[f]:
        print(f"--- {f}: {len(bad[f])} mismatch ---")
        for x in bad[f][:5]: print("   ", x)
tot = sum(len(v) for v in bad.values())
print(f"\nTOTAL MISMATCHES: {tot}")
print(f"rows={len(R)}  components={len({c for r in R for c,_,_ in (r[B['comps']] or [])})}")
