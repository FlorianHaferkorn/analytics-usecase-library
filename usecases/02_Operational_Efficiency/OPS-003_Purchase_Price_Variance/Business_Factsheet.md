---
id: "OPS-003"
title: "Purchase Price Variance (PPV) & Supplier Performance"
domain: "Operational Efficiency"
owner: "Head of Procurement Controlling"
impact: "High"
status: "Draft"
last_update: "04.11.2025"
maturity: "Pilot"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["COGS % of Sales", "Gross Margin %", "Supplier OTIF %"]
supports_strategic_kpi_ids: ["cost.cogs.amount", "margin.gm.pct", "ops.otif.pct"]
action_codes: ["PC2", "O2", "PC4", "SP1", "PC3"]
expected_impact: "-2-4 % average COGS; +5-10 pp OTIF; +10-20 % verified savings"
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>Plant>Company",
  "Supplier.Group>Vendor",
  "Product.Category>MaterialGroup>Material",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 12M",
  "Org: All",
  "Supplier: All"
]
qa_asserts: ["RI_OK", "Contract_Link_Exists", "PPV_InRange"]
required_kpi_ids: [
  "ops.ppv.pct",
  "ops.ppv.amount",
  "ops.contract.compliance.pct",
  "ops.otif.pct"
]
required_kpis:
  ops.ppv.pct: "PPV %"
  ops.ppv.amount: "PPV Amount"
  ops.contract.compliance.pct: "Contract Compliance %"
  ops.otif.pct: "OTIF %"
data_requirements:
  facts:
    - name: fact_purchase_orders
      grain: po_line_receipt
      primary_key: [PONumber, POLine, ReceiptID]
      required_columns:
        - { name: ReceiptDate, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: SupplierID, type: string, role: supplier_key }
        - { name: MaterialID, type: string, role: product_key }
        - { name: "Actual Unit Price", type: decimal, role: amount }
        - { name: "Contract Unit Price", type: decimal, role: amount }
        - { name: Quantity, type: decimal, role: quantity }
        - { name: Currency, type: string, role: currency }
        - { name: "Delivery Date", type: date, role: helper }
    - name: fact_contracts
      grain: contract_material
      primary_key: [ContractID, MaterialID]
      required_columns:
        - { name: ContractEffectiveDate, type: date, role: date_key }
        - { name: ContractPrice, type: decimal, role: amount }
        - { name: IndexationType, type: string, role: helper }
        - { name: SupplierID, type: string, role: supplier_key }
  dims:
    - name: dim_date
      grain: date
      primary_key: [Date]
    - name: dim_org
      grain: org
      primary_key: [OrgID]
    - name: dim_supplier
      grain: supplier
      primary_key: [SupplierID]
      required_columns:
        - { name: SupplierGroup, type: string }
        - { name: CategoryManager, type: string }
    - name: dim_material
      grain: product
      primary_key: [MaterialID]
      required_columns:
        - { name: MaterialGroup, type: string }
        - { name: Category, type: string }
  relationships:
    - { from: fact_purchase_orders.ReceiptDate, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_purchase_orders.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_purchase_orders.SupplierID, to: dim_supplier.SupplierID, cardinality: many-to-one, direction: single }
    - { from: fact_purchase_orders.MaterialID, to: dim_material.MaterialID, cardinality: many-to-one, direction: single }
    - { from: fact_contracts.SupplierID, to: dim_supplier.SupplierID, cardinality: many-to-one, direction: single }
    - { from: fact_contracts.MaterialID, to: dim_material.MaterialID, cardinality: many-to-one, direction: single }
model_mapping:
  "Actual Unit Price": "fact_purchase_orders[Actual Unit Price]"
  "Contract Unit Price": "fact_purchase_orders[Contract Unit Price]"
  "Quantity": "fact_purchase_orders[Quantity]"
  "Contract Price": "fact_contracts[ContractPrice]"
  "Receipt Date": "fact_purchase_orders[ReceiptDate]"
  "Org": "dim_org[OrgID]"
  "Supplier": "dim_supplier[SupplierID]"
  "Material": "dim_material[MaterialID]"
---

# Purchase Price Variance (PPV) & Supplier Performance - Business Factsheet

## 1. Summary
- **Business Goal:** Control and reduce material costs by identifying deviations between actual and contracted purchase prices, evaluating supplier performance, and enabling proactive negotiation and sourcing actions.
- **Target Audience:** Head of Procurement Controlling
- **Business Priority:** High
- **Expected Impact:** -2-4 % average COGS; +5-10 pp OTIF; +10-20 % verified savings

## 2. Core Questions
- What is the Delta and Delta% between actual and contracted purchase prices?
- Which suppliers or materials contribute most to PPV?
- Are deviations caused by market prices, indexation, or process inefficiencies?
- How reliable are suppliers in pricing and delivery (OTIF, cost adherence)?
- Where should procurement focus renegotiation or rebid efforts?

## 3. KPI Set (Business View)
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| PPV % | (Actual Price - Contract Price) / Contract Price | % | 1 decimal |
| PPV Amount | (Actual Price - Contract Price) * Quantity | EUR | 0 decimals |
| Contract Compliance % | Spend under valid contract / Total spend | % | 1 decimal |
| Supplier OTIF % | On-time, in-full deliveries / Deliveries | % | 1 decimal |
| Savings Verified % | Realized savings / Negotiated savings | % | 1 decimal |

## 4. Business Logic & Thresholds
- Actual and Contract Price must be > 0.
- PPV % capped between [-50%; +100%].
- Missing contract references flagged as 'No Valid Contract'.
- Supplier master reconciles with vendor list; duplicates resolved.
- Referential integrity >= 99.9 % across Date/Org/Supplier/Material.

## 5. Action Codes (Business Perspective)
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Renegotiate supplier terms and pricing | PC2 | COGS -1-3 %; GM % +0.5 pp |
| Enforce contract price adherence and prevent off-contract spend | O2 | Contract Compliance improves; PPV reduces |
| Implement supplier scorecards for cost, quality, delivery | PC4 | OTIF improves; PPV variability reduces |
| Consolidate spend to preferred suppliers | SP1 | Scale leverage improves; COGS reduces |
| Adjust procurement indexation policy | PC3 | PPV volatility reduces 30 % |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for PPV %, PPV Amount, Contract Compliance %, OTIF % with Plan/LY deltas.
- Threshold coloring for immediate outliers.
- Short callout summarizing key variance.

### 6.2 30-Second Layer (Story)
- Trend chart (12-24M) for main KPIs.
- Variance bridge vs Plan/LY by driver.
- Ranking visuals for top/bottom segments.

### 6.3 300-Second Layer (Detail)
- Matrix/table with Org/Product/Customer drill-down.
- Drill-through to transactional detail (orders/invoices).
- Export-ready table including action status.

## 7. Dependencies & Constraints
- PPV = (Actual Price - Contract Price) / Contract Price.
- Contract Price from latest valid agreement effective on order date.
- Exclude freight/overhead unless contractually bundled.
- Currency normalized to EUR using posting date FX.
- Negative PPV (price gain) treated as positive variance for savings tracking.

## 8. Success Criteria
| Dimension | Expected Impact | Measurement |
|------------|-----------------|-------------|
| Cost of Goods | -2-4 % average COGS | vs Plan |
| Supplier Reliability | OTIF +5-10 pp | rolling 3M |
| Compliance | Off-contract spend < 5 % | share of spend |