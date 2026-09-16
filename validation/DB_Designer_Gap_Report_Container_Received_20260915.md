# Gap Report: Container, Received Date and Received Warehouse (LEDSone database)

**For:** LEDSone Database Designer
**Date:** 2026-09-15
**Prepared by:** Sarujanan (Dashboard V2)

**Sources compared, SKU by SKU:**
1. **Inventory system (admin site):** `dashboard.digitweblk.com`, the UK Supply List, supply order pages and product pages (screenshots supplied by the user).
2. **Inventory Team dashboard:** reads LEDSone; its logic was reproduced read-only.
3. **LEDSone database:** `169.58.91.229/ledsone`, queried SELECT-only on 2026-09-15.

No data, schema or dashboard was changed. This report supersedes the earlier draft of this file, which proposed container `completed` status as the received signal. The evidence below shows that status is **not** a reliable receipt signal.

---

## 1. Summary

| # | Finding | Type |
|---|---|---|
| 1 | The **UK Supply List** (supply order `SUxxxx`: status, container, estimate date, per-SKU qty) **does not exist in LEDSone**. The only trace is free text in `inventory.product_history.history`. | Genuine database gap |
| 2 | **Received date and warehouse** exist only inside that free text ("Supply - SU1318 loaded by … On 2026-08-25 … unit5 changed from 0 to 115"). No structured receipt table exists. | Data exists, not structured |
| 3 | `inventory.product_history` is a **one-time copy**: every row has `source_updated_at` = 2026-08-26 07:48. Receipts after 26 Aug 2026 are not in LEDSone. | Genuine database gap |
| 4 | **No key links a receipt (SU) to a supplier PO line or container** (`suppliers.order_items`). The admin's container for a received SU can't be joined. | Missing relationship |
| 5 | **Container not assigned** on PO lines that were shipped and received (e.g. CND062026: 8 SKUs received 25 Aug, no container). | Missing relationship |
| 6 | **Admin container names ≠ LEDSone container names.** Admin names follow the loading scheme ("Container 05 2026"); LEDSone final containers use "UK Container 8th 2026". The two are many-to-many with no key. | Missing relationship |
| 7 | `suppliers.final_containers.status = 'completed'` is **not proof of receipt**. It is set on containers with zero stock, no receipt, or before the PO was even raised. | Unreliable field |
| 8 | **Re-coded SKUs are not mapped.** A receipt recorded under the new code (IMAC7714CW) doesn't link to the PO SKU (IMACCW); `inventory.product_mapping` has no row. | Missing relationship |
| 9 | **Warehouse id 33 (Unit 5)** is used in `inventory.physical_product_stock` (3,232 rows, 592,475 units) but has **no row in `inventory.warehouse`**. | Missing reference row |
| 10 | Legacy container **"Container 14 2025"** has `status` NULL although all 225 PO lines arrived and the admin shows its supply orders Completed. | Missing status |

---

## 2. How the admin (Inventory system) defines "received"

From the screenshots:
- **Supply order list** columns: Supply Order ID, Order Created At, Estimate Date, Container ID, Supplier, Status (`order` or `Completed`).
- **Product page:** a table of supply orders for the SKU (ID, Quantity, Status, Container, Supplier), plus the history text.
- **When a supply order is received,** a history line is written, for example:
  `Supply - SU1318 loaded by mithusha On 2026-08-25 10:27:04 - … - unit5 changed from 0 to 115`
  - **Received date** = the `On` timestamp.
  - **Received warehouse** = the stock field that increased.
  - **Supply order** = the SU number.

**History field → warehouse**, confirmed against admin stock and LEDSone `physical_product_stock`:

| History field | Admin label | LEDSone `physical_product_stock.warehouse` | `inventory.warehouse` row |
|---|---|---|---|
| `Quantity` | Unit3 | 1 | ✔ "UK Unit3" |
| `unit1` | Unit18 | 6 | ✔ "UK Unit18" |
| `unit3` | Unit4 | 8 | ✔ "UK Unit4" |
| `unit2` | Mark | — | — |
| `unit5` | Unit 5 | **33** | ✘ **missing** |

