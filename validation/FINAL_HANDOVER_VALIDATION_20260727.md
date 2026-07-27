# Final End-to-End Handover Validation — SCWTS Dashboard-v1 Automation
**Date:** 2026-07-27 · **Scope:** 8-section pre-handover audit of the daily automation
(`scripts/refresh_and_publish.sh` → `dashboard-v1-sql/build_new_scope.py` →
`dashboard-v1-update/push_to_hub.js` → `varman_aios.hub_pages`).
**Mandate honored:** no changes were made to `build_new_scope.py`, `refresh_and_publish.sh`,
or any other deliverable file. All failure-scenario testing used disposable scratch
copies (see Section 4 note on one exception, disclosed there).

---

## 1. End-to-end automation test — **PASS**

Ran the real `scripts/refresh_and_publish.sh`, unmodified, exactly as cron (`0 11 * * *`)
invokes it. Every stage fired in order and succeeded:

| Stage | Result |
|---|---|
| PostgreSQL connection | OK — `temp_user@149.28.134.54:5435/order_management_copy` |
| Data fetch | OK — all datasets fetched live, no cache |
| SQL execution / validation | OK — 16/16 checks PASS |
| HTML payload generation | OK — `const PAYLOAD` regenerated |
| HTML file generation | OK — 2,385,986 bytes, all structural markers present |
| Upload to Varman AIOS | OK — `sarujanan/supplier-to-customer-workflow-tracking` |
| Validation report generation | OK — `validation/validation_20260727_155202.md` |
| Execution log generation | OK — `logs/automation.log` |

