# Evidence-Grain Audit: 15 Use Cases

**Date:** 2026-02-13  
**Purpose:** Determine the lowest common evidence grain for the 300s-Seite (page 2 execution) evidence table per use case.

---

## Summary Table

| UseCase_ID | Haupt-Action | Empfohlene_Grain | Feasibility | Supporting Table(s) |
|------------|--------------|------------------|-------------|---------------------|
| COM-001 | C-M2.1 (Price Realization Guardrails) | **invoice_line** | ✅ Covered | `fact_sales` (grain: invoice_line) |
| COM-002 | C-M2.2 (Margin Variance Recovery) | **invoice_line** | ✅ Covered | `fact_sales` (grain: invoice_line) |
| COM-003 | C-M2.2 (Margin Variance Recovery) | **customer_month** | ⚠️ Partial | `fact_sales` can aggregate to customer_month |
| COM-004 | C-M2.1 (Price Realization Guardrails) | **promotion** | ✅ Covered | `fact_promo` (grain: promotion) |
| FIN-001 | F-C1.1 (Cash Release Orchestration) | **entity_month** | ✅ Covered | `fact_fin` (grain: entity_month) |
| FIN-002 | F-K2.1 (Plant Unit-Cost Discipline) | **plant_line_product_month** | ✅ Covered | `fact_cost` (grain: plant_line_product_month) |
| OPS-001 | O-O1.1 (Availability Uplift) | **line_day** | ✅ Covered | `fact_ops` (grain: line_day) |
| OPS-002 | O-A2.1 (Asset Downtime Prevention) | **failure_event** | ✅ Covered | `fact_ops_failures` (grain: failure_event) |
| OPS-003 | O-Q3.1 (Scrap & Yield Guardrails) | **line_day** | ✅ Covered | `fact_ops` (grain: line_day); `fact_quality` (grain: line_day) |
| SCM-001 | S-I1.1 (Inventory Orchestration) | **location_sku_month** | ✅ Covered | `fact_inventory` (grain: location_sku_month) |
| SCM-002 | S-R2.1 (OTIF Orchestration) | **shipment_line** | ✅ Covered | `fact_shipments` (grain: shipment_line) |
| SCM-003 | S-F3.1 (Forecast Accuracy Orchestration) | **sku_location_month** | ✅ Covered | `fact_forecast` (grain: sku_location_month) |
| XD-001 | X-S1.1 (Service Level Orchestration) | **case** | ✅ Covered | `fact_support_cases` (grain: case) |
| XD-002 | X-R2.1 (Utilization Orchestration) | **agent_day** | ✅ Covered | `fact_workforce_management` (grain: agent_day) |
| XD-003 | X-E3.2 (Value-at-Risk Escalation) | **entity_month** | ✅ Covered | `fact_exec` (grain: entity_month) |

---

## Detailed Analysis per Use Case

### COM-001: Sales Performance vs Plan & LY
- **Action codes:** C-M2.1, C-S1.1, C-S1.2
- **Haupt-Action:** C-M2.1 (Price Realization Guardrails)
- **Required entities (union):** Region, Channel, Product, Customer Segment
- **Action targets:** Product-level pricing, sales mix
- **Empfohlene_Grain:** **invoice_line**
- **Rationale:** All actions target product/channel/region-level sales performance. The evidence table needs to show individual invoice lines to support drill-down into price realization, mix effects, and segment performance.
- **Feasibility:** ✅ **Covered** – `fact_sales` at `invoice_line` grain (commercial_sales.yaml)
- **Current bracket value:** `transaction_line` (placeholder, needs update)

---

### COM-002: Margin & Price Performance
- **Action codes:** C-M2.2, C-P4.1, C-S1.2
- **Haupt-Action:** C-M2.2 (Margin Variance Recovery)
- **Required entities:** Region, Channel, Product
- **Action targets:** Margin recovery at product level
- **Empfohlene_Grain:** **invoice_line**
- **Rationale:** Same as COM-001; margin analysis requires transaction-level detail for pricing and COGS decomposition.
- **Feasibility:** ✅ **Covered** – `fact_sales` at `invoice_line`
- **Current bracket value:** `transaction_line`

---

