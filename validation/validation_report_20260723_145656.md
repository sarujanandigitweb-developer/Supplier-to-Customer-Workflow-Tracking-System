# Dashboard Refresh Validation — 20260723_145656

**Result:** ❌ FAIL  ·  Mode: **DEGRADED**  ·  Window 2026-01-01 → 2026-07-23


> ⚠️ **Degraded refresh** — the connected role lacks USAGE on the `supplier` schema, so **components, purchaseOrders** were carried forward unchanged from the previous `data.js`. The other datasets refreshed live from `public`. Grant this role read access to `supplier` (or run with the broader MCP role) for a full refresh of components + purchase orders.

## Dataset reconciliation (live export vs current data.js)

| Dataset | data.js (current) | New export | Added | Removed | Match |
|---|---:|---:|---:|---:|:--:|
| components | 456 | 456 | +0 | -0 | ✅ |
| combos | 4,381 | 4,389 | +8 | -0 | ↕️ |
| componentComboMap | 4,553 | 4,564 | +11 | -0 | ↕️ |
| listings | 1,393 | 1,425 | +33 | -1 | ↕️ |
| orders | 5,169 | 5,215 | +59 | -13 | ↕️ |
| traffic | 7,567 | 1,082 | +10 | -6,495 | ↕️ |
| returns | 269 | 269 | +1 | -1 | ↕️ |
| purchaseOrders | 93 | 93 | +0 | -0 | ✅ |

## KPI totals (recalculated from PostgreSQL — not hardcoded)

| KPI | Current data.js | New export | Δ |
|---|---:|---:|---:|
| new_components | 456 | 456 | 0 |
| combos | 4381 | 4389 | 8 |
| listed_combos | 3689 | 3697 | 8 |
| non_listed | 692 | 692 | 0 |
| listings | 1932 | 1970 | 38 |
| order_lines | 5179 | 5225 | 46 |
| orders | 4763 | 4807 | 44 |
| units | 8580 | 8652 | 72 |
| revenue | 160371.29 | 161617.86 | 1246.5699999999779 |
| returns | 272 | 272 | 0 |
| returns_amazon | 186 | 186 | 0 |
| returns_ebay | 47 | 47 | 0 |
| returns_shopify | 39 | 39 | 0 |
| traffic_rows | 7567 | 1082 | -6485 |
| impressions | 193563630 | 9555257 | -184008373 |
| clicks | 516541 | 32449 | -484092 |
| purchase_orders | 93 | 93 | 0 |
| suppliers | 34 | 34 | 0 |
| containers | 13 | 13 | 0 |

## Validation checks

| Check | Result | Detail |
|---|:--:|---|
| components: non-empty | ✅ | 456 rows |
| combos: non-empty | ✅ | 4389 rows |
| componentComboMap: non-empty | ✅ | 4564 rows |
| listings: non-empty | ✅ | 1970 rows |
| orders: non-empty | ✅ | 5225 rows |
| returns: non-empty | ✅ | 272 rows |
| purchaseOrders: non-empty | ✅ | 93 rows |
| combos: unique key | ✅ | 0 dup combo_sku |
| mapping: unique pairs | ✅ | 0 dup pairs |
| traffic: no fan-out | ✅ | 0 dup (source,ref_id,market_place) |
| purchaseOrders: unique PO | ✅ | 0 dup PO |
| KPI: revenue > 0 | ✅ | £161,617.86 |
| KPI: orders > 0 | ✅ | 4807 orders |
| KPI: returns channels sum | ✅ | 272 = 186+47+39 |
| components: change guard | ✅ | 456 rows (carried forward, unchanged) |
| combos: change guard | ✅ | 4381 -> 4389 (1.00x) |
| componentComboMap: change guard | ✅ | 4553 -> 4564 (1.00x) |
| listings: change guard | ✅ | 1932 -> 1970 (1.02x) |
| orders: change guard | ✅ | 5179 -> 5225 (1.01x) |
| returns: change guard | ✅ | 272 -> 272 (1.00x) |
| purchaseOrders: change guard | ✅ | 93 rows (carried forward, unchanged) |
| traffic: change guard | ❌ | 7567 -> 1082 (0.14x) |

## ❌ Failure analysis

- **traffic: change guard** — 7567 -> 1082 (0.14x). Likely cause: a broken/renamed source table, an incorrect WHERE/JOIN, or a partial export. data.js was **NOT** replaced; previous dashboard kept.
