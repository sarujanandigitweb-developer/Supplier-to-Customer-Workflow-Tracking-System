# Duplicate Truth Assessment

**Title:** Duplicate Truth Assessment
**Purpose:** Assess whether the dashboard, its SQL, or its use of PostgreSQL duplicates existing sources of truth, and recommend how to avoid a competing "second truth".
**Business Question:** *"Does this dashboard create a duplicate or conflicting source of truth, and how do we prevent that?"*

---

## 1. Assets Assessed
| Asset | What it is | Truth role |
|---|---|---|
| **Existing dashboard** | `dashboard/*` SPA reading `data.js` snapshot | **Presentation layer** — displays, does not own data |
| **Existing SQL** | `sql/discovery_queries.sql`, `dashboard_queries.sql`, `validation_queries.sql` | **Read-only** extraction/validation queries |
| **Existing PostgreSQL** | `public.*`, `supplier.*`, `staging_ai.*` | **System of record** (source of truth) |

## 2. Duplicate Risk Analysis
| Risk area | Finding | Risk level |
|---|---|---|
| **Data ownership** | Dashboard reads a snapshot; it never writes back to PostgreSQL. No new authoritative store is created. | 🟢 Low |
| **Metric redefinition** | KPIs reuse existing definitions (Completed orders, `wrong_sku=0` listings, `'+'` combos). No new metric semantics invented. | 🟢 Low |
| **Snapshot drift** | `data.js` is a point-in-time copy (2026-07-21). If treated as live, it could diverge from PostgreSQL over time. | 🟡 Medium |
| **Combo relationship** | Derived from `'+'` SKU pattern rather than the (sparse) `child_item_products` FK. Two possible "truths" for combo membership. | 🟡 Medium |
| **Supplier/receive data** | Purchasing truth lives in a separate un-mirrored backend; dashboard must not present its own receive-date. | 🟡 Medium (mitigated — disclosed, not shown) |
| **Google Sheets legacy** | Component master migrated to `components_sot_*`; sheets must be retired as truth to avoid two masters. | 🟡 Medium |

## 3. Assessment
The dashboard is a **thin presentation layer over the existing PostgreSQL system of record** and does **not** create a competing source of truth. The only realistic duplication risks are (a) the snapshot being mistaken for live data, (b) two definitions of combo membership, and (c) legacy Google Sheets lingering as a parallel master. All are process risks, not architectural ones.

## 4. Recommendation
1. **Label the snapshot** clearly with its capture timestamp (already shown as "Last Refresh") and treat PostgreSQL as the sole authority.
2. **Pick one combo-membership truth** — prefer a populated `child_item_products` FK; keep the `'+'` parse only as a fallback and document it.
3. **Retire Google Sheets** as component master now that `components_sot_*` exists.
4. **Never render receive-date/CBM** from a guess; keep disclosing the gap until the purchasing backend is replicated (owner: Tamilchelvan).
5. **Keep all dashboard SQL read-only** — no writes to PostgreSQL.

**Verdict:** ✅ No duplicate source of truth created. Proceed; apply the mitigations above.

---

| Field | Value |
|---|---|
| **Source** | `dashboard/*`, `sql/*`, live `public.*`/`supplier.*`/`staging_ai.*` |
| **Evidence** | `documentation/postgres_data_mapping.md`; gap `GAP-PURCH-CBM-2026-06-09-01` |
| **Status** | ✅ ASSESSED — low architectural duplicate risk |
| **Owner** | Dashboard Development Team |
| **Reviewer** | Varmen; purchasing truth → Tamilchelvan |
| **Next Step** | Implement mitigations 1–3; confirm Sheets retirement |
| **Pass/Fail Rule** | PASS when PostgreSQL remains the single source of truth and the dashboard/SQL stay read-only presentation |
| **Known Limitations** | Snapshot can drift; two combo-membership definitions exist; legacy Sheets may persist |
