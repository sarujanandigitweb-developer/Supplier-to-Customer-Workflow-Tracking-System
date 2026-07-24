# SKILL FILE — 2026-07-23 — SCWTS — REQ-01-D02

Supplier's Basket → Customer's Home: automated daily refresh, MCP-sourced master
tracking view, and gap correction of the modified snapshot.

---

## METADATA BLOCK

```yaml
date: 2026-07-23
developer: Sarujanan
project: Supplier-to-Customer Workflow Tracking System
project_code: scwts
phase: Development - phase 02
requirement_id: REQ-01
deliverable_id: D02
status: Completed
evidence_location: /home/led-247/Supplier-to-Customer-Workflow-Tracking-System/
  - dashboard_refresh.py
  - dashboard-v1/supplier_basket_to_customer_home.html
  - dashboard-v1-sql/ (01_components … 07_returns, _common.sql)
  - validation/validation_report_20260723_145959.md (PASS)
  - data_backup/data_20260723_150013.js
  - logs/refresh.log
  - daily_works_logs/2026-07-23__sarujanan__scwts_daily-activities.csv
blos_keys_used:
  - reporting_period_start
  - refresh_drop_guard
  - refresh_inflate_guard
  - refresh_schedule_time
  - listed_definition
  - marketplace_filter
  - date_range_filter
hardcoded_thresholds:
  - reporting_window_start = 2026-01-01
  - refresh_drop_guard = 0.50           # min new/current dataset ratio to publish
  - refresh_inflate_guard = 3.0         # max new/current dataset ratio to publish
  - refresh_schedule_time = 10:00 daily
  - traffic_organic_expected = 120.77M  # regression anchor after dedup
  - clip_column_width = 240px
  - default_rows_per_page = 100
three_am_standard: TRUE
llm_queryable: TRUE
company_knowledge_candidate: TRUE
domain: Ecommerce Operations - Supplier to Customer Workflow
User: Varmen
Benefit status: Pass
```

---

## 1. SYSTEM STATE (before today)

- The dashboard ran on a **raw-data-first, offline** model: PostgreSQL → SQL export → a single embedded `dashboard/data.js` → offline HTML → client-side JS filtering (built 2026-07-21, REQ-01-D01).
- `data.js` was a **hand/refreshed point-in-time snapshot** with **no automated refresh**; it had already been modified since export and had drifted from the database.
- Two disconnected PostgreSQL access paths existed: the **broad Claude MCP role** (reaches `supplier.*`) and a **`temp_user` refresh role** (public schema only) — a distinction not yet accounted for in any pipeline.
- Traffic export used a `refids` CTE that was `DISTINCT (ref_id, channel, market_place)` but joined on `ref_id` only.
- No single master table existed that showed the full lifecycle (component → container → combo → listing → traffic → orders → returns) in one view.

## 2. WHAT CHANGED TODAY

- **Automated daily refresh (`dashboard_refresh.py`).** An 8-step, 10:00-cron pipeline: connect → export all 8 datasets → recompute KPIs from raw rows → validate the live export against the current `data.js` → write a timestamped validation report → back up the current `data.js` → replace it **only on PASS** → append `logs/refresh.log`. On any failure the previous dashboard is kept untouched.
- **Degraded refresh mode.** The pipeline detects at runtime whether the connected role can read `supplier`. If not, it seeds the new-component lineage from the SKUs already in `data.js`, refreshes the 6 public datasets live, and carries `components` + `purchaseOrders` forward; it auto-upgrades to FULL mode with a supplier-capable role.
- **Traffic query corrected.** Replaced the fan-out `refids` with `SELECT ref_id, MAX(which_channel_name) … GROUP BY ref_id` (one row per `ref_id`) and **removed** a later, incorrect `created_at >= 2026-01-01` gate on `refids`. The window is applied on the **traffic date** only.
- **New one-page master tracking view** (`dashboard-v1/supplier_basket_to_customer_home.html`) — a self-contained HTML file reusing the exact dashboard theme, at **one Combo SKU × one platform** grain (activity-union), with 4 calculated columns computed live in JS.
- **Re-sourced dashboard-v1 fresh from PostgreSQL via MCP** (not from the gappy `data.js`), authoring 7 canonical queries in `dashboard-v1-sql/`.
- **UX** (table format unchanged): removed sidebar; `// @ts-nocheck` to clear editor red-lines; frozen table header; fixed shell (app bar, filters, KPI cards, pagination stay, only the table body scrolls); taller header bar; fixed-width clipped Name/Description columns with hover/click overlay tooltip; reduced pagination padding + "All" page size; row-click detail drawer grouping all 30 columns into 8 lifecycle sections.

