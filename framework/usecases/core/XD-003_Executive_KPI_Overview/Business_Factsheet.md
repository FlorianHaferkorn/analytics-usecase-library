---
id: XD-003
factsheet_type: business
---

# XD-003 - Executive KPI Overview

## Business Factsheet

---

## 0. Metadata (Mandatory)

- **Use Case ID:** XD-003
- **Domain:** Executive / Cross-Functional
- **Business Owner:** CEO / CFO / COO
- **KPI Owner:** Finance / Strategy / Ops Controlling
- **Decision Owner:** Executive Committee
- **Reporting Level:** Strategic
- **Analytics Stage:** Descriptive / Diagnostic
- **Related Data Contract:** framework/framework/framework/data_contracts/domains/executive.yaml
- **Related Semantic Model:** framework/framework/framework/semantic_models/core_action_ready/model_definition.yaml

---

## 1. Business Summary

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

  - id: sales.net_sales.delta_pct.ly
    kpi_catalog_id: Growth
    name: Net Sales % vs LY
    purpose: Show topline growth vs last year.
    agg: avg

  - id: margin.gm.pct
    name: Gross Margin %
    purpose: Track profitability after cost of goods sold.
    agg: avg

  - id: crm.clv.amount
    name: Customer Lifetime Value Amount
    purpose: Measure expected lifetime profit per customer.
    agg: avg

  - id: svc.sla.attainment.pct
    name: SLA Attainment %
    purpose: Reflect service reliability to customers.
    agg: avg

  - id: ops.otif.pct
    name: OTIF %
    purpose: Measure supply reliability.
    agg: avg

  - id: ops.working_capital.ccc.days
    name: Cash Conversion Cycle (Days)
    purpose: Measure working-capital efficiency end-to-end.
    agg: avg

  - id: people.digital_adoption.pct
    name: Digital Adoption %
    purpose: Track active usage of core digital tools.
    agg: avg

  - id: people.attrition_risk.pct
    name: Attrition Risk %
    purpose: Monitor risk of losing key talent.
    agg: avg

  - id: enterprise.action_routed.count
    name: Actions Routed Count
    purpose: Execution volume
    agg: sum

  - id: enterprise.action_outcome_rate.pct
    name: Action Outcome Rate %
    purpose: Execution effectiveness
    agg: avg

  - id: enterprise.value_at_risk.index
    name: Enterprise Value-at-Risk Index
    purpose: Cross-domain risk concentration
    agg: avg
```

---

## 4. Action Codes (Summary)

Structured summary of action codes (definitions remain in YAML).

```yaml
action_codes:

  - id: X-E3.2
    name: Cross-Domain Risk Prioritisation
    purpose: Prioritise Cross-Domain Performance Risk by Value-at-Risk
    status: active
    owner: Head of Enterprise Controlling
    trigger_kpis: [sales.revenue.growth_pct, margin.gm.pct, svc.sla.attainment.pct, supply.otif.pct, wc.ccc.days, people.attrition_risk.pct]
    guardrail_kpis: []
    outcome_kpis: [enterprise.value_at_risk.index]
    impact_range: enterprise.value_at_risk.index: -10.0--30.0 %
    levels: L1-L3

  - id: X-E3.3
    name: Action Follow-up & Outcome Governance
    purpose: Ensure Routed Actions Are Executed and Outcomes Measured
    status: active
    owner: Chief of Staff / PMO Lead
    trigger_kpis: [enterprise.action_routed.count]
    guardrail_kpis: []
    outcome_kpis: [enterprise.action_outcome_rate.pct]
    impact_range: enterprise.action_outcome_rate.pct: 10.0-25.0 pp
    levels: L1-L3
```

---

## 5. 3-30-300 Page Layout (Mandatory)

### 5.1 3-Second Layer (KPI Cards)

- Net Sales % vs LY
- Gross Margin %
- Customer Lifetime Value Amount
- OTIF %
- SLA Attainment %
- Cash Conversion Cycle (Days)
- Digital Adoption %
- Attrition Risk %

### 5.2 30-Second Layer (Main Visuals)

| Visual Name | Visual Type | X-Axis | Y-Axis | Segment | Default Filter | Notes |
|-------------|-------------|--------|--------|---------|----------------|-------|
| Executive Trend | Line | Date[Month] | All 8 KPI measures | Org / Region | 12-24M | Trend vs Plan/LY bands |
| Driver Variance | Clustered/Waterfall | Drivers | KPI variance | Org / Segment | Recent period | Focus on growth/margin/service drivers |

### 5.3 Required Slicers (Mandatory)

- Date (Month/Year)
- Org / Region / Entity
- Product or Customer Segment (where relevant)
- Function / Department (for People KPIs)

### 5.4 300-Second Layer (Diagnostics)

- Domain drilldowns by Org/Region/Segment with variance decomposition (price, mix, volume, cost, service).
- Root-cause tables for OTIF/Service failures (lane, supplier, reason code).
- Working-capital driver table (DSO, DIO, DPO contributors).
- Digital adoption cohort analysis (role, tool, region).
- Attrition risk drivers (role, tenure, performance band).

---

## 6. Data Requirements Summary

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

## 7. Dependencies, Assumptions & Constraints

- Executive KPIs align with certified strategic reporting; definitions mirror the KPI Catalog.
- Plan/LY references must be available for all headline KPIs.
- Conformed dimensions (Date, Org, Product, Customer, Employee) are mandatory for cross-domain joins.
- Service level and OTIF rely on accurate fulfillment flags; CCC depends on upstream AR/AP/Inventory.
- Digital adoption and attrition risk depend on HR/IT systems providing timely updates (at least monthly).

---

## 8. Success Criteria

- Impact: Net Sales % vs LY and Gross Margin % on/above target; CCC Days on/under target.
- Adoption: Executive dashboard used in formal exec meeting cadence (weekly/monthly).
- Quality: 100% KPI certification and plan/LY availability; RLS applied correctly for exec roles.
- Decision Frequency: At least monthly executive review with documented action-code follow-ups.

---

## 9. Risks & Wrong Interpretations (Short)

- Misalignment of KPI definitions across domains could lead to conflicting executive narratives.
- Incomplete plan/LY data would misstate growth and margin performance.
- Over-rotating on single KPIs without cross-checking drivers (e.g., margin vs service) could trigger suboptimal actions.



