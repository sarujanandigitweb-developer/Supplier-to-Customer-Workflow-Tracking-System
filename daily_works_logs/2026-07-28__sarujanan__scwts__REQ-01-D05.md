# SKILL FILE — 2026-07-28 — SCWTS — REQ-01-D05

Dashboard V2: a new supplier→customer tracking data model built from scratch,
plus the discovery that the supplier schema has **no receipt date** and that a
second, richer container table (`supplier.final_containers`) is the real
system-of-record for shipments.

---

## METADATA BLOCK

```yaml
date: 2026-07-28
developer: Sarujanan
project: Supplier-to-Customer Workflow Tracking System
project_code: scwts
phase: Development - phase 05
requirement_id: REQ-01
deliverable_id: D05
status: Completed
evidence_location: /home/led-247/Supplier-to-Customer-Workflow-Tracking-System/
  - dashboard-v2/index.html                  # delivered dashboard (475 KB, self-contained)
  - dashboard-v2-sql/build_v2.py             # V2 payload builder (live PostgreSQL)
  - dashboard-v2-sql/make_html.py            # HTML composer (reuses V1 design tokens)
  - dashboard-v2-sql/v2_queries.sql          # delivered SQL (Q1-Q9)
  - dashboard-v2-sql/payload_v2.json         # embedded payload
  - dashboard-v2-sql/validation_v2.json      # 21 automated checks
  - varman_aios.hub_pages id=65              # published: sarujanan/supplier-to-customer-workflow-tracking-v2
blos_keys_used:
  - reporting_period_start
  - new_component_definition
  - combo_component_mapping
  - container_receipt_source
  - marketplace_platform_bucket
  - traffic_window_rule
  - return_rate_formula
hardcoded_thresholds:
  - reporting_window_start = 2026-01-01
  - new_components_expected = 178          # regression anchor
  - combos_expected = 223                  # regression anchor
  - component_combo_pairs_expected = 261   # regression anchor
  - combo_rows_expected = 513
  - component_rows_expected = 189
  - sku_suffix_regex = '[_-][A-Za-z]{2,4}$'
  - return_rate = (total_returns / units_sold) * 100
  - drawer_width_px = 640
three_am_standard: TRUE
llm_queryable: TRUE
company_knowledge_candidate: TRUE
domain: Ecommerce Operations - Supplier to Customer Workflow
User: Varmen
Benefit status: Pass (with 2 declared data-source gaps)
```

---

## 1. SYSTEM STATE (before today)

- Dashboard V1 was live and automated (11:00 cron → Varman AIOS), built on a
  **listing-driven** scope of 3,383 new 2026 SKUs across 4,982 rows.
- V1's "Component Received" column was populated from
  `public.inv_products.created_at` — the date the SKU record was created in the
  catalogue, presented to the user as a receipt date.
- Supplier data was known only through four tables (`suppliers`, `orders`,
  `containers`, `order_items`). `supplier.final_containers`, `supplier.invoices`
  and `supplier.order_item_logs` had not been discovered.
- Component images were sourced from `public.listing_data.main_image_url`.
- V1 carried a hard gate, "Revenue reconciles to independent PostgreSQL total",
  added on 2026-07-27 after a revenue-attachment bug.

---

## 2. WHAT CHANGED TODAY

**Built Dashboard V2 as a new data model** (not an update of V1). The scope
chain was inverted: V1 started from listings, V2 starts from **physical stock
received from a supplier**.

Scope chain implemented in `build_v2.py`:

1. **New component** = `inv_products.created_at >= 2026-01-01`, `isdeleted = 0`,
   `sku NOT LIKE '%+%'`, **and** the sku appears in `supplier.order_items`
   (i.e. it was actually purchased) → **178 components**.
2. **Combo** = `inv_product_combo.product` where `.inventory` is one of those
   components (`inventory <> product`), combo `created_at >= 2026-01-01`
   → **223 combos**, **261 component×combo pairs**.
3. **Row** = one per **(combo, marketplace)** — deliberately *not* per
   (component, combo, marketplace); see §6.

**Corrected three data sources that V1 had wrong:**

- **Received Date** moved off `inv_products.created_at` onto the shipping
  container's close-out (§3, §5).
