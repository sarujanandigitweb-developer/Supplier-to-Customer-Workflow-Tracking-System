# Claude Code Prompt — Save SCWTS 2026-07-28 daily progress to PostgreSQL (via MCP)

Copy everything in the block below into Claude Code and run it.

---

Use the Claude MCP PostgreSQL tool (`mcp__claude_ai_postgres__execute_sql`) to persist
today's SCWTS daily progress record into the `daily_task` schema.

Schema: `daily_task`
Table:  `daily_task.tbl_scwts_sarujanan`

Do exactly this, in order:

1. **Ensure the table exists, then insert.** Read the idempotent ingest script
   `daily_works_logs/2026-07-28__sarujanan__scwts_ingest.sql` and execute its full
   contents via `mcp__claude_ai_postgres__execute_sql`. The script:
   - runs `CREATE SCHEMA IF NOT EXISTS daily_task;`
   - runs `CREATE TABLE IF NOT EXISTS daily_task.tbl_scwts_sarujanan (...)` — 25 activity
     columns plus `created_at` / `updated_at`, primary key `(project_code, activity_id)`,
   - inserts today's **13** activity rows (`project_code='scwts'`, `activity_id`
     `D05-A01 … D05-A13`) using
     `INSERT ... ON CONFLICT (project_code, activity_id) DO UPDATE SET ..., updated_at=now();`

   So: **if the table does not exist it is created first, then the rows are inserted;
   if it already exists the rows are inserted/updated into it.** It is safe to re-run
   (idempotent — no duplicates).

2. **Confirm the insert with a SELECT before closing:**
   ```sql
   SELECT activity_id, activity_type, status, priority, activity_title
   FROM daily_task.tbl_scwts_sarujanan
   WHERE project_code = 'scwts' AND activity_date = DATE '2026-07-28'
   ORDER BY activity_id;
   ```
   Expect **13 rows** returned: `D05-A01` through `D05-A13`.

3. Also report the total row count for the project and then stop:
   ```sql
   SELECT count(*) AS scwts_total FROM daily_task.tbl_scwts_sarujanan WHERE project_code = 'scwts';
   ```
   (Expect 8 from D01 + 9 from D02 + 12 from D03 + 11 from D04 + 13 from D05 = **53** if all
   five days are loaded.)

Constraints: do not modify or delete any pre-existing rows; do not drop or alter
existing columns; only create-if-not-exists and upsert today's records.

---

## What today's 13 records cover

| activity_id | Type | Title |
|---|---|---|
| D05-A01 | investigation | Prove Component Received was showing the SKU catalogue date, not a receipt date |
| D05-A02 | investigation | Establish that the supplier schema contains no receipt or arrival date at all |
| D05-A03 | investigation | Discover `supplier.final_containers` as the real shipping container table |
| D05-A04 | implementation | Build the Dashboard V2 data model from supplier-received stock |
| D05-A05 | bugfix | Stop raw container foreign keys rendering as business values |
| D05-A06 | bugfix | Re-source component images from the supplier system instead of marketplace listings |
| D05-A07 | bugfix | Find and fix a join fan-out double-counting every KPI |
| D05-A08 | implementation | Add independent Components and Combos datasets behind one table |
| D05-A09 | validation | Prove no customer-review source exists before shipping Average Feedback |
| D05-A10 | enhancement | Restructure the table into grouped product blocks with per-marketplace colour |
| D05-A11 | enhancement | Add a one-page detail drawer exposing all 23 fields without scrolling |
| D05-A12 | bugfix | Catch four front-end defects that a syntax check could not detect |
| D05-A13 | implementation | Publish Dashboard V2 to Varman AIOS under its own hub slug |

**Source of the records:** skill file
`daily_works_logs/2026-07-28__sarujanan__scwts__REQ-01-D05.md`
and CSV `daily_works_logs/2026-07-28__sarujanan__scwts_daily-activities.csv`.

## Headline numbers from today

- Scope anchors: **178** new components → **223** combos → **261** component×combo pairs
- Output: **513** combo rows (349 products) · **189** component rows (178 products)
- KPI double-count corrected: impressions **10,174,398 → 9,416,881**, revenue **£11,383.18 → £11,090.48**
- Published: `varman_aios.hub_pages` id **65**, MD5-verified against the local file

## Two declared gaps (deliberate, not defects)

1. **Received Date** is derived from `final_containers.updated_at` where
   `status='completed'` — a container close-out, not a declared arrival event.
   326/513 rows populated; the rest are containers still open and are left blank
   rather than back-filled with the PO date.
2. **Average Feedback** has no source in this database and renders "No Reviews"
   for every row. The column is wired end-to-end and fills the moment a
   marketplace reviews feed exists.
