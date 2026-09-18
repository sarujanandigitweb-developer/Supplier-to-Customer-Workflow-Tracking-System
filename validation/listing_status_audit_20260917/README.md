# Dashboard V2 listing-status validation — 17 September 2026

Validation only. No application code, payload, database records, or published dashboard changed during this audit. Existing image-viewer edits were left untouched.

## Scope and method

Compared the local HTML's embedded payload with payload_v2.json: identical. Checked every distinct SKU in the default and All Data views against live LEDSone source records using SELECT only through the database connector. The direct connection was unavailable; the connector succeeded.

Checked 1,295 distinct SKUs and 2,876 matching listing records from Amazon, eBay, Shopify and B&Q. Matching includes the builder's mapped-SKU precedence and locale suffix removal, plus case-insensitive raw/mapped exact-SKU candidates for diagnosing mapping exclusions. No fuzzy equivalence between different products or bundles was assumed. Marketplace websites were not independently checked.

## Results

| View | Products | At least one Listed platform | No Listed platform |
|---|---:|---:|---:|
| Default components | 311 | 95 | 216 |
| Default combos/packs | 413 | 272 | 141 |
| All Data components | 677 | 177 | 500 |
| All Data combos/packs | 618 | 404 | 214 |

Default is a subset of All Data; do not add the two scopes together.

**Zero SKU/platform mismatches against the current builder rules. This does not mean the label accurately describes current marketplace availability.**

Of the 714 All Data SKUs with no Listed platform:
- 32 (2 components, 30 combos/packs) have otherwise qualifying listing records excluded solely because their creation date is before 2026.
- Of those 32, 20 have a source record explicitly marked Active/active. 31 have either an explicitly active record or an eBay record marked not ended. These are database indicators, not independent storefront verification.
- 12 additional SKUs have only parent or different-resolved-SKU evidence requiring review.
- 670 have no matching record under the checked SKU rules in these four source tables. This is not proof that the physical product is unavailable under a different SKU or in an unsynced marketplace.

Six of the 32 older-record cases are in the default view: PHHRE2HETX2HE, ENC9760, and the four CRFF4002BM / CRFF4503BM / CRFF5004BM / CRFF5005BM combos listed in not_listed_review.csv.

## Concrete examples

| SKU | Platform | Source creation date | Source status | Dashboard |
|---|---|---|---|---|
| PHHRE2HETX2HE | Amazon | 2024-07-01 | Active | Not Listed |
| PHLSGP350WI | Shopify | 2023-12-15 | active | Not Listed |
| ENC9760 | eBay | 2024-10-09 | is_ended = 0; status blank | Not Listed |

The immediate cause is the condition ld.created_at >= '2026-01-01' in both listing queries (build_v2.py, around lines 492 and 627). The source adapter adds 5 hours 30 minutes before this comparison. The builder comment calls this an approved reporting-window rule to avoid recycled historical listing records. Changing that rule needs a separate decision; this audit does not change it.

The existing builder also does not require Amazon/Shopify/B&Q source status to be active; a qualifying draft or inactive record can count as Listed. Consequently Listed currently means a qualifying database listing record exists in the reporting window, not necessarily that the listing is currently live.

## Scope-count discrepancy

The local skill's historical reference counts are 411 default combos/packs and 615 All Data combos/packs. The saved 17 September payload has 413 and 618 respectively. This audit uses and reports the actual payload counts; it does not adjust targets or validate changes to component/combo discovery.

## Review files

- all_skus.csv: one row per SKU, dashboard statuses, source platforms and exclusion counts.
- not_listed_review.csv: all 44 Not Listed SKUs with source evidence requiring review.
- source_evidence.csv: matching source records with dates, status, flags, mappings, URLs and exclusion reasons.
- rule_mismatches.csv: zero mismatches.
- summary.json: machine-readable scope and comparison counts.

Recommended next decision: define whether Listed should mean current marketplace availability or a listing created in the 2026 reporting window. If it means current availability, creation date alone cannot determine the status; active/ended state and recycled-record handling also need to be considered.
