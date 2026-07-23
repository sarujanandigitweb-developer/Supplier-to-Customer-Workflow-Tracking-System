# Dashboard Refresh Validation — 20260723_144747

**Result:** ❌ FAIL  ·  Window 2026-01-01 → 2026-07-23


> **Aborted:** permission denied for schema supplier
LINE 3:        FROM supplier.order_items
                    ^


## Dataset reconciliation (live export vs current data.js)

| Dataset | data.js (current) | New export | Added | Removed | Match |
|---|---:|---:|---:|---:|:--:|

## KPI totals (recalculated from PostgreSQL — not hardcoded)

| KPI | Current data.js | New export | Δ |
|---|---:|---:|---:|

## Validation checks

| Check | Result | Detail |
|---|:--:|---|
| export/validation | ❌ | permission denied for schema supplier
LINE 3:        FROM supplier.order_items
                    ^
 |

## ❌ Failure analysis

- **export/validation** — permission denied for schema supplier
LINE 3:        FROM supplier.order_items
                    ^
. Likely cause: a broken/renamed source table, an incorrect WHERE/JOIN, or a partial export. data.js was **NOT** replaced; previous dashboard kept.