**Latest completed container** (admin) = the most recent supply order with status `Completed`, with its Container ID and receipt line.

---

## 3. Evidence per SKU

**Legend:**
- V2 values: **P** = published build (15 Sep 11:00); **L** = local build with the approved history fallback (not published).
- Categories: **A** = Inventory has data and LEDSone has data (dashboard retrieval issue). **B** = Inventory has data and LEDSone doesn't (genuine gap). **C** = LEDSone has data but the relationship or mapping is missing. **OK** = blank is correct.

### 3.1 SU1318: SPCR60605CH, SPCR60603CH, RD42, PCCR6030CH/CO/SN/YB, CBSF95NA

| Field | Inventory (admin) | LEDSone | Missing | Cat. |
|---|---|---|---|---|
| Supply order | SU1318, **Completed**, created 2026-08-18, estimate 2026-08-30, "Conduit Pipe Supplier" | ✘ no table. SU1318 appears only in history text (10 products). | SU record | **B** |
| Container | **"Countainer 05 2026"** (typo in admin) | PO **CND062026** (shipped, `status_arrived` = false): **all 8 lines have `assigned_container_id` and `final_container_id` NULL**. Loading container "Container 05 2026" (id 37) exists but no CND062026 line is assigned to it. | container on PO lines; SU ↔ PO link | **C** |
| Received date | 2026-08-25 10:27:04 | ✔ history text, same timestamp | — | **A** (V2 P and L show 2026-08-25) |
| Received warehouse | Unit 5 (e.g. SPCR60605CH 0 → 115) | ✔ history `unit5`; stock in warehouse **33**, e.g. SPCR60605CH 115, RD42 1,186, CBSF95NA 4,000 | name for warehouse 33 | **C** |
| Qty | SPCR60605CH 115, SPCR60603CH 139, PCCR6030CO 207 | PO pcs 108, 108, **0** | — | Data mismatch |
| Scope | SU1318 also contains SPCR60603YB (14) and SPCR60605CO (9) | Those two sit on a different PO, **CND032026** (UK Container 1st 2026) | SU ↔ PO link | **C** |

**Root cause:** the shipment was received through the admin supply list. LEDSone's PO lines were never given a container or marked arrived, and nothing links SU1318 to CND062026.

### 3.2 LSMS3202 (GY, OR, WH are V2 components; BI, GR, RE, YE are also on the order)

| Field | Inventory (admin) | LEDSone | Missing | Cat. |
|---|---|---|---|---|
| Supply orders | **SU1317 Completed**, "Container 05 2026", created 2026-08-18, estimate 2026-08-30, qty 100/50 · SU1331 order, "Container 11 2026" | ✘ no SU table | SU record | **B** |
| PO for the received shipment | (SU1317) | ✘ **No PO line for these SKUs** except the September re-orders MCY092026 (9 Sep) and MCS092026 (8 Sep), both not shipped. BI, GR, RE and YE have **no PO at all**. | PO lines for SU1317 | **B** |
| Latest completed container | Container 05 2026 | ✘ none linked | container | **B** |
| Received date | 2026-08-25 11:02:43 | ✔ history text (all 7 SKUs) | — | **A** (V2 P: blank because it shows the newest PO; L: 2026-08-25) |
| Received warehouse | Unit 5 | ✔ history `unit5`; stock warehouse 33 (GY 100, OR 50, WH 100) | name for warehouse 33 | **C** |

### 3.3 LSGLST148AR, LSGLST150AR, LSGLST1618AR (SU1253)

