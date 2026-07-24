#!/usr/bin/env python3
"""
build_new_scope.py — regenerate the dashboard-v1 PAYLOAD using the VALIDATED data model.
UI (HTML/CSS/JS) is never touched; only `const PAYLOAD = {...};` is replaced.

SCOPE (confirmed by the manager, 2026-07-24):
  NEW products only  ->  public.inv_products.created_at >= 2026-01-01 (isdeleted=0)
  Start from listing_data; one row per Combo SKU per Marketplace platform.

RELATIONSHIPS (all proven against the live DB):
  listing_data.mapped_sku|sku
     -> raw_sku  = COALESCE(NULLIF(TRIM(mapped_sku),''), TRIM(sku))
     -> base_sku = regexp_replace(raw_sku,'[_-][A-Za-z]{2,4}$','')   (country/channel suffix)
     -> inv_products (sku UNIQUE)                                      = PRODUCT MASTER
     -> inv_product_combo  product=COMBO id, inventory=COMPONENT id,
                           pack_count=qty, product_combo=row PK (NOT an FK)
        A genuine COMBO has >=1 row with inventory <> product (self-maps mark singles).
  NEVER split the SKU on '+' (34% of split parts match no real component).

Phase 1 (this script, --phase1): build everything from PUBLIC tables, write
  out/rows.json + out/components.txt (SKUs needing supplier attributes).
Phase 2 (--phase2): merge supplier attributes fetched via MCP into the rows and
  splice the PAYLOAD into dashboard-v1/index.html.
"""
import re, json, sys
from pathlib import Path
from datetime import date
import psycopg2

BASE  = Path(__file__).resolve().parent
OUT   = BASE / "out"; OUT.mkdir(exist_ok=True)
PAGE  = BASE.parent / "dashboard-v1" / "index.html"
START = "2026-01-01"
DB = dict(host="149.28.134.54", port="5435", dbname="order_management_copy",
          user="temp_user", password="12we34rt")

RESOLVE = """COALESCE(NULLIF(TRIM({t}.mapped_sku),''), TRIM({t}.sku))"""
PLAT = """CASE WHEN lower({c}) LIKE '%%amazon%%'  THEN 'amazon'
               WHEN lower({c}) LIKE '%%ebay%%'    THEN 'ebay'
               WHEN lower({c}) LIKE '%%shopify%%' THEN 'shopify'
               WHEN lower({c}) LIKE '%%b&q%%'     THEN 'b&q'
               WHEN lower({c}) LIKE '%%wayfair%%' THEN 'wayfair'
               ELSE 'other' END"""


