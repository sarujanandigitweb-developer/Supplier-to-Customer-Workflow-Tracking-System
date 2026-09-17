# Dashboard V2 — Pack classification, All-Products counts and daily-refresh validation

**Date:** 2026-09-17 · **Developer:** Sarujanan · **Reviewer:** Varmen (pending)
**Status:** PASS · **Published:** NO · **Committed:** NO · **Database writes:** NONE (SELECT only)

---

## 1. Requirement
1. Split the product population into three first-class categories — **Component / Combo / Pack** — with Packs as their own tab.
2. On the All Data (All Products) scope show **Combo Components** and **Pack Count** as *distinct products*, never marketplace rows.
3. Validate the daily cron refresh end to end and prove new records are discovered automatically.

## 2. Files inspected / changed
| File | Change |
|---|---|
| `dashboard-v2-sql/v2_sources.py` | **changed** — added `CREATE TEMP VIEW product_pk` (authoritative pack codes) |
| `dashboard-v2-sql/build_v2.py` | **changed** — §1c canonical classification (`is_pack`, `classify`), `B["cls"]` on every row, classification/count reconciliation, payload keys `classification` + `packCodes` |
| `dashboard-v2-sql/make_html.py` | **changed** — Packs tab, datasets split by `B.cls`, distinct-product badges, Combo Components / Pack Count on the count line, phone tab compaction |
| `scripts/refresh_and_publish_v2.sh` | inspected only, **not modified** |
| `logs/automation_v2.log`, `crontab -l` | inspected only |

## 3. Authoritative Pack source
`inventory.product_pk` — 28 rows, `pack_char → pack_qty`: A=10, B=15, C=20, D=30, E=50, F=100, G=12, H=16, I=24, J=75, K=150, L=11, M=80, N=200, O=250, P=300, Q=500, R=1000, S=25 and 1–9 = 1–9.
The build reads this table **every run** (`SELECT pack_char FROM pg_temp.product_pk`); the code list is never hardcoded.

## 4. Classification rule and precedence
```
PACK      := sku has no '+'  AND  sku ~ '(<pack_char>|...)PK$'      -- codes read from inventory.product_pk
COMBO     := product is not a component product and is not a PACK    -- '+' combos and coded ENC* combos
COMPONENT := eligible component product that is not a PACK
```
**Precedence:** authoritative pack table → PACK → existing combo relationship → COMBO → COMPONENT.
A `+` SKU is never a Pack. Evidence: 7,190 pack SKUs exist database-wide with **0** false positives (no SKU contains "PK" other than as a terminal pack token; 0 SKUs end in "PK" with a non-pack character before it), while 5,901 `+` SKUs merely contain pack tokens and stay COMBO.

**Single source of truth:** classification happens only in `build_v2.py` and travels in the payload as `B["cls"]`. The UI filters on that value; no regex exists in the JavaScript.

## 5. The 273 pack-suffixed `inventory_bool = true` products
All **273** were created **before** the current year (`created_at < date_trunc('year', CURRENT_DATE)`), so none reaches the 677-product eligible base set (in-scope count = **0**). The rule is nevertheless applied to the eligible population, not assumed: `classify()` tests the pack rule **before** the component branch, so a future in-scope component SKU ending in a pack code becomes PACK automatically. The build reports this as `component_products_classified_pack` (currently 0).

## 6. Classification results (current database, 2026-09-17)
| Category | Main scope | All Data scope |
|---|---:|---:|
| Component | 311 | **677** |
| Combo | 257 | **407** |
| Pack | 156 | **211** |
| **All products** | **724** | **1,295** |

Discovery (2026-09-16) projected 404 / 211 / 1,292 for All Data. The delta is live data: **+3 combos** created since, so 618 combo-side products instead of 615 (407 + 211 = 618 ✓). No number was forced.

**Changed SKUs:** every SKU moved is a Combo → Pack move; no SKU moved in any other direction.
Main scope: 156 products (e.g. `CO432AGY5PK`, `CO432AGYCPK`, `CO832AGY5PK`, `CO832AGYCPK`, `MBEX2535WHBPK`).
All Data: 211 products. Components: 0 moved. Pack suffixes actually used: 2PK, 3PK, 4PK, 5PK, 6PK, APK, BPK, CPK, FPK, GPK, IPK, NPK, PPK, QPK — all present in `inventory.product_pk`.

## 7. Independent reconciliation (DB query vs payload)
| Population | Database | Payload | Missing | Extra |
|---|---:|---:|---:|---:|
| Components | 677 | 677 | 0 | 0 |
| Combos | 407 | 407 | 0 | 0 |
| Packs | 211 | 211 | 0 | 0 |
| All products | 1,295 | 1,295 | 0 | 0 |

Exclusivity: Component ∩ Combo = 0 · Component ∩ Pack = 0 · Combo ∩ Pack = 0 · products with more than one class = 0 · duplicate classifications = 0.
Pack integrity: pack SKUs not matching a `product_pk` code = **0**; `+` combos wrongly moved to Pack = **0**; payload packs whose component is not in the base set = **0**.

## 8. Relationships
| Measure | Count |
|---|---:|
| Database eligible relationships | **795** |
| Payload relationships | **795** |
| Missing / Extra / Duplicates | **0 / 0 / 0** |
| Split: normal combo + pack | 584 + 211 = 795 ✓ |

No pack relationship was deleted; the relationship is preserved and only the target product's category changed.

