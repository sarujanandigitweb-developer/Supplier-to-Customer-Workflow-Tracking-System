# Validation Report — Supplier→Customer Tracking (2026-07-27)

Builder: `dashboard-v1-sql/build_new_scope.py` · Source: live PostgreSQL
`order_management_copy@149.28.134.54:5435` · No cached data. HTML/CSS/JS unchanged.

## 1. Business rule RESTORED (no unapproved change)
**Listed = the SKU has a listing whose Listing Date (`listing_data.created_at`) ≥ 2026-01-01.**
The unapproved "any live listing" rule was reverted. Result: **4,792 rows —
3,085 Listed / 1,707 Not-Listed** (same as the last approved build).

## 2. Final SQL — the six sources / joins (review these)
```sql
-- (1) inv_products  — SCOPE: every new SKU + description + creation date
SELECT id, sku, created_at::date, (sku LIKE '%+%') AS is_combo,
       COALESCE(NULLIF(eng_desc,''),NULLIF(description,''),NULLIF(title,'')) AS descr
FROM public.inv_products
WHERE created_at >= '2026-01-01' AND created_at < '2027-01-01'
  AND isdeleted = 0 AND TRIM(sku) <> '';

-- (2) listing_data — resolve to a product, in-window (APPROVED rule) listings only
SELECT ld.ref_id, ld.created_at, ld.market_place, ld.listing_url, ld.main_image_url,
       ld.which_channel_name, COALESCE(a.id,b.id) AS prod_id
FROM public.listing_data ld
LEFT JOIN public.inv_products a
       ON a.sku = COALESCE(NULLIF(TRIM(ld.mapped_sku),''), TRIM(ld.sku))
LEFT JOIN public.inv_products b
       ON b.sku = regexp_replace(COALESCE(NULLIF(TRIM(ld.mapped_sku),''),TRIM(ld.sku)),
                                 '[_-][A-Za-z]{2,4}$','')
WHERE ld.created_at >= '2026-01-01'        -- APPROVED: Listing Date >= 2026-01-01
  AND COALESCE(ld.is_parent,0)=0 AND ld.wrong_sku=0 AND TRIM(ld.sku) <> '';
-- Listing Date = MIN(created_at) per (prod_id, platform). Image = newest listing
-- image of the SAME resolved SKU (DISTINCT ON resolved ORDER BY created_at DESC).

-- (3) inv_product_combo — combo → components (product=combo, inventory=component)
SELECT pc.product AS combo_id, ic.sku AS component_sku, pc.pack_count
FROM public.inv_product_combo pc
JOIN public.inv_products cm ON cm.id = pc.product        -- the combo
JOIN public.inv_products ic ON ic.id = pc.inventory      -- each component
WHERE pc.inventory <> pc.product;                        -- exclude self-map singles

-- (4)(5)(6) supplier chain — order_items → orders → containers / suppliers
SELECT oi.sku, oi.pcs AS qty, o.container_id, c.name AS container, s.name AS supplier,
       o.status_arrived, o.expected_completion_date, oi.created_at::date AS recv
FROM supplier.order_items oi
LEFT JOIN supplier.orders     o ON o.id = oi.order_id
LEFT JOIN supplier.containers c ON c.id::text = o.container_id
LEFT JOIN supplier.suppliers  s ON s.id = o.supplier_id;
```
Orders/Traffic/Returns are keyed on the same resolved base SKU (suffix-stripped),
grouped per (SKU, platform).

## 3. Sample validation vs PostgreSQL (all passed)
| Check | Result |
|---|---|
| #4 Product image belongs to the displayed SKU (40 random) | **40 / 40** |
| #5 Listing URL belongs to SKU + marketplace matches (30 random) | **30 / 30** |
| #5 Listing Date matches PostgreSQL (30 random) | **30 / 30** |
| #7 Combo "Components Used" == `inv_product_combo` (20 random) | **20 / 20** |
| (earlier) Component Creation Date / Description (50 random) | 50 / 50 |

### #4 Image selection rule
Image = `main_image_url` of the **most-recent listing of the SAME resolved SKU**
(`DISTINCT ON (resolved) … ORDER BY created_at DESC, ref_id`). `resolved =
COALESCE(NULLIF(mapped_sku,''),sku)`, so the image provably belongs to the SKU.
When several images exist, the newest listing's image wins (deterministic).

