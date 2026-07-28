# SKILL FILE — 2026-07-27 — SCWTS — REQ-01-D04

Supplier's Basket → Customer's Home: corrected inventory-table data model,
full validation audit, daily automation to Varman AIOS, and a revenue-accuracy
fix discovered through independent reconciliation.

---

## METADATA BLOCK

date: 2026-07-27
developer: Sarujanan
project: Supplier-to-Customer Workflow Tracking System
project_code: scwts
phase: Phase-04 – Dashboard Data Validation & Automation
requirement_id: REQ-01
deliverable_id: D04
status: Completed
evidence_location: /home/led-247/Supplier-to-Customer-Workflow-Tracking-System/
  - dashboard-v1/index.html
  - dashboard-v1/VALIDATION_REPORT.md
  - dashboard-v1-sql/build_new_scope.py
  - dashboard-v1-sql/marketplace_view.sql
  - dashboard-v1-sql/supplier_fresh.psv
  - scripts/refresh_and_publish.sh
  - AUTOMATION.md
  - validation/validation_20260727_145034.md
  - validation/fetch_summary_20260727_145034.json
  - logs/automation.log
  - dashboard-v1-update/push_to_hub.js  (reused unchanged)
blos_keys_used:
  - reporting_period_start
  - new_sku_definition
  - combo_component_mapping
  - listing_date_source
  - platform_activity_attachment
  - automation_schedule
hardcoded_thresholds:
  - reporting_window_start = 2026-01-01
  - reporting_window_end_exclusive = 2027-01-01
  - sku_suffix_regex = '[_-][A-Za-z]{2,4}$'
  - new_skus_expected = 3383            # regression anchor (1866 components + 1517 combos)
  - tracking_rows_expected = 4982
  - revenue_expected = 107462.92
  - revenue_reconciliation_tolerance = 0.01
  - html_publish_min_bytes = 500000
  - cron_schedule = "0 11 * * *"
three_am_standard: TRUE
llm_queryable: TRUE
company_knowledge_candidate: TRUE
domain: Ecommerce Operations - Supplier to Customer Workflow
User: Varmen
Benefit status: Pass

---

## 1. SYSTEM STATE (before today)

- `dashboard-v1` was on the "genuinely-new-SKU" scope (`supplier.order_items`
  first-seen definition), giving 240 components / 353 combos — correct by that
  definition but far short of the manager's own count (3,383 new SKUs).
- Supplier data depended on a manually cached PSV (`supplier_attrs.psv`, 178
  SKUs) because `temp_user` was believed to lack `supplier`-schema access.
- No automation existed for this dashboard specifically — refreshes and hub
  publishes were run by hand, one command at a time.
- Orders/traffic/returns were attached to a row only when the transaction's
  platform matched a SKU's *listed* platform — an unnoticed gap.

## 2. WHAT WAS DONE

1. **Rebuilt the data model on the manager's inventory tables.** Verified
   `inv_product_combo` live (`product`=combo id, `inventory`=component id,
   `inventory<>product` excludes self-map singles) against a real 3-part combo.
   Rewrote `build_new_scope.py` scope to **every** `inv_products` row created
   in 2026 (`isdeleted=0`), not just combos — 3,383 SKUs (1,866 components +
   1,517 combos), matching the manager's independently-reported count exactly.
2. **Fixed pack-SKU descriptions.** SKUs like `12IP201302PK` have no `+` but
   *are* mapped in `inv_product_combo` to a base component; they were
   misclassified as bare components and showed "Combo Default Title.".
   Resolved description + supplier through the mapping for every mapped SKU
   (component_description fill 100%, was ~1,400 generic titles).
3. **Reverted an unapproved business-rule change.** "Listed" had drifted to
   "any live listing"; restored the approved rule — Listed = Listing Date
   (`listing_data.created_at`) >= 2026-01-01 — and re-validated.
4. **Ran the manager's full validation checklist**: final SQL shown for all 6
   sources/joins; 40/40 product images verified to belong to the displayed
   SKU (newest listing of the resolved SKU); 30/30 listing URLs + marketplaces
   + listing dates verified against PostgreSQL; 20/20 combo mappings verified
   against `inv_product_combo`; 20/20 supplier chains traced
   order_item→order→container→supplier; full reconciliation table
   (inv_products → listing_data → inv_product_combo → supplier.order_items →
   dashboard) with every record-count difference explained. Wrote
   `VALIDATION_REPORT.md`.
5. **Verified multi-account/marketplace listing coverage.** Confirmed one SKU
   can hold many `listing_data` rows (found one with 20 rows across 13
   accounts, 4 channels, 6 country-markets) and proved the dashboard's
   per-(SKU, platform) metrics sum every account/market with zero loss
   (spot-checked against `traffic_data`/`ppc_performance`; global total
   50,131,743 impressions matched exactly).
6. **Added a marketplace tab list** (filters the existing master table
   in-place via the existing `S.market` state) and a standalone
   `dashboard-v1-sql/marketplace_view.sql` (Query A tracking rows, B tab
   counts, C per-marketplace KPIs, D per-account drill-down), validated
   1:1 against the live tab counts (907/862/1058/258/1707 = 4792). The
   manager subsequently reverted the tab UI from the page; the SQL file and
   its validation remain as a delivered, reusable artifact.
