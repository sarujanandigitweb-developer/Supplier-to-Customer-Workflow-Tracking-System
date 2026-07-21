# Prompt — Dashboard Implementation

**Title:** Claude Dashboard Prompt
**Purpose:** Store the prompt(s) that drove the dashboard build and refinement.
**Business Question:** *"What instruction produced the dashboard implementation and its professional styling?"*

---

## Prompt (as used)

> Create the **dashboard** folder with `index.html`, `style.css`, `script.js` (and a generated `data.js` snapshot). Build the Supplier-to-Customer Workflow Tracking Dashboard from the verified PostgreSQL discovery. Use only verified data — no placeholder values; disclose any missing field in the UI.
>
> Then improve the dashboard with a more professional, modern design while keeping the existing theme (navy sidebar, light content, blue accent):
> - Full-height sidebar with brand + collapse; taller header with Reporting Period / Last Refresh pills.
> - **6 KPI cards** (icon + title + value + subtitle), compact height, single theme-blue accent with a left+bottom stripe.
> - Journey funnel as circular nodes; sales-trend chart; marketplace distribution bars.
> - Tables with **rows-per-page** (10/25/50/100, default 25) and **click-to-sort** on date and count columns.
> - Keep all functionality (filters, drill-downs, CSV export, light/dark theme).

## Implementation Result
- Files: `dashboard/index.html`, `style.css`, `script.js`, `data.js`.
- Brand: **TrackFlow**. 8 views. Snapshot: 108,341 records (2026-07-21).
- Constraints honoured: no PostgreSQL modification; no new business logic; gaps disclosed (Warehouse Receive Date; impressions/clicks).

---

| Field | Value |
|---|---|
| **Source** | Session prompts (2026-07-21) |
| **Evidence** | `documentation/dashboard_architecture.md`; `evidence/dashboard_screenshots.md` |
| **Status** | ✅ Executed — dashboard complete |
| **Owner** | Dashboard Development Team |
| **Reviewer** | Varmen |
| **Next Step** | Re-run to add impressions/clicks panels after snapshot refresh |
| **Pass/Fail Rule** | PASS when the dashboard renders all verified data with the specified UI and no placeholder values |
| **Known Limitations** | Static snapshot; two data areas disclosed as unavailable |
