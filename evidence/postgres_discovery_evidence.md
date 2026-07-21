# PostgreSQL Discovery Evidence

**Title:** PostgreSQL Discovery Evidence
**Purpose:** Record the verified evidence for the 13 usable data discoveries and the 1 missing field, with row counts, source tables, and discovery date.
**Business Question:** *"What did the PostgreSQL discovery actually find, and can each finding be trusted with hard evidence?"*

---

## Discovery Context
- **Discovery date:** 2026-07-21
- **Method:** Read-only queries via the `claude_ai_postgres` MCP (`list_schemas`, `list_objects`, `get_table_definition`, `execute_sql`) plus a column-level sweep across all user schemas.
- **Scope swept:** 24 user schemas (`public` 44 tables/~91.8M rows; `supplier` 16 tables; `staging_ai` 633 tables; `google_search_console`, `analytics`, etc.).

## 13 Usable Discoveries (with evidence)

| # | Requirement | Source Table(s) | Row Count (2026-07-21) | Evidence |
|---|---|---|---|---|
| 1 | New Components | `public.components_sot_skus` (+attrs/values) | 1,813 / 343 / 213,554 | 6 `source_tab` types; synced from Google Sheets, last sync 2026-06-16 |
| 2 | New Combo SKUs | `listing_data` / `inv_final_stock` / `order_transaction` | 32,681 / 20,026 / 16,975 distinct `sku LIKE '%+%'` | Combo pattern present across listing, stock, and sales |
| 3 | Component → Combo relationship | derived split + `supplier.child_item_products` | 1,339 of 1,812 components matched; 76 supplier links | 6,020 distinct combo parts; 1,339 match component master |
| 4 | Supplier | `supplier.suppliers` | 47 | Real names/codes (e.g. id 35 `CON` "Connector Supplier"), created 2025-07 → 2026-07-16 |
| 5 | Purchase Order | `supplier.orders` | 250 | `order_id`, `order_date`, status flags, `container_id` |
| 6 | Container Number | `supplier.containers` (+`final_containers`) | 24 (+16) | `orders.container_id` → container name |
| 7 | Marketplace Listing Status | `public.listing_data` | 332,370 | 1,376 components listed / 436 not; 4 channels |
| 8 | Listing Date (proxy) | `listing_data.row_update` / first `order_transaction.order_date` | 332,370 | No first-listed column; proxy documented |
| 9 | Impressions | `traffic_data` + `ppc_performance` | 9,340,574 / 25,774,052 | Organic `impression` + paid `impressions`; current to 2026-07-21 |
| 10 | Clicks | `traffic_data` + `ppc_performance` | (same tables) | `click` / `clicks` |
| 11 | Orders | `public.order_transaction` | 1,237,523 | Completed orders; SKU↔ASIN bridge |
| 12 | Sales | `order_transaction.order_total` | 1,237,523 | Revenue where `order_status='Completed'` |
| 13 | Returns | `amazon_returns` / `ebay_returns` / `shopify_returns` / `return_by_cs_team` | 4,688 / 31,319 / 1,781 / 28,195 | Amazon SKU-level; eBay/Shopify order-level |

## 1 Missing Field

| Requirement | Result | Evidence |
|---|---|---|
| **Warehouse Receive Date** | ❌ **NOT FOUND** | No receive-date column in any schema. `supplier.orders` has only `status_arrived` + `confirmed_date`/`finished_date`/`expected_completion_date`. Authoritative gap: `staging_ai.purchasing_intelligence_source_gaps` → `GAP-PURCH-CBM-2026-06-09-01` (HIGH): purchasing backend `order_management_copy @10.8.0.3:5435` not mirrored into this analytics PostgreSQL. |

## Cross-checks performed
- **Supplier schema populated** — confirmed live counts (suppliers 47, orders 250, order_items 3,826, containers 24) after MCP reconnect; earlier connection returned 0 rows (connection-dependent — always re-verify).
- **Combo linkage** — `string_to_array(sku,'+')` parts matched against `components_sot_skus.sku` (1,339/1,812).
- **Listing coverage** — components listed vs not via `listing_data` (`wrong_sku=0`, `COALESCE(mapped_sku,sku)`).

---

| Field | Value |
|---|---|
| **Source** | `claude_ai_postgres` MCP live queries (see `sql/discovery_queries.sql`) |
| **Evidence** | Row counts above; gap register `GAP-PURCH-CBM-2026-06-09-01` |
| **Status** | ✅ 13 usable + 1 NOT FOUND — matches requirement |
| **Owner** | Dashboard Development Team |
| **Reviewer** | Varmen; gap owner Tamilchelvan |
| **Next Step** | Re-run discovery after purchasing backend replication to close the Warehouse Receive Date gap |
| **Pass/Fail Rule** | PASS when each usable finding has a non-zero row count from a named table and the missing field is evidenced by the gap register |
| **Known Limitations** | Supplier-schema availability is connection-dependent; traffic/ppc verified in DB but excluded from the current dashboard snapshot |
