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
# Purchase Price Variance (PPV) & Supplier Performance

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md) - Ziele, KPIs, Action Codes und 3-30-300 Layout.
- [Technical_Factsheet.md](./Technical_Factsheet.md) - Data Contract, Semantic Model, DAX, RLS und QA.

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
