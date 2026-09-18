#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# SCWTS Dashboard V2 — daily refresh, then publish to Varman AIOS.
#
# Called by cron at 11:00 (see `crontab -l`). Three gated stages:
#   1. dashboard-v2-sql/build_v2.py   -> probes supplier-schema access with the
#      project credential, fetches Listing / Traffic / Orders / Returns /
#      Supplier data fresh from PostgreSQL, runs 26 validation checks and
#      regenerates dashboard-v2-sql/payload_v2.json.
#      Exits NON-ZERO if any HARD check fails.
#   2. dashboard-v2-sql/make_html.py  -> embeds that payload into
#      dashboard-v2/index.html (self-contained, no external assets).
#   3. dashboard-v2-update/push_to_hub.js -> upserts the finished HTML into
#      varman_aios.hub_pages. This is the EXISTING Varman AIOS uploader,
#      reused as-is (byte-identical to dashboard-v1-update/push_to_hub.js).
#
# Stage 3 runs ONLY if stages 1-2 exited 0 AND the HTML passes sanity checks,
# so a failed or partial build can never overwrite yesterday's good dashboard.
#
# V1 (dashboard-v1) publishes to a DIFFERENT slug from its own script; this
# script never touches it.
#
# Credentials: taken from the environment (optionally an adjacent .env), with
# the project defaults as a fallback. The connection string is never printed —
# it is redacted from the log as a backstop in case a driver error echoes it.
# ---------------------------------------------------------------------------
set -uo pipefail

PROJECT="/home/led-247/Supplier-to-Customer-Workflow-Tracking-System"
MEMBER_NAME="sarujanan"
PAGE_SLUG="supplier-to-customer-workflow-tracking-v2"
PAGE_TITLE="Supplier to Customer Tracking System V2"
# Paths default to production; the V2_* overrides exist only so the retry logic can
# be exercised against fakes without touching the real build, HTML, log or uploader.
HTML="${V2_HTML:-$PROJECT/dashboard-v2/index.html}"
BUILDER="${V2_BUILDER:-$PROJECT/dashboard-v2-sql/build_v2.py}"
COMPOSER="${V2_COMPOSER:-$PROJECT/dashboard-v2-sql/make_html.py}"
PUSHER_DIR="${V2_PUSHER_DIR:-$PROJECT/dashboard-v2-update}"
LOG="${V2_LOG:-$PROJECT/logs/automation_v2.log}"
LOCK="${V2_LOCK:-$PROJECT/logs/.v2.lock}"

# --- stage-1 retry policy ----------------------------------------------------
# The ONLY retried condition is a temporary PostgreSQL connection-capacity
# refusal, evidenced twice in this log (2026-09-15 11:15, 2026-09-16 11:00):
#   psycopg2.OperationalError: ... FATAL:  too many connections for role "tech_user"
# The SAME class of failure reaches the build from the OLD reference DB with a
# different PostgreSQL wording, evidenced 2026-09-17 11:00 (the build was wrongly
# classified non-transient, never retried, and the dashboard went a day stale):
#   ... 149.28.134.54:5435 failed: FATAL:  remaining connection slots are
#   reserved for roles with the SUPERUSER attribute
# 'sorry, too many clients already' is the third wording of the same condition.
# Everything else -- Python exceptions, SQL/schema errors, hard validation
# failures, classification failures, missing files -- fails immediately and is
# never masked. Bounded: 3 attempts, waits of 30s then 60s, then give up.
BUILD_MAX_ATTEMPTS=3
BUILD_RETRY_WAITS=(30 60)
BUILD_RETRYABLE_RE='too many connections for role|remaining connection slots are reserved|sorry, too many clients already'

MIN_BYTES=300000          # a healthy V2 dashboard is ~475 KB; never publish a stub

# cron gets a bare environment — set an explicit PATH.
PATH=/usr/local/bin:/usr/bin:/bin
export PATH

