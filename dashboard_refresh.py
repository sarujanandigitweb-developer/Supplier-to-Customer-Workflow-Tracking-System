#!/usr/bin/env python3
"""
dashboard_refresh.py
====================
Automated daily refresh for the Supplier-to-Customer Workflow Tracking System (SCWTS)
dashboard. Intended to run every day at 10:00 AM via cron.

Workflow (fail-safe — data.js is NEVER overwritten unless validation passes):
  1. Connect to PostgreSQL (abort + log on failure).
  2. Run every dataset export used by the dashboard (8 pages, 8 datasets).
  3. Build a fresh in-memory dataset (no write yet).
  4. Validate: live export vs current data.js (row counts, added/removed,
     duplicates, KPI totals, catastrophic-drop guard).
  5. Write a timestamped validation report (PASS/FAIL + reasons).
  6. If PASS: back up the current data.js, then write the new one.
  7. Append a refresh log entry (start/end/duration/counts/result/errors).
  8. If FAIL: keep the existing dashboard, write a detailed error report.

Datasets  -> pages:
  components, componentComboMap  -> Component Journey, Executive
  combos                         -> Combo Creation, Executive
  listings                       -> Marketplace Status, Executive
  orders                         -> Sales Performance, Executive
  traffic                        -> Traffic
  returns                        -> Returns, Executive
  purchaseOrders                 -> Supplier & Container

Cron (run daily at 10:00):
  0 10 * * * /usr/bin/python3 /home/led-247/Supplier-to-Customer-Workflow-Tracking-System/dashboard_refresh.py
See the "CRON SETUP" section at the bottom of this file.

Dependencies: psycopg2 (pip install psycopg2-binary). Std-lib: pathlib, logging,
json, datetime, collections, hashlib, shutil.
"""

import sys, json, shutil, hashlib, logging
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal
from collections import Counter

try:
    import psycopg2
    from psycopg2.extras import execute_values
except ImportError:
    print("ERROR: psycopg2 is not installed. Run:  pip install psycopg2-binary")
    sys.exit(2)

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
DB_CONFIG = {
    "host": "149.28.134.54",
    "port": "5435",
    "dbname": "order_management_copy",
    "user": "temp_user",
    "password": "12we34rt",
}

START_DATE = "2026-01-01"          # dashboard reporting-window start (business rule)
DROP_GUARD = 0.50                  # FAIL if a dataset collapses below 50% of current
INFLATE_GUARD = 3.0               # FAIL if a dataset balloons above 3x current (query bug)
CRITICAL = ["components", "combos", "componentComboMap", "listings",
            "orders", "returns", "purchaseOrders"]

# Datasets sourced from the `supplier` schema (the un-mirrored purchasing DB).
# If the connected role lacks USAGE on `supplier`, these are carried forward
# unchanged from the current data.js and the 6 public datasets refresh live.
SUPPLIER_DATASETS = ["components", "purchaseOrders"]

BASE_DIR      = Path(__file__).resolve().parent
DASHBOARD_DIR = BASE_DIR / "dashboard"
DATA_JS       = DASHBOARD_DIR / "data.js"
BACKUP_DIR    = BASE_DIR / "data_backup"
LOGS_DIR      = BASE_DIR / "logs"
REPORT_DIR    = BASE_DIR / "validation"
for d in (BACKUP_DIR, LOGS_DIR, REPORT_DIR):
    d.mkdir(parents=True, exist_ok=True)

# Column order for every dataset MUST match dashboard/script.js CI indices + meta.schema
SCHEMA = {
    "components":        ["sku", "description", "supplier", "po", "container", "created_date", "status_arrived"],
    "combos":            ["combo_sku", "part_count", "first_listed", "is_listed"],
    "componentComboMap": ["component_sku", "combo_sku"],
    "listings":          ["ref_id", "sku", "mapped_sku", "channel", "market_place", "status",
                          "is_deleted", "is_ended", "wrong_sku", "listing_date"],
    "orders":            ["order_id", "sku", "source_name", "market_place", "order_status",
                          "order_date", "quantity", "order_total"],
    "traffic":           ["source", "ref_id", "channel", "market_place", "impressions", "clicks"],
    "returns":           ["channel", "order_id", "sku", "request_date", "reason", "qty", "refund"],
    "purchaseOrders":    ["po", "supplier", "code", "order_date", "container", "cbm",
                          "arrived", "confirmed_date", "finished_date", "expected_completion"],
}

