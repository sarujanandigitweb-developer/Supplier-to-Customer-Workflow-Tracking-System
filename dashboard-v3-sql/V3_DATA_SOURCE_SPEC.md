# Dashboard V3 — Data Source Specification
**Status:** discovery complete, container mapping built, payload build not yet run.
**Date:** 2026-07-31

V3 is independent of V2. V2 is untouched and still works.

---

## 1. CRITICAL — the old database is being dismantled

V2 reads `order_management_copy` (149.28.134.54:5435). During this session its tables
were emptied/dropped mid-flight:

| Table | State |
|---|---|
| `public.inv_products` | **0 rows** |
| `public.inv_product_combo` | **0 rows** |
| `public.amazon_returns` | **0 rows** |
| `public.ebay_returns` / `shopify_returns` | **DROPPED** |
| `supplier.*` (all 6 tables) | **0 rows** |
| `public.listing_data` | 335,981 (still live) |
| `public.order_transaction` | 1,244,420 (still live) |
| `public.traffic_data` / `ppc_performance` | 9.5M / 26M (still live) |

**V3 must therefore be built on the new `ledsone` database**, reached via the
`Ledsone_postgres` MCP connector (user `dbhub_readonly`). V2's own scheduled run
will start failing — its hard gates already caught it and correctly refused to publish.

## 2. MCP connector → database map

| Connector | Database | Notes |
|---|---|---|
| `Ledsone_postgres` | **`ledsone`** | NEW. 18 schemas, fully documented. Supplier data in `suppliers` (note the **s**). |
| `postgres_2` | `order_management_copy` | The original DB. Not new. |

No direct (psycopg2) credentials for `ledsone` exist on this machine — all access is
via MCP only. Bulk extraction must therefore be chunked.

## 3. Container → Component SKU (the V3 source of truth)

From `dashboard-v3-data/New Containers to UK - 2026 .xlsx`, parsed by
`read_sheet.py` (stdlib only — no openpyxl in this environment) into
`sheet_containers.json`.

| Container | SKUs |
|---|---|
| Container 11 | 19 |
| Container 12 | 82 |
| Container 13 | 32 |
| Container 14 | 30 |
| Container 15 | 2 |
| Container 16 | 45 |
| Container 17 | **0 — tab is empty in the sheet** |
| **Total** | **210 rows / 209 distinct** |

- `LSGLULSG` appears in **both** Container 12 and 13 (legitimate — same part shipped twice).
- **209 of 210** resolve in `inventory.products`; **1 does not** — must be reported, not silently dropped.

## 4. Field → source mapping (all in `ledsone`)

| V3 column | Source |
|---|---|
| ~~Supplier~~ | **REMOVED per spec** |
| ~~Received Date~~ | **REMOVED per spec** |
| Container | Google Sheet tab name (source of truth) |
| Component SKU | Sheet, validated against `inventory.products.sku` |
| Component Image | `inventory.products` → fallback `listings.*.main_image_url`; sheet has `Image Link` too |
| Component Created | `inventory.products.created_at` |
| Combo SKU | **Derived** — no `inv_product_combo` equivalent exists in `ledsone`. Two rules:<br>① pack: `sku ~ '^<COMP>[0-9A-Z]*PK$'`<br>② true combo: `sku LIKE '%+%' AND ('+'\|\|sku\|\|'+') LIKE '%+<COMP>+%'`<br>→ **293 combos** derived from the 209 components |
| Combo Image / Created | `inventory.products` (same row as the combo SKU) |
| Marketplace | Which listing table the row came from |
| Listing Status / Listed Date / URL | `listings.amazon_listings`, `ebay_listings`, `shopify_listings`, `bandq_listings`<br>(cols: `sku, mapped_sku, status, main_image_url, listing_url, is_parent, wrong_sku, created_at`) |
| Impressions / Clicks | `business_reports.amz_traffic_by_asin` (sessions/page_views, by `sku`)<br>`business_reports.ebay_traffic_data` (impressions/views, by `item_id`)<br>plus `amazon_campaigns.performance_data`, `ebay_campaigns.performance_data` |
| Orders / Units / Revenue | `order_management.orders` + `order_item_info` (`item_sku`/`real_sku`, `item_quantity`, `item_price`); marketplace via `order_management.market_place` lookup (id → UK=23, DE=10, US=24 …) |
| Total Returns / Return Rate | `customer_service.amazon_returns` (220), `customer_service.ebay_returns` (31,747) |
| Top Reason | `amazon_returns.reason`, `ebay_returns.reason` |
| **Average Feedback** | ✅ **NOW AVAILABLE** — `customer_service.ebay_orders_customer_feedbacks`<br>313,634 rows, cols `item_id, rating_star, buyer_score, comment, date`<br>Join `item_id` → `listings.ebay_listings.item_id`. **This did not exist in the old DB** — the V2 column that renders "No Reviews" can finally be populated (eBay only). |

## 5. Still-missing / risks

1. **No product-level combo mapping table** in `ledsone`. The `+`/`PK` naming
   derivation above is a convention-based inference, not a declared relationship.
   `order_management.order_combo` only covers combos that have been *ordered*.
   → Worth asking whether `inv_product_combo` will be migrated.
2. **1 sheet SKU not in `inventory.products`** — needs identifying and reporting.
3. **Container 17 tab is empty** — confirm with the manager whether it should have data.
4. Amazon traffic is **sessions/page-views**, not impressions/clicks — not the same
   metric V2 showed. Needs a decision on which to display.

## 6. Build order (remaining)

1. `build_v3.py` — extract per container via MCP, assemble `payload_v3.json`
2. `make_html_v3.py` — clone V2's composer, drop Supplier + Received Date columns,
   add the Container tab list, keep everything else identical
3. Validate: container→component, component→combo, combo→marketplace, no
   duplicate `(product, marketplace)` rows (the V2 fan-out bug — do not repeat it),
   images, listing status/date, traffic, orders, revenue, returns

## 7. Files

```
dashboard-v3-data/   New Containers to UK - 2026 .xlsx   (manager's sheet)
                     ... - Container 11.csv
dashboard-v3-sql/    read_sheet.py            parses the xlsx  -> sheet_containers.json
                     sheet_containers.json    Container -> SKU + ASINs + platform flags
                     _sheet_cte.sql           reusable SQL CTE of the mapping
                     V3_DATA_SOURCE_SPEC.md   this file
```