mkdir -p "$PROJECT/logs" "$PROJECT/validation"

log()    { printf '%s | %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >> "$LOG"; }
redact() { sed -E 's#(postgres(ql)?://[^:/@]+:)[^@]*@#\1***REDACTED***@#g' >> "$LOG" 2>&1; }

# Single-instance guard: a slow run must never stack on top of itself (both
# builds would hammer the same PostgreSQL traffic tables concurrently).
exec 9>"$LOCK"
if ! flock -n 9; then
  log "SKIPPED — another V2 run is still in progress (lock held)"
  exit 0
fi

START_TS=$(date +%s)
log "================ SCWTS V2 refresh + publish started ================"

# --- database credentials (env > .env > project defaults) --------------------
[ -r "$PROJECT/.env" ] && . "$PROJECT/.env"
export PGHOST="${PGHOST:-149.28.134.54}"
export PGPORT="${PGPORT:-5435}"
export PGDATABASE="${PGDATABASE:-order_management_copy}"
export PGUSER="${PGUSER:-temp_user}"
export PGPASSWORD="${PGPASSWORD:-12we34rt}"

# --- stage 1: fetch fresh data, probe supplier access, validate --------------
# Data comes from LEDSone (LEDSONE_PG* in .env); the PG* database above is used
# only for the deleted-product reference and the Varman AIOS hub publish.
log "stage 1 build: starting (fresh fetch from LEDSone ${LEDSONE_PGHOST:-<unset>}:${LEDSONE_PGPORT:-5432}/${LEDSONE_PGDATABASE:-<unset>} as ${LEDSONE_PGUSER:-<unset>}; deleted-flag reference ${PGHOST}:${PGPORT}/${PGDATABASE})"
BUILD_OK=0
BUILD_ATTEMPT=1
while [ "$BUILD_ATTEMPT" -le "$BUILD_MAX_ATTEMPTS" ]; do
  log "[BUILD] attempt ${BUILD_ATTEMPT}/${BUILD_MAX_ATTEMPTS}"
  BUILD_OUT="$(mktemp "${TMPDIR:-/tmp}/v2build.XXXXXX")"
  if /usr/bin/python3 "$BUILDER" > "$BUILD_OUT" 2>&1; then
    redact < "$BUILD_OUT"; rm -f "$BUILD_OUT"
    log "[BUILD] success on attempt ${BUILD_ATTEMPT}/${BUILD_MAX_ATTEMPTS}"
    log "stage 1 build: OK — supplier access verified, datasets validated, payload regenerated"
    BUILD_OK=1
    break
  fi
  redact < "$BUILD_OUT"
  if grep -qE "$BUILD_RETRYABLE_RE" "$BUILD_OUT"; then
    log "[BUILD] transient PostgreSQL connection failure on attempt ${BUILD_ATTEMPT}/${BUILD_MAX_ATTEMPTS}"
    if [ "$BUILD_ATTEMPT" -lt "$BUILD_MAX_ATTEMPTS" ]; then
      WAIT=${BUILD_RETRY_WAITS[$((BUILD_ATTEMPT-1))]}
      log "[BUILD] retrying in ${WAIT} seconds"
      rm -f "$BUILD_OUT"
      sleep "$WAIT"
      BUILD_ATTEMPT=$((BUILD_ATTEMPT+1))
      continue
    fi
    log "[BUILD] attempt ${BUILD_ATTEMPT}/${BUILD_MAX_ATTEMPTS} failed"
    log "[FATAL] database build failed after ${BUILD_MAX_ATTEMPTS} attempts — PostgreSQL connection capacity"
  else
    log "[BUILD] non-transient failure on attempt ${BUILD_ATTEMPT}/${BUILD_MAX_ATTEMPTS} — not retried"
    log "[FATAL] database build failed — hard validation / Python / SQL error, not a connection-capacity problem"
  fi
  rm -f "$BUILD_OUT"
  break
done

if [ "$BUILD_OK" -ne 1 ]; then
  log "stage 1 build: FAILED — dashboard left unchanged, payload NOT regenerated"
  log "[PUBLISH] skipped because fresh build did not complete"
  log "================ finished (exit 1) ================"
  exit 1
fi

# --- stage 2: embed the payload into the HTML --------------------------------
if /usr/bin/python3 "$COMPOSER" 2>&1 | redact; then
  log "stage 2 compose: OK — payload embedded into dashboard-v2/index.html"
else
  log "stage 2 compose: FAILED — HTML not regenerated"
  log "[PUBLISH] skipped because the HTML was not regenerated from the fresh payload"
  log "================ finished (exit 1) ================"
  exit 1
fi

# --- pre-publish sanity: never ship a truncated or structurally broken page ---
if [ ! -r "$HTML" ]; then
  log "stage 3 publish: SKIPPED — $HTML not readable"
  log "================ finished (exit 1) ================"; exit 1
fi
BYTES=$(wc -c < "$HTML")
if [ "$BYTES" -lt "$MIN_BYTES" ]; then
  log "stage 3 publish: SKIPPED — HTML only ${BYTES}B (< ${MIN_BYTES}B floor)"
  log "================ finished (exit 1) ================"; exit 1
fi
for marker in 'const PAYLOAD =' 'id="tbl"' 'id="tbody"' 'id="viewtabs"' '</html>'; do
  if ! grep -qF "$marker" "$HTML"; then
    log "stage 3 publish: SKIPPED — '$marker' missing from HTML"
    log "================ finished (exit 1) ================"; exit 1
  fi
done
log "sanity: OK — ${BYTES} bytes, PAYLOAD + table + tabs + closing tag present"

# --- stage 3: publish via the EXISTING Varman AIOS upload implementation ------
HUB_DB_URL="$(/usr/bin/python3 - <<'PY'
import os, urllib.parse
q = lambda v: urllib.parse.quote(v, safe="")
print("postgresql://%s:%s@%s:%s/%s" % (
    q(os.environ["PGUSER"]), q(os.environ["PGPASSWORD"]),
    os.environ["PGHOST"], os.environ["PGPORT"], os.environ["PGDATABASE"]))
PY
)"
if [ -z "${HUB_DB_URL:-}" ]; then
  log "stage 3 publish: SKIPPED — could not build HUB_DB_URL"
  log "================ finished (exit 1) ================"; exit 1