# --------------------------------------------------------------------------- #
# Logging (console + logs/refresh.log)
# --------------------------------------------------------------------------- #
logger = logging.getLogger("refresh")
logger.setLevel(logging.INFO)
_fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s", "%Y-%m-%d %H:%M:%S")
_fh = logging.FileHandler(LOGS_DIR / "refresh.log"); _fh.setFormatter(_fmt); logger.addHandler(_fh)
_ch = logging.StreamHandler(sys.stdout); _ch.setFormatter(_fmt); logger.addHandler(_ch)

def step(msg):  logger.info(msg)
def warn(msg):  logger.warning(msg)
def err(msg):   logger.error(msg)

# --------------------------------------------------------------------------- #
# SQL — temp tables build the shared lineage once, then each dataset selects.
# All queries are parameterised (%(start)s) — NO hardcoded KPI values anywhere.
# --------------------------------------------------------------------------- #
# Shared lineage built ON TOP of t_nc (the new-component SKU set). t_nc is seeded
# differently per mode (see build_lineage): from supplier.order_items when the
# supplier schema is reachable, else from the current data.js components array.
LINEAGE_SQL = [
    # every combo SKU seen anywhere (listing_data or order_transaction)
    """CREATE TEMP TABLE t_universe AS
       SELECT DISTINCT sku FROM public.listing_data      WHERE wrong_sku = 0 AND sku LIKE '%%+%%'
       UNION SELECT DISTINCT sku FROM public.order_transaction WHERE sku LIKE '%%+%%';""",
    # qualifying combos = combos containing at least one NEW component
    """CREATE TEMP TABLE t_qc AS
       SELECT DISTINCT c.sku
       FROM t_universe c
       CROSS JOIN LATERAL (SELECT TRIM(x) AS part FROM unnest(string_to_array(c.sku,'+')) x) p
       WHERE p.part IN (SELECT sku FROM t_nc);""",
    "CREATE INDEX ON t_qc (sku);",
    # order_id -> combo sku + ordered qty (bridge for eBay/Shopify returns + Shopify qty)
    """CREATE TEMP TABLE t_co AS
       SELECT order_id, sku, SUM(quantity)::int AS oqty
       FROM public.order_transaction WHERE sku IN (SELECT sku FROM t_qc)
       GROUP BY order_id, sku;""",
    "CREATE INDEX ON t_co (order_id);",
]

def supplier_accessible(cur):
    """True only if the connected role can read the supplier schema."""
    try:
        cur.execute("SELECT has_schema_privilege(current_user,'supplier','USAGE')")
        if not cur.fetchone()[0]:
            return False
        cur.execute("SELECT 1 FROM supplier.order_items LIMIT 1")
        cur.fetchone()
        return True
    except Exception:
        return False

def build_lineage(cur, mode, nc_skus=None):
    """
    Seed t_nc (new-component SKUs + first_created), then build the shared lineage.
      mode='full'     -> t_nc from supplier.order_items (authoritative first-seen).
      mode='degraded' -> t_nc from nc_skus (component SKUs carried from data.js);
                         first_created is unknown here (components are carried forward).
    """
    if mode == "full":
        cur.execute("""CREATE TEMP TABLE t_nc AS
            SELECT sku, MIN(created_at) AS first_created
            FROM supplier.order_items
            WHERE sku <> '' GROUP BY sku HAVING MIN(created_at) >= %(start)s;""",
            {"start": START_DATE})
    else:
        cur.execute("CREATE TEMP TABLE t_nc (sku text, first_created timestamp);")
        execute_values(cur, "INSERT INTO t_nc (sku) VALUES %s",
                       [(s,) for s in sorted(set(nc_skus or [])) if s])
    cur.execute("CREATE INDEX ON t_nc (sku);")
    for sql in LINEAGE_SQL:
        cur.execute(sql, {"start": START_DATE})