### COM-003: Customer Value
- **Action codes:** C-M2.2, C-P4.1, C-S1.2
- **Haupt-Action:** C-M2.2
- **Required entities:** Customer, Region, Channel, Product
- **Action targets:** Customer lifetime value, retention
- **Empfohlene_Grain:** **customer_month**
- **Rationale:** Customer-centric use case; evidence needs customer-month aggregation for CLV, retention, churn analysis.
- **Feasibility:** ⚠️ **Partial** – No dedicated `customer_month` table, but `fact_sales` can aggregate to it.
- **Recommendation:** Consider derived `fact_customer_performance` at `customer_month` grain.
- **Current bracket value:** `transaction_line`

---

### COM-004: Promotion Effectiveness
- **Action codes:** C-M2.1, C-S1.1, C-M2.2, C-P4.1, C-S1.2
- **Haupt-Action:** C-M2.1
- **Required entities:** Promotion, Region, Product
- **Action targets:** Promotion ROI, incremental sales, cannibalization
- **Empfohlene_Grain:** **promotion**
- **Rationale:** Promotion is the natural unit of analysis; evidence shows promotion-level metrics (incremental, ROI, baseline).
- **Feasibility:** ✅ **Covered** – `fact_promo` at `promotion` grain (commercial_sales.yaml)
- **Current bracket value:** `transaction_line`

---

### FIN-001: Cash & Liquidity Performance
- **Action codes:** F-C1.1, F-C1.2, F-C1.3, F-C1.4
- **Haupt-Action:** F-C1.1 (Cash Release Orchestration)
- **Required entities:** Legal Entity, Customer, Supplier, Product Category, Warehouse
- **Action targets:** DSO, DIO, DPO (Working Capital components)
- **Empfohlene_Grain:** **entity_month**
- **Rationale:** Cash/liquidity actions operate at entity-month level; component actions (AR, AP, Inventory) roll up to this orchestration grain.
- **Feasibility:** ✅ **Covered** – `fact_fin` at `entity_month` (finance.yaml)
- **Current bracket value:** `transaction_line`

---

### FIN-002: Cost Performance
- **Action codes:** F-K2.1, F-K2.2, F-K2.3, F-K2.4
- **Haupt-Action:** F-K2.1 (Plant Unit-Cost Discipline)
- **Required entities:** Plant, Product, Production Line, Cost Center
- **Action targets:** Unit cost, material cost %, labor productivity, OpEx
- **Empfohlene_Grain:** **plant_line_product_month**
- **Rationale:** Cost actions target plant/line/product combinations; evidence needs this granularity for cost driver analysis.
- **Feasibility:** ✅ **Covered** – `fact_cost` at `plant_line_product_month` (finance.yaml)
- **Current bracket value:** `transaction_line`

---

### OPS-001: Operations Performance
- **Action codes:** O-O1.1, O-O1.2, O-O1.3, O-O1.4
- **Haupt-Action:** O-O1.1 (Availability Uplift)
- **Required entities:** Plant, Production Line
- **Action targets:** OEE components (Availability, Performance, Quality)
- **Empfohlene_Grain:** **line_day**
- **Rationale:** Operations actions track daily line-level performance; evidence shows line-day metrics for OEE decomposition.
- **Feasibility:** ✅ **Covered** – `fact_ops` at `line_day` (operations.yaml)
- **Current bracket value:** `transaction_line`

---

### OPS-002: Asset Performance
- **Action codes:** O-A2.1, O-A2.2, O-A2.3, O-A2.4, O-A2.5
- **Haupt-Action:** O-A2.1 (Asset Downtime Prevention)
- **Required entities:** Asset, Plant
- **Action targets:** MTBF, MTTR, PM compliance, spare parts availability
- **Empfohlene_Grain:** **failure_event** (or **asset_month** for orchestration view)
- **Rationale:** Asset reliability actions need event-level detail for failure analysis; alternative: asset_month for aggregated view.
- **Feasibility:** ✅ **Covered** – `fact_ops_failures` at `failure_event`; `fact_ops_maintenance` at `maintenance_order` (operations.yaml)
- **Recommendation:** Primary grain `failure_event` for root-cause drill-down; secondary `asset_month` for trend view.
- **Current bracket value:** `transaction_line`

---

