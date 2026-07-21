# Data Validation Results — Live PostgreSQL

**Title:** Data Validation Results
**Purpose:** Record the live PostgreSQL validation of the values rendered by the dashboard for the reporting period, with record counts and limitations.
**Business Question:** *"Do the numbers shown on the dashboard match live PostgreSQL for March 2026 → current date?"*

---

## Validation Window
**Reporting period:** 2026-03-01 → CURRENT_DATE (2026-07-21). **Snapshot captured:** 2026-07-21. **Total records loaded:** 108,341.

## Validated Values (dashboard snapshot vs source)

| Metric | Dashboard value | Source table | Notes |
|---|---|---|---|
| New Components (since Mar) | 349 | `components_sot_skus` / `supplier.order_items` | 1,390 order lines behind them |
| Combo SKUs Created (since Mar) | 6,274 | `listing_data` combos (`'+'`) | period-scoped |
| Listed Combo SKUs | 16,015 | `listing_data` (`wrong_sku=0`) | total listed across channels |
| Non-Listed Combo SKUs | 8,596 | `listing_data` vs combo universe | gap analysis |
| Suppliers | 47 | `supplier.suppliers` | full table |
| Purchase Orders | 250 (99 since Mar) | `supplier.orders` | full / period |
| Containers | 24 (16 finalized) | `supplier.containers` / `final_containers` | full table |
| Orders | 97,050 | `order_transaction` (Completed) | period-scoped |
| Units Sold | 158,685 | `order_transaction` | period-scoped |
| Sales (Revenue) | £2,304,870.01 | `order_transaction.order_total` | AOV £23.75 |
| Return Lines | 4,569 | returns tables | Amazon 3,297 / eBay 906 / Shopify 366 |
| Return Qty (Amazon) | 4,258 | `amazon_returns.qty` | SKU-level |

## Channel Distribution (validated)
| Channel | Listings | Combo SKUs |
|---|---|---|
| shopify | 52,659 | 13,025 |
| amazon | 40,734 | 18,333 |
| ebay | 13,946 | 15,863 |
| B&Q | 3,843 | 1,511 |

## Combo statistics (validated)
Total components 1,500 · marketplace combos created 6,274 · supplier-defined combos 65 · combo links 76 · avg components/combo (sample) 2.4.

## Limitations found during validation
1. **Warehouse Receive Date — NOT FOUND.** Arrival shown only via `supplier.orders.status_arrived`. No placeholder value is displayed.
2. **Impressions / Clicks — not in snapshot.** `traffic_data` (9.3M) + `ppc_performance` (25.8M) exist in the DB but the connection pool closed during the pull, so the Sales page shows an explicit note instead of fabricated values.
3. **Listing Date — proxy.** `listing_data` has `row_update`/`end_date` only; first-listed date is approximated by earliest sale.
4. **eBay / Shopify returns — no SKU column.** Per-SKU return detail is Amazon-only; eBay/Shopify are counted at line/order level.
5. **Supplier schema is connection-dependent** — validated as populated on 2026-07-21; must be re-confirmed live before each refresh.

---

| Field | Value |
|---|---|
| **Source** | `dashboard/data.js` snapshot vs `public.*` / `supplier.*` live tables; `sql/validation_queries.sql` |
| **Evidence** | Meta `totalRecordsLoaded=108,341`; per-metric row counts above |
| **Status** | ✅ PASS for 13 metrics; 1 gap (receive date) + 1 deferred (traffic/ppc) disclosed |
| **Owner** | Dashboard Development Team |
| **Reviewer** | Varmen |
| **Next Step** | Re-pull snapshot with traffic/ppc; re-validate after purchasing-backend replication |
| **Pass/Fail Rule** | PASS when each rendered metric equals its live PostgreSQL value for the reporting window (± snapshot timing), and every gap is disclosed |
| **Known Limitations** | Snapshot timing vs "Today"; traffic/ppc excluded; receive-date absent; eBay/Shopify returns lack SKU |