| Field | Inventory (admin) | LEDSone | Missing | Cat. |
|---|---|---|---|---|
| Supply orders | **SU1253 Completed**, "Container 03 2026", qty 120 · SU1310 order, "Container 09 2026" · SU1351 order, "Container 11 2026" | ✘ no SU table | SU record | **B** |
| Latest completed container | Container 03 2026 | 148AR / 150AR: PO **GL2052026** (4 Jun, arrived) → final "UK Container 3rd 2026", **no loading container**. **1618AR: not on GL2052026 at all**; its only PO is GL2092026 (not shipped). | 1618AR PO line; admin ↔ LEDSone container name link | **C** / **B** (1618AR) |
| Received date | 2026-07-07 10:55:48 | ✔ history text (all 3) | — | **A** |
| Container "completed" date | — | UK Container 3rd 2026 `completed`, `updated_at` **2026-05-21**. That is **before** the PO date (2026-06-04) and 47 days before the receipt (2026-07-07). | real completion / receipt timestamp | **C** (unreliable field) |
| Received warehouse | Unit18 (`unit1` 0 → 120) | ✔ history `unit1` → warehouse 6 "UK Unit18" | — | **A** |

**Dashboard retrieval:**
- **V2 published:** 08Sep2026 / blank (it shows the newest, unshipped PO).
- **V2 local:** UK Container 3rd 2026 / **2026-05-21**. This date is wrong, because it comes from the container's `updated_at`; the correct date is 2026-07-07.
- **Inventory dashboard:** UK Container 3rd 2026 / 2026-07-07, Unit 18. It uses the history receipt, so its date is correct.

### 3.4 LHXSHE27BM (SU1168)

| Field | Inventory (admin) | LEDSone | Missing | Cat. |
|---|---|---|---|---|
| Supply orders | **SU1168 Completed**, "Container 11 2025", created and estimate 2026-01-23, qty 1,000 · SU1280 order, "Container 07 2026" · SU1349 order, "Container 12 2026" | ✘ no SU table | SU record | **B** |
| Latest completed container | Container 11 2025 | ✘ **No PO line** for this SKU in Container 11 2025. Only NPH072026 (23 Jul, not shipped) and PVC072026 (15 Jul, not confirmed). A loading container "Container 11" exists, but not for this SKU. | PO line for SU1168 | **B** |
| Received date | 2026-01-23 10:26:52 | ✔ history text | — | **A** (V2 P: blank; L: 2026-01-23) |
| Received warehouse | Unit3 (`Quantity` 0 → 1000) | ✔ history → warehouse 1 "UK Unit3" | — | **A** |

### 3.5 IMACCW, IMACGR, IMACYE (SU1185)

| Field | Inventory (admin) | LEDSone | Missing | Cat. |
|---|---|---|---|---|
| Supply order | **SU1185 Completed**, "Container 14 2025", created 2026-02-17, estimate 2026-02-26 · lists IMACCW 15,000, IMACYE 10,000, IMACGR 5,000, IMACWW 5,000 | ✘ no SU table | SU record | **B** |
| Container | Container 14 2025 | ✔ PO **LDI 12 2025** (arrived) → final "Container 14 2025" | — | **A** (V2 shows it) |
| Container status | Completed | "Container 14 2025" `status` **NULL** (225 of 225 lines arrived) | status and completion date | **C** |
| Received date | 2026-02-26 (SU1185) | IMACCW, IMACGR and IMACYE have **no history row**. The SU1185 receipt is recorded under **IMAC7714CW** (0 → 15,000), **IMAC7714GR** (5,000), **IMAC7714YE** (10,000) and **IMAC9820WW** (5,000 = IMACWW). | SKU mapping old ↔ new | **C** |
| SKU mapping | same product | `inventory.product_mapping`: **no row** for any of these ids. `products.sku_original` repeats the SKU itself. | mapping rows | **C** |
| Received warehouse | Unit3 | history `Quantity` → UK Unit3; LEDSone stock IMACCW 15,000 in UK Unit3 | — | **A** |

### 3.6 CRSFX120BM, CRSFX120YB, CRSF100CF (SU1358)

