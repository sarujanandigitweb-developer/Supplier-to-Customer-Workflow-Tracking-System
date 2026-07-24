# SKILL FILE — 2026-07-24 — SCWTS — REQ-01-D03

Supplier's Basket → Customer's Home: data-model correction (inv_products /
inv_product_combo), listing-date-driven scope, UI defect fixes, and hub publish.

---

## METADATA BLOCK

```yaml
date: 2026-07-24
developer: Sarujanan
project: Supplier-to-Customer Workflow Tracking System
project_code: scwts
phase: Development - phase 03
requirement_id: REQ-01
deliverable_id: D03
status: Completed
evidence_location: /home/led-247/Supplier-to-Customer-Workflow-Tracking-System/
  - dashboard-v1/index.html
  - dashboard-v1/DATA_FIX_REPORT.md
  - dashboard-v1-sql/build_new_scope.py
  - dashboard-v1-sql/build_listing_driven.py
  - dashboard-v1-sql/04_listings.sql
  - dashboard-v1-sql/01_components.sql
  - dashboard-v1-sql/supplier_meta.psv
  - dashboard-v1-sql/component_meta_all.psv
  - dashboard-v1-update/push_to_hub.js
  - daily_works_logs/2026-07-24__sarujanan__scwts_daily-activities.csv
blos_keys_used:
  - reporting_period_start
  - new_product_definition
  - listing_date_source
  - sku_normalisation_rule
  - combo_component_mapping
  - row_grain
hardcoded_thresholds:
  - reporting_window_start = 2026-01-01
  - sku_suffix_regex = '[_-][A-Za-z]{2,4}$'
  - tracking_rows_expected = 2852        # regression anchor (NEW scope)
  - combos_expected = 1542
  - components_expected = 826
  - revenue_expected = 67733.17
  - drawer_max_height_query = 770px
three_am_standard: TRUE
llm_queryable: TRUE
company_knowledge_candidate: TRUE
domain: Ecommerce Operations - Supplier to Customer Workflow
User: Varmen
Benefit status: Pass
```

---

## 1. SYSTEM STATE (before today)

- `dashboard-v1` master tracking page existed but its data was derived from an
  **activity-union** row model built on `supplier.order_items` lineage.
- Components were derived by **splitting the combo SKU string on `+`**.
- Listing rows were filtered with `is_child = 1` and **no `created_at` window**.
- `Container Arrival` displayed `expected_completion_date` (a forecast).
- The page was not published anywhere; the file was not named `index.html`.
- The inventory master tables (`inv_products`, `inv_product_combo`) were unknown
  to the pipeline.

## 2. WHAT WAS DONE

### 2.1 UI / layout defects (fixed, then frozen)
- **Header dead band + KPI overlap**: `.appbar` had `height:104px` but, as a flex
  item of a `100vh` `.main`, it shrank to 48px while `.filterbar` stayed pinned at
  `top:104px` — leaving a 56px gap and covering the **top 34px of every KPI card**.
  Fixed with `flex:0 0 auto` + removal of the hardcoded sticky offset.
- **Accessibility**: all 9 `<label>` elements were unassociated (no `for`), plus two
  `<label>&nbsp;</label>` spacers and an unlabelled `#perpage` select. All fixed.
- **Tooltip vs sticky column**: `placeTip()` used the cell's raw viewport `left`; when
  the table scrolled right the cell sat under the pinned Record ID column (measured
  −79 … −479px) so the tooltip was drawn over "REC-000xx". Clamped to the sticky
  column's right edge (155 vs 147) at every scroll offset.
- **Detail drawer**: rebuilt as a full-height ONE-PAGE view (no scroll) showing **one
  image per component** in the combo. Verified `scrollHeight == clientHeight` at
  1034/900/768/700/660px.

### 2.2 Deployment
- Vercel returned `404: NOT_FOUND` because `dashboard-v1/` had no `index.html`.
  Renamed the page; documented Root Directory = `dashboard-v1`.
- Published to the **Varman AIOS Hub** via `push_to_hub.js` (member `sarujanan`,
  slug `supplier-to-customer-workflow-tracking`) — upsert, so re-push updates in place.

### 2.3 DATA MODEL CORRECTION (the main deliverable)
Discovered and validated the real product model:

