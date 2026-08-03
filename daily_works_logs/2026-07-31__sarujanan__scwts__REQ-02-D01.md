# SKILL FILE — 2026-07-31 — SCWTS — REQ-02-D01

Dashboard V3: a container-first tracking view whose scope comes from the
manager's Google Sheet, not the database — plus the discovery that the project's
source database is being **dismantled mid-flight**, and the migration of the
`inv_products` source to the new LEDs One warehouse.

---

## METADATA BLOCK

```yaml
date: 2026-07-31
developer: Sarujanan
project: Supplier-to-Customer Workflow Tracking System
project_code: scwts
phase: Development - phase 06
requirement_id: REQ-02
deliverable_id: D01
status: Completed (with 4 declared source gaps)
evidence_location: /home/led-247/Supplier-to-Customer-Workflow-Tracking-System/
  - dashboard-v3/index.html                    # delivered dashboard (484 KB, self-contained)
  - dashboard-v3-sql/read_sheet.py             # stdlib .xlsx parser -> container mapping
  - dashboard-v3-sql/sheet_containers.json     # Container -> Component SKU (source of truth)
  - dashboard-v3-sql/build_v3.py               # V3 payload builder (V2 logic, swapped source)
  - dashboard-v3-sql/make_html_v3.py           # HTML composer (V2 design + drawer)
  - dashboard-v3-sql/ledsone_products.json     # inv_products master pulled from LEDs One
  - dashboard-v3-sql/payload_v3.json           # embedded payload (776 rows)
  - dashboard-v3-sql/validation_v3.json        # 18 automated checks (14 PASS / 4 declared FAIL)
  - dashboard-v3-sql/V3_DATA_SOURCE_SPEC.md    # field -> source map + risks
  - dashboard-v3-data/New Containers to UK - 2026 .xlsx   # manager's sheet
blos_keys_used:
  - container_component_source        # NEW: the Google Sheet, not the DB
  - inv_products_source_of_truth      # NEW: LEDs One inventory.products
  - combo_component_mapping
  - marketplace_platform_bucket
  - traffic_window_rule
  - return_rate_formula
hardcoded_thresholds:
  - reporting_window_start = 2026-01-01
  - containers_expected = 6                 # regression anchor (Container 11-16)
  - sheet_rows_expected = 210
  - components_expected = 209               # distinct; 1 SKU in 2 containers
  - combos_derived_expected = 295
  - v3_rows_expected = 776
  - listed_rows_expected = 658
  - sku_suffix_regex = '[_-][A-Za-z]{2,4}$'
  - pack_combo_regex = '^<COMPONENT>[0-9A-Z]*PK$'
  - return_rate = (total_returns / units_sold) * 100
  - html_min_bytes = 300000
three_am_standard: TRUE
llm_queryable: TRUE
company_knowledge_candidate: TRUE
domain: Ecommerce Operations - Supplier to Customer Workflow
User: Varmen
Benefit status: Pass (with 4 declared data-source gaps)
```

---

## 1. SYSTEM STATE (before today)

- Dashboard V2 was live and published (`varman_aios.hub_pages` id 65), built on
  `order_management_copy`: 178 new components → 223 combos → 513 rows, with a
  Components/Combos tab pair and a grouped product × marketplace table.
- V2's scope was **derived from the database** (`inv_products` ∩
  `supplier.order_items`). Nobody outside the DB decided what was in scope.
- Two new MCP connectors appeared: `Ledsone_postgres` (database `ledsone`) and
  `postgres_2` (the original `order_management_copy`).

## 2. WHAT WAS DONE

1. **Answered the lead's container-receipt question, definitively.** Searched
   every schema of the new `ledsone` DB for a date column meaning
   arrival/receipt (`arriv|receiv|inbound|delivere|landed|grn|eta|ata|clear`).
   Two hits, both irrelevant (returns delivery, eBay message receipt). Dumped all
   41 container rows (25 `containers` + 16 `final_containers`): the only dates
   are `created_at`/`updated_at`. **`status_arrived` is a boolean with no date.**
   The system records *that* goods arrived, never *when*. Escalation written up:
   the fix is one `arrived_date` column at source, not a connector change.
2. **Found the source database being dismantled mid-session.** While validating,
   `public.inv_products`, `public.inv_product_combo`, `public.amazon_returns` and
   all six `supplier.*` tables went to **0 rows**, and `public.ebay_returns` /
   `public.shopify_returns` were **dropped outright**. `listing_data`,
   `order_transaction`, `traffic_data`, `ppc_performance` survived. V2's own hard
   gates caught this and correctly refused to publish — the live dashboard and
   the hub copy were never overwritten.
3. **Built Dashboard V3 as an independent deliverable.** V2 untouched
   (`dashboard-v2/index.html` still MD5 `a69752c2…`). New `dashboard-v3*` folders.
4. **Made the Google Sheet the scope authority.** Parsed
   `New Containers to UK - 2026 .xlsx` with the **standard library only** — an
   .xlsx is a zip of XML, and `pip install openpyxl` is blocked by PEP 668 in
   this environment. Header row and SKU/image columns are located **by name, not
   position**, so the parser survives column reordering. 6 containers, 210 rows,
   209 distinct SKUs.
5. **Kept V2's retrieval logic byte-for-byte** — same `listing_data` resolution
   (`mapped_sku`→`sku`→suffix-strip, `is_parent=0`, `wrong_sku=0`), same platform
   CASE bucketing, same listing aggregation, same traffic union counted from each
   listing's own Listed Date, same completed-orders revenue, same returns pattern.
   Only the *scope* and the `inv_products` *source* changed.
