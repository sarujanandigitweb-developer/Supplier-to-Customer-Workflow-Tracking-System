#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Supplier→Customer Tracking System (SCWTS) — daily refresh, then publish.
#
# Called by cron at 11:00 (see `crontab -l`). Two gated stages:
#   1. dashboard-v1-sql/build_new_scope.py  -> connects to PostgreSQL, fetches
#      ALL datasets fresh, validates them, regenerates the embedded
#      `const PAYLOAD` inside dashboard-v1/index.html, writes the validation
#      report + fetch summary. Exits non-zero if any HARD check fails.
#   2. dashboard-v1-update/push_to_hub.js   -> upserts the finished HTML into
#      varman_aios.hub_pages (the EXISTING Varman AIOS upload implementation —
#      reused as-is, not reimplemented).
#
# Stage 2 runs ONLY if stage 1 exited 0 AND the HTML passes sanity checks, so a
# failed/partial build can never overwrite yesterday's good dashboard on the hub.
#
# Credentials: taken from the environment (optionally an adjacent .env), with
# the project defaults as a fallback. The connection string is never printed —
# it is redacted from the log as a backstop in case a driver error echoes it.
#
# Scope: only ever writes varman_aios.hub_pages for MEMBER_NAME below (upsert on
# (member_name, page_slug)). The credential can reach other tables; this must not.
# ---------------------------------------------------------------------------
set -uo pipefail

PROJECT="/home/led-247/Supplier-to-Customer-Workflow-Tracking-System"
MEMBER_NAME="sarujanan"
PAGE_SLUG="supplier-to-customer-workflow-tracking"
PAGE_TITLE="Supplier to Customer Tracking System"
HTML="$PROJECT/dashboard-v1/index.html"
BUILDER="$PROJECT/dashboard-v1-sql/build_new_scope.py"
PUSHER_DIR="$PROJECT/dashboard-v1-update"
LOG="$PROJECT/logs/automation.log"
MIN_BYTES=500000          # a healthy dashboard is ~1.7MB; never publish a stub

# cron gets a bare environment — set an explicit PATH.
PATH=/usr/local/bin:/usr/bin:/bin
export PATH

mkdir -p "$PROJECT/logs" "$PROJECT/validation"

log()    { printf '%s | %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >> "$LOG"; }
redact() { sed -E 's#(postgres(ql)?://[^:/@]+:)[^@]*@#\1***REDACTED***@#g' >> "$LOG" 2>&1; }

START_TS=$(date +%s)
log "================ SCWTS refresh + publish started ================"

# --- database credentials (env > .env > project defaults) --------------------
[ -r "$PROJECT/.env" ] && . "$PROJECT/.env"
export PGHOST="${PGHOST:-149.28.134.54}"
export PGPORT="${PGPORT:-5435}"
export PGDATABASE="${PGDATABASE:-order_management_copy}"
export PGUSER="${PGUSER:-temp_user}"
export PGPASSWORD="${PGPASSWORD:-12we34rt}"

# --- stage 1: fetch fresh data, validate, regenerate the embedded payload ----
log "stage 1 build: starting (fresh fetch from ${PGHOST}:${PGPORT}/${PGDATABASE})"
if /usr/bin/python3 "$BUILDER" 2>&1 | redact; then
  log "stage 1 build: OK — datasets validated, PAYLOAD regenerated"
else
  log "stage 1 build: FAILED — validation did not pass; dashboard left unchanged, skipping publish"
  log "================ finished (exit 1) ================"
  exit 1
fi

# --- pre-publish sanity: never ship a truncated or structurally broken page ---
if [ ! -r "$HTML" ]; then
  log "stage 2 publish: SKIPPED — $HTML not readable"; exit 1
fi
BYTES=$(wc -c < "$HTML")
if [ "$BYTES" -lt "$MIN_BYTES" ]; then
  log "stage 2 publish: SKIPPED — HTML only ${BYTES}B (< ${MIN_BYTES}B floor)"; exit 1
fi
for marker in 'const PAYLOAD =' 'id="tbl"' 'id="tbody"' '</html>'; do
  if ! grep -qF "$marker" "$HTML"; then
    log "stage 2 publish: SKIPPED — '$marker' missing from HTML"; exit 1
  fi
done
log "sanity: OK — ${BYTES} bytes, PAYLOAD + table + closing tag present"

# --- stage 2: publish via the EXISTING Varman AIOS upload implementation ------
HUB_DB_URL="$(/usr/bin/python3 - <<'PY'
import os, urllib.parse
q = lambda v: urllib.parse.quote(v, safe="")
print("postgresql://%s:%s@%s:%s/%s" % (
    q(os.environ["PGUSER"]), q(os.environ["PGPASSWORD"]),
    os.environ["PGHOST"], os.environ["PGPORT"], os.environ["PGDATABASE"]))
PY
)"
if [ -z "${HUB_DB_URL:-}" ]; then
  log "stage 2 publish: SKIPPED — could not build HUB_DB_URL"; exit 1
fi
export HUB_DB_URL

cd "$PUSHER_DIR" || { log "stage 2 publish: FAILED — cannot cd to $PUSHER_DIR"; unset HUB_DB_URL; exit 1; }
if /usr/bin/node push_to_hub.js "$MEMBER_NAME" "$PAGE_SLUG" "$PAGE_TITLE" "$HTML" 2>&1 | redact; then
  log "stage 2 publish: OK — ${MEMBER_NAME}/${PAGE_SLUG} (${BYTES} bytes)"
  STATUS=0
else
  log "stage 2 publish: FAILED — dashboard rebuilt locally but hub not updated"
  STATUS=1
fi
unset HUB_DB_URL

# --- execution summary -------------------------------------------------------
ELAPSED=$(( $(date +%s) - START_TS ))
LATEST_VAL=$(ls -1t "$PROJECT/validation"/validation_*.md 2>/dev/null | head -1)
RESULT=$(grep -m1 -o '\*\*Result: [A-Z]*\*\*' "$LATEST_VAL" 2>/dev/null | tr -d '*')
log "validation report: ${LATEST_VAL:-none}  (${RESULT:-n/a})"
log "execution time: ${ELAPSED}s"
log "================ finished (exit $STATUS) ================"
exit "$STATUS"
