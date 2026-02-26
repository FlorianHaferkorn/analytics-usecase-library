---
id: <USE CASE ID>
factsheet_type: business
---
# [ID] - [Title]

## Business Factsheet

---

## 0. Metadata (Mandatory)

- **Use Case ID:** [e.g., COM-001]
- **Domain:** [e.g., Commercial]
- **Business Owner:** [e.g., CCO / Head of Sales]
- **KPI Owner:** [e.g., Commercial Controlling Lead]
- **Decision Owner:** [e.g., Sales Leadership Team]
- **Reporting Level:** [Tactical / Strategic / Operational]
- **Analytics Stage:** [Descriptive / Diagnostic / Predictive / Prescriptive]
- **Related Data Contract:** [e.g., core/data_contracts/domains/commercial_sales.yaml]
- **Related Semantic Model:** [Framework and/or Aurora domain model reference.]

---

## 1. Business Summary

**Purpose:** [1–2 sentences: what business problem this use case solves.]

**Business Value:** [Measurable impact, e.g. "Reduction of discount leakage by 2%".]

**Out of Scope:** [What this use case does NOT cover.]

---

## 2. Core Business Questions

- [Question 1 the user should answer in 5 minutes]
- [Question 2]
- [Question 3]

---

## 3. Required KPIs (Mandatory)

All KPIs must exist in the KPI Catalog.

> Machine-readable KPI + Action configuration lives in `UseCase_Bracket.yaml` (SSOT). This factsheet focuses on business context only.

---

## 4. Action Codes (Summary)

Structured summary of action codes (definitions remain in YAML).

> Machine-readable config in `UseCase_Bracket.yaml` (SSOT).

---

## 5. 3-30-300 Page Layout (Mandatory)

### 5.1 3-Second Layer (KPI Cards)

- [KPI card 1]
- [KPI card 2]
- [Further cards]

### 5.2 30-Second Layer (Main Visuals)

- **[Visual name]**
  - Visual Type: [e.g., Line, Waterfall, Column]
  - X-Axis / Y-Axis / Segment / Default Filter / Notes

### 5.3 Required Slicers (Mandatory)

- [Date (Month/Quarter)]
- [Region / Channel]
- [Further slicers]

### 5.4 300-Second Layer (Diagnostics)

- [Evidence table, action panel, drill-down description.]

---

## 6. Data Requirements Summary

```yaml
required_facts: []
required_dimensions: []
required_grain: ""
required_time_range: ""
required_slicers: ""
```

---

## 7. Dependencies, Assumptions & Constraints

- [Assumption 1]
- [Constraint 2]
- [Data/conformance requirements.]

---

## 8. Success Criteria

- **Impact:** [Measurable outcome.]
- **Adoption:** [Who uses it; how often.]
- **Quality:** [Reconciliation, tolerance.]
- **Decision Frequency:** [e.g., Monthly/Quarterly.]

---

## 9. Risks & Wrong Interpretations (Short)

- [Risk 1: e.g., misstated Plan/LY leading to false gaps.]
- [Risk 2]
- [How to avoid wrong interpretations.]

---
