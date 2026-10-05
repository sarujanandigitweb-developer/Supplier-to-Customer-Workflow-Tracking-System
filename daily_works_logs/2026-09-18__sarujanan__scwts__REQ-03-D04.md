# SKILL FILE — 2026-09-18 — SCWTS — REQ-03-D04

Listings that were visibly live on the marketplaces were showing as Not Listed. A twelve-phase
read-only investigation proved the listing SQL was never wrong: the dashboard was simply a day
old because the 17 September 11:00 refresh aborted on a connection-capacity refusal it failed
to recognise. The retry classifier was widened, an unrelated UI change was isolated and
preserved, a hard-coded credential was reported, and exactly five approved files were committed.

---

## METADATA BLOCK

```yaml
date: 2026-09-18
developer: Sarujanan
project: Supplier-to-Customer Workflow Tracking System
project_code: scwts
phase: Development - phase 07
requirement_id: REQ-03
deliverable_id: D04
status: Completed (build PASS; committed 34af9a6; NOT pushed, NOT published)
evidence_location: /home/led-247/Supplier-to-Customer-Workflow-Tracking-System/
  - validation/V2_missing_listing_reconciliation_20260918.md   # full reconciliation evidence
  - scripts/refresh_and_publish_v2.sh                          # BUILD_RETRYABLE_RE widened
  - dashboard-v2-sql/payload_v2.json                           # release build 20260918_100139
  - dashboard-v2-sql/validation_v2.json                        # RESULT PASS
  - dashboard-v2/index.html                                    # composed from approved source only
  - logs/automation_v2.log                                     # the 2026-09-17 11:00 failure
  - /home/led-247/scwts_preserved_work/image_viewer_20260918/  # unrelated UI work, preserved outside the repo
blos_keys_used:
  - refresh_retry_policy                 # CHANGED: three wordings of the same capacity refusal
  - listing_resolution_rule              # unchanged - verified, not modified
  - listing_window_rule                  # unchanged - created_at >= 2026-01-01
  - release_scope_control                # explicit staging of an approved file list only
hardcoded_thresholds:
  - resolving_listing_rows_before = 2872
  - unexplained_before = 9
  - resolving_listing_rows_after = 2880
  - unexplained_after = 0
  - missing_after = 0
  - duplicates_after = 0
  - listed_after = 2380
  - excluded_pre_2026 = 317
  - excluded_ebay_ended = 96
  - excluded_is_parent = 87
  - build_retry_max_attempts = 3
  - classification_all = 684 components / 421 combos / 211 packs
  - all_products_total = 1316
  - status_completed / incoming / no_supply_data = 311 / 102 / 271
three_am_standard: TRUE
llm_queryable: TRUE
company_knowledge_candidate: TRUE
domain: Ecommerce Operations - Supplier to Customer Workflow
User: Varmen
Benefit status: Pass (0 missing, 0 unexplained; publication still pending approval)
```

---

## 1. SYSTEM STATE (before today)

- The hub served the build of 2026-09-17 09:47 (hub id 65).
- The 2026-09-17 11:00 cron had failed; nobody had noticed why.
- The working tree carried changes made outside any approved task: an image viewer in
  `make_html.py` and an untracked `validation/listing_status_audit_20260917/` folder.

## 2. WHAT WAS DONE

1. **Mapped the listing flow and inventoried the marketplace tables** — amazon 134,859 rows /
   50,044 ASINs, ebay 309,142 / 31,305 item ids (137,239 ended), shopify 72,515, bandq 4,414.
2. **Classified every listing row that resolves to an in-scope product.** 2,872 rows → 2,487
   shown Listed, 228 excluded by the approved pre-2026 window, 95 eBay ended, 53 `is_parent`,
   leaving **9 unexplained**.
3. **Proved the 9 are not a code defect.** Every one carries `updated_at` 2026-09-18
   02:01–03:01, i.e. they were synced into LEDSone *after* the last successful build, and
   re-running the **unchanged** builder listing logic today returned all 9 as INCLUDED.
4. **Found the real cause in the log.** The 11:00 refresh died on
   `FATAL: remaining connection slots are reserved for roles with the SUPERUSER attribute`
   from the old reference database. `BUILD_RETRYABLE_RE` matched only the LEDSone wording
   `too many connections for role`, so a retryable failure was declared fatal on attempt 1/3
   and no dashboard was produced.
