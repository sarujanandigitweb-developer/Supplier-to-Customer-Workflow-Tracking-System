# Business Workflow — Supplier's Basket to Customer's Home

**Title:** Business Workflow
**Purpose:** Explain the complete end-to-end business workflow the dashboard tracks, stage by stage, with the data source and the one confirmed limitation at each link.
**Business Question:** *"What is the full lifecycle of a product from supplier to customer, and is every link in that chain visible and evidenced?"*

---

## End-to-End Workflow

```
        Supplier
           │        supplier.suppliers (47)
           ▼
    Purchase Order
           │        supplier.orders (250 · 99 since Mar)
           ▼
       Container
           │        supplier.orders.container_id → supplier.containers (24 · 16 final)
           ▼
       Component
           │        components_sot_skus (1,813) / supplier.order_items (3,826) · 349 new since Mar
           ▼
         Combo
           │        combo sku = A+B (split '+') · 6,274 created since Mar
           ▼
      Marketplace
           │        listing_data (Amazon/eBay/Shopify/B&Q) · Listed 16,015 / Non-Listed 8,596
           ▼
        Orders
           │        order_transaction · 97,050 orders · £2,304,870 · AOV £23.75
           ▼
        Returns
           │        amazon/ebay/shopify_returns + return_by_cs_team · 4,569 return lines
           ▼
        Customer  (delivery — "customer's home")
```

## Stage Detail

| # | Stage | What happens | Source (verified) | Link status |
|---|---|---|---|---|
| 1 | **Supplier** | A supplier is registered and supplies components | `supplier.suppliers` | ✅ |
| 2 | **Purchase Order** | Components are ordered from the supplier | `supplier.orders` (`order_id`, `order_date`, status flags) | ✅ |
| 3 | **Container** | The PO is assigned to a shipping container | `supplier.orders.container_id` → `supplier.containers` | ✅ |
| 4 | **Component** | Goods received as new components (SKUs) | `public.components_sot_skus` + `supplier.order_items` | ✅ |
| 5 | **Combo** | Components combined into saleable combo SKUs (`A+B`) | derived from `'+'` SKUs across listing/stock/sales | ✅ (derived) |
| 6 | **Marketplace** | Combos/components listed (or not) on channels | `public.listing_data` (`wrong_sku=0`) | ✅ |
| 7 | **Orders** | Customers buy; revenue & units recorded | `public.order_transaction` (Completed) | ✅ |
| 8 | **Returns** | Post-purchase returns recorded | `amazon/ebay/shopify_returns`, `return_by_cs_team` | ✅ |
| 9 | **Customer** | Delivery to the customer's home | — (endpoint; no separate table) | ✅ endpoint |

## The "Breaking Link" — Current Limitation

> **Warehouse Receive Date = NOT FOUND.**
> There is **no warehouse-receive-date column anywhere** in the database. `supplier.orders` records only an **arrival flag** (`status_arrived`) plus `confirmed_date`, `finished_date`, and `expected_completion_date` — none of which is the physical warehouse receive date.
> A prior exhaustive investigation is recorded in `staging_ai.purchasing_intelligence_source_gaps` (gap **GAP-PURCH-CBM-2026-06-09-01**, severity HIGH): the purchasing backend (`order_management_copy @10.8.0.3:5435`) carrying carton/CBM/receive detail is **not mirrored** into this analytics PostgreSQL.
> **Dashboard behaviour:** the Supplier & Container page shows arrival via `status_arrived` and displays an explicit note that Warehouse Receive Date does not exist — **no placeholder value is invented.**

Between stages 3 (Container) and 4 (Component) the *physical receive event* is therefore not timestamped. Every other link in the chain is intact and evidenced.

---

| Field | Value |
|---|---|
| **Source** | `supplier.*` and `public.*` verified tables; gap register `staging_ai.purchasing_intelligence_source_gaps` |
| **Evidence** | `evidence/postgres_discovery_evidence.md`; `workflows/supplier_to_customer_workflow.md` |
| **Status** | ✅ 8 of 9 links fully sourced; 1 link (receive-date timestamp) documented as NOT FOUND |
| **Owner** | Dashboard Development Team; purchasing-source gap → Tamilchelvan |
| **Reviewer** | Varmen |
| **Next Step** | Replicate the purchasing backend to capture Warehouse Receive Date and CBM |
| **Pass/Fail Rule** | PASS when every stage 1–8 maps to a real source with data and the receive-date gap is explicitly disclosed |
| **Known Limitations** | Warehouse Receive Date NOT FOUND; combo relationship derived from SKU pattern; delivery ("customer") is an endpoint, not a tracked table |
