# XD-003 - Executive KPI Overview
## Business Factsheet (v1.2)

---

## 0. Metadata (Mandatory)
- **Use Case ID:** XD-003
- **Domain:** Executive / Cross-Functional
- **Business Owner:** CEO / CFO / COO
- **KPI Owner:** Finance / Strategy / Ops Controlling
- **Decision Owner:** Executive Committee
- **Reporting Level:** Strategic
- **Analytics Stage:** Descriptive / Diagnostic
- **Related Data Contract:** data_contracts/domains/executive.yaml
- **Related Semantic Model:** semantic_models/domains/executive/model_definition.yaml

---

## 1. Business Summary & Business Value
**Purpose:** Provide a unified, enterprise-wide performance cockpit for leadership.  
**Business Value:** Aggregates critical financial, customer, operational, and people KPIs into one strategic view to assess if the company is on track and to surface cross-domain interventions rapidly via the 3-30-300 navigation.  
**Out of Scope:** Detailed domain diagnostics; operational incident tracking; standalone domain scorecards without executive alignment.

---

## 2. Core Business Questions
- Are we growing profitably and in line with the strategic plan?
- Is margin performance healthy across price, mix, and cost structures?
- Are we delivering expected value to customers?
- Is our supply chain reliable and stable?
- Are we operating with sufficient working capital efficiency?
- Are digital tools adopted at scale?
- Are we retaining and developing key talent?

---

## 3. Required KPIs (Mandatory)
All KPIs must exist in the KPI Catalog.

```yaml
required_kpis:
  - id: sales.net_sales_growth.pct
    name: Net Sales Growth %
    purpose: Show topline growth vs plan and prior year.
    definition_short: Percentage change in net sales vs plan or prior period.
    unit: "%"
    grain: month
    agg: avg
    target: Strategic growth target per entity/region
    interpretation: Higher is better; negative indicates revenue risk.
    lineage: fact_revenue[Net Sales Amount], plan/LY reference in finance data
  - id: margin.gross_margin.pct
    name: Gross Margin %
    purpose: Track profitability after cost of goods sold.
    definition_short: Gross Margin % = Gross Margin Amount / Net Sales Amount.
    unit: "%"
    grain: month
    agg: avg
    target: Margin target by entity/region
    interpretation: Higher is better; sustained decline signals margin leakage.
    lineage: fact_finance[Gross Margin Amount], fact_revenue[Net Sales Amount]
  - id: customer.value.clv.amount
    name: Customer Lifetime Value
    purpose: Measure expected lifetime profit per customer.
    definition_short: Discounted gross profit per customer over expected lifetime.
    unit: "€"
    grain: month (reported), customer-level calculation upstream
    agg: avg
    target: Strategic CLV target per segment
    interpretation: Higher indicates stronger customer value creation.
    lineage: fact_customer_value[CLV Amount]
  - id: service.level_pct
    name: Service Level %
    purpose: Reflect service reliability to customers.
    definition_short: Share of fulfilled demand without stockout at requested time.
    unit: "%"
    grain: month
    agg: avg
    target: Service level SLO per channel/region
    interpretation: Higher is better; low values drive churn risk.
    lineage: fact_service[Service Level %], fact_fulfillment for calculation check
  - id: supply.otif.pct
    name: OTIF %
    purpose: Measure supply reliability.
    definition_short: Orders delivered on time and in full / total orders.
    unit: "%"
    grain: month (order-level base)
    agg: avg
    target: OTIF target per lane/region
    interpretation: Higher is better; low OTIF triggers capacity/root-cause actions.
    lineage: fact_fulfillment[OTIF Flag], fact_fulfillment[Order Qty]
  - id: liquidity.ccc.days
    name: Cash Conversion Cycle (Days)
    purpose: Measure working-capital efficiency end-to-end.
    definition_short: CCC = DSO + DIO - DPO.
    unit: days
    grain: month
    agg: avg
    target: CCC target per entity
    interpretation: Lower is better; rising CCC signals cash risk.
    lineage: fact_wc[CCC Days] derived from AR/AP/Inventory facts
  - id: people.digital_adoption.pct
    name: Digital Adoption %
    purpose: Track active usage of core digital tools.
    definition_short: Active users / eligible users for core digital tools.
    unit: "%"
    grain: month
    agg: avg
    target: Adoption target per function
    interpretation: Higher is better; low adoption blocks scaling of efficiencies.
    lineage: fact_digital[Active Users], fact_digital[Eligible Users]
  - id: people.attrition_risk.pct
    name: Attrition Risk %
    purpose: Monitor risk of losing key talent.
    definition_short: Probability of attrition across key roles or segments.
    unit: "%"
    grain: month
    agg: avg
    target: Risk tolerance per segment
    interpretation: Lower is better; high risk requires retention action.
    lineage: fact_hr[Attrition Risk %], fact_hr[Leavers], fact_hr[Headcount]
```