- **Container name** moved off the `orders.container_id` fallback, which was
  leaking raw foreign keys into the UI (§6).
- **Component image** moved off `listing_data.main_image_url` onto
  `supplier.order_items.image_url`. Components are supplier parts and are rarely
  listed on a marketplace, so the listing table only ever covered 26/178.
  Supplier photo first, listing image as fallback → **26 → 92 of 178**.

**Two independent datasets, one table:** a Components tab (single-SKU listings,
189 rows) and a Combos tab (513 rows), each with its own listings/traffic/
orders/returns queries. No combo query is reused for components.

**Presentation:** grouped rowspan layout (one product block, marketplace rows
nested beneath); per-marketplace row tints; a one-page detail drawer showing all
23 fields without scrolling; Record ID pinned left; dual-axis table scrolling.

---

## 3. POSTGRESQL / MCP FINDING

**Finding 1 — `supplier.final_containers` is the real shipping container.**
The schema has **two** container tables and they are not interchangeable:

| Table | Linked by | Meaning | Coverage of the 178 components |
|---|---|---|---|
| `supplier.containers` | `order_items.assigned_container_id` | loading/planning container | **88 / 178** |
| `supplier.final_containers` | `order_items.final_container_id` | **the container that ships and arrives** | **154 / 178** |

`final_containers` carries `status` (`completed` / `in_progress`) and
`main_container` (`UK` / `GERMAN` / `US`).

**Finding 2 — there is no receipt/arrival date column anywhere.**
Exhaustively checked: `orders.status_arrived` is a date-less 0/1 flag;
`orders.updated_at` is a generic row-edit timestamp that also moves on
**never-arrived** POs (162 orders with `status_arrived = 0` have `updated_at`
values running to 2026-07-27, identical in range to arrived ones), so it cannot
be used as an arrival date. `supplier.order_item_logs` (7,269 rows) logs only
dimension edits (`weight`, `ctns`, `cbm`, `pcs`, `length`, `height`, `width`) —
**no container or arrival events**.

**Finding 3 — no customer-review source exists.** Searched every schema for
columns matching `rating|review|feedback|star|score|comment` and every table
named like reviews. Only hits: `public.blos_maduro_review_queue_v1` (a
threshold-approval workflow queue for a different project, 14 rows) and
`ph_asin_health_alerts` (alert_type is only `Listing Inactive` /
`Amazon Inventory Zero`). Return *comments* exist on returns tables but are
return text, not product reviews.

**Finding 4 — three join type-casts are mandatory:**

```sql
oi.order_id            = o.id                      -- bigint = bigint
                                                   -- NOT o.order_id (that is the PO TEXT, e.g. 'BBS032026-02')
ct.id                  = oi.assigned_container_id::bigint   -- double precision -> bigint
fc.id                  = oi.final_container_id::bigint      -- double precision -> bigint
ct.id::text            = o.container_id                     -- container_id is TEXT
```

**Finding 5 — return reason coverage is uneven:** `amazon_returns.reason` is
100% populated (4,858/4,858); `ebay_returns.reason` only ~10.6% (3,336/31,595);
`shopify_returns` has **no reason column at all**.

---

## 4. GAP FOUND

1. **No auditable receipt date.** The best available signal is
   `final_containers.updated_at` gated on `status = 'completed'`, which is still
   a row-modification timestamp, not a declared arrival event. If a completed
   container row is ever edited for an unrelated reason, that date shifts. A
   dedicated `arrived_date` column on `final_containers` would make this
   auditable. **Coverage: 326/513 rows; the remaining 187 are containers still
   open, deliberately left blank.**
2. **Average Feedback has no data source.** The column is built end-to-end and
   renders "No Reviews" for every row. A marketplace reviews feed is required.
3. **Component images: 86 of 178 components have no photo** — `image_url` is
   NULL on *every* `order_items` row for those SKUs. Source-data gap, not a
   fetch defect. The `image_up` flag is **not** a reliable indicator (2,158 rows
   carry a real `image_url` while `image_up = 0`).
4. **47 supplier SKUs are absent from `inv_products`** — purchased but never
   catalogued, so invisible to any dashboard that starts from `inv_products`.
