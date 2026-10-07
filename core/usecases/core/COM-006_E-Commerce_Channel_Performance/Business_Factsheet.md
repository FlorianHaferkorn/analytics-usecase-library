---
id: COM-006
factsheet_type: business
---

# COM-006 - E-Commerce Channel Performance

## Business Factsheet

---

## 0. Metadata (Mandatory)

- **Use Case ID:** COM-006
- **Domain:** Commercial
- **Business Owner:** Head of E-Commerce / Head of Sales
- **KPI Owner:** Commercial Controlling
- **Reporting Level:** Strategic / Tactical
- **Analytics Stage:** Descriptive / Diagnostic
- **Related Data Contract:** core/data_contracts/domains/commercial_sales.yaml

---

## 1. Business Summary

**Purpose:** Show whether the e-commerce channel gains share of total revenue, whether session conversion explains a stalling share, and which regions hold it back.
**Business Value:** One governed view of the digital share of the business, read next to the total net sales it is a share of.
**Out of Scope:** Total sales steering vs plan and prior year (COM-001); basket breadth and category cross-sell in stores (COM-IND-R001); marketing attribution and traffic acquisition.

---

## 2. Core Business Questions

- Is the e-commerce share of revenue growing as planned?
- Is session conversion the reason the share stalls?
- Which regions and categories hold the e-commerce share back the most?

---

### 3. KPI & Action Code Overview

| KPI ID | Role |
|--------|------|
| KPI-COM-032 | Strategic |
| KPI-COM-034 | Influencing |
| KPI-COM-005 | Supporting |

**Action Codes:** none yet — no action code in the framework covers e-commerce conversion or channel-shift levers.

> Full machine-readable configuration in `UseCase_Bracket.yaml` (SSOT).

---

### 3.1 Standards basis

The headline KPIs reference these external standards — *reference, don't redefine* (full alignment & drift audit under `core/kpi_catalog/standards/`):

- **E-Commerce Revenue Share** (`KPI-COM-032`) → **Retail analytics (convention)** (none): Channel share of revenue is a retail-analytics convention; which channels count as e-commerce (own web shop, marketplace) is set by the channel model, not by an external standard.
- **E-Commerce Conversion Rate** (`KPI-COM-034`) → **Web analytics (convention)** (none): Session-based conversion is a web-analytics convention; session definition and bot filtering differ between analytics tools, so the value is tool-dependent.
- **Net Sales Amount** (`KPI-COM-005`) → **IFRS 15** (partial): Net sales is a presentation of IFRS 15 revenue, net of VAT and returns.

---

## 5. 3-30-300 Page Layout (Mandatory)

### 5.1 3-Second Layer (KPI Cards)

- E-Commerce Revenue Share (KPI-COM-032) as KPI card with the delta to the prior year.

### 5.2 30-Second Layer (Main Visuals)

- E-commerce share over time as a line chart.
- Session conversion (KPI-COM-034) over time as a line chart.
- E-commerce share by region as a bar chart.

### 5.4 300-Second Layer (Diagnostics)

- Exception table by region and product category with the e-commerce share and net sales, lowest share first, Top 20.

---

## 6. Data Requirements Summary

This use case is **new**: its KPIs are governed and standards-grounded, but two of them
cannot be computed yet. KPI-COM-032 waits on the open decision which channel values count
as e-commerce; KPI-COM-034 needs a web-analytics session fact that no ALUCA data contract
carries. The exact blockers are recorded per KPI (`technical.calculation.reason`). Until
they are resolved the KPIs report `UNCOMPUTED` (ADR-0009), never a fabricated value.

---

## 8. Success Criteria

- Benchmark: none governed; the catalog notes that peer conversion values differ strongly by product category, so a single benchmark would mislead.
- Impact: the e-commerce share and session conversion are reported monthly from governed sources.
- Adoption: used in the monthly channel review by commercial controlling and the e-commerce lead.
- Decision frequency: monthly channel review.

---

## 9. Risks & Wrong Interpretations (Short)

- A share is not growth: the e-commerce share rises when store sales fall, even with flat online sales. Read it next to net sales (KPI-COM-005).
- Channel attribution decides the value: click-and-collect, marketplace and returns booked in another channel shift the share without any change in buying behaviour.
- Conversion is tool-dependent: a changed session definition or bot filter moves KPI-COM-034 without a change in the shop.

---

## 10. Typical Decision Scenarios

### Scenario 1: Share stalls while conversion holds

**Situation:** the e-commerce share is flat against the prior year while session conversion is stable.

**Decision question:** is the gap traffic or order value rather than the shop? Neither has a catalog KPI yet, so the use case flags the question and does not answer it.

**Who decides:** commercial controlling with the e-commerce lead.

### Scenario 2: Conversion falls ahead of the share

**Situation:** session conversion falls for several weeks while the share has not moved yet.

**Decision question:** which change in shop, checkout or assortment explains the drop, before it reaches revenue?

**Who decides:** e-commerce lead; commercial controlling tracks the effect on the share.
