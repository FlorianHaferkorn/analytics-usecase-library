---
id: SCM-004
factsheet_type: business
---

# SCM-004 - Procurement & Supplier Performance

## Business Factsheet

---

## 0. Metadata (Mandatory)

- **Use Case ID:** SCM-004
- **Domain:** Supply Chain
- **Business Owner:** Chief Procurement Officer / Head of Sourcing
- **KPI Owner:** Procurement Controlling / Sourcing
- **Reporting Level:** Tactical
- **Analytics Stage:** Diagnostic / Prescriptive
- **Related Data Contract:** core/data_contracts/domains/supply_chain.yaml

---

## 1. Business Summary

**Purpose:** Realise procurement savings by raising on-contract spend, controlling purchase-price variance, and improving supplier reliability.
**Business Value:** Protected savings, lower maverick buying, and earlier action on supplier price and delivery risk.
**Out of Scope:** Customer-facing OTIF (SCM-002); inventory optimisation (SCM-001); statutory spend reporting (out of scope).

---

## 2. Core Business Questions

- Are savings realised against target by category?
- Is the leak off-contract buying, price variance, or supplier reliability?
- Which Tier-1 suppliers lack a passed ESG audit (KPI-ESG-002), read next to supplier risk?
- Which categories and suppliers should recovery target first?

---

### 3. KPI & Action Code Overview

| KPI ID | Role |
|--------|------|
| KPI-SCM-023 | Strategic |
| KPI-SCM-024 | Influencing |
| KPI-SCM-025 | Influencing |
| KPI-SCM-026 | Influencing |
| KPI-SCM-027 | Supporting |
| KPI-SCM-022 | Supporting |
| KPI-ESG-002 | Supporting |

**Action Codes:** S-P1.1

> Full machine-readable configuration in `UseCase_Bracket.yaml` (SSOT).

---

### 3.1 Standards basis

The headline KPIs reference these external standards — *reference, don't redefine* (full alignment & drift audit under `core/kpi_catalog/standards/`):

- **Realised Savings %** (`KPI-SCM-023`) → **Procurement & spend analytics (convention)** (none): Savings realisation is a procurement-controlling convention; no external standards body defines the metric.
- **On-Contract Spend %** (`KPI-SCM-024`) → **Procurement & spend analytics (convention)** (none): Contract-compliance / maverick-buying share is a procurement convention, not an external standard.
- **Purchase Price Variance %** (`KPI-SCM-025`) → **Procurement & spend analytics (convention)** (none): PPV is a standard cost-accounting/procurement convention; align the baseline definition to the internal standard-cost policy.
- **Supplier On-Time Delivery %** (`KPI-SCM-026`) → **SCOR-DS** (partial): SCOR governs supplier delivery reliability under Source (sS); grain here is receipt-level inbound OTD, a partial mapping to SCOR's supplier reliability metrics.
- **Managed Spend** (`KPI-SCM-027`) → **Procurement & spend analytics (convention)** (none): Addressable-spend scoping is a procurement convention, not an external standard.
- **Supplier Risk Score** (`KPI-SCM-022`) → **SCOR-DS** (partial): Loose link only: SCOR Agility (AG) measures adaptability and overall value-at-risk, not a supplier-risk composite score. Conceptual neighbour, not the same metric.

---

## 6. Data Requirements Summary

This use case is **new**: its KPIs are governed and standards-grounded, but the backing
Aurora synthetic data does not yet exist. The precise required tables/columns are recorded
per KPI (`technical.calculation.reason`) and consolidated in
`internal/project_mgmt/AURORA_SYNTHETIC_DATA_GAPS.md`. Until that data lands, the KPIs
report `UNCOMPUTED` (ADR-0009), never a fabricated value.

---

## 8. Success Criteria

- Benchmark: realised savings ≥ target; on-contract spend ≥ 85%; PPV within tolerance.
- Impact: savings recovered in leaking categories; on-contract share and PPV improved.
- Decision frequency: monthly procurement review.