| Field | Inventory (admin) | LEDSone | Missing | Cat. |
|---|---|---|---|---|
| Supply orders | **SU1358 order** (not received), "Container 12 2026", created 2026-09-14, estimate **2027-03-09**, qty 500. Product page lists **only** SU1358; stock 0; history empty. | PO CRG092026-01 (14 Sep, confirmed) and **CND092026-1** (15 Sep, not confirmed, same 500 units under a different supplier: probable duplicate) | — | — |
| Planned container | Container 12 2026 | ✘ not in `containers` or `final_containers`; PO lines have no container | container | **B** |
| Received date / container | none (correct) | Older PO **CRG032026** (100 units, shipped, **not arrived**) → final "UK Container 7th 2026", `status` **completed** 2026-08-19. **No receipt, stock 0, and the admin has no supply order for it.** | — | **OK** blank; "completed" is misleading (**C**) |

### 3.7 CRSP cables (PO AL1052026)

| Field | Inventory (admin) | LEDSone | Missing | Cat. |
|---|---|---|---|---|
| Supply order | none shown; history empty; stock 0 (all 7 checked) | — | — | — |
| Container | not received | 212R48WH, 217R66CH, 217R66CO → final "UK Container 8th 2026" (`completed` 2026-08-19, **invoice ship-by 2026-09-09**). 212R48CH, 212R48CO, 217R66WH, 217R66YB, 112R48CH, 112R48WH → **no container**, although on the same shipped PO. | container on 6 lines | **C** |
| Received date | none | none (stock 0, no receipt) | — | **OK**. V2 shows a false "19 Aug" on 3 SKUs because `completed` ≠ received. |

### 3.8 Correct blanks (not received in either system)

| SKU | Inventory (admin) | LEDSone | Verdict |
|---|---|---|---|
| SPCA70BM, PCFTLBM, PCFTLCF, PCFTLYB | no receipt, stock 0 | AL1062026 not shipped, no container | **OK** |
| CBSF95CL | no supply order; stock came from a manual "inventory CSV" entry on 2026-07-22 | same manual line in history; PO CRG092026-01 not shipped | **OK**. Warehouse mismatch: admin Unit 2: 15; LEDSone UK Unit3 15 and Trossingen −5. |
| MBWHBSL | no supply order, stock 0 | PO WHN 04 2026 never confirmed (last updated 2026-04-03) | **OK** |
| LSCY2902 ×6 | SU1313 / SU1331 status `order` | MCY082026 / MCY092026 / MCS092026 not shipped. Loading "Container 09 2026" and "08Sep2026"; admin says "Container 11 2026". LEDSone final "Container 011th 2026" is not linked. | Received **OK**; container naming gap (**C**) |

---

## 4. Proof that `final_containers.status = 'completed'` is not a receipt signal

| Final container | `completed` (updated_at) | PO lines | Lines with `status_arrived` | Evidence against "received" |
|---|---|---|---|---|
| UK Container 3rd 2026 | 2026-05-21 | 138 | 129 | GL2052026 received **2026-07-07** (SU1253); container date precedes the PO date 2026-06-04 |
| UK Container 6th 2026 | 2026-08-24 | 42 | **0** | — |
| UK Container 7th 2026 | 2026-08-19 | 87 | **6** | CRSFX120BM/YB: stock 0, no receipt, no admin supply order |
| UK Container 8th 2026 | 2026-08-19 | 157 | **0** | Invoice ship-by **2026-09-09**; CRSP cables stock 0, history empty |

`orders.status_arrived` is also incomplete: it was last set on 2026-09-02, and CND062026 is still `false` although its goods were received on 25 Aug. **Neither flag records a receipt date.**

---

## 5. Search performed before classifying anything as "missing"

- **Table and column names across all 18 schemas:** no table or column for supply orders, receipts, goods-in or arrival dates outside `suppliers.*`.
- **Values in 186 text columns** in `inventory`, `suppliers`, `public`, `staff`, `employee_management`, `configurator` and `order_management` (the large order tables excluded), searched for `SU1318`, `SU1317`, `SU1185`, `SU1253`, `SU1358`, `Countainer`, `Container 11 2025`, `Container 12 2026`, `Container 03 2026` and `Container 11 2026`:
  - Found only in `inventory.product_history.history` (SU1318 ×10, SU1317 ×7, SU1185 ×9, SU1253 ×21 products).
  - `suppliers.containers.name`: only "Container 03 2026".
  - SU1358, "Countainer", "Container 12 2026" and "Container 11 2026": **0 hits anywhere**.
