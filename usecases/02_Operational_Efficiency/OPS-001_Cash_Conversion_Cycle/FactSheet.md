---
id: "OPS-001"
title: "Cash Conversion Cycle (DSO + DIO - DPO)"
domain: "Operational Efficiency"
owner: "Head of Finance / Treasury"
impact: "High"
status: "Draft"
last_update: "04.11.2025"
maturity: "Pilot"
reporting_level: "Operational"
analytics_stage: "Descriptive"
supports_strategic_kpi: ["Working Capital %", "Cash Conversion Cycle", "Operating Cash Flow"]
supports_strategic_kpi_ids: ["ops.working_capital.pct", "ops.working_capital.ccc.days", "fin.cashflow.ocf.amount"]
action_codes: ["W1", "I1", "W2", "O2", "SP1"]
expected_impact: "DSO -5-10 days; DIO -3-7 days; DPO +5-10 days; CCC -5-8 days"
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>Area>Store",
  "Product.Category>Subcategory>SKU",
  "Channel",
  "Time.Year>Month>Week"
]
filters_default: [
  "Time: Last 12M",
  "Org: All",
  "Channel: All"
]
qa_asserts: ["RI_OK", "DSO_InRange", "CCC_Calculates"]
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
  ops.working_capital.ccc.delta_days: "Δ CCC (Days)"
