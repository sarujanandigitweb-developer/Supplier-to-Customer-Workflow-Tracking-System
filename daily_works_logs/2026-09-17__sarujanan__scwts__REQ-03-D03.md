# SKILL FILE — 2026-09-17 — SCWTS — REQ-03-D03

Products were split into three first-class categories (Component / Combo / Pack) from the
database's own pack table, the All-Products counts were redefined as distinct products, the
11:00 refresh was made to survive a temporary PostgreSQL connection-limit refusal, the build
was published to the AIOS hub after a controlled commit, and the afternoon was spent on a
SELECT-only listing-status audit of all 1,295 SKUs against the four marketplace tables and
the public storefront.

---

## METADATA BLOCK

```yaml
date: 2026-09-17
developer: Sarujanan
project: Supplier-to-Customer Workflow Tracking System
project_code: scwts
phase: Development - phase 07
requirement_id: REQ-03
deliverable_id: D03
status: Completed (build PASS; published to hub id 65 at 10:11:01)
evidence_location: /home/led-247/Supplier-to-Customer-Workflow-Tracking-System/
  - dashboard-v2-sql/build_v2.py                                              # §1c canonical classification, B["cls"]
  - dashboard-v2-sql/v2_sources.py                                            # TEMP VIEW product_pk (authoritative pack codes)
  - dashboard-v2-sql/make_html.py                                             # Packs tab, distinct-product badges
  - scripts/refresh_and_publish_v2.sh                                         # bounded stage-1 retry
  - validation/V2_pack_classification_all_products_cron_validation_20260917.md
  - validation/V2_daily_refresh_retry_validation_20260917.md
  - validation/V2_commit_history_closure_20260917.md
  - validation/listing_status_audit_20260917/                                 # 23 files, SELECT-only audit
blos_keys_used:
  - product_classification_rule          # NEW: PACK / COMBO / COMPONENT, single source of truth
  - pack_code_source                     # NEW: inventory.product_pk, read every build
  - distinct_product_counting            # NEW: counts are products, never marketplace rows
  - refresh_retry_policy                 # NEW: bounded retry on connection capacity only
  - publish_control_rule                 # explicit staging, read-back after publish
hardcoded_thresholds:
  - pack_codes_from_product_pk = 28
  - classification_main = 311 components / 257 combos / 156 packs
  - classification_all  = 677 components / 407 combos / 211 packs
  - all_products_total = 1295
  - combo_components_distinct = 128
  - pack_count_distinct = 211
  - pack_false_positives = 0
  - pack_suffixed_inventory_products_out_of_scope = 273
  - build_retry_max_attempts = 3
  - build_retry_waits = 30s, 60s
  - publish_min_bytes = 300000
  - hub_page_id = 65
  - audit_skus_checked = 1295
  - audit_source_records = 2876
  - audit_rule_mismatches = 0
three_am_standard: TRUE
llm_queryable: TRUE
company_knowledge_candidate: TRUE
domain: Ecommerce Operations - Supplier to Customer Workflow
User: Varmen
Benefit status: Pass (dashboard published; one control exception documented, not remediated)
```

---

## 1. SYSTEM STATE (before today)

- V2 had All Data mode (677 components / 615 combos) but only two tabs, and packs were mixed
  into the combo population with no way to see or count them separately.
- The count line reported marketplace rows, which read as inflated product counts.
- The 11:00 cron had failed on 2026-09-15 and 2026-09-16 with
  `FATAL: too many connections for role "tech_user"` — a single connection attempt, no retry.
- Nothing had been published since 2026-09-15 11:15.

## 2. WHAT WAS DONE

1. **Discovery before any edit.** Found the authoritative pack table `inventory.product_pk`
   (28 rows, `pack_char → pack_qty`: A=10 … S=25 and 1–9). The build now reads it **every
   run**; no pack code is ever hardcoded in Python or JavaScript.
2. **Wrote the classification rule and proved it.**
   `PACK := sku has no '+' AND sku ends in <pack_char>PK`; a `+` SKU is never a Pack.
   Evidence: 7,190 pack SKUs exist database-wide with **0 false positives**, while 5,901 `+`
   SKUs merely contain pack tokens and correctly stay COMBO.
3. **Made classification single-source.** It happens only in `build_v2.py` and travels in the
   payload as `B["cls"]`; the UI filters on that value and contains no regex of its own.
4. **Added the Packs tab** as a third first-class view (Components | Combos | Packs), with the
   phone breakpoint compacted so three tabs still fit at 375px.
5. **Redefined the counts as distinct products** — Combo Components **128** and Pack Count
   **211** on the All Data scope, never marketplace rows.
6. **Proved the rule is applied, not assumed.** All 273 pack-suffixed `inventory_bool = true`
   products were created before the current year, so 0 reach the eligible base set; the build
   still reports `component_products_classified_pack` (currently 0) so a future in-scope pack
   SKU is classified automatically.
