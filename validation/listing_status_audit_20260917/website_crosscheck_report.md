# Public website cross-check — 17 September 2026

No application code, dashboard payload, or database records changed. This report extends the database-only audit with public website checks.

## Coverage

- Dashboard scope: 1,295 distinct SKUs.
- 625 SKUs have matching/candidate source listing evidence: 581 with at least one dashboard Listed platform, 44 with no Listed platform.
- Checked all 2,120 unique nonblank source listing URLs, deduplicated into 1,639 public requests (Shopify variants share a product JSON endpoint).
- 670 SKUs have no source listing URL/evidence under the earlier matching rules. No claim is made that those physical products do not exist elsewhere.
- The source listing evidence contains 31 records without URLs. These records cannot independently be website-checked.
- The exact identity proof used for confirmed matches is Shopify public product JSON: requested variant ID exists and its SKU equals the dashboard SKU character for character.
- Checks read public data only; no checkout or purchase was attempted. available=true is the storefront's availability flag, not a completed order.
- Amazon/eBay/B&Q page availability or SKU text alone was not accepted as exact variant proof.

## Main result: dashboard Not Listed

| Result | Distinct SKUs |
|---|---:|
| Exact website variant SKU verified and available=true on at least one checked page | 9 |
| Exact website variant SKU verified, but all verified variants have available=false | 8 |
| Source evidence exists, exact website variant SKU remains unverified | 27 |
| No matching source evidence / listing URL | 670 |
| Total with no Listed dashboard platform | 714 |

Thus **17 Not Listed SKUs have confirmed exact website listing identity; 9 also report availability**. All 17 belong to the previously identified 32 date-cutoff cases. The 8 availability=false products still have public listing records; they should not be described as currently purchasable based on this check.

The earlier counts answer different questions:
- 32: source records excluded only by the pre-2026 creation-date rule.
- 20: subset of those 32 whose inventory record was created in 2026, like ENC9760.
- 17: exact listing identity independently verified on public websites.
- 9: subset of those 17 currently returning available=true.

The 17 and 9 are confirmed findings, not an estimate that the remaining products are unlisted.

## Whole-scope website results

| Dashboard status | Exact SKU, available=true | Exact SKU, available=false on verified pages | Exact SKU unverified |
|---|---:|---:|---:|
| At least one Listed platform | 284 | 85 | 212 |
| No Listed platform, source evidence exists | 9 | 8 | 27 |
| Total with source evidence | 293 | 93 | 239 |

386 unique SKUs have an exact website SKU match. 239 with source evidence remain unverified. Availability=false on a checked Shopify variant says nothing definitive about stock on another marketplace.

## Access limitations

Of 1,639 public requests: 1,036 returned HTTP 200, 325 returned 403, 208 returned 503, 68 returned 404, 1 returned 401, and 1 request failed. A 200 page can still omit the seller SKU or exact variant data. Errors and missing SKU details were retained as unverified, not converted to Not Listed. A 404 on one source URL does not prove the product is absent from every website.

ENC9760 remains outside the 17 exact website-confirmed SKUs: the database child-SKU mapping is verified, and the eBay page shows the parent product/variation choices, but the public website check did not independently prove the exact selected variation's seller SKU. The web search tool's parent-page result was cached, so it was not used as current exact-SKU proof.

## Files

- website_confirmed_not_listed.csv: the 17 confirmed exact-SKU listings and their URLs.
- website_all_skus_summary.csv: all 1,295 SKUs with dashboard and website findings.
- website_record_checks.csv: per-source-record URL/variant comparison.
- website_fetch_results.jsonl: public request status, UTC check time and extracted variant SKU/availability evidence.
- website_summary.json: machine-readable counts.

## Interpretation

The complaint is supported for at least 17 products whose exact public listing exists while the dashboard says Not Listed; 9 also have positive website availability evidence. The dashboard's 2026 listing-record date cutoff explains these 17 cases. Listing existence, current availability, and SKU first-listed date are separate facts. No SKU rename or original SKU attachment date is proven by this website check.
