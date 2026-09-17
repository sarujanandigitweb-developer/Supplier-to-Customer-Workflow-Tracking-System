# SKILL FILE — 2026-09-15 — SCWTS — REQ-03-D01

Dashboard V2 on the LEDs One database: the migration was validated and published,
the blank Container / Received Date cells were investigated across three systems
and written up for the database designer, two approved fallback rules filled what
LEDSone could still answer, and the responsive rebuild was started.

---

## METADATA BLOCK

```yaml
date: 2026-09-15
developer: Sarujanan
project: Supplier-to-Customer Workflow Tracking System
project_code: scwts
phase: Development - phase 07
requirement_id: REQ-03
deliverable_id: D01
status: Completed (build PASS; published 11:15; responsive work carried to D02)
evidence_location: /home/led-247/Supplier-to-Customer-Workflow-Tracking-System/
  - dashboard-v2-sql/build_v2.py                 # payload builder (Rule A / Rule B, images, record ids)
  - dashboard-v2-sql/v2_sources.py               # LEDSone -> old-shape temp views
  - dashboard-v2-sql/make_html.py                # HTML composer (ordering, hidden columns, responsive start)
  - dashboard-v2-sql/payload_v2.json             # embedded payload
  - dashboard-v2/index.html                      # published artefact (hub id 65)
  - validation/DB_Designer_Gap_Report_Container_Received_20260915.md
  - validation/V2_container_received_date_gap_evidence_20260914.md
blos_keys_used:
  - inv_products_source_of_truth
  - combo_component_mapping
  - container_received_date_rule
  - marketplace_platform_bucket
  - traffic_window_rule
  - return_rate_formula
hardcoded_thresholds:
  - reporting_window_start = 2026-01-01
  - components_expected = 269
  - combos_expected = 305
  - received_date_filled = 216 of 269       # was 188 before Rule A / Rule B
  - container_filled = 244 of 269
  - rule_a_components = 9                   # last ARRIVED PO shown
  - rule_b_components = 21                  # received date from warehouse stock-in
  - false_received_dates = 42               # completed != received (declared defect)
  - html_min_bytes = 300000
three_am_standard: TRUE
llm_queryable: TRUE
company_knowledge_candidate: TRUE
domain: Ecommerce Operations - Supplier to Customer Workflow
User: Varmen
Benefit status: Pass (gap report issued; 1 defect declared, not yet fixed)
```

---

## 1. SYSTEM STATE (before today)

- Dashboard V2 had just been repointed at the **LEDs One** database through
  `v2_sources.py`, which recreates every old table shape as session-only `pg_temp`
  views so `build_v2.py`'s business SQL runs unchanged.
- Scope: components created ≥ 2026-01-01 that appear on a supplier PO → **269
  components, 305 combos**. Container and Received Date came only from the new PO
  system, and both were blank on many rows.
- Two fallback rules added during the migration (catalogue image, PO-header
  container) had been reverted on instruction because they were new business rules.

## 2. WHAT WAS DONE

1. **Validated the migration and kept the old database for two values only** — the
   `isdeleted` flag and the 10 order sources LEDSone does not carry. Google Ads
   `product_performance` holds superseded duplicate ids, so the latest version per
   id is used (802,585 / 802,585 exact).
2. **Filled every blank product image from the database catalogue**
   (`inventory.product_images`, then `product_media` main-image) only where the
   supplier and listing photos were empty: **81 blank cells → 0**.
3. **Wrote the Record ID once per product** with a `rowspan` instead of repeating it
   on every marketplace row, numbered in display order, and stopped the Combos tab
   repeating component-only rows.
4. **Ordered rows by completeness** — container + received first, then container
   only, then neither — display order only, values untouched. Hid the three
   combo-only columns on the Components tab.
5. **Published the validated 11:00 build to Varman AIOS** (hub id 65, 11:15:44,
   MD5-verified). A manual rebuild had failed on the LEDSone connection limit, so
   the artefact that had already passed was published instead.
