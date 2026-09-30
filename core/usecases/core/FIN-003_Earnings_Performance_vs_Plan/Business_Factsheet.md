---
id: FIN-003
factsheet_type: business
---

# FIN-003 - Earnings Performance vs Plan

## Business Factsheet

---

## 0. Metadata (Mandatory)

- **Use Case ID:** FIN-003
- **Domain:** Finance
- **Business Owner:** Chief Financial Officer
- **KPI Owner:** Finance Controlling / FP&A
- **Reporting Level:** Tactical
- **Analytics Stage:** Diagnostic / Prescriptive
- **Related Data Contract:** core/data_contracts/domains/finance.yaml

---

## 1. Business Summary

**Purpose:** Steer consolidated earnings to plan by decomposing the EBITDA-margin gap into revenue, gross-margin and opex drivers.
**Business Value:** A single earnings-vs-plan view that routes the recovery to the actual driver instead of a blanket cost cut.
**Out of Scope:** Cash & liquidity steering (FIN-001); unit-cost deep dive (FIN-002); statutory reporting (out of scope).

---

## 2. Core Business Questions

- Is EBITDA margin on plan this period?
- Is the gap revenue, gross margin or opex?
- Which entities and cost centres drive the shortfall?

---

### 3. KPI & Action Code Overview

| KPI ID | Role |
|--------|------|
| KPI-FIN-018 | Strategic |
| KPI-FIN-021 | Influencing |
| KPI-COM-009 | Influencing |
| KPI-COM-013 | Influencing |
| KPI-FIN-014 | Influencing |
| KPI-FIN-020 | Supporting |
| KPI-FIN-009 | Supporting |

**Action Codes:** F-E1.1

> Full machine-readable configuration in `UseCase_Bracket.yaml` (SSOT).

---

### 3.1 Standards basis

The headline KPIs reference these external standards — *reference, don't redefine* (full alignment & drift audit under `core/kpi_catalog/standards/`):

- **EBITDA Margin** (`KPI-FIN-018`) → **ESMA-APM** (none): EBITDA is NOT defined by IFRS. It is an Alternative Performance Measure: under the ESMA APM Guidelines it must be labelled as non-GAAP, reconciled to the most directly reconcilable IFRS line item, and shown with a comparative. Under IFRS 18 (eff. 1 Jan 2027) an EBITDA-type figure used in public communication is a Management-defined Performance Measure (MPM) requiring a dedicated reconciliation note to the nearest IFRS subtotal — IFRS 18's closest defined analogue is OPDAI ('operating profit before depreciation, amortisation and impairments'). Do not present as an IFRS metric.
- **EBITDA Margin vs Plan** (`KPI-FIN-021`) → **ESMA-APM** (partial): EBITDA-vs-plan variance is an APM comparison; ESMA APM Guidelines require consistent, reconciled definition period-over-period.
- **Net Sales % vs Plan** (`KPI-COM-009`) → **IFRS 15** (none): Net-sales-vs-plan is an internal budget-variance metric; the actual base is IFRS 15 revenue, the variance is convention.
- **Gross Margin %** (`KPI-COM-013`) → **ESMA-APM** (partial): A ratio of two IFRS figures (IFRS 15 revenue, IAS 2 cost of sales); the percentage itself is a non-GAAP APM. Inputs are IFRS-clean — label the ratio as an APM in external reporting.
- **OpEx vs Plan %** (`KPI-FIN-014`) → **IFRS** (none): Internal budget-variance management metric; no external financial-reporting standard defines it. Actual and plan inputs trace to IAS 1 operating expenses.
- **EBITDA** (`KPI-FIN-020`) → **ESMA-APM** (partial): EBITDA is not defined by IFRS; ESMA APM Guidelines govern its disclosure. Reconcile to the nearest IFRS line (operating profit) per ESMA.
- **Operating Cash Flow** (`KPI-FIN-009`) → **IFRS** (exact): Maps to the IAS 7 operating-activities cash-flow section. Aligns; IAS 7 permits the direct or indirect method — pin which one is used so period-over-period comparisons are stable.

---

## 6. Data Requirements Summary

This use case is **new**: its KPIs are governed and standards-grounded, but the backing
Aurora synthetic data does not yet exist. The precise required tables/columns are recorded
per KPI (`technical.calculation.reason`) and consolidated in
`internal/project_mgmt/AURORA_SYNTHETIC_DATA_GAPS.md`. Until that data lands, the KPIs
report `UNCOMPUTED` (ADR-0009), never a fabricated value.

---

## 8. Success Criteria

- Benchmark: EBITDA margin at or above plan; opex-to-plan variance within tolerance band.
- Impact: earnings gap closed at the driver; no indiscriminate cost cutting.
- Decision frequency: monthly close review.