## 9. All-Products count definitions and validation
| Metric | Definition (approved) | UI | Independent source count | Result |
|---|---|---:|---:|---|
| **Combo Components** | distinct component SKUs participating in **normal combo** relationships (packs excluded) | 128 | 128 | PASS |
| **Pack Count** | distinct **pack product** SKUs | 211 | 211 | PASS |
| Main scope equivalents | same definitions, main scope | 70 / 156 | 70 / 156 | PASS |

Discovery expected 215 for Combo Components. 215 is the count of components in **any** relationship; excluding pack relationships as instructed gives **128** (90 components have pack relationships only; 128 + 90 = 218 components with any relationship today, up from 215 because of the 3 new combos). Both numbers are computed dynamically from the active scope.

## 10. Regression — pre-change code vs post-change code, same database
The pre-change builder was re-run against the current database minutes before the new build:

| Dataset | Rows before | Rows after | Field differences |
|---|---:|---:|---|
| Combo rows | 976 | 976 | **NONE** |
| Component rows | 434 | 434 | **NONE** |
| All-data components | 885 | 885 | **NONE** |
| All-data combos | 1,207 | 1,207 | **NONE** |

28 fields compared per row (supplier, container, received, SKUs, images, created, listing status/date/URL, marketplace, impressions, clicks, orders, units, revenue, returns, return-rate, reason, destination, PO, qty, notes, feedback, SOT, category, Record ID). `meta` identical (311 / 413 / 468), `allData` identical. The only payload difference is the added `cls` key.

UI regression at 1600 / 1280 / 1024 / 768 / 375: filter rows 1 / 2 / 2 / 2 / 7 (unchanged), header-body alignment drift 0.0px, page overflow 0, 0 console errors. Search, category filter, pagination and column sorting verified on the Packs tab. CSV export unchanged at 23 columns and scoped to the active tab (Combos 415 rows, Packs 393, Components 434). Record ID prefixes unchanged (REC / CMP / ALB).
One fix was required: the third tab pushed the page 24px wide at 375px; a tab-compaction rule at ≤600px restores overflow to 0.

## 11. Daily cron
| Item | Value |
|---|---|
| Schedule | `0 11 * * *` (plus V1 11:15 and V3 16:00) |
| Command | `scripts/refresh_and_publish_v2.sh >> logs/cron_v2.out` |
| Working dir / lock | project root, `flock -n` guard against concurrent runs |
| Environment | `. "$PROJECT/.env"` (LEDSONE_PG*) |
| Stage 1 | `/usr/bin/python3 dashboard-v2-sql/build_v2.py` → `payload_v2.json` |
| Stage 2 | `/usr/bin/python3 dashboard-v2-sql/make_html.py` → `dashboard-v2/index.html` |
| Stage 3 | `node dashboard-v2-update/push_to_hub.js sarujanan supplier-to-customer-workflow-tracking-v2` → `varman_aios.hub_pages`, gated on stage 1–2 exit 0 and `MIN_BYTES=300000` |
| Log | `logs/automation_v2.log` (credentials redacted) |
| Failure handling | any stage non-zero → exit 1, dashboard left unchanged, publish skipped |

**Flow (verified):** cron → `.env` → LEDSone → `build_v2.py` → `v2_sources.py` temp views → eligible products → relationships → **pack classification** → counts → `payload_v2.json` → `make_html.py` → `dashboard-v2/index.html` → hub publish.

**Fresh-query proof:** `build_v2.py` only ever *writes* `payload_v2.json` (line 1178) — it never reads it. There is no cached JSON, no static SKU list and no stored component/combo list anywhere in the builder; every population comes from a live `SELECT`. `make_html.py` reads the payload that stage 1 has just written.

## 12. New-data discovery (freshness witnesses, read-only)
| Witness | Record | In payload | In HTML |
|---|---|---|---|
| Newest component | `SPAL68YB` (2026-09-14 13:26) | YES | YES |
| Newest `+` combo | `CRSF10025WH+WSUSHE27WH+SPAL68WH+LSGL12010FW` (2026-09-16 12:52) | YES | YES |
| Newest relationship | `WSUSHE27WH` → that combo | YES | YES (component listed on the row) |
| Newest pack | `CCBC93PK` (2026-09-16 12:52) | NO — **correct**: its base component `CCBC9` was created 2024-10-25, outside this year's base set | — |

**New pack code (test fixture, nothing written to the database):** building the rule from the live 28 codes classifies `EXAMPLETPK` as not-a-pack; building it from the same list plus a hypothetical `T` classifies it as a pack, while `CRSF100BM+LHX2PK` stays a combo in both. Because the list is read from `inventory.product_pk` at build time, a new code is honoured on the next run with no code change.

## 13. Risks / blockers (evidence-based)
| Risk | Evidence | Status |
|---|---|---|
| **LEDSone connection limit** | `logs/automation_v2.log` 2026-09-16 11:00:04 — `FATAL: too many connections for role "tech_user"` → stage 1 failed, publish skipped | **ACTIVE BLOCKER** — yesterday's refresh produced no new dashboard. No retry logic in the script |
| Cron only fires while the PC is on | machine-local crontab | Known |
| Payload size 2.6 MB / page 2.74 MB | file sizes | Watch publish duration |
| 266 components still have no PO/supply record | earlier audit | Data gap, owned by purchasing |

## 14. Limitations
- Packs are shown through the combo-side product columns (Combo SKU / Image / Created); no new columns were added.
- The Components tab keeps the completed-only scope unless All Data is on.
- `ingest`-style publication was not run; nothing was published or committed.

## 15. Next step
Fix the cron connection-limit failure (retry loop in `refresh_and_publish_v2.sh`), then request publication approval.