## 3. POSTGRESQL / MCP FINDING

- **`temp_user` (refresh role) has NO `supplier` USAGE** (`has_schema_privilege(current_user,'supplier','USAGE') = false`). Usable schemas: `analytics, audit, public, staging_ai, tech_team_outputs, varman_aios`. The `supplier` schema is reachable **only via the broad MCP role**.
- **Gap-field source tables** (that the snapshot lacked): quantity received = `supplier.order_items.pcs` (total units = `ctns × ctn_pcs`); container name = `supplier.orders.container_id::text = supplier.containers.id::text → containers.name` (covers 239/250 orders); supplier = `supplier.suppliers.name`; component receive date = earliest `supplier.order_items.created_at`.
- **No true "container arrival date" column** exists; best available proxy is `orders.expected_completion_date → finished_date → confirmed_date`. `status_arrived` is a flag with no date.
- **Combo product name** = `MAX(listing_data.title)` per combo SKU (only for listed combos). **No operational combo-master** covers the set: `staging_ai.ipc_llm_combo_summary` holds only 4 rows. **Combo Qty Created is untracked** anywhere in the DB.
- **Combo SKUs are literally '+'-joined component SKUs** (e.g. `CRSF100BM+LHNSE27BM`); a combo qualifies when at least one part is a new component.
- **MCP large-result behaviour:** results over the token limit are **auto-saved to a `tool-results/*.txt` file** in `{result:[{text:"<python-repr>"}]}` form; parse via `json.loads → text → ast.literal_eval → [0]['json_agg']`.

## 4. GAP FOUND

- **Modified snapshot under-reported reality.** In the drifted `data.js`, container and quantity were **near-empty**, and listings had been narrowed to `is_child=1 AND created_at>=2026-01-01`, hiding ~4,400 older-but-still-live listings. This manufactured **4,134 "not listed"** rows when the true count is **1,199** (3,697 of 4,389 combos are actually listed).
- **Refresh credentials cannot serve the whole dashboard.** `temp_user` cannot compute the new-component set (needs `supplier.order_items`), so a naive psycopg2 refresh of the supplier half is impossible with the provided role.
- **"Container Arrival Date" has no first-class field** — requirement assumes a date the DB does not store; a proxy is used and must be governed.
- **"Combo Qty Created" has no source** — the requirement column cannot be populated; shown as "—".
- **Row-count guards alone are insufficient** — value-level corruption (impression inflation at stable row counts) needs KPI reconciliation too.

## 5. VALIDATION RULE ADDED OR CHANGED

- **VR-REFRESH-01 (publish gate):**
  `IF` connection fails `OR` any critical dataset is empty `OR` duplicate/fan-out rows exist `OR` any KPI ≤ 0 `OR` any dataset row count < 0.50× or > 3.00× the current published count
  `THEN` mark the run FAILED, keep the existing `data.js`, and write a FAIL report.
  `ELSE` back up `data.js` and publish.
- **VR-TRAFFIC-01 (no fan-out / window on event date):**
  `refids` must be **one row per `ref_id`** (`GROUP BY ref_id`) and must **NOT** be gated on listing `created_at`; the reporting window is applied on `traffic_data.date` / `ppc_performance.date`. Regression anchor: organic impressions ≈ **120.77M**.
- **VR-LISTED-01 (listed definition):**
  A combo is **Listed** on a platform `IF` a live `listing_data` row exists (`is_deleted=0 AND is_ended=0`) for that combo+platform, **regardless of `created_at`**; else **Not Listed** with a red `GAP - Not Listed` flag.
- **VR-ROWGRAIN-01 (no dropped sales):**
  Master-table rows = the **union** of (combo, platform) with a live listing OR completed orders OR returns; revenue must reconcile to the source dashboard (GBP 161,617.86).

## 6. FAILURE MODE OR EDGE CASE

- **Silent scope collapse:** gating traffic `refids` on `created_at` dropped 6,394/7,630 listings and 86% of impressions with **no error** — only the change-guard catches it. (Observed: traffic 7,567 → 1,082 rows, 0.14×, correctly blocked publish.)
- **Empty-snapshot degraded start:** degraded mode aborts (does not write) if `data.js` has no components to seed the lineage.
- **Wrong-role refresh:** running the pipeline with `temp_user` yields a degraded (not full) refresh; components/POs are carried forward, not live.
- **Default date filter hiding data:** keying the date filter on **listing date** hid rows for combos listed years ago; it must key on **component received date** (lifecycle start, always ≥ window start).
- **"All" pagination on large sets:** rendering ~7,000 rows unpaginated is heavy; filter first.
- **Credential exposure risk:** `dashboard_refresh.py` contains a DB password supplied by the user — flagged for BLOS/secret governance (see below).