fi
export HUB_DB_URL

cd "$PUSHER_DIR" || { log "stage 3 publish: FAILED — cannot cd to $PUSHER_DIR"; unset HUB_DB_URL; exit 1; }
if /usr/bin/node push_to_hub.js "$MEMBER_NAME" "$PAGE_SLUG" "$PAGE_TITLE" "$HTML" 2>&1 | redact; then
  log "stage 3 publish: OK — ${MEMBER_NAME}/${PAGE_SLUG} (${BYTES} bytes)"
  STATUS=0
else
  log "stage 3 publish: FAILED — dashboard rebuilt locally but hub not updated"
  STATUS=1
fi
unset HUB_DB_URL

# --- execution summary -------------------------------------------------------
ELAPSED=$(( $(date +%s) - START_TS ))
RESULT=$(/usr/bin/python3 -c "
import json,sys
try:
    v=json.load(open('$PROJECT/dashboard-v2-sql/validation_v2.json'))
    t=v.get('totals',{}); tc=v.get('totals_components',{})
    print(f\"Result: {v.get('result','?')} | combo rows {t.get('rows','?')} / component rows {tc.get('rows','?')}\"
          f\" | revenue {t.get('revenue','?')} | impressions {t.get('impressions','?')}\")
except Exception as e:
    print('validation summary unavailable:', e)
" 2>/dev/null)
log "validation: ${RESULT:-n/a}"
log "execution time: ${ELAPSED}s"
log "================ finished (exit $STATUS) ================"
exit "$STATUS"