- `inventory.product_mapping` (516 rows): no rows for IMACCW, IMACGR, IMACYE or IMAC7714*.
- `inventory.warehouse`: ids 1–8, 10, 32 only. **33 is absent.**
- `inventory.product_history`: 6,316 rows (of 44,561 products); `source_updated_at` 2026-08-26 07:48:08 to 07:48:24 for every row.
- **Loading vs final containers:** many-to-many. For example, loading "Container 01 2026" lines are spread over 10 different final containers. 71 PO lines dated 2026 have no container at all; 19 of them are already shipped.

---

## 6. What needs to be corrected

| # | Correction | Fixes | Example SKUs |
|---|---|---|---|
| D1 | **Mirror the UK Supply List into LEDSone.** A `supply_orders` table (su_no, status, created_at, estimate_date, container_name, supplier) plus `supply_order_items` (su_no, sku, qty) | Supply order, status and admin container missing | all samples |
| D2 | **Structured receipts table:** `supply_receipts` (su_no, sku, inventory_id, warehouse_id, qty_received, received_at, received_by), instead of free text only | Received date / warehouse unusable | SU1318, SU1317, SU1253, SU1168 groups |
| D3 | **Link receipts and supply orders to PO lines:** `supply_order_items.order_item_id` → `suppliers.order_items.id` | SU ↔ PO ↔ container can't be joined | SU1318 ↔ CND062026 / CND032026 |
| D4 | **Container link table** between admin container name, `suppliers.containers` (loading) and `suppliers.final_containers`, with one normalised name | Three naming schemes | Countainer 05 2026, Container 11 2026 ↔ Container 011th 2026 ↔ 08Sep2026 |
| D5 | Add **`final_containers.received_at`** (set only when goods are received), separate from `status` and `updated_at` | "completed" ≠ received; wrong dates | UK Container 3rd / 7th / 8th 2026 |
| D6 | **Keep `inventory.product_history` in sync** (currently frozen at 2026-08-26), or deliver D2 | Receipts after 26 Aug invisible | any receipt after 2026-08-26 |
| D7 | **Assign containers to shipped PO lines;** block `status_shipped` when a line has no container; keep `status_arrived` in step with receipts | Blank containers; stale arrival | CND062026 (8 SKUs), AL1052026 (6 lines) |
| D8 | **Add SKU re-code mappings** in `inventory.product_mapping` (old ↔ new inventory_id) | Receipt under a different SKU | IMACCW ↔ IMAC7714CW, IMACGR ↔ IMAC7714GR, IMACYE ↔ IMAC7714YE, IMACWW ↔ IMAC9820WW |
| D9 | **Insert warehouse 33** ("UK Unit5") into `inventory.warehouse` | Unit 5 stock has no name | SU1318 and SU1317 groups (469 products, 592,475 units) |
| D10 | **Set status and completion for legacy containers** ("Container 14 2025", "Container 02 2025") | No received date | IMACCW, IMACGR, IMACYE, CRSF120HBM |
| D11 | **Review duplicate POs** | Wrong "latest PO" | CND092026-1 vs CRG092026-01; MCY092026 vs MCS092026 |
| D12 | **Record the PO for SU shipments that have none** | No container possible | SU1317 (LSMS3202 ×7), SU1168 (LHXSHE27BM), SU1253 line for LSGLST1618AR |

---

## 7. Impact on Dashboard V2 (for information)

**Items V2 can already take from LEDSone:**
- The history receipt date and warehouse. The local build takes the date. Warehouse isn't a V2 column.
- The container of an arrived PO.

**Items V2 can't show until D1–D5 exist:**
- The admin's "latest completed container" name for received SUs.
- A trustworthy received date for containers.

**Items that are V2 logic issues, not database gaps:**
- Choosing the newest PO over an older received one.
- Using `final_containers.updated_at` as the received date. It gives 2026-05-21 instead of 2026-07-07 for LSGLST148AR, and 19 Aug for unreceived CRSP cables.
