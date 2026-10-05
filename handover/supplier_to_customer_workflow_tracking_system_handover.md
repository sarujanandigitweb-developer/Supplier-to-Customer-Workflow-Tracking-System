# Supplier to Customer Workflow Tracking System (SCWTS) - Handover

Project name: `supplier_to_customer_workflow_tracking_system` | Project code: `scwts` | Folder: `/home/led-247/Supplier-to-Customer-Workflow-Tracking-System`
Developer: Sarujanan (git author `sarujanandigitweb-developer`) | Handover written: 2026-10-05 | Latest commit: `5e5bd8f` (2026-10-05) | Git status: clean, `main` = `origin/main`
Source of truth: the current code and this folder. Old docs (`AUTOMATION.md`, `documentation/`, `workflows/`, `capability/`) describe the July V1 and are outdated.

## 1. Project Overview

SCWTS is a set of self-contained HTML dashboards, titled "Supplier's Basket to Customer's Home", that follow every new 2026 product from supplier/container to marketplace listing and then to customer outcomes (impressions, clicks, orders, units, revenue, returns, feedback). Requested by Varmen; data owners are listed in section 11. There are three generations in one repo:

| Version | Folder | Scope | Hub page slug (member `sarujanan`) | Status |
|---|---|---|---|---|
| V1 | `dashboard-v1/` | Every new 2026 SKU (3,383 in July): one row per SKU x marketplace, listed/not listed, orders, traffic, returns. Source: old DB `order_management_copy` | `supplier-to-customer-workflow-tracking` | FROZEN. Daily cron is broken (build code deleted from repo). Hub copy is the 2026-09-11 build |
| V2 | `dashboard-v2/` | New 2026 components (inventory) and combos/packs derived from them, with supplier/PO/supply status. Source: LEDSone DB | `supplier-to-customer-workflow-tracking-v2` | LIVE, main dashboard. Last successful cron publish 2026-09-21 11:02 |
| V3 | `dashboard-v3/` | Container-to-customer: scope is a manager Google-Sheet of containers 11-17 (209 component SKUs) | `container-to-customer-workflow-tracking` | LIVE. Last successful cron publish 2026-10-01 16:03 |

All dashboards are single static HTML files with the data embedded as `const PAYLOAD = {...}`. Publishing = upsert of the HTML into `varman_aios.hub_pages` (Varman AIOS hub, a Vercel site that reads that table).

## 2. Final Status

- Overall: Known Limitation / External Dependency. V2 and V3 build, validate and publish automatically; V1 is retired in practice but its cron still fires and fails every day.
- V2 (LIVE): last validation `RESULT: PASS`, run 20260921_110001: combos rows 999 (311 components, 440 combos), component rows 435, revenue 19,208.57 (combo view), impressions 4,788,755. Only standing soft failure: "Average Feedback source" (no review table in the V2 source).
- V3 (LIVE): last build 2026-10-01: 6 containers (17 is empty), 209 components, 314 combos, 868 rows, 734 listed, revenue 37,919.80. Exit 0 but 5 soft FAILs (see section 10).
- V1: last successful publish 2026-09-11 (hub id of that page not documented here). Cron entry runs `scripts/refresh_and_publish.sh` at 11:15 and has failed every day since 2026-09-15 (`dashboard-v1-sql/build_new_scope.py: No such file`).
- Cron runs only while the PC is powered on. `logs/automation_v2.log` has no runs between 2026-09-22 and 2026-10-05 and V3 only has 2026-10-01 after 09-21, so expect gaps.
- Nothing is pending in git. Commits are on `origin/main`. A zip backup of the whole folder exists one level up (`Supplier-to-Customer-Workflow-Tracking-System.zip`, 2026-10-05). The sibling folder `Supplier-to-Customer-Workflow-Tracking-System (Copy)` is a stale duplicate from 2026-09-14; do not use or edit it.

## 3. Latest Updates

Chronology (git + `daily_works_logs/` + `validation/`):

