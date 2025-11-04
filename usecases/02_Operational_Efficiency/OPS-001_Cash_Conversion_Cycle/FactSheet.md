---
id: "OPS-001"
title: "Cash Conversion Cycle (DSO + DIO - DPO)"
domain: "Operational Efficiency"
owner: "Head of Finance / Treasury"
impact: "High"
status: "Draft"
last_update: "04.11.2025"
supports_strategic_kpi: ["Working Capital %", "Cash Conversion Cycle", "Operating Cash Flow"]
supports_strategic_kpi_ids: ["ops.working_capital.pct", "ops.working_capital.ccc.days", "fin.cashflow.ocf.amount"]
action_codes: ["W1", "I1", "W2", "O2", "SP1"]
expected_impact: "DSO -5-10 days; DIO -3-7 days; DPO +5-10 days; CCC -5-8 days"
required_kpi_ids: [
  "ops.working_capital.dso.days",
  "ops.working_capital.dio.days",
  "ops.working_capital.dpo.days",
  "ops.working_capital.ccc.days",
  "ops.working_capital.ccc.delta_days"
]
required_kpis:
  ops.working_capital.dso.days: "DSO (Days)"
  ops.working_capital.dio.days: "DIO (Days)"
  ops.working_capital.dpo.days: "DPO (Days)"
  ops.working_capital.ccc.days: "CCC (Days)"
  ops.working_capital.ccc.delta_days: "Î” CCC (Days)"

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

# Cash Conversion Cycle (DSO + DIO - DPO)

## 1. Business Goal
Optimize working capital and liquidity by managing receivables, inventory, and payables efficiency â€” measured through the Cash Conversion Cycle (CCC).

---

## 3. Key Questions
- How long does it take to convert operational investments into cash?
- Which levers drive changes in DSO, DIO, and DPO?
- Which customers or suppliers cause high working capital requirements?
- How does inventory policy affect liquidity?
- What scenarios can shorten the CCC without harming service levels?

---

## 5. Required Attributes (Business-Level)
- Date (month end)
- Org (legal entity, region)
- AR Balance, AP Balance, Inventory Value
- Net Sales Amount, COGS Amount
- Days in Period (calendar mapping)
- Optional: Supplier/Customer, Payment Terms, Country, Currency

---

## 7. Scope & Assumptions
- Balances are period-end values.
- Net Sales and COGS from monthly financials (P&L).
- AR/AP balances reconciled with GL accounts.
- Inventory from end-of-month stock snapshot.
- Currency = EUR; FX translation at closing rate.

---

## 9. Edge Cases & QA Rules
- AR/AP balances cannot be negative.
- DSO capped at [0; 180] days, DIO at [0; 365].
- Referential integrity >= 99.9 % across Date/Org.
- Manual adjustments documented in audit log.
- Currency differences reconciled within +/- 0.5 %.

---

## 11. Typical Actions
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Accelerate collections via credit control and factoring | W1 | DSO -5-10 days |
| Optimize inventory levels and safety stocks | I1 | DIO -3-7 days |
| Negotiate extended supplier terms | W2 | DPO +5-10 days |
| Improve payment discipline and dunning automation | O2 | DSO -2 days; CCC -2 days |
| Align S&OP and Treasury on working capital targets | SP1 | CCC -5-8 days overall |

---

## 13. Related Processes
Order-to-Cash -> Purchase-to-Pay -> Inventory Management -> Treasury Forecasting -> Financial Close.

---

## 15. Cross-References
- Related Use Cases:  
  `[OPS-002 Inventory Health](../OPS-002_Inventory_Health/FactSheet.md)`  
  `[OPS-003 Purchase Price Variance](../OPS-003_Purchase_Price_Variance/FactSheet.md)`  
  `[COM-002 Gross Margin Analysis](../../01_Commercial/COM-002_Gross_Margin_Analysis/FactSheet.md)`  
- Related Documents:  
  [`KPI Catalog`](../../../_includes/kpi_catalog/README.md) | [`Action Codes`](../../../_includes/ActionCodes.md) | [`Glossary`](../../../_includes/Glossary.md)

---

_Last updated: 04.11.2025_