5. **Widened the retry pattern to the three wordings of the same condition** and re-proved the
   behaviour on copies: transient → 3 attempts then give up; hard validation failure → no
   retry; failed build → no compose, no publish of stale output. Bounds unchanged.
6. **Isolated the unrelated image viewer.** Git evidence proved it exists in no commit on any
   branch (`git log --all -S "imageViewer"` empty, absent from HEAD, nothing staged). It was
   preserved outside the repository as an exact patch plus full copies, `git apply --check`
   confirmed it re-applies cleanly, `make_html.py` was restored to HEAD, and the dashboard was
   recomposed from approved source only.
7. **Rebuilt and reconciled.** 2,880 resolving rows → 2,380 Listed, 317 pre-2026, 96 ended,
   87 parent, **0 unexplained, 0 missing, 0 duplicates**. All 9 rows render as Listed in the
   browser, each in its correct tab, with 0 console errors.
8. **Reported a hard-coded credential without printing it.** The old-DB password is a literal
   fallback in five tracked files and `PGPASSWORD` is **not** in the production `.env`, so the
   fallback cannot be deleted until the variable is added — removing it today would break the
   cron. Left unchanged and written up as a separate follow-up.
9. **Committed exactly five approved files** after showing the staged scope and running a
   secret scan.

## 3. DEFECTS FOUND (with measurements)

| # | Defect | Measurement |
|---|---|---|
| 1 | Retry classifier recognised only one wording of a connection-capacity refusal | 1 lost refresh; dashboard a full day stale |
| 2 | Listings synced after the last good build were invisible | 9 rows across 7 products |
| 3 | Unrelated UI work would have shipped inside this release | ~63 lines, 0 commits, 3,317 bytes of HTML |
| 4 | Old-DB password hard-coded in tracked source and in git history | 5 files |

## 4. ROOT CAUSE (one sentence)

The dashboard was stale, not wrong: a temporary database connection-capacity refusal, worded
differently by the old database, was misclassified as permanent, so the 11:00 rebuild never ran
and the overnight marketplace sync never reached the payload.

## 5. VALIDATION

- Release build `20260918_100139`: build exit 0, compose exit 0, **RESULT PASS**, 26 checks,
  0 hard failures, 1 standing soft failure (no customer-review table exists).
- Missing eligible listings **0**, unexplained **0**, duplicate rows **0**.
- The 9 rows verified three ways: source query, payload, and rendered DOM.
- Regression vs yesterday: COMPLETED stays 311 and packs stay 211; **0 products removed**;
  growth is +7 components and +14 combos, and INCOMING +2 / NO SUPPLY DATA +5 accounts exactly
  for the 7 new components.
- Secret scan over the staged diff: no credential value; the only matches are variable names
  and `<literal>` placeholders in the evidence document.

## 6. RELEASE SCOPE

| Class | Files |
|---|---|
| A — fix | `scripts/refresh_and_publish_v2.sh` (retry pattern only) |
| A — evidence | `validation/V2_missing_listing_reconciliation_20260918.md` |
| B — generated | `payload_v2.json`, `validation_v2.json`, `dashboard-v2/index.html` |
| C — excluded, preserved | image viewer (outside repo), `listing_status_audit_20260917/`, V3 artifacts, logs |
| D — follow-up | credential removal, as a separate approved task |

Commit `34af9a6` — *fix: prevent stale V2 dashboard after database connection limits* —
5 files, +327 / −70. **Not pushed. Not published.**

## 7. GAPS / RISKS

| Gap | Size | Owner |
|---|---|---|
| Hub still serves the 2026-09-17 build | 1 day stale | Awaiting publish approval |
| `PGPASSWORD` absent from `.env`, fallback hard-coded in 5 tracked files | committed in history | Security follow-up; rotate with the DB owner |
| Old reference DB runs out of connection slots at 11:00 | 3 failures in 4 days | Database team — the retry is a mitigation, not a cure |
| Image viewer undecided | ~63 lines preserved | Varmen |
| Three commits ahead of `origin/main` | `34af9a6`, `3d34eb6`, `f6d7f99` | Awaiting push approval |

## 8. NEXT ACTIONS

1. Approve publishing the 2026-09-18 build so the hub stops showing yesterday's data.
2. Confirm tomorrow that the 11:00 cron completes by itself with the widened retry.
3. Decide on the image viewer; the patch is preserved and applies cleanly.
4. Schedule the credential follow-up: add `PG*` to `.env` → verify → remove the five
   fallbacks → rotate the password.
5. Ask the database team why the old DB saturates its connection slots at 11:00.