**Independent proof (not just trusting the script's own PASS output):** the hub's stored
`html_content` MD5 was queried directly from `varman_aios.hub_pages` and compared to the
local file's MD5 — **exact match** (`46917f6d2f5f13433b20886b4c228884`), `updated_at`
fresh (2026-07-27 15:52:36). Total wall time: 36.29s.

---

## 2. Data completeness validation — **PASS, 100/100 records, 14/14 fields, 0 mismatches**

Sampled 100 rows from the freshly-published payload (64 Listed / 36 Not Listed, 45
combo / 55 component-only, 99 distinct scope SKUs). Re-derived ground truth directly
from PostgreSQL using the **same join logic as the builder** (copy-verified line-by-line
against `build_new_scope.py`), restricted to the sampled SKUs.

| Field | Checked | Mismatches |
|---|---|---|
| Component SKU | 100 | 0 |
| Combo SKU | 45 | 0 |
| Component Creation Date | 100 | 0 |
| Product Description | 100 | 0 |
| Product Image | 100 | 0 |
| Listing Date | 100 | 0 |
| Listing URL | 100 | 0 |
| Marketplace | 100 | 0 |
| Orders | 100 | 0 |
| Sales | 100 | 0 |
| Traffic | 100 | 0 |
| Returns | 100 | 0 |
| Supplier | 100 | 0 |
| Container | 100 | 0 |

**Process note:** the first comparison pass produced several apparent mismatches
(platform bucketing, one traffic total, image/listing-date/url selection). Every one
of them traced back to a bug in my own diagnostic re-implementation, not the dashboard:
wrong platform CASE mapping, a missing `is_parent=0 AND wrong_sku=0` filter on the
traffic join, and a too-loose "any candidate" check instead of the builder's exact
MIN/first-non-null aggregation. After fixing the diagnostic script to match the
builder's logic precisely, all 100 records reconcile exactly on all 14 fields.

---

## 3. Supplier validation — **PASS**

Confirmed the join chain `supplier.order_items → supplier.orders → supplier.containers /
supplier.suppliers` with counts at every stage:

| Step | Count |
|---|---|
| `supplier.suppliers` (base) | 47 |
| `supplier.orders` (base) | 267 |
| `supplier.containers` (base) | 25 |
| `supplier.order_items` (base) | 4,029 |
| order_items with non-blank SKU | 4,027 |
| distinct SKUs in order_items | 1,541 |
| order_items ⋈ orders (INNER) | 4,029 (0 orphans — every item has an order) |
| ⋈ orders ⋈ containers (INNER, via `container_id`) | 3,906 (123 items' orders have no matching container row) |
| ⋈ orders ⋈ suppliers (INNER, via `supplier_id`) | 4,029 (0 orphans) |
| **Full chain, all 4 tables (INNER)** | **3,906** |
| Distinct SKUs via the dashboard's actual LEFT JOIN chain | 1,541 (matches builder's "supplier chain fetched LIVE: 1,541 SKUs") |
| Of those, distinct SKUs also present in `inv_products` | 1,494 |

The 123-row gap (orders whose `container_id` doesn't resolve to a `containers` row) is
absorbed harmlessly by the builder's `LEFT JOIN`s — those rows still surface supplier
name/PO, just with a blank container, which is correct behavior, not a defect.

---

## 4. Failure scenarios — **5 of 6 handled correctly; 3 real defects found; 2 gaps found**

All scenarios were run against a fully isolated scratch copy of the project (separate
directory, separate log/validation folders) so the real deliverables and, with one
disclosed exception, the real hub were never at risk.

| # | Scenario | Exec log | Validation report | Previous dashboard protected | Error message | Verdict |
|---|---|---|---|---|---|---|
| A | PostgreSQL unavailable | ✅ | ❌ **not generated** | ✅ (crash pre-write) | ✅ `OperationalError: ... timeout expired` | **Gap found** |
| B | Supplier schema unavailable | ✅ (partial) | ❌ **crashes before writing** | ✅ (crash pre-write) | ✅ (probe correctly logs missing grant) | **Bug found** |
| C | Upload/hub failure | ✅ | ✅ Result: PASS | ✅ hub not updated | ✅ `Push failed: connect ETIMEDOUT ...` | **PASS** |
| D | Empty listing data | ✅ | ✅ Result: FAIL | ⚠️ **hub protected, but local file overwritten** | ✅ `HARD FAILURES: Listing Data: listed rows present` | **Bug found** |
| E | Empty traffic data | ✅ | ✅ Result: PASS (soft-fail recorded) | N/A — publishes anyway | recorded but not surfaced as an alert | **Gap found** |
| F | Empty returns data | ✅ | ✅ Result: PASS (check can't fail) | N/A — publishes anyway | check is a no-op | **Gap found** |

### Defects found (not fixed, per the read-only mandate)

1. **No validation report on a hard PostgreSQL-connection failure.** The connection
   (`psycopg2.connect`, line 80) has no surrounding `try/except`, and the
   `validation_*.md` / `fetch_summary_*.json` files are only written at the very end of
   the script (lines 466/489). An unreachable database therefore produces an uncaught
   traceback in the log but **no validation report at all** — only the execution log
   captures the failure.

2. **`KeyError: 'fallback_rows'` if the supplier schema ever becomes unreadable.**
   `VAL['supplier']['fallback_rows']` is referenced at line 488 during report generation
   but is **never assigned anywhere in the file** (only `fallback_file` is set, at line
   132). Reproduced deterministically: pointing the schema probe at a nonexistent schema
   correctly triggers the documented cache-fallback path and logs the missing-grant
   message, then **crashes with an uncaught `KeyError` while writing the report** — the
   exact disaster-recovery path the code and skill-file documentation both claim is
   graceful is, in fact, broken. This only manifests if the current live `supplier`
   grant is ever revoked (it is currently intact and working).

3. **The local `dashboard-v1/index.html` is overwritten even when a hard validation
   check subsequently fails.** `PAGE.write_text(...)` (line 393) runs unconditionally,
   before any of the hard-gate checks (lines 422–494) and before the `sys.exit(1)` on
   failure. Reproduced with a forced empty-listing-data run: the script correctly
   detects the hard failure, exits 1, and the orchestrator correctly skips the hub
   publish — but the **local HTML file was already overwritten** with the run's
   necessarily-incomplete data before the check ran. The orchestrator's own log line,
   *"stage 1 build: FAILED — validation did not pass; dashboard left unchanged, skipping
   publish,"* is therefore **inaccurate for the local file** (only the hub-published
   version is actually protected). Practically bounded — the next successful run
   overwrites it again — but a repeat failure, or anyone inspecting the local file
   in between, would see a broken dashboard despite the reassuring log message.

### Gaps found (soft-validation design, not crashes)

4. **Empty traffic data silently publishes.** "Traffic fetched" is a soft (non-hard)
   check. When forced to zero, the report correctly shows `[FAIL] Traffic fetched — 0
   impressions`, but overall `RESULT: PASS` and the hub publish proceeds normally — a
   genuine traffic-source outage would ship a dashboard with zero impressions/clicks
   everywhere with no distinct alert beyond a line buried in the validation report.

5. **"Returns fetched" can never fail.** The check condition is `tot('ret') >= 0`,
   which is a tautology (a count can never be negative) — it will show `[PASS]`
   regardless of whether returns data is fully populated or completely empty. Confirmed
   by forcing the Amazon and eBay returns legs to zero rows: the check still reported
   `[PASS] Returns fetched — 51 units returned` (Shopify leg only). This check currently
   provides no actual detection of an empty-returns scenario.

### Disclosure: one scratch run unintentionally reached the live hub

While preparing the "empty traffic" simulation, an early patch attempt failed its own
assertion (formatting mismatch) *before* modifying the query, so the subsequent
orchestrator run executed with a **fully unmodified, valid builder** — but with the
real project's DB and hub credentials. It performed a genuine, valid refresh-and-publish
cycle against the **real production hub** (`varman_aios.hub_pages`, id 14), using fresh,
correct data equivalent to any normal scheduled run. No real project file was written
(the scratch copy's own `dashboard-v1/index.html` was rebuilt and pushed, not the
repo's), and the data pushed was valid and correct — but it was an unintended extra
publish cycle, not part of the original plan, so it's disclosed here for transparency.
All subsequent scenario tests were run as `build_new_scope.py` directly (no orchestrator,
no hub contact) to eliminate this risk.

---

## 5. Performance — bottleneck identified

| Phase | Time |
|---|---|
| DB connect | 0.82s |
| Supplier fetch (live) | 1.32s |
| Scope query | 0.50s |
| Row assembly (dominant cost) | 31.83s |
| — of which: **traffic query (traffic_data + ppc_performance join)** | **18.14s** |
| — of which: returns (3-way union) | 4.62s |
| — of which: product-image lookup | 3.93s |
| Validation | 0.04s |
| **Total** | **~34–36s** |

The traffic query is the single largest cost, over half of total build time, driven by
the full-table join against `traffic_data`/`ppc_performance` (no date-range index
appears to make this sub-second at full scale, though restricted samples resolve in
under 3s). Not a correctness issue — well within any reasonable daily cron budget — but
the clear place to look first if build time ever needs to shrink.

---

## 6. Duplicate/cache logic — **PASS, no reuse of stale data**

Confirmed by code inspection: the builder's only file reads are (a) `supplier_fresh.psv`,
read **only** inside the degraded-fallback path when the supplier schema is unreadable —
not touched on any normal run (all runs this session logged "supplier chain fetched
LIVE," never "from cache fallback"), and (b) the existing `index.html` itself, read
solely as a template shell to locate and replace the `const PAYLOAD` region — the
surrounding UI/CSS/JS is preserved, but every data value inside the payload is a fresh
PostgreSQL query result, not reused from any prior run. Two independent full pipeline
runs this session produced two different file hashes minutes apart — expected, correct
evidence of live fetching against a live database, not caching.

---

## 7. Output validation — **PASS**

- `capturedAt: "2026-07-27"` — matches today, confirms freshness.
- `const PAYLOAD =`, `id="tbl"`, `id="tbody"`, `</html>` — all present.
- 4,982 rows, 1,866 new components, 1,957 `compImg` entries embedded.
- 0/3,773 image URLs malformed, 0/3,085 listing URLs malformed (well-formed http/https
  with a valid host) — checked every non-blank URL in the payload, not a sample.
- 0 Listed rows missing a URL or Listing Date; 0 Not-Listed rows carrying a stray URL.
- Placeholder scan: initial hits for "TBD", "NaN", "undefined" were all false positives
  (substrings inside real SKUs like `CL2TBD`, real words like "Nano"/"Klemmenanschluss",
  and a legitimate `toLocaleString(undefined, …)` JS call). One genuine residual gap:
  SKU `PSOS2RROCO2PK` still shows the generic "Combo Default Title." description (1 row
  out of 4,982) — a source-data gap (no real title anywhere in `inv_products` or
  `listing_data` for that SKU), consistent with the same already-documented
  data-quality-gap pattern from the prior validation pass, not a pipeline defect.

---

## 8. Final handover summary

| Item | Result |
|---|---|
| **Overall result** | **PASS**, with 3 defects and 2 design gaps disclosed above (none currently active in production — all require a specific failure condition, like a lost grant, that isn't presently occurring) |
| Total records fetched (scope) | 3,383 new SKUs (1,866 components + 1,517 combos) |
| Total dashboard rows generated | 4,982 (3,085 Listed / 1,897 Not Listed) |
| Supplier validation | PASS — full 4-table chain traced, 3,906/4,029 order_items resolve end-to-end (123 orphaned containers absorbed gracefully via LEFT JOIN) |
| Traffic validation | PASS on live data (50,131,743 impressions, 156,775 clicks); soft-gate design means a genuine outage would publish silently (Gap #4) |
| Returns validation | PASS on live data (280 units); the validation check itself cannot detect an empty-returns scenario (Gap #5) |
| Listing validation | PASS — 100/100 sampled listing dates/URLs/marketplaces exact-matched |
| Upload status | Hub content MD5 == local file MD5 (exact match), confirmed independently via direct SQL query |
| Execution duration | 36.29s (real run) / ~34–36s typical |
| Revenue reconciliation | £107,462.92 dashboard == £107,462.92 independent PostgreSQL total |

### Remaining known limitations
- ~25% of rows have no product image (genuinely absent from `listing_data`, not a fetch
  defect — carried over from the prior validation pass).
- 1 combo SKU (`PSOS2RROCO2PK`) has no real title/description anywhere in source data.
- **3 defects requiring a decision** (Section 4, items 1–3): no validation report on a
  hard DB-connect failure; a guaranteed `KeyError` crash if the supplier grant is ever
  lost; and the local HTML file being overwritten (though the hub stays protected) on a
  hard validation failure, contradicting the orchestrator's own log message.
- **2 soft-validation gaps** (Section 4, items 4–5): an empty-traffic day would publish
  silently; the returns-fetched check can never fail regardless of actual data.

None of these were fixed, per the "do not modify unless a validation fails, then report
and seek approval" instruction — all five are flagged here for a decision on whether
and how to address them before or after handover.
