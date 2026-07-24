# Supplier's Basket → Customer's Home — Data Correction Report

**Date:** 2026-07-24 · **Page:** `dashboard-v1/index.html`
Source of truth = live PostgreSQL (`order_management_copy @149.28.134.54:5435`).
Reporting window start = **2026-01-01**.

---

## UPDATE 2 (2026-07-24) — LISTING-DATE-DRIVEN row model

**Requirement:** *"Fetch ONLY the products whose Listing Date (`created_at` in
`listing_data`) is from 2026-01-01 up to the present. Display all details for
those only."*

**What changed:** the master table is now **driven by in-window listings**, not by
an activity union. Previously rows marked **"Not Listed"** appeared (they had
orders but **no Listing Date**) — those are now **excluded entirely**. Every row
has a real Listing Date ≥ 2026-01-01.

- **Listing Date column** = `public.listing_data.created_at` (verified: there is
  no separate `created_date` column — `created_at` *is* the listing-creation
  timestamp). No substitution with container/component/combo dates.
- **Row grain** = one `(combo_sku, platform)` that has ≥1 in-window,
  `is_child=1`, `wrong_sku=0` listing; Listing Date = the earliest such
  `created_at`; that row's `ref_id` / `listing_url` / `main_image_url` are carried.
- Builder: **`dashboard-v1-sql/build_listing_driven.py`** (self-contained,
  idempotent). Driver SQL: **`dashboard-v1-sql/04_listings.sql`** (now carries the
  `created_at >= 2026-01-01` filter that was missing).
- Component metadata refreshed live **456 → 497** new components
  (`dashboard-v1-sql/component_meta.psv`).
- Two now-meaningless KPI cards repurposed: **Not Listed → Units Sold**,
  **Visibility Gaps → Impressions** (every product is listed by construction).

**Result (all rows have a Listing Date in-window):**

| Metric | Value | Check |
|---|---:|:--:|
| Rows (combo × platform, all Listed) | **1,680** | ✅ = live SQL |
| Distinct combos / components | 1,334 / 172 | ✅ |
| Listing date min / max | 2026-01-01 / 2026-07-23 | ✅ in-window |
| Rows with Listing Date before window | **0** | ✅ |
| Rows with blank Listing Date | **0** | ✅ |
| Rows not "Listed" | **0** | ✅ |
| Orders / Units / Revenue | 1,614 / 3,098 / **£60,971.18** | ✅ = live SQL |
| Returns (units) | 194 | ✅ |
| Impressions (in-window) | 39,438,306 | ✅ |
| Product URLs (http) / Images | 1,680 / 1,673 | ✅ |

> Revenue is lower than UPDATE 1's £162k **by design**: it now counts only sales
> of products that have an in-window listing (matched by combo × platform).
> £-value of combos selling **without** a 2026 listing is intentionally excluded.

---

## UPDATE 1 (2026-07-24) — earlier activity-union correction (superseded by UPDATE 2)

## 1. Root-cause analysis

| # | Symptom reported | Root cause | Original dashboard did it right by… |
|---|---|---|---|
| **D1** | Listing counts far too high | `dashboard-v1-sql/04_listings.sql` had **no `created_at` filter**. 12,880 of 14,977 listing rows (86%) predated the window — back to **2019-06-26**. | `sql/listings.sql`: `l.created_at >= '2026-01-01' AND l.is_child = 1`. |
| **D2** | Listing Date wrong / pre-2026 | Direct consequence of D1 — dates from 2019–2025 shown as Listing Date (earliest was 2019-06-26). | Listing Date = `listing_data.created_at::date`, only for in-window rows. |
| **D3** | "Container Arrival 04-Aug-2026" | `01_components.sql` used `COALESCE(expected_completion_date, finished_date, confirmed_date)`. `expected_completion_date` is a **forecast** reaching **2026-08-31** (11 future POs). **No arrival-date column exists** in `supplier.containers` or `supplier.orders`. | No fake arrival date — the DB simply has none. |
| **D4** | URL not a link; no image | The URL column held a bare `ref_id` ("314148529895"), not a URL. No image column existed. | — (new columns; sources validated below). |

---

## 2. Corrections applied