| Date | Change |
|---|---|
| 2026-07-21 to 07-27 | V1 built (see `daily_works_logs/` D01-D05): inventory-table driven scope, 13 validation checks (8 HARD / 5 soft), daily cron + hub publish |
| 2026-07-28 to 08-03 | V2 created (`build_v2.py`, `make_html.py`, `refresh_and_publish_v2.sh`); V3 data spec and builder (`dashboard-v3-sql/V3_DATA_SOURCE_SPEC.md`) |
| 2026-08-03/08-18 | V3 builder fix (sheet image beats marketplace image), V3 cron script added 08-18 |
| 2026-09-14 | Commit `2061344`: V2 data source migrated from the old DB to LEDSone via `v2_sources.py` temp views. V1 build code (`dashboard-v1-sql/`, `dashboard-v1-update/`) deleted from the repo |
| 2026-09-15/16 | User-approved V2 rules in `build_v2.py`: stock-in received-date fallback, Rule A (latest PO not arrived -> show last arrived PO), Rule B (still blank -> latest UK stock-in receipt). Gap report `validation/DB_Designer_Gap_Report_Container_Received_20260915.md` |
| 2026-09-17 | Pack classification (Component / Combo / Pack, Packs tab, All Data counts) using `inventory.product_pk`; retry logic for DB connection failures in `refresh_and_publish_v2.sh` (`741af8e`); closure doc `validation/V2_commit_history_closure_20260917.md` (control exception: pushed before staged-scope review; history not rewritten) |
| 2026-09-18 | Commit `34af9a6` "fix: prevent stale V2 dashboard after database connection limits": retry regex widened to the 3 wordings of a connection-capacity refusal (`too many connections for role`, `remaining connection slots are reserved`, `sorry, too many clients already`). Reconciliation proved the listing SQL correct (0 missing / 0 unexplained / 0 duplicates, 2,380 Listed) - see `validation/V2_missing_listing_reconciliation_20260918.md`. Commit `d56a944`: refreshed artifacts + `validation/listing_status_audit_20260917/` |
| 2026-10-05 | Final commit `5e5bd8f` "Enhance SCWTS with comprehensive logging and validation improvements": despite the title it only adds daily logs D03/D04 (`daily_works_logs/2026-09-17...REQ-03-D03.md`, `2026-09-18...REQ-03-D04.md`), refreshed V2/V3 payloads, HTML and validation JSON, and appends to `logs/automation*.log`. The only code-like change is a CSS block in `dashboard-v3/index.html` (3 view tabs fit a phone row) plus the V3 payload dated 2026-10-01 |

Latest working implementation to continue from: V2 (`dashboard-v2-sql/build_v2.py` -> `make_html.py` -> `push_to_hub.js` driven by `scripts/refresh_and_publish_v2.sh`) and V3 (same pattern with `build_v3.py` / `make_html_v3.py` / `refresh_and_publish_v3.sh`).

## 4. Project Structure / Important Files

