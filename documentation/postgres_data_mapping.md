# PostgreSQL Data Mapping — Supplier-to-Customer Workflow

**Title:** PostgreSQL Data Mapping
**Purpose:** Map every dashboard data requirement to its verified PostgreSQL schema, table, keys, relationships, and usability status.
**Business Question:** *"For each stage of the supplier-to-customer journey, exactly which PostgreSQL table, key, and join produces the value shown on the dashboard?"*

---

## Mapping Table
All row counts are **live full-table counts** discovered **2026-07-21** via the `claude_ai_postgres` MCP. "Status" is usability for the dashboard.

| Requirement | Schema | Table | Primary Key | Join Keys | Relationship | Row Count | Status |
|---|---|---|---|---|---|---|---|
| **Supplier** | `supplier` | `suppliers` | `id` | `orders.supplier_id → suppliers.id` | 1 supplier → N orders | 47 | ✅ Usable |
| **Orders (Purchase Order)** | `supplier` | `orders` | `id` | `order_items.order_id → orders.id`; `orders.supplier_id → suppliers.id`; `orders.container_id → containers.id` | 1 PO → N order_items; 1 supplier → N POs | 250 | ✅ Usable |
| **Components (new)** | `public` | `components_sot_skus` (+ `components_sot_attributes`, `components_sot_attribute_values`) | `id` | `attribute_values.sot_sku_id → skus.id`; `skus.sku` joins listings/sales/combos | EAV: 1 SKU → N attribute values (343 attributes) | 1,813 skus / 343 attrs / 213,554 values | ✅ Usable |
| **Components (supplier-side)** | `supplier` | `order_items` | `id` | `order_items.order_id → orders.id` | 1 PO → N line items | 3,826 | ✅ Usable |
| **Combo SKUs** | `public` | `listing_data` / `inv_final_stock` / `order_transaction` (derived) | table `id` | combo `sku LIKE '%+%'`; split on `'+'` → `components_sot_skus.sku` | 1 combo → N component parts | 32,681 / 20,026 / 16,975 distinct combos | ✅ Usable (derived) |
| **Component → Combo relationship** | `public` / `supplier` | derived from `'+'` split; `supplier.child_item_products` | `child_item_products.id` | part_sku = `components_sot_skus.sku`; `child_item_products` bridges parent↔child | N components ↔ N combos | 1,339 of 1,812 component SKUs matched to combo parts; 76 supplier links | ✅ Usable (derived) |
| **Containers** | `supplier` | `containers` (+ `final_containers`) | `id` | `orders.container_id → containers.id` (text/id); `order_items.assigned_container_id` | 1 container → N POs/items | 24 (+16 final) | ✅ Usable |
| **Marketplace Listings** | `public` | `listing_data` | `id` | `sku` / `mapped_sku` → component/combo; `ref_id`+`which_channel` → traffic/ppc | 1 SKU → N channel listings | 332,370 (filter `wrong_sku=0`) | ✅ Usable |
| **Traffic (impressions/clicks)** | `public` | `traffic_data` (organic) + `ppc_performance` (paid) | table `id` | `ref_id`+`market_place`+`which_channel`/`source`+`sub_source`; SKU via `listing_data` bridge | ASIN/item_id ↔ SKU (bridged) | 9,340,574 / 25,774,052 | ⚠️ Usable in DB; NOT in current snapshot |
| **Sales / Orders** | `public` | `order_transaction` | `id` (`order_id` business key) | `sku` → components/combos; `asin`/`item_id`/`product_id` → traffic/ppc; `order_id` → returns/expenses | 1 order → N lines; SKU↔ASIN bridge | 1,237,523 | ✅ Usable |
| **Returns** | `public` | `amazon_returns` + `ebay_returns` + `shopify_returns` + `return_by_cs_team` | `id` | `amazon_returns.sku` / `order_id → order_transaction.order_id` | 1 order → N return lines (SKU on Amazon only) | 4,688 / 31,319 / 1,781 / 28,195 | ✅ Usable (Amazon SKU-level; eBay/Shopify no SKU) |
| **Marketplace Listing Date** | `public` | `listing_data` (`row_update`, `end_date`) | `id` | `sku`/`ref_id` | last-update timestamp only; no first-listed date | 332,370 | ⚠️ Partial (proxy = first `order_date`) |
| **Warehouse Receive Date** | `supplier` | `orders` (`status_arrived`, `finished_date`, `confirmed_date`, `expected_completion_date`) | `id` | `orders.id` | arrival flag only; **no receive-date column anywhere** | 250 | ❌ NOT FOUND |

## Channel / Source consistency (join rule)
| `traffic_data.which_channel` | `order_transaction.source_name` | `ppc_performance.source` |
|---|---|---|
| 1 | `AMAZON` | 1 |
| 2 | `EBAY` | 2 |
| 3 | `SHOPIFY` | 3 |

`ref_id` alone is never sufficient — always combine `ref_id + market_place + channel/source + sub_source + date range`. Stock/listing joins from traffic/ppc must go **through `listing_data`** (`wrong_sku=0`, prefer `mapped_sku`).

---

| Field | Value |
|---|---|
| **Source** | `claude_ai_postgres` MCP curated table definitions + live counts (2026-07-21) |
| **Evidence** | `evidence/postgres_discovery_evidence.md`; `sql/discovery_queries.sql` |
| **Status** | ✅ COMPLETE — 13 usable mappings, 1 NOT FOUND (Warehouse Receive Date) |
| **Owner** | Dashboard Development Team |
| **Reviewer** | Varmen; supplier/purchasing → Tamilchelvan |
| **Next Step** | Add a true listing-created date and warehouse receive date once the purchasing backend is replicated |
| **Pass/Fail Rule** | PASS when every mapped requirement resolves to a real table+key with a non-zero row count OR is explicitly marked NOT FOUND |
| **Known Limitations** | Traffic/PPC not in snapshot; Listing Date is a proxy; Warehouse Receive Date absent; combo relationship is derived (no populated FK bridge at scale) |
