# Prompt — PostgreSQL Discovery

**Title:** Claude Discovery Prompt
**Purpose:** Store the exact prompt used to run the PostgreSQL discovery so it is repeatable.
**Business Question:** *"What instruction produced the verified data discovery for this dashboard?"*

---

## Prompt (as used)

> You are only performing PostgreSQL discovery using Claude MCP.
> DO NOT search repositories. DO NOT search folders. DO NOT modify any files. DO NOT create SQL. DO NOT implement anything.
>
> **Objective:** Find the PostgreSQL data required to build the Supplier-to-Customer Workflow Tracking Dashboard.
>
> Identify: (1) New Components, (2) New Combo SKUs, (3) Component → Combo relationship, (4) Supplier, (5) Purchase Order, (6) Container Number, (7) Warehouse Receive Date, (8) Marketplace Listing Status, (9) Listing Date, (10) Impressions, (11) Clicks, (12) Orders, (13) Sales, (14) Returns.
>
> For every dataset provide: Schema, Table, Columns, Primary Key, Join Keys, Relationship, Example row count, Whether it is usable.
>
> Output format: `| Requirement | Schema | Table | Columns | Join Key | Evidence | Status |`
> If multiple tables exist, identify the recommended source. If any requirement cannot be found, clearly state **NOT FOUND**. Do not guess. Stop after discovery.
>
> Then: perform a deep analysis of all databases and tables with the help of the SKILL folder. Discover everything thoroughly and identify what data is available and what data is missing.

## Execution Notes
- Tools used: `mcp__claude_ai_postgres__list_schemas`, `list_objects`, `list_table_definitions`, `get_table_definition`, `execute_sql`, `list_skills`, `get_skill`.
- Result: **13 usable** requirements + **1 NOT FOUND** (Warehouse Receive Date), captured 2026-07-21.

---

| Field | Value |
|---|---|
| **Source** | Session prompt (2026-07-21) |
| **Evidence** | `evidence/postgres_discovery_evidence.md`; `sql/discovery_queries.sql` |
| **Status** | ✅ Executed — discovery complete |
| **Owner** | Dashboard Development Team |
| **Reviewer** | Varmen |
| **Next Step** | Re-run after purchasing-backend replication |
| **Pass/Fail Rule** | PASS when the prompt yields a table+evidence per requirement with NOT FOUND where applicable |
| **Known Limitations** | Discovery is read-only; results are connection-dependent for `supplier.*` |
