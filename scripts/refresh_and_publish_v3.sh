#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# SCWTS Dashboard V3 (Container-to-Customer) — daily refresh, then publish to
# Varman AIOS.  Same three-stage structure as refresh_and_publish_v2.sh.
#
# Called by cron at 16:00 (see `crontab -l`). Three gated stages:
#   1. dashboard-v3-sql/build_v3.py       -> reads the Google-Sheet container
#      mapping (sheet_containers.json), probes source availability, fetches
#      Listing / Traffic / Orders / Returns fresh from PostgreSQL, runs the
#      validation checks and regenerates dashboard-v3-sql/payload_v3.json.
#      Exits NON-ZERO if any HARD check fails.
#   2. dashboard-v3-sql/make_html_v3.py   -> embeds that payload into
#      dashboard-v3/index.html (self-contained, no external assets).
#   3. dashboard-v3-update/push_to_hub.js -> upserts the finished HTML into
#      varman_aios.hub_pages. This is the EXISTING Varman AIOS uploader,
#      reused as-is (byte-identical to dashboard-v2-update/push_to_hub.js).
#
# Stage 3 runs ONLY if stages 1-2 exited 0 AND the HTML passes sanity checks,
# so a failed or partial build can never overwrite yesterday's good dashboard.
#
# V1 and V2 publish to DIFFERENT slugs from their own scripts; this script
# never touches them.
#
# Credentials: taken from the environment (optionally an adjacent .env), with
# the project defaults as a fallback. The connection string is never printed —
# it is redacted from the log as a backstop in case a driver error echoes it.
# ---------------------------------------------------------------------------
set -uo pipefail

PROJECT="/home/led-247/Supplier-to-Customer-Workflow-Tracking-System"
MEMBER_NAME="sarujanan"
PAGE_SLUG="container-to-customer-workflow-tracking"
PAGE_TITLE="Container Tracking V3 — Supplier's Basket to Customer's Home"
HTML="$PROJECT/dashboard-v3/index.html"
BUILDER="$PROJECT/dashboard-v3-sql/build_v3.py"
COMPOSER="$PROJECT/dashboard-v3-sql/make_html_v3.py"
PUSHER_DIR="$PROJECT/dashboard-v3-update"
LOG="$PROJECT/logs/automation_v3.log"
LOCK="$PROJECT/logs/.v3.lock"
MIN_BYTES=300000          # a healthy V3 dashboard is ~455 KB; never publish a stub

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
  log "SKIPPED — another V3 run is still in progress (lock held)"
  exit 0
fi

START_TS=$(date +%s)
log "================ SCWTS V3 refresh + publish started ================"

# --- database credentials (env > .env > project defaults) --------------------
[ -r "$PROJECT/.env" ] && . "$PROJECT/.env"
export PGHOST="${PGHOST:-149.28.134.54}"
export PGPORT="${PGPORT:-5435}"
export PGDATABASE="${PGDATABASE:-order_management_copy}"
export PGUSER="${PGUSER:-temp_user}"
export PGPASSWORD="${PGPASSWORD:-12we34rt}"

# --- the Google Sheet mapping is V3's scope authority; without it, stop -------
SHEETMAP="$PROJECT/dashboard-v3-sql/sheet_containers.json"
if [ ! -s "$SHEETMAP" ]; then
  log "stage 1 build: SKIPPED — container mapping $SHEETMAP is missing or empty."
  log "  Re-generate it with: python3 dashboard-v3-sql/read_sheet.py"
  log "================ finished (exit 1) ================"; exit 1
fi

# --- stage 1: fetch fresh data, validate, regenerate the payload -------------
log "stage 1 build: starting (fresh fetch from ${PGHOST}:${PGPORT}/${PGDATABASE} as ${PGUSER})"
if /usr/bin/python3 "$BUILDER" 2>&1 | redact; then
  log "stage 1 build: OK — container mapping applied, datasets validated, payload regenerated"
else
  log "stage 1 build: FAILED — a HARD validation check did not pass; dashboard left unchanged, skipping publish"
  log "================ finished (exit 1) ================"
  exit 1
fi

# --- stage 2: embed the payload into the HTML --------------------------------
if /usr/bin/python3 "$COMPOSER" 2>&1 | redact; then
  log "stage 2 compose: OK — payload embedded into dashboard-v3/index.html"
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
for marker in 'const PAYLOAD =' 'id="tbl"' 'id="tbody"' 'id="conttabs"' '</html>'; do
  if ! grep -qF "$marker" "$HTML"; then
    log "stage 3 publish: SKIPPED — '$marker' missing from HTML"
    log "================ finished (exit 1) ================"; exit 1
  fi
done
# self-contained check: the hub renders the page as-is, external assets break it
if grep -qE '<script[^>]*src="|<link[^>]*href="https?://' "$HTML"; then
  log "stage 3 publish: SKIPPED — HTML references an external asset; must be self-contained"
  log "================ finished (exit 1) ================"; exit 1
fi
log "sanity: OK — ${BYTES} bytes, PAYLOAD + table + container tabs + closing tag present, self-contained"

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
import json
try:
    v=json.load(open('$PROJECT/dashboard-v3-sql/validation_v3.json'))
    t=v.get('totals',{})
    fails=[c['check'] for c in v.get('checks',[]) if c['status']=='FAIL']
    print(f\"containers {t.get('containers','?')} | components {t.get('components','?')}\"
          f\" | rows {t.get('rows','?')} | listed {t.get('listed','?')}\"
          f\" | revenue {t.get('revenue','?')} | soft-fails {len(fails)}\")
except Exception as e:
    print('validation summary unavailable:', e)
" 2>/dev/null)
log "validation: ${RESULT:-n/a}"
log "execution time: ${ELAPSED}s"
log "================ finished (exit $STATUS) ================"
exit "$STATUS"