7. **Built the daily automation pipeline** — reviewed existing assets first
   (per instruction) and reused the sibling `Returns-Reason-Hotspot-Report`
   project's `refresh_and_publish.sh` pattern and the existing
   `push_to_hub.js` Varman AIOS uploader **unchanged**. Added: env-driven DB
   credentials; a `supplier`-schema permission probe (discovered `temp_user`
   now HAS `USAGE` — upgraded supplier fetch from a 178/739-row cache
   fallback to a **live** fetch, 1,541 SKUs every run); a 13→14-check dataset
   validation gate (hard checks block publish); the 2-stage gated
   orchestrator `scripts/refresh_and_publish.sh` (build → sanity-gate →
   publish, credential-redacted log); installed the `0 11 * * *` cron entry;
   wrote `AUTOMATION.md`.
8. **Independently verified the automation instead of trusting its own PASS
   output.** Ran the real pipeline (hub MD5 == local file MD5); simulated a
   hard build failure (publish correctly skipped, hub untouched); simulated
   an undersized/corrupt HTML (sanity gate correctly blocked publish, hub
   untouched). Cross-checked revenue independently against raw
   `order_transaction` and found a real, quantified gap.
9. **Found and fixed a silent revenue-accuracy bug**, with the manager's
   explicit approval before changing any business logic: orders/traffic/
   returns were matched to a row by `(SKU, listed platform)`; a completed
   order on a platform where the SKU had no listing computed correctly but
   attached to no row — £31,734.23 (~1,000 orders) invisible in every KPI,
   and "Not Listed" rows could read £0 despite real sales. Fixed by making
   the row set the union of listed platforms and platforms with real
   order/traffic/return activity (no listing there renders correctly as
   "Not Listed" carrying its true numbers). Re-verified revenue reconciles
   **exactly** to an independent SQL total (£107,462.92) and added a
   permanent hard-gate regression check, "Revenue reconciles to independent
   PostgreSQL total". Re-ran the full pipeline and republished (4,982 rows).
10. **Fixed a UI defect**: the pinned Record ID column visually collapsed
    into scrolled-away cell text on row hover. Root cause:
    `tbody tr:hover td.sticky-c{background:rgba(47,111,237,.05)}` was only 5%
    opaque, letting that row's other (scrolled-under, same-screen-position)
    cells bleed through. Fixed by layering an opaque `background-color`
    under the translucent tint; verified via the parsed CSS rule, republished.
11. **Documented the Combo Product Name lineage** on request:
    `listing_data.title` (this row's own platform listing first, else the
    longest non-empty title across all the combo's listings), falling back
    to `inv_products.title` only when it is not the generic placeholder.

## 3. DEFECTS FOUND (with measurements)

| # | Defect | Measurement |
|---|---|---|
| 1 | Pack SKUs misclassified as bare components | ~1,400 rows showed "Combo Default Title." |
| 2 | Unapproved "Listed" rule drift | reverted to approved definition |
| 3 | Sticky-column hover bleed-through | `rgba(...,.05)` = 5% opaque on `tr:hover` |
| 4 | Silent revenue-attachment gap | £31,734.23 / ~1,000 orders unattached to any row |

## 4. FINAL SCOPE (approved by the manager)

- New SKU = `inv_products.created_at` in `[2026-01-01, 2027-01-01)` AND
  `isdeleted = 0` AND `TRIM(sku) <> ''` → **3,383** (1,866 components + 1,517 combos).
- Listed = a listing on that platform with Listing Date >= 2026-01-01.
- Row = one SKU × one platform where either a listing OR real order/traffic/
  return activity exists; a SKU/platform pair with zero activity anywhere
  collapses to a single all-zero "Not Listed" gap row.

## 5. VALIDATION (PostgreSQL vs Dashboard)

| Check | Result |
|---|---|
| Product image belongs to displayed SKU (40 random) | 40/40 |
| Listing URL + marketplace + listing date match DB (30 random) | 30/30 |
| Combo "Components Used" == `inv_product_combo` (20 random) | 20/20 |
| Supplier chain SKU→order_item→order→container→supplier (20 random) | 20/20 |
| Automation: hub content MD5 vs local file MD5 | exact match |
| Automation: hard build-failure blocks publish | verified, hub untouched |
| Automation: undersized/corrupt HTML blocks publish | verified, hub untouched |
| Revenue reconciles to independent PostgreSQL total | £107,462.92 = £107,462.92 |
| Rows without any 2026 anchor date | 0 |
| Listed rows missing a Listing Date | 0 |

## 6. EXPLAINED DIFFERENCES (not errors)

- Revenue rose from £75,728.69 to £107,462.92 after fix #9 — this is real
  previously-hidden revenue surfacing, not inflation.
- Order-count totals (e.g. 3,789 dashboard rows vs 3,709 independent
  distinct `order_id`s) differ by design: a single multi-SKU order is
  counted once per affected SKU-row, so summing across rows can exceed a
  single global distinct count. Revenue, which must never double-count,
  matches exactly.
- Marketplace tab UI was built and validated, then reverted by the manager;
  the underlying `marketplace_view.sql` remains delivered and correct.

## 7. GAPS / RISKS

- ~25% of rows still have no product image (genuinely absent from
  `listing_data` for those SKUs — not a fetch defect).
- 1 combo SKU (`CO232AGYCPK+CO232AGYCPK`) has no `inv_product_combo` row —
  a source data-quality gap, not a query defect.
- If the `supplier` schema grant is ever revoked, the build now degrades
  gracefully to the cached PSV and logs the exact missing `GRANT` statement
  rather than failing silently.

## 8. NEXT ACTIONS

- Decide whether to re-apply the marketplace tab UI now that the underlying
  SQL and data model are stable.
- Monitor the first unattended 11:00 cron execution and confirm
  `logs/automation.log` / `validation/validation_<ts>.md` look as expected.

## 9. LLM STANDARD CHECK

-LLM Queryable: TRUE
-Operational reasoning documented: TRUE
-Edge cases documented: TRUE
-Evidence linked: TRUE
