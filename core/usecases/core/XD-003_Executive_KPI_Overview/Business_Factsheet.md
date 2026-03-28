---
id: XD-003
factsheet_type: business
---

# XD-003 - Executive KPI Overview

## Business Factsheet

> **Canonical KPI definitions:** [core/kpi_catalog/KPI_Catalog.md](../../../kpi_catalog/KPI_Catalog.md).  
> This document is a derived/aggregation view and must not redefine KPI semantics.

---

## 0. Metadata (Mandatory)

- **Use Case ID:** XD-003
- **Domain:** Executive / Cross-Functional
- **Business Owner:** CEO / CFO / COO
- **KPI Owner:** Finance / Strategy / Ops Controlling
- **Decision Owner:** Executive Committee
- **Reporting Level:** Strategic
- **Analytics Stage:** Descriptive / Diagnostic
- **Related Data Contract:** core/data_contracts/domains/executive.yaml
- **Related Semantic Model:** Framework: core/strategy_operating_model/operating_model/semantic_layer.md. Aurora: showcases/aurora_group/semantic_models/Experience.SemanticModel (domain model for XD-*).

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


> Machine-readable KPI + Action configuration has been extracted to `UseCase_Bracket.yaml` (SSOT).
> This factsheet focuses on business context only.


---

## 4. Action Codes (Summary)

Structured summary of action codes (definitions remain in YAML).


> Machine-readable KPI + Action configuration has been extracted to `UseCase_Bracket.yaml` (SSOT).
> This factsheet focuses on business context only.


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




## 10. Typical Decision Scenarios

These scenarios illustrate how this use case drives decisions in practice. They are examples — not exhaustive.

### Scenario A: GM% on Target but Multiple Domains Underperforming

**Situation:** Overall gross margin is +0.5pp vs plan, but drilling into the domain heatmap reveals that Commercial and Operations are both below target, masked by a one-time gain in Finance (favorable FX).

**Decision question:** Should leadership treat this as "on track" or intervene in the underperforming domains before the FX tailwind reverses?

**Who decides:** Executive Leadership Team.

**Consequence of inaction:** FX-driven margin provides temporary cover; structural gaps in COM and OPS compound in following quarters.

**Action Code triggered:** X-E3.2 (Cross-Domain Performance Review) — activates domain-level root-cause drill and action routing to domain leads.

### Scenario B: Action Outcome Rate Below Threshold

**Situation:** Enterprise action routed count is high (45 actions in Q2), but outcome rate is only 38% (target 65%). Value at risk index has increased as unresolved actions accumulate.

**Decision question:** Are actions failing due to unclear ownership, resource constraints, or incorrect trigger thresholds generating false positives?

**Who decides:** Executive Sponsor + Analytics Lead.

**Consequence of inaction:** Action framework loses credibility; teams stop responding to triggers, defeating the purpose of action-ready analytics.

**Action Code triggered:** X-E3.3 (Action Effectiveness Review) — activates action completion funnel analysis and trigger threshold recalibration.