QUERIES = {
    # 1) COMPONENTS — one row per new component; date = first-seen (FIXED)
    "components": """
        SELECT DISTINCT ON (oi.sku)
          oi.sku,
          LEFT(COALESCE(oi.english_description,''),80),
          s.name, o.order_id,
          COALESCE(c.name, o.container_id),
          nc.first_created::date,
          CASE WHEN o.status_arrived = 1 THEN 1 ELSE 0 END
        FROM t_nc nc
        JOIN supplier.order_items oi ON oi.sku = nc.sku
        LEFT JOIN supplier.orders     o ON oi.order_id  = o.id
        LEFT JOIN supplier.suppliers  s ON o.supplier_id = s.id
        LEFT JOIN supplier.containers c ON c.id::text    = o.container_id
        ORDER BY oi.sku, oi.created_at DESC;
    """,
    # 2) COMBOS — one row per qualifying combo
    "combos": """
        SELECT q.sku,
               array_length(string_to_array(q.sku,'+'),1),
               l.first_listed::date,
               CASE WHEN l.sku IS NOT NULL THEN 1 ELSE 0 END
        FROM t_qc q
        LEFT JOIN (SELECT sku, MIN(created_at)::date AS first_listed
                   FROM public.listing_data WHERE wrong_sku=0 AND sku LIKE '%%+%%'
                   GROUP BY sku) l ON l.sku = q.sku
        ORDER BY q.sku;
    """,
    # 3) COMPONENT -> COMBO mapping (new component, qualifying combo) pairs
    "componentComboMap": """
        SELECT DISTINCT p.part, q.sku
        FROM t_qc q
        CROSS JOIN LATERAL (SELECT TRIM(x) AS part FROM unnest(string_to_array(q.sku,'+')) x) p
        WHERE p.part IN (SELECT sku FROM t_nc)
        ORDER BY 1,2;
    """,
    # 4) LISTINGS — marketplace listings for qualifying combos (child, in-window)
    "listings": """
        SELECT l.ref_id, l.sku, NULLIF(l.mapped_sku,''), l.which_channel_name, l.market_place,
               l.status, COALESCE(l.is_deleted,0)::int, COALESCE(l.is_ended,0)::int,
               l.wrong_sku::int, l.created_at::date
        FROM public.listing_data l
        WHERE l.sku IN (SELECT sku FROM t_qc) AND l.created_at >= %(start)s AND l.is_child = 1
        ORDER BY l.created_at DESC, l.ref_id;
    """,
    # 5) ORDERS — raw order lines for qualifying combos (all statuses)
    "orders": """
        SELECT ot.order_id, ot.sku, ot.source_name, ot.market_place, ot.order_status,
               ot.order_date::date, ot.quantity::int, ot.order_total
        FROM public.order_transaction ot
        WHERE ot.sku IN (SELECT sku FROM t_qc) AND ot.order_date >= %(start)s
        ORDER BY ot.order_date DESC;
    """,
    # 6) TRAFFIC — FIXED: refids deduped to ONE row per ref_id (no join fan-out).
    #    NOTE: do NOT gate refids on listing created_at — a combo listed before the
    #    window still earns in-window impressions; the window is applied on the
    #    traffic date (td.date / pp.date) below, not on when the listing was created.
    "traffic": """
        WITH refids AS (
          SELECT ref_id, MAX(which_channel_name) AS channel
          FROM public.listing_data
          WHERE wrong_sku = 0 AND sku IN (SELECT sku FROM t_qc)
          GROUP BY ref_id
        )
        SELECT 'organic', td.ref_id, MAX(r.channel), td.market_place,
               SUM(COALESCE(td.impression,0))::bigint, SUM(COALESCE(td.click,0))::bigint
        FROM public.traffic_data td JOIN refids r ON r.ref_id = td.ref_id
        WHERE td.date >= %(start)s GROUP BY td.ref_id, td.market_place
        UNION ALL
        SELECT 'paid', pp.ref_id, MAX(r.channel), pp.marketplace,
               SUM(COALESCE(pp.impressions,0))::bigint, SUM(COALESCE(pp.clicks,0))::bigint
        FROM public.ppc_performance pp JOIN refids r ON r.ref_id = pp.ref_id
        WHERE pp.date >= %(start)s GROUP BY pp.ref_id, pp.marketplace;
    """,
    # 7) RETURNS — Amazon (direct) + eBay (per return_id) + Shopify (qty from order line)
    "returns": """
        SELECT 'amazon', ar.order_id, ar.sku, ar.request_date::date, ar.reason,
               ar.qty::int, ROUND(ar.refunded_amount::numeric,2)::float8
        FROM public.amazon_returns ar
        WHERE ar.sku IN (SELECT sku FROM t_qc) AND ar.request_date >= %(start)s
        UNION ALL
        SELECT 'ebay', eb.order_id, eb.sku, eb.rdate, eb.reason, eb.qty, eb.refund FROM (
          SELECT er.return_id, MIN(er.order_id) AS order_id, MIN(co.sku) AS sku,
                 MIN(er.request_date::date) AS rdate,
                 MAX(er.reason) FILTER (WHERE er.reason IS NOT NULL AND er.reason<>'') AS reason,
                 MAX(er.return_qty)::int AS qty, ROUND(MAX(er.buyer_refund_amount)::numeric,2)::float8 AS refund
          FROM public.ebay_returns er JOIN t_co co ON co.order_id = er.order_id
          WHERE er.request_date >= %(start)s GROUP BY er.return_id) eb
        UNION ALL
        SELECT 'shopify', s.order_id, s.sku, s.sdate, NULL, s.oqty, s.refund FROM (
          SELECT DISTINCT ON (sr.id) sr.id, sr.order_id, co.sku, sr.date::date AS sdate, co.oqty,
                 ROUND(sr.refund_amount::numeric,2)::float8 AS refund
          FROM public.shopify_returns sr JOIN t_co co ON co.order_id = sr.order_id
          WHERE sr.date >= %(start)s ORDER BY sr.id, co.oqty DESC) s
        ORDER BY 1, 4 DESC;
    """,
    # 8) PURCHASE ORDERS — POs containing new components, with container + status dates
    "purchaseOrders": """
        SELECT o.order_id, s.name, s.code, o.order_date::date,
               COALESCE(cont.name, o.container_id),
               ROUND(o.cbm::numeric,2)::float8,
               o.status_arrived::int,
               o.confirmed_date::date, o.finished_date::date, o.expected_completion_date::date
        FROM supplier.orders o
        JOIN (SELECT DISTINCT oi.order_id AS oid FROM supplier.order_items oi
              WHERE oi.sku IN (SELECT sku FROM t_nc)) x ON x.oid = o.id
        LEFT JOIN supplier.suppliers s ON o.supplier_id = s.id
        LEFT JOIN supplier.containers cont ON cont.id::text = o.container_id
        ORDER BY o.order_date DESC;
    """,
}

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def norm(v):
    """Convert DB types to JSON-safe primitives."""
    if v is None:              return None
    if isinstance(v, Decimal): return round(float(v), 2)
    if isinstance(v, (date, datetime)): return v.isoformat()[:10]
    return v