| Object | Role |
|---|---|
| `public.inv_products` | SKU **master**; `sku` UNIQUE (43,844/43,844); `created_at` defines a NEW product |
| `public.inv_product_combo` | `product` = COMBO id, `inventory` = COMPONENT id, `pack_count` = qty; `product_combo` is a row PK, **not** an FK; `product = inventory` marks a single |
| `public.listing_data` | listing facts; `created_at` **is** the Listing Date (no `created_date` column exists) |

**SKU normalisation** (mandatory): `COALESCE(NULLIF(TRIM(mapped_sku),''),TRIM(sku))`
then strip one `[_-][A-Za-z]{2,4}$` country/channel suffix
(`_DE`, `-IDE`, `-CA`, `_AMN`, `_KR`, `_TH`, …). Resolution 11,558 → **14,658/15,437 (95%)**.

## 3. DEFECTS FOUND (with measurements)

| # | Defect | Evidence |
|---|---|---|
| 1 | Components from `+` string-split | **28,522 / 83,073** split parts (34%) match no real component; true mapping = **120,851** rows. `PHCHPCRYB3PK` never matched `PHCHPCRYB` |
| 2 | Raw SKU matching (no `mapped_sku`, no suffix strip) | 3,879 SKUs unresolved; stripping rescued 3,100 |
| 3 | `is_child = 1` | dropped **1,183 standalone** listings (all with URL/price/image) |
| 4 | "New" from `supplier.order_items` | that is *first purchased* (405 SKUs), counted re-orders as new |
| 5 | Listing scope had no date filter | 12,880/14,977 rows (86%) predated the window, back to **2019-06-26** |
| 6 | `expected_completion_date` shown as arrival | forecast reaching 2026-08-31 → "04-Aug-2026" bug; **no arrival column exists** |

## 4. FINAL SCOPE (approved by the manager)

NEW products only: `inv_products.created_at >= 2026-01-01 AND isdeleted = 0`,
listed on/after 2026-01-01, `is_parent = 0`, `wrong_sku = 0`, non-empty SKU.
**Row grain = one Combo SKU × one marketplace platform.**

## 5. VALIDATION (PostgreSQL vs Dashboard)

| Metric | PostgreSQL | Dashboard | Match |
|---|---:|---:|:--:|
| Tracking rows | 2,852 | 2,852 | OK |
| Distinct combos | 1,542 | 1,542 | OK |
| Components | 826 | 826 | OK |
| NEW components | 103 | 103 | OK |
| Units sold | 3,179 | 3,179 | OK |
| Revenue | £67,733.17 | £67,733.17 | OK |
| Orders | 2,318 | 2,318 | OK |
| Listing date range | 2026-01-01 → 2026-07-23 | same | OK |

Coverage: URLs 2,852/2,852 · images 2,837/2,852 · supplier data on 2,471 rows.

## 6. EXPLAINED DIFFERENCES (not errors)

- **£17,780.66 / 771 units excluded** — sales on marketplaces where the combo has no
  in-window listing; at the combo×platform grain those rows do not exist.
- **1,021 listing rows / 779 SKUs unresolved** (3%) — absent from `inv_products`.
- **393 of 826 components have no supplier record** — `supplier.order_items` history
  only starts 2025-07.
- **2,031 rows had a pre-2026 supplier receipt.** UI `rowDate = crecv || ldate ||
  ccreate` would have hidden them (only 821 visible). Fixed **in data only**: in-window
  receipts stay in *Component Received*, pre-window receipts move to *Notes*, so the
  row anchors to its always-in-window Listing Date. All 2,852 now visible.

## 7. GAPS / RISKS

- `supplier.orders.status_arrived` is **stale**: 395/497 not-arrived, of which **224 are
  overdue** (ETAs as far back as January; e.g. PO `TBO032026DE` shipped, finished
  2026-05-22, ETA 2026-04-26, 89 days overdue). No arrival date exists to fall back on.
- `temp_user` cannot read `supplier.*` — those attributes must be fetched via MCP and
  cached (`supplier_meta.psv`).
- 779 listing SKUs still unresolved against the master.

## 8. NEXT ACTIONS

1. Escalate the stale `status_arrived` flag to purchasing (owner Tamilchelvan).
2. Wire `build_new_scope.py` into the 10:00 daily refresh job.
3. Decide handling for the 779 unresolved SKUs (retire vs map).
