# Claude Code Prompt — Save SCWTS 2026-07-23 daily progress to PostgreSQL (via MCP)

Copy everything in the block below into Claude Code and run it.

---

Use the Claude MCP PostgreSQL tool (`mcp__claude_ai_postgres__execute_sql`) to persist
today's SCWTS daily progress record into the `daily_task` schema.

Schema: `daily_task`
Table:  `daily_task.tbl_scwts_sarujanan`

Do exactly this, in order:

1. **Ensure the table exists, then insert.** Read the idempotent ingest script
   `daily_works_logs/2026-07-23__sarujanan__scwts_ingest.sql` and execute its full
   contents via `mcp__claude_ai_postgres__execute_sql`. The script:
   - runs `CREATE SCHEMA IF NOT EXISTS daily_task;`
   - runs `CREATE TABLE IF NOT EXISTS daily_task.tbl_scwts_sarujanan (...)` with
     primary key `(project_code, activity_id)`,
   - inserts today's 9 activity rows (`project_code='scwts'`, `activity_id`
     `D02-A01 … D02-A09`) using
     `INSERT ... ON CONFLICT (project_code, activity_id) DO UPDATE SET ..., updated_at=now();`
   So: **if the table does not exist it is created first, then the rows are inserted;
   if it already exists the rows are inserted/updated into it.** It is safe to re-run
   (idempotent — no duplicates).

2. **Confirm the insert with a SELECT before closing:**
   ```sql
   SELECT activity_id, activity_type, status, priority, activity_title
   FROM daily_task.tbl_scwts_sarujanan
   WHERE project_code = 'scwts' AND activity_date = '2026-07-23'
   ORDER BY activity_id;
   ```
   Expect **9 rows** returned: `D02-A01` through `D02-A09`.

3. Also report the total row count for the project and then stop:
   ```sql
   SELECT count(*) AS scwts_total FROM daily_task.tbl_scwts_sarujanan WHERE project_code = 'scwts';
   ```

Constraints: do not modify or delete any pre-existing rows; do not drop or alter
existing columns; only create-if-not-exists and upsert today's records.

---

**Source of the records:** skill file
`daily_works_logs/2026-07-23__sarujanan__scwts__REQ-01-D02.md`
and CSV `daily_works_logs/2026-07-23__sarujanan__scwts_daily-activities.csv`.