def fetch_dataset(cur, name):
    cur.execute(QUERIES[name], {"start": START_DATE})
    return [[norm(c) for c in row] for row in cur.fetchall()]

def compute_kpis(ds):
    """Recalculate every KPI from raw rows — nothing hardcoded."""
    S = SCHEMA
    oi = {k: i for i, k in enumerate(S["orders"])}
    ri = {k: i for i, k in enumerate(S["returns"])}
    ti = {k: i for i, k in enumerate(S["traffic"])}
    ci = {k: i for i, k in enumerate(S["combos"])}
    completed = [o for o in ds["orders"] if o[oi["order_status"]] == "Completed"]
    oids = {o[oi["order_id"]] for o in completed}
    ret = ds["returns"]
    return {
        "new_components":  len(ds["components"]),
        "combos":          len(ds["combos"]),
        "listed_combos":   sum(1 for r in ds["combos"] if r[ci["is_listed"]] == 1),
        "non_listed":      sum(1 for r in ds["combos"] if r[ci["is_listed"]] == 0),
        "listings":        len(ds["listings"]),
        "order_lines":     len(ds["orders"]),
        "orders":          len(oids),
        "units":           sum((o[oi["quantity"]] or 0) for o in completed),
        "revenue":         round(sum((o[oi["order_total"]] or 0) for o in completed), 2),
        "returns":         len(ret),
        "returns_amazon":  sum(1 for r in ret if r[ri["channel"]] == "amazon"),
        "returns_ebay":    sum(1 for r in ret if r[ri["channel"]] == "ebay"),
        "returns_shopify": sum(1 for r in ret if r[ri["channel"]] == "shopify"),
        "traffic_rows":    len(ds["traffic"]),
        "impressions":     sum((t[ti["impressions"]] or 0) for t in ds["traffic"]),
        "clicks":          sum((t[ti["clicks"]] or 0) for t in ds["traffic"]),
        "purchase_orders": len(ds["purchaseOrders"]),
        "suppliers":       len({c[2] for c in ds["components"] if c[2]}),
        "containers":      len({p[4] for p in ds["purchaseOrders"] if p[4]}),
    }

