# Dashboard V2 — Container / Received Date Gap: Evidence & Closure Note

| Item | Value |
|---|---|
| Dashboard | Supplier-to-Customer Workflow Tracking — Dashboard V2 |
| Data source | LEDSone PostgreSQL (`ledsone`), via the V2 source layer `dashboard-v2-sql/v2_sources.py` |
| Investigation date | 2026-09-14 |
| Investigation type | Read-only (SELECT queries only; no code, data or schema changed; nothing published) |
| Scope snapshot | 268 components on the Components tab |
| Status | **PASS — closed, no code change** |

---

## 1. Purpose

Dashboard V2 shows blank **Container** and **Received Date** values for some components.
This note records whether those blanks are correct under the existing V2 business logic,
or whether LEDSone holds the same business fact somewhere V2 does not yet read.
It is written to be reused whenever the same question is raised again.

## 2. Existing V2 rule (unchanged)

Defined in `dashboard-v2-sql/build_v2.py`, section 2 (`sup` temp table). One row per component.

| Field | Rule |
|---|---|
| **PO** | The component's **latest** supplier PO line: `suppliers.order_items` joined to `suppliers.orders`, ordered by `orders.order_date DESC NULLS LAST, orders.id DESC`. |
| **Container** | On that PO line: shipping container name (`order_items.final_container_id → final_containers.name`), else loading container name (`order_items.assigned_container_id → containers.name`), else blank. The PO header (`orders.container_id` / `orders.final_container_id`) is **never** used. |
| **Received Date** | The line's shipping container's `updated_at` date **only when `final_containers.status = 'completed'`**; else the earliest `invoices.ship_by_date` for that shipping container; else blank. The PO date is never used as a receipt date. |

Timestamps from `suppliers.*` are converted UTC → local (+5h30) by the source layer, as validated during the LEDSone migration.

## 3. Investigation scope

| Gap | Components |
|---|---|
| No Container | **24** |
| Container present, no Received Date | **66** |
| **Total investigated** | **90** |

Every one of the 90 components was traced:
component SKU → latest PO line → line shipping/loading container → PO header containers →
container status and dates → invoices → shipping-cost records → arrival flags.

## 4. Source tables checked

**Schema-wide metadata search** across all 18 LEDSone schemas for table/column names matching:
`container, receiv*, arriv*, complet*, shipment, deliver*, invoice, ship_by, warehouse, goods, receipt, grn, inbound, loading`.

| Table | Relevant fields | Finding |
|---|---|---|
| `suppliers.order_items` | `final_container_id`, `assigned_container_id`, `not_completed`, `loading_order`, `created_at` | V2's authoritative line-level source |
| `suppliers.orders` | `final_container_id`, `container_id`, `status_shipped`, `status_arrived` (boolean), `expected_completion_date` | PO-header values; no arrival **date** |
| `suppliers.final_containers` | `name`, `status`, `updated_at` | V2's received-date source |
| `suppliers.containers` | `name`, `status`, `updated_at` | Loading containers |
| `suppliers.invoices` | `final_container_id`, `invoice_date`, `ship_by_date` | V2's received-date fallback |
| `suppliers.invoice_shipping_cost` | `final_container_id`, `shipping_cost` | No dates |
| `suppliers.order_item_logs` | `change_key`, `old_value`, `new_value` | No container-assignment history is logged (keys are weight, ctns, cbm, pcs, sku, …) |
| `suppliers.order_items_child`, `incidents`, `images`, `supplier_documents` | — | No container or receipt dates |
| `inventory.physical_product_stock`, `inventory.warehouse`, `inventory.local_inventory_current_stock_location_wise` | warehouse, quantities | No receipt dates |
| `order_management.shipment`, `shipment_tracking_log` | customer shipments | Outbound customer parcels, not supplier containers |
| `amazon_fba.excess_inventory_data` | `inbound_received` | Amazon FBA quantities, not supplier containers |

**Result:** LEDSone has **no** goods-receipt, container-arrival-date, warehouse-receipt or container-status-history table.

## 5. Missing Container breakdown (24)

