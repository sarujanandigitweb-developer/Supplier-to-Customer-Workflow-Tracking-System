# Claude Code Prompt — Save SCWTS REQ-02-D01 daily progress to PostgreSQL (via MCP)

> **Why this file exists:** the ingest could not be run at generation time — every
> PostgreSQL MCP connector was disconnected, and the project credential
> (`temp_user`) is **denied on the `daily_task` schema**
> (`permission denied for schema daily_task`). The schema is only reachable via
> the broad MCP role. Run the block below once a PostgreSQL MCP connector is back.

Copy everything in the block below into Claude Code and run it.

---

Use the Claude MCP PostgreSQL tool (`mcp__claude_ai_postgres__execute_sql`, or
whichever PostgreSQL connector is currently connected) to persist the SCWTS
REQ-02-D01 progress record into the `daily_task` schema.

Schema: `daily_task`
Table:  `daily_task.tbl_scwts_sarujanan`

Do exactly this, in order:

1. **Ensure the table exists, then insert.** Read the idempotent ingest script
   `daily_works_logs/2026-07-31__sarujanan__scwts_ingest.sql` and execute its full
   contents. The script:
   - runs `CREATE SCHEMA IF NOT EXISTS daily_task;`
   - runs `CREATE TABLE IF NOT EXISTS daily_task.tbl_scwts_sarujanan (...)` — 25
     activity columns plus `created_at` / `updated_at`, primary key
     `(project_code, activity_id)`
   - inserts **10** activity rows (`project_code='scwts'`, `requirement_id='REQ-02'`,
     `deliverable_id='D01'`, `activity_id` `D01-A01 … D01-A10`) using
     `INSERT ... ON CONFLICT (project_code, activity_id) DO UPDATE SET ..., updated_at=now();`

   So: **if the table does not exist it is created first, then the rows are
   inserted; if it already exists the rows are inserted/updated into it.** Safe to
   re-run — idempotent, no duplicates.

2. **Confirm the insert with a SELECT before closing:**
   ```sql
   SELECT activity_id, activity_date, activity_type, priority, activity_title
   FROM daily_task.tbl_scwts_sarujanan
   WHERE project_code = 'scwts' AND requirement_id = 'REQ-02' AND deliverable_id = 'D01'
   ORDER BY activity_id;
   ```
   Expect **10 rows**: `D01-A01` through `D01-A10`.

3. **Report the project total, then stop:**
   ```sql
   SELECT count(*) AS scwts_total FROM daily_task.tbl_scwts_sarujanan WHERE project_code = 'scwts';
   ```
   (Previously loaded: 8 from D01 + 9 from D02 + 12 from D03 + 11 from D04, plus
   whatever REQ-01-D05 added. This adds **10** more.)

Constraints: do not modify or delete any pre-existing rows; do not drop or alter
existing columns; only create-if-not-exists and upsert these records.

---

## What these 10 records cover

| activity_id | Date | Type | Title |
|---|---|---|---|
| D01-A01 | 2026-07-31 | implementation | Parse the manager's container workbook into a Container → Component SKU map |
| D01-A02 | 2026-07-31 | investigation | Discover the source database being dismantled mid-session |
| D01-A03 | 2026-07-31 | investigation | Answer the container received-date question definitively |
| D01-A04 | 2026-07-31 | implementation | Build Dashboard V3 as an independent container-first deliverable |
| D01-A05 | 2026-07-31 | bugfix | Swap the inv_products source to LEDs One `inventory.products` |
| D01-A06 | 2026-07-31 | enhancement | Apply the requested V3 UI changes only |
| D01-A07 | 2026-07-31 | enhancement | Add Dashboard V2's detail drawer to V3 |
| D01-A08 | 2026-08-03 | bugfix | Fix Component Images being taken from the marketplace instead of the Google Sheet |
| D01-A09 | 2026-08-03 | validation | Validate all 18 dashboard fields independently against their sources |
| D01-A10 | 2026-08-03 | deployment | Publish V3 to the Varman AIOS hub and rename the page slug |

**Source of the records:** skill file
`daily_works_logs/2026-07-31__sarujanan__scwts__REQ-02-D01.md`
and CSV `daily_works_logs/2026-07-31__sarujanan__scwts_daily-activities.csv`
(10 rows × 25 columns, parse-validated with `csv.DictReader`).

**Key evidence embedded in the records:** 6 containers / 209 components / 295
combos / 781 rows · 95 component images corrected · 18 fields validated with
**0 mismatches** · hub id 125 `container-to-customer-workflow-tracking`.