7. **Validated the daily cron end to end** and proved new records are discovered automatically.
8. **Made the refresh survive a temporary connection-limit refusal.** Stage 1 now retries up to
   3 times with 30s then 60s waits, and **only** on a connection-capacity refusal; every other
   failure class still fails on the first attempt and publish is skipped whenever no fresh
   build exists.
9. **Published under control.** Explicit staging (never `git add .`), then publish through
   `push_to_hub.js` as member `sarujanan`, then a read-back from the hub.
10. **Refused to rewrite published history.** A soft reset of `741af8e` was requested; once
    `git ls-remote` proved the commit was already on `origin/main`, the reset was abandoned and
    the exception was documented instead.
11. **Ran a SELECT-only listing-status audit** (afternoon) over all 1,295 SKUs and 2,876
    matching marketplace records, including a public-storefront cross-check.
12. **A product image viewer was added to `make_html.py`** during the afternoon and left
    uncommitted.

## 3. DEFECTS / ISSUES FOUND (with measurements)

| # | Issue | Measurement |
|---|---|---|
| 1 | Counts reported marketplace rows, not products | Combos badge 802 rows vs 411 products |
| 2 | Packs were invisible inside the combo population | 211 pack products, no tab, no count |
| 3 | Stage 1 aborted on the first connection refusal | 2 lost refreshes (15 and 16 Sep) |
| 4 | Pre-commit staged-scope review could not be claimed for `741af8e` | commit reached origin/main outside the review session |
| 5 | Listing labels are rule-correct but not storefront-truth | 0 rule mismatches, yet 32 SKUs hold otherwise-eligible pre-2026 records |

## 4. FINAL SCOPE (end of day)

| Population | Main scope | All Data |
|---|---:|---:|
| Component | 311 | **677** |
| Combo | 257 | **407** |
| Pack | 156 | **211** |
| Total products | 724 | **1,295** |
| Combo Components (distinct) | 70 | **128** |

## 5. VALIDATION

- `build_v2.py`: **RESULT PASS** (standing soft FAIL only — no customer-review table exists).
- Pack rule: 0 false positives across 7,190 pack SKUs; 0 `+` SKUs misclassified.
- Reconciliation: 677 + 407 + 211 = 1,295; relationships 795 = 584 combo + 211 pack;
  0 missing, 0 extra, 0 duplicate, 0 multi-category.
- Non-functional proof: the pre-change builder was re-run against the same database and every
  field was identical — only `cls` was added.
- Retry harness: transient refusal → 3 attempts with waits; hard validation failure → no
  retry; failed build → no compose and no publish.
- Publish read-back: hub page **id 65**, `updated_at` 2026-09-17 10:11:01, md5
  `89e771a385791e4d7d29c5023c111cb1` byte-identical to the local file, exactly **1** row
  updated, V1 and V3 untouched.

## 6. AFTERNOON LISTING-STATUS AUDIT (validation only, nothing changed)

- 1,295 distinct SKUs and 2,876 matching source records from Amazon, eBay, Shopify and B&Q,
  using the builder's own mapped-SKU precedence and locale-suffix removal.
- **0 SKU/platform mismatches** against the current builder rules — the labels are internally
  correct. That is not the same as being true on the storefront today.
- Of 714 All Data SKUs with no Listed platform: **32** have otherwise qualifying records
  excluded solely because the listing was created before 2026 (20 of them marked Active),
  **12** have only parent or different-resolved-SKU evidence and need review, and **670** have
  no matching record at all in the four tables.
- Storefront cross-check: 1,639 public page requests — 293 exact SKU available, 93 present but
  availability false, 239 unverified, 670 with no source listing URL.

## 7. GAPS / RISKS

| Gap | Size | Owner |
|---|---|---|
| Pre-2026 listing window hides otherwise eligible records | 32 SKUs | Business decision (Varmen) |
| Parent-only / different-resolved-SKU listing evidence | 12 SKUs | Database team |
| Pre-commit review control not claimable for `741af8e` | 1 commit | Documented, contained |
| Image viewer added to `make_html.py`, uncommitted and unvalidated | ~63 lines | Decide keep or drop |
| Old-DB password hard-coded as a fallback in tracked scripts | 5 files | Security follow-up |

## 8. NEXT ACTIONS

1. Check tomorrow morning that the 11:00 cron publishes by itself.
2. Decide whether the pre-2026 window rule should be relaxed for the 32 SKUs.
3. Decide whether the image viewer is wanted; it is not part of any approved task.
4. Push the two local commits `f6d7f99` and `3d34eb6` when approved.
5. Run the `*_ingest.sql` files when approved — they are generated, never executed.