data_requirements:
  facts:
    - name: fact_working_capital
      grain: period_end
      primary_key: [PeriodEndDate, OrgID]
      required_columns:
        - { name: "AR Balance", type: decimal, role: receivables }
        - { name: "AP Balance", type: decimal, role: payables }
        - { name: "Inventory Value", type: decimal, role: inventory }
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: "COGS Amount", type: decimal, role: amount }
        - { name: "Days In Period", type: int, role: helper }
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
  dims:
    - name: dim_date
      grain: date
      primary_key: [Date]
      required_columns:
        - { name: Year, type: int }
        - { name: Month, type: int }
    - name: dim_org
      grain: org
      primary_key: [OrgID]
      required_columns:
        - { name: Region, type: string }
        - { name: Entity, type: string }
  relationships:
    - { from: fact_working_capital.Date, to: dim_date.Date, cardinality: many-to-one, direction: single, ri_expected: ">=99.9%" }
    - { from: fact_working_capital.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
model_mapping:
  "AR Balance": "fact_working_capital[AR Balance]"
  "AP Balance": "fact_working_capital[AP Balance]"
  "Inventory Value": "fact_working_capital[Inventory Value]"
  "Net Sales Amount": "fact_working_capital[Net Sales Amount]"
  "COGS Amount": "fact_working_capital[COGS Amount]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
---

# Cash Conversion Cycle (DSO + DIO - DPO)

## 1. Business Goal
Optimize working capital and liquidity by managing receivables, inventory, and payables efficiency - measured through the Cash Conversion Cycle (CCC).

---

## 2. Business Context
Working capital ties up cash that could otherwise finance growth or reduce debt. Receivables, inventory, and payables are frequently managed by different teams, which leads to conflicting targets and delayed corrective action. A standardized CCC view aligns Treasury, Sales, Supply Chain, and Procurement on a single narrative of how cash moves through the organization and who owns the levers. This use case provides a transparent drill from corporate CCC to customer, product, and supplier segments so that tactical actions translate directly into liquidity improvements.

---

## 3. Key Questions
- How long does it take to convert operational investments into cash?
- Which levers drive changes in DSO, DIO, and DPO?
- Which customers or suppliers cause high working capital requirements?
- How does inventory policy affect liquidity and service levels?
- What scenarios can shorten the CCC without harming service levels?

---

## 4. Key KPIs
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| DSO (Days) | Accounts Receivable / Net Sales * Days in Period | days | 0 decimals |
| DIO (Days) | Inventory / COGS * Days in Period | days | 0 decimals |
| DPO (Days) | Accounts Payable / COGS * Days in Period | days | 0 decimals |
| Cash Conversion Cycle (Days) | DSO + DIO - DPO | days | 0 decimals |
| Δ CCC (Days) | CCC variance vs Plan or LY | days | +/- sign |

---

## 5. Required Attributes (Business-Level)
- Date (month end)
- Org (legal entity, region)
- AR Balance, AP Balance, Inventory Value
- Net Sales Amount, COGS Amount, Days in Period
- Optional: Customer/Supplier, Payment Terms, Product hierarchy, FX rate

---

## 6. Segmentation & Hierarchies
- Org: Region > Entity > Business Unit
- Customer: Channel > Customer Group > Customer
- Supplier: Category > Supplier > Vendor
- Product: Category > Subcategory > SKU (for DIO analysis)
- Time: Year > Quarter > Month

---

## 7. Scope & Assumptions
- Balances are period-end values aligned with Financial Close.
- Net Sales and COGS derive from the same closing version to avoid mismatches.
- AR/AP balances reconciled with GL accounts; inventory snapshots at standard cost.
- Returns excluded from Net Sales and COGS.
- Currency = EUR; FX translation at closing rate.

---

## 8. Data Freshness & Cadence
- Refresh frequency: daily after month-end close (06:00 CET) plus intra-month preview.
- Latency target: <= 24h after source systems close.
- Historical depth: 36 months for trend analysis.
- Data Owner: Treasury Analytics; Technical Owner: Finance BI.

---

## 9. Edge Cases & QA Rules
- AR/AP balances cannot be negative.
- DSO bounded [0; 180] days, DIO bounded [0; 365] days, DPO bounded [0; 180] days.
- Δ CCC calculated only where Plan CCC > 0.
- Referential integrity >= 99.9 % across Date/Org.
- Manual adjustments documented in audit log; FX differences reconciled within +/- 0.5 %.

---

## 10. Minimum Viable Dataset (MVD)
- Required: Date, Org, AR Balance, AP Balance, Inventory Value, Net Sales Amount, COGS Amount, Days in Period.
- Optional: Customer and Supplier dimensions, Payment Terms, Product hierarchy.
- Extended: Aging buckets, Credit Risk Rating, S&OP scenarios, scenario tags.

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

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|------------|-----------------|-------------|
| Liquidity | CCC -5 to -8 days | vs Prior Quarter |
| Working Capital | DSO -5-10 days; DIO -3-7 days | vs Plan |
| Supplier Relations | DPO +5-10 days without penalty | vs Contract Baseline |

---

## 13. Related Processes
Order-to-Cash -> Purchase-to-Pay -> Inventory Management -> Treasury Forecasting -> Financial Close.

---

## 14. Insights & Learnings
Receivables discipline typically explains more CCC variance than payables negotiations, yet payables actions deliver the fastest wins when coordinated with Procurement. Aligning S&OP buffers with Treasury targets prevents inventory build-up that would otherwise offset AR improvements.

---

## 15. Cross-References
- Related Use Cases:  
  `[OPS-002 Inventory Health](../OPS-002_Inventory_Health/FactSheet.md)`  
  `[OPS-003 Purchase Price Variance](../OPS-003_Purchase_Price_Variance/FactSheet.md)`  
  `[COM-002 Gross Margin Analysis](../../01_Commercial/COM-002_Gross_Margin_Analysis/FactSheet.md)`  
- Related Documents:  
  [`KPI Catalog`](../../../_includes/kpi_catalog/README.md) | [`Action Codes`](../../../_includes/ActionCodes.md) | [`Glossary`](../../../_includes/Glossary.md)

---

## 16. Review Information
| Field | Value |
|--------|--------|
| Business Reviewer | [Name / Role] |
| Technical Reviewer | [Name / Role] |
| Version | v1.0 |
| Review Date | DD.MM.YYYY |
| Review Notes | [Summary of comments] |

---

_Last updated: 04.11.2025_