---

## 4. Business Logic & Thresholds

### 4.1 Logic Description
- Flag deviations vs plan/target for growth, margin, service, supply reliability, working capital, digital adoption, and attrition risk.
- Escalate cross-domain interventions through predefined Action Codes with accountable owners.
- Prioritise entities/regions with highest value-at-risk and customer impact.

### 4.2 Formal Trigger Rules (Machine-Readable)
```yaml
triggers:
  - kpi: sales.net_sales_growth.pct
    condition: below_plan
    threshold: plan_delta_pct
    scope: Org/Region, Month
    exclusion: none
    action_code: P4 Price Repositioning
  - kpi: margin.gross_margin.pct
    condition: below_target
    threshold: margin_target_pct
    scope: Org/Region, Month
    exclusion: promo periods where approved
    action_code: P2 Margin Leakage Correction
  - kpi: customer.value.clv.amount
    condition: declining
    threshold: negative_trend_3m
    scope: Segment, Customer
    exclusion: newly onboarded customers (<90 days)
    action_code: C2 Retention Action
  - kpi: supply.otif.pct
    condition: below_target
    threshold: otif_sla_pct
    scope: Lane/Region, Month
    exclusion: force majeure
    action_code: S3 Capacity Intervention
  - kpi: service.level_pct
    condition: below_target
    threshold: service_slo_pct
    scope: Channel/Region, Month
    exclusion: planned maintenance windows
    action_code: S3 Capacity Intervention
  - kpi: liquidity.ccc.days
    condition: above_target
    threshold: ccc_target_days
    scope: Entity, Month
    exclusion: none
    action_code: F1 Cash Collection Initiative
  - kpi: people.digital_adoption.pct
    condition: below_target
    threshold: adoption_target_pct
    scope: Function/Region, Month
    exclusion: newly deployed tools (<30 days)
    action_code: H1 Digital Enablement Push
  - kpi: people.attrition_risk.pct
    condition: above_threshold
    threshold: attrition_risk_tolerance_pct
    scope: Critical Roles/Region, Month
    exclusion: seasonal/temporary workforce
    action_code: C2 Retention Action
```

---

## 5. Action Codes (Mandatory)

| Action Code | Name | Trigger (formal) | Description | Expected KPI Impact | Level (L1/L2/L3) | Owner |
|-------------|------|------------------|-------------|---------------------|------------------|-------|
| P2 | Margin Leakage Correction | margin.gross_margin.pct below target | Address mix/discounts/leakage to restore margin | Increase GM%, stabilise revenue | L2 | Finance / Sales Ops |
| P4 | Price Repositioning | sales.net_sales_growth.pct below plan | Adjust price/pack/discount to recover growth without eroding margin | Increase Net Sales Growth %, stable GM% | L2 | Commercial |
| C2 | Retention Action | customer.value.clv.amount declining OR people.attrition_risk.pct above threshold | Targeted retention playbooks for customers or critical talent | Increase CLV, reduce Attrition Risk | L2 | CX / HR |
| S3 | Capacity Intervention | supply.otif.pct or service.level_pct below target | Short-term capacity, expediting, rerouting, or supplier escalation | Increase OTIF %, Increase Service Level % | L2 | Supply Chain |
| F1 | Cash Collection Initiative | liquidity.ccc.days above target | Accelerate receivables, extend payables where possible, optimise inventory | Reduce CCC Days | L2 | Finance |
| H1 | Digital Enablement Push | people.digital_adoption.pct below target | Training, comms, incentives to lift active digital usage | Increase Digital Adoption %, Increase productivity | L2 | IT / HR |