| Classification | Count | PO | Components | Evidence |
|---|---|---|---|---|
| SOURCE MISSING — no container assigned anywhere | 4 | CRG092026-01 (created 2026-09-14, not shipped) | CBSF95CL, CRSF100CF, CRSFX120BM, CRSFX120YB | 0 of 4 PO lines and no header container. CRSFX120's older PO (CRG032026, UK Container 7th 2026) is correctly not shown: the latest-PO rule selects the newer PO. |
| SOURCE MISSING | 8 | CND062026 (shipped flag, not arrived) | CBSF95NA, PCCR6030CH, PCCR6030CO, PCCR6030SN, PCCR6030YB, RD42, SPCR60603CH, SPCR60605CH | 0 of 8 PO lines and no header container |
| SOURCE MISSING | 4 | AL1062026 (not shipped) | PCFTLBM, PCFTLCF, PCFTLYB, SPCA70BM | No line or header container |
| SOURCE MISSING | 1 | NLM072026 (not shipped) | IMAC9820WW | No line or header container on the latest PO |
| SOURCE MISSING | 1 | WHN 04 2026 (not shipped) | MBWHBSL | No line or header container |
| BUSINESS-RULE CHANGE REQUIRED — PO-header container only | 6 | AL1052026 | CRSP112R48CH, CRSP112R48WH, CRSP212R48CH, CRSP212R48CO, CRSP217R66WH, CRSP217R66YB | Header shipping container = UK Container 8th 2026 (completed). 73 of the PO's 79 lines are line-assigned to it; these 6 lines were added 2026-08-12 and were **never** line-assigned. No record proves they were loaded. |

**Totals:** 18 genuinely unassigned + 6 header-only = **24**.

## 6. Missing Received Date breakdown (66)

| Classification | Count | Container (status) | Components |
|---|---|---|---|
| NOT RECEIVED YET | 21 | UK Container 9th 2026 (**in_progress**, no invoice) | LHETBM, LHETCH, LHETCO, LHETSN, LHETWH, LHETYB, PC22500BM, PC5020BM, PC5020CH, PC5020CO, PC5020RO, PC5020SN, PC5020WH, PC5020YB, SPCR60803BM, SPCR60803CO, SPCR60803YB, SPCR60805BM, SPCR60805CO, SPCR60805YB, LHXSHE27BM |
| NOT RECEIVED YET | 17 | 08Sep2026 (loading container only, no status, PO not shipped) | LSCY2902BI, LSCY2902GR, LSCY2902GY, LSCY2902RE, LSCY2902WH, LSCY290DBI, LSGL100145BL, LSGL10014AR, LSGLST148AR, LSGLST150AR, LSGLST1618AR, LSGLWA140AR, LSHM240BG, LSMS3202GY, LSMS3202OR, LSMS3202WH, WSAFT200BG |
| NOT RECEIVED YET | 8 | Container 08 2026 (loading only, not shipped) | LHSWPBB22CH, LHSWPBB22GD, LHSWPBB22SN, LSFRO3ROPWFG, SPPGUK3PBM, SPPGUK3PBR, SPPGUK3PTR, SPPGUK3PWH |
| NOT RECEIVED YET | 5 | Container 07 2026 (loading only, not shipped) | LSGL12010AR, LSGL14010CL, LSGL14023SG, LSGLULAR, PHHRE2HETX2HE |
| NOT RECEIVED YET | 4 | Container 09 2026 (loading only, not shipped) | LSCY2902BG, WCFRE3LNPYBM, WCFRO3WDPYBM, WLFS220YBG |
| NOT RECEIVED YET | 4 | 01Sep2026 (loading only, not shipped) | LSFRE3ROPCCH, PHRN1002BM, WLFS2202YBG, WSLFS100BM |
| NOT RECEIVED YET | 2 | Container 010th 2026 (no status, no invoice) | LQK1, LSGLLN14020AR |
| SOURCE MISSING — arrived, no date anywhere | 1 | Container 02 2025 (no status, no invoice) | CRSF120HBM — PO `status_arrived = true`, but no date exists in any table |
| BUSINESS-RULE CHANGE REQUIRED | 3 | Container 14 2025 (shipping container **no status**) | IMACCW, IMACGR, IMACYE — PO arrived; loading container "Container 14" is completed (`containers.updated_at` 2026-03-30) |
| BUSINESS-RULE CHANGE REQUIRED | 1 | "Unassign" (placeholder shipping container) | LSGLCA16015AR — PO arrived; PO header shipping container UK Container 3rd 2026, completed 2026-05-21 |