6. **Swapped the `inv_products` source to LEDs One `inventory.products`** on
   instruction, because `public.inv_products` is a stale/dead copy. No direct
   credentials exist for `ledsone` (MCP only), so the master was extracted in
   three exact-SKU chunks into `ledsone_products.json` (420 products). A regex
   scan over all 43,949 products timed out via MCP; exact-SKU `= ANY(ARRAY[…])`
   lookups return instantly — that is the workable extraction pattern.
7. **Carried V2's fan-out guard into V3 from the start.** Row grain is
   (container, product, marketplace); a build gate asserts uniqueness so the KPI
   double-counting bug found in V2 on 2026-07-28 cannot recur here.
8. **Applied the requested UI changes only.** Removed Supplier and Received Date
   columns (18 remain); added a Container tab list with live counts and an
   "All Containers" tab. Grouped layout, filters, search, sort, pagination, CSV,
   theme and responsive behaviour untouched.
9. **Added V2's detail drawer.** Same markup, same CSS (V3 inherits V2's whole
   `<style>` block), same open/close/Esc/backdrop behaviour and the same reflow
   fix that stops an invisible overlay swallowing clicks. V2's *Supply chain*
   card is replaced by a **Container** card, since Supplier and Received Date no
   longer exist in V3. Multi-component `stack()` behaviour preserved: values
   collapse when every component agrees, list separately when they differ.
10. **Sanitised spreadsheet error values.** `#N/A` was leaking from the sheet's
    Image Link column into `<img src>`. Now rejected at parse time — a value must
    start with `http://`/`https://` to be treated as an image.

## 3. DEFECTS FOUND (with measurements)

| # | Defect | Measurement |
|---|---|---|
| 1 | Source DB emptied/dropped mid-session | 4 tables → 0 rows; 2 tables dropped |
| 2 | No container arrival date exists anywhere | 0 of 41 container rows carry one |
| 3 | `#N/A` sheet error rendered as an image URL | 1 malformed URL, now 0 |
| 4 | Container 17 tab present but empty | 0 SKUs — needs manager confirmation |

## 4. FINAL SCOPE (V3)

- **Container → Component SKU comes from the Google Sheet.** 6 containers
  (11–16), 210 sheet rows, **209 distinct SKUs**. `LSGLULSG` legitimately appears
  in both Container 12 and 13.
- Combos derived from SKU naming (see §7 risk): **295** combos covering
  111/209 components.
- Row = one (container, product, marketplace); product = the combo when one
  exists, else the component itself.

## 5. VALIDATION (18 checks — 14 PASS / 4 declared FAIL)

| Check | Result |
|---|---|
| Container → Component from the Google Sheet | 6 containers / 210 rows / 209 SKUs |
| Every sheet SKU represented | **209 / 209** |
| No duplicate (container, product, marketplace) — no fan-out | **0 duplicates in 776 rows** |
| Combo → Marketplace | 658 listed rows, every one carries a Listed Date |
| Listing Status consistent with Listed Date | 0 mismatches |
| Return Rate maths | exact |
| `inv_products` sourced from LEDs One (not `public.inv_products`) | 420 products cached |
| Component Created Dates populated | **775 / 776** |
| Combo Created Dates populated | **556 / 659** |
| Images | component 774/776, combo 656/776, **0 malformed URLs** |
| JS syntax | parses clean |
| V2 unchanged | MD5 `a69752c21142971bc88e3ac6feb33b4a` |

**Totals:** 776 rows · 658 listed · 23,469,724 impressions · 72,120 clicks ·
1,296 orders · 1,890 units · **£26,666.85** · 94 returns.
**Per container:** 11→83, 12→325, 13→165, 14→91, 15→2, 16→110.

## 6. EXPLAINED DIFFERENCES (not errors)

- **95 of 209 sheet SKUs have a listing**; the other 114 render "Not Listed"
  rather than being dropped — the visibility gap is the point of the view.
- V3 totals differ from V2's because the scope is different by design: V2 was
  DB-derived (178 components), V3 is sheet-derived (209 components).
- `returns` moved 0 → 94 mid-day because `public.amazon_returns` repopulated
  while the migration ran.

## 7. GAPS / RISKS

- **`inv_product_combo` is dead on postgres_2 AND has no LEDs One equivalent** —
  searched every schema. Component → Combo is therefore an **inference** from SKU
  naming (`+` tokens, `…PK` suffix), not a declared mapping. Highest-value item
  to fix; the instruction was to swap only `inv_products`, but this table is
  equally dead.
- **84 combo SKUs absent from `inventory.products`** — almost all locale variants
  (`…+RPR44WH_KR`, `_AA`, `_DE`, `_HM`, `_UT`). They exist as listings but not as
  products, so 103 combo rows have no Combo Created Date.
- **1 sheet component missing from LEDs One:** `PCRMFF`.
- **Top Reason / Average Feedback still unavailable** on postgres_2 (no reason
  data, no review table). LEDs One *does* have
  `customer_service.ebay_orders_customer_feedbacks` (313,634 rows with
  `rating_star`) — Average Feedback becomes buildable the moment that source is
  approved for use.
- **V2's scheduled run will keep failing** until it is repointed at `ledsone`;
  its guards stop it publishing, so this degrades safely but is not self-healing.

## 8. NEXT ACTIONS

- Get `inv_product_combo` migrated (or an equivalent published) so Component →
  Combo stops being an inference.
- Decide whether V3 may read returns/feedback from LEDs One, which would close
  Top Reason and Average Feedback.
- Confirm with the manager whether Container 17 should contain SKUs.
- Repoint Dashboard V2 at `ledsone`, or accept that its 11:00 cron stays red.
- Request an `arrived_date` column on `suppliers.final_containers` at source —
  the only real fix for the container-receipt question.
