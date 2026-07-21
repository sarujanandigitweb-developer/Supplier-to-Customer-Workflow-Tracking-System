# Data Quality Report

**Title:** Data Quality Report
**Purpose:** Document available fields, missing fields, known limitations, and recommended improvements for the dashboard's data foundation.
**Business Question:** *"How good is the data behind the dashboard, and what would make it better?"*

---

## 1. Available Fields (usable)
| Domain | Key fields | Source |
|---|---|---|
| Supplier | id, name, name_zh, code, created_at | `supplier.suppliers` |
| Purchase Order | order_id, order_date, status_confirmed/finished/shipped/arrived, container_id, expected_completion_date | `supplier.orders` |
| Container | id, main_container, name, current_cbm, status | `supplier.containers`, `final_containers` |
| Component (spec) | sku, product_name, dimensions, material, finish, 343 EAV attributes | `components_sot_skus` + `components_sot_attribute_values` |
| Component (supply) | sku, description, pcs, ctns, cbm, assigned_container_id | `supplier.order_items` |
| Combo | combo sku (`A+B`), parent parts (split) | `listing_data` / `order_transaction` / `inv_final_stock` |
| Listing | sku, mapped_sku, which_channel_name, market_place, status, is_deleted, is_ended, wrong_sku, price | `listing_data` |
| Sales | order_id, order_date, sku, asin, item_id, order_total, order_status | `order_transaction` |
| Traffic/PPC | ref_id, impression(s), click(s), date, market_place, source | `traffic_data`, `ppc_performance` |
| Returns | request_date, order_id, asin, sku (Amazon), qty, reason | `amazon/ebay/shopify_returns`, `return_by_cs_team` |

## 2. Missing / Partial Fields
| Field | State | Impact |
|---|---|---|
| **Warehouse Receive Date** | ❌ NOT FOUND (no column in DB) | Physical receive event not timestamped; only `status_arrived` flag |
| **Listing Date (first listed)** | ⚠️ Partial — only `row_update`/`end_date` | Uses first `order_date` as proxy; "days live" approximate |
| **Impressions / Clicks (in snapshot)** | ⚠️ Deferred — exist in DB, not in `data.js` | Sales page shows a note; funnel/engagement metrics incomplete |
| **Combo FK bridge (populated at scale)** | ⚠️ Partial — `supplier.child_item_products` = 76 rows | Component→combo mostly derived from `'+'` SKU pattern |
| **eBay / Shopify return SKU** | ⚠️ Missing column | Per-SKU returns are Amazon-only |
| **CBM (non-null on new items)** | ⚠️ Sparse | Container-load calculations limited (per gap register) |

## 3. Known Limitations
1. Supplier-schema visibility is **connection-dependent** (0 rows on one MCP target, populated on another) — always re-verify with a live `COUNT(*)`.
2. Dashboard reads a **captured snapshot**, not the live DB — values are correct as of 2026-07-21.
3. Cross-table joins from traffic/ppc to stock **must** go through `listing_data` (`wrong_sku=0`) — direct joins silently return wrong SKUs.
4. Purchasing carton/CBM/receive detail lives in a **separate, un-mirrored backend** (`order_management_copy @10.8.0.3:5435`).

## 4. Recommended Improvements
1. **Replicate the purchasing backend** into `staging_ai` (read-only) to expose Warehouse Receive Date + CBM (owner: Tamilchelvan).
2. **Add a true `listing_created_at`** to `listing_data` at ETL time (removes the proxy).
3. **Refresh the dashboard snapshot** with a stable connection to include `traffic_data` + `ppc_performance` aggregates.
4. **Populate the combo FK bridge** at ETL so component→combo is relational, not string-parsed.
5. **Standardise return SKU** across eBay/Shopify for per-SKU return analysis.
6. **Add a snapshot timestamp banner** so viewers see data recency at a glance.

---

| Field | Value |
|---|---|
| **Source** | Verified table definitions + live counts (2026-07-21); `dashboard/data.js` |
| **Evidence** | `evidence/postgres_discovery_evidence.md`; gap `GAP-PURCH-CBM-2026-06-09-01` |
| **Status** | ✅ Usable foundation with 1 hard gap + several partials |
| **Owner** | Dashboard Development Team |
| **Reviewer** | Varmen; source gaps → Tamilchelvan |
| **Next Step** | Action recommendations 1–3 (highest value) |
| **Pass/Fail Rule** | PASS when available fields are evidenced and every missing/partial field is disclosed with impact |
| **Known Limitations** | Receive date absent; traffic/ppc deferred; combo relationship derived; eBay/Shopify return SKU missing |