def load_current():
    """Parse the existing dashboard/data.js into a dict (or None)."""
    if not DATA_JS.exists():
        return None
    txt = DATA_JS.read_text(encoding="utf-8")
    i = txt.find("window.DASHBOARD_DATA")
    if i < 0:
        return None
    b = txt.find("{", i)
    e = txt.rfind("}")
    try:
        return json.loads(txt[b:e + 1])
    except Exception as ex:
        warn(f"Could not parse current data.js: {ex}")
        return None

def dup_count(rows, keyfn):
    c = Counter(keyfn(r) for r in rows)
    return sum(v - 1 for v in c.values() if v > 1)

# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #
def validate(new_ds, cur_obj, kpi_new, kpi_cur, carried=()):
    checks = []
    carried = set(carried or ())
    def add(name, ok, detail): checks.append((name, bool(ok), detail))

    # (a) critical datasets non-empty
    for k in CRITICAL:
        add(f"{k}: non-empty", len(new_ds[k]) > 0, f"{len(new_ds[k])} rows")

    # (b) uniqueness / no-fan-out (catches join bugs like the old traffic double-count)
    add("combos: unique key", dup_count(new_ds["combos"], lambda r: r[0]) == 0,
        f"{dup_count(new_ds['combos'], lambda r: r[0])} dup combo_sku")
    add("mapping: unique pairs", dup_count(new_ds["componentComboMap"], lambda r: (r[0], r[1])) == 0,
        f"{dup_count(new_ds['componentComboMap'], lambda r: (r[0], r[1]))} dup pairs")
    tdup = dup_count(new_ds["traffic"], lambda r: (r[0], r[1], r[3]))
    add("traffic: no fan-out", tdup == 0, f"{tdup} dup (source,ref_id,market_place)")
    add("purchaseOrders: unique PO", dup_count(new_ds["purchaseOrders"], lambda r: r[0]) == 0,
        f"{dup_count(new_ds['purchaseOrders'], lambda r: r[0])} dup PO")

    # (c) KPI sanity — must be positive/coherent
    add("KPI: revenue > 0", kpi_new["revenue"] > 0, f"£{kpi_new['revenue']:,}")
    add("KPI: orders > 0", kpi_new["orders"] > 0, f"{kpi_new['orders']} orders")
    add("KPI: returns channels sum", kpi_new["returns"] ==
        kpi_new["returns_amazon"] + kpi_new["returns_ebay"] + kpi_new["returns_shopify"],
        f"{kpi_new['returns']} = {kpi_new['returns_amazon']}+{kpi_new['returns_ebay']}+{kpi_new['returns_shopify']}")

    # (d) catastrophic-change guard vs current data.js (skip carried-forward sets)
    if cur_obj:
        for k in CRITICAL + ["traffic"]:
            if k in carried:
                add(f"{k}: change guard", True, f"{len(new_ds[k])} rows (carried forward, unchanged)")
                continue
            oldc = len(cur_obj.get(k, []))
            newc = len(new_ds[k])
            if oldc == 0:
                add(f"{k}: change guard", True, f"{oldc} -> {newc} (no baseline)")
            else:
                ratio = newc / oldc
                ok = DROP_GUARD <= ratio <= INFLATE_GUARD
                add(f"{k}: change guard", ok, f"{oldc} -> {newc} ({ratio:.2f}x)")

    passed = all(ok for _, ok, _ in checks)
    return passed, checks

