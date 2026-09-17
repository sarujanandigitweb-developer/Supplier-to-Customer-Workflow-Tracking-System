# Dashboard V2 — daily refresh resilience to transient PostgreSQL connection-limit failures

**Date:** 2026-09-17 · **Developer:** Sarujanan · **Reviewer:** Varmen (pending)
**Status:** PASS · **Published:** NO · **Committed:** NO · **Production database changes:** NONE

---

## 1. Requirement
Make the 11:00 cron refresh survive a temporary PostgreSQL connection-capacity refusal, without ever
publishing stale output and without masking real errors.

## 2. Observed original failure (evidence)
`logs/automation_v2.log`, twice:
```
2026-09-15 11:15:13 | stage 1 build: starting (fresh fetch from LEDSone ... as tech_user)
  File ".../dashboard-v2-sql/build_v2.py", line 78, in <module>
    conn = psycopg2.connect(connect_timeout=40, **DB)
psycopg2.OperationalError: connection to server at "169.58.91.229", port 5432 failed:
FATAL:  too many connections for role "tech_user"
2026-09-15 11:15:15 | stage 1 build: FAILED — ... skipping publish
2026-09-16 11:00:04 | stage 1 build: FAILED — ... skipping publish
```
**Which command failed:** stage 1, `/usr/bin/python3 dashboard-v2-sql/build_v2.py`, at its very first
`psycopg2.connect` to LEDSone (line 78) — proven by the traceback, not assumed. `make_html.py` and
`push_to_hub.js` were never reached. Log history: 25 stage-1 successes, 15 failures; the only
connection-type error ever recorded is `too many connections for role` (2 occurrences).

## 3. Root cause
The LEDSone role `tech_user` has a per-role connection limit that is occasionally saturated by other
clients at 11:00. The build made a single connection attempt and aborted the whole refresh.

## 4. Changed file
`scripts/refresh_and_publish_v2.sh` only (148 → 195 lines). **No** change to `build_v2.py`,
`make_html.py`, `v2_sources.py`, the dashboard, the Pack classification or any business rule.
Two additions:
1. A bounded retry loop around stage 1.
2. `V2_*` path overrides (`V2_BUILDER`, `V2_COMPOSER`, `V2_PUSHER_DIR`, `V2_LOG`, `V2_HTML`, `V2_LOCK`),
   each defaulting to the production path, so the retry logic can be tested against fakes. Cron passes
   none of them, so cron behaviour is unchanged.

## 5. Retry policy
| Setting | Value |
|---|---|
| Max attempts | **3** |
| Waits | **30 s** after attempt 1, **60 s** after attempt 2 |
| Retryable condition | `BUILD_RETRYABLE_RE='too many connections for role'` — the only transient pattern evidenced in this log |
| Everything else | fails immediately, never retried, never hidden: Python exceptions, SQL/schema errors, hard validation failures, classification failures, missing files, malformed payload |
| On exhaustion | log `[FATAL]`, skip compose and publish, `exit 1` |

## 6. Stale-publication protection (control flow)
```
stage 1 build  -> BUILD_OK=1 only when python3 build_v2.py exits 0 (payload rewritten)
   |  if BUILD_OK != 1 -> log [PUBLISH] skipped ... -> exit 1      (compose never runs)
stage 2 compose -> make_html.py rebuilds index.html from that fresh payload
   |  on failure   -> log [PUBLISH] skipped ... -> exit 1          (publish never runs)
pre-publish sanity -> file readable, >= 300,000 bytes, must contain
                      'const PAYLOAD =', 'id="tbl"', 'id="tbody"', 'id="viewtabs"', '</html>'
   |  on failure   -> exit 1
stage 3 publish -> push_to_hub.js (only reachable when all of the above passed)
```
A failed build therefore cannot publish yesterday's `payload_v2.json` or `dashboard-v2/index.html`:
publication is not a separate step that reads whatever is on disk — it is gated behind both stages
exiting 0 in the same run.

## 7. Tests (safe simulation — no connection exhaustion, no publishing)
The **real** script was executed with fakes injected through the `V2_*` overrides; the fake uploader
records the call instead of contacting the hub.

