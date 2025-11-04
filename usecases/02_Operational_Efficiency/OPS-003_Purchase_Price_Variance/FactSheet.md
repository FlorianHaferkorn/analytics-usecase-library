---
id: "OPS-003"
title: "Purchase Price Variance (PPV) & Supplier Performance"
domain: "Operational Efficiency"
owner: "Head of Procurement Controlling"
impact: "High"
status: "Draft"
last_update: "04.11.2025"
supports_strategic_kpi: ["COGS % of Sales", "Gross Margin %", "Supplier OTIF %"]
action_codes: ["PC2", "O2", "PC4", "SP1", "PC3"]
expected_impact: "-2-4 % average COGS; +5-10 pp OTIF; +10-20 % verified savings"
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

dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: ["Org.Region>Area>Store","Product.Category>Subcategory>SKU","Channel","Time.Year>Month>Week"]
filters_default: ["Time: Last 12M","Org: All","Channel: All"]
qa_asserts: ["RI_OK"]

data_requirements:
  facts:
    - name: fact_main
      grain: invoice_line
      primary_key: [InvoiceLineID]
      required_columns:
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: "Units Qty", type: int, role: quantity }
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: Channel, type: string, role: channel }
  dims:
    - name: dim_date
      grain: date
      primary_key: [Date]
    - name: dim_org
      grain: org
      primary_key: [OrgID]
    - name: dim_product
      grain: product
      primary_key: [ProductID]
  relationships:
    - { from: fact_main.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_main.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_main.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }

model_mapping:
  "Net Sales Amount": "fact_main[Net Sales Amount]"
  "Units Qty": "fact_main[Units Qty]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"---

# Purchase Price Variance (PPV) & Supplier Performance

## 1. Business Goal
Control and reduce material costs by identifying deviations between actual and contracted purchase prices, evaluating supplier performance, and enabling proactive negotiation and sourcing actions.

## 3. Key Questions
- What is the Î” and Î”% between actual and contracted purchase prices?  
- Which suppliers or materials contribute most to PPV?  
- Are deviations caused by market prices, indexation, or process inefficiencies?  
- How reliable are suppliers in pricing and delivery (OTIF, cost adherence)?  
- Where should procurement focus renegotiation or rebid efforts?

## 5. Required Attributes (Business-Level)
- Date (purchase order or GR date)  
- Org (plant, region, company)  
- Supplier ID, Supplier Name  
- Material ID, Material Group, Category  
- Actual Unit Price, Contract Unit Price, Quantity, COGS Amount  
- Optional: Indexation Type, Currency, Purchase Order ID, Delivery Date

## 7. Scope & Assumptions
- PPV = (Actual Price - Contract Price) / Contract Price.  
- Contract Price derived from latest valid agreement (effective date <= order date).  
- Exclude freight or overhead costs unless specified in agreement.  
- Currency = EUR; FX translation at posting date.  
- Negative PPV (price gain) treated as positive variance for savings tracking.

## 9. Edge Cases & QA Rules
- Actual and Contract Price must be > 0.  
- PPV % capped between [-50%; +100%].  
- Missing contract references flagged as 'No Valid Contract'.  
- Supplier master must reconcile with vendor list.  
- Referential integrity >= 99.9 % across Date/Org/Supplier/Material.

## 11. Typical Actions
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Renegotiate supplier terms and pricing | PC2 | COGS -1-3 %; GM % +0.5 pp |
| Enforce contract price adherence and prevent off-contract spend | O2 | Contract Compliance improves; PPV reduces |
| Implement supplier scorecards for cost, quality, delivery | PC4 | OTIF improves; PPV variability reduces |
| Consolidate spend to preferred suppliers | SP1 | Scale leverage improves; COGS reduces |
| Adjust procurement indexation policy | PC3 | PPV volatility reduces 30 % |

## 13. Related Processes
Source-to-Contract -> Procure-to-Pay -> Supplier Management -> Financial Planning & Analysis.

## 15. Cross-References
- Related Use Cases:  
  `[OPS-001 Cash Conversion Cycle](../OPS-001_Cash_Conversion_Cycle/FactSheet.md)`  
  `[COM-002 Gross Margin Analysis](../../01_Commercial/COM-002_Gross_Margin_Analysis/FactSheet.md)`  
  `[COR-001 Project ROI Tracking](../../04_Corporate_and_Strategy/COR-001_Project_ROI_and_Benefit_Tracking/FactSheet.md)`  
- Related Documents:  
  [`KPI Catalog`](../../../_includes/kpi_catalog/README.md) | [`Action Codes`](../../../_includes/ActionCodes.md) | [`Glossary`](../../../_includes/Glossary.md)

_Last updated: 04.11.2025_



