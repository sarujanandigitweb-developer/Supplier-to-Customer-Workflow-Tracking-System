# Prompt — Dashboard Validation

**Title:** Claude Validation Prompt
**Purpose:** Store the prompt used to validate the dashboard's values against live PostgreSQL.
**Business Question:** *"What instruction confirmed the dashboard values are real and evidenced?"*

---

## Prompt (as used)

> Validate the Supplier-to-Customer Workflow Tracking Dashboard against live PostgreSQL for the reporting period **2026-03-01 → CURRENT_DATE**.
> - For every dashboard section, confirm the rendered value comes from a verified source table and record a **PASS/FAIL** with evidence.
> - Confirm record counts (components, combos, suppliers, POs, containers, orders, sales, returns).
> - Explicitly flag any value that is **NOT FOUND** or not in the snapshot — never accept a placeholder.
> - Produce a validation checklist and a data-quality report.

## Validation Result
- **13 PASS**, **2 disclosed FAIL** (Impressions/Clicks not in snapshot; Warehouse Receive Date NOT FOUND).
- No fabricated values found.
- Artifacts: `validation/validation_checklist.md`, `validation/data_quality_report.md`, `evidence/data_validation_results.md`, `sql/validation_queries.sql`.

---

| Field | Value |
|---|---|
| **Source** | Session prompt (2026-07-21) |
| **Evidence** | `validation/validation_checklist.md`; `evidence/data_validation_results.md` |
| **Status** | ✅ Executed — validation complete |
| **Owner** | Dashboard Development Team |
| **Reviewer** | Varmen; receive-date → Tamilchelvan |
| **Next Step** | Re-validate after snapshot refresh (traffic/ppc) and backend replication |
| **Pass/Fail Rule** | PASS when every section is verified against source or disclosed as unavailable |
| **Known Limitations** | Validation is snapshot-relative; live "Today" values drift with time |