## 7. DECISIONS MADE TODAY

- **Never overwrite the live artifact on failure** — validation-gated publish with pre-write backup.
- **Capability-detect the DB role and degrade gracefully** rather than hard-failing when `supplier` is unreachable.
- **Treat a modified snapshot as untrusted** and **re-source from the database of record via MCP**; resolve every gap field to its true source table.
- **Activity-union row grain** (not listing-only) so no order is dropped; a "Not Listed" row that still has orders is the intended *reconcile* signal.
- **Window belongs on the event date**, never on a linked entity's creation date.
- **Do not change the table format** for usability — add overlay tooltip + detail drawer instead of expanding cells.
- **Combo Qty Created left blank** ("—") rather than fabricated, since no source exists.

## 8. COMPANY KNOWLEDGE EXTRACT (reusable)

- **Validation-gated snapshot refresh** is a reusable pattern for any offline/embedded reporting artifact: connect → export raw → recompute KPIs → validate vs current → report → backup → publish only on PASS → log. Reusable across inventory, finance, logistics, marketplace dashboards.
- **Runtime capability detection + graceful degradation** (`has_schema_privilege`) lets one pipeline serve multiple DB roles and self-document the mode used.
- **Metric-through-a-bridge joins must dedup the bridge to one row per join key**; otherwise entities in >1 category fan out and inflate sums. Apply reporting windows on the **event date**.
- **Snapshots drift** — when a shared export is modified, re-fetch from the database of record; do not treat the snapshot as source of truth. Keep per-dataset **self-contained** queries so any dataset is reproducible alone.
- **Canonical "listed" definition:** any live listing (not deleted/ended) = Listed; never narrow listing visibility by `created_at`.
- **Reveal-without-reflow UX:** clip dense columns to a fixed width and surface full content via an overlay tooltip + grouped detail drawer, preserving a stable table layout.
- **MCP is the supplier-schema bridge**; large results land in `tool-results` files parsed via `json → text → literal_eval → json_agg`.

## 9. LLM STANDARD CHECK

- Terminology consistent (combo, platform, new component, qualifying combo, activity-union, fan-out, change-guard): **TRUE**
- Business rules explained (VR-REFRESH-01, VR-TRAFFIC-01, VR-LISTED-01, VR-ROWGRAIN-01): **TRUE**
- Assumptions documented (arrival-date proxy, combo-qty untracked, date filter on receive date): **TRUE**
- Edge cases documented (silent scope collapse, empty-snapshot start, wrong-role refresh): **TRUE**
- Evidence referenced (files, validation report, backups, MCP counts, revenue reconciliation): **TRUE**
- Another developer can continue independently (3 AM standard): **TRUE**
- LLM-queryable structure: **TRUE**

---

## BLOS GOVERNANCE

The following business thresholds are currently hardcoded and **must be moved to BLOS** (visible, governed, reviewable, reusable) rather than living in code:

| BLOS key (proposed) | Current hardcoded value | Where it lives now |
|---|---|---|
| reporting_period_start | 2026-01-01 | dashboard_refresh.py, dashboard-v1-sql/*.sql, page JS |
| refresh_drop_guard | 0.50 | dashboard_refresh.py |
| refresh_inflate_guard | 3.0 | dashboard_refresh.py |
| refresh_schedule_time | 10:00 daily | cron entry |
| traffic_organic_expected | ~120.77M (regression anchor) | validation reasoning |
| listed_definition | is_deleted=0 AND is_ended=0 | dashboard-v1-sql/04_listings.sql |
| default_rows_per_page | 100 | page JS |
| clip_column_width | 240px | page CSS |

**Escalation flag:** `dashboard_refresh.py` embeds a database password provided by the user. This is a **credential-in-file** condition — the connection secret must be moved to an environment variable / secret store and removed from source before this file is shared or committed.

---

## Benefit Status: PASS

Complete, gap-free, date-filterable master tracking view delivered; revenue reconciles exactly to source (GBP 161,617.86); automated refresh with fail-safe validation in place. Outstanding governance items (BLOS keys, credential relocation) recorded above.
