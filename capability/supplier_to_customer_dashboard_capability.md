# Capability — Supplier-to-Customer Dashboard

**Title:** Supplier-to-Customer Dashboard Capability
**Purpose:** Define this deliverable as a reusable capability — its purpose, inputs, execution, validation, evidence, reuse, and limitations.
**Business Question:** *"Can this dashboard-building capability be reused to turn verified PostgreSQL discovery into an evidenced, system-driven tracking dashboard?"*

---

## Purpose
Turn a verified PostgreSQL discovery into a single-page, evidenced workflow-tracking dashboard that follows a product from supplier to customer — with no manual spreadsheet tracking and no fabricated values.

## Inputs
- **Verified discovery** — schema/table/key/relationship map for all required data points (`documentation/postgres_data_mapping.md`).
- **PostgreSQL access** — read-only via `claude_ai_postgres` MCP (schemas: `public`, `supplier`, `staging_ai`).
- **Reporting window** — 2026-03-01 → CURRENT_DATE.
- **Snapshot** — `dashboard/data.js` (108,341 records, captured 2026-07-21).

## Execution
1. Discover and validate sources (13 usable, 1 NOT FOUND).
2. Capture a period-scoped snapshot into `data.js`.
3. Render 8 views (`index.html` + `style.css` + `script.js`): KPIs, funnel, charts, tables (sortable/paginated), drill-downs, CSV export.
4. Disclose gaps in-UI (Warehouse Receive Date; impressions/clicks) — never placehold.

## Validation
- Per-section PASS/FAIL: `validation/validation_checklist.md` (13 PASS / 2 disclosed FAIL).
- Live values vs snapshot: `evidence/data_validation_results.md`.
- Visual proof: `evidence/dashboard_screenshots.md`.

## Evidence
- `evidence/postgres_discovery_evidence.md` — row counts + gap register.
- `sql/discovery_queries.sql`, `sql/dashboard_queries.sql`, `sql/validation_queries.sql`.

## Reuse
Reusable for any supplier→customer catalogue where components combine into combos and list across marketplaces. To re-apply: swap the discovery mapping, re-point the snapshot generator at the target schemas, keep the same UI shell. The gap-disclosure pattern (`purchasing_intelligence_source_gaps`) is a reusable register for any missing source.

## Limitations
- Renders a **snapshot**, not live DB (refresh required for currency).
- **Warehouse Receive Date** unavailable until the purchasing backend is replicated.
- **Impressions/Clicks** deferred (not in current snapshot).
- Supplier-schema availability is **connection-dependent** — re-verify live before each build.

---

| Field | Value |
|---|---|
| **Source** | Dashboard implementation + verified discovery (2026-07-21) |
| **Evidence** | `evidence/*`, `validation/*`, `sql/*` |
| **Status** | ✅ REUSABLE — proven on this project |
| **Owner** | Dashboard Development Team |
| **Reviewer** | Varmen; source gaps → Tamilchelvan |
| **Next Step** | Parameterise the snapshot generator so the capability runs against new schemas |
| **Pass/Fail Rule** | PASS when the capability reproduces an evidenced dashboard with all gaps disclosed and no placeholder data |
| **Known Limitations** | Snapshot-based; receive-date gap; traffic/ppc deferred; connection-dependent supplier data |