def phase1():
    conn = psycopg2.connect(connect_timeout=40, **DB); conn.autocommit = True
    cur = conn.cursor()

    # ---------- resolve every in-window listing row to a product ----------------
    cur.execute(f"""
    CREATE TEMP TABLE res AS
    SELECT ld.ref_id, ld.created_at, ld.market_place, ld.listing_url,
           ld.main_image_url, ld.title,
           {PLAT.format(c='ld.which_channel_name')} AS platform,
           COALESCE(a.id, b.id)  AS prod_id,
           COALESCE(a.sku, b.sku) AS base_sku
    FROM public.listing_data ld
    LEFT JOIN public.inv_products a
           ON a.sku = COALESCE(NULLIF(TRIM(ld.mapped_sku),''), TRIM(ld.sku))
    LEFT JOIN public.inv_products b
           ON b.sku = regexp_replace(COALESCE(NULLIF(TRIM(ld.mapped_sku),''),
                                              TRIM(ld.sku)),'[_-][A-Za-z]{{2,4}}$','')
    WHERE ld.created_at >= %(s)s
      AND COALESCE(ld.is_parent,0) = 0
      AND ld.wrong_sku = 0
      AND COALESCE(TRIM(ld.sku),'') <> '';
    CREATE INDEX ON res(prod_id);
    """, {"s": START})

    # ---------- genuine combos, and the NEW-product gate ------------------------
    cur.execute("""
    CREATE TEMP TABLE combo AS
      SELECT product AS prod_id, count(*) AS part_count
      FROM public.inv_product_combo WHERE inventory <> product GROUP BY product;
    CREATE INDEX ON combo(prod_id);
    CREATE TEMP TABLE scope AS
      SELECT DISTINCT r.prod_id, r.base_sku
      FROM res r
      JOIN combo cb ON cb.prod_id = r.prod_id
      JOIN public.inv_products ip ON ip.id = r.prod_id
      WHERE ip.created_at >= %(s)s AND COALESCE(ip.isdeleted,0) = 0;
    CREATE INDEX ON scope(prod_id);
    """, {"s": START})
    cur.execute("SELECT count(*) FROM scope"); n_combo = cur.fetchone()[0]

    # ---------- DRIVER rows: one per (combo, platform) --------------------------
    cur.execute("""
    SELECT s.base_sku, r.platform,
           MIN(r.created_at)::date::text                       AS listing_date,
           (array_agg(r.ref_id         ORDER BY r.created_at, r.ref_id))[1] AS ref_id,
           (array_agg(r.listing_url    ORDER BY r.created_at, r.ref_id))[1] AS url,
           (array_agg(r.main_image_url ORDER BY r.created_at, r.ref_id))[1] AS img,
           (array_agg(r.title          ORDER BY r.created_at, r.ref_id))[1] AS title,
           (array_agg(r.market_place   ORDER BY r.created_at, r.ref_id))[1] AS mkt
    FROM res r JOIN scope s ON s.prod_id = r.prod_id
    GROUP BY s.base_sku, r.platform;""")
    listed = {(a, b): dict(ld=c, ref=d or "", url=e or "", img=f or "", title=g or "", mkt=h or "")
              for a, b, c, d, e, f, g, h in cur.fetchall()}

    # ---------- combo -> components (inv_product_combo) -------------------------
    cur.execute("""
    SELECT s.base_sku, ic.sku, COALESCE(pc.pack_count,''),
           (ic.created_at >= %(s)s AND COALESCE(ic.isdeleted,0)=0)::int AS is_new,
           COALESCE(NULLIF(ic.eng_desc,''), NULLIF(ic.description,''), NULLIF(ic.title,''),'')
    FROM scope s
    JOIN public.inv_product_combo pc ON pc.product = s.prod_id AND pc.inventory <> pc.product
    JOIN public.inv_products ic      ON ic.id = pc.inventory
    ORDER BY s.base_sku, ic.sku;""", {"s": START})
    parts = {}
    compinfo = {}
    for combo, csku, pack, isnew, desc in cur.fetchall():
        parts.setdefault(combo, []).append(csku)
        compinfo[csku] = dict(isnew=bool(isnew), desc=(desc or "")[:80], pack=pack)

    # ---------- combo creation date + best product name -------------------------
    cur.execute("""SELECT ip.sku, ip.created_at::date::text
                   FROM public.inv_products ip JOIN scope s ON s.prod_id = ip.id;""")
    combo_created = dict(cur.fetchall())
    cur.execute("""
      SELECT base_sku, title FROM (
        SELECT s.base_sku, ld.title,
               ROW_NUMBER() OVER (PARTITION BY s.base_sku ORDER BY length(ld.title) DESC) rn
        FROM res r JOIN scope s ON s.prod_id=r.prod_id
        JOIN public.listing_data ld ON ld.ref_id=r.ref_id
        WHERE COALESCE(ld.title,'')<>'') z WHERE rn=1;""")
    combo_name = dict(cur.fetchall())

    # ---------- component images (each component's own listing) -----------------
    cur.execute("""
      SELECT resolved, MAX(NULLIF(main_image_url,'')) FROM (
        SELECT COALESCE(NULLIF(TRIM(mapped_sku),''),TRIM(sku)) AS resolved, main_image_url
        FROM public.listing_data WHERE COALESCE(main_image_url,'')<>'') z
      GROUP BY resolved;""")
    img_by_sku = dict(cur.fetchall())

    # ---------- orders / traffic / returns, keyed on resolved base_sku ----------
    cur.execute(f"""
    WITH o AS (
      SELECT regexp_replace(TRIM(ot.sku),'[_-][A-Za-z]{{2,4}}$','') AS base_sku,
             {PLAT.format(c='ot.source_name')} AS platform,
             ot.order_id, ot.quantity, ot.order_total
      FROM public.order_transaction ot
      WHERE ot.order_status='Completed' AND ot.order_date >= %(s)s)
    SELECT o.base_sku, o.platform, count(DISTINCT o.order_id), SUM(o.quantity)::int,
           ROUND(SUM(o.order_total)::numeric,2)::float8
    FROM o JOIN scope s ON s.base_sku = o.base_sku
    GROUP BY 1,2;""", {"s": START})
    orders = {(a, b): (c, d, e) for a, b, c, d, e in cur.fetchall()}

    cur.execute("""
    WITH t AS (
      SELECT ref_id, COALESCE(impression,0) i, COALESCE(click,0) c
      FROM public.traffic_data WHERE date >= %(s)s
      UNION ALL
      SELECT ref_id, COALESCE(impressions,0), COALESCE(clicks,0)
      FROM public.ppc_performance WHERE date >= %(s)s)
    SELECT s.base_sku, r.platform, SUM(t.i)::bigint, SUM(t.c)::bigint
    FROM res r JOIN scope s ON s.prod_id=r.prod_id
    JOIN t ON t.ref_id = r.ref_id
    GROUP BY 1,2;""", {"s": START})
    traffic = {(a, b): (c, d) for a, b, c, d in cur.fetchall()}

    cur.execute("""
    WITH co AS (
      SELECT ot.order_id,
             regexp_replace(TRIM(ot.sku),'[_-][A-Za-z]{2,4}$','') AS base_sku,
             SUM(ot.quantity)::int AS oqty
      FROM public.order_transaction ot GROUP BY 1,2),
    r AS (
      SELECT regexp_replace(TRIM(ar.sku),'[_-][A-Za-z]{2,4}$','') AS base_sku,
             'amazon' AS platform, ar.qty::int AS qty
      FROM public.amazon_returns ar WHERE ar.request_date >= %(s)s
      UNION ALL
      SELECT co.base_sku,'ebay', e.qty FROM (
        SELECT return_id, MIN(order_id) order_id, MAX(return_qty)::int qty
        FROM public.ebay_returns WHERE request_date >= %(s)s GROUP BY return_id) e
      JOIN co ON co.order_id = e.order_id
      UNION ALL
      SELECT co.base_sku,'shopify', co.oqty FROM (
        SELECT DISTINCT ON (id) id, order_id FROM public.shopify_returns
        WHERE date >= %(s)s ORDER BY id) sh
      JOIN co ON co.order_id = sh.order_id)
    SELECT r.base_sku, r.platform, SUM(COALESCE(r.qty,0))::int
    FROM r JOIN scope s ON s.base_sku = r.base_sku GROUP BY 1,2;""", {"s": START})
    returns = {(a, b): c for a, b, c in cur.fetchall()}

    # ---------- unresolved diagnostics ------------------------------------------
    cur.execute("""SELECT count(*) FILTER (WHERE prod_id IS NULL), count(*) FROM res""")
    unres_rows, all_rows = cur.fetchone()
    cur.execute("""SELECT count(DISTINCT base_sku) FROM res WHERE prod_id IS NOT NULL""")
    resolved_skus = cur.fetchone()[0]
    conn.close()

    data = dict(listed={f"{k[0]}{k[1]}": v for k, v in listed.items()},
                parts=parts, compinfo=compinfo, combo_created=combo_created,
                combo_name=combo_name,
                img_by_sku={k: v for k, v in img_by_sku.items()},
                orders={f"{k[0]}{k[1]}": v for k, v in orders.items()},
                traffic={f"{k[0]}{k[1]}": v for k, v in traffic.items()},
                returns={f"{k[0]}{k[1]}": v for k, v in returns.items()},
                diag=dict(all_rows=all_rows, unresolved_rows=unres_rows,
                          resolved_skus=resolved_skus, combos=n_combo))
    (OUT / "phase1.json").write_text(json.dumps(data), encoding="utf-8")
    comps = sorted(compinfo)
    (OUT / "components.txt").write_text("\n".join(comps), encoding="utf-8")
    print(f"combos in scope        : {n_combo}")
    print(f"tracking rows          : {len(listed)}")
    print(f"distinct components    : {len(comps)}  (NEW: {sum(1 for v in compinfo.values() if v['isnew'])})")
    print(f"listing rows in-window : {all_rows}  unresolved: {unres_rows}")
    print(f"orders/traffic/returns keys: {len(orders)}/{len(traffic)}/{len(returns)}")
    print(f"-> wrote {OUT/'phase1.json'} and {OUT/'components.txt'}")


