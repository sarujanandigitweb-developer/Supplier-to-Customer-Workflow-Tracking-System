/* Supplier-to-Customer Workflow Tracking — LIVE PostgreSQL snapshot (via Claude MCP)
   Period: 2026-03-01 -> CURRENT_DATE. Captured 2026-07-21. No sample/mock values.
   Regenerate: re-run scratchpad/gen_data.py after refreshing MCP query results. */
window.DASHBOARD_DATA = {
 "meta": {
  "capturedAt": "2026-07-21",
  "periodStart": "2026-03-01",
  "periodEnd": "CURRENT_DATE",
  "periodLabel": "March 01, 2026 \u2192 Today",
  "totalRecordsLoaded": 108341,
  "recordCounts": {
   "componentJourney": 349,
   "purchaseOrders": 99,
   "suppliers": 47,
   "topCombos": 50,
   "topSKUs": 25,
   "marketplaceSample": 32,
   "returnsAmazon": 35,
   "ordersAggregated": 97050,
   "returnLines": 4569,
   "combosCreated": 6274
  },
  "notes": "All values are live PostgreSQL results (MCP snapshot 2026-07-21). Warehouse receive date does not exist; arrival shown via supplier.orders.status_arrived. Impressions/Clicks (traffic_data/ppc_performance) not in this snapshot \u2014 pool closed during pull."
 },
 "kpi": {
  "newComponentsSinceMarch": 349,
  "componentRowsSinceMarch": 1390,
  "combosCreatedSinceMarch": 6274,
  "listedCombosTotal": 16015,
  "nonListedCombosTotal": 8596,
  "suppliers": 47,
  "purchaseOrders": 250,
  "posSinceMarch": 99,
  "containers": 24,
  "finalContainers": 16,
  "orders": 97050,
  "units": 158685,
  "sales": 2304870.01,
  "aov": 23.75,
  "returnsLines": 4569,
  "returnsQtyAmazon": 4258,
  "supplierDefinedCombos": 65,
  "comboLinks": 76,
  "componentsTotal": 1500
 },
 "funnel": [
  {
   "stage": "Supplier",
   "value": 47,
   "view": "suppliers"
  },
  {
   "stage": "Purchase Order",
   "value": 99,
   "view": "suppliers"
  },
  {
   "stage": "Container",
   "value": 24,
   "view": "suppliers"
  },
  {
   "stage": "Component (new)",
   "value": 349,
   "view": "journey"
  },
  {
   "stage": "Combo Created",
   "value": 6274,
   "view": "combos"
  },
  {
   "stage": "Listed",
   "value": 6274,
   "view": "marketplace"
  },
  {
   "stage": "Orders",
   "value": 97050,
   "view": "sales"
  },
  {
   "stage": "Returns",
   "value": 4569,
   "view": "returns"
  }
 ],
 "newComponentsByMonth": [
  {
   "month": "2026-03",
   "count": 115
  },
  {
   "month": "2026-04",
   "count": 11
  },
  {
   "month": "2026-05",
   "count": 76
  },
  {
   "month": "2026-06",
   "count": 98
  },
  {
   "month": "2026-07",
   "count": 49
  }
 ],
 "salesTrend": [
  {
   "month": "2026-03",
   "orders": 24554,
   "sales": 569549.97,
   "units": 39631
  },
  {
   "month": "2026-04",
   "orders": 21429,
   "sales": 500747.32,
   "units": 35686
  },
  {
   "month": "2026-05",
   "orders": 20727,
   "sales": 492602.54,
   "units": 34168
  },
  {
   "month": "2026-06",
   "orders": 18906,
   "sales": 460030.61,
   "units": 30622
  },
  {
   "month": "2026-07",
   "orders": 11434,
   "sales": 281939.57,
   "units": 18578
  }
 ],
 "marketplaceDist": [
  {
   "channel": "shopify",
   "listings": 52659,
   "combos": 13025
  },
  {
   "channel": "amazon",
   "listings": 40734,
   "combos": 18333
  },
  {
   "channel": "ebay",
   "listings": 13946,
   "combos": 15863
  },
  {
   "channel": "B&Q",
   "listings": 3843,
   "combos": 1511
  }
 ],
 "returns": {
  "channel": {
   "amazon": {
    "lines": 3297,
    "qty": 4258
   },
   "ebay": {
    "lines": 906,
    "qty": 1288
   },
   "shopify": {
    "lines": 366,
    "qty": 0
   }
  },
  "linesTotal": 4569,
  "amazonBySku": [
   {
    "sku": "LSCY290YE+RPR44WH-IN",
    "reason": "AMZ-PG-BAD-DESC",
    "qty": 25
   },
   {
    "sku": "LSCY290RE+RPR44WH LS",
    "reason": "CR-MISSING_PARTS",
    "qty": 24
   },
   {
    "sku": "WCCYSP160BM2PK",
    "reason": "CR-NOT_COMPATIBLE",
    "qty": 19
   },
   {
    "sku": "CRFF500BM+PHCH1BMRBM3PK+LSCY210BG3PK T",
    "reason": "CR-DAMAGED_BY_CARRIER",
    "qty": 13
   },
   {
    "sku": "CRSF120BM+WSCH135BM+SCRN70BM+LSFT220RE_S",
    "reason": "CR-DEFECTIVE",
    "qty": 13
   },
   {
    "sku": "ENC6343",
    "reason": "CR-ORDERED_WRONG_ITEM",
    "qty": 13
   },
   {
    "sku": "12UK3P2A",
    "reason": "CR-NOT_COMPATIBLE",
    "qty": 12
   },
   {
    "sku": "G95 4W B22",
    "reason": "CR-QUALITY_UNACCEPTABLE",
    "qty": 10
   },
   {
    "sku": "ENC7859",
    "reason": "CR-UNWANTED_ITEM",
    "qty": 10
   },
   {
    "sku": "ENC8271",
    "reason": "CR-UNWANTED_ITEM",
    "qty": 10
   },
   {
    "sku": "WCCYSP180GD2PK+RPR44WH2PK",
    "reason": "CR-NOT_COMPATIBLE",
    "qty": 10
   },
   {
    "sku": "TSSTYF8012GY",
    "reason": "CR-MISSED_ESTIMATED_DELIVERY",
    "qty": 9
   },
   {
    "sku": "CRSF100BM+PHRYWP1RBM",
    "reason": "CR-UNWANTED_ITEM",
    "qty": 9
   },
   {
    "sku": "CRSF100YB+PHCHPCRYB+LSCY290YB C",
    "reason": "CR-NOT_COMPATIBLE",
    "qty": 9
   },
   {
    "sku": "LSGLSC115AR+RPM40WH",
    "reason": "AMZ-PG-BAD-DESC",
    "qty": 8
   },
   {
    "sku": "ENC8921",
    "reason": "CR-QUALITY_UNACCEPTABLE",
    "qty": 8
   },
   {
    "sku": "CRFF500BM+PHHT1PBRRO3PK+WCWDRO3PK",
    "reason": "CR-MISSING_PARTS",
    "qty": 8
   },
   {
    "sku": "TSWGQBRE+TSLCQB15WH3PK+TSLTRE",
    "reason": "CR-DEFECTIVE",
    "qty": 8
   },
   {
    "sku": "IMRG D",
    "reason": "CR-ORDERED_WRONG_ITEM",
    "qty": 8
   },
   {
    "sku": "LSMS320BG+RPR44WH-IN",
    "reason": "CR-UNWANTED_ITEM",
    "qty": 8
   },
   {
    "sku": "CRSF100BM+PHRNWP1RBM",
    "reason": "CR-NOT_COMPATIBLE",
    "qty": 8
   },
   {
    "sku": "LSCY290BC2PK+RPR44WH2PK",
    "reason": "AMZ-PG-BAD-DESC",
    "qty": 8
   },
   {
    "sku": "LSCP150BA+RPR44WH",
    "reason": "CR-NO_REASON_GIVEN",
    "qty": 7
   },
   {
    "sku": "BC3W50",
    "reason": "CR-NOT_COMPATIBLE",
    "qty": 7
   },
   {
    "sku": "PLHARR+LSOL180RR",
    "reason": "CR-UNWANTED_ITEM",
    "qty": 7
   },
   {
    "sku": "LSCY210BG+RPR44WH G",
    "reason": "CR-NOT_COMPATIBLE",
    "qty": 7
   },
   {
    "sku": "CRSF100BM+PHCHPBRCO+LSCY290CO",
    "reason": "CR-NOT_COMPATIBLE",
    "qty": 7
   },
   {
    "sku": "LHPHE27GB",
    "reason": "AMZ-PG-BAD-DESC",
    "qty": 7
   },
   {
    "sku": "LSCYRO200GD2PK+RPR44WH2PK",
    "reason": "CR-NOT_COMPATIBLE",
    "qty": 7
   },
   {
    "sku": "PHSF1BMRBM+ICST64E27_T",
    "reason": "CR-UNWANTED_ITEM",
    "qty": 7
   },
   {
    "sku": "WCDTBM2PK+RPR44WH2PK",
    "reason": "CR-NOT_COMPATIBLE",
    "qty": 6
   },
   {
    "sku": "PCFT90TBM",
    "reason": "AMZ-PG-BAD-DESC",
    "qty": 6
   },
   {
    "sku": "LDMG95E278APK",
    "reason": "CR-NOT_COMPATIBLE",
    "qty": 6
   },
   {
    "sku": "LSGLULCL+RPM40WH_",
    "reason": "CR-QUALITY_UNACCEPTABLE",
    "qty": 6
   },
   {
    "sku": "LSMS320BG+RPR44WH-IN",
    "reason": "AMZ-PG-BAD-DESC",
    "qty": 6
   }
  ]
 },
 "comboStats": {
  "totalComponents": 1500,
  "componentsUsedSupplierBridge": 66,
  "supplierDefinedCombos": 65,
  "comboLinks": 76,
  "marketplaceCombosCreated": 6274,
  "avgComponentsPerComboSample": 2.4
 },
 "topCombos": [
  {
   "sku": "PHUH1HETBM+LSHM400HE",
   "created": "2026-03-24",
   "marketplaces": 2,
   "orders": 127,
   "sales": 7997.33
  },
  {
   "sku": "LSMS320BG+RPR44WH",
   "created": "2026-03-13",
   "marketplaces": 2,
   "orders": 216,
   "sales": 7123.66
  },
  {
   "sku": "CRFF500BM+PHCH1BMRBM3PK+LSCY210BG3PK",
   "created": "2026-03-31",
   "marketplaces": 2,
   "orders": 102,
   "sales": 5347.84
  },
  {
   "sku": "PHCH1FBRBM+LSCY290BI",
   "created": "2026-05-26",
   "marketplaces": 1,
   "orders": 118,
   "sales": 5247.49
  },
  {
   "sku": "LSCY290BM+RPR44WH",
   "created": "2026-03-02",
   "marketplaces": 1,
   "orders": 214,
   "sales": 5005.57
  },
  {
   "sku": "LSCY290WH+RPR44WH",
   "created": "2026-03-07",
   "marketplaces": 2,
   "orders": 209,
   "sales": 5000.57
  },
  {
   "sku": "CRSF100CH+PHCHPCRCH+LSMS320GR",
   "created": "2026-03-24",
   "marketplaces": 1,
   "orders": 112,
   "sales": 4746.92
  },
  {
   "sku": "WCDTBM2PK+RPR44WH2PK",
   "created": "2026-05-27",
   "marketplaces": 2,
   "orders": 238,
   "sales": 4703.89
  },
  {
   "sku": "LSMS320GR+RPR44WH",
   "created": "2026-07-08",
   "marketplaces": 1,
   "orders": 172,
   "sales": 4325.68
  },
  {
   "sku": "LSCY290BM2PK+RPR44WH2PK",
   "created": "2026-03-24",
   "marketplaces": 3,
   "orders": 123,
   "sales": 4271.73
  },
  {
   "sku": "LSCY290CO+RPR44WH",
   "created": "2026-03-07",
   "marketplaces": 2,
   "orders": 158,
   "sales": 4244.43
  },
  {
   "sku": "LSMS320GY+RPR44WH",
   "created": "2026-03-02",
   "marketplaces": 2,
   "orders": 205,
   "sales": 4219.85
  },
  {
   "sku": "CRSF100BM+PHCH1BMRBM+LSCY290BI",
   "created": "2026-03-17",
   "marketplaces": 1,
   "orders": 89,
   "sales": 3867.65
  },
  {
   "sku": "LSCY290BG+RPR44WH",
   "created": "2026-03-02",
   "marketplaces": 3,
   "orders": 113,
   "sales": 3792.04
  },
  {
   "sku": "LSCY290WH2PK+RPR44WH2PK",
   "created": "2026-03-10",
   "marketplaces": 2,
   "orders": 121,
   "sales": 3716.52
  },
  {
   "sku": "LSSS300RE+RPR44WH",
   "created": "2026-03-02",
   "marketplaces": 3,
   "orders": 61,
   "sales": 3627.47
  },
  {
   "sku": "LSCY290YE+RPR44WH",
   "created": "2026-03-02",
   "marketplaces": 1,
   "orders": 112,
   "sales": 3591.97
  },
  {
   "sku": "LSCY210BG3PK+RPR44WH3PK",
   "created": "2026-03-04",
   "marketplaces": 2,
   "orders": 80,
   "sales": 3433.54
  },
  {
   "sku": "LSMS320WH+RPR44WH",
   "created": "2026-03-11",
   "marketplaces": 1,
   "orders": 145,
   "sales": 3392.02
  },
  {
   "sku": "LSCY210BG+RPR44WH",
   "created": "2026-03-02",
   "marketplaces": 1,
   "orders": 188,
   "sales": 3365.8
  },
  {
   "sku": "LSCY290NB+RPR44WH",
   "created": "2026-03-18",
   "marketplaces": 1,
   "orders": 177,
   "sales": 3358.52
  },
  {
   "sku": "LSCY290OR+RPR44WH",
   "created": "2026-03-02",
   "marketplaces": 2,
   "orders": 147,
   "sales": 3336.08
  },
  {
   "sku": "LSCY290BI+RPR44WH",
   "created": "2026-03-02",
   "marketplaces": 2,
   "orders": 134,
   "sales": 3302.96
  },
  {
   "sku": "CRSF100BM+PHCH1BMRBM+LSCY290BM",
   "created": "2026-03-05",
   "marketplaces": 2,
   "orders": 97,
   "sales": 2991.86
  },
  {
   "sku": "LSCY290GR+RPR44WH",
   "created": "2026-03-02",
   "marketplaces": 1,
   "orders": 113,
   "sales": 2966.73
  },
  {
   "sku": "CRSF100BM3PK+PHSQ1PBRYB3PK+LSSS300GR3PK",
   "created": "2026-03-20",
   "marketplaces": 2,
   "orders": 49,
   "sales": 2933.65
  },
  {
   "sku": "CRSF100BM+PHHT1PBRBM+LSHM400HE",
   "created": "2026-07-05",
   "marketplaces": 1,
   "orders": 45,
   "sales": 2912.81
  },
  {
   "sku": "CRSF100BM+PHCH1BMRBM+LSCY290BG",
   "created": "2026-06-29",
   "marketplaces": 1,
   "orders": 70,
   "sales": 2912.53
  },
  {
   "sku": "CRSF100BM+PHRYWP1RBM",
   "created": "2026-04-09",
   "marketplaces": 3,
   "orders": 124,
   "sales": 2860.4
  },
  {
   "sku": "CRSF100BC+LHNSE27YB+SCRN70BC+LSWD360BC",
   "created": "2026-06-08",
   "marketplaces": 1,
   "orders": 70,
   "sales": 2744.04
  },
  {
   "sku": "CRFF100BM+LHNSE27BM",
   "created": "2026-05-25",
   "marketplaces": 2,
   "orders": 133,
   "sales": 2638.63
  },
  {
   "sku": "CRSF100CH+PHCHPCRCH+LSMS320GY",
   "created": "2026-03-24",
   "marketplaces": 1,
   "orders": 68,
   "sales": 2620.81
  },
  {
   "sku": "LSCY290CB+RPR44WH",
   "created": "2026-06-16",
   "marketplaces": 1,
   "orders": 116,
   "sales": 2546.13
  },
  {
   "sku": "LSCY290YB+RPR44WH",
   "created": "2026-03-07",
   "marketplaces": 2,
   "orders": 85,
   "sales": 2543.27
  },
  {
   "sku": "LSCY290BL+RPR44WH",
   "created": "2026-03-02",
   "marketplaces": 2,
   "orders": 97,
   "sales": 2532.68
  },
  {
   "sku": "LSCY290BC+RPR44WH",
   "created": "2026-03-02",
   "marketplaces": 1,
   "orders": 103,
   "sales": 2522.08
  },
  {
   "sku": "LSCY290GY+RPR44WH",
   "created": "2026-03-02",
   "marketplaces": 1,
   "orders": 130,
   "sales": 2487.92
  },
  {
   "sku": "CRFF100GB+LHNSE27GB",
   "created": "2026-04-06",
   "marketplaces": 3,
   "orders": 128,
   "sales": 2433.2
  },
  {
   "sku": "LSMS320YE+RPR44WH",
   "created": "2026-05-13",
   "marketplaces": 1,
   "orders": 105,
   "sales": 2426.89
  },
  {
   "sku": "LSCY290RE+RPR44WH",
   "created": "2026-03-02",
   "marketplaces": 1,
   "orders": 95,
   "sales": 2317.27
  },
  {
   "sku": "PHUH1HETBM+LSHM300HE",
   "created": "2026-03-09",
   "marketplaces": 3,
   "orders": 40,
   "sales": 2280.45
  },
  {
   "sku": "PSDS2BMRBM+ICST64E27",
   "created": "2026-03-02",
   "marketplaces": 2,
   "orders": 62,
   "sales": 2127.11
  },
  {
   "sku": "CRSF100CH+PHCHPCRCH+LSMS320WH",
   "created": "2026-03-24",
   "marketplaces": 1,
   "orders": 54,
   "sales": 2098.76
  },
  {
   "sku": "CRFF500BM+PHRI1PBRYB3PK+LSFT220BM3PK",
   "created": "2026-05-20",
   "marketplaces": 2,
   "orders": 61,
   "sales": 2065.19
  },
  {
   "sku": "WCB7WH+RPR44WH",
   "created": "2026-07-07",
   "marketplaces": 1,
   "orders": 158,
   "sales": 2011.97
  },
  {
   "sku": "CRSF100YB+PHCHPCRYB+LSCY290YB",
   "created": "2026-05-08",
   "marketplaces": 1,
   "orders": 24,
   "sales": 2006.99
  },
  {
   "sku": "CRFF500BM+PHCH1BMRBM3PK+LSDO210BG3PK",
   "created": "2026-07-15",
   "marketplaces": 1,
   "orders": 52,
   "sales": 1995.51
  },
  {
   "sku": "CRSF100CO+LHNSE27CO+SCRN70CO+LSTF40CO",
   "created": "2026-03-18",
   "marketplaces": 1,
   "orders": 55,
   "sales": 1994.82
  },
  {
   "sku": "CRSF100GB+PHCHPBRGB+LSCY290GB",
   "created": "2026-03-11",
   "marketplaces": 1,
   "orders": 35,
   "sales": 1986.48
  },
  {
   "sku": "LSMS320BI2PK+RPR44WH2PK",
   "created": "2026-05-05",
   "marketplaces": 1,
   "orders": 67,
   "sales": 1981.66
  }
 ],
 "topSKUs": [
  {
   "sku": "TPOSBDBM",
   "orders": 466,
   "sales": 10966.11,
   "units": 474,
   "isCombo": false
  },
  {
   "sku": "PLADBC",
   "orders": 189,
   "sales": 10741.88,
   "units": 235,
   "isCombo": false
  },
  {
   "sku": "PLADBM",
   "orders": 194,
   "sales": 10082.52,
   "units": 215,
   "isCombo": false
  },
  {
   "sku": "PHUH1HETBM+LSHM400HE",
   "orders": 127,
   "sales": 7997.33,
   "units": 212,
   "isCombo": true
  },
  {
   "sku": "LSMS320BG+RPR44WH",
   "orders": 216,
   "sales": 7123.66,
   "units": 338,
   "isCombo": true
  },
  {
   "sku": "LDMG125E278",
   "orders": 428,
   "sales": 7087.48,
   "units": 720,
   "isCombo": false
  },
  {
   "sku": "LDMST64E274",
   "orders": 594,
   "sales": 6547.7,
   "units": 1590,
   "isCombo": false
  },
  {
   "sku": "LDMST64E2786PK",
   "orders": 265,
   "sales": 5866.22,
   "units": 354,
   "isCombo": false
  },
  {
   "sku": "CL3THEAPK",
   "orders": 193,
   "sales": 5631.05,
   "units": 261,
   "isCombo": false
  },
  {
   "sku": "ENC685",
   "orders": 94,
   "sales": 5423.96,
   "units": 105,
   "isCombo": false
  },
  {
   "sku": "ENC1991",
   "orders": 39,
   "sales": 5368.49,
   "units": 50,
   "isCombo": false
  },
  {
   "sku": "CRFF500BM+PHCH1BMRBM3PK+LSCY210BG3PK",
   "orders": 102,
   "sales": 5347.84,
   "units": 122,
   "isCombo": true
  },
  {
   "sku": "PHCH1FBRBM+LSCY290BI",
   "orders": 118,
   "sales": 5247.49,
   "units": 199,
   "isCombo": true
  },
  {
   "sku": "LSCY290BM+RPR44WH",
   "orders": 214,
   "sales": 5005.57,
   "units": 298,
   "isCombo": true
  },
  {
   "sku": "LSCY290WH+RPR44WH",
   "orders": 209,
   "sales": 5000.57,
   "units": 286,
   "isCombo": true
  },
  {
   "sku": "ENC3550",
   "orders": 39,
   "sales": 4990.86,
   "units": 50,
   "isCombo": false
  },
  {
   "sku": "CRSF100CH+PHCHPCRCH+LSMS320GR",
   "orders": 112,
   "sales": 4746.92,
   "units": 159,
   "isCombo": true
  },
  {
   "sku": "LDMG95E278APK",
   "orders": 102,
   "sales": 4737.44,
   "units": 122,
   "isCombo": false
  },
  {
   "sku": "LSMS320BI+RPR44WH",
   "orders": 152,
   "sales": 4721.37,
   "units": 294,
   "isCombo": true
  },
  {
   "sku": "WCDTBM2PK+RPR44WH2PK",
   "orders": 238,
   "sales": 4703.89,
   "units": 256,
   "isCombo": true
  },
  {
   "sku": "12IP67100",
   "orders": 166,
   "sales": 4694.57,
   "units": 235,
   "isCombo": false
  },
  {
   "sku": "ENC686",
   "orders": 80,
   "sales": 4621.95,
   "units": 86,
   "isCombo": false
  },
  {
   "sku": "LSMS320GR+RPR44WH",
   "orders": 172,
   "sales": 4325.68,
   "units": 270,
   "isCombo": true
  },
  {
   "sku": "LSCY290BM2PK+RPR44WH2PK",
   "orders": 123,
   "sales": 4271.73,
   "units": 147,
   "isCombo": true
  },
  {
   "sku": "LSCY290CO+RPR44WH",
   "orders": 158,
   "sales": 4244.43,
   "units": 219,
   "isCombo": true
  }
 ],
 "marketplaceSample": [
  [
   "amzn.gr.CRSF100CO_PHSH1PBRCO_L-3K-4DL-LN",
   "amazon",
   "UK",
   "Listed",
   "2026-07-21",
   0,
   1,
   0
  ],
  [
   "amzn.gr.CRFF105GB2PK_HK10GB2PK-5rYuyJ-VG",
   "amazon",
   "UK",
   "Listed",
   "2026-07-21",
   0,
   1,
   0
  ],
  [
   "ENC10239",
   "shopify",
   "Germany",
   "Listed",
   "2026-07-20",
   1,
   0,
   0
  ],
  [
   "ENC10173",
   "shopify",
   "Germany",
   "Listed",
   "2026-07-20",
   1,
   0,
   0
  ],
  [
   "ENC10176",
   "shopify",
   "France",
   "Listed",
   "2026-07-20",
   1,
   0,
   0
  ],
  [
   "WJBSQIP683BM",
   "shopify",
   "UK",
   "Listed",
   "2026-07-20",
   1,
   0,
   0
  ],
  [
   "WJBIP683BM",
   "shopify",
   "UK",
   "Listed",
   "2026-07-20",
   1,
   0,
   0
  ],
  [
   "WJBIP686BM",
   "shopify",
   "UK",
   "Listed",
   "2026-07-20",
   1,
   0,
   0
  ],
  [
   "WJBIP685BM",
   "shopify",
   "UK",
   "Listed",
   "2026-07-20",
   1,
   0,
   0
  ],
  [
   "WJBIP684BM",
   "shopify",
   "UK",
   "Listed",
   "2026-07-20",
   1,
   0,
   0
  ],
  [
   "WLGCH85E27BM",
   "ebay",
   "Germany",
   "Listed",
   "2026-07-20",
   1,
   0,
   0
  ],
  [
   "WLGCH73E27BM",
   "ebay",
   "Germany",
   "Listed",
   "2026-07-20",
   1,
   0,
   0
  ],
  [
   "LHCTOBM",
   "shopify",
   "France",
   "Listed",
   "2026-07-20",
   1,
   0,
   0
  ],
  [
   "LHCTOWH",
   "shopify",
   "France",
   "Listed",
   "2026-07-20",
   1,
   0,
   0
  ],
  [
   "WSNWBS+LSCY290BS+LDMST64E274_HDE",
   "amazon",
   "Germany",
   "Listed",
   "2026-07-20",
   1,
   0,
   0
  ],
  [
   "WSNWBC+LSCY290BC+LDMST64E274_HDE",
   "amazon",
   "Germany",
   "Listed",
   "2026-07-20",
   1,
   0,
   0
  ],
  [
   "WSNWBM+LSCY290BM+LDMST64E274_HDE",
   "amazon",
   "Germany",
   "Listed",
   "2026-07-20",
   1,
   0,
   0
  ],
  [
   "WSNWBC+LSHQ180BC+ICST64E27_HDE",
   "amazon",
   "Germany",
   "Listed",
   "2026-07-20",
   1,
   0,
   0
  ],
  [
   "WSNWBC+LSUL220BC+LDMG95E274_HDE",
   "amazon",
   "Germany",
   "Listed",
   "2026-07-20",
   1,
   0,
   0
  ],
  [
   "WSNWBM+LSHQ180BM+ICST64E27_HDE",
   "amazon",
   "Germany",
   "Listed",
   "2026-07-20",
   1,
   0,
   0
  ],
  [
   "ENC5747",
   "amazon",
   "Ireland",
   "Listed",
   "2026-07-20",
   1,
   0,
   0
  ],
  [
   "LSGLULAR2PK+RPM40WH2PK_HDE",
   "amazon",
   "Germany",
   "Listed",
   "2026-07-20",
   1,
   0,
   0
  ],
  [
   "PLADBM_HDE",
   "amazon",
   "Germany",
   "Listed",
   "2026-07-20",
   1,
   0,
   0
  ],
  [
   "PLADBC_HDE",
   "amazon",
   "Germany",
   "Listed",
   "2026-07-20",
   1,
   0,
   0
  ],
  [
   "WLGM108E27BM",
   "ebay",
   "Germany",
   "Listed",
   "2026-07-20",
   1,
   0,
   0
  ],
  [
   "WLGG105E27BM",
   "ebay",
   "Germany",
   "Listed",
   "2026-07-20",
   1,
   0,
   0
  ],
  [
   "WLGM115E27BM",
   "ebay",
   "Germany",
   "Listed",
   "2026-07-20",
   1,
   0,
   0
  ],
  [
   "WLGS110E27BM",
   "ebay",
   "Germany",
   "Listed",
   "2026-07-20",
   1,
   0,
   0
  ],
  [
   "LSFT220BM2PK+RPR44WH2PK",
   "ebay",
   "UK",
   "Listed",
   "2026-07-20",
   1,
   0,
   0
  ],
  [
   "LSFT220BG2PK+RPR44WH2PK",
   "ebay",
   "UK",
   "Listed",
   "2026-07-20",
   1,
   0,
   0
  ],
  [
   "LSSS300BS+RPR44WH",
   "shopify",
   "UK",
   "Listed",
   "2026-07-20",
   1,
   0,
   0
  ],
  [
   "LHC4E27WH5PK",
   "ebay",
   "UK",
   "Listed",
   "2026-07-20",
   1,
   0,
   0
  ]
 ],
 "suppliers": [
  [
   "Cable Supplier",
   "CAB",
   12,
   233,
   6,
   12
  ],
  [
   "Assembling lady 1",
   "AL1",
   16,
   226,
   8,
   11
  ],
  [
   "Ceiling rose guy",
   "CRG",
   15,
   125,
   6,
   13
  ],
  [
   "Brushed Curvy Supplier",
   "BRC",
   16,
   107,
   10,
   13
  ],
  [
   "Assembling Lady 2",
   "AL2",
   18,
   98,
   10,
   14
  ],
  [
   "Condieut pipelight accessoies",
   "CND",
   6,
   86,
   3,
   4
  ],
  [
   "Different type of wire cage",
   "DWC",
   11,
   60,
   4,
   11
  ],
  [
   "Pipe lightning Supplier",
   "PLS",
   9,
   59,
   5,
   9
  ],
  [
   "Multi colour shade supplier",
   "MCS",
   10,
   55,
   3,
   9
  ],
  [
   "Multi colour curvy shade supplier",
   "MCY",
   19,
   49,
   5,
   13
  ],
  [
   "Bulbs supplier",
   "BBS",
   16,
   48,
   7,
   15
  ],
  [
   "Celing Rose Lady",
   "CRL",
   8,
   47,
   3,
   7
  ],
  [
   "Transformer HN Supplier",
   "THN",
   7,
   39,
   3,
   6
  ],
  [
   "Barrel Cage Supplier",
   "BRL",
   7,
   32,
   5,
   7
  ],
  [
   "Connector Supplier",
   "CON",
   6,
   30,
   0,
   6
  ],
  [
   "Glass shade 2 Supplier",
   "GL2",
   1,
   22,
   0,
   0
  ],
  [
   "Transformer SM Supplier",
   "TSM",
   4,
   21,
   2,
   4
  ],
  [
   "AM packing",
   "AMP",
   8,
   19,
   3,
   8
  ],
  [
   "Hemp Supplier",
   "HEM",
   8,
   18,
   3,
   8
  ],
  [
   "Bakelite holders",
   "BKH",
   2,
   18,
   0,
   1
  ],
  [
   "Led Induction module supplier",
   "LDI",
   3,
   17,
   1,
   3
  ],
  [
   "New Bulb Supplier",
   "NBS",
   1,
   13,
   0,
   1
  ],
  [
   "BI Chandelier Supplier",
   "BCA",
   1,
   12,
   1,
   1
  ],
  [
   "Black and white Tranformer supplier",
   "TBW",
   4,
   11,
   1,
   4
  ],
  [
   "PVC lamp holder",
   "PVC",
   2,
   11,
   0,
   2
  ],
  [
   "Warehouse mechine supplier",
   "WMS",
   1,
   8,
   0,
   0
  ],
  [
   "Adapters",
   "ADP",
   2,
   8,
   1,
   2
  ],
  [
   "Handle Supplier",
   "HAN",
   3,
   8,
   2,
   3
  ],
  [
   "Mosaic Lighting Supplier",
   "MSL",
   5,
   8,
   2,
   5
  ],
  [
   "Warehouse needed things",
   "WHN",
   3,
   7,
   1,
   2
  ],
  [
   "Ceiling Bracket",
   "CBR",
   1,
   7,
   0,
   1
  ],
  [
   "Electro plating Supplier",
   "ELP",
   2,
   7,
   1,
   2
  ],
  [
   "New Bubble bag supplier",
   "NBB",
   2,
   7,
   0,
   1
  ],
  [
   "Transformer NG Supplier",
   "TNG",
   2,
   7,
   0,
   2
  ],
  [
   "Plugin Pendent Supplier",
   "PPS",
   1,
   6,
   0,
   1
  ],
  [
   "Glass shade supplier",
   "GLS",
   4,
   6,
   1,
   4
  ],
  [
   "Chain Supplier",
   "CHN",
   1,
   5,
   1,
   1
  ],
  [
   "New clear glass supplier",
   "NCG",
   2,
   5,
   0,
   2
  ],
  [
   "Transformer Blue and Orange Supplier",
   "TBO",
   2,
   4,
   0,
   2
  ],
  [
   "New Pendent light",
   "NPL",
   1,
   4,
   1,
   1
  ],
  [
   "New Lamp Holder",
   "NLH",
   1,
   4,
   0,
   1
  ],
  [
   "Black shade with border gold line supplier",
   "BGL",
   3,
   4,
   0,
   3
  ],
  [
   "Ceiling Fan 2 Supplier",
   "CFS2",
   1,
   3,
   0,
   0
  ],
  [
   "Ceiling Fan Supplier",
   "CFS",
   1,
   3,
   0,
   0
  ],
  [
   "New Wall light Supplier",
   "NWS",
   1,
   2,
   0,
   1
  ],
  [
   "New Pendant supplier",
   "NPS",
   1,
   1,
   0,
   0
  ],
  [
   "Sensor light supplier",
   "SEN",
   0,
   0,
   0,
   0
  ]
 ],
 "purchaseOrders": [
  [
   "New Bubble bag supplier",
   "NBB072026",
   null,
   "In Transit",
   "2026-07-20",
   null,
   null
  ],
  [
   "Multi colour curvy shade supplier",
   "MCY072026",
   null,
   "In Transit",
   "2026-07-20",
   "2026-08-20",
   null
  ],
  [
   "Warehouse mechine supplier",
   "WMS072026",
   null,
   "In Transit",
   "2026-07-16",
   null,
   "2026-07-19"
  ],
  [
   "New clear glass supplier",
   "NCG072026-02",
   "Container 07 2026",
   "In Transit",
   "2026-07-15",
   null,
   null
  ],
  [
   "Assembling Lady 2",
   "AL2072026-02",
   "Container 07 2026",
   "In Transit",
   "2026-07-15",
   "2026-08-31",
   null
  ],
  [
   "Barrel Cage Supplier",
   "BRL072026-02",
   "Container 07 2026",
   "In Transit",
   "2026-07-15",
   null,
   null
  ],
  [
   "Ceiling rose guy",
   "CRG072026-02",
   "Container 07 2026",
   "In Transit",
   "2026-07-15",
   null,
   null
  ],
  [
   "Hemp Supplier",
   "HEM072026-02",
   "Container 07 2026",
   "In Transit",
   "2026-07-15",
   null,
   null
  ],
  [
   "Transformer HN Supplier",
   "THN072026",
   "Container 06 2026",
   "In Transit",
   "2026-07-15",
   null,
   null
  ],
  [
   "PVC lamp holder",
   "PVC072026",
   "Container 06 2026",
   "In Transit",
   "2026-07-15",
   null,
   null
  ],
  [
   "Different type of wire cage",
   "DWC072026",
   "Container 06 2026",
   "In Transit",
   "2026-07-15",
   null,
   null
  ],
  [
   "Black and white Tranformer supplier",
   "TBW072026",
   "Container 06 2026",
   "In Transit",
   "2026-07-15",
   null,
   null
  ],
  [
   "Brushed Curvy Supplier",
   "BRC072026",
   "Container 06 2026",
   "In Transit",
   "2026-07-15",
   "2026-08-08",
   null
  ],
  [
   "Cable Supplier",
   "CAB072026-02",
   "Container 07 2026",
   "In Transit",
   "2026-07-15",
   "2026-07-31",
   null
  ],
  [
   "Mosaic Lighting Supplier",
   "MSL072026-02",
   "Container 07 2026",
   "In Transit",
   "2026-07-15",
   null,
   null
  ],
  [
   "Black shade with border gold line supplier",
   "BGL072026",
   "Container 06 2026",
   "In Transit",
   "2026-07-15",
   null,
   null
  ],
  [
   "Bulbs supplier",
   "BBS072026",
   "Container 06 2026",
   "In Transit",
   "2026-07-15",
   null,
   null
  ],
  [
   "AM packing",
   "AMP072026",
   "Container 06 2026",
   "In Transit",
   "2026-07-15",
   null,
   null
  ],
  [
   "Multi colour curvy shade supplier",
   "MCY062026",
   "Container 05 2026",
   "In Transit",
   "2026-07-06",
   "2026-08-06",
   null
  ],
  [
   "Ceiling rose guy",
   "CRG062026",
   "Container 05 2026",
   "In Transit",
   "2026-07-06",
   "2026-08-04",
   null
  ],
  [
   "Different type of wire cage",
   "DWC062026",
   "Container 05 2026",
   "In Transit",
   "2026-07-06",
   null,
   null
  ],
  [
   "Hemp Supplier",
   "HEM062026",
   "Container 05 2026",
   "In Transit",
   "2026-07-06",
   "2026-08-31",
   null
  ],
  [
   "Assembling lady 1",
   "AL1062026-02",
   "Container 05 2026",
   "In Transit",
   "2026-07-06",
   null,
   null
  ],
  [
   "Assembling Lady 2",
   "AL2062026",
   "Container 05 2026",
   "In Transit",
   "2026-07-06",
   "2026-08-30",
   null
  ],
  [
   "AM packing",
   "AMP062026",
   "Container 05 2026",
   "In Transit",
   "2026-07-06",
   "2026-07-31",
   null
  ],
  [
   "Connector Supplier",
   "CON062026",
   "Container 05 2026",
   "In Transit",
   "2026-07-06",
   "2026-07-31",
   null
  ],
  [
   "Assembling lady 1",
   "AL1062026",
   null,
   "In Transit",
   "2026-06-18",
   null,
   null
  ],
  [
   "Condieut pipelight accessoies",
   "CND062026",
   null,
   "In Transit",
   "2026-06-10",
   null,
   "2026-06-18"
  ],
  [
   "New clear glass supplier",
   "NCG062026",
   "Container 04 2026",
   "In Transit",
   "2026-06-04",
   null,
   null
  ],
  [
   "Glass shade 2 Supplier",
   "GL2052026",
   null,
   "In Transit",
   "2026-06-04",
   "2026-05-15",
   "2026-05-14"
  ],
  [
   "Assembling Lady 2",
   "AL2052026-02",
   "Container 04 2026",
   "In Transit",
   "2026-06-03",
   "2026-07-08",
   null
  ],
  [
   "Bulbs supplier",
   "BBS052026",
   "Container 04 2026",
   "In Transit",
   "2026-06-01",
   null,
   null
  ],
  [
   "Assembling lady 1",
   "AL1052026",
   "Container 04 2026",
   "In Transit",
   "2026-06-01",
   "2026-07-16",
   null
  ],
  [
   "New Lamp Holder",
   "NLH052026",
   "Container 04 2026",
   "In Transit",
   "2026-06-01",
   null,
   null
  ],
  [
   "Led Induction module supplier",
   "LDI052026",
   "Container 04 2026",
   "In Transit",
   "2026-06-01",
   "2026-06-29",
   "2026-07-01"
  ],
  [
   "Pipe lightning Supplier",
   "PLS052026",
   "Container 04 2026",
   "In Transit",
   "2026-06-01",
   "2026-07-15",
   null
  ],
  [
   "Ceiling rose guy",
   "CRG052026",
   "Container 04 2026",
   "In Transit",
   "2026-06-01",
   "2026-07-15",
   null
  ],
  [
   "Cable Supplier",
   "CAB052026",
   "Container 04 2026",
   "In Transit",
   "2026-06-01",
   "2026-06-28",
   "2026-07-03"
  ],
  [
   "Brushed Curvy Supplier",
   "BRC052026",
   "Container 04 2026",
   "In Transit",
   "2026-06-01",
   "2026-07-05",
   "2026-07-01"
  ],
  [
   "Assembling Lady 2",
   "AL2052026",
   "Container 04 2026",
   "In Transit",
   "2026-06-01",
   "2026-07-15",
   null
  ],
  [
   "Ceiling rose guy",
   "CRG052026-DE",
   "DE Container 02 2026",
   "In Transit",
   "2026-05-22",
   null,
   null
  ],
  [
   "AM packing",
   "AMP052026-DE",
   "DE Container 02 2026",
   "In Transit",
   "2026-05-22",
   "2026-06-02",
   "2026-06-08"
  ],
  [
   "Assembling Lady 2",
   "AL2052026-DE",
   "DE Container 02 2026",
   "In Transit",
   "2026-05-22",
   "2026-06-22",
   "2026-07-14"
  ],
  [
   "Assembling lady 1",
   "AL1052026-DE",
   "DE Container 02 2026",
   "In Transit",
   "2026-05-22",
   "2026-06-30",
   "2026-07-14"
  ],
  [
   "Black and white Tranformer supplier",
   "TBW052026-DE",
   "DE Container 02 2026",
   "In Transit",
   "2026-05-22",
   "2026-06-30",
   "2026-07-16"
  ],
  [
   "Transformer Blue and Orange Supplier",
   "TBO052026-DE",
   "DE Container 02 2026",
   "In Transit",
   "2026-05-22",
   null,
   null
  ],
  [
   "Brushed Curvy Supplier",
   "BRC052026-DE",
   "DE Container 02 2026",
   "In Transit",
   "2026-05-22",
   "2026-06-12",
   "2026-06-10"
  ],
  [
   "Bulbs supplier",
   "BBS052026-DE",
   "DE Container 02 2026",
   "In Transit",
   "2026-05-22",
   null,
   null
  ],
  [
   "Cable Supplier",
   "CAB052026-DE",
   "DE Container 02 2026",
   "In Transit",
   "2026-05-22",
   "2026-06-20",
   "2026-06-30"
  ],
  [
   "Celing Rose Lady",
   "CRL052026-DE",
   "DE Container 02 2026",
   "In Transit",
   "2026-05-22",
   "2026-05-22",
   "2026-06-17"
  ],
  [
   "Connector Supplier",
   "CON052026-DE",
   "DE Container 02 2026",
   "In Transit",
   "2026-05-22",
   null,
   null
  ],
  [
   "Hemp Supplier",
   "HEM052026-DE",
   "DE Container 02 2026",
   "In Transit",
   "2026-05-22",
   "2026-07-31",
   null
  ],
  [
   "Led Induction module supplier",
   "LDI052026-DE",
   "DE Container 02 2026",
   "In Transit",
   "2026-05-22",
   "2026-06-29",
   "2026-07-01"
  ],
  [
   "Multi colour curvy shade supplier",
   "MCY052026-DE",
   "DE Container 02 2026",
   "In Transit",
   "2026-05-22",
   "2026-06-25",
   "2026-06-30"
  ],
  [
   "Multi colour shade supplier",
   "MCS052026-DE",
   "DE Container 02 2026",
   "In Transit",
   "2026-05-22",
   "2026-07-10",
   "2026-07-14"
  ],
  [
   "Pipe lightning Supplier",
   "PLS052026-DE",
   "DE Container 02 2026",
   "In Transit",
   "2026-05-22",
   "2026-06-20",
   "2026-06-26"
  ],
  [
   "Transformer HN Supplier",
   "THN052026-DE",
   "DE Container 02 2026",
   "In Transit",
   "2026-05-22",
   null,
   "2026-06-18"
  ],
  [
   "Transformer NG Supplier",
   "TNG052026-DE",
   "DE Container 02 2026",
   "In Transit",
   "2026-05-22",
   "2026-05-30",
   "2026-05-29"
  ],
  [
   "Transformer SM Supplier",
   "TSM052026-DE",
   "DE Container 02 2026",
   "In Transit",
   "2026-05-22",
   "2026-05-31",
   "2026-07-14"
  ],
  [
   "New Pendant supplier",
   "NPS052026",
   null,
   "In Transit",
   "2026-05-20",
   null,
   "2026-05-21"
  ],
  [
   "Ceiling Fan 2 Supplier",
   "CFS2052026",
   null,
   "In Transit",
   "2026-05-11",
   "2026-06-15",
   "2026-06-30"
  ],
  [
   "Ceiling Fan Supplier",
   "CFS052026",
   null,
   "In Transit",
   "2026-05-11",
   "2026-05-20",
   "2026-06-11"
  ],
  [
   "Condieut pipelight accessoies",
   "CND042026",
   "Container 03 2026",
   "In Transit",
   "2026-05-07",
   "2026-06-19",
   null
  ],
  [
   "Hemp Supplier",
   "HEM042026",
   "Container 03 2026",
   "In Transit",
   "2026-05-07",
   "2026-06-30",
   "2026-06-30"
  ],
  [
   "Ceiling rose guy",
   "CRG042026",
   "Container 03 2026",
   "In Transit",
   "2026-05-07",
   null,
   null
  ],
  [
   "Mosaic Lighting Supplier",
   "MSL042026",
   "Container 03 2026",
   "In Transit",
   "2026-05-07",
   "2026-06-06",
   "2026-06-08"
  ],
  [
   "Different type of wire cage",
   "DWC042026",
   "Container 03 2026",
   "In Transit",
   "2026-05-07",
   "2026-07-01",
   "2026-07-01"
  ],
  [
   "Multi colour curvy shade supplier",
   "MCY042026",
   null,
   "In Transit",
   "2026-04-24",
   "2026-05-26",
   "2026-06-08"
  ],
  [
   "Warehouse needed things",
   "WHN 04 2026",
   null,
   "In Transit",
   "2026-04-02",
   null,
   null
  ],
  [
   "Assembling lady 1",
   "AL1022026-2",
   "Container 01 2026",
   "In Transit",
   "2026-03-31",
   "2026-05-23",
   "2026-03-31"
  ],
  [
   "Barrel Cage Supplier",
   "BRL032026",
   "Container 02 2026",
   "In Transit",
   "2026-03-31",
   null,
   "2026-05-11"
  ],
  [
   "Connector Supplier",
   "CON032026",
   "Container 02 2026",
   "In Transit",
   "2026-03-31",
   "2026-04-17",
   "2026-04-20"
  ],
  [
   "Hemp Supplier",
   "HEM032026",
   "Container 02 2026",
   "In Transit",
   "2026-03-31",
   "2026-05-16",
   "2026-05-15"
  ],
  [
   "Different type of wire cage",
   "DWC032026",
   "Container 02 2026",
   "In Transit",
   "2026-03-31",
   "2026-06-18",
   "2026-05-21"
  ],
  [
   "Multi colour shade supplier",
   "MCS032026",
   "Container 02 2026",
   "In Transit",
   "2026-03-31",
   "2026-04-30",
   "2026-05-06"
  ],
  [
   "Multi colour curvy shade supplier",
   "MCY032026-02",
   "Container 02 2026",
   "In Transit",
   "2026-03-31",
   "2026-04-30",
   "2026-05-14"
  ],
  [
   "Pipe lightning Supplier",
   "PLS032026",
   "Container 02 2026",
   "In Transit",
   "2026-03-31",
   "2026-05-15",
   "2026-05-16"
  ],
  [
   "Bulbs supplier",
   "BBS032026-02",
   "Container 02 2026",
   "In Transit",
   "2026-03-30",
   "2026-04-20",
   "2026-05-07"
  ],
  [
   "Multi colour curvy shade supplier",
   "MCY032026",
   "Container 01 2026",
   "In Transit",
   "2026-03-27",
   "2026-04-10",
   "2026-05-14"
  ],
  [
   "Celing Rose Lady",
   "CRL032026-02",
   "Container 01 2026",
   "In Transit",
   "2026-03-24",
   "2026-03-25",
   "2026-03-25"
  ],
  [
   "AM packing",
   "AMP122025",
   "Container 17",
   "In Transit",
   "2026-03-19",
   "2026-03-19",
   "2026-04-08"
  ],
  [
   "Assembling Lady 2",
   "AL2122025",
   "Container 16",
   "In Transit",
   "2026-03-19",
   "2026-04-29",
   "2026-05-12"
  ],
  [
   "Transformer Blue and Orange Supplier",
   "TBO032026DE",
   "DE Container 01 2026",
   "In Transit",
   "2026-03-18",
   "2026-04-26",
   "2026-05-22"
  ],
  [
   "Transformer HN Supplier",
   "THN032026DE",
   "DE Container 01 2026",
   "In Transit",
   "2026-03-18",
   null,
   "2026-05-09"
  ],
  [
   "Multi colour curvy shade supplier",
   "MCY032026-DE",
   "DE Container 01 2026",
   "In Transit",
   "2026-03-18",
   "2026-04-08",
   "2026-04-28"
  ],
  [
   "Brushed Curvy Supplier",
   "BRC032026-DE",
   "DE Container 01 2026",
   "In Transit",
   "2026-03-18",
   "2026-04-06",
   "2026-04-06"
  ],
  [
   "Assembling lady 1",
   "AL1032026-DE",
   "DE Container 01 2026",
   "In Transit",
   "2026-03-18",
   "2026-04-30",
   "2026-05-04"
  ],
  [
   "Assembling Lady 2",
   "AL2032026-DE",
   "DE Container 01 2026",
   "In Transit",
   "2026-03-18",
   "2026-07-18",
   "2026-06-11"
  ],
  [
   "Condieut pipelight accessoies",
   "CND032026",
   "Container 01 2026",
   "In Transit",
   "2026-03-18",
   null,
   "2026-03-19"
  ],
  [
   "Bakelite holders",
   "BKH032026",
   "Container 01 2026",
   "In Transit",
   "2026-03-12",
   "2026-04-01",
   "2026-04-08"
  ],
  [
   "Assembling lady 1",
   "AL1122025-2",
   "Container 17",
   "In Transit",
   "2026-03-12",
   null,
   "2026-03-12"
  ],
  [
   "Celing Rose Lady",
   "CRL032026",
   "Container 01 2026",
   "In Transit",
   "2026-03-10",
   "2026-04-20",
   "2026-05-14"
  ],
  [
   "Assembling Lady 2",
   "AL2032026",
   "Container 01 2026",
   "In Transit",
   "2026-03-10",
   "2026-05-05",
   "2026-06-08"
  ],
  [
   "Handle Supplier",
   "HAN032026",
   "Container 01 2026",
   "In Transit",
   "2026-03-10",
   null,
   "2026-04-28"
  ],
  [
   "Bulbs supplier",
   "BBS 03 2026",
   "Container 01 2026",
   "In Transit",
   "2026-03-10",
   "2026-04-15",
   "2026-04-15"
  ],
  [
   "Ceiling rose guy",
   "CRG032026",
   "Container 01 2026",
   "In Transit",
   "2026-03-10",
   null,
   "2026-06-03"
  ],
  [
   "Glass shade supplier",
   "GLS 03 2026",
   "Container 01 2026",
   "In Transit",
   "2026-03-10",
   "2026-04-13",
   "2026-04-28"
  ],
  [
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "In Transit",
   "2026-03-10",
   "2026-04-11",
   "2026-06-08"
  ],
  [
   "Brushed Curvy Supplier",
   "BRC032026",
   "Container 01 2026",
   "In Transit",
   "2026-03-10",
   "2026-04-06",
   "2026-04-06"
  ]
 ],
 "componentJourney": [
  [
   "ITEM-527-1784547314644",
   "50 X 20 cm height Roll",
   "New Bubble bag supplier",
   "NBB072026",
   "\u2014",
   "2026-07-20",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "ITEM-527-1784547254364",
   "50 x 40CM height Roll",
   "New Bubble bag supplier",
   "NBB072026",
   "\u2014",
   "2026-07-20",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "ITEM-524-1784195741193",
   "LIFTING AND TRANSPLANTING MACHINE\nD700-L758*W696",
   "Warehouse mechine supplier",
   "WMS072026",
   "\u2014",
   "2026-07-16",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "ITEM-524-1784195539697",
   "LABEL PRINTER &LABEL PASTING MACHINE\nTB-DT400D",
   "Warehouse mechine supplier",
   "WMS072026",
   "\u2014",
   "2026-07-16",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "ITEM-524-1784195447577",
   "90 DEGREE CONVEYOR\nRCV90",
   "Warehouse mechine supplier",
   "WMS072026",
   "\u2014",
   "2026-07-16",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "ITEM-524-1784195363466",
   "MOTOR-DRIVE ROLLOR CONVEROR\nRC1M/D",
   "Warehouse mechine supplier",
   "WMS072026",
   "\u2014",
   "2026-07-16",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "ITEM-524-1784195257113",
   "NON-DRIVE ROLLOR CONVEROR\nRC1M",
   "Warehouse mechine supplier",
   "WMS072026",
   "\u2014",
   "2026-07-16",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "ITEM-524-1784195154467",
   "SIDE SEALER\nAS723",
   "Warehouse mechine supplier",
   "WMS072026",
   "\u2014",
   "2026-07-16",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "ITEM-524-1784195105269",
   "CARTON SEALER\nFX-AT5050",
   "Warehouse mechine supplier",
   "WMS072026",
   "\u2014",
   "2026-07-16",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "ITEM-524-1784194757243",
   "CARTON ERECTOR\nCES4035",
   "Warehouse mechine supplier",
   "WMS072026",
   "\u2014",
   "2026-07-16",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "CL2RBK",
   "2Core round 100m roll",
   "Cable Supplier",
   "CAB072026-02",
   "Container 07 2026",
   "2026-07-15",
   0,
   4,
   "Listed",
   "Listed"
  ],
  [
   "LHNSE27SN",
   "Short holder with extension",
   "Cable Supplier",
   "CAB072026-02",
   "Container 07 2026",
   "2026-07-15",
   79,
   2,
   "Listed",
   "Selling"
  ],
  [
   "LHNSE27WH",
   "Short holder with extension",
   "Cable Supplier",
   "CAB072026-02",
   "Container 07 2026",
   "2026-07-15",
   118,
   2,
   "Listed",
   "Selling"
  ],
  [
   "LSGL12010AR",
   "",
   "New clear glass supplier",
   "NCG072026-02",
   "Container 07 2026",
   "2026-07-15",
   4,
   0,
   "Not Listed",
   "Has Combo"
  ],
  [
   "LSGL14010CL",
   "",
   "New clear glass supplier",
   "NCG072026-02",
   "Container 07 2026",
   "2026-07-15",
   2,
   0,
   "Not Listed",
   "Has Combo"
  ],
  [
   "LSGL14023SG",
   "",
   "New clear glass supplier",
   "NCG072026-02",
   "Container 07 2026",
   "2026-07-15",
   3,
   0,
   "Not Listed",
   "Has Combo"
  ],
  [
   "LSGLULAR",
   "",
   "New clear glass supplier",
   "NCG072026-02",
   "Container 07 2026",
   "2026-07-15",
   3,
   0,
   "Not Listed",
   "Has Combo"
  ],
  [
   "LSGLULCL",
   "",
   "New clear glass supplier",
   "NCG072026-02",
   "Container 07 2026",
   "2026-07-15",
   3,
   1,
   "Listed",
   "Selling"
  ],
  [
   "PHSF1AGRGB",
   "1m round   Army green cable+ Green brass ceiling",
   "Assembling Lady 2",
   "AL2072026-02",
   "Container 07 2026",
   "2026-07-15",
   8,
   4,
   "Listed",
   "Selling"
  ],
  [
   "CRFF100SN",
   "100x25 Front fittings",
   "Ceiling rose guy",
   "CRG072026-02",
   "Container 07 2026",
   "2026-07-15",
   18,
   3,
   "Listed",
   "Selling"
  ],
  [
   "CRFF65SN",
   "",
   "Ceiling rose guy",
   "CRG072026-02",
   "Container 07 2026",
   "2026-07-15",
   8,
   1,
   "Listed",
   "Selling"
  ],
  [
   "CRSF100HYB",
   "100*25",
   "Ceiling rose guy",
   "CRG072026-02",
   "Container 07 2026",
   "2026-07-15",
   2,
   1,
   "Listed",
   "Selling"
  ],
  [
   "CRSF100LFG",
   "",
   "Ceiling rose guy",
   "CRG072026-02",
   "Container 07 2026",
   "2026-07-15",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "CRSF108WH",
   "108 Side fitting ceiling rose",
   "Ceiling rose guy",
   "CRG072026-02",
   "Container 07 2026",
   "2026-07-15",
   15,
   4,
   "Listed",
   "Selling"
  ],
  [
   "CRSF125CO",
   "",
   "Ceiling rose guy",
   "CRG072026-02",
   "Container 07 2026",
   "2026-07-15",
   3,
   2,
   "Listed",
   "Selling"
  ],
  [
   "LSDO300SN",
   "300*150",
   "Ceiling rose guy",
   "CRG072026-02",
   "Container 07 2026",
   "2026-07-15",
   43,
   2,
   "Listed",
   "Selling"
  ],
  [
   "LSDO300YB",
   "300*150",
   "Ceiling rose guy",
   "CRG072026-02",
   "Container 07 2026",
   "2026-07-15",
   39,
   1,
   "Listed",
   "Selling"
  ],
  [
   "PHHRE2HETX2HE",
   "2m   hemp",
   "Hemp Supplier",
   "HEM072026-02",
   "Container 07 2026",
   "2026-07-15",
   0,
   1,
   "Listed",
   "Listed"
  ],
  [
   "PHUH1HETBM",
   "1m",
   "Hemp Supplier",
   "HEM072026-02",
   "Container 07 2026",
   "2026-07-15",
   486,
   4,
   "Listed",
   "Selling"
  ],
  [
   "PHUH2HETBM",
   "2m",
   "Hemp Supplier",
   "HEM072026-02",
   "Container 07 2026",
   "2026-07-15",
   202,
   4,
   "Listed",
   "Selling"
  ],
  [
   "24IP6724",
   "24v24w Waterproof",
   "Transformer HN Supplier",
   "THN072026",
   "Container 06 2026",
   "2026-07-15",
   0,
   3,
   "Listed",
   "Listed"
  ],
  [
   "LHXSHE27BM",
   "",
   "PVC lamp holder",
   "PVC072026",
   "Container 06 2026",
   "2026-07-15",
   0,
   1,
   "Listed",
   "Listed"
  ],
  [
   "WCDTBL",
   "open hole 4cm",
   "Different type of wire cage",
   "DWC072026",
   "Container 06 2026",
   "2026-07-15",
   28,
   1,
   "Listed",
   "Selling"
  ],
  [
   "WCFRE3LNPYBM",
   "",
   "Different type of wire cage",
   "DWC072026",
   "Container 06 2026",
   "2026-07-15",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "WCFRO3WDPYBM",
   "",
   "Different type of wire cage",
   "DWC072026",
   "Container 06 2026",
   "2026-07-15",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "LSCO335WH",
   "330*90mm",
   "Brushed Curvy Supplier",
   "BRC072026",
   "Container 06 2026",
   "2026-07-15",
   4,
   1,
   "Listed",
   "Selling"
  ],
  [
   "LSCY290AA",
   "290 round",
   "Brushed Curvy Supplier",
   "BRC072026",
   "Container 06 2026",
   "2026-07-15",
   25,
   2,
   "Listed",
   "Selling"
  ],
  [
   "LSHH240BG",
   "",
   "Brushed Curvy Supplier",
   "BRC072026",
   "Container 06 2026",
   "2026-07-15",
   6,
   1,
   "Listed",
   "Selling"
  ],
  [
   "LSHH240BM",
   "",
   "Brushed Curvy Supplier",
   "BRC072026",
   "Container 06 2026",
   "2026-07-15",
   41,
   2,
   "Listed",
   "Selling"
  ],
  [
   "LSOL180BB",
   "180*100\u8d8a\u5357\u5e3d",
   "Brushed Curvy Supplier",
   "BRC072026",
   "Container 06 2026",
   "2026-07-15",
   24,
   2,
   "Listed",
   "Selling"
  ],
  [
   "LSOL180RR",
   "180*100\u8d8a\u5357\u5e3d",
   "Brushed Curvy Supplier",
   "BRC072026",
   "Container 06 2026",
   "2026-07-15",
   39,
   2,
   "Listed",
   "Selling"
  ],
  [
   "PHHF1PBRBC",
   "",
   "Brushed Curvy Supplier",
   "BRC072026",
   "Container 06 2026",
   "2026-07-15",
   6,
   0,
   "Not Listed",
   "Has Combo"
  ],
  [
   "PHHF1PBRBM",
   "",
   "Brushed Curvy Supplier",
   "BRC072026",
   "Container 06 2026",
   "2026-07-15",
   6,
   0,
   "Not Listed",
   "Has Combo"
  ],
  [
   "CRSF100GS",
   "",
   "Black shade with border gold line supplier",
   "BGL072026",
   "Container 06 2026",
   "2026-07-15",
   81,
   1,
   "Listed",
   "Selling"
  ],
  [
   "LDMA60B224WW",
   "",
   "Bulbs supplier",
   "BBS072026",
   "Container 06 2026",
   "2026-07-15",
   0,
   1,
   "Listed",
   "Listed"
  ],
  [
   "LDMT185E273",
   "",
   "Bulbs supplier",
   "BBS072026",
   "Container 06 2026",
   "2026-07-15",
   0,
   3,
   "Listed",
   "Listed"
  ],
  [
   "LDSG125XMSE274",
   "",
   "Bulbs supplier",
   "BBS072026",
   "Container 06 2026",
   "2026-07-15",
   0,
   4,
   "Listed",
   "Listed"
  ],
  [
   "PHDH1HETHE",
   "1m double head",
   "AM packing",
   "AMP072026",
   "Container 06 2026",
   "2026-07-15",
   6,
   4,
   "Listed",
   "Selling"
  ],
  [
   "PHUH2HE3TBM",
   "",
   "AM packing",
   "AMP072026",
   "Container 06 2026",
   "2026-07-15",
   7,
   3,
   "Listed",
   "Selling"
  ],
  [
   "PSOS4BMTHE",
   "",
   "AM packing",
   "AMP072026",
   "Container 06 2026",
   "2026-07-15",
   12,
   3,
   "Listed",
   "Selling"
  ],
  [
   "WSLR200BM",
   "",
   "AM packing",
   "AMP072026",
   "Container 06 2026",
   "2026-07-15",
   58,
   4,
   "Listed",
   "Selling"
  ],
  [
   "PHCH1PWRSGR",
   "1m",
   "Multi colour curvy shade supplier",
   "MCY062026",
   "Container 05 2026",
   "2026-07-06",
   33,
   0,
   "Not Listed",
   "Has Combo"
  ],
  [
   "LHLAE2715DBM",
   "",
   "Assembling lady 1",
   "AL1062026-02",
   "Container 05 2026",
   "2026-07-06",
   0,
   1,
   "Listed",
   "Listed"
  ],
  [
   "LHTMGU10CH",
   "",
   "Assembling lady 1",
   "AL1062026-02",
   "Container 05 2026",
   "2026-07-06",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "LHTMGU10SN",
   "",
   "Assembling lady 1",
   "AL1062026-02",
   "Container 05 2026",
   "2026-07-06",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "LHTTAGU10WH",
   "",
   "Assembling lady 1",
   "AL1062026-02",
   "Container 05 2026",
   "2026-07-06",
   4,
   3,
   "Listed",
   "Selling"
  ],
  [
   "LHTTE2730BM",
   "",
   "Assembling lady 1",
   "AL1062026-02",
   "Container 05 2026",
   "2026-07-06",
   2,
   1,
   "Listed",
   "Selling"
  ],
  [
   "LHTTE27WH",
   "",
   "Assembling lady 1",
   "AL1062026-02",
   "Container 05 2026",
   "2026-07-06",
   5,
   2,
   "Listed",
   "Selling"
  ],
  [
   "PHCT80YBCYB",
   "",
   "Assembling lady 1",
   "AL1062026-02",
   "Container 05 2026",
   "2026-07-06",
   0,
   3,
   "Listed",
   "Listed"
  ],
  [
   "PHHCF1BMRBM",
   "",
   "Assembling lady 1",
   "AL1062026-02",
   "Container 05 2026",
   "2026-07-06",
   1,
   4,
   "Listed",
   "Selling"
  ],
  [
   "PHHCF1BMRYB",
   "",
   "Assembling lady 1",
   "AL1062026-02",
   "Container 05 2026",
   "2026-07-06",
   1,
   3,
   "Listed",
   "Selling"
  ],
  [
   "PHHT1PBRGD",
   "1m 3 Core PVC cable",
   "Assembling lady 1",
   "AL1062026-02",
   "Container 05 2026",
   "2026-07-06",
   12,
   0,
   "Not Listed",
   "Has Combo"
  ],
  [
   "PHMU1PBRCO",
   "Note :We have to send this cups to assembling la",
   "Assembling lady 1",
   "AL1062026-02",
   "Container 05 2026",
   "2026-07-06",
   14,
   0,
   "Not Listed",
   "Has Combo"
  ],
  [
   "PHRB1PBR40BM",
   "Black pvc cable and holder and cord grip 40mm",
   "Assembling lady 1",
   "AL1062026-02",
   "Container 05 2026",
   "2026-07-06",
   31,
   1,
   "Listed",
   "Selling"
  ],
  [
   "PHUP1PBRYB",
   "3 core pvc 1m Yellow brass cable",
   "Assembling lady 1",
   "AL1062026-02",
   "Container 05 2026",
   "2026-07-06",
   15,
   0,
   "Not Listed",
   "Has Combo"
  ],
  [
   "RPM40WH",
   "",
   "Assembling lady 1",
   "AL1062026-02",
   "Container 05 2026",
   "2026-07-06",
   47,
   2,
   "Listed",
   "Selling"
  ],
  [
   "SPHEBM",
   "",
   "Assembling lady 1",
   "AL1062026-02",
   "Container 05 2026",
   "2026-07-06",
   3,
   2,
   "Listed",
   "Selling"
  ],
  [
   "WSFSRO",
   "",
   "Assembling lady 1",
   "AL1062026-02",
   "Container 05 2026",
   "2026-07-06",
   7,
   1,
   "Listed",
   "Selling"
  ],
  [
   "WSNW170BM",
   "Need to send this wall scone to assembling lady",
   "Assembling lady 1",
   "AL1062026-02",
   "Container 05 2026",
   "2026-07-06",
   125,
   1,
   "Listed",
   "Selling"
  ],
  [
   "WSTR135BM",
   "",
   "Assembling lady 1",
   "AL1062026-02",
   "Container 05 2026",
   "2026-07-06",
   142,
   0,
   "Not Listed",
   "Has Combo"
  ],
  [
   "LHNDE27CO",
   "30cm cable with Short holder with extension",
   "Assembling Lady 2",
   "AL2062026",
   "Container 05 2026",
   "2026-07-06",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "PHRY1PCRWH",
   "",
   "Assembling Lady 2",
   "AL2062026",
   "Container 05 2026",
   "2026-07-06",
   2,
   1,
   "Listed",
   "Selling"
  ],
  [
   "PHHRE1HETHE",
   "3 core hemp rope",
   "AM packing",
   "AMP062026",
   "Container 05 2026",
   "2026-07-06",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "SPSSDBM",
   "S hook",
   "AM packing",
   "AMP062026",
   "Container 05 2026",
   "2026-07-06",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "CO33PWH",
   "",
   "Connector Supplier",
   "CON062026",
   "Container 05 2026",
   "2026-07-06",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "CO532AGY",
   "",
   "Connector Supplier",
   "CON062026",
   "Container 05 2026",
   "2026-07-06",
   0,
   2,
   "Listed",
   "Listed"
  ],
  [
   "CODCCR",
   "",
   "Connector Supplier",
   "CON062026",
   "Container 05 2026",
   "2026-07-06",
   6,
   3,
   "Listed",
   "Selling"
  ],
  [
   "CODL232AGY",
   "2 way",
   "Connector Supplier",
   "CON062026",
   "Container 05 2026",
   "2026-07-06",
   0,
   2,
   "Listed",
   "Listed"
  ],
  [
   "COWP4W3CBM",
   "",
   "Connector Supplier",
   "CON062026",
   "Container 05 2026",
   "2026-07-06",
   0,
   3,
   "Listed",
   "Listed"
  ],
  [
   "COY9ABM",
   "",
   "Connector Supplier",
   "CON062026",
   "Container 05 2026",
   "2026-07-06",
   0,
   4,
   "Listed",
   "Listed"
  ],
  [
   "WJBIP68T12BM",
   "",
   "Connector Supplier",
   "CON062026",
   "Container 05 2026",
   "2026-07-06",
   0,
   3,
   "Listed",
   "Listed"
  ],
  [
   "WJBIP68T14BM",
   "",
   "Connector Supplier",
   "CON062026",
   "Container 05 2026",
   "2026-07-06",
   0,
   3,
   "Listed",
   "Listed"
  ],
  [
   "CRFF100YB",
   "100x25 Front fittings",
   "Ceiling rose guy",
   "CRG062026",
   "Container 05 2026",
   "2026-07-06",
   7,
   3,
   "Listed",
   "Selling"
  ],
  [
   "CRFF140BC",
   "",
   "Ceiling rose guy",
   "CRG062026",
   "Container 05 2026",
   "2026-07-06",
   16,
   3,
   "Listed",
   "Selling"
  ],
  [
   "LSRP260GB",
   "260*160",
   "Ceiling rose guy",
   "CRG062026",
   "Container 05 2026",
   "2026-07-06",
   31,
   3,
   "Listed",
   "Selling"
  ],
  [
   "PCFTLBM",
   "",
   "Assembling lady 1",
   "AL1062026",
   "\u2014",
   "2026-06-18",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "PCFTLCF",
   "",
   "Assembling lady 1",
   "AL1062026",
   "\u2014",
   "2026-06-18",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "PCFTLYB",
   "",
   "Assembling lady 1",
   "AL1062026",
   "\u2014",
   "2026-06-18",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "SPCA70BM",
   "",
   "Assembling lady 1",
   "AL1062026",
   "\u2014",
   "2026-06-18",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "CBSF95NA",
   "",
   "Condieut pipelight accessoies",
   "CND062026",
   "\u2014",
   "2026-06-18",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "CRSP1PRC48BM",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "CRSP1PRC66BM",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "CRSP2PRC48BM",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "CRSP2PRC66BM",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "LH2HTE27YB",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "LHF3HT40BM",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "LHF3HT40WH",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "LHLHTE27YB",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "LHMHTE27YB",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "LHTHT30GD",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "LHTHT50CF",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "LHTHT50GD",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "LHTT10150BG",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "LHTT10200BG",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "LHTT10250BG",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "LHTT15E27CF",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "LHTT15E27GD",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "LHTT30E27GD",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "LHTT50E27GD",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "LHTTAGU10CO",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   2,
   "Listed",
   "Listed"
  ],
  [
   "LSCASN3BCL",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "LSCASN5BCL",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "PCFT1E27BM",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "PCFT1E27BS",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "PCFT45E27BM",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "PCFT45E27BS",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "PCWPLH1BM",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "PCWPLH35BM",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "PHCH1PWRSWH",
   "1m white pvc cable",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   55,
   0,
   "Not Listed",
   "Has Combo"
  ],
  [
   "PHTC1PGTGD",
   "1m",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "TPFHTWB12BM",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "TPFHTWB12SN",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "TPFHTWB12WH",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "WS1SHWHBM",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "WSHTB3P16GD",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "WSLS10CFGD",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "WSLSH68YBBM",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "WSLSH68YBCF",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "WSLSH68YBGD",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "WSSH68CFYB",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "WSSH68YBBM",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "WSSH68YBGD",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "WSUSHE27BM",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "WSUSHE27CO",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "WSUSHE27WH",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-06-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "PCCR6030CH",
   "",
   "Condieut pipelight accessoies",
   "CND062026",
   "\u2014",
   "2026-06-10",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "PCCR6030CO",
   "",
   "Condieut pipelight accessoies",
   "CND062026",
   "\u2014",
   "2026-06-10",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "PCCR6030SN",
   "",
   "Condieut pipelight accessoies",
   "CND062026",
   "\u2014",
   "2026-06-10",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "PCCR6030YB",
   "",
   "Condieut pipelight accessoies",
   "CND062026",
   "\u2014",
   "2026-06-10",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "RD42",
   "",
   "Condieut pipelight accessoies",
   "CND062026",
   "\u2014",
   "2026-06-10",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "SPCR60603CH",
   "",
   "Condieut pipelight accessoies",
   "CND062026",
   "\u2014",
   "2026-06-10",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "SPCR60605CH",
   "",
   "Condieut pipelight accessoies",
   "CND062026",
   "\u2014",
   "2026-06-10",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "CGCYBM",
   "",
   "Assembling lady 1",
   "AL1052026",
   "Container 04 2026",
   "2026-06-01",
   1,
   1,
   "Listed",
   "Selling"
  ],
  [
   "CGCYSN",
   "",
   "Assembling lady 1",
   "AL1052026",
   "Container 04 2026",
   "2026-06-01",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "LHTMGU10BM",
   "",
   "Assembling lady 1",
   "AL1052026",
   "Container 04 2026",
   "2026-06-01",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "WSSS70SN",
   "",
   "Assembling lady 1",
   "AL1052026",
   "Container 04 2026",
   "2026-06-01",
   25,
   2,
   "Listed",
   "Selling"
  ],
  [
   "SPPGUK3PBM",
   "",
   "New Lamp Holder",
   "NLH052026",
   "Container 04 2026",
   "2026-06-01",
   0,
   1,
   "Listed",
   "Listed"
  ],
  [
   "SPPGUK3PBR",
   "",
   "New Lamp Holder",
   "NLH052026",
   "Container 04 2026",
   "2026-06-01",
   0,
   1,
   "Listed",
   "Listed"
  ],
  [
   "SPPGUK3PTR",
   "",
   "New Lamp Holder",
   "NLH052026",
   "Container 04 2026",
   "2026-06-01",
   0,
   1,
   "Listed",
   "Listed"
  ],
  [
   "SPPGUK3PWH",
   "",
   "New Lamp Holder",
   "NLH052026",
   "Container 04 2026",
   "2026-06-01",
   5,
   1,
   "Listed",
   "Selling"
  ],
  [
   "IMRG",
   "6915 RGB",
   "Led Induction module supplier",
   "LDI052026",
   "Container 04 2026",
   "2026-06-01",
   0,
   3,
   "Listed",
   "Listed"
  ],
  [
   "PLHNBM",
   "",
   "Pipe lightning Supplier",
   "PLS052026",
   "Container 04 2026",
   "2026-06-01",
   2,
   3,
   "Listed",
   "Selling"
  ],
  [
   "PLWEFBC",
   "",
   "Pipe lightning Supplier",
   "PLS052026",
   "Container 04 2026",
   "2026-06-01",
   1,
   3,
   "Listed",
   "Selling"
  ],
  [
   "PLWERR",
   "",
   "Pipe lightning Supplier",
   "PLS052026",
   "Container 04 2026",
   "2026-06-01",
   13,
   2,
   "Listed",
   "Selling"
  ],
  [
   "CRSF100HCO",
   "100*25 3hole ceiling rose",
   "Ceiling rose guy",
   "CRG052026",
   "Container 04 2026",
   "2026-06-01",
   5,
   1,
   "Listed",
   "Selling"
  ],
  [
   "CL2RBR5PK",
   "2core Round 5m roll",
   "Cable Supplier",
   "CAB052026",
   "Container 04 2026",
   "2026-06-01",
   0,
   4,
   "Listed",
   "Listed"
  ],
  [
   "CL2RLB",
   "2Core round 100m roll",
   "Cable Supplier",
   "CAB052026",
   "Container 04 2026",
   "2026-06-01",
   0,
   3,
   "Listed",
   "Listed"
  ],
  [
   "CL2RWHAPK",
   "2core Round 10m roll",
   "Cable Supplier",
   "CAB052026",
   "Container 04 2026",
   "2026-06-01",
   0,
   3,
   "Listed",
   "Listed"
  ],
  [
   "CL3RGR",
   "3 Core round 100m roll",
   "Cable Supplier",
   "CAB052026",
   "Container 04 2026",
   "2026-06-01",
   1,
   4,
   "Listed",
   "Selling"
  ],
  [
   "CL3TBD",
   "3core Twist 100m roll",
   "Cable Supplier",
   "CAB052026",
   "Container 04 2026",
   "2026-06-01",
   0,
   4,
   "Listed",
   "Listed"
  ],
  [
   "CL3TIVAPK",
   "3core Twist 10m roll",
   "Cable Supplier",
   "CAB052026",
   "Container 04 2026",
   "2026-06-01",
   0,
   3,
   "Listed",
   "Listed"
  ],
  [
   "CL3TLG",
   "3core Twist 100m roll",
   "Cable Supplier",
   "CAB052026",
   "Container 04 2026",
   "2026-06-01",
   0,
   4,
   "Listed",
   "Listed"
  ],
  [
   "CL3TLP",
   "3core Twist 100m roll",
   "Cable Supplier",
   "CAB052026",
   "Container 04 2026",
   "2026-06-01",
   0,
   4,
   "Listed",
   "Listed"
  ],
  [
   "CL3TOR",
   "3core Twist 100m roll",
   "Cable Supplier",
   "CAB052026",
   "Container 04 2026",
   "2026-06-01",
   1,
   4,
   "Listed",
   "Selling"
  ],
  [
   "LHNSE27BY",
   "Short holder with extension",
   "Cable Supplier",
   "CAB052026",
   "Container 04 2026",
   "2026-06-01",
   85,
   3,
   "Listed",
   "Selling"
  ],
  [
   "LSEL400WH",
   "400*180mm",
   "Brushed Curvy Supplier",
   "BRC052026",
   "Container 04 2026",
   "2026-06-01",
   5,
   0,
   "Not Listed",
   "Has Combo"
  ],
  [
   "LSTF40BM",
   "220x40mm",
   "Brushed Curvy Supplier",
   "BRC052026",
   "Container 04 2026",
   "2026-06-01",
   79,
   3,
   "Listed",
   "Selling"
  ],
  [
   "PHCH1PBRBS",
   "",
   "Brushed Curvy Supplier",
   "BRC052026",
   "Container 04 2026",
   "2026-06-01",
   130,
   0,
   "Not Listed",
   "Has Combo"
  ],
  [
   "PHHF1PBRBS",
   "",
   "Brushed Curvy Supplier",
   "BRC052026",
   "Container 04 2026",
   "2026-06-01",
   5,
   0,
   "Not Listed",
   "Has Combo"
  ],
  [
   "LQDO",
   "LQ-DO",
   "Bulbs supplier",
   "BBS052026",
   "Container 04 2026",
   "2026-06-01",
   0,
   3,
   "Listed",
   "Listed"
  ],
  [
   "LQDR3",
   "LQ-DR-3",
   "Bulbs supplier",
   "BBS052026",
   "Container 04 2026",
   "2026-06-01",
   0,
   3,
   "Listed",
   "Listed"
  ],
  [
   "LQK",
   "LQ-K",
   "Bulbs supplier",
   "BBS052026",
   "Container 04 2026",
   "2026-06-01",
   2,
   3,
   "Listed",
   "Selling"
  ],
  [
   "WLFS220YBG",
   "",
   "Assembling Lady 2",
   "AL2052026",
   "Container 04 2026",
   "2026-06-01",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "12IP20100",
   "12V IP20 100W  8.5A",
   "Transformer SM Supplier",
   "TSM052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   0,
   3,
   "Listed",
   "Listed"
  ],
  [
   "24IP20240",
   "24V IP20 240W 10A",
   "Transformer SM Supplier",
   "TSM052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   0,
   4,
   "Listed",
   "Listed"
  ],
  [
   "24IP20400",
   "24V IP20 400W 16.5A",
   "Transformer SM Supplier",
   "TSM052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   0,
   4,
   "Listed",
   "Listed"
  ],
  [
   "12IP2012",
   "12v IP20 12W 1A",
   "Transformer NG Supplier",
   "TNG052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   0,
   3,
   "Listed",
   "Listed"
  ],
  [
   "12IP2040",
   "12V IP20 40W 3.2A",
   "Transformer NG Supplier",
   "TNG052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   0,
   3,
   "Listed",
   "Listed"
  ],
  [
   "12IP20600",
   "12v 50a 600w IP20",
   "Transformer HN Supplier",
   "THN052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   0,
   4,
   "Listed",
   "Listed"
  ],
  [
   "12IP67120OL2",
   "",
   "Transformer HN Supplier",
   "THN052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   0,
   4,
   "Listed",
   "Listed"
  ],
  [
   "12IP67250",
   "12v IP67 250w waterproo",
   "Transformer HN Supplier",
   "THN052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   0,
   4,
   "Listed",
   "Listed"
  ],
  [
   "PHSH1PBRBB",
   "",
   "Pipe lightning Supplier",
   "PLS052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   17,
   0,
   "Not Listed",
   "Has Combo"
  ],
  [
   "PHSH1PBRBC",
   "",
   "Pipe lightning Supplier",
   "PLS052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   43,
   0,
   "Not Listed",
   "Has Combo"
  ],
  [
   "PHSH1PBRBS",
   "",
   "Pipe lightning Supplier",
   "PLS052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   44,
   0,
   "Not Listed",
   "Has Combo"
  ],
  [
   "PLHABC",
   "",
   "Pipe lightning Supplier",
   "PLS052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   28,
   3,
   "Listed",
   "Selling"
  ],
  [
   "PLTABC",
   "",
   "Pipe lightning Supplier",
   "PLS052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   9,
   3,
   "Listed",
   "Selling"
  ],
  [
   "PLTABM",
   "",
   "Pipe lightning Supplier",
   "PLS052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   13,
   3,
   "Listed",
   "Selling"
  ],
  [
   "LSBS160GR",
   "",
   "Multi colour shade supplier",
   "MCS052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   13,
   3,
   "Listed",
   "Selling"
  ],
  [
   "LSBS160RE",
   "",
   "Multi colour shade supplier",
   "MCS052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   18,
   3,
   "Listed",
   "Selling"
  ],
  [
   "LSCP150BU",
   "",
   "Multi colour shade supplier",
   "MCS052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   18,
   0,
   "Not Listed",
   "Has Combo"
  ],
  [
   "LSCP150GY",
   "",
   "Multi colour shade supplier",
   "MCS052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   23,
   0,
   "Not Listed",
   "Has Combo"
  ],
  [
   "LSHQ150BM",
   "",
   "Multi colour shade supplier",
   "MCS052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   21,
   2,
   "Listed",
   "Selling"
  ],
  [
   "CMWH",
   "COB Cool white",
   "Led Induction module supplier",
   "LDI052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   0,
   2,
   "Listed",
   "Listed"
  ],
  [
   "IMRE",
   "SMD Red",
   "Led Induction module supplier",
   "LDI052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   0,
   3,
   "Listed",
   "Listed"
  ],
  [
   "CRFF108GB",
   "Green Brass 108mm",
   "Celing Rose Lady",
   "CRL052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   22,
   3,
   "Listed",
   "Selling"
  ],
  [
   "CRFF2009BM",
   "9 Outlet Black 200mm",
   "Celing Rose Lady",
   "CRL052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   0,
   3,
   "Listed",
   "Listed"
  ],
  [
   "CRSF1204BM",
   "4 Outlet Black 120x25mm",
   "Celing Rose Lady",
   "CRL052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   30,
   3,
   "Listed",
   "Selling"
  ],
  [
   "SCRN70GB",
   "BIG golden screw",
   "Ceiling rose guy",
   "CRG052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   35,
   3,
   "Listed",
   "Selling"
  ],
  [
   "CL2RAG",
   "2Core round 100m roll",
   "Cable Supplier",
   "CAB052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   0,
   4,
   "Listed",
   "Listed"
  ],
  [
   "CL2RGD",
   "2Core round 100m roll",
   "Cable Supplier",
   "CAB052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   0,
   4,
   "Listed",
   "Listed"
  ],
  [
   "CL2RGL",
   "2Core round 100m roll",
   "Cable Supplier",
   "CAB052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   0,
   4,
   "Listed",
   "Listed"
  ],
  [
   "CL3RCR",
   "3 Core round 100m roll",
   "Cable Supplier",
   "CAB052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   1,
   4,
   "Listed",
   "Selling"
  ],
  [
   "LHSHE27RO",
   "Short holder",
   "Cable Supplier",
   "CAB052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   9,
   4,
   "Listed",
   "Selling"
  ],
  [
   "LDSG125MUE274",
   "G125-RDS-4W-MUSIC-AMBER-E27",
   "Bulbs supplier",
   "BBS052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   2,
   4,
   "Listed",
   "Selling"
  ],
  [
   "LSCY210BS",
   "21cm Shade only",
   "Brushed Curvy Supplier",
   "BRC052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   29,
   1,
   "Listed",
   "Selling"
  ],
  [
   "LSLC180BC",
   "",
   "Brushed Curvy Supplier",
   "BRC052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   27,
   1,
   "Listed",
   "Selling"
  ],
  [
   "12BO18",
   "18w Blue and Orange case",
   "Transformer Blue and Orange Supplier",
   "TBO052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   0,
   4,
   "Listed",
   "Listed"
  ],
  [
   "12BO28",
   "28w Blue and Orange case",
   "Transformer Blue and Orange Supplier",
   "TBO052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   0,
   3,
   "Listed",
   "Listed"
  ],
  [
   "12BO48",
   "48W Blue and Orange case",
   "Transformer Blue and Orange Supplier",
   "TBO052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   0,
   4,
   "Listed",
   "Listed"
  ],
  [
   "12BO72",
   "72w Blue and Orange case",
   "Transformer Blue and Orange Supplier",
   "TBO052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   0,
   4,
   "Listed",
   "Listed"
  ],
  [
   "CCBKNWE50",
   "37-50W black & white transformer",
   "Black and white Tranformer supplier",
   "TBW052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   0,
   4,
   "Listed",
   "Listed"
  ],
  [
   "PHSH2PBRYB",
   "2m Black PVC cabe 3Core + Yellow Brass Holder",
   "Assembling lady 1",
   "AL1052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   118,
   1,
   "Listed",
   "Selling"
  ],
  [
   "WSRH230CO",
   "",
   "Assembling lady 1",
   "AL1052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   16,
   0,
   "Not Listed",
   "Has Combo"
  ],
  [
   "WSSS70CH",
   "short Arm short 2cm rod holder",
   "Assembling lady 1",
   "AL1052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   10,
   2,
   "Listed",
   "Selling"
  ],
  [
   "WSSS70GB",
   "short Arm short 2cm rod holder",
   "Assembling lady 1",
   "AL1052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   13,
   2,
   "Listed",
   "Selling"
  ],
  [
   "PHHR1DSTHE",
   "",
   "AM packing",
   "AMP052026-DE",
   "DE Container 02 2026",
   "2026-05-22",
   4,
   4,
   "Listed",
   "Selling"
  ],
  [
   "ITEM-462-1779277506815",
   "",
   "New Pendant supplier",
   "NPS052026",
   "\u2014",
   "2026-05-20",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "CFRGB420WH",
   "POWA 2.0 IR/CCT ICRGB White",
   "Ceiling Fan 2 Supplier",
   "CFS2052026",
   "\u2014",
   "2026-05-20",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "CFRGB460WH",
   "D46 Fanora Fan IRCCT ICRGB",
   "Ceiling Fan 2 Supplier",
   "CFS2052026",
   "\u2014",
   "2026-05-20",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "CFRGB480WH",
   "D48 CCT+ICRGB Starry",
   "Ceiling Fan 2 Supplier",
   "CFS2052026",
   "\u2014",
   "2026-05-20",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "CF3B46BM",
   "MODEL: ZY1173,MOTOR: DC-35W,SIZE: 46,INCH,BLADE:",
   "Ceiling Fan Supplier",
   "CFS052026",
   "\u2014",
   "2026-05-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "CF3B52BM",
   "MODEL: ZY1301\nMOTOR: DC-40W\nSIZE: 52 INCH\nBLADE:",
   "Ceiling Fan Supplier",
   "CFS052026",
   "\u2014",
   "2026-05-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "CF3BL52WO",
   "MODEL: ZY1296\nSIZE: 52 INCH\nMOTOR: DC-35W\nBLADE:",
   "Ceiling Fan Supplier",
   "CFS052026",
   "\u2014",
   "2026-05-11",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "WCDSBM",
   "",
   "Different type of wire cage",
   "DWC042026",
   "Container 03 2026",
   "2026-05-07",
   9,
   1,
   "Listed",
   "Selling"
  ],
  [
   "LHCTOCH",
   "",
   "Condieut pipelight accessoies",
   "CND042026",
   "Container 03 2026",
   "2026-05-07",
   0,
   4,
   "Listed",
   "Listed"
  ],
  [
   "LHPOE27BM",
   "",
   "Condieut pipelight accessoies",
   "CND042026",
   "Container 03 2026",
   "2026-05-07",
   0,
   2,
   "Listed",
   "Listed"
  ],
  [
   "LHPOE27CH",
   "",
   "Condieut pipelight accessoies",
   "CND042026",
   "Container 03 2026",
   "2026-05-07",
   0,
   3,
   "Listed",
   "Listed"
  ],
  [
   "LHPOE27SN",
   "",
   "Condieut pipelight accessoies",
   "CND042026",
   "Container 03 2026",
   "2026-05-07",
   0,
   3,
   "Listed",
   "Listed"
  ],
  [
   "LHTOE27SN",
   "",
   "Condieut pipelight accessoies",
   "CND042026",
   "Container 03 2026",
   "2026-05-07",
   0,
   4,
   "Listed",
   "Listed"
  ],
  [
   "PCFT90TBM",
   "20mm T tube",
   "Condieut pipelight accessoies",
   "CND042026",
   "Container 03 2026",
   "2026-05-07",
   1,
   2,
   "Listed",
   "Selling"
  ],
  [
   "LAGLFL130AR",
   "130 Diamond Pendant",
   "Glass shade 2 Supplier",
   "GL2052026",
   "\u2014",
   "2026-05-07",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "LAGLWD150AR",
   "150 Waist Drum",
   "Glass shade 2 Supplier",
   "GL2052026",
   "\u2014",
   "2026-05-07",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "LSGL100145BL",
   "145",
   "Glass shade 2 Supplier",
   "GL2052026",
   "\u2014",
   "2026-05-07",
   1,
   0,
   "Not Listed",
   "Has Combo"
  ],
  [
   "LSGL10014AR",
   "145",
   "Glass shade 2 Supplier",
   "GL2052026",
   "\u2014",
   "2026-05-07",
   1,
   0,
   "Not Listed",
   "Has Combo"
  ],
  [
   "LSGL10014CL",
   "145",
   "Glass shade 2 Supplier",
   "GL2052026",
   "\u2014",
   "2026-05-07",
   4,
   0,
   "Not Listed",
   "Has Combo"
  ],
  [
   "LSGL12010FC",
   "150 Pendant",
   "Glass shade 2 Supplier",
   "GL2052026",
   "\u2014",
   "2026-05-07",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "LSGL12010FW",
   "150 Pendant",
   "Glass shade 2 Supplier",
   "GL2052026",
   "\u2014",
   "2026-05-07",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "LSGL16015AR",
   "150\u00d7160 Striped",
   "Glass shade 2 Supplier",
   "GL2052026",
   "\u2014",
   "2026-05-07",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "LSGL3L150AR",
   "3 Layer Pagoda",
   "Glass shade 2 Supplier",
   "GL2052026",
   "\u2014",
   "2026-05-07",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "LSGLCA16015AR",
   "150\u00d7160 Three Concave Ball",
   "Glass shade 2 Supplier",
   "GL2052026",
   "\u2014",
   "2026-05-07",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "LSGLFE150WH",
   "150 Folded Edge",
   "Glass shade 2 Supplier",
   "GL2052026",
   "\u2014",
   "2026-05-07",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "LSGLLN14020AR",
   "140\u00d7200 Striped Lantern",
   "Glass shade 2 Supplier",
   "GL2052026",
   "\u2014",
   "2026-05-07",
   1,
   0,
   "Not Listed",
   "Has Combo"
  ],
  [
   "LSGLLN150AR",
   "150 Lantern",
   "Glass shade 2 Supplier",
   "GL2052026",
   "\u2014",
   "2026-05-07",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "LSGLSC1508CL",
   "Three Concave Striped",
   "Glass shade 2 Supplier",
   "GL2052026",
   "\u2014",
   "2026-05-07",
   1,
   0,
   "Not Listed",
   "Has Combo"
  ],
  [
   "LSGLST148AR",
   "Striped Pineapple",
   "Glass shade 2 Supplier",
   "GL2052026",
   "\u2014",
   "2026-05-07",
   3,
   0,
   "Not Listed",
   "Has Combo"
  ],
  [
   "LSGLST150AR",
   "150 Striped Globe",
   "Glass shade 2 Supplier",
   "GL2052026",
   "\u2014",
   "2026-05-07",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "LSGLST200AR",
   "200 Striped",
   "Glass shade 2 Supplier",
   "GL2052026",
   "\u2014",
   "2026-05-07",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "LSGLWA170AR",
   "170 Striped Wave",
   "Glass shade 2 Supplier",
   "GL2052026",
   "\u2014",
   "2026-05-07",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "LSMS320BI2PK+RPR44WH2PK",
   "320mm",
   "Multi colour curvy shade supplier",
   "MCY042026",
   "\u2014",
   "2026-04-24",
   0,
   4,
   "Listed",
   "Listed"
  ],
  [
   "LSMS320GR2PK+RPR44WH2PK",
   "320mm",
   "Multi colour curvy shade supplier",
   "MCY042026",
   "\u2014",
   "2026-04-24",
   0,
   4,
   "Listed",
   "Listed"
  ],
  [
   "LSMS320GY2PK+RPR44WH2PK",
   "320mm",
   "Multi colour curvy shade supplier",
   "MCY042026",
   "\u2014",
   "2026-04-24",
   0,
   3,
   "Listed",
   "Listed"
  ],
  [
   "LSMS320OR2PK+RPR44WH2PK",
   "320mm",
   "Multi colour curvy shade supplier",
   "MCY042026",
   "\u2014",
   "2026-04-24",
   0,
   4,
   "Listed",
   "Listed"
  ],
  [
   "LSMS320RE2PK+RPR44WH2PK",
   "320mm",
   "Multi colour curvy shade supplier",
   "MCY042026",
   "\u2014",
   "2026-04-24",
   0,
   3,
   "Listed",
   "Listed"
  ],
  [
   "LSMS320WH2PK+RPR44WH2PK",
   "320mm",
   "Multi colour curvy shade supplier",
   "MCY042026",
   "\u2014",
   "2026-04-24",
   0,
   4,
   "Listed",
   "Listed"
  ],
  [
   "LSMS320YE2PK+RPR44WH2PK",
   "320mm",
   "Multi colour curvy shade supplier",
   "MCY042026",
   "\u2014",
   "2026-04-24",
   0,
   4,
   "Listed",
   "Listed"
  ],
  [
   "ITEM-419-1775548735282",
   "",
   "Condieut pipelight accessoies",
   "CND032026",
   "Container 01 2026",
   "2026-04-07",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "ITEM-419-1775546185974",
   "",
   "Condieut pipelight accessoies",
   "CND032026",
   "Container 01 2026",
   "2026-04-07",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "PCWH20BX",
   "",
   "Condieut pipelight accessoies",
   "CND032026",
   "Container 01 2026",
   "2026-04-07",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "MBWHBSL",
   "Air bubble bag\n200x320mmx300m",
   "Warehouse needed things",
   "WHN 04 2026",
   "\u2014",
   "2026-04-02",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "CO232AGY",
   "",
   "Connector Supplier",
   "CON032026",
   "Container 02 2026",
   "2026-03-31",
   0,
   2,
   "Listed",
   "Listed"
  ],
  [
   "CO332AGY",
   "",
   "Connector Supplier",
   "CON032026",
   "Container 02 2026",
   "2026-03-31",
   0,
   2,
   "Listed",
   "Listed"
  ],
  [
   "CODH632AGY",
   "",
   "Connector Supplier",
   "CON032026",
   "Container 02 2026",
   "2026-03-31",
   0,
   2,
   "Listed",
   "Listed"
  ],
  [
   "CODL332AGY",
   "3 way",
   "Connector Supplier",
   "CON032026",
   "Container 02 2026",
   "2026-03-31",
   0,
   2,
   "Listed",
   "Listed"
  ],
  [
   "CODL632AGY",
   "2 to 6 way",
   "Connector Supplier",
   "CON032026",
   "Container 02 2026",
   "2026-03-31",
   0,
   2,
   "Listed",
   "Listed"
  ],
  [
   "CODL932AGY",
   "",
   "Connector Supplier",
   "CON032026",
   "Container 02 2026",
   "2026-03-31",
   0,
   2,
   "Listed",
   "Listed"
  ],
  [
   "COI9ABM",
   "",
   "Connector Supplier",
   "CON032026",
   "Container 02 2026",
   "2026-03-31",
   0,
   2,
   "Listed",
   "Listed"
  ],
  [
   "LSF1HT300HE",
   "",
   "Hemp Supplier",
   "HEM032026",
   "Container 02 2026",
   "2026-03-31",
   0,
   2,
   "Listed",
   "Listed"
  ],
  [
   "PHHR2HETHE",
   "2m   hemp",
   "Hemp Supplier",
   "HEM032026",
   "Container 02 2026",
   "2026-03-31",
   5,
   3,
   "Listed",
   "Selling"
  ],
  [
   "LSDO400CB",
   "400*150",
   "Multi colour shade supplier",
   "MCS032026",
   "Container 02 2026",
   "2026-03-31",
   26,
   1,
   "Listed",
   "Selling"
  ],
  [
   "LSDO400RE",
   "400*150",
   "Multi colour shade supplier",
   "MCS032026",
   "Container 02 2026",
   "2026-03-31",
   21,
   1,
   "Listed",
   "Selling"
  ],
  [
   "LSRD260AZ",
   "",
   "Pipe lightning Supplier",
   "PLS032026",
   "Container 02 2026",
   "2026-03-31",
   0,
   3,
   "Listed",
   "Listed"
  ],
  [
   "PL4HBC",
   "",
   "Pipe lightning Supplier",
   "PLS032026",
   "Container 02 2026",
   "2026-03-31",
   3,
   3,
   "Listed",
   "Selling"
  ],
  [
   "PL4HRR",
   "",
   "Pipe lightning Supplier",
   "PLS032026",
   "Container 02 2026",
   "2026-03-31",
   3,
   3,
   "Listed",
   "Selling"
  ],
  [
   "WSDM240BC",
   "Double head with balloon cage Full set",
   "Pipe lightning Supplier",
   "PLS032026",
   "Container 02 2026",
   "2026-03-31",
   13,
   2,
   "Listed",
   "Selling"
  ],
  [
   "WSFHTYB",
   "",
   "Assembling lady 1",
   "AL1022026-2",
   "Container 01 2026",
   "2026-03-31",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "LDMA60E274",
   "",
   "Bulbs supplier",
   "BBS032026-02",
   "Container 02 2026",
   "2026-03-30",
   3,
   3,
   "Listed",
   "Selling"
  ],
  [
   "LSWE315BM",
   "Vintage Industrial Metal Black Colour Ceiling Sh",
   "Multi colour curvy shade supplier",
   "MCY032026",
   "Container 01 2026",
   "2026-03-27",
   17,
   3,
   "Listed",
   "Selling"
  ],
  [
   "LSWE315OR",
   "Modern Retro Industrial Vintage Metal Hanging Ce",
   "Multi colour curvy shade supplier",
   "MCY032026",
   "Container 01 2026",
   "2026-03-27",
   18,
   3,
   "Listed",
   "Selling"
  ],
  [
   "LSWE315WH",
   "Beat style colour White Lampshade",
   "Multi colour curvy shade supplier",
   "MCY032026",
   "Container 01 2026",
   "2026-03-27",
   19,
   3,
   "Listed",
   "Selling"
  ],
  [
   "LSWE315YE",
   "Beat style colour Yellow Lampshade",
   "Multi colour curvy shade supplier",
   "MCY032026",
   "Container 01 2026",
   "2026-03-27",
   21,
   3,
   "Listed",
   "Selling"
  ],
  [
   "CRFF500BC",
   "500*60*25 ceiling rose 3 out let",
   "Pipe lightning Supplier",
   "PLS122025.",
   "Container 01 2026",
   "2026-03-26",
   25,
   1,
   "Listed",
   "Selling"
  ],
  [
   "CRFF500BS",
   "500*60*25 ceiling rose 3 out let",
   "Pipe lightning Supplier",
   "PLS122025.",
   "Container 01 2026",
   "2026-03-26",
   24,
   1,
   "Listed",
   "Selling"
  ],
  [
   "CRSFM100BR",
   "",
   "Celing Rose Lady",
   "CRL032026-02",
   "Container 01 2026",
   "2026-03-24",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "CRSFML100BM",
   "",
   "Celing Rose Lady",
   "CRL032026-02",
   "Container 01 2026",
   "2026-03-24",
   0,
   1,
   "Listed",
   "Listed"
  ],
  [
   "CRSFML100YB",
   "",
   "Celing Rose Lady",
   "CRL032026-02",
   "Container 01 2026",
   "2026-03-24",
   0,
   1,
   "Listed",
   "Listed"
  ],
  [
   "PC16FTNLCH",
   "2side",
   "Condieut pipelight accessoies",
   "CND032026",
   "Container 01 2026",
   "2026-03-19",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "PC16FTNLWH",
   "2side",
   "Condieut pipelight accessoies",
   "CND032026",
   "Container 01 2026",
   "2026-03-19",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "PC16FTNLYB",
   "2side",
   "Condieut pipelight accessoies",
   "CND032026",
   "Container 01 2026",
   "2026-03-19",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "PCBS16T10BM",
   "",
   "Condieut pipelight accessoies",
   "CND032026",
   "Container 01 2026",
   "2026-03-19",
   1,
   3,
   "Listed",
   "Selling"
  ],
  [
   "PCBS16T10CH",
   "",
   "Condieut pipelight accessoies",
   "CND032026",
   "Container 01 2026",
   "2026-03-19",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "PCBS16T10WH",
   "",
   "Condieut pipelight accessoies",
   "CND032026",
   "Container 01 2026",
   "2026-03-19",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "PCBS16T10YB",
   "",
   "Condieut pipelight accessoies",
   "CND032026",
   "Container 01 2026",
   "2026-03-19",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "PC16FT250BA",
   "",
   "Condieut pipelight accessoies",
   "CND032026",
   "Container 01 2026",
   "2026-03-19",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "PC16FT250CH",
   "",
   "Condieut pipelight accessoies",
   "CND032026",
   "Container 01 2026",
   "2026-03-19",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "PC16FT250WH",
   "",
   "Condieut pipelight accessoies",
   "CND032026",
   "Container 01 2026",
   "2026-03-19",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "PC16FT250YB",
   "",
   "Condieut pipelight accessoies",
   "CND032026",
   "Container 01 2026",
   "2026-03-19",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "SPCR60603CO",
   "",
   "Condieut pipelight accessoies",
   "CND032026",
   "Container 01 2026",
   "2026-03-19",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "SPCR60603SN",
   "",
   "Condieut pipelight accessoies",
   "CND032026",
   "Container 01 2026",
   "2026-03-19",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "SPCR60603YB",
   "",
   "Condieut pipelight accessoies",
   "CND032026",
   "Container 01 2026",
   "2026-03-19",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "SPCR60605CO",
   "",
   "Condieut pipelight accessoies",
   "CND032026",
   "Container 01 2026",
   "2026-03-19",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "SPCR60605SN",
   "",
   "Condieut pipelight accessoies",
   "CND032026",
   "Container 01 2026",
   "2026-03-19",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "SPCR60605YB",
   "",
   "Condieut pipelight accessoies",
   "CND032026",
   "Container 01 2026",
   "2026-03-19",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "CRSFM110080CH",
   "",
   "Condieut pipelight accessoies",
   "CND032026",
   "Container 01 2026",
   "2026-03-18",
   0,
   1,
   "Listed",
   "Listed"
  ],
  [
   "CRSFM110080CO",
   "",
   "Condieut pipelight accessoies",
   "CND032026",
   "Container 01 2026",
   "2026-03-18",
   0,
   1,
   "Listed",
   "Listed"
  ],
  [
   "CRSFM110080SN",
   "",
   "Condieut pipelight accessoies",
   "CND032026",
   "Container 01 2026",
   "2026-03-18",
   0,
   1,
   "Listed",
   "Listed"
  ],
  [
   "CRSFM110080YB",
   "",
   "Condieut pipelight accessoies",
   "CND032026",
   "Container 01 2026",
   "2026-03-18",
   0,
   1,
   "Listed",
   "Listed"
  ],
  [
   "CRSFM210080BM",
   "",
   "Condieut pipelight accessoies",
   "CND032026",
   "Container 01 2026",
   "2026-03-18",
   1,
   2,
   "Listed",
   "Selling"
  ],
  [
   "CRSFM210080CH",
   "",
   "Condieut pipelight accessoies",
   "CND032026",
   "Container 01 2026",
   "2026-03-18",
   1,
   2,
   "Listed",
   "Selling"
  ],
  [
   "CRSFM210080CO",
   "",
   "Condieut pipelight accessoies",
   "CND032026",
   "Container 01 2026",
   "2026-03-18",
   1,
   2,
   "Listed",
   "Selling"
  ],
  [
   "CRSFM210080SN",
   "",
   "Condieut pipelight accessoies",
   "CND032026",
   "Container 01 2026",
   "2026-03-18",
   1,
   2,
   "Listed",
   "Selling"
  ],
  [
   "CRSFM210080WH",
   "",
   "Condieut pipelight accessoies",
   "CND032026",
   "Container 01 2026",
   "2026-03-18",
   1,
   2,
   "Listed",
   "Selling"
  ],
  [
   "CRSFM210080YB",
   "",
   "Condieut pipelight accessoies",
   "CND032026",
   "Container 01 2026",
   "2026-03-18",
   1,
   2,
   "Listed",
   "Selling"
  ],
  [
   "12ASIP20100",
   "",
   "Transformer HN Supplier",
   "THN032026DE",
   "DE Container 01 2026",
   "2026-03-18",
   0,
   4,
   "Listed",
   "Listed"
  ],
  [
   "12ASIP2060",
   "",
   "Transformer HN Supplier",
   "THN032026DE",
   "DE Container 01 2026",
   "2026-03-18",
   0,
   3,
   "Listed",
   "Listed"
  ],
  [
   "12SIP67150",
   "12V Slim IP67 150",
   "Transformer HN Supplier",
   "THN032026DE",
   "DE Container 01 2026",
   "2026-03-18",
   0,
   3,
   "Listed",
   "Listed"
  ],
  [
   "12SIP67200",
   "12V Slim IP67 200",
   "Transformer HN Supplier",
   "THN032026DE",
   "DE Container 01 2026",
   "2026-03-18",
   0,
   3,
   "Listed",
   "Listed"
  ],
  [
   "PHHT2PBRBM",
   "2m 3 Core PVC cable",
   "Assembling lady 1",
   "AL1032026-DE",
   "DE Container 01 2026",
   "2026-03-18",
   19,
   1,
   "Listed",
   "Selling"
  ],
  [
   "WSSS70CO",
   "short Arm short 2cm rod holder",
   "Assembling lady 1",
   "AL1032026-DE",
   "DE Container 01 2026",
   "2026-03-18",
   12,
   2,
   "Listed",
   "Selling"
  ],
  [
   "LHC1E27WH",
   "",
   "Bakelite holders",
   "BKH032026",
   "Container 01 2026",
   "2026-03-12",
   0,
   3,
   "Listed",
   "Listed"
  ],
  [
   "LHC3E27WH",
   "",
   "Bakelite holders",
   "BKH032026",
   "Container 01 2026",
   "2026-03-12",
   0,
   4,
   "Listed",
   "Listed"
  ],
  [
   "LHC4E27WH",
   "",
   "Bakelite holders",
   "BKH032026",
   "Container 01 2026",
   "2026-03-12",
   0,
   4,
   "Listed",
   "Listed"
  ],
  [
   "LHC5E27WH",
   "",
   "Bakelite holders",
   "BKH032026",
   "Container 01 2026",
   "2026-03-12",
   0,
   4,
   "Listed",
   "Listed"
  ],
  [
   "LHC6E27WH",
   "",
   "Bakelite holders",
   "BKH032026",
   "Container 01 2026",
   "2026-03-12",
   0,
   4,
   "Listed",
   "Listed"
  ],
  [
   "LSDO210BL",
   "210 mm Dome",
   "Brushed Curvy Supplier",
   "BRC032026",
   "Container 01 2026",
   "2026-03-10",
   30,
   2,
   "Listed",
   "Selling"
  ],
  [
   "PHCH1PBRBB",
   "1m",
   "Brushed Curvy Supplier",
   "BRC032026",
   "Container 01 2026",
   "2026-03-10",
   101,
   1,
   "Listed",
   "Selling"
  ],
  [
   "PHOP1PBRBM",
   "1m",
   "Brushed Curvy Supplier",
   "BRC032026",
   "Container 01 2026",
   "2026-03-10",
   113,
   0,
   "Not Listed",
   "Has Combo"
  ],
  [
   "CRFF2005BM",
   "200mm 5 outlet",
   "Celing Rose Lady",
   "CRL032026",
   "Container 01 2026",
   "2026-03-10",
   5,
   3,
   "Listed",
   "Selling"
  ],
  [
   "SWPLGD",
   "",
   "Celing Rose Lady",
   "CRL032026",
   "Container 01 2026",
   "2026-03-10",
   12,
   3,
   "Listed",
   "Selling"
  ],
  [
   "SWPLSL",
   "",
   "Celing Rose Lady",
   "CRL032026",
   "Container 01 2026",
   "2026-03-10",
   0,
   3,
   "Listed",
   "Listed"
  ],
  [
   "LSFRE3FTPYBM",
   "500mm 3outlet rectangle ceiling rose + 1m 3core",
   "Assembling Lady 2",
   "AL2032026",
   "Container 01 2026",
   "2026-03-10",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "LSFRE3ROPCCH",
   "500mm 3 outlet rectangle ceiling rose+ 1m 3core",
   "Assembling Lady 2",
   "AL2032026",
   "Container 01 2026",
   "2026-03-10",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "LSFRO3ROPWFG",
   "200mm 3 outlet French Gold round ceiling rose+ 1",
   "Assembling Lady 2",
   "AL2032026",
   "Container 01 2026",
   "2026-03-10",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "PHFMHT1BRBM",
   "1m",
   "Assembling Lady 2",
   "AL2032026",
   "Container 01 2026",
   "2026-03-10",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "PSHYOS2BRBM",
   "2m",
   "Assembling Lady 2",
   "AL2032026",
   "Container 01 2026",
   "2026-03-10",
   6,
   4,
   "Listed",
   "Selling"
  ],
  [
   "LSFS3O1YBGS",
   "",
   "Assembling Lady 2",
   "AL2122025",
   "Container 16",
   "2026-03-10",
   1,
   1,
   "Listed",
   "Selling"
  ],
  [
   "LHHTE27BM",
   "3 cores, 10mm leakage",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-03-10",
   69,
   1,
   "Listed",
   "Selling"
  ],
  [
   "LHTTAGU10EBM",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-03-10",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "LHTTAGU10EYB",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-03-10",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "NT3",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-03-10",
   0,
   1,
   "Listed",
   "Listed"
  ],
  [
   "WSFSBA",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-03-10",
   8,
   1,
   "Listed",
   "Selling"
  ],
  [
   "WSIWH70BM",
   "7cm as shown in the picture",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-03-10",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "WSIWH70YB",
   "7cm as shown in the picture",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-03-10",
   0,
   0,
   "Not Listed",
   "No Combo"
  ],
  [
   "WSWS1PHTBM",
   "",
   "Assembling lady 1",
   "AL1032026",
   "Container 01 2026",
   "2026-03-10",
   4,
   1,
   "Listed",
   "Selling"
  ],
  [
   "LDT185E274",
   "T185 E27 4 W",
   "Bulbs supplier",
   "BBS 03 2026",
   "Container 01 2026",
   "2026-03-10",
   1,
   3,
   "Listed",
   "Selling"
  ],
  [
   "CRSFX120BM",
   "120mm*25mm",
   "Ceiling rose guy",
   "CRG032026",
   "Container 01 2026",
   "2026-03-10",
   0,
   1,
   "Listed",
   "Listed"
  ],
  [
   "CRSFX120YB",
   "120mm*25mm",
   "Ceiling rose guy",
   "CRG032026",
   "Container 01 2026",
   "2026-03-10",
   0,
   1,
   "Listed",
   "Listed"
  ],
  [
   "LHTKE27YB",
   "",
   "Ceiling rose guy",
   "CRG032026",
   "Container 01 2026",
   "2026-03-10",
   6,
   1,
   "Listed",
   "Selling"
  ],
  [
   "SCRN70BA",
   "",
   "Ceiling rose guy",
   "CRG032026",
   "Container 01 2026",
   "2026-03-10",
   15,
   1,
   "Listed",
   "Selling"
  ],
  [
   "HLLK75BM",
   "75mm",
   "Handle Supplier",
   "HAN032026",
   "Container 01 2026",
   "2026-03-10",
   0,
   3,
   "Listed",
   "Listed"
  ]
 ]
};
