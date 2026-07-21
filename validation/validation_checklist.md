# Validation Checklist — Dashboard Sections

**Title:** Validation Checklist
**Purpose:** Provide a per-section PASS/FAIL validation of the dashboard against live PostgreSQL, with the evidence for each verdict.
**Business Question:** *"Is every dashboard section backed by real, verified data — and where it is not, is that explicitly disclosed?"*

---

## Section Checklist

| # | Dashboard Section | Validation | Status | Evidence |
|---|---|---|---|---|
| 1 | **Dashboard — KPI cards** | 6 cards resolve to live values (349 / 6,274 / 16,015 / 8,596 / 97,050 / £2,304,870) | ✅ PASS | `data.js` KPI block; `evidence/data_validation_results.md` |
| 2 | **Journey Funnel** | 8 stages map to real counts (Supplier 47 … Orders 97,050) | ✅ PASS | `data.js` `funnel`; `postgres_data_mapping.md` |
| 3 | **Sales Trend chart** | Monthly revenue from `order_transaction` | ✅ PASS | `data.js` `salesTrend` |
| 4 | **Marketplace Distribution** | Listings/combos per channel | ✅ PASS | `data.js` `marketplaceDist` |
| 5 | **Component Journey** | 349 new components with supplier→PO→container→market | ✅ PASS | `data.js` `componentJourney` (349) |
| 6 | **Combo Creation** | 6,274 combos; parent components; orders/sales/returns | ✅ PASS | `data.js` `topCombos`, `comboStats` |
| 7 | **Marketplace Status** | Listed vs non-listed; 4 channels | ✅ PASS | `data.js` `marketplaceSample`; `listing_data` |
| 8 | **Sales Performance** | Orders/revenue/units/AOV + top SKUs | ✅ PASS | `data.js` KPI + `topSKUs` |
| 9 | **Sales — Impressions/Clicks panel** | Traffic/PPC aggregate | ⚠️ FAIL (deferred) | Not in snapshot; explicit note shown — no placeholder. `traffic_data`/`ppc_performance` exist in DB |
| 10 | **Returns** | 4,569 return lines by channel | ✅ PASS | `data.js` `returns` |
| 11 | **Supplier & Container** | 47 suppliers, 250 POs, 24 containers | ✅ PASS | `data.js` + `supplier.*` |
| 12 | **Supplier & Container — Warehouse Receive Date** | Physical receive-date field | ❌ FAIL (NOT FOUND) | No column in DB; note shown; gap `GAP-PURCH-CBM-2026-06-09-01` |
| 13 | **SKU Explorer** | Search across component/combo/SKU/ASIN/supplier/PO | ✅ PASS | `runExplorer()` over snapshot arrays |
| 14 | **Filters** | Marketplace/Supplier/Container/Status/Search | ✅ PASS | `filterJourney/filterMarket/filterPO` |
| 15 | **Tables — sort & pagination** | Date/count sort; rows per page 10/25/50/100 | ✅ PASS | `tableP()`; `evidence/dashboard_screenshots.md` |

## Summary
- **PASS:** 13 sections.
- **FAIL (disclosed):** 2 — Impressions/Clicks panel (deferred; data exists but not in snapshot) and Warehouse Receive Date (NOT FOUND in DB).
- **No section renders a fabricated or placeholder value.**

---

| Field | Value |
|---|---|
| **Source** | `dashboard/data.js`, `dashboard/script.js`; live `public.*`/`supplier.*` |
| **Evidence** | `evidence/data_validation_results.md`, `evidence/postgres_discovery_evidence.md` |
| **Status** | ✅ 13 PASS / 2 disclosed FAIL |
| **Owner** | Dashboard Development Team |
| **Reviewer** | Varmen; receive-date → Tamilchelvan |
| **Next Step** | Convert the 2 FAIL items to PASS after snapshot refresh (traffic/ppc) and backend replication (receive date) |
| **Pass/Fail Rule** | A section PASSES only when its values come from a verified source; UNAVAILABLE data must be disclosed, never placeheld |
| **Known Limitations** | Two sections depend on data not in the current snapshot / not in the DB |
