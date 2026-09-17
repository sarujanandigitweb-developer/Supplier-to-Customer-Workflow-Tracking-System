# Dashboard V2 — commit history closure (Pack classification + resilient daily refresh)

**Date:** 2026-09-17 · **Developer:** Sarujanan · **Reviewer:** Varmen (pending)
**Status:** PASS *for the follow-up artifact/closure operation only* — see the control exception below.
**Dashboard published:** NO · **Follow-up commit pushed:** NO · **Database writes:** NONE

---

## 1. Implementation commit (already on the remote)
```
741af8e9341807cdf60860357f3e8673c0e02c27
"Implement retry logic for PostgreSQL connection failures in refresh_and_publish_v2.sh"
9 files, +586 / -74
```
Contents: `dashboard-v2-sql/build_v2.py`, `dashboard-v2-sql/make_html.py`, `dashboard-v2-sql/v2_sources.py`,
`scripts/refresh_and_publish_v2.sh`, `dashboard-v2-sql/payload_v2.json`, `dashboard-v2-sql/validation_v2.json`,
`dashboard-v2/index.html`, `validation/V2_pack_classification_all_products_cron_validation_20260917.md`,
`validation/V2_daily_refresh_retry_validation_20260917.md`.

## 2. CONTROL EXCEPTION (not remediated — documented and contained)
`741af8e` was **committed and pushed to `origin/main` before the requested pre-commit staged-scope review
could be performed**. That control therefore **cannot be claimed as PASS** for this commit. It was not
created by the review session, and the first `git status` of the review task still showed the files as
uncommitted, so the commit occurred outside that session.

**History was deliberately NOT rewritten.** A soft reset was requested and then correctly abandoned once
`git ls-remote origin refs/heads/main` proved the commit is on the GitHub server
(`741af8e… refs/heads/main`), and `git rev-list --left-right --count origin/main...HEAD` showed `0 0`.
Rewriting would have required a force-push of published history.

**Proof it was remote before any action:**
```
git log --decorate     -> 741af8e (HEAD -> main, origin/main)
git rev-parse HEAD     =  741af8e9341807cdf60860357f3e8673c0e02c27
git rev-parse origin/main = 741af8e9341807cdf60860357f3e8673c0e02c27
git ls-remote origin refs/heads/main -> 741af8e9341807cdf60860357f3e8673c0e02c27
```
No reset, amend, revert or force-push was executed.

## 3. Post-hoc verification of the pushed implementation
| Check | Result |
|---|---|
| Committed source == validated working source | identical (`git diff HEAD` empty for all 4 source files) |
| Authoritative pack source `inventory.product_pk` | present (`v2_sources.py` temp view, read every build) |
| Canonical Pack classification (`is_pack` / `classify`) | present in `build_v2.py`; **no duplicate regex in the JS** — the UI consumes `B.cls` |
| `'+'` combos protected from Pack | rule requires no `'+'`; 0 misclassified |
| `cls` shipped in payload | yes (`B["cls"]`) |
| Packs tab, All Products counts, Combo Components, Pack Count | present in `make_html.py` |
| Bounded retry: max 3 attempts, 30 s then 60 s, only `too many connections for role` | present in `refresh_and_publish_v2.sh` |
| Failed build cannot publish stale dashboard | proven by Tests C/D/E |
| Secret scan | clean; `.env` ignored and untracked |
| Classification validation | PASS — `validation/V2_pack_classification_all_products_cron_validation_20260917.md` |
| Retry validation | PASS — `validation/V2_daily_refresh_retry_validation_20260917.md` |

## 4. Current validated counts (fresh build 2026-09-17, run 20260917_094706, RESULT PASS)
| Scope | Components | Combos | Packs | All products |
|---|---:|---:|---:|---:|
| All Data | **677** | **407** | **211** | **1,295** |
| Main | **311** | **257** | **156** | **724** |

Relationships **795** = 584 combo + 211 pack · missing **0** · extra **0** · duplicates **0** ·
multi-category **0** · Combo Components **128** · Pack Count **211**.
All figures were re-verified against the live database after this build; no historical number was forced.

## 5. Follow-up commit (local only)
```
f6d7f99818a8ff6ed8aac6eda9cb7db4d1898075
"chore: refresh V2 artifacts after pack and retry validation"
3 files, +4 / -4
```
Files: `dashboard-v2-sql/payload_v2.json`, `dashboard-v2-sql/validation_v2.json`, `dashboard-v2/index.html`.
These three are long-standing tracked build outputs (tracked since 2026-07-28, 8 commits each). The diff
against `741af8e` is build-run metadata only — `run` id `20260917_093714 → 20260917_094706` and
`duration_sec` `134.4 → 185.7`; the `B` map, `classification`, row counts (976 / 434 / 885 / 1207) and
everything in the HTML outside the embedded payload are **identical**. No source file is in this commit.

Pre-commit review performed **before** committing: staged list, diff-stat, secret scan, forbidden-path check.

## 6. State after this task
- `origin/main` = `741af8e…` (unchanged, untouched)
- local `main` = `f6d7f99…`, exactly **1 commit ahead**, **0 behind**
- working tree **clean**
- dashboard **not published** — the hub row still holds the 2026-09-15 11:15 artefact
- follow-up commit **not pushed**

## 7. Known limitations
- The missing pre-commit gate on `741af8e` is permanent in history; it is documented here, not fixed.
- Something outside the review session commits and pushes this repository; if that is an IDE or hook it
  should be identified, otherwise the same control can be bypassed again.

## 8. Next step
Request approval separately before pushing `f6d7f99` or publishing the dashboard.