**Totals:** 61 not received + 1 arrived-without-date + 4 alternative-date = **66**.

## 7. Why no safe fallback exists

1. **The PO header is not equivalent to the PO line.** Across all LEDSone supplier PO lines:

   | Measure | Lines |
   |---|---|
   | Lines whose PO header has a shipping container | 2,644 |
   | Lines with **both** line and header shipping container | 2,627 |
   | …same container | 2,388 |
   | …**different** container | **239 (≈ 9%)** |
   | Header container set, line container blank | 17 |

   21 POs have lines split across two or more containers. The header holds a single container per PO, while lines genuinely ship in different containers. Substituting the header would change V2's "container of this PO line" meaning.

2. **A loading container is a different record.** V2's received date is the *shipping* container's close-out. `containers.updated_at` belongs to the loading container, which is a different business event.

3. **No dated receipt source exists.** `orders.status_arrived` is a boolean with no timestamp. No goods-receipt, arrival or container-history table exists in LEDSone.

4. **The current source mapping is complete.** Every LEDSone field that carries V2's line-level container and shipping-container close-out is already read.

## 8. Business-rule changes requiring approval (NOT implemented)

| # | Proposed rule | Would fill | Risk |
|---|---|---|---|
| R1 | If the PO line has no container, use the PO-header shipping container (and its close-out date) | 6 containers + received dates (AL1052026 → UK Container 8th 2026 / 2026-08-19); also LSGLCA16015AR's received date | ≈9% of lines with both values ship in a different container from their PO header; no proof the 6 lines were loaded |
| R2 | If the shipping container has no status, use the loading container's completion date | 3 received dates (IMACCW/GR/YE → 2026-03-30) | Uses a different container record's date as the shipment close-out |

Either rule changes existing V2 business logic and needs explicit business-owner approval before any implementation.

## 9. Known limits

- The findings reflect LEDSone as of 2026-09-14. Counts change as the supplier team assigns and closes containers.
- `final_containers.updated_at` is the last update of the container record. V2 treats it as the close-out date only when status = `completed` (existing rule, not re-evaluated here).
- Two historical shipping containers (Container 14 2025, Container 02 2025) have NULL status. Their `updated_at` of 2026-01-01 looks like a data-load timestamp, not a real close-out.
- Line-to-container assignments have no audit history in LEDSone, so it cannot be proven whether the 6 AL1052026 lines were physically loaded.
- `orders.status_shipped` / `status_arrived` are true/false flags only and cannot supply dates.

## 10. Conclusion

**PASS**

- **No code change required.**
- **Current blanks are correct under existing V2 business logic.**
- **Future values will populate only when LEDSone receives the required container/receipt data** (line-level container assignment, container status set to `completed`, or a supplier invoice ship-by date).

| Result | Count |
|---|---|
| Missing Containers solvable without changing V2 logic | 0 of 24 |
| Genuinely no container assignment | 18 |
| PO-header container only (rule change required) | 6 |
| Missing Received Dates solvable without changing V2 logic | 0 of 66 |
| Correctly blank — not received / not closed | 61 |
| Marked arrived, no date anywhere | 1 |
| Alternative date only (rule change required) | 4 |

## 11. Reviewer required

| Role | Review needed |
|---|---|
| Dashboard owner (task assigner) | Accept closure; decide whether R1 / R2 should be raised as business-rule changes |
| Supplier / purchasing data owner | Confirm whether the 6 AL1052026 lines shipped in UK Container 8th 2026, and set status/dates for Container 14 2025 and Container 02 2025 |

## 12. Next action

1. Reviewer signs off this closure note.
2. Ask the supplier team to complete source data in LEDSone: assign containers to the 18 unassigned PO lines when loaded; line-assign the 6 AL1052026 lines if they shipped in UK Container 8th 2026; set status on Container 14 2025 and Container 02 2025.
3. No dashboard action is needed. The daily V2 refresh picks up corrected LEDSone data automatically.
4. Re-run this check only if the gap counts rise, or if R1/R2 is approved as a business-rule change.
