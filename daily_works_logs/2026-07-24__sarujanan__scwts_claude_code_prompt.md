# Claude Code Prompt — Save SCWTS 2026-07-24 daily progress to PostgreSQL (via MCP)

Copy everything in the block below into Claude Code and run it.

---

Use the Claude MCP PostgreSQL tool (`mcp__claude_ai_postgres__execute_sql`) to persist
today's SCWTS daily progress record into the `daily_task` schema.

Schema: `daily_task`
Table:  `daily_task.tbl_scwts_sarujanan`

Do exactly this, in order:

1. **Ensure the table exists, then insert.** Read the idempotent ingest script
   `daily_works_logs/2026-07-24__sarujanan__scwts_ingest.sql` and execute its full
   contents via `mcp__claude_ai_postgres__execute_sql`. The script:
   - runs `CREATE SCHEMA IF NOT EXISTS daily_task;`
   - runs `CREATE TABLE IF NOT EXISTS daily_task.tbl_scwts_sarujanan (...)` — 25 activity
     columns plus `created_at` / `updated_at`, primary key `(project_code, activity_id)`,
   - inserts today's **12** activity rows (`project_code='scwts'`, `activity_id`
     `D03-A01 … D03-A12`) using
     `INSERT ... ON CONFLICT (project_code, activity_id) DO UPDATE SET ..., updated_at=now();`

   So: **if the table does not exist it is created first, then the rows are inserted;
   if it already exists the rows are inserted/updated into it.** It is safe to re-run
   (idempotent — no duplicates).

2. **Confirm the insert with a SELECT before closing:**
   ```sql
   SELECT activity_id, activity_type, status, priority, activity_title
   FROM daily_task.tbl_scwts_sarujanan
   WHERE project_code = 'scwts' AND activity_date = '2026-07-24'
   ORDER BY activity_id;
   ```
   Expect **12 rows** returned: `D03-A01` through `D03-A12`.

3. Also report the total row count for the project and then stop:
   ```sql
   SELECT count(*) AS scwts_total FROM daily_task.tbl_scwts_sarujanan WHERE project_code = 'scwts';
   ```
   (Expect 8 rows from D01 + 9 from D02 + 12 from D03 = **29** if all three days are loaded.)

Constraints: do not modify or delete any pre-existing rows; do not drop or alter
existing columns; only create-if-not-exists and upsert today's records.

---

## What today's 12 records cover

| activity_id | Type | Title |
|---|---|---|
| D03-A01 | bugfix | Fix header dead band and KPI card overlap in master tracking shell |
| D03-A02 | bugfix | Fix accessibility: unassociated form labels in filter toolbar and pagination |
| D03-A03 | bugfix | Resolve Vercel 404 by renaming the page to index.html |
| D03-A04 | investigation | Discover and validate the true product data model (inv_products, inv_product_combo) |
| D03-A05 | bugfix | Replace SKU string-splitting with the authoritative combo-component mapping |
| D03-A06 | implementation | Implement SKU normalisation for country and channel suffixes |
| D03-A07 | bugfix | Correct listing scope: date window, is_parent, wrong_sku and empty SKUs |
| D03-A08 | bugfix | Stop presenting a forecast date as Container Arrival |
| D03-A09 | enhancement | Rebuild product detail drawer as full-height one-page view with component images |
| D03-A10 | bugfix | Fix hover tooltip overlapping the sticky Record ID column |
| D03-A11 | implementation | Publish master tracking dashboard to the Varman AIOS Hub |
| D03-A12 | implementation | Rebuild dashboard data on the NEW-product scope with full reconciliation |

**Source of the records:** skill file
`daily_works_logs/2026-07-24__sarujanan__scwts__REQ-01-D03.md`
and CSV `daily_works_logs/2026-07-24__sarujanan__scwts_daily-activities.csv`.
