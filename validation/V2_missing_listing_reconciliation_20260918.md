# Dashboard V2 — Missing Listing Data: Root Cause, Fix and End-to-End Validation
Date: 2026-09-18 · Scope: Dashboard V2 only · Database access: READ-ONLY (SELECT + session-only TEMP objects)
Published: NO · Committed: NO · Reviewer: sarujanan (techclawweb@gmail.com)
Release build: `20260918_100139`, composed from approved (committed) source only.

## 1. Verdict

There is **no defect in the listing resolution logic**. The listings the user could not see were
absent because the published/on-disk dashboard was built at **2026-09-17 09:47** and the daily
refresh that should have replaced it at **2026-09-17 11:00 failed and was never retried**.
The marketplace rows in question were synced into LEDSone during the night of
**2026-09-18 02:01–03:01**, i.e. after the last successful build.

The real defect is in the daily-refresh **retry classifier**, which treated a temporary
PostgreSQL connection-capacity refusal as a permanent error because it was worded differently
from the wording seen when the retry logic was written.

## 2. Reconciliation before the rebuild (payload of 2026-09-17 09:47)

Every listing row in LEDSone that resolves to an in-scope product was classified:

| Outcome | Rows |
|---|---:|
| Shown as Listed | 2,487 |
| Excluded — listing created before 2026-01-01 (approved window rule) | 228 |
| Excluded — eBay `is_ended=1` | 95 |
| Excluded — `is_parent=1` | 53 |
| **UNEXPLAINED** | **9** |
| Total resolving rows | 2,872 |

The 9 unexplained rows, and their `updated_at` in LEDSone:

| Product | Platform | Marketplace ref | listing created | LEDSone `updated_at` |
|---|---|---|---|---|
| ENC10413 | amazon | B0HK3KNBLP | 2026-09-17 | 2026-09-18 02:01–03:01 |
| CENU4010WH | ebay | 267787755181 | 2026-09-17 | 2026-09-18 02:01–03:01 |
| CENU4020WH | ebay | 267787755181 | 2026-09-17 | 2026-09-18 02:01–03:01 |
| CRSF100YB+WSLS155YB+LSGL12010AR | ebay | 318085358945 | 2026-03-31 | 2026-09-18 02:01–03:01 |
| CRSF120CH+WSUSHE27CH+SPAL68CH+LSGLSC1508CL | shopify | 42963106660427 | 2026-07-31 | 2026-09-18 02:01–03:01 |
| CRSF120CH+WSUSHE27CH+SPAL68CH+LSGLSC1508CL | shopify | 57226635247881 | 2026-07-29 | 2026-09-18 02:01–03:01 |
| CRSF120CH+WSUSHE27CH+SPAL68CH+LSGLSC1508CL | shopify | 56795769373058 | 2026-07-27 | 2026-09-18 02:01–03:01 |
| IMDC7714BYENPK | b&q | 5056756362249 | 2026-09-17 | 2026-09-18 02:01–03:01 |
| IMDC7714BGRNPK | b&q | 5056756341732 | 2026-09-17 | 2026-09-18 02:01–03:01 |

Re-running the **unchanged** builder listing logic against today's database returned all 9 as
INCLUDED. That is the proof that the code was never wrong: only the build was old.

## 3. Root cause of the stale build

`logs/automation_v2.log`, 2026-09-17 11:00:

```
[BUILD] attempt 1/3
connected tech_user@169.58.91.229:5432/ledsone
old-DB reference (inv_products.isdeleted / fallback order sources) unavailable:
connection to server at "149.28.134.54", port 5435 failed:
FATAL:  remaining connection slots are reserved for roles with the SUPERUSER attribute
[BUILD] non-transient failure on attempt 1/3 — not retried
[FATAL] database build failed — hard validation / Python / SQL error, not a connection-capacity problem
[PUBLISH] skipped because fresh build did not complete
```

`BUILD_RETRYABLE_RE` matched only `too many connections for role` — the LEDSone wording.
The old reference database (149.28.134.54:5435) reports the *same* condition with the
PostgreSQL wording `remaining connection slots are reserved for roles with the SUPERUSER
attribute`, so a retryable failure was classified as fatal on the first attempt.

## 4. Code fix (the only code change made)

`scripts/refresh_and_publish_v2.sh` — one configuration line plus its comment:

```diff
-BUILD_RETRYABLE_RE='too many connections for role'
+BUILD_RETRYABLE_RE='too many connections for role|remaining connection slots are reserved|sorry, too many clients already'
```

No change to SQL, business rules, listing filters, payload generation or the UI.
Attempts remain bounded at 3 with 30s/60s waits; every other failure class still fails
immediately and publish is still skipped when the build does not complete.

