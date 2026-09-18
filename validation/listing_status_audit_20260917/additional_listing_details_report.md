# Additional listing-detail audit — 17 September 2026

Excluded the previously discussed 32 SKUs with wholly Not Listed status and older qualifying listing records. Requeried all dashboard SKU source records with SELECT only. No application code or dashboard data changed.

## Wholly Not Listed: 12 other SKUs

Five have matching parent records excluded by the builder; seven have Amazon raw-SKU matches whose mapped_sku resolves to a different product. These are review cases, not 12 proven code bugs.

| SKU | Platform | Reason | Resolved SKU | Source status |
|---|---|---|---|---|
| LSGL3L150AR | ebay | PARENT_RECORD | LSGL3L150AR | Active |
| LSSC315BI3PK+SPCC320BM3PK | ebay | PARENT_RECORD | LSSC315BI3PK+SPCC320BM3PK | Active |
| PCBM20MX+PCDO20CO+PCBSM2FCO+RW12CO2PK | ebay | PARENT_RECORD | PCBM20MX+PCDO20CO+PCBSM2FCO+RW12CO2PK | Active |
| RBPLTFBC | ebay | PARENT_RECORD | RBPLTFBC | Active |
| SPPGUK3PGD2PK | amazon | SKU_MAPPING_DIFFERENT | SPPGUK3PBR2PK | Inactive |
| SPPGUK3PGD4PK | amazon | SKU_MAPPING_DIFFERENT | SPPGUK3PBR4PK | Inactive |
| SPPGUK3PGD6PK | amazon | SKU_MAPPING_DIFFERENT | SPPGUK3PBR6PK | Inactive |
| WLWOFTWO+LDSST64E274 | amazon | SKU_MAPPING_DIFFERENT | WLWOFTWO+CBSF70+CBSFBM+LDSST64E274 | Inactive |
| WLWOHTBM+LSGL10012AR | amazon | SKU_MAPPING_DIFFERENT | WLWOHTBM+LSGL12010AR+CBSF75 | Inactive |
| WLWOHTBM+LSGL12010AR | amazon | SKU_MAPPING_DIFFERENT | WLWOHTBM+LSGL12010AR+CBSF75 | Inactive |
| WLWOHTBM+LSGL7512CL | amazon | SKU_MAPPING_DIFFERENT | WLWOHTBM+LSGL1275CL | Active |
| WLWOHTBM3PK+LSGL14010CL3PK | ebay | PARENT_RECORD | WLWOHTBM3PK+LSGL14010CL3PK | Active |

Parent details: LSGL3L150AR is a parent for three different child SKUs (LSGL3L150AR+RPM40WH, LSGL3L150AR2PK+RPM40WH2PK, LSGL3L150AR3PK+RPM40WH3PK). Parent activity does not prove a standalone LSGL3L150AR offer. The four other parent-only SKU cases have no child records returned by either the explicit mapping join or same-item-ID query; all five corresponding eBay item records (RBPLTFBC has two) are marked Active and not ended. This may reflect incomplete child ingestion or a parent classification issue, and requires source-system review.

## Partially represented marketplaces

56 additional SKUs have at least one Listed platform but candidate source records on another non-Listed/absent platform. Across all 68 SKUs (12 wholly Not Listed plus 56 partial): 21 have pre-2026 exclusions, 23 have parent exclusions, 28 have different-SKU mappings, and 3 have wrong_sku exclusions. Categories overlap; do not sum them. Exact per-record evidence is in other_listing_platform_gaps.csv. These reasons can be legitimate; they do not establish that every excluded record should be assigned to the SKU.

No source listing meeting all current builder rules was found missing from Listed status. No currently Listed All Data row had a blank platform, listing date, or listing URL. The broader problems are matching semantics, parent handling, reporting-window scope, and source/website consistency.

## Five independently rechecked website variant issues

All five public product JSON endpoints returned HTTP 200. These are individual source URL issues; a SKU may have a valid listing elsewhere.

| Dashboard SKU | Result at stored variant URL |
|---|---|
| ENC2859 | Current website SKU: ENC2859-IDE |
| LDCWA60HE2776PK | Requested variant ID absent from current product variants |
| LSGL3L150AR+RPM40WH | Current website SKU: LSGL3L150AR+RPM40WH_HIT |
| PCCO20WH5PK | Requested variant ID absent from current product variants |
| WLGA400E27BM | Requested variant ID absent from current product variants |

Suffix differences are identity/mapping questions, not automatically proof of a different physical product. They were not silently normalized. Complete URLs and responses are in other_website_variant_recheck.json.

## Files

- other_listing_platform_gaps.csv: 187 source records across 68 SKUs, excluding the original 32.
- listed_missing_details.csv: no blank URL/date/platform findings.
- other_website_variant_recheck.json: five current public variant checks.
