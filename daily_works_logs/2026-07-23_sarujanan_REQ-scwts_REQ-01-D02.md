# Daily Requirement Document

---

# 1. Metadata Block

| Field | Value |
|-------|-------|
| daily_requirement_submitted_date | 2026-07-23 |
| expected_deadline_date | 2026-07-23 |
| end_user | Varmen |
| expected_roi | Improve dashboard usability and provide complete, accurate, date-filterable reporting for business users. |
| developer | Sarujanan |
| project | Supplier-to-Customer Workflow Tracking System |
| project_code | SCWTS |
| phase | Phase-01 – Sales Performance, Marketplace Status, Traffic, Returns & Supplier Dashboard Enhancement |
| requirement_id | REQ-01 |
| deliverable_id | REQ-01-D02 |
| blos_keys | Reporting Period, Marketplace Filter, Date Range Filter |
| domain | Ecommerce Operations – Supplier to Customer Workflow Dashboard |
| planned_benefits | Complete dashboard data visibility. Marketplace-wise sales analysis. Date-wise reporting using embedded data. Improved dashboard usability with interactive filtering. |

---

# 2. Today Requirement Block

## 2.1 Today Requirement

### Task Name

Supplier-to-Customer Workflow Dashboard Enhancement and Data Validation

---

### Business Purpose

Enhance the dashboard by improving the Sales Performance, Marketplace Status, Traffic, Returns, and Supplier & Container sections. Validate the exported PostgreSQL data and enable marketplace and date-based filtering using the embedded data.js dataset.

---

### Source Information

**Source System**

PostgreSQL (Exported Snapshot)

**Source Files**

* dashboard/data.js
* sql/components.sql
* sql/combos.sql
* sql/component_combo_mapping.sql
* sql/listings.sql
* sql/orders.sql
* sql/traffic.sql
* sql/returns.sql

---

### Filter Conditions

**Reporting Period:**

2026-01-01 → User Selected Date Range

**Marketplace:**

* All
* Amazon
* eBay
* Shopify
* Wayfair
* B&Q (if available)

---

### Required Data Output

| Field | Purpose |
|-------|---------|
| Marketplace | Marketplace-wise filtering |
| Order Date | Date filtering |
| Order ID | Order identification |
| Marketplace | Sales filtering |
| SKU | Product identification |
| Product Name | Product details |
| Quantity | Sales quantity |
| Sales Amount | Revenue calculation |
| Order Status | Order tracking |
| Customer Country | Customer information |
| Supplier | Supplier analysis |
| Traffic | Marketplace performance |
| Returns | Return analysis |

---

# 3. Business Logic Block

## Sales Performance & Marketplace Filtering

### Rule 1

IF a marketplace is selected

THEN display only the sales records for that marketplace.

---

### Rule 2

IF the user changes the date range

THEN recalculate all KPI cards, charts, tables, and summaries using only the selected reporting period.

---

### Rule 3

IF "All" is selected

THEN display data for every marketplace.

---

### Rule 4

Dashboard calculations must use only the embedded data.js dataset.

No backend queries or API calls are allowed during dashboard usage.

---

# 4. Data Enrichment Block

## Purpose

Provide complete order information for business analysis.

## Required Data

| Field | Reason |
|-------|--------|
| Marketplace | Marketplace analysis |
| Order Date | Date filtering |
| Order ID | Order identification |
| SKU | Product tracking |
| Product Name | Product identification |
| Quantity | Sales analysis |
| Sales Amount | Revenue reporting |
| Order Status | Order monitoring |
| Customer Country | Business reporting |
| Supplier | Supplier tracking |
| Traffic | Performance analysis |
| Returns | Return analysis |
