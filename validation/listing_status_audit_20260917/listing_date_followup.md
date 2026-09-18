# Listing creation vs inventory creation: follow-up

Rechecked live LEDSone records for all 1,295 dashboard SKUs using SELECT only. No application or dashboard data changed.

- 32 SKUs have no Listed platform in All Data but have pre-2026 listing records passing the other builder rules.
- 20 of those 32 have inventory records created in 2026: the same date pattern as ENC9760. Six appear in the default view; 14 only in All Data.
- The remaining 12 have inventory records created before 2026; they are still excluded because of the listing-date cutoff.
- Across the 32, 31 have a qualifying listing date before their inventory creation date. ENC3408 is the exception: inventory 2024-10-25, listing 2025-02-11. Both precede 2026.
- Across all SKUs, 53 have a 2026 inventory record and a pre-2026 otherwise qualifying listing record. Only 20 have no Listed platform; the other 33 also have qualifying newer listing evidence.
- Across all SKUs, 223 have at least one otherwise qualifying listing whose calendar date precedes inventory creation. This broader count is not a count of incorrect Not Listed statuses.

Dates compared at calendar-day precision: listing timestamps use the existing adapter's +5h30 conversion; inventory timestamps are raw. The pre-2026 versus 2026 cases are not same-day timestamp ambiguities.

These figures count products, not marketplace rows. They establish record-date order and dashboard exclusions, not historical SKU replacement. SKU-change history was not available to prove that each current SKU was attached to its old listing during 2026. They do not independently verify current storefront availability.

The 20 in this follow-up are selected by 2026 inventory creation, not by Active status. The earlier report also counted 20 explicitly active products among the 32; that is a different criterion and should not be conflated with this count.

Files:
- 2026_inventory_older_listing_not_listed.csv: exact 20 matching the ENC9760 date pattern.
- not_listed_older_listing_dates.csv: all 32 date-cutoff cases.
- listing_before_inventory_all.csv: broader date diagnostics.
- listing_date_counts.json: count definitions and results.
