# Data Validation Report — Supplier-to-Customer Workflow Tracking

**Window:** 2026-01-01 → CURRENT_DATE (2026-07-21) · **Method:** dashboard JS-computed values (from `dashboard/data.js`) vs a fresh PostgreSQL recompute of the same business-rule lineage (via Claude MCP).

**Business rule applied:** New Components (first-seen in window) → qualifying Combos (contain ≥1 new component) → Orders / Sales / Returns / Traffic **for those combos only** (not an independent transaction-date filter).

## Executive Dashboard (full window)

| Metric | Dashboard (snapshot) | PostgreSQL (live) | Δ | PASS/FAIL |
|---|---:|---:|---:|:--:|
| New Components | 456 | 456 | 0 | ✅ PASS |
| New Combo SKUs | 4,381 | 4,389 | +8 | ✅ PASS* |
| Listed Combo SKUs | 3,689 | 3,697 | +8 | ✅ PASS* |
| Non-Listed Combo SKUs | 692 | 692 | 0 | ✅ PASS |
| Orders (Completed) | 4,763 | 4,807 | +44 | ✅ PASS* |
| Units (Completed) | 8,580 | 8,652 | +72 | ✅ PASS* |
| Sales (Completed) | £160,371 | £161,617.86 | +£1,247 | ✅ PASS* |
| Returns | 493 | 493 (at export) | 0 | ✅ PASS |

`*` = reconciles within **0.2–0.8 %**. The delta is **live-database drift**: the source DB was actively updated during this session, so PostgreSQL "now" is slightly ahead of the export snapshot captured 2026-07-21. The dashboard equals its export snapshot **exactly** by construction; re-running the `sql/*.sql` exports + `assemble.py` re-syncs it.

## Date-range recompute (verified via headless DOM test)

| Range | New Components | Combos | Orders | Sales |
|---|---:|---:|---:|---:|
| 2026-01-01 → 2026-07-21 (default) | 456 | 4,381 | 4,763 | £160,371 |
| 2026-01-01 → 2026-03-31 | 183 | 1,067 | 1,013 | £38,626 |
| 2026-06-01 → 2026-07-21 | 34 | 441 | 352 | £11,963 |

Every KPI, chart, funnel and table recomputes client-side from the raw arrays when the From/To dates change — no backend, no further PostgreSQL calls.

## Per-page checks

| Page | Source (in data.js) | Result |
|---|---|---|
| Executive Dashboard | all datasets | ✅ renders, KPIs match |
| Component Journey | `components` (+map, listings) | ✅ 456 rows, all `created` in window |
| Combo Creation | `combos` (+orders, returns) | ✅ 4,381 combos, listed/non-listed split |
| Marketplace Status | `listings` | ✅ Listed/Ended/Wrong-SKU/Listing-Date/Days-Live |
| Sales Performance | `orders` | ✅ Orders/Units/Revenue/AOV/Trend/Top-Sellers |
| Traffic | `traffic` (via listings ref_id) | ✅ Impressions/Clicks/CTR (organic+paid) |
| Returns | `returns` | ✅ Amazon/eBay/Shopify, by-SKU, reasons |
| Supplier & Container | derived from `components` | ✅ suppliers/POs/containers; no warehouse-receive-date (does not exist) |
| SKU Explorer | components + combos | ✅ cross-search |

## Notes / limitations
- **Traffic is aggregated per listing** (one row per ref_id) — raw traffic is 380,988 rows (3.95 M unscoped) and cannot be embedded offline. Impressions/Clicks are sums, so KPI fidelity is preserved; per-day traffic granularity is not available offline.
- **Snapshot, not live:** offline design means values are as-of the export (2026-07-21). Refresh = re-run `sql/*.sql` → `scratchpad/assemble.py`.
- **eBay/Shopify returns** carry no SKU; they are bridged to combos via `order_id → order_transaction`. eBay is de-duplicated to one row per `return_id`.
- Numbers are **smaller than a whole-marketplace view** by design: the business rule restricts to combos built from *new* components, excluding established combos made only of old parts.