---

## 6. 3-30-300 Page Layout (Mandatory)

### 6.1 3-Second Layer (KPI Cards)
- Net Sales Growth %
- Gross Margin %
- Customer Lifetime Value
- OTIF %
- Service Level %
- Cash Conversion Cycle (Days)
- Digital Adoption %
- Attrition Risk %

### 6.2 30-Second Layer (Main Visuals)
| Visual Name | Visual Type | X-Axis | Y-Axis | Segment | Default Filter | Notes |
|-------------|-------------|--------|--------|---------|----------------|-------|
| Executive Trend | Line | Date[Month] | All 8 KPI measures | Org / Region | 12-24M | Trend vs Plan/LY bands |
| Driver Variance | Clustered/Waterfall | Drivers | KPI variance | Org / Segment | Recent period | Focus on growth/margin/service drivers |

### 6.3 Required Slicers (Mandatory)
- Date (Month/Year)
- Org / Region / Entity
- Product or Customer Segment (where relevant)
- Function / Department (for People KPIs)

### 6.4 300-Second Layer (Diagnostics)
- Domain drilldowns by Org/Region/Segment with variance decomposition (price, mix, volume, cost, service).
- Root-cause tables for OTIF/Service failures (lane, supplier, reason code).
- Working-capital driver table (DSO, DIO, DPO contributors).
- Digital adoption cohort analysis (role, tool, region).
- Attrition risk drivers (role, tenure, performance band).

---

## 7. Data Requirements Summary
```yaml
required_facts:
  - fact_revenue
  - fact_finance
  - fact_customer_value
  - fact_service
  - fact_fulfillment
  - fact_wc
  - fact_digital
  - fact_hr
required_dimensions:
  - dim_date
  - dim_org
  - dim_product
  - dim_customer
  - dim_employee
required_grain: month (with order-level base for OTIF and service where applicable)
required_time_range: minimum 24 months history with plan/LY references
required_slicers: Date, Org/Region/Entity, Product or Customer Segment, Function/Department
```

---

## 8. Dependencies, Assumptions & Constraints
- Executive KPIs align with certified strategic reporting; definitions mirror the KPI Catalog.
- Plan/LY references must be available for all headline KPIs.
- Conformed dimensions (Date, Org, Product, Customer, Employee) are mandatory for cross-domain joins.
- Service level and OTIF rely on accurate fulfillment flags; CCC depends on upstream AR/AP/Inventory.
- Digital adoption and attrition risk depend on HR/IT systems providing timely updates (at least monthly).

---

## 9. Success Criteria
- Impact: Net Sales Growth % and Gross Margin % on/above target; CCC Days on/under target.
- Adoption: Executive dashboard used in formal exec meeting cadence (weekly/monthly).
- Quality: 100% KPI certification and plan/LY availability; RLS applied correctly for exec roles.
- Decision Frequency: At least monthly executive review with documented action-code follow-ups.

---

## 10. Risks & Wrong Interpretations (Short)
- Misalignment of KPI definitions across domains could lead to conflicting executive narratives.
- Incomplete plan/LY data would misstate growth and margin performance.
- Over-rotating on single KPIs without cross-checking drivers (e.g., margin vs service) could trigger suboptimal actions.

---
