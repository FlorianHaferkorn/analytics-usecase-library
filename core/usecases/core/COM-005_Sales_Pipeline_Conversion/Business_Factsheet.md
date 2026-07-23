---
id: COM-005
factsheet_type: business
---

# COM-005 - Sales Pipeline & Conversion

## Business Factsheet

---

## 0. Metadata (Mandatory)

- **Use Case ID:** COM-005
- **Domain:** Commercial
- **Business Owner:** Chief Revenue Officer / Head of Sales
- **KPI Owner:** Commercial Controlling / Revenue Operations
- **Reporting Level:** Tactical
- **Analytics Stage:** Diagnostic / Prescriptive
- **Related Data Contract:** core/data_contracts/domains/growth.yaml

---

## 1. Business Summary

**Purpose:** Secure forward revenue by keeping qualified pipeline coverage healthy and improving conversion through the funnel.
**Business Value:** Earlier warning on revenue risk, higher win rates, and a faster, more predictable sales cycle.
**Out of Scope:** Realised revenue and margin steering (COM-001/COM-002); promotion effectiveness (COM-004).

---

## 2. Core Business Questions

- Is pipeline coverage sufficient for the remaining target?
- Is the gap volume or conversion, and where does the funnel leak?
- Which reps and segments should the conversion push target first?

---

### 3. KPI & Action Code Overview

| KPI ID | Role |
|--------|------|
| sales.pipeline.coverage.ratio | Strategic |
| sales.win_rate.pct | Influencing |
| sales.conversion.pct | Influencing |
| sales.sales_cycle.days | Influencing |
| sales.velocity.amount | Influencing |
| sales.pipeline.value.amount | Supporting |

**Action Codes:** C-P1.1

> Full machine-readable configuration in `UseCase_Bracket.yaml` (SSOT).

---

### 3.1 Standards basis

The headline KPIs reference these external standards — *reference, don't redefine* (full alignment & drift audit under `core/kpi_catalog/standards/`):

- **Pipeline Coverage** (`sales.pipeline.coverage.ratio`) → **Sales pipeline management (convention)** (none): No ISO/IFRS standard governs pipeline coverage; this is an established commercial-steering convention (typical ≥3x rule), not an external standard.
- **Win Rate %** (`sales.win_rate.pct`) → **Sales pipeline management (convention)** (none): Win rate is a standard commercial-analytics convention; no external standards body defines it.
- **Stage Conversion %** (`sales.conversion.pct`) → **Sales pipeline management (convention)** (none): Funnel conversion is a commercial-analytics convention, not an external standard.
- **Sales Cycle Length** (`sales.sales_cycle.days`) → **Sales pipeline management (convention)** (none): Sales-cycle length is a commercial-analytics convention, not an external standard.
- **Sales Velocity** (`sales.velocity.amount`) → **Sales pipeline management (convention)** (none): Sales velocity is a widely-used commercial convention (opps x value x win-rate / cycle); no external standard defines it.
- **Open Pipeline Value** (`sales.pipeline.value.amount`) → **Sales pipeline management (convention)** (none): Open pipeline value is a commercial-analytics convention, not an external standard.

---

## 6. Data Requirements Summary

This use case is **new**: its KPIs are governed and standards-grounded, but the backing
Aurora synthetic data does not yet exist. The precise required tables/columns are recorded
per KPI (`technical.calculation.reason`) and consolidated in
`internal/project_mgmt/AURORA_SYNTHETIC_DATA_GAPS.md`. Until that data lands, the KPIs
report `UNCOMPUTED` (ADR-0009), never a fabricated value.

---

## 8. Success Criteria

- Benchmark: pipeline coverage ≥ 3x remaining target; win rate ≥ segment benchmark; cycle length not lengthening.
- Impact: coverage restored above threshold; win rate and cycle improved in target segments.
- Decision frequency: weekly pipeline review.
