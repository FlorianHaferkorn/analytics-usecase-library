---
id: HR-001
factsheet_type: business
---

# HR-001 - Workforce Performance & Retention

## Business Factsheet

---

## 0. Metadata (Mandatory)

- **Use Case ID:** HR-001
- **Domain:** People & Culture
- **Business Owner:** Chief People Officer / Head of HR
- **KPI Owner:** HR Controlling / People Analytics
- **Reporting Level:** Tactical
- **Analytics Stage:** Diagnostic / Prescriptive
- **Related Data Contract:** core/data_contracts/domains/people.yaml

---

## 1. Business Summary

**Purpose:** Improve workforce stability and productivity by lowering voluntary attrition, raising engagement, and containing workforce cost and absence.
**Business Value:** Lower replacement cost, protected delivery capacity, and earlier retention intervention where risk concentrates.
**Out of Scope:** Compensation-benchmark design (separate reward study); individual performance management (out of scope, aggregate only).

---

## 2. Core Business Questions

- Where is attrition above target by team, role and segment?
- Is engagement the driver, or is it cost/absence/workload?
- Which teams should retention actions target first?

---

### 3. KPI & Action Code Overview

| KPI ID | Role |
|--------|------|
| KPI-PPL-001 | Strategic |
| KPI-PPL-002 | Influencing |
| KPI-PPL-003 | Influencing |
| KPI-PPL-004 | Influencing |
| KPI-PPL-005 | Influencing |
| KPI-PPL-006 | Supporting |
| KPI-SVC-003 | Supporting |

**Action Codes:** X-R1.1

> Full machine-readable configuration in `UseCase_Bracket.yaml` (SSOT).

---

### 3.1 Standards basis

The headline KPIs reference these external standards — *reference, don't redefine* (full alignment & drift audit under `core/kpi_catalog/standards/`):

- **Attrition %** (`KPI-PPL-001`) → **ISO 30414** (exact): ISO 30414:2018 defines turnover/attrition rate; this is the realised voluntary-turnover base metric.
- **Engagement Index** (`KPI-PPL-002`) → **ISO 30414** (partial): ISO 30414 reports engagement under organizational culture; the index here is a survey-mean variant.
- **Time to Fill** (`KPI-PPL-003`) → **ISO 30414** (exact): ISO 30414 defines time-to-fill within recruitment metrics; definition matches.
- **Absence Rate %** (`KPI-PPL-004`) → **ISO 30414** (exact): ISO 30414 defines absenteeism rate; definition matches.
- **Workforce Cost per FTE** (`KPI-PPL-005`) → **ISO 30414** (partial): ISO 30414 reports total workforce cost; per-FTE normalisation is a managerial variant of the ISO cost base.
- **Headcount FTE** (`KPI-PPL-006`) → **ISO 30414** (exact): ISO 30414 defines FTE headcount within workforce availability; definition matches.
- **Attrition Risk %** (`KPI-SVC-003`) → **ISO 30414** (partial): ISO 30414:2018 (human capital reporting) defines turnover and retention-rate metrics. Attrition RISK here is a predicted probability — a modelling variant of the ISO turnover family; align the realised-turnover base to ISO 30414 and treat the risk score as a forward-looking overlay.

---

## 6. Data Requirements Summary

This use case is **new**: its KPIs are governed and standards-grounded, but the backing
Aurora synthetic data does not yet exist. The precise required tables/columns are recorded
per KPI (`technical.calculation.reason`) and consolidated in
`internal/project_mgmt/AURORA_SYNTHETIC_DATA_GAPS.md`. Until that data lands, the KPIs
report `UNCOMPUTED` (ADR-0009), never a fabricated value.

---

## 8. Success Criteria

- Benchmark: voluntary attrition < 10% p.a. (knowledge work); engagement index ≥ +30 eNPS; time-to-fill < 45 days.
- Impact: attrition returned to target in hotspot segments; absence and time-to-fill stabilised.
- Decision frequency: monthly people review.
