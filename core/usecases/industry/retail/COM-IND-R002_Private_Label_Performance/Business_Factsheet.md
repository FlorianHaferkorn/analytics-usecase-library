---
id: COM-IND-R002
factsheet_type: business
---

# COM-IND-R002 - Private Label Performance

## Business Factsheet

---

## 0. Metadata (Mandatory)

- **Use Case ID:** COM-IND-R002
- **Domain:** Commercial / Retail
- **Business Owner:** Head of Category Management
- **KPI Owner:** Category Management / Commercial Controlling
- **Reporting Level:** Strategic / Tactical
- **Analytics Stage:** Descriptive / Diagnostic
- **Related Data Contract:** core/data_contracts/domains/commercial_sales.yaml

---

## 1. Business Summary

**Purpose:** Show whether the private-label (own-brand) share of revenue grows, and in which categories and regions the own-brand programme lands.
**Business Value:** One governed own-brand share per category that category management and commercial controlling both read.
**Out of Scope:** Gross-margin steering (COM-002); own-brand sourcing and supplier terms (SCM-004); basket and cross-sell activation (COM-IND-R001).

---

## 2. Core Business Questions

- Is the private-label share of revenue growing in the categories we steer?
- Which categories carry the private-label share, and which lag?
- Which categories and regions should own-brand assortment and pricing work target first?

---

### 3. KPI & Action Code Overview

| KPI ID | Role |
|--------|------|
| KPI-COM-033 | Strategic |
| KPI-COM-005 | Supporting |

**Action Codes:** none yet — no action code in the framework covers own-brand assortment or pricing decisions.

> Full machine-readable configuration in `UseCase_Bracket.yaml` (SSOT).

---

### 3.1 Standards basis

The headline KPIs reference these external standards — *reference, don't redefine* (full alignment & drift audit under `core/kpi_catalog/standards/`):

- **Private Label Penetration %** (`KPI-COM-033`) → **Retail analytics (convention)** (none): Private-label share is a retail-analytics convention; some sources measure it by units instead of revenue — this KPI is revenue-based.
- **Net Sales Amount** (`KPI-COM-005`) → **IFRS 15** (partial): Net sales is a presentation of IFRS 15 revenue, net of VAT and returns.

---

## 5. 3-30-300 Page Layout (Mandatory)

### 5.1 3-Second Layer (KPI Cards)

- Private Label Penetration % (KPI-COM-033) as KPI card with the delta to the prior year.

### 5.2 30-Second Layer (Main Visuals)

- Private-label share over time as a line chart.
- Private-label share by product category as a bar chart.

### 5.4 300-Second Layer (Diagnostics)

- Exception table by category and region with the private-label share and net sales, lowest share first, Top 20.

---

## 6. Data Requirements Summary

This use case is **new**: its strategic KPI is governed and standards-grounded, but it
cannot be computed yet. The commercial_sales contract has no private-label attribute
(`dim_product` carries Brand only, no own-brand flag), so the numerator cannot be sourced
(`technical.calculation.reason`). Until `dim_product` gains that flag the KPI reports
`UNCOMPUTED` (ADR-0009), never a fabricated value.

---

## 8. Success Criteria

- Benchmark: none governed; own-brand targets are set per retailer and category and are not part of the catalog.
- Impact: the private-label share is reported per category and region from a governed own-brand flag.
- Adoption: used in the monthly category review by category management.
- Decision frequency: monthly category review.

---

## 9. Risks & Wrong Interpretations (Short)

- Revenue share, not unit share: cheaper own brands can gain units while the revenue share stays flat. The catalog defines this KPI on revenue.
- The share depends on the own-brand flag of every SKU; unflagged SKUs understate it.
- A higher share is not a margin result by itself; the margin effect is steered in COM-002.

---

## 10. Typical Decision Scenarios

### Scenario 1: Share grows in one category only

**Situation:** the private-label share rises in one category and stays flat in the others.

**Decision question:** is the growth an assortment decision that can be carried to the other categories, or a one-off listing?

**Who decides:** category manager.

### Scenario 2: Share falls after a brand promotion

**Situation:** the private-label share drops in a category during a brand promotion.

**Decision question:** is the drop temporary (promotion period only) or does it persist after the promotion ends?

**Who decides:** category manager with trade marketing.
