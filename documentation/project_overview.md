# Project Overview — Supplier-to-Customer Workflow Tracking System

**Title:** Project Overview
**Purpose:** Give a single, authoritative summary of what the Supplier-to-Customer Workflow Tracking dashboard is, why it exists, what it covers, and its current status.
**Business Question:** *"Can we replace manual, human-time tracking with a system-driven view of a product's full journey — from a supplier's basket to a customer's home — using PostgreSQL as the source of truth?"*

---

## 1. Project Purpose
Eliminate "human time" spent on manual spreadsheet tracking and move to a **system-based visibility model** that follows the entire lifecycle of a product: from the moment a component is ordered from a supplier, through combo creation and marketplace listing, to sales, returns, and the customer.

## 2. Business Objective
- Identify the **last new components** received from suppliers and how many **Combo Products** were created from them.
- Show, for each component, its **association across all listings** and which marketplaces it is (or is not) listed on.
- Provide **real-time performance** per listed SKU/Combo from listing date to now: impressions, clicks, orders, sales, and returns.
- Guarantee **no "breaking link"** in the product's journey — every stage traceable and evidenced.

## 3. Scope
**In scope:** New components, combo SKUs, component→combo relationship, supplier, purchase order, container, marketplace listing status, orders, sales, returns, and a SKU/component/ASIN explorer — all rendered in a single-page dashboard.
**Out of scope (this release):** Warehouse Receive Date (not present in the database — see Known Limitations), live impressions/clicks aggregation (not in current snapshot), and any write-back to PostgreSQL.

## 4. Reporting Period
**2026-03-01 → CURRENT_DATE** (labelled "March 01, 2026 → Today"). Snapshot captured **2026-07-21**. Total records loaded into the dashboard snapshot: **108,341**.

## 5. Dashboard Pages
1. **Dashboard** — 6 KPI cards, journey funnel, sales trend, marketplace distribution, latest components, top combos.
2. **Component Journey** — every new component with supplier → PO → container → market lineage (349 rows).
3. **Combo Creation** — combo SKUs built from new components (6,274 created since March).
4. **Marketplace Status** — listed vs non-listed across Amazon / eBay / Shopify / B&Q.
5. **Sales Performance** — orders, revenue, units, AOV, top-selling SKUs.
6. **Returns** — return lines by channel (Amazon / eBay / Shopify).
7. **Supplier & Container** — suppliers, purchase orders, containers, arrival status.
8. **SKU Explorer** — search across component / combo / marketplace SKU / ASIN / supplier / PO.

## 6. PostgreSQL Source Systems
- **`public`** schema — components master (`components_sot_*`), listings (`listing_data`), sales (`order_transaction`), stock (`inv_final_stock`), traffic/PPC (`traffic_data`, `ppc_performance`), returns (`amazon_returns`, `ebay_returns`, `shopify_returns`, `return_by_cs_team`).
- **`supplier`** schema — suppliers, purchase orders, containers, order items (populated: 47 suppliers, 250 orders, 24 containers).
- **`staging_ai`** schema — purchasing-intelligence gap register (`purchasing_intelligence_source_gaps`) documenting the missing warehouse/CBM source.
- Access is **read-only via the `claude_ai_postgres` MCP**. The dashboard consumes a captured **snapshot** (`dashboard/data.js`); it does not query the database at runtime.

## 7. Current Project Status
**Build complete and evidenced.** 13 of 14 required data points are sourced and rendered; 1 (Warehouse Receive Date) is confirmed absent from the database. Dashboard UI implemented (`index.html`, `style.css`, `script.js`, `data.js`) with filters, sortable/paginated tables, drill-downs, CSV export, and light/dark theme.

---

| Field | Value |
|---|---|
| **Source** | `dashboard/data.js` snapshot (2026-07-21); PostgreSQL discovery via `claude_ai_postgres` MCP |
| **Evidence** | `evidence/postgres_discovery_evidence.md`, `evidence/data_validation_results.md`; snapshot meta `totalRecordsLoaded=108341` |
| **Status** | ✅ COMPLETE (13/14 data points live; 1 documented gap) |
| **Owner** | Dashboard Development Team (Supplier-to-Customer Workflow Tracking) |
| **Reviewer** | Varmen; purchasing-source gap → Tamilchelvan |
| **Next Step** | Replicate purchasing backend to expose Warehouse Receive Date; refresh snapshot to include impressions/clicks |
| **Pass/Fail Rule** | PASS when every dashboard page renders live PostgreSQL-sourced values for the reporting period with documented evidence; FAIL if any value is a placeholder or unsourced |
| **Known Limitations** | Warehouse Receive Date = NOT FOUND; impressions/clicks absent from current snapshot; dashboard reads a snapshot, not live DB |