def diff_counts(new_ds, cur_obj):
    """Row added/removed per dataset (by a stable key)."""
    keys = {
        "components": lambda r: r[0], "combos": lambda r: r[0],
        "componentComboMap": lambda r: (r[0], r[1]),
        "listings": lambda r: (r[0], r[3], r[4]),
        "orders": lambda r: (r[0], r[1], r[5], r[6], r[7]),
        "traffic": lambda r: (r[0], r[1], r[3]),
        "returns": lambda r: (r[0], r[1], r[2], r[3]),
        "purchaseOrders": lambda r: r[0],
    }
    out = {}
    for k, kf in keys.items():
        new_keys = set(kf(r) for r in new_ds[k])
        cur_keys = set(kf(r) for r in (cur_obj.get(k, []) if cur_obj else []))
        out[k] = {
            "current": len(cur_keys), "new": len(new_keys),
            "added": len(new_keys - cur_keys), "removed": len(cur_keys - new_keys),
        }
    return out

# --------------------------------------------------------------------------- #
# Output generation
# --------------------------------------------------------------------------- #
def build_datajs(new_ds, kpi_new, mode="full", carried=()):
    obj = {
        "meta": {
            "capturedAt": date.today().isoformat(),
            "periodStart": START_DATE,
            "periodEnd": date.today().isoformat(),
            "title": "Supplier-to-Customer Workflow Tracking System",
            "schema": SCHEMA,
            "counts": {k: len(v) for k, v in new_ds.items()},
            "kpi": kpi_new,
            "refreshMode": mode,
            "carriedForward": list(carried or []),
            "source": "dashboard_refresh.py (live PostgreSQL)",
        },
    }
    obj.update(new_ds)
    note = ("" if mode == "full"
            else f"   DEGRADED: {', '.join(carried)} carried forward (supplier schema not reachable).\n")
    header = ("/* Supplier-to-Customer Workflow Tracking — LIVE PostgreSQL export.\n"
              f"   Auto-generated by dashboard_refresh.py at {datetime.now():%Y-%m-%d %H:%M:%S}.\n"
              f"   Window: {START_DATE} -> {date.today().isoformat()}. Traffic aggregated per listing.\n"
              f"{note}*/\n")
    return header + "window.DASHBOARD_DATA=" + json.dumps(obj, separators=(",", ":")) + ";\n"

