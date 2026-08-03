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
HTML="$PROJECT/dashboard-v2/index.html"
BUILDER="$PROJECT/dashboard-v2-sql/build_v2.py"
COMPOSER="$PROJECT/dashboard-v2-sql/make_html.py"
PUSHER_DIR="$PROJECT/dashboard-v2-update"
LOG="$PROJECT/logs/automation_v2.log"
LOCK="$PROJECT/logs/.v2.lock"
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
log "stage 1 build: starting (fresh fetch from ${PGHOST}:${PGPORT}/${PGDATABASE} as ${PGUSER})"
if /usr/bin/python3 "$BUILDER" 2>&1 | redact; then
  log "stage 1 build: OK — supplier access verified, datasets validated, payload regenerated"
else
  log "stage 1 build: FAILED — a HARD validation check did not pass; dashboard left unchanged, skipping publish"
  log "================ finished (exit 1) ================"
  exit 1
fi

# --- stage 2: embed the payload into the HTML --------------------------------
if /usr/bin/python3 "$COMPOSER" 2>&1 | redact; then
  log "stage 2 compose: OK — payload embedded into dashboard-v2/index.html"
else
  log "stage 2 compose: FAILED — HTML not regenerated, skipping publish"
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
