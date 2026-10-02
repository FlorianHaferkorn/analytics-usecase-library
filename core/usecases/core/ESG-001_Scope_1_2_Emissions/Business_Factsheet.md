---
id: ESG-001
factsheet_type: business
---

# ESG-001 - Scope 1+2 Emissions

## Business Factsheet

---

## 0. Metadata (Mandatory)

- **Use Case ID:** ESG-001
- **Domain:** ESG
- **Business Owner:** Head of Sustainability
- **KPI Owner:** Sustainability Controlling
- **Reporting Level:** Strategic
- **Analytics Stage:** Descriptive / Diagnostic
- **Related Data Contract:** core/data_contracts/domains/esg.yaml

---

## 1. Business Summary

**Purpose:** Show whether greenhouse-gas emissions from own operations and purchased energy (Scope 1+2) fall, and which sites and scopes carry the total.
**Business Value:** One governed Scope 1+2 figure per site and scope that the reduction programme and the sustainability report can both read.
**Out of Scope:** Scope 3 emissions; the full ESRS E1-6 disclosure (this use case carries the Scope 1+2 subtotal only); supplier ESG due diligence (KPI-ESG-002 in SCM-004).

---

## 2. Core Business Questions

- Are Scope 1+2 emissions falling year over year?
- Is own combustion (Scope 1) or purchased energy (Scope 2) the larger share?
- Which sites and scopes should the reduction programme target first?

---

### 3. KPI & Action Code Overview

| KPI ID | Role |
|--------|------|
| KPI-ESG-001 | Strategic |

**Action Codes:** none yet — no action code in the framework covers emission-reduction measures.

> Full machine-readable configuration in `UseCase_Bracket.yaml` (SSOT).

---

### 3.1 Standards basis

The headline KPIs reference these external standards — *reference, don't redefine* (full alignment & drift audit under `core/kpi_catalog/standards/`):

- **Scope 1+2 CO2 Emissions** (`KPI-ESG-001`) → **GHG Protocol** (partial): Scope boundaries follow the GHG Protocol Corporate Standard; its Scope 2 Guidance asks for both location-based and market-based Scope 2 figures, this KPI carries the market-based one only.
- **Scope 1+2 CO2 Emissions** (`KPI-ESG-001`) → **ESRS E1** (partial): ESRS E1-6 discloses Scope 1, Scope 2 and Scope 3 separately plus a total; this KPI is the Scope 1+2 subtotal and not a full E1-6 disclosure.

---

## 5. 3-30-300 Page Layout (Mandatory)

### 5.1 3-Second Layer (KPI Cards)

- Scope 1+2 CO2 Emissions (KPI-ESG-001) as KPI card with the delta to the prior year.

### 5.2 30-Second Layer (Main Visuals)

- Scope 1+2 emissions over time as a line chart.
- Scope 1 and Scope 2 over time as a line chart split by scope.
- Scope 1+2 emissions by site as a bar chart.

### 5.4 300-Second Layer (Diagnostics)

- Exception table by site and scope, highest emissions first, Top 20.

---

## 6. Data Requirements Summary

This use case is **new**: its KPI is governed and standards-grounded, but it cannot be
computed yet. The emission data is defined in the ESG data contract (`fact_emissions`,
`dim_emission_scope`), which is a structured placeholder; the KPI's filtered sum by scope
is not yet expressible in the calculation grammar (`technical.calculation.reason`). Until
both are resolved the KPI reports `UNCOMPUTED` (ADR-0009), never a fabricated value.

---

## 8. Success Criteria

- Benchmark: none governed; reduction targets are set per company and are not part of the catalog.
- Impact: Scope 1+2 emissions are reported per site and scope from governed sources, with the Scope 2 method (market-based) stated next to the value.
- Adoption: used in the quarterly emission review by sustainability controlling.
- Decision frequency: quarterly emission review, annual inventory consolidation.

---

## 9. Risks & Wrong Interpretations (Short)

- Market-based only: the catalog KPI carries market-based Scope 2; a fall can come from purchased certificates rather than lower energy use. State the method next to the value.
- Annual inventory: in-year values are incomplete until the annual consolidation.
- Absolute, not intensity: lower emissions after a site closure or lower output are not efficiency gains.

---

## 10. Typical Decision Scenarios

### Scenario 1: Total flat despite reduction measures

**Situation:** the Scope 1+2 total does not fall although reduction measures run at several sites.

**Decision question:** do the measures sit in sites with a small share of the total?

**Who decides:** sustainability controlling with the site managers.

### Scenario 2: Scope 2 falls, Scope 1 does not

**Situation:** Scope 2 falls after a change in the energy contract while Scope 1 stays flat.

**Decision question:** which sites need fuel switching or process changes, now that the purchasing lever is used?

**Who decides:** head of sustainability with operations.