```
Supplier-to-Customer-Workflow-Tracking-System/
  .env                      git-ignored; only LEDSONE_PGHOST/PORT/DATABASE/USER/PASSWORD/SSLMODE
  scripts/
    refresh_and_publish.sh      V1 orchestrator (BROKEN - target scripts deleted)
    refresh_and_publish_v2.sh   V2 orchestrator (flock lock, retry x3, sanity gate, publish)
    refresh_and_publish_v3.sh   V3 orchestrator (flock lock, sheet-mapping guard, publish)
  dashboard-v1/index.html       V1 page (frozen; ALSO REQUIRED by V2: make_html.py copies its CSS)
  dashboard-v2/index.html       V2 composed page
  dashboard-v2-sql/
    build_v2.py        V2 builder: queries, classification, 26 validation checks -> payload_v2.json + validation_v2.json
    v2_sources.py      LEDSone -> old-table-shape pg_temp views (fix source mappings HERE, not in build_v2 SQL)
    make_html.py       payload -> dashboard-v2/index.html (all CSS/JS)
    v2_queries.sql     reference queries (July)
  dashboard-v2-update/push_to_hub.js (+package.json, node_modules)  hub uploader
  dashboard-v3/index.html
  dashboard-v3-sql/
    build_v3.py, make_html_v3.py, validate_v3.py, read_sheet.py
    sheet_containers.json   container -> SKU mapping (static, generated from the xlsx)
    ledsone_products.json   static cache of LEDSone inventory.products (31 Jul)
    V3_DATA_SOURCE_SPEC.md, payload_v3.json, validation_v3.json
  dashboard-v3-data/        manager sheet "New Containers to UK - 2026 .xlsx" (+ Container 11 csv)
  dashboard-v3-update/push_to_hub.js
  .claude/skills/dashboard-v2-daily/SKILL.md   project skill: V2 daily procedure and approved rules
  daily_works_logs/   per-day SKILL md, daily-activities CSV, ingest SQL (memory table daily_task.tbl_scwts_sarujanan)
  validation/         per-run V1 validation (to 2026-09-11), V2 evidence reports, listing_status_audit_20260917/
  logs/               automation.log (V1), automation_v2.log, automation_v3.log, cron*.out
  sql/, dashboard_refresh.py, dashboard/   legacy original dashboard (July, pre-V1) - not scheduled
  documentation/, workflows/, capability/, skills/, AUTOMATION.md   July-era docs (outdated; AUTOMATION.md describes V1 at 11:00, now 11:15 and broken)
```
Missing from the repo: `dashboard-v1-sql/` and `dashboard-v1-update/` (deleted 2026-09-14/15; recoverable with `git show 54e63d5:dashboard-v1-sql/build_new_scope.py` or from the "(Copy)" folder). The `.claude/skills/dashboard-v2-daily` skill is project-local; the home `~/.claude/skills/synced` folder does not contain it.

## 5. Data Sources / Database Tables

V2 (LEDSone, read-only `tech_user`, host/db/port in project `.env`):
- `inventory.products` (component scope: `inventory_bool = true`, `created_at >= start of current year`, non-blank SKU, not deleted), `inventory.product_pk` (pack codes, read each run), `inventory.product_history` (frozen partial copy, NOT used)
- `suppliers.orders`, `suppliers.old_supplyorder`, `suppliers.old_supplyorderlist` (PO / SUPPLY resolution, container, received date)
- `configurator.components_sot_skus` (SOT column)
- Listings: `listings.amazon_listings`, `ebay_listings`, `shopify_listings`, `bandq_listings`
- Orders: `order_management.orders` / `order_item_info`; traffic: `business_reports.*`, `amazon_campaigns` / `ebay_campaigns` / `google_ads.product_performance`; returns: `customer_service.*_returns`
- All remapped to the old table shapes as pg_temp views by `dashboard-v2-sql/v2_sources.py`. LEDSone lacks `inv_product_combo` (derived from `sku_original` tokens plus pack suffix) and `isdeleted`.
- Old DB (`order_management_copy`, env `PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD`, NOT in `.env`): V2 uses it only for `public.inv_products.isdeleted` and for 10 order sources LEDSone does not carry (REPLACEMENT, ETSY, MANUAL OM, MANUALORDER, AVASAM, BOL, MANOMANO, FAIRE, RESEND, ONBUY; guarded - build stops if LEDSone starts carrying one). All V1/V2/V3 hub publishes write to `varman_aios.hub_pages` on this DB.
- Timestamps: listings/suppliers in LEDSone are UTC (+5h30 applied). `google_ads.product_performance` has superseded duplicate ids (latest `updated_at` per id).

V3: Google Sheet export `dashboard-v3-data/New Containers to UK - 2026 .xlsx` (container -> SKU authority, parsed by `read_sheet.py`); old DB `public.listing_data`, `order_transaction`, `traffic_data`, `ppc_performance` for listings/orders/traffic; `ledsone_products.json` cache for created dates; V3 returns come from the old DB (reported as 129 in the last run). Old DB `inv_products`, `inv_product_combo`, `supplier.*` are empty/dropped there, so they are not used.

V1 (frozen): old DB `inv_products`, `inv_product_combo` (product = combo id, inventory = component id), `inv_final_stock`, `listing_data`, `order_transaction`, `traffic_data`, `ppc_performance`, `amazon/ebay/shopify_returns`, `supplier.*`.

## 6. Current Workflow / Architecture