5. **14 combo-style SKUs (with `+`) appear on supplier POs**, contradicting the
   "suppliers ship components, we assemble combos" rule (e.g.
   `LSMS320BI2PK+RPR44WH2PK` on PO `MCY042026`). Either the supplier
   pre-assembles kits, or the finished combo SKU was entered instead of its
   component lines. Needs business confirmation.
6. **The V1 revenue-reconciliation hard gate was not carried into V2** — this is
   what allowed §6's double-count to reach the UI undetected.

---

## 5. VALIDATION RULE ADDED OR CHANGED

**Rule — Received Date (replaces the SKU-creation-date rule):**

```
Received Date =
  IF final_containers.status = 'completed'
     THEN final_containers.updated_at::date        -- container closed into inventory
  ELSE IF invoices.ship_by_date IS NOT NULL
     THEN invoices.ship_by_date                    -- shipped, not yet closed
  ELSE NULL                                        -- container still open

NEVER fall back to orders.order_date. The PO date is when stock was ORDERED,
not received; substituting it silently misreports receipt by weeks or months.
A blank cell is correct when no receipt has occurred.
```

**Rule — Container name (never expose a foreign key):**

```
Container = COALESCE(final_containers.name, containers.name)

MUST NOT fall back to orders.container_id. That column is a raw FK string and
rendered bare integers such as "31" as if they were container names.
```

**Rule — Row grain / anti-double-count (new hard gate):**

```
Combo view    : exactly one row per (combo_sku, marketplace)
Component view: exactly one row per (component_sku, marketplace)

Because all orders/traffic/returns are keyed on the COMBO sku, emitting one row
per (component, combo, marketplace) replicates the combo's metrics once per
component and inflates every KPI when rows are summed.

GATE: len({(product, marketplace)}) == len(rows)  -- build fails otherwise.
```

**Rule — Traffic window:** traffic is summed from **each listing's own Listed
Date to today** (`t.date >= l.listed_on`), not from the reporting-window start.

**Rule — Return Rate:** `(total_returns / units_sold) * 100`, and **0.00 when
units_sold = 0** (never division-by-zero, never NULL).

---

## 6. FAILURE MODE OR EDGE CASE

**Failure 1 — join fan-out silently inflating every KPI (found and fixed).**
36 of 223 combos are built from more than one new component. Rows were emitted
per (component, combo, marketplace) while metrics were keyed on the combo alone,
so each combo's numbers were written into N identical rows. Summing across rows
double-counted. Measured inflation:

| Metric | Displayed | Correct | Over-stated |
|---|---|---|---|
| Impressions | 10,174,398 | 9,416,881 | **+757,517** |
| Clicks | 40,231 | 35,901 | +4,330 |
| Orders | 665 | 636 | +29 |
| Units | 807 | 778 | +29 |
| Revenue | £11,383.18 | £11,090.48 | **+£292.70** |

Only ~16% of combos were affected, so spot-checks passed. Every per-row check
(return-rate maths, dates in window, no nulls) also passed — the rows were
individually valid; the defect was **relational**, visible only across rows.
Surfaced when the grouped layout stripped the repeated product columns away and
left two visibly identical marketplace rows.

**Failure 2 — a sticky cell that is not fully opaque.** Columns scrolling
underneath show through and smear into the pinned text. Any `position: sticky`
cell must set a solid `background-color`; a hover tint must be layered as a
separate `background-image`, never as a translucent background-color.

**Failure 3 — an invisible full-screen overlay swallowing all clicks.** The
detail drawer opened but `.open` was added inside `requestAnimationFrame`, which
did not fire. With `opacity: 0` plus `position: fixed; inset: 0; z-index: 80`,
the page looked frozen. Guard: `pointer-events: none` unless `.open`, and toggle
the class in the same tick after a forced reflow.

**Failure 4 — CSS specificity collisions when reusing another page's stylesheet.**
V1 defines `.dbody.onepage { display: flex }` (0,2,0). A new `.dbody { display: grid }`
(0,1,0) silently lost, and combined with `overflow: hidden` would have **clipped
fields out of view entirely** — worse than scrolling, because nothing indicates
data is missing.

