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
  ops.working_capital.ccc.delta_days: "Î” CCC (Days)"
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

# Cash Conversion Cycle (DSO + DIO - DPO) - Business Factsheet

## 1. Summary
- **Business Goal:** Optimize working capital and liquidity by managing receivables, inventory, and payables efficiency - measured through the Cash Conversion Cycle (CCC).
- **Target Audience:** Head of Finance / Treasury
- **Business Priority:** High
- **Expected Impact:** DSO -5-10 days; DIO -3-7 days; DPO +5-10 days; CCC -5-8 days

## 2. Core Questions
- How long does it take to convert operational investments into cash?
- Which levers drive changes in DSO, DIO, and DPO?
- Which customers or suppliers cause high working capital requirements?
- How does inventory policy affect liquidity and service levels?
- What scenarios can shorten the CCC without harming service levels?

## 3. KPI Set (Business View)
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| DSO (Days) | Accounts Receivable / Net Sales * Days in Period | days | 0 decimals |
| DIO (Days) | Inventory / COGS * Days in Period | days | 0 decimals |
| DPO (Days) | Accounts Payable / COGS * Days in Period | days | 0 decimals |
| Cash Conversion Cycle (Days) | DSO + DIO - DPO | days | 0 decimals |
| Delta CCC (Days) | CCC variance vs Plan or LY | days | +/- sign |

## 4. Business Logic & Thresholds
- AR/AP balances cannot be negative.
- DSO bounded [0; 180] days, DIO bounded [0; 365] days, DPO bounded [0; 180] days.
- Delta CCC calculated only where Plan CCC > 0.
- Referential integrity >= 99.9 % across Date/Org.
- Manual adjustments documented in audit log; FX differences reconciled within +/- 0.5 %.

## 5. Action Codes (Business Perspective)
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Accelerate collections via credit control and factoring | W1 | DSO -5-10 days |
| Optimize inventory levels and safety stocks | I1 | DIO -3-7 days |
| Negotiate extended supplier terms | W2 | DPO +5-10 days |
| Improve payment discipline and dunning automation | O2 | DSO -2 days; CCC -2 days |
| Align S&OP and Treasury on working capital targets | SP1 | CCC -5-8 days overall |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for DSO (Days), DIO (Days), DPO (Days), CCC (Days), Delta CCC (Days) with Plan/LY deltas.
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
- Balances are period-end values aligned with Financial Close.
- Net Sales and COGS derive from the same closing version to avoid mismatches.
- AR/AP balances reconciled with GL accounts; inventory snapshots at standard cost.
- Returns excluded from Net Sales and COGS.
- Currency = EUR; FX translation at closing rate.

## 8. Success Criteria
| Dimension | Expected Impact | Measurement |
|------------|-----------------|-------------|
| Liquidity | CCC -5 to -8 days | vs Prior Quarter |
| Working Capital | DSO -5-10 days; DIO -3-7 days | vs Plan |
| Supplier Relations | DPO +5-10 days without penalty | vs Contract Baseline |