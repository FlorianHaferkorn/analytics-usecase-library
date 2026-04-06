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

### 3. KPI & Action Code Overview

| KPI ID | Role |
|--------|------|
| enterprise.value_at_risk.index | Strategic |
| margin.gm.pct | Influencing |
| sales.net_sales.delta_pct.ly | Influencing |
| crm.clv.amount | Influencing |
| svc.sla.attainment.pct | Influencing |
| ops.otif.pct | Influencing |
| ops.working_capital.ccc.days | Influencing |
| people.digital_adoption.pct | Influencing |
| people.attrition_risk.pct | Influencing |
| cost.cogs.amount | Supporting |
| sales.net_sales.amount | Supporting |
| supply.otif.pct | Supporting |

**Action Codes:** X-E3.2

> Full machine-readable configuration in `UseCase_Bracket.yaml` (SSOT).

---

## 4. Action Codes (Summary)

Structured summary of action codes (definitions remain in YAML).


> Machine-readable KPI + Action configuration has been extracted to `UseCase_Bracket.yaml` (SSOT).
> This factsheet focuses on business context only.


---

## 5. 3-30-300 Page Layout (Mandatory)

### 5.1 3-Second Layer (KPI Cards)

- Net Sales % vs LY
- Enterprise Value-at-Risk Index
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
| Executive Trend | Line | Date[Month] | Enterprise Value-at-Risk Index + selected driver KPIs | Org / Region | 12-24M | Trend vs Plan/LY bands |
| Driver Variance | Clustered/Waterfall | Drivers | KPI variance | Org / Segment | Recent period | Focus on growth, margin, service, working-capital and people drivers |

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
- Cross-domain risk prioritisation table with top entities ranked by enterprise value-at-risk and material driver contribution.

---

## 6. Data Requirements Summary

- Required facts: executive summary aggregates for revenue, margin, customer value, service, fulfillment, working capital, digital adoption, and people risk signals.
- Required dimensions: date, organization/entity, product, customer, employee.
- Required grain: entity_month, with lower-grain operational sources rolled up into executive comparators where needed.
- Required time range: minimum 24 months with plan and prior-year references.
- Required slicers: Date, Org/Region/Entity, Product or Customer Segment, Function/Department.

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

### Scenario B: Service and Working-Capital Signals Deteriorate Together

**Situation:** OTIF drops below target in two regions while cash conversion cycle lengthens at the same time. The enterprise value-at-risk index rises even though gross margin remains stable.

**Decision question:** Which entities require immediate executive attention when service reliability and working-capital pressure deteriorate together?

**Who decides:** Executive Leadership Team.

**Consequence of inaction:** Service erosion and cash pressure reinforce each other; enterprise downside grows before domains react in a coordinated way.

**Action Code triggered:** X-E3.2 (Cross-Domain Risk Prioritisation) — ranks the most material entity-domain combinations so leadership can intervene where service and cash signals combine into enterprise downside first.
