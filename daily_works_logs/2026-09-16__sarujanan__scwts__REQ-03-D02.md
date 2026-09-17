# SKILL FILE — 2026-09-16 — SCWTS — REQ-03-D02

The supply chain was rebuilt on the newly-added old supply-order tables and the
free-text history parsing was deleted; SOT and Category were added; the filter bar
was compacted to two rows; and a full combo-population audit proved that 204 combos
were being hidden by the completed-container rule — closed by a new All Data mode.

---

## METADATA BLOCK

```yaml
date: 2026-09-16
developer: Sarujanan
project: Supplier-to-Customer Workflow Tracking System
project_code: scwts
phase: Development - phase 07
requirement_id: REQ-03
deliverable_id: D02
status: Completed (local build PASS; nothing published)
evidence_location: /home/led-247/Supplier-to-Customer-Workflow-Tracking-System/
  - dashboard-v2-sql/build_v2.py                 # scope, PO/SUPPLY resolution, SOT, Category, All Data
  - dashboard-v2-sql/v2_sources.py               # old supply views; product_history view deleted
  - dashboard-v2-sql/make_html.py                # responsive filter grid, SOT column, All Data button
  - dashboard-v2-sql/payload_v2.json             # embedded payload (2.61 MB)
  - dashboard-v2/index.html                      # generated dashboard (2.70 MB, NOT published)
  - .claude/skills/dashboard-v2-daily/SKILL.md   # reusable project skill
blos_keys_used:
  - component_scope_rule                 # CHANGED: year + inventory_bool, no supplier join
  - supply_source_resolution             # NEW: arrived PO vs completed supply, most recent wins
  - completed_only_display_rule          # NEW: dashboard filter
  - combo_component_mapping              # CHANGED: discovery from the base set, no combo-date filter
  - sot_membership_flag                  # NEW
  - sku_prefix_category                  # NEW
hardcoded_thresholds:
  - components_this_year_incl_deleted = 684
  - components_deleted = 7
  - components_base = 677
  - status_completed / incoming / no_supply_data = 311 / 100 / 266
  - main_view_components = 311
  - main_view_combos = 411
  - all_data_components = 677
  - all_data_combos = 615
  - combo_relationships = 786
  - combos_no_completed_component = 204
  - combos_mixed_status = 69
  - restored_by_dropping_combo_date_filter = 17 combos / 29 relationships
  - supply_status_match = lower(trim(status)) = 'completed'
  - filter_rows_max = 2                     # 768px .. 1559px
three_am_standard: TRUE
llm_queryable: TRUE
company_knowledge_candidate: TRUE
domain: Ecommerce Operations - Supplier to Customer Workflow
User: Varmen
Benefit status: Pass (2 genuine data gaps declared, owned by the database team)
```

---

## 1. SYSTEM STATE (before today)

- V2 was published on 2026-09-15 (hub id 65) with **269 components / 305 combos**,
  container 244 and received 216, using Rule A (last arrived PO) and Rule B
  (warehouse-history stock-in).
- Supplier/container still came from the new PO system only; the old supply system
  existed nowhere in LEDSone, so the received date was parsed out of free text.
- The responsive rebuild from the previous day was implemented but not yet validated.

## 2. WHAT WAS DONE

1. **Finished and proved the responsive rebuild.** The scratchpad had been wiped, so
   the before-baseline was rebuilt from git HEAD and confirmed byte-identical.
   Measured both builds at 10 viewports: 0 overlaps, 0 clipped controls, 0 page
   overflow, header/body drift **0.0px**, 0 console errors.
2. **Hid the summary cards and the Record ID column** by CSS only — both stay in the
   payload and the CSV.
3. **Added the SOT column** (`configurator.components_sot_skus`, matched on the SKU,
   never a prefix) and the **Category filter** (longest-prefix rule). The two
   overlapping prefixes were settled from the SOT sheet's own `source_tab`: PH is
   398/399 `pendantholder` and WS is 180/180 `wallarm`, so **PH → Pendant Lamp
   Holder** and **WS → Wall Arm**, not Lighting.
4. **Cross-checked every combo against the database**: 391 links vs 374 shown, 0
   extra; 13 missing were genuinely deleted combos and 4 were created after the
   build (picked up by the rebuild: 301 → 305 combos).
5. **Compacted the filter bar.** Each `<select>` had been sizing itself to its
   longest option (Supplier 261px) so the bar wrapped to 3–4 rows; replaced with a
   fixed grid — **1 row ≥1560px, 2 rows 768–1559px** — plus a compacted header.
6. **Rebuilt the supply chain on the three tables the user added**
   (`old_supplyorder` 987, `old_supplyorderlist` 15,635, `old_supplier` 120). The
   displayed container is the one that actually **arrived**: an arrived PO or a
   completed supply order, most recent wins (proved necessary by IMACCW, whose Feb
   supply receipt is newer than its Dec PO). `lower(trim(status))` is mandatory —
   the column holds `Completed` 811 **and** `completed` 48.