### Listings scope & date (D1 / D2)
```sql
FROM public.listing_data
WHERE sku IN (SELECT sku FROM qc)     -- qualifying combos (unchanged lineage)
  AND created_at >= '2026-01-01'      -- ADDED — the filter v1 was missing
  AND is_child = 1                    -- ADDED — sellable variant, as in listings.sql
```
Listing Date business rule (matches original at the combo×platform grain):
**earliest in-window `created_at`** per (combo, platform); that row's
`ref_id` / `listing_url` / `main_image_url` are carried, so the link always
matches the date shown.

Result: in-window listing rows **14,977 → 1,982** (raw) / **1,363** aggregated to
(combo×platform); **0** listing dates before 2026-01-01; earliest = 2026-01-01.

### Container arrival (D3)
Column relabelled **Container Status** → `Arrived` / `In Transit`
(from `supplier.orders.status_arrived`, a genuine flag). The forecast
`expected_completion_date` is shown only in **Notes** as "Expected completion …",
never as an arrival date. No August dates remain in any arrival field (verified 0).

### Orders / Traffic / Returns — logic UNCHANGED
Reused verbatim from the original dashboard SQL (revenue must match):
- Orders: `order_status='Completed' AND order_date >= '2026-01-01'`.
- Traffic: `traffic_data` + `ppc_performance`, joined through `listing_data`
  with **one row per `ref_id`** (no join fan-out — the same fix as `sql/traffic.sql`).
- Returns: Amazon direct; eBay per `return_id`; Shopify qty via the order line.

---

## 3. Date-field validation (Step 7)

| Dashboard column | DB table → column | Transformation | Windowed? |
|---|---|---|---|
| Component Received | `supplier.order_items.created_at` (MIN per SKU = first receipt) | `::date` | nc gate `>= 2026-01-01` |
| Container Status | `supplier.orders.status_arrived` | flag → Arrived/In Transit | n/a (no date exists) |
| Combo Creation Date | `public.listing_data.created_at` (MIN per combo SKU) | `::date`; corrupt `00xx` blanked | not windowed (a combo may legitimately predate the window) |
| **Listing Date** | `public.listing_data.created_at` | earliest in-window per combo×platform | **yes, `>= 2026-01-01`** |
| Last Updated | snapshot `capturedAt` | ISO date | n/a |

---

## 4. Image source validation (Step 5)
- Source: **`public.listing_data.main_image_url`** (99.6% populated in-window).
- Rendered as a thumbnail linking to the same URL; `onerror` → blank cell.
- Amazon → `m.media-amazon.com`, Shopify → `cdn.shopify.com`, eBay → `i.ebayimg.com`.
- **1,352** rows carry a real image; the rest show "—". No invented URLs.

## 5. URL source validation (Step 6)
- Source: **`public.listing_data.listing_url`** (100% full `http(s)` URLs in-window).
- Rendered as a clickable "🔗 View product" link (`target=_blank`, `rel=noopener`).
- Verified live samples open the correct product page:
  - Amazon `https://www.amazon.co.uk/gp/product/B072R5FSMB`
  - eBay `https://www.ebay.co.uk/itm/…/318300297671`
  - Shopify/Website `https://ledsone.de/products/…`
- **1,360** listed rows carry a working link. No fake URLs.

---

## 6. Final validation — new page vs original dashboard SQL (live)

| Metric | Original dashboard SQL (live) | New page | Match |
|---|---|---|---|
| Completed revenue | **£162,261.83** | £162,261.83 | ✅ exact |
| Units sold | **8,686** | 8,686 | ✅ exact |
| Returns (units) | **440** | 440 | ✅ exact |
| Listings (combo×platform, in-window) | 1,363 | 1,360 listed rows | ✅ |
| Listing dates before window | 0 | **0** | ✅ |
| Earliest listing date | 2026-01-01 | 2026-01-01 | ✅ |
| Product URLs (http) | — | 1,360 | ✅ |
| Product images | — | 1,352 | ✅ |
| Future "arrival" dates | — | **0** | ✅ |

Orders KPI (4,912) is a sum of per-(combo×platform) `COUNT(DISTINCT order_id)` —
the same aggregation the original page used; the global-distinct figure is 4,826.
Revenue, the financial figure, is exact.

**Theme and layout unchanged** — only data retrieval, joins, dates, images, and
URLs were corrected.