### OPS-003: Quality & Yield
- **Action codes:** O-Q3.1, O-Q3.2, O-Q3.3, O-Q3.4, O-Q3.5
- **Haupt-Action:** O-Q3.1 (Scrap & Yield Guardrails)
- **Required entities:** Plant, Production Line, Product
- **Action targets:** FPY, scrap %, rework %, defect density, COPQ, complaint %
- **Empfohlene_Grain:** **line_day** (or **line_month** for aggregated view)
- **Rationale:** Quality actions operate at line/product level; daily grain enables timely intervention.
- **Feasibility:** ✅ **Covered** – `fact_ops` at `line_day`; `fact_quality` likely at similar grain (operations.yaml)
- **Current bracket value:** `transaction_line`

---

### SCM-001: Inventory Performance
- **Action codes:** S-I1.1, S-I1.2, S-I1.3, S-I1.4, S-I1.5
- **Haupt-Action:** S-I1.1 (Inventory Orchestration)
- **Required entities:** SKU, Location, Product Category, Warehouse
- **Action targets:** DIO, turnover, stockout %, obsolete %, forecast accuracy
- **Empfohlene_Grain:** **location_sku_month** (or **location_sku_day** for weekly actions)
- **Rationale:** Inventory actions target SKU-location combinations; month is orchestration grain, but weekly/daily actions (e.g., S-I1.3 stockout prevention) may need finer grain.
- **Feasibility:** ✅ **Covered** – `fact_inventory` at `location_sku_month` and `location_sku_day` (supply_chain.yaml)
- **Recommendation:** **location_sku_month** for orchestration; optionally `location_sku_day` for time-sensitive actions.
- **Current bracket value:** `transaction_line`

---

### SCM-002: Supply Reliability & OTIF
- **Action codes:** S-R2.1, S-R2.2, S-R2.3, S-R2.4, S-R2.5
- **Haupt-Action:** S-R2.1 (OTIF Orchestration)
- **Required entities:** Lane, Distribution Center, SKU, Customer, Carrier
- **Action targets:** OTIF %, on-time %, in-full %, penalty/expedite costs
- **Empfohlene_Grain:** **shipment_line**
- **Rationale:** OTIF actions require shipment-line level detail for on-time and in-full analysis.
- **Feasibility:** ✅ **Covered** – `fact_shipments` at `shipment_line` (supply_chain.yaml)
- **Current bracket value:** `transaction_line`

---

### SCM-003: Forecast vs Actual
- **Action codes:** S-F3.1, S-F3.2, S-F3.3, S-F3.4
- **Haupt-Action:** S-F3.1 (Forecast Accuracy Orchestration)
- **Required entities:** SKU, Location, S&OP Cycle
- **Action targets:** Forecast accuracy %, bias %, MAPE %, service impact %, replan count
- **Empfohlene_Grain:** **sku_location_month**
- **Rationale:** Forecast actions operate at SKU-location-month level for accuracy and bias analysis.
- **Feasibility:** ✅ **Covered** – `fact_forecast` implied at `sku_location_month` (can aggregate from fact_sales + forecast tables in supply_chain.yaml)
- **Current bracket value:** `transaction_line`

---

### XD-001: Service Level Performance
- **Action codes:** X-S1.1, X-S1.2, X-S1.3, X-S1.4
- **Haupt-Action:** X-S1.1 (Service Level Orchestration)
- **Required entities:** Queue, Channel, Agent Group
- **Action targets:** SLA attainment %, FCR %, AHT, backlog, escalation %
- **Empfohlene_Grain:** **case**
- **Rationale:** Service actions need case-level detail for FCR, escalation, and handling-time analysis.
- **Feasibility:** ✅ **Covered** – `fact_support_cases` at `case` grain (experience.yaml)
- **Current bracket value:** `transaction_line`

---

### XD-002: Resource Utilization
- **Action codes:** X-R2.1, X-R2.2, X-R2.3, X-R2.4
- **Haupt-Action:** X-R2.1 (Utilization Orchestration)
- **Required entities:** Queue, Channel, Agent Group, Region
- **Action targets:** Utilization %, occupancy %, shrinkage %, overtime %
- **Empfohlene_Grain:** **agent_day** (or **queue_day**)
- **Rationale:** Workforce actions operate at daily agent/queue level for capacity balancing.
- **Feasibility:** ✅ **Covered** – `fact_workforce_management` at `agent_day` (experience.yaml)
- **Note:** Action codes specify `queue_day` as scope; `agent_day` is finer and supports all queue_day aggregations.
- **Current bracket value:** `transaction_line`

