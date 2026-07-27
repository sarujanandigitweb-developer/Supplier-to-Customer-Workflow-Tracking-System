# Claude Code Prompt — Save SCWTS 2026-07-27 daily progress to PostgreSQL (via MCP)

Copy everything in the block below into Claude Code and run it.

---

Use the Claude MCP PostgreSQL tool (`mcp__claude_ai_postgres__execute_sql`) to persist
today's SCWTS daily progress record into the `daily_task` schema.

Schema: `daily_task`
Table:  `daily_task.tbl_scwts_sarujanan`

Do exactly this, in order:

1. **Ensure the table exists, then insert.** Read the idempotent ingest script
   `daily_works_logs/2026-07-27__sarujanan__scwts_ingest.sql` and execute its full
   contents via `mcp__claude_ai_postgres__execute_sql`. The script:
   - runs `CREATE SCHEMA IF NOT EXISTS daily_task;`
   - runs `CREATE TABLE IF NOT EXISTS daily_task.tbl_scwts_sarujanan (...)` — 25 activity
     columns plus `created_at` / `updated_at`, primary key `(project_code, activity_id)`,
   - inserts today's **11** activity rows (`project_code='scwts'`, `activity_id`
     `D04-A01 … D04-A11`) using
     `INSERT ... ON CONFLICT (project_code, activity_id) DO UPDATE SET ..., updated_at=now();`

   So: **if the table does not exist it is created first, then the rows are inserted;
   if it already exists the rows are inserted/updated into it.** It is safe to re-run
   (idempotent — no duplicates).

2. **Confirm the insert with a SELECT before closing:**
   ```sql
   SELECT activity_id, activity_type, status, priority, activity_title
   FROM daily_task.tbl_scwts_sarujanan
   WHERE project_code = 'scwts' AND activity_date = '2026-07-27'
   ORDER BY activity_id;
   ```
   Expect **11 rows** returned: `D04-A01` through `D04-A11`.

3. Also report the total row count for the project and then stop:
   ```sql
   SELECT count(*) AS scwts_total FROM daily_task.tbl_scwts_sarujanan WHERE project_code = 'scwts';
   ```
   (Expect 8 rows from D01 + 9 from D02 + 12 from D03 + 11 from D04 = **40** if all
   four days are loaded.)

Constraints: do not modify or delete any pre-existing rows; do not drop or alter
existing columns; only create-if-not-exists and upsert today's records.

---

## What today's 11 records cover

| activity_id | Type | Title |
|---|---|---|
| D04-A01 | investigation | Validate inv_product_combo mapping semantics and correct the new-SKU scope |
| D04-A02 | bugfix | Fix pack-SKU descriptions misresolved through the combo mapping |
| D04-A03 | bugfix | Revert unapproved Listed business-rule change |
| D04-A04 | validation | Run full 6-source join and field-level validation audit |
| D04-A05 | investigation | Verify multi-account and multi-marketplace listing_data coverage per SKU |
| D04-A06 | enhancement | Add marketplace tab list and standalone marketplace_view.sql (later reverted by manager) |
| D04-A07 | implementation | Build the daily automation pipeline and reuse the existing AIOS uploader |
| D04-A08 | validation | Independently verify the automation instead of trusting its own PASS output |
| D04-A09 | bugfix | Fix silent revenue-attachment gap and add a permanent reconciliation guard |
| D04-A10 | bugfix | Fix sticky Record ID column visually collapsing on row hover |
| D04-A11 | documentation | Document the Combo Product Name data lineage |

**Source of the records:** skill file
`daily_works_logs/2026-07-27__sarujanan__scwts__REQ-01-D04.md`
and CSV `daily_works_logs/2026-07-27__sarujanan__scwts_daily-activities.csv`.