| Test | Scenario | Attempts | Waits | Exit | Compose | Publish | Result |
|---|---|---:|---|---:|---|---|---|
| **A** | attempt 1 succeeds | 1 | none | 0 | ran | eligible (fake called) | **PASS** |
| **B** | transient, then success | 2 | 30 s (measured 31 s) | 0 | ran after attempt 2 | eligible (fake called) | **PASS** |
| **C** | transient on all 3 | 3 | 30 s + 60 s (measured 90 s) | **1** | skipped | skipped | **PASS** |
| **D** | non-transient error (UndefinedTable / hard check) | 1 | none — **not retried** | **1** | skipped | skipped | **PASS** |
| **E** | build OK, compose fails | 1 | none | **1** | failed | skipped | **PASS** |

Log evidence (Test C):
```
[BUILD] attempt 1/3
[BUILD] transient PostgreSQL connection failure on attempt 1/3
[BUILD] retrying in 30 seconds
[BUILD] attempt 2/3
[BUILD] transient PostgreSQL connection failure on attempt 2/3
[BUILD] retrying in 60 seconds
[BUILD] attempt 3/3
[BUILD] attempt 3/3 failed
[FATAL] database build failed after 3 attempts — PostgreSQL connection capacity
stage 1 build: FAILED — dashboard left unchanged, payload NOT regenerated
[PUBLISH] skipped because fresh build did not complete
```
Test D log: `[BUILD] non-transient failure on attempt 1/3 — not retried`.

## 8. Cron-environment validation
The real script (real `build_v2.py`, real `make_html.py`, fake uploader) was run under a bare
environment: `env -i HOME=… PATH=/usr/bin:/bin SHELL=/bin/sh`.

| Item | Result |
|---|---|
| Working directory | script uses absolute `$PROJECT`, independent of cwd — OK |
| `.env` loading | `[ -r "$PROJECT/.env" ] && . "$PROJECT/.env"` — LEDSone credentials resolved |
| PATH | script sets `/usr/local/bin:/usr/bin:/bin` itself — OK |
| Python / Node | absolute `/usr/bin/python3`, `/usr/bin/node` — OK |
| flock | single-instance lock acquired — OK |
| Log destination | written, credentials redacted — **0** credential occurrences |
| Output paths | `payload_v2.json` 2,652,670 B and `index.html` 2,740,437 B regenerated |
| Outcome | `[BUILD] attempt 1/3` → success, compose OK, sanity OK (2,740,437 B), publish → **fake** uploader, **exit 0**, 134 s |

## 9. Fresh-build regression (after the change)
| Check | Result |
|---|---|
| Hard validation gates | **PASS** (only the standing soft FAIL "Average Feedback source") |
| `make_html` | PASS — HTML regenerated from the fresh payload |
| Components / Combos / Packs (All Data) | 677 / 407 / 211 → all products **1,295** |
| Main scope | 311 / 257 / 156 → 724 |
| Exclusivity | Component∩Combo 0 · Component∩Pack 0 · Combo∩Pack 0 · multi-category 0 |
| Relationships | 795 = 584 combo + 211 pack · missing 0 · extra 0 · duplicates 0 |
| Combo Components / Pack Count | 128 / 211 (unchanged definitions) |
| Packs whose component is outside the base set | 0 |
| Business logic | unchanged — no edit to any builder, source-mapping or UI rule |

Totals in `validation_v2.json` (revenue, impressions) move with live marketplace data; the scope and
classification counts are identical to the pre-change run.

## 10. Known limitations
- Retry covers only stage 1. A connection failure inside stage 3's hub publish (different database) is
  still a single attempt — not observed in the log, so not addressed.
- Only `too many connections for role` is retried. If a sibling capacity error such as
  `sorry, too many clients already` ever appears, add it to `BUILD_RETRYABLE_RE`.
- Worst case adds 90 s before a run gives up; the 11:00 slot has ample headroom.
- Cron still only fires while the machine is on.

## 11. Publication status
Nothing was published. The hub row still holds the 2026-09-15 11:15 artefact. During tests only the
fake uploader was invoked.

## 12. PASS / FAIL — **PASS**
First-attempt success causes no retry · transient capacity failure retries · max 3 attempts · bounded
30 s/60 s · non-transient errors are not hidden · 3 failures exit non-zero · a failed build cannot
publish old payload/HTML · compose failure cannot publish · fresh build passes · Pack/Combo/Component
classification unchanged · no business-logic change · no production database change · nothing published.

## 13. Next step
Request approval to publish the current build (Pack classification + All Data + retry) and to commit
the three changed files with this evidence.
