# ENC9760 listing-date investigation — 17 September 2026

Read-only SELECT validation against LEDSone. No application code or data changed.

## Verified records

- Inventory product ID 41979, SKU ENC9760: created_at 2026-04-06 08:01:04; updated_at 2026-05-07 10:39:07 (raw database timestamps).
- Current composition: CRFF500BM+PHHRE2HETX2HE3PK+ICST64E273PK+CO123PCL.
- eBay item 265768509380, parent database ID 10622: created_at 2022-07-06 13:03:49; status Active; is_ended 0.
- Child database ID 722803: current SKU ENC9760; variation “Required the Bulbs?” = “Yes”; created_at 2024-10-09 10:05:26; updated_at 2026-09-17 03:00:47; is_ended 0; wrong_sku 0; is_parent 0; is_child 1. Child status is NULL.
- Explicit parent-child mapping ID 9425 connects parent 10622 to child 722803.
- The other child, ID 722804, is SKU CRFF500BM+PHHRE2HETHE3PK+CO123PCL and represents “Required the Bulbs?” = “No”, under the same eBay item.
- No inventory.product_mapping row was returned for ENC9760 on either side of the mapping. No other inventory product with the exact same sku_original composition was returned.

## Interpretation

This is an exact current child-SKU match with an explicit parent-child relationship, not merely a matching product name. The current inventory record was created in 2026, while the parent and child listing records carry older creation dates.

It is possible the current SKU was attached to an existing variation in 2026, or that older data was imported/recreated in inventory. The queried current-state records do not establish which event occurred. There is no attachment timestamp in the parent-child mapping table, and no listing/SKU audit-history table was found by the metadata search. updated_at is not proof of a SKU reassignment date.

Therefore 9 October 2024 is the stored child listing-record creation date, not a verified first-listed date for the present ENC9760 inventory product. The exact SKU attachment/first-listed date remains unverified.

The dashboard adds 5h30 to the listing timestamp and excludes it because it precedes 1 January 2026. This explains Not Listed under the existing reporting rule. However, the current database shows ENC9760 associated with a non-ended variation under an Active parent listing. Live eBay availability was not independently verified.

Listing URL: https://www.ebay.co.uk/itm/265768509380