def phase2():
    d = json.loads((OUT / "phase1.json").read_text(encoding="utf-8"))
    listed = {tuple(k.split("")): v for k, v in d["listed"].items()}
    orders = {tuple(k.split("")): v for k, v in d["orders"].items()}
    traffic = {tuple(k.split("")): v for k, v in d["traffic"].items()}
    returns = {tuple(k.split("")): v for k, v in d["returns"].items()}
    parts, compinfo = d["parts"], d["compinfo"]
    combo_created, combo_name, img_by_sku = d["combo_created"], d["combo_name"], d["img_by_sku"]

    # supplier attributes (fetched via MCP -> supplier_meta.psv): sku|supplier|container|po|qty|recv|arrived|expected
    sup = {}
    f = BASE / "supplier_meta.psv"
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.startswith(">"): continue
            p = (line.split("|") + [""] * 8)[:8]
            sup[p[0]] = dict(supplier=p[1], container=p[2], po=p[3], qty=p[4],
                             recv=p[5], arrived=p[6] == "1", expected=p[7])
    print(f"supplier attributes for {len(sup)} components")

    B = dict(rid=0, cont=1, arr=2, sup=3, csku=4, cdesc=5, qty=6, crecv=7, combo=8, cname=9,
             used=10, ccreate=11, cqty=12, status=13, plat=14, url=15, ldate=16, impr=17,
             clk=18, ord=19, rev=20, units=21, ret=22, dsrc=23, updated=24, notes=25)
    LBL = {"amazon": "Amazon", "ebay": "eBay", "shopify": "Website",
           "b&q": "B&Q", "wayfair": "Wayfair", "other": "Other"}
    today = date.today().isoformat()

    rows, n = [], 0
    for (combo, plat) in sorted(listed):
        L = listed[(combo, plat)]
        pl = parts.get(combo, [])
        # representative component: prefer a NEW one, then one with supplier data
        rep = next((p for p in pl if compinfo.get(p, {}).get("isnew")), None) \
              or next((p for p in pl if p in sup), None) or (pl[0] if pl else "")
        sm = sup.get(rep, {}); ci = compinfo.get(rep, {})
        o = orders.get((combo, plat), (0, 0, 0.0)); t = traffic.get((combo, plat), (0, 0))
        def num(x):
            try: return int(float(x))
            except Exception: return ""
        r = [None] * 26; n += 1
        r[B["rid"]]     = f"REC-{n:05d}"
        r[B["cont"]]    = sm.get("container", "")
        r[B["arr"]]     = ("Arrived" if sm.get("arrived") else "In Transit") if sm else ""
        r[B["sup"]]     = sm.get("supplier", "")
        r[B["csku"]]    = rep
        r[B["cdesc"]]   = ci.get("desc", "")
        r[B["qty"]]     = num(sm.get("qty"))
        # The UI's date filter uses rowDate = crecv || ldate || ccreate. A supplier
        # receipt BEFORE the window (supplier history reaches back to 2025-07) would
        # push the row outside the default From=2026-01-01 range and hide it, even
        # though the product itself is in scope. Keep in-window receipts in the
        # column; carry pre-window receipts into Notes so nothing is lost and the
        # row anchors to its (always in-window) Listing Date instead.
        recv = sm.get("recv", "")
        notes = []
        if recv and recv < START:
            notes.append(f"Component received {recv} (before window)")
            recv = ""
        r[B["crecv"]]   = recv
        r[B["combo"]]   = combo
        r[B["cname"]]   = L["title"] or combo_name.get(combo, "")
        r[B["used"]]    = ", ".join(pl)
        r[B["ccreate"]] = combo_created.get(combo, "")
        r[B["cqty"]]    = L["img"]
        r[B["status"]]  = "Listed"
        r[B["plat"]]    = plat
        r[B["url"]]     = L["url"]
        r[B["ldate"]]   = L["ld"]
        r[B["impr"]], r[B["clk"]] = t[0], t[1]
        r[B["ord"]], r[B["units"]], r[B["rev"]] = o[0], o[1], o[2]
        r[B["ret"]]     = returns.get((combo, plat), 0)
        r[B["dsrc"]]    = "Postgres + " + LBL.get(plat, plat) + " API"
        r[B["updated"]] = today
        exp = sm.get("expected", "")
        if exp and not sm.get("arrived"):
            notes.append("Expected completion " + exp)
        r[B["notes"]]   = " · ".join(notes)
        rows.append(r)

    used_parts = {p for r in rows for p in (r[B["used"]].split(", ") if r[B["used"]] else [])}
    P = {"capturedAt": today, "window": {"start": START, "end": today},
         "note": "NEW products only (inv_products.created_at >= 2026-01-01) that were "
                 "listed on/after 2026-01-01. One row per Combo SKU per marketplace.",
         "compImg": {k: v for k, v in img_by_sku.items() if k in used_parts and v},
         "newComps": sorted(k for k in used_parts if compinfo.get(k, {}).get("isnew")),
         "rows": rows}

    html = PAGE.read_text(encoding="utf-8")
    m = re.search(r'(const PAYLOAD\s*=\s*)(\{.*?\})(;\s*\n)', html, re.S)
    PAGE.write_text(html[:m.start(2)] + json.dumps(P, separators=(",", ":")) + html[m.end(2):],
                    encoding="utf-8")

    ld = [r[B["ldate"]] for r in rows]
    print(f"\nROWS            : {len(rows)}")
    print(f"distinct combos : {len({r[B['combo']] for r in rows})}")
    print(f"components used : {len(used_parts)}  (NEW {len(P['newComps'])})")
    print(f"rows w/ supplier: {sum(1 for r in rows if r[B['sup']])}")
    print(f"orders / units  : {sum(r[B['ord']] for r in rows)} / {sum(r[B['units']] for r in rows)}")
    print(f"revenue         : {round(sum(float(r[B['rev']] or 0) for r in rows),2)}")
    print(f"returns / impr  : {sum(r[B['ret']] for r in rows)} / {sum(r[B['impr']] for r in rows)}")
    print(f"urls / images   : {sum(1 for r in rows if str(r[B['url']]).startswith('http'))} / "
          f"{sum(1 for r in rows if str(r[B['cqty']]).startswith('http'))}")
    print(f"listing date min/max: {min(ld)} / {max(ld)}")
    print(f"out-of-window / blank: {sum(1 for x in ld if x < START)} / {sum(1 for x in ld if not x)}")


if __name__ == "__main__":
    (phase1 if "--phase1" in sys.argv else phase2)()