6. **Traced the Container / Received Date loss across three systems** — the admin UK
   Supply List, the Inventory team dashboard and LEDSone — over 13 sample groups.
   The decisive finding: `final_containers.status='completed'` is set at **dispatch**,
   not receipt (UK Container 8th 2026 is "completed" with an invoice ship-by of
   9 Sep, 0 of 157 lines arrived and zero stock).
7. **Issued the database-designer gap report** with 7 evidenced gaps and 12
   requested fixes (D1–D12), each backed by the SELECT that produced it.
8. **Added the two approved fallback rules.** Rule A shows the last **arrived** PO
   when the newest PO has not arrived; Rule B takes the received date from the
   latest warehouse stock-in even when it predates the latest PO.
9. **Started the responsive rebuild** — found the page locked to `100vh` with
   `overflow:hidden`, added `clamp()` scaling, released the shell on small/short
   screens and let the app bar wrap; measured before/after at 8 viewports.

## 3. DEFECTS FOUND (with measurements)

| # | Defect | Measurement |
|---|---|---|
| 1 | `completed` container ≠ goods received | UK Container 6th/7th/8th: 0–7% of lines arrived → **42 false received dates** |
| 2 | Latest PO hid an older arrived shipment | 9 components blank instead of showing the arrived container |
| 3 | Receipt recorded under a re-coded SKU | IMACCW receipt sits under IMAC7714CW; no `product_mapping` row |
| 4 | Containers never assigned on shipped POs | CND062026: 8 SKUs received, 0 lines carry a container |
| 5 | Warehouse id 33 (Unit 5) missing from `inventory.warehouse` | 469 products, 592,475 units |
| 6 | Product images blank | 81 components |
| 7 | Page locked to 100vh; pager unreachable | failed at 1024, 600 and 375 |

## 4. FINAL SCOPE (end of day)

| Measure | Value |
|---|---|
| Components / combos | 269 / 305 |
| Container filled | 244 of 269 |
| Received Date filled | **216** of 269 (was 188) |
| Rule A / Rule B components | 9 / 21 |
| Published artefact | hub id 65, 2026-09-15 11:15:44 |

## 5. VALIDATION

- `build_v2.py` gates: **RESULT PASS** (only the standing soft FAIL "Average Feedback
  source" — no review table exists in this database).
- Every filled value carries its source in the row notes (`received date from
  warehouse stock-in (SU1318)`), so nothing is silently invented.
- Hub copy MD5-verified against the local file after publishing.
- Responsive measurements captured at 8 viewports for both the before and after
  builds; the report itself was completed the next day (see REQ-03-D02).

## 6. EXPLAINED DIFFERENCES (not errors)

| Observation | Explanation |
|---|---|
| Screenshots showed blanks that were already filled | the user's page was a stale copy; today's build already carried the values |
| SPCA70BM, CBSF95CL, MBWHBSL blank | correct — never shipped, or stock entered by manual CSV |
| Inventory dashboard shows dates V2 does not | it reads the warehouse history; V2 read only container close-out until Rule B |

## 7. GAPS / RISKS

| Gap | Size | Owner |
|---|---|---|
| Supply list (SU orders) not mirrored into LEDSone | all receipts | Database designer |
| No real received-date column; container `updated_at` used as a proxy | all rows | Database designer (fix R5) |
| `completed` set at dispatch | 42 false dates | Supplier team / logic fix pending |
| SKU re-codes with no mapping row | IMAC* family | Database team |
| `inventory.product_history` frozen at 2026-08-26 | later receipts invisible | Database team |
| LEDSone `tech_user` connection limit | intermittent build failures | Infrastructure |

## 8. NEXT ACTIONS

1. Decide whether to fix the "completed ≠ received" defect (42 rows).
2. Send the gap report to the database designer and track D1–D12.
3. Finish the responsive validation report and publish nothing until approved.
4. Add a retry loop to `scripts/refresh_and_publish_v2.sh` for the connection limit.
