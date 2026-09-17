---
name: dashboard-v2-daily
description: Daily working procedure for Dashboard V2 (Supplier's Basket → Customer's Home) — build, validate, report and publish rules, the approved business rules (PO/SUPPLY resolution, completed-only vs All Data, SOT, Category), and the safety rules. Use for any Dashboard V2 data, query, validation, UI or publish task, and for the daily task update.
---

# Dashboard V2 — daily working procedure

## 0. Safety rules (never break these)
- **Database is READ-ONLY.** SELECT only. No INSERT/UPDATE/DELETE/DDL, on LEDSone or the old DB.
- **Never publish unless the user explicitly says so.** Publishing = `dashboard-v2-update/push_to_hub.js`, member name **`sarujanan`** only.
- **Never commit, push or create branches** unless asked.
- **Credentials only from the project `.env`** (`LEDSONE_PG*`, old DB `PG*`). Never hard-code them in a file or print them.
- **Do not change V2 business logic, SQL or UI design without approval.** New business rules need an explicit OK first.
- For a big change: **show the plan (files, line numbers, before/after, SQL) and STOP** until the user approves.

## 1. Load the environment first
```bash
cd /home/led-247/Supplier-to-Customer-Workflow-Tracking-System
set -a && . ./.env && set +a
```
LEDSone `tech_user` often returns *"too many connections for role"* — always wrap a build/query in a retry loop (5 tries, 20s apart).

## 2. The pipeline (3 stages)
```bash
python3 dashboard-v2-sql/build_v2.py      # LEDSone -> payload_v2.json (+ validation_v2.json)
python3 dashboard-v2-sql/make_html.py     # payload -> dashboard-v2/index.html
cd dashboard-v2-update && node push_to_hub.js sarujanan <slug> "<title>" ../dashboard-v2/index.html   # ONLY when asked
```
- `build_v2.py` ends with `RESULT: PASS/FAIL`. **Never publish a FAIL.** The "Average Feedback source" FAIL is a known *soft* one (no review table exists) and does not block.
- `make_html.py` needs `dashboard-v1/index.html` (it reuses the V1 CSS). Do not delete it.
- Cron `0 11 * * *` runs `scripts/refresh_and_publish_v2.sh`; it only fires when the PC is on.

## 3. Approved business rules (current)
**Component scope (base set)** — `inventory.products`: `inventory_bool = true`, `created_at >= date_trunc('year', CURRENT_DATE)`, non-blank SKU, **not deleted** (deleted flag comes from the old DB `inv_products.isdeleted`). No supplier join, no stock condition.

**Supply resolution (per component)** — arrived PO and completed supply are both "arrived"; take the **most recent** one:
- PO: `suppliers.orders.status_arrived = true`
- SUPPLY: `suppliers.old_supplyorder` + `old_supplyorderlist`, `lower(trim(status)) = 'completed'` (both `Completed` and `completed` exist)
- Received date: PO = container close-out / invoice ship-by · SUPPLY = `estimatedate`, else `date`
- Notes carry `SU1247 · source SUPPLY` or `LDI 12 2025 · source PO`
- **Never** parse `inventory.product_history` "Supply - SU…" text. That fallback is deleted.

**Status is an attribute, not a filter:** COMPLETED / INCOMING / NO SUPPLY DATA.

**Combos** — a combo qualifies only if it *uses* a base component (link derived from `inventory.products.sku_original` tokens with pack suffix `[A-Z]?[0-9]*PK`). Deleted combos excluded. The combo's own creation date is **not** a condition. Never use "all combos created this year".

**SOT column** — `configurator.components_sot_skus`, matched on the SKU itself, never on a prefix.

**Category filter** — SKU prefix, longest prefix first. `PH → Pendant Lamp Holder`, `WS → Wall Arm` (proved from the SOT `source_tab`). Unmatched → `Other`.

**Two modes** — default = completed-only; the **All Data** button shows the full base set. Default must always be OFF and turning it off must restore the default view exactly.

## 4. Expected numbers (check every build; if one differs, STOP and explain)
| Check | Value |
|---|---|
| components this year incl. deleted / deleted / base | 684 / 7 / 677 |
| status COMPLETED / INCOMING / NO SUPPLY DATA | 311 / 100 / 266 |
| main view components / combos | 311 / 411 |
| All Data components / combos | 677 / 615 |
| combo relationships (after deleted exclusion) | 786 |
| combos with no completed component / mixed | 204 / 69 |

Never adjust a target to match the output — report the discrepancy instead.

## 5. UI rules
- No redesign. Reuse existing components: `.btn` / `.btn ghost` for buttons, `.tab` for tabs, existing table/columns/colours.
- Never add a column without asking.
- All CSS lives in `make_html.py` (V1 stylesheet + the V2 blocks). Responsive rules: filter bar is 1 row ≥1560px, 2 rows 768–1559px, stacked below 768px.
- Wrap any optional feature in `/* ---- FEATURE (start/end) ---- */` markers so it can be deleted cleanly, and say which lines to delete.

## 6. Validation before reporting
1. Build log: `RESULT: PASS`, scope counts match §4.
2. Headless Chrome check (`/usr/bin/google-chrome` + playwright): row counts, toggles, filters, search, pagination, sort, **0 console errors**.
3. For a CSS/UI-only change, prove the payload and script bytes are unchanged (md5 of the file outside `<style>`).
4. `grep -rn "product_history\|Supply - " dashboard-v2-sql/` → comments only.
5. Report faithfully: if a number differs, say so; never hide a failure.

## 7. Daily task update (when the user asks for it — keep it short)
```
Today's Task: <what was done, 1–2 lines>
Task Assigned By: Varmen
User: Varmen
Expected Benefit: <business benefit, 1 line>
```

## 8. Known data gaps (report, do not paper over)
- 266 components have no PO and no supply record (157 of them hold stock). 4 SKUs are whitespace/typo near-misses — do not silently normalise.
- SKU re-codes (e.g. IMACCW → IMAC7714CW) have no `inventory.product_mapping` row.
- Warehouse id 33 (Unit 5) is missing from `inventory.warehouse`.
- `inventory.product_history` is a frozen partial copy (26 Aug 2026) — not a data source any more.
- Gap reports live in `validation/` (e.g. `DB_Designer_Gap_Report_Container_Received_20260915.md`).

## 9. Troubleshooting
| Symptom | Fix |
|---|---|
| `too many connections for role` | retry loop, 5 × 20s |
| `Cannot find module 'pg'` on publish | `npm install pg` inside `dashboard-v2-update/` |
| `make_html.py` fails | `dashboard-v1/index.html` is missing — restore from git |
| Disk full | scratchpad in `/tmp/claude-1000/...` is wiped on restart; keep backups of payload/HTML before a rebuild |