V2 and V3 share one pipeline: orchestrator shell script (cron) -> stage 1 builder (fetch, validate, write payload JSON; non-zero exit on any HARD failure) -> stage 2 composer (embed payload into HTML) -> sanity gate (file size floor 300 KB, markers `const PAYLOAD =`, `id="tbl"`, `id="tbody"`, `id="viewtabs"` (V2) / `id="conttabs"` (V3), `</html>`; V3 also rejects external `<script src>` / `<link href=http>`) -> stage 3 `push_to_hub.js` upsert. A failed build never overwrites the previous hub page.

V2 business rules (approved; full text in `.claude/skills/dashboard-v2-daily/SKILL.md` section 3):
- Components: new this year, not deleted. Status is an attribute not a filter: COMPLETED / INCOMING / NO SUPPLY DATA. Arrived PO (`status_arrived = true`) and completed supply (`lower(trim(status)) = 'completed'`) both count as arrived; the most recent wins. Never parse `product_history` "Supply - SU..." text.
- Combos qualify only if they use a base component (pack suffix `[A-Z]?[0-9]*PK`); deleted combos excluded; the combo's own created date is not a condition.
- Classification Component / Combo / Pack (tabs). Default view = completed-only; "All Data" button shows the full base set (must default OFF).
- Listing: resolved via mapped_sku/sku, window `created_at >= 2026-01-01`, not parent, not wrong_sku, eBay ended excluded. Revenue = completed orders. Category from SKU prefix (longest first: PH = Pendant Lamp Holder, WS = Wall Arm, else Other).
- Rules A/B for received date (see section 3, 2026-09-15). Open and unapproved: `fc.status='completed'` is not proof of receipt (~42 false dates).
- Last numbers (2026-09-21): main view 311 components / 272 combos / 168 packs; All Data 686 / 427 / 226 (SKILL.md section 4 lists older targets 311/411 and 677/615 - treat as outdated; the checks it describes still apply).

V3 rules: row grain = one row per (container, product, marketplace) where product is the combo if one exists else the component (never component x combo x marketplace - the V2 fan-out bug, regression-gated). Combos derived from SKU naming (pack: `<COMP>[0-9A-Z]*PK`; combo: `+`-joined token list containing the component). Component image = sheet "Image Link" first, marketplace image as fallback. Supplier and Received Date columns intentionally removed.

## 7. How to Run

Always from the project folder with the environment loaded:
```bash
cd /home/led-247/Supplier-to-Customer-Workflow-Tracking-System
set -a && . ./.env && set +a            # LEDSONE_PG* (never print or commit)
# V2 (needs old-DB PG* variables too; otherwise the code falls back to a hard-coded default - see section 10)
python3 dashboard-v2-sql/build_v2.py     # prints RESULT: PASS/FAIL, writes payload_v2.json + validation_v2.json
python3 dashboard-v2-sql/make_html.py    # writes dashboard-v2/index.html (needs dashboard-v1/index.html)
# V3
python3 dashboard-v3-sql/read_sheet.py   # only when the xlsx changes: regenerates sheet_containers.json
python3 dashboard-v3-sql/build_v3.py && python3 dashboard-v3-sql/make_html_v3.py
```
Full automated run (same as cron): `scripts/refresh_and_publish_v2.sh` / `scripts/refresh_and_publish_v3.sh` (both write the real hub - run only when you intend to publish). LEDSone `tech_user` often hits "too many connections for role": retry (the V2 script already retries 3 times: waits 30 s then 60 s).
Manual publish (only when approved): `cd dashboard-v2-update && HUB_DB_URL=<set inline, never in a file> node push_to_hub.js sarujanan <slug> "<title>" ../dashboard-v2/index.html`.

## 8. Refresh / Deployment Process

Crontab of user `led-247` (read-only inspection 2026-10-05):

| Version | Schedule | Command | Log |
|---|---|---|---|
| V2 | `0 11 * * *` | `scripts/refresh_and_publish_v2.sh` | `logs/automation_v2.log`, `logs/cron_v2.out` |
| V1 | `15 11 * * *` | `scripts/refresh_and_publish.sh` | `logs/automation.log`, `logs/cron.out` (fails daily) |
| V3 | `0 16 * * *` | `scripts/refresh_and_publish_v3.sh` | `logs/automation_v3.log`, `logs/cron_v3.out` |