Proof (harness run against copies, production paths untouched, waits shortened to 1s):

* old-DB connection-slot error → `attempt 1/3 → 2/3 → 3/3`, each logged
  `[BUILD] transient PostgreSQL connection failure`, then
  `[FATAL] … after 3 attempts — PostgreSQL connection capacity`, `[PUBLISH] skipped`.
* hard validation failure → `[BUILD] non-transient failure on attempt 1/3 — not retried`
  (unchanged; not masked).

## 5. Rebuild and post-fix reconciliation

Two fresh builds were run. The first (`20260918_093903`) confirmed the diagnosis; the release
build (`20260918_100139`) was re-run **after** the unrelated image-viewer change was removed
from the composer, so the shipped HTML comes from approved source only. Both: build exit 0,
compose exit 0, RESULT **PASS** — 26 checks, 0 hard failures, 1 pre-existing soft failure
(`Average Feedback source`: the database has no customer-review table). Reconciliation figures
below are from the release build and are identical across the two.

| Outcome (post-rebuild) | Rows |
|---|---:|
| Shown as Listed | 2,380 |
| Excluded — created before 2026-01-01 | 317 |
| Excluded — eBay `is_ended=1` | 96 |
| Excluded — `is_parent=1` | 87 |
| Excluded — `wrong_sku=1` | 0 |
| Excluded — blank sku | 0 |
| **UNEXPLAINED** | **0** |
| Total resolving rows | 2,880 |

Bucket sizes are attributed by first-matching rule in builder order, so individual bucket
totals are not directly comparable with section 2 (which used a different attribution order);
the totals and the UNEXPLAINED count are.

All 9 rows now resolve to a product that is shown as **Listed** on that platform, in the
payload and in the rendered dashboard (headless Chrome, All Data ON, correct tab per product):

```
[comp ] CENU4010WH                                 Listed
[comp ] CENU4020WH                                 Listed
[pack ] IMDC7714BYENPK                             Listed
[pack ] IMDC7714BGRNPK                             Listed
[combo] ENC10413                                   Listed (Amazon, 17 Sep 2026)
[combo] CRSF100YB+WSLS155YB+LSGL12010AR            Listed (eBay)
[combo] CRSF120CH+WSUSHE27CH+SPAL68CH+LSGLSC1508CL Listed
JS errors: none
```

## 6. Regression check (2026-09-17 09:47 build vs 2026-09-18 09:39 build)

| Measure | Before | After | Change |
|---|---:|---:|---|
| All-data components | 677 | 684 | +7 new products, **0 removed** |
| All-data combos/packs | 618 | 632 | +14 new, 0 removed |
| Relationships | 795 | 833 | +38 |
| Status COMPLETED | 311 | 311 | unchanged |
| Status INCOMING | 100 | 102 | +2 |
| Status NO SUPPLY DATA | 266 | 271 | +5 |
| Pack count (all) | 211 | 211 | unchanged |
| Products misclassified as pack | 0 | 0 | unchanged |
| Duplicate (product, marketplace) rows | 0 | 0 | builder hard check PASS + independent recount = 0 |

INCOMING +2 and NO SUPPLY DATA +5 account exactly for the 7 new components; COMPLETED and the
pack population are untouched. No product present yesterday disappeared, so the deleted-product
exclusion still behaves identically.

New products entering scope (normal inventory growth, not a scope change):
components LSCA6R70BM, TPFHTWB12BMCH, TPFHTWB12BMSN, TPFHTWB12BMYB, TPFHTWB15GD, WSFAHQS400BG,
WSLSGL20YB; combos ENC10415–ENC10425 and 3 CRSF/TPFHTWB combinations.

## 7. Isolation of unrelated work (not part of this release)

### 7.1 Product image viewer — REMOVED from this release, preserved intact

`dashboard-v2-sql/make_html.py` carried an unrelated ~63-line product-image viewer
(`<dialog id="imageViewer">`, `data-image-preview` on the two `<img>` renderers, plus its CSS),
file mtime 2026-09-17 14:32. Git evidence:

* `git status --short` — modified, **unstaged**.
* `git diff --cached` — **empty**: nothing staged.
* `git show HEAD:dashboard-v2-sql/make_html.py | grep -c imageViewer` → **0**.
* `git log --all -S "imageViewer" -- dashboard-v2-sql/make_html.py` → **no commits**.

It therefore exists in no commit on any branch and was never approved for release. Action taken:

1. Preserved outside the repository at
   `/home/led-247/scwts_preserved_work/image_viewer_20260918/` —
   `image_viewer.patch` (exact `git diff`), the full modified composer, the committed baseline,
   and the HTML that had been built from it.