---

### XD-003: Executive KPI Overview
- **Action codes:** X-E3.2, X-E3.3
- **Haupt-Action:** X-E3.2 (Value-at-Risk Escalation)
- **Required entities:** Legal Entity, Region
- **Action targets:** Cross-functional KPIs (GM%, Sales, CLV, SLA, OTIF, CCC, Action Routed Count)
- **Empfohlene_Grain:** **entity_month**
- **Rationale:** Executive use case aggregates cross-domain KPIs at entity-month level for leadership view.
- **Feasibility:** ✅ **Covered** – `fact_exec` at `entity_month` (executive.yaml)
- **Current bracket value:** `transaction_line`

---

## Key Findings

1. **Current placeholder grain (`transaction_line`) is inappropriate for all use cases.** It does not match any governed data contract grain.

2. **All recommended grains are technically covered** by existing data contracts, except:
   - **COM-003** (Customer Value): No dedicated `customer_month` table; can be derived from `fact_sales`.

3. **Grain diversity across domains:**
   - **Commercial:** invoice_line, promotion, customer_month
   - **Finance:** entity_month, plant_line_product_month
   - **Operations:** line_day, failure_event
   - **Supply Chain:** location_sku_month, shipment_line, sku_location_month
   - **Experience:** case, agent_day, entity_month

4. **Action scope vs evidence grain mismatch:** Action codes specify `default_grain` (e.g., `month`) for **trigger evaluation**, but the evidence table should display the **operational grain** (e.g., `invoice_line`, `line_day`) to support drill-down and root-cause analysis.

5. **Governance recommendation:** Update all 15 `UseCase_Bracket.yaml` files to replace `evidence_grain: transaction_line` with the recommended grains above.

---

## Next Steps (if governance update is requested)

1. Update `UseCase_Bracket.yaml` for each use case with the recommended `evidence_grain`.
2. Validate changes with `.\tooling\run_stage1_checks.ps1`.
3. Update semantic models and measure dictionaries if grains change significantly.
4. Consider creating derived `fact_customer_performance` table for COM-003.

---

**Report generated:** 2026-02-13  
**Tool:** Evidence-Grain Audit (Stage 1 governance quality check)

---

## Nachtrag 24.10.2026: Kreuztabelle (`visual_type: matrix`) je Use Case

Seit PR #642 kann `component_300s` eine gestufte Kreuztabelle bestellen
(`visual_type: matrix`, `row_fields`). Pilot: COM-002. Die Sichtung der übrigen 23 Use Cases hat
gemessen, ob die Detailspalten in den Showdaten eine echte Verschachtelung bilden.

**Methode:** duckdb auf `showcases/aurora_group/data/gold` (aktive Dateien aus `_delta_log`).
Aliase aufgelöst mit `ConfigLoader.get_page_config(uc, 'detail')` gegen das gebundene Modell.
`E/K/M` = Eltern / Kinder / Kinder mit mehr als einem Elternteil. M = 0 heißt echte Hierarchie.
Nachgemessen 24.10.2026: COM-002 Category>Subcategory 3/14/1; SCM-003 Zellen AX 14, AY 1,
BX 6, CX 16, CY 3.

**Regel aus Power BI:** Ein TopN-Filter auf Visual-Ebene gehört zum Filterkontext. Damit rechnen
auch die Zwischensummen der äußeren Ebenen nur über die Top-N-Blätter (hergeleitet; Desktop-
Bestätigung offen, siehe `project_mgmt/CLAUDE_CLI_PBI_DESKTOP_TASKS.md` M2).