The crontab also contains jobs of other projects (WLSP, PSLD, RRHD, ANPIA, SOT listing, postage); do not touch them. System timezone Asia/Colombo.
Deployment = hub publish: `push_to_hub.js` runs `INSERT INTO varman_aios.hub_pages (member_name, page_slug, page_title, html_content) ... ON CONFLICT (member_name, page_slug) DO UPDATE` with member `sarujanan`. It reads `HUB_DB_URL` from the environment; the shell scripts build it from the `PG*` variables and redact connection strings in logs. The shared credential reaches beyond this table, so only ever upsert your own rows (member `sarujanan`). Check a publish with `Pushed successfully` in the log; no site redeploy is needed.
To retire V1 cleanly: remove the V1 cron line (decision for the owner, not done).

## 9. Validation Completed

- V2 builder: 26 checks per run (`dashboard-v2-sql/validation_v2.json`, last PASS 2026-09-21). Evidence: `validation/V2_pack_classification_all_products_cron_validation_20260917.md`, `V2_daily_refresh_retry_validation_20260917.md` (retry behaviour proven on fakes: transient -> 3 attempts then stop; hard failure -> no retry; failed build -> no compose, no publish), `V2_missing_listing_reconciliation_20260918.md` (0 missing / 0 unexplained / 0 duplicates), `V2_commit_history_closure_20260917.md`, `V2_container_received_date_gap_evidence_20260914.md`, `DB_Designer_Gap_Report_Container_Received_20260915.md`, `listing_status_audit_20260917/` (website cross-check of listed/not-listed SKUs).
- V3: `validation_v3.json` / `validate_v3.py`: container->component, component->combo, combo->marketplace, duplicate-row gate, images, listing, traffic, orders, revenue.
- V1 (historic): `validation/validation_<ts>.md` and `fetch_summary_<ts>.json` per run until 2026-09-11, plus `FINAL_HANDOVER_VALIDATION_20260727.md`.
- Previously reported V1 defects (memory note `scwts-final-validation-defects-20260727`, 3 bugs + 2 weak checks in `build_new_scope.py`) were never fixed, and the file no longer exists in the repo, so they are moot unless V1 is restored.
- Not re-run by this handover: no builds, publishes or DB queries were executed while writing it.

## 10. Known Issues / Dependencies

1. V1 cron broken since 2026-09-15 (missing `dashboard-v1-sql/build_new_scope.py`); hub V1 page frozen at 2026-09-11. Decide: remove the cron line, or restore the deleted folders from git and port V1 to LEDSone.
2. Hard-coded fallback database password (old reference DB, user `temp_user`) in tracked files: `dashboard-v2-sql/build_v2.py`, `dashboard-v3-sql/build_v3.py`, `dashboard-v3-sql/validate_v3.py`, `dashboard_refresh.py`, `scripts/refresh_and_publish*.sh` (3 files); also in git history. `PG*` variables are not in `.env`, so the fallback is what cron actually uses; removing it before adding `PG*` to `.env` would break the cron. Follow-up: add `PG*` to `.env`, verify, remove fallbacks, rotate the password with the DB owner.
3. Old reference DB runs out of connection slots around 11:00 (failures 2026-09-15, 16, 17). The retry is a mitigation. The old DB is also being dismantled (V3 spec: `inv_products`, `inv_product_combo`, returns, `supplier.*` emptied or dropped on 2026-07-31); V3 still reads its listing/order/traffic tables, so V3 will break if those are removed. Migration to LEDSone for V3 is not done.
4. V3 data is partly static: `sheet_containers.json` (Container 11-16 only; tab 17 empty) and `ledsone_products.json` (31 Jul) are not refreshed by cron, so new containers or SKUs need `read_sheet.py` plus a re-extraction of LEDSone products. Soft FAILs in the last V3 run: component created dates 867/868, combo created dates 584/754, PCRMFF missing from LEDSone, sheet images missing for PCRMFF and SPPGUK3PGD, no customer-review table. Note Average Feedback IS available in LEDSone (`customer_service.ebay_orders_customer_feedbacks`, eBay only) but is not wired in.
5. V2 soft FAIL: "Average Feedback" renders "No Reviews" for the same reason. Component supply gaps (about 270 components have no PO or supply record), SKU re-codes without a `product_mapping` row, warehouse id 33 missing (SKILL.md section 8).
6. Image viewer feature (about 63 lines, not committed anywhere) preserved outside the repo at `/home/led-247/scwts_preserved_work/image_viewer_20260918/` (patch + copies); decision pending with Varman.
7. The V2 page build requires `dashboard-v1/index.html` (CSS source) - do not delete V1's HTML.
8. Cron needs the PC on; no catch-up mechanism. Node 'pg' module is installed under `dashboard-v2-update/node_modules` and `dashboard-v3-update/node_modules` (git-ignored; `npm install pg` if missing).
9. Unapproved open item: `fc.status='completed'` treated as received (~42 false received dates).
External dependencies: LEDSone DB (owner/DB team), old order_management_copy DB (Varman AIOS hub table + deleted flag), Varman AIOS hub (Vercel), manager's container Google Sheet, Google Chrome/playwright for UI checks (optional).