2. `git apply --check image_viewer.patch` → **applies cleanly**, so the change is fully
   recoverable on demand.
3. `git checkout -- dashboard-v2-sql/make_html.py` restored the committed version; the file is
   now clean against HEAD and `make_html.py` is **not** part of this release.
4. The dashboard was rebuilt and recomposed from that approved source. The shipped HTML contains
   **0** occurrences of `imageViewer` (2,769,281 bytes, vs 2,772,598 when the viewer was present).

Nothing of the image-viewer work was deleted or overwritten.

### 7.2 `validation/listing_status_audit_20260917/` — left untouched

A 23-file, SELECT-only listing audit from 2026-09-17 14:41–17:23 (another session). It is
**untracked** (`git ls-files` → 0 entries), unrelated to this fix, and is neither modified nor
staged here. Its own README records that no application code or dashboard data was changed by it.

### 7.3 V3 artifacts and logs — excluded

`dashboard-v3-sql/payload_v3.json`, `dashboard-v3-sql/validation_v3.json`,
`dashboard-v3/index.html` and the three files under `logs/` are modified by other processes and
are excluded from the listing-fix commit.

## 7a. Security finding (read-only; nothing changed)

The old reference database's password is **hard-coded as a fallback in tracked source**:

* `scripts/refresh_and_publish_v2.sh` — `export PGPASSWORD="${PGPASSWORD:-<literal>}"`
* `dashboard-v2-sql/build_v2.py` — `os.getenv("PGPASSWORD", "<literal>")`
* the same pattern also exists in `refresh_and_publish.sh`, `refresh_and_publish_v3.sh`
  and `dashboard-v3-sql/build_v3.py` — five tracked files in total.

The literal is already committed in git history. **No credential value is recorded in this
document and none was printed.**

Environment check (names only, values never read out):

```
PGPASSWORD present in .env: NO
.env keys present: LEDSONE_PGDATABASE, LEDSONE_PGHOST, LEDSONE_PGPASSWORD,
                   LEDSONE_PGPORT, LEDSONE_PGSSLMODE, LEDSONE_PGUSER
.env tracked by git: NO (git-ignored)
```

This is the reason the fallback must **not** be deleted yet: the production `.env` supplies only
the LEDSone credentials, so removing the fallback today would break the 11:00 cron at the
old-DB connection. LEDSone itself is already correct — `build_v2.py` requires `LEDSONE_PG*` from
the environment and exits if any is missing.

Recommended follow-up, as a separate approved task (not done here):

1. Add `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD` to the production `.env`.
2. Verify a manual refresh succeeds with the variables supplied from `.env` only.
3. Then remove the five hard-coded fallbacks, making the scripts fail loudly when a variable is
   absent, exactly as `build_v2.py` already does for LEDSone.
4. Rotate the old-DB password, since the current one is recoverable from git history, and
   confirm with the database owner before rotation.

## 7b. Release scope

| Class | Files |
|---|---|
| A — intended fix | `scripts/refresh_and_publish_v2.sh` (retry pattern only) |
| A — evidence | `validation/V2_missing_listing_reconciliation_20260918.md` |
| B — generated from approved source | `dashboard-v2-sql/payload_v2.json`, `dashboard-v2-sql/validation_v2.json`, `dashboard-v2/index.html` |
| C — unrelated, preserved, excluded | image viewer (outside repo), `validation/listing_status_audit_20260917/`, V3 artifacts, `logs/*` |
| D — security follow-up | separate task; nothing changed in this release |

Secret scan over class A + B: no credential value present in any of them; the only literal is
the pre-existing fallback in `refresh_and_publish_v2.sh`, unchanged by this task
(`git diff` touches 0 `PGPASSWORD` lines). The two generic keyword hits are the English word
"tokens" in prose. `.env` is git-ignored and untracked.

## 7c. Status and next action

* Published: **NO** — the hub still serves the 2026-09-17 09:47 build.
* Committed: **NO** — nothing staged; awaiting review.
* Next action: approve the class A + B file set for commit, then publish the 2026-09-18 build.

## 8. Evidence

* `logs/automation_v2.log` — 2026-09-17 11:00 failure, and the 2026-09-15/16 failures.
* `dashboard-v2-sql/validation_v2.json` — release run `20260918_100139`, PASS.
* `dashboard-v2-sql/payload_v2.json` — `capturedAt` 2026-09-18.
* `dashboard-v2/index.html` — regenerated 2026-09-18 10:04 from approved source (2,769,281 bytes, md5 `eaa7481e7c358050dcbff0a97efbc063`).
* `/home/led-247/scwts_preserved_work/image_viewer_20260918/` — preserved unrelated UI work.
