# SCWTS — Daily Dashboard Automation

Fully automated: every day at **11:00** the system fetches fresh PostgreSQL data,
validates it, regenerates the embedded dashboard payload, and publishes the
finished HTML to **Varman AIOS** — no manual step.

## 1. Architecture

```
                    cron  0 11 * * *
                          │
            scripts/refresh_and_publish.sh          (orchestrator, gated)
                          │
   ┌──────────────────────┴───────────────────────┐
   │ STAGE 1  dashboard-v1-sql/build_new_scope.py │
   │                                              │
   │   connect PostgreSQL (env creds)             │
   │        ↓                                     │
   │   SUPPLIER PERMISSION PROBE                  │
   │     supplier.suppliers / orders /            │
   │     containers / order_items                 │
   │     ├─ readable  → fetch supplier chain LIVE │
   │     └─ denied    → log missing GRANTs,       │
   │                    fall back to cache,       │
   │                    CONTINUE (never break)    │
   │        ↓                                     │
   │   FETCH FRESH (no cache, no old JSON):       │
   │     inv_products · inv_product_combo ·       │
   │     listing_data · order_transaction ·       │
   │     traffic_data + ppc_performance ·         │
   │     amazon/ebay/shopify_returns · supplier.* │
   │        ↓                                     │
   │   VALIDATE 13 checks (8 HARD / 5 soft)       │
   │        ↓                                     │
   │   REGENERATE  const PAYLOAD  in index.html   │
   │        ↓                                     │
   │   WRITE validation_<ts>.md + fetch_summary   │
   │   exit 0 = PASS · exit 1 = HARD FAIL         │
   └──────────────────────┬───────────────────────┘
                          │  (stage 2 runs ONLY on exit 0)
   ┌──────────────────────┴───────────────────────┐
   │ SANITY GATE                                  │
   │   HTML readable · ≥ 500 KB ·                 │
   │   markers: const PAYLOAD / #tbl / #tbody /   │
   │            </html>                           │
   └──────────────────────┬───────────────────────┘
                          │
   ┌──────────────────────┴───────────────────────┐
   │ STAGE 2  dashboard-v1-update/push_to_hub.js  │
   │   EXISTING AIOS uploader — reused as-is      │
   │   upsert varman_aios.hub_pages               │
   │   ON CONFLICT (member_name, page_slug)       │
   └──────────────────────┬───────────────────────┘
                          │
              logs/automation.log  (+ execution time, status)
```

A failed build **cannot** overwrite yesterday's good dashboard: stage 2 is gated
on stage 1's exit code *and* the HTML sanity gate.

## 2. Files

### Reused unchanged
| File | Role |
|---|---|
| `dashboard-v1-update/push_to_hub.js` | **Varman AIOS upload** — existing implementation, not reimplemented |
| `dashboard-v1-update/node_modules`, `package.json` | uploader deps |
| `dashboard-v1/index.html` | dashboard shell (only `const PAYLOAD` is replaced) |
| `dashboard-v1-sql/marketplace_view.sql` | standalone marketplace-wise SQL |

### Modified
| File | Change |
|---|---|
| `dashboard-v1-sql/build_new_scope.py` | credentials now env-driven (`PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD`); **supplier permission probe**; supplier chain fetched **live** (cache only as fallback); 13-check dataset validation; writes validation report + fetch summary; non-zero exit on hard failure |

### New
| File | Role |
|---|---|
| `scripts/refresh_and_publish.sh` | orchestrator (cron entry), gated 2 stages, sanity gate, logging + credential redaction, execution timing |
| `AUTOMATION.md` | this document |
| `validation/validation_<ts>.md` | per-run validation report |
| `validation/fetch_summary_<ts>.json` | per-run machine-readable fetch summary |
| `logs/automation.log` | execution log |
| `logs/cron.out` | raw cron stdout/stderr |

## 3. Scheduler

```cron
0 11 * * * /home/led-247/Supplier-to-Customer-Workflow-Tracking-System/scripts/refresh_and_publish.sh \
           >> /home/led-247/Supplier-to-Customer-Workflow-Tracking-System/logs/cron.out 2>&1
```
Installed (`crontab -l`). Runs daily at 11:00, ~3 minutes.

## 4. Validation

Datasets fetched and reported every run: **Listing Data, Returns, Traffic,
Supplier, Orders, Sales, Inventory, Component Data, Combo Data, Product Images,
Listing URLs**.

**HARD checks** (any failure ⇒ build aborts, nothing published):
1. Inventory: new SKUs present
2. Listing Data: listed rows present
3. Component Data present
4. Combo Mapping present
5. Component Mapping — every row has a description
6. Every row has an anchor date (`crecv||ldate||ccreate`)
7. Listed rows all carry a Listing Date
8. Listing Dates within the window (≥ 2026-01-01)

**Soft checks** (recorded, never block): Listing URLs, Product Images,
Orders/Sales, Traffic, Returns, supplier access + cache integrity.

Latest run: **PASS** — 4,792 rows (3,085 Listed / 1,707 Not-Listed), 3,383 new
SKUs, 1,866 components, 2,838 combos/packs, 2,741 orders, revenue £75,728.69,
50.1 M impressions, 225 returns.

## 5. Supplier validation

Probed with the project's `temp_user` **before** any supplier value is used:

| Table | Status |
|---|---|
| `supplier.suppliers` | readable — 47 rows |
| `supplier.orders` | readable — 267 rows |
| `supplier.containers` | readable — 25 rows |
| `supplier.order_items` | readable — 4,029 rows |

`temp_user` now **has** `USAGE` on the `supplier` schema, so the chain
(Supplier Name → Supplier ID → Container → Purchase Order → Order Items) is
fetched **live every run** — 1,541 SKUs, 100 % with Supplier Name, 1,488 with a
Container. The old PSV cache is no longer used.

If the grant is ever revoked the run does **not** break: it logs the exact
missing tables and the fix
(`GRANT USAGE ON SCHEMA supplier TO temp_user; GRANT SELECT ON … TO temp_user;`),
falls back to `dashboard-v1-sql/supplier_fresh.psv`, and continues — supplier
columns simply blank out for uncovered SKUs.

## 6. Error handling / artifacts

Never silently fails. Every execution produces:
- **execution log** — `logs/automation.log` (stage results, byte count, exit code)
- **validation report** — `validation/validation_<ts>.md` (datasets, 13 checks, supplier)
- **fetch summary** — `validation/fetch_summary_<ts>.json`
- **upload status** — logged `stage 2 publish: OK|FAILED`
- **execution time** — logged in seconds

Credentials are never printed; any connection string appearing in subprocess
output is redacted from the log.

## 7. Manual run

```bash
/home/led-247/Supplier-to-Customer-Workflow-Tracking-System/scripts/refresh_and_publish.sh
tail -20 logs/automation.log
```
To override credentials, export `PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD`
or create a `.env` beside the project root (`chmod 600`).