**Failure 5 — `overflow: auto` shorthand leaving one axis `visible`**, so only
horizontal scrolling worked. Set `overflow-x` and `overflow-y` explicitly.

**Edge case — multi-component products:** a combo built from components with
*different* suppliers/containers/receipt dates must show all values stacked;
where every component shares one value it must show once. 27 of 36
multi-component products share a supplier; 9 genuinely differ.

---

## 7. DECISIONS MADE TODAY

1. **Received Date will show blank rather than a wrong date.** 187 rows have no
   receipt because their container is still open. Back-filling with the PO date
   would have looked complete and been wrong.
2. **Average Feedback ships as an empty, wired column** rather than being
   dropped or filled with placeholder ratings. Populating
   `feedback[(sku, platform)]` in `build_v2.py` is the only change needed when a
   reviews feed exists.
3. **Row grain fixed at source, not in the UI.** Deduplicating at render would
   have left the payload and CSV export still double-counted.
4. **V2 published to a new hub slug** (`…-tracking-v2`, id 65) rather than
   overwriting V1 (id 14). V1's 11:00 cron republishes that slug daily, so an
   overwrite would have been silently reverted within 24 hours.
5. **UI verified by executing the page in a real DOM (jsdom)**, not by parsing.
   A parse check cannot catch an undefined function, an `opacity:0` panel, or a
   lost specificity battle — all three occurred today.
6. **V1 left untouched.** V2 is a parallel deliverable; only the design tokens
   (`<style>` block) are reused.

---

## 8. COMPANY KNOWLEDGE EXTRACT

1. **A timestamp is not an event.** `status_arrived` (flag), `updated_at`
   (row-edit) and `created_at` (record creation) are routinely mistaken for
   business events. Before using any date as a business date, test it against
   rows where the event did *not* happen — if `updated_at` moves on never-arrived
   POs, it is not an arrival date. This single test invalidated two candidate
   receipt-date sources today.
2. **When metrics are keyed at a coarser grain than rows, summing rows
   double-counts.** Any one-to-many expansion (component→combo, order→line)
   needs a uniqueness gate on `(entity, dimension)` *and* a reconciliation of
   the dashboard total against an independent aggregate. Per-row validation
   cannot detect this class of defect.
3. **Port your regression guards when you fork a pipeline.** V1's
   "Revenue reconciles to independent PostgreSQL total" gate was built for
   exactly this failure mode on 2026-07-27 and was not carried into V2 — so the
   same class of bug reached the UI the very next day. A guard that exists in
   one pipeline but not its successor provides no protection.
4. **Never render a foreign key as a business value.** `COALESCE(name, raw_id)`
   is a silent failure: it looks like a value and reads as data. Prefer blank.
---

## 9. LLM STANDARD CHECK

- Terminology consistent: TRUE (component / combo / product / marketplace row,
  used identically in SQL, builder, and UI)
- Business rules explained with the reasoning, not just the code: TRUE (§5)
- Assumptions documented: TRUE — the receipt-date proxy is stated as a proxy in
  the SQL header, the payload `meta.receivedDateNote`, and §4
- Edge cases documented: TRUE (§6, five distinct failure modes with measurements)
- Evidence referenced: TRUE (§ metadata `evidence_location`, hub id 65,
  21 automated checks in `validation_v2.json`)
- Another developer can continue independently: TRUE — regression anchors
  (178 / 223 / 261 / 513 / 189) let any future run self-verify scope
- LLM queryable: TRUE

---

## 10. DELIVERED / VALIDATION SUMMARY

| Check | Result |
|---|---|
| New components in scope | 178 ✅ anchor |
| Combos built from them | 223 ✅ anchor |
| Component × combo pairs | 261 ✅ anchor |
| Combo rows / Component rows | 513 / 189 |
| No duplicate (product, marketplace) rows | PASS (new hard gate) |
| Received Date from container close-out | 326/513 (rest genuinely open) |
| No raw container IDs in the Container column | PASS |
| Component images (supplier → listing fallback) | 92/178 components |
| Return Rate maths | PASS |
| All dates >= 2026-01-01 | PASS |
| Average Feedback source | **FAIL (declared)** — no review table exists |
| Published to Varman AIOS | id 65, MD5 verified against local file |