def write_report(ts, passed, checks, diffs, kpi_new, kpi_cur, error=None, mode="full", carried=()):
    path = REPORT_DIR / f"validation_report_{ts}.md"
    L = []
    L.append(f"# Dashboard Refresh Validation — {ts}")
    L.append(f"\n**Result:** {'✅ PASS' if passed else '❌ FAIL'}  ·  "
             f"Mode: **{mode.upper()}**  ·  "
             f"Window {START_DATE} → {date.today().isoformat()}\n")
    if mode == "degraded":
        L.append(f"\n> ⚠️ **Degraded refresh** — the connected role lacks USAGE on the `supplier` "
                 f"schema, so **{', '.join(carried) or 'supplier datasets'}** were carried forward "
                 f"unchanged from the previous `data.js`. The other datasets refreshed live from "
                 f"`public`. Grant this role read access to `supplier` (or run with the broader MCP "
                 f"role) for a full refresh of components + purchase orders.\n")
    if error:
        L.append(f"\n> **Aborted:** {error}\n")

    L.append("## Dataset reconciliation (live export vs current data.js)\n")
    L.append("| Dataset | data.js (current) | New export | Added | Removed | Match |")
    L.append("|---|---:|---:|---:|---:|:--:|")
    for k, d in (diffs or {}).items():
        same = "✅" if d["added"] == 0 and d["removed"] == 0 else "↕️"
        L.append(f"| {k} | {d['current']:,} | {d['new']:,} | +{d['added']:,} | -{d['removed']:,} | {same} |")

    L.append("\n## KPI totals (recalculated from PostgreSQL — not hardcoded)\n")
    L.append("| KPI | Current data.js | New export | Δ |")
    L.append("|---|---:|---:|---:|")
    for k in kpi_new:
        old = (kpi_cur or {}).get(k, "—")
        try:
            delta = kpi_new[k] - old
        except Exception:
            delta = "—"
        L.append(f"| {k} | {old} | {kpi_new[k]} | {delta} |")

    L.append("\n## Validation checks\n")
    L.append("| Check | Result | Detail |")
    L.append("|---|:--:|---|")
    for name, ok, detail in checks:
        L.append(f"| {name} | {'✅' if ok else '❌'} | {detail} |")

    if not passed:
        L.append("\n## ❌ Failure analysis\n")
        for name, ok, detail in checks:
            if not ok:
                L.append(f"- **{name}** — {detail}. "
                         f"Likely cause: a broken/renamed source table, an incorrect WHERE/JOIN, "
                         f"or a partial export. data.js was **NOT** replaced; previous dashboard kept.")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path

def backup_current():
    if not DATA_JS.exists():
        return None
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = BACKUP_DIR / f"data_{ts}.js"
    shutil.copy2(DATA_JS, dst)
    return dst

# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    t0 = datetime.now()
    ts = t0.strftime("%Y%m%d_%H%M%S")
    step("=" * 68)
    step(f"SCWTS dashboard refresh started  {t0:%Y-%m-%d %H:%M:%S}")

    # --- Step 1: connect ---------------------------------------------------- #
    try:
        step(f"[1/8] Connecting to PostgreSQL {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']} …")
        conn = psycopg2.connect(connect_timeout=20, **DB_CONFIG)
        conn.autocommit = True
    except Exception as ex:
        err(f"CONNECTION FAILED: {ex}")
        write_report(ts, False, [("PostgreSQL connection", False, str(ex))], {}, {}, {}, error=str(ex))
        err("data.js NOT modified. Aborting.")
        sys.exit(1)

    try:
        cur = conn.cursor()
        # --- Step 2: pick mode, build lineage, run exports ------------------ #
        cur_obj = load_current()
        full = supplier_accessible(cur)
        mode = "full" if full else "degraded"

        if full:
            step("[2/8] supplier schema reachable — FULL refresh (all 8 datasets live).")
            build_lineage(cur, "full")
            carried = []
        else:
            warn("[2/8] supplier schema NOT reachable for this role — DEGRADED refresh.")
            warn("       components + purchaseOrders will be CARRIED FORWARD from current data.js;")
            warn("       combos/mapping/listings/orders/traffic/returns refresh live from public.")
            if not cur_obj or not cur_obj.get("components"):
                msg = ("Degraded mode needs component SKUs from the current data.js to seed the "
                       "lineage, but data.js is missing or has no components. Cannot refresh.")
                err(msg)
                write_report(ts, False, [("degraded-mode seed", False, msg)], {}, {}, {}, error=msg)
                sys.exit(1)
            nc_skus = [r[0] for r in cur_obj["components"] if r and r[0]]
            step(f"       seeded {len(set(nc_skus))} new-component SKUs from data.js.")
            build_lineage(cur, "degraded", nc_skus)
            carried = list(SUPPLIER_DATASETS)

        step(f"[2/8] Running dataset exports (mode={mode}) …")
        new_ds = {}
        for name in SCHEMA:                       # deterministic order
            if name in carried:
                new_ds[name] = [list(r) for r in cur_obj.get(name, [])]
                step(f"        - {name:<18} {len(new_ds[name]):>7,} rows  (carried forward)")
            else:
                new_ds[name] = fetch_dataset(cur, name)
                step(f"        - {name:<18} {len(new_ds[name]):>7,} rows  (live)")

        # --- Step 3: build fresh dataset + KPIs (in memory) ----------------- #
        step("[3/8] Computing KPIs from live data …")
        kpi_new = compute_kpis(new_ds)
        step(f"        orders={kpi_new['orders']:,}  units={kpi_new['units']:,}  "
             f"revenue=£{kpi_new['revenue']:,}  returns={kpi_new['returns']}  "
             f"impressions={kpi_new['impressions']:,}")

        # --- Step 4: validate against current data.js ----------------------- #
        step("[4/8] Validating (live export vs current data.js) …")
        kpi_cur = compute_kpis(cur_obj) if cur_obj else {}
        diffs = diff_counts(new_ds, cur_obj)
        passed, checks = validate(new_ds, cur_obj, kpi_new, kpi_cur, carried)
        for name, ok, detail in checks:
            (step if ok else warn)(f"        {'PASS' if ok else 'FAIL'}  {name} — {detail}")

        # --- Step 5: validation report -------------------------------------- #
        step("[5/8] Writing validation report …")
        report = write_report(ts, passed, checks, diffs, kpi_new, kpi_cur, mode=mode, carried=carried)
        step(f"        report -> {report}")

        # --- Steps 6/7/8: replace only if PASS ------------------------------ #
        if passed:
            step("[6/8] Validation PASSED — backing up + replacing data.js …")
            bak = backup_current()
            if bak: step(f"        backup -> {bak}")
            content = build_datajs(new_ds, kpi_new, mode, carried)
            DATA_JS.write_text(content, encoding="utf-8")
            checksum = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
            step(f"        wrote {DATA_JS}  ({len(content):,} bytes, sha256:{checksum})")
            result = "PASS — data.js updated"
        else:
            err("[6/8] Validation FAILED — keeping previous data.js (NOT replaced).")
            result = "FAIL — data.js kept"

        # --- Step 7: refresh log summary ------------------------------------ #
        t1 = datetime.now()
        step("[7/8] Refresh summary")
        step(f"        start={t0:%H:%M:%S}  end={t1:%H:%M:%S}  duration={(t1-t0).total_seconds():.1f}s")
        step(f"        datasets={list(new_ds)}")
        step(f"        counts={ {k: len(v) for k,v in new_ds.items()} }")
        step(f"[8/8] RESULT: {result}")
        step("=" * 68)
        sys.exit(0 if passed else 3)

    except Exception as ex:
        err(f"EXPORT/VALIDATION ERROR: {ex}")
        write_report(ts, False, [("export/validation", False, str(ex))], {}, {}, {}, error=str(ex))
        err("data.js NOT modified due to error.")
        sys.exit(1)
    finally:
        try: conn.close()
        except Exception: pass


if __name__ == "__main__":
    main()

# =============================================================================
# CRON SETUP  —  run every day at exactly 10:00 AM
# =============================================================================
#   1. Install the driver once:      pip install psycopg2-binary
#   2. Edit the current user's crontab:   crontab -e
#   3. Add this line (adjust the python path with `which python3`):
#
#        0 10 * * * /usr/bin/python3 \
#          /home/led-247/Supplier-to-Customer-Workflow-Tracking-System/dashboard_refresh.py \
#          >> /home/led-247/Supplier-to-Customer-Workflow-Tracking-System/logs/cron.out 2>&1
#
#   4. Verify it is scheduled:        crontab -l
#   5. Ensure cron is running:        systemctl status cron   (Debian/Ubuntu)
#
#   Outputs produced each run:
#     dashboard/data.js                    (updated only on PASS)
#     data_backup/data_<ts>.js             (backup of the previous data.js)
#     validation/validation_report_<ts>.md (PASS/FAIL + diffs + reasons)
#     logs/refresh.log                     (appended every run)
#     logs/cron.out                        (stdout/stderr captured by cron)
# =============================================================================
