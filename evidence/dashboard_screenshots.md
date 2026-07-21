# Dashboard Screenshots — Evidence Register

**Title:** Dashboard Screenshots Evidence
**Purpose:** Reference the rendered dashboard captures used as visual proof that the implementation renders live-sourced values.
**Business Question:** *"Is there visual evidence that the dashboard renders the verified data as designed?"*

---

## Capture Method
Rendered headless (Google Chrome `--headless=new`) directly from `dashboard/index.html` against the `data.js` snapshot on **2026-07-21**, viewport 1500–1600px wide, light theme.

## Screenshot Register

| # | View captured | Date captured | Purpose / What it proves |
|---|---|---|---|
| 1 | Dashboard — full page | 2026-07-21 | 6 KPI cards, journey funnel, sales trend, marketplace distribution, latest components + top combos render with live values |
| 2 | Dashboard — 6 KPI cards | 2026-07-21 | Card count reduced to 6, compact height, single theme-blue accent with left+bottom stripe |
| 3 | Journey Funnel (nodes) | 2026-07-21 | Supplier 47 → PO 99 → Container 24 → Component 349 → Combo 6,274 → Listed 6,274 → Orders 97,050 → Returns rendered as circular nodes |
| 4 | Component Journey table | 2026-07-21 | 349 new components with supplier → PO → container → market lineage; pagination + rows-per-page |
| 5 | Component Journey — sorted | 2026-07-21 | Click-to-sort on Combos (desc): 486 → 202 → 142 …; active header themed blue with ▼ |
| 6 | Table footer | 2026-07-21 | "Rows per page" selector (10/25/50/100) and pager ("Page 1 / 35") working |

## Notes
- Screenshots are working artifacts generated during build/validation; they are stored outside version control (session scratchpad) and reproduced on demand from `index.html` + `data.js`.
- To regenerate: open `dashboard/index.html` in a browser, or run a headless capture per view. No data changes are required.
- Numbers in captures match the `data.js` snapshot (`totalRecordsLoaded=108,341`, captured 2026-07-21).

---

| Field | Value |
|---|---|
| **Source** | Headless render of `dashboard/index.html` + `dashboard/data.js` |
| **Evidence** | Six captures listed above (2026-07-21) |
| **Status** | ✅ COMPLETE — visual evidence captured for key views |
| **Owner** | Dashboard Development Team |
| **Reviewer** | Varmen |
| **Next Step** | Add captures of Marketplace, Sales, Returns, Supplier & Container, and dark theme for a full visual set |
| **Pass/Fail Rule** | PASS when each captured view matches the snapshot values and the documented design |
| **Known Limitations** | Captures reflect a point-in-time snapshot; not all 8 views have a stored image yet |
