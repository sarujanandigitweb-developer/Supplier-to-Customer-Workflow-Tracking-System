# Dashboard Architecture — Supplier-to-Customer Workflow Tracking

**Title:** Dashboard Architecture
**Purpose:** Describe how the dashboard is built — layout, navigation, cards, charts, tables, filters, and user interaction — so it can be maintained and extended without re-reading all source.
**Business Question:** *"How is the dashboard structured, and how does a user move through it to trace a product's journey?"*

---

## 1. Technology & Files
A dependency-free, single-page application (SPA). No frameworks, no build step, no runtime database calls.

| File | Role |
|---|---|
| `dashboard/index.html` | Shell: sidebar (brand **TrackFlow**, nav, collapse), header, filter bar, content mount, modal root |
| `dashboard/style.css` | Theme tokens + all component styles (light/dark via `data-theme`) |
| `dashboard/script.js` | View router, renderers (KPI/funnel/chart/tables), filters, sorting, pagination, drill-down modals, CSV export |
| `dashboard/data.js` | Captured PostgreSQL snapshot (`window.DASHBOARD_DATA`), 108,341 records, captured 2026-07-21 |

## 2. Layout
- **Full-height left sidebar** (navy `#1b2a44`): brand mark, 8 nav items, Collapse toggle.
- **Right column**: sticky header (62–76px) with title, records-loaded, Reporting Period pill, Last Refresh pill, Export + Theme buttons; sticky filter bar; scrolling content area.
- **Theme**: accent blue `#2f6fed`, green `#12b886`, orange `#f08c00`, red `#e03131`; light and dark palettes via CSS variables.

## 3. Navigation
Sidebar links carry `data-view` (`dashboard`, `journey`, `combos`, `marketplace`, `sales`, `returns`, `suppliers`, `explorer`). `render(view)` swaps `#content`, sets the active link, and re-wires interactive elements. Any element with `data-view` (KPI cards, funnel nodes, "View all" buttons) also navigates.

## 4. Cards (KPI)
Six headline cards on the Dashboard: **New Components, Combo SKUs Created, Listed Combo SKUs, Non-Listed Combo SKUs, Orders, Sales**. Each card = icon badge + title (+ muted period note) + large value + subtitle, with a left+bottom accent stripe. All cards use the single theme-blue accent. Inner pages render their own KPI rows via the same `kpi()` helper.

## 5. Charts (inline SVG)
- **Sales Trend** — area/line chart (`lineChart()`) over `salesTrend` (monthly revenue), rendered as SVG with hover tooltips.
- **Marketplace Distribution** — horizontal mini-bars (`miniBars()`) coloured per channel.
- **Journey Funnel** — 8 circular nodes (Supplier → PO → Container → Component → Combo → Listed → Orders → Returns) with values and a status legend; each node is clickable and drills to its page.

## 6. Tables
Rendered by the shared `tableP(id, cols, rows, opts)`:
- **Pagination** — page controls + **Rows per page** selector (10 / 25 / 50 / 100, default **25**).
- **Sorting** — click-to-sort on **date and count columns** (first click descending, toggles ascending); active column highlighted in theme blue with ▲/▼, other sortable columns show a faint ↕.
- **Drill-down** — clickable rows open a modal tracing the record's chain (e.g. Supplier → PO → Container → Component → Combos → Markets).
- Sorting operates on a copy of the data so the snapshot order is never mutated, and row-click handlers stay correct after sorting.

## 7. Filters
Sticky filter bar: **Reporting Period** (read-only 2026-03-01 → Today), **Marketplace** (All/amazon/ebay/shopify/B&Q), **Supplier** (populated from snapshot), **Container** (populated from POs), **Status** (Listed / Not Listed / Has Combo / No Combo), **Search SKU / Component / ASIN**. Changing any filter resets pagination and re-renders the current view; Enter in search routes to Component Journey or the SKU Explorer.

## 8. User Interaction Flow
Open dashboard → scan KPIs → optionally apply filters → click a funnel stage or a KPI card to jump to its page → sort/paginate the table → click a row to open the drill-down chain → export the current dataset to CSV. Theme toggle switches light/dark; Collapse narrows the sidebar to icons.

---

| Field | Value |
|---|---|
| **Source** | `dashboard/index.html`, `dashboard/style.css`, `dashboard/script.js`, `dashboard/data.js` |
| **Evidence** | `evidence/dashboard_screenshots.md` (rendered captures 2026-07-21) |
| **Status** | ✅ COMPLETE — all 8 views implemented and rendering |
| **Owner** | Dashboard Development Team |
| **Reviewer** | Varmen |
| **Next Step** | Add impressions/clicks panels to Sales once the snapshot includes traffic/ppc |
| **Pass/Fail Rule** | PASS when every view renders from `DASHBOARD_DATA` with working filters, sort, pagination, and drill-downs |
| **Known Limitations** | Static snapshot (no live refresh in-page); Sales page shows a note where impressions/clicks are absent |