## 11. Backup Person / Owner

- Backup developer: Not documented.
- Requester / reviewer: Varmen (named in daily logs and the skill's "Task Assigned By").
- Data owners documented in the project memory/logs: Tamilchelvan (purchasing backend, supplier/PO/CBM data), Mani (validator for that gap); database team for the old DB connection limits and for LEDSone access; "DB Designer" gap report for container received dates.
- Owner of the `sarujanan` hub rows and the project `.env`: the departing developer; transfer or re-key before leaving (the hub rows are keyed by `member_name = 'sarujanan'`; a different member name would create new pages and leave the old ones stale).

## 12. Troubleshooting

| Symptom | Check / fix |
|---|---|
| `too many connections for role` / `remaining connection slots are reserved` | Temporary capacity refusal: retry; the V2 script does it automatically (3 attempts) |
| V2 build "LEDSone credentials missing" | `.env` not loaded: `set -a && . ./.env && set +a` |
| `make_html.py` fails | `dashboard-v1/index.html` missing: `git checkout -- dashboard-v1/index.html` |
| V1 log: `can't open file .../dashboard-v1-sql/build_new_scope.py` | Expected (see issue 1) |
| `Cannot find module 'pg'` at publish | `cd dashboard-v2-update && npm install pg` (same for v3) |
| Hub page stale | Read last lines of `logs/automation_v2.log` / `automation_v3.log`: look for `[FATAL]`, `stage 3 publish: OK`; check the PC was on at 11:00/16:00 and the `flock` lock (`logs/.v2.lock`, `.v3.lock`) is not held |
| V3 `container mapping ... missing or empty` | `python3 dashboard-v3-sql/read_sheet.py` |
| A count differs from expected targets | Stop and report, never adjust the target (SKILL.md rule); see `validation_v2.json` |
| V3 shows blank created dates / PCRMFF missing | Refresh `ledsone_products.json` from LEDSone `inventory.products` and rebuild |

## 13. Final Handover Notes

- Treat V2 as the main product and V3 as the container view; V1 is legacy. Start with `.claude/skills/dashboard-v2-daily/SKILL.md` (safety rules: DB read-only, publish only when told, no credentials in files, no business-rule changes without approval).
- Do not rely on `AUTOMATION.md`, `documentation/`, `workflows/` for V2/V3; they pre-date them.
- First actions for the backup: (a) remove or fix the V1 cron entry, (b) move the old-DB credentials into `.env` and remove the hard-coded fallback, (c) confirm the PC is on for 11:00 / 16:00 runs or move the jobs to an always-on host, (d) decide on the image viewer and the V3 LEDSone migration.
- Existing handover status: the `handover/` folder was empty, so this file is newly created. The daily logs under `daily_works_logs/` (D01 to REQ-03-D04) are the detailed change history; the last (2026-09-18, REQ-03-D04) describes the retry-fix work.
- Secrets: none recorded here; env var names only.