| UC | Urteil | row_fields (Vorschlag) | Messung (E/K/M, Quelle) | Grund |
|---|---|---|---|---|
| COM-001 | matrix | dim_org.Region > dim_org.Country > dim_org.OrgName | 5/15/0 und 15/99/0 (fact_sales) | Wo-Frage, echte Org-Hierarchie. Heute 15 Zeilen, Top-20 wirkungslos. Category als Slicer. Top-20 auf Stores würde die Zwischensummen verzerren |
| SCM-003 | matrix, `top_n` streichen | dim_product.ABC_Class > XYZ_Class > ProductCode | ABC/XYZ > ProductCode 7/5000/0 (dim). 40 SKUs in 5 Zellen (fact_forecast) | Erst Cluster, dann SKU. Hierarchie 'ABC/XYZ Classification' im Modell schon vorhanden. Top-20 von 40 SKUs verfälscht die Cluster-Summen |
| XD-004 | matrix (umgesetzt 24.10.2026) | fact_action_outcome.domain > action_code_id | 4/15/0 | Erst Domäne, dann Action Code. `outcome_status` aus den Zeilen genommen |
| COM-003 | Tabelle | – | Segment × Channel 5/5/5 | Kreuzklassifikation. Channel filtert den CLV nicht (fact_customer_value nur CustomerKey) |
| COM-004 | Tabelle | – | Mechanic > PromoName 4/29/11 | Frage nach einzelnen Promotions. PromoName ist nicht eindeutig |
| COM-006 | Tabelle | – | Region × Category 5/3/3, 15 Zeilen | Kreuzklassifikation. Store-Ebene sinnlos (ein Channel je Org) |
| FIN-001 | Tabelle | – | fact_AR: 10 Orgs gemischter Ebenen | Gemischte Ebenen zählen in Zwischensummen doppelt |
| FIN-002 | Tabelle | – | 513 Entities. Category konstant (Fashion) | Elementfrage. Category-Spalte ohne Aussage |
| FIN-003 | Tabelle | – | Entity × Cost Center 534/6/6 | Kreuzklassifikation. `cost_center` löst sich nicht auf |
| OPS-001 | Tabelle | – | 8 Assets. Kein Fakt mit Asset und Product | Elementfrage. Category filtert OEE nicht |
| OPS-002 | Tabelle | – | Criticality > Asset 3/10/0 | Hierarchie echt, aber nur 10 Assets |
| OPS-003 | Tabelle | – | fact_quality: 1 Category, 20 SKUs | Keine Dimension für Fehlerarten. Asset nicht an fact_quality |
| SCM-001 | Tabelle | – | Category > ABC 3/3/3 | Kreuzklassifikation. ProductCode fehlt in evidence_columns |
| SCM-002 | Tabelle | – | Customer × Mode 4/3/3 | Kreuzklassifikation, 15 Zeilen |
| XD-001 | Tabelle | – | Queue × IssueType 4/5/5 | Zwei unabhängige Achsen, keine Fall-ID. `top_n` gestrichen 24.10.2026 (keine Spalte über 10 Werte, Top-20 lag auf Severity mit 3) |
| COM-IND-R001 | Tabelle | – | hergeleitet aus COM-001/003 (Aliase nicht einzeln aufgelöst): Region × Category 5/3/3, Segment × Channel 5/5/5 (fact_sales) | Drei unabhängige Attribute, keine Hierarchie |
| COM-IND-R002 | Tabelle | – | hergeleitet aus COM-006: Region × Category 5/3/3, 15 Zeilen | Kreuzklassifikation, Top-20 wirkungslos |
| XD-003 | Tabelle | – | nicht gemessen | `period` löst zu dim_date.Date auf (Tageskörnung) |
| COM-005 | unklar | (nach Modellierung) dim_salesrep.Team > 'Rep Name' | Team > Rep 5/40/0 (Gold) | dim_salesrep fehlt im Modell |
| ESG-001 | unklar | – | nicht messbar | Kein Modell, kein Emissions-Fakt |
| HR-001 | unklar | (ANNAHME) dim_employee_segment.Function > Segment | Function > Segment 5/20/0 (Gold) | Kein HR-Modell. `segment` trifft das Kundensegment |
| SCM-004 | unklar | – | Category > Vendor 8/40/28 | Lieferanten nicht verschachtelt. Kein Modell gebunden |
| XD-002 | unklar | dim_case_queue.Channel > QueueName | Channel > Queue 3/4/0. Org darunter gemischt | Org-Ebene zählt doppelt. Seit 24.10.2026 Spalten Servicekanal vor Queue (Tabelle), `top_n` gestrichen (4 Queues, 32 Zeilen: Top-20 filterte nichts) |

**Ergebnis:** 3 Kandidaten (COM-001, SCM-003, XD-004), 15 Tabellen, 5 unklar wegen fehlender
Modelltabellen. Die Ursachen dafür (falsche Aliase, fehlende Dimensionen, gemischte Org-Ebenen)
stehen in `technical_backlog.md` unter „Page Scaffold Generator“.