7. **Deleted every free-text `product_history` code path** and removed the
   supplier-PO INNER JOIN from the scope. Added an Incoming button for containers
   still on order or shipping.
8. **Audited the whole combo population** after the count was challenged: 38,078
   combo products exist and 3,446 were created this year, but only **615** actually
   use a component created this year. The old database still holds the real
   structured table `public.inv_product_combo` (122,237 rows) and the LEDSone
   `sku_original` derivation reproduces it exactly — 781 shared links, 19 newer,
   **0 missed**.
9. **Audited the 266 components with no supply record**: only 4 are matching
   problems (trailing spaces or a typo), 157 hold stock with no record at all, and
   109 were simply never ordered.
10. **Separated combo discovery from container status** and shipped **All Data**:
    discovery now runs from the 677-component base set, the combo-created-this-year
    condition was dropped, status became an attribute, and the Incoming button
    became All Data (OFF keeps the completed-only view exactly).
11. **Created the reusable project skill** `.claude/skills/dashboard-v2-daily/SKILL.md`.

## 3. DEFECTS FOUND (with measurements)

| # | Defect | Measurement |
|---|---|---|
| 1 | Supplier-PO INNER JOIN silently cut the population | 684 → 272 → 269 (415 lost) |
| 2 | Combo discovery ran off the completed subset | 615 → 411 (**204 combos hidden**) |
| 3 | Combo-created-this-year filter hid valid combos | 17 combos / 29 relationships |
| 4 | Filter bar wrapped to 3–4 rows; controls never shrank | 1024px: 223px/3 rows → 117px/2 rows |
| 5 | Search and Clear each took a whole row on wide screens | 1920px: 162px/2 rows → 75px/1 row |
| 6 | `lower()` missing on supply status would drop rows | 48 of 859 completed supply orders |

## 4. FINAL SCOPE (end of day)

| Population | Count |
|---|---|
| Components created this year (incl. deleted / deleted / base) | 684 / 7 / **677** |
| Status: COMPLETED / INCOMING / NO SUPPLY DATA | 311 / 100 / 266 |
| Main view (completed only): components / combos | **311 / 411** |
| All Data: components / combos | **677 / 615** |
| Combo relationships (deleted excluded) | 786 |
| Source split of the 311 | 68 arrived PO + 243 completed supply |

## 5. VALIDATION

- `build_v2.py` gates: **RESULT PASS** (standing soft FAIL only).
- Targets asserted and matched: 684/7/677 · 311/100/266 · 800/623/786/615/411/204/69 ·
  598→615 (+17 combos, +29 relationships) · 0 duplicates · 0 deleted leakage ·
  0 broken relationships · 0 unrelated combos.
- Browser: All Data OFF restores 311/411 exactly; ON shows 677/615; filters, search,
  category, pagination and sorting all work in both modes; **0 console errors**.
- CSS-only changes proved by md5 of the file outside `<style>` plus a 25-state
  interaction harness and an identical CSV hash.
- Spot-checks reconciled with the database: `LPMC50CW9W` → SU1247 / New A60 Bulbs
  supplier / New A60 Bulb Container / 3,400; `IMACCW` → SU1185 / Container 14 2025 /
  15,000; `CBSF95NA` shows its completed SUPPLY container, not its unarrived PO.

## 6. EXPLAINED DIFFERENCES (not errors)

| Observation | Explanation |
|---|---|
| "I expected 3,000+ combos" | 3,446 = every combo **created** this year; only 615 use a component created this year |
| "I saw ~800 earlier" | 800 = component→combo relationship rows; the Combos tab badge counts **marketplace rows** (802), not products (411) |
| Incoming 152 vs expected 155 | the 3 difference are deleted products (PCAM22MJBM/SN/YB), excluded on instruction |
| PO/SUPPLY split 68/243, not 143/168 | tie-break is "most recent arrival wins", which the IMACCW spot-check requires |

## 7. GAPS / RISKS

| Gap | Size | Owner |
|---|---|---|
| Components with no PO and no supply record | 266 (157 hold stock) | Purchasing / warehouse |
| SKU whitespace and typo near-misses | 4 (`WSLFS1002BM␣␣`, `COPA9TWH␣`, `LHTHT15CF␣`, `12RPIP454002`) | Database team |
| SKU re-codes with no `product_mapping` row | IMAC* family | Database team |
| No real received-date column | all rows | Database designer (fix R5) |
| Payload grew to 2.6 MB with All Data | page 2.70 MB | watch publish time |

## 8. NEXT ACTIONS

1. Decide whether to publish this build (nothing published since 2026-09-15 11:15).
2. Confirm whether the Components tab should also follow the All Data base set.
3. Hand the database team the 4 typo SKUs and the 157 stock-without-record list.
4. Run the two `*_ingest.sql` files when approved (they are generated, never executed).
5. Keep `.claude/skills/dashboard-v2-daily/SKILL.md` updated as rules change.