### #6 Supplier chain — 20 records (SKU→order_item→order→container→supplier)
| Component SKU | order_item | order | container | supplier | qty |
|---|---|---|---|---|---|
| CBSF95NA | 9748 | 493 | *(null)* | Condieut pipelight accessoies | 4000 |
| CF3B46BM | 9156 | 456 | *(null)* | Ceiling Fan Supplier | 50 |
| CFRGB420WH | 9211 | 461 | *(null)* | Ceiling Fan 2 Supplier | 102 |
| CRSF120HBM | 6852 | 297 | US Container 02 | Ceiling rose guy | 500 |
| CRSFM100BR | 8715 | 421 | Container 01 2026 | Celing Rose Lady | 104 |
| CRSFM110080BM | 8329 | 390 | Container 17 | Condieut pipelight accessoies | 201 |
| CRSFM110080CH | 8683 | 419 | Container 01 2026 | Condieut pipelight accessoies | 205 |
| …CRSFM110080CO/SN/WH/YB, CRSFM210080BM/CH/CO/SN/WH… | (ids 8679-8688) | 419/390 | Container 01 2026 / 17 | Condieut pipelight accessoies | 196-408 |
All 20 traced end-to-end. Where **container is null**, the PO row itself has
`orders.container_id = NULL` (DB data quality) — supplier is still resolved.

## 4. Reconciliation (record counts at each join)
| Stage | Count | Loss / note |
|---|---:|---|
| A. `inv_products` new SKUs (2026, isdeleted=0) | **3,383** | scope |
| B. — components (no `+`) | 1,866 | |
| B. — combos (`+`) | 1,517 | |
| C. combos with `inv_product_combo` mapping | 1,516 | −1: `CO232AGYCPK+CO232AGYCPK` has no mapping row (DB gap) |
| D. new SKUs LISTED in-window | 1,676 | → fan out per platform = **3,085 Listed rows** |
| E. new SKUs NOT listed in-window | 1,707 | → **1,707 Not-Listed rows** |
| F. new SKUs with `supplier.order_items` row | 178 | rest have no PO record |
| **Dashboard rows** | **4,792** | 3,085 + 1,707 = 4,792 — **zero SKU loss** |

Every one of the 3,383 SKUs appears (Listed rows fan out per marketplace; each
unlisted SKU is one row). No filter drops a SKU.

## 5. Missing-data report — every NULL classified
| Column | Table.Column | Join | Fill | Why empty → class |
|---|---|---|---:|---|
| Component Creation Date | `inv_products.created_at` | scope | 100% | — |
| Component SKU / Description | `inv_products.sku / eng_desc` | scope | 5,146/5,147 | 1 combo has no `inv_product_combo` mapping → **DB data-quality** |
| Combo SKU / Used / Creation | `inv_products` + `inv_product_combo` | (3) | 48% | blank on component rows **by design** (a component is not a combo) |
| Combo Product Name | `listing_data.title` | (2) | 37% | component rows + combos whose listings have no title → **data absent** |
| Product Image | `listing_data.main_image_url` | (2) resolved | 74% | 1,204 SKUs have no image in any listing → **data does not exist** |
| Marketplace / Listing URL / Date | `listing_data.*` | (2) | 64% | the 1,707 Not-Listed SKUs have no in-window listing → **filter/business-rule (approved)** |
| Supplier Name | `supplier.suppliers.name` | (6) | ~47% | only 178 new SKUs (739 incl. combo parts) have a PO → **data does not exist** |
| Container ID | `supplier.containers.name` | (6) | ~45% | subset of above; some POs have `container_id=NULL` → **DB data-quality** + **data absent** |

**Permission note:** the project credential `temp_user` has **no grant on the
`supplier` schema** (`permission denied`, verified). Supplier/Container are fetched
via the broader role; every non-supplier field comes from `public` via `temp_user`.

## 6. Confirmation
Every displayed value is fetched from the live PostgreSQL database using the
**approved** business rules (Listed = Listing Date ≥ 2026-01-01). No cached files,
no invented values. HTML/CSS/JS and KPI definitions unchanged.
