# KPI Taxonomy (Reference View)

## Purpose

This document provides a **readable, domain-oriented view** of the KPI Catalog. It supports discovery, onboarding, and AI grounding. Authoritative definitions remain in `KPI_Catalog.md` and the catalog schema; this taxonomy is a summary only.

**Structure:** Domain → Topic (prefix) → KPI id and short purpose. **Used in** refers to core use case IDs.

---

## Commercial (COM)

| KPI ID | Short purpose | Used in |
|--------|----------------|---------|
| KPI-COM-005 | Net revenue; core revenue control | COM-001, XD-003 |
| KPI-COM-009 | Net Sales % vs Plan | COM-001 |
| KPI-COM-008 | Net Sales % vs Last Year | COM-001, XD-003 |
| KPI-COM-010 | Price effect on sales gap | COM-001 |
| KPI-COM-011 | Volume effect on sales gap | COM-001 |
| KPI-COM-004 | Mix effect on sales gap | COM-001, COM-002 |
| KPI-COM-013 | Gross margin % | COM-001, COM-002, XD-003 |
| KPI-COM-019 | Gross margin amount | COM-002 |
| KPI-FIN-017 | Gross margin % vs Plan | COM-002 |
| KPI-COM-003 | Realized price vs list; discount leakage | COM-002, COM-004 |
| KPI-COM-016 | Promotion return on investment | COM-004 |
| KPI-COM-021 | Incremental sales from promo | COM-004 |
| KPI-FIN-012 | Gross margin % on promo | COM-004 |
| KPI-COM-018 | Cannibalization from promo | COM-004 |

---

## Customer & CRM (COM-003, XD-003)

| KPI ID | Short purpose | Used in |
|--------|----------------|---------|
| KPI-CUS-001 | Customer lifetime value | COM-003, XD-003 |
| KPI-CUS-005 | Lifetime revenue per customer | COM-003 |
| KPI-CUS-002 | Customer retention rate | COM-003 |
| KPI-CUS-004 | Churned customers | COM-003 |
| KPI-OPS-001 | Revenue at risk from churn | COM-003 |
| KPI-CUS-006 | Active customer count | COM-003 |
| KPI-CUS-003 | Net Promoter Score | COM-003, XD-001 |
| KPI-SVC-001 | Complaint count | COM-003 |

---

## Retail — Basket & Cross-Sell (COM-IND-R001)

Industry-tier namespaces (`retail.*`, `customer.rfm.*`) introduced with the ADR-0004 use-case tier. Sector tag: `Retail`.

| KPI ID | Short purpose | Used in |
|--------|----------------|---------|
| KPI-COM-022 | Share of transactions spanning ≥2 categories (strategic) | COM-IND-R001 |
| KPI-COM-023 | Average distinct items per transaction | COM-IND-R001 |
| KPI-COM-024 | Average net basket value (basket-economics guardrail) | COM-IND-R001 |
| KPI-COM-025 | Margin-accretive attachment on promoted baskets | COM-IND-R001 |
| KPI-CUS-007 | RFM purchase-frequency score (segment average) | COM-IND-R001 |

---

## Finance (FIN)

| KPI ID | Short purpose | Used in |
|--------|----------------|---------|
| KPI-FIN-007 | Cash balance | FIN-001 |
| KPI-FIN-009 | Operating cash flow | FIN-001 |
| KPI-FIN-010 | Cash vs plan | FIN-001 |
| KPI-FIN-006 | Cash conversion cycle (days) | FIN-001, XD-003 |
| KPI-FIN-001 | Days sales outstanding | FIN-001 |
| KPI-FIN-004 | Days inventory outstanding | FIN-001 |
| KPI-FIN-005 | Days payables outstanding | FIN-001 |
| KPI-FIN-015 | Unit cost | FIN-002 |
| KPI-FIN-016 | COGS % of revenue | FIN-002 |
| KPI-FIN-014 | OpEx vs plan | FIN-002 |
| KPI-SCM-020 | Material cost share | FIN-002 |
| KPI-FIN-013 | COGS per unit | COM-002, FIN-002 |
| KPI-OPS-004 | Labor productivity | FIN-002 |

---

## Operations (OPS)

| KPI ID | Short purpose | Used in |
|--------|----------------|---------|
| KPI-OPS-011 | Overall equipment effectiveness | OPS-001 |
| KPI-OPS-016 | Availability % | OPS-001, OPS-002 |
| KPI-OPS-002 | Performance % | OPS-001 |
| KPI-OPS-003 | Quality % | OPS-001 |
| KPI-OPS-009 | Throughput (units) | OPS-001 |
| KPI-OPS-017 | Downtime % | OPS-001 |
| KPI-OPS-005 | Mean time between failures | OPS-002 |
| KPI-OPS-006 | Mean time to repair | OPS-002 |
| KPI-OPS-018 | Unplanned downtime % | OPS-002 |
| KPI-OPS-008 | Spare parts stockout % | OPS-002 |
| KPI-OPS-007 | Preventive maintenance compliance | OPS-002 |
| KPI-QUA-001 | First pass yield % | OPS-003 |
| KPI-QUA-002 | Scrap % | OPS-003 |
| KPI-OPS-010 | Rework % | OPS-003 |
| KPI-QUA-003 | Cost of poor quality | OPS-003 |
| KPI-QUA-004 | Complaint rate | OPS-003 |
| KPI-QUA-005 | Defect density | OPS-003 |

---

## Supply Chain (SCM)

| KPI ID | Short purpose | Used in |
|--------|----------------|---------|
| KPI-SCM-001 | Days inventory outstanding | SCM-001, FIN-001 |
| KPI-SCM-016 | Inventory turnover | SCM-001 |
| KPI-SCM-002 | Stockout % | SCM-001 |
| KPI-SCM-004 | Obsolete inventory % | SCM-001 |
| KPI-SCM-007 | On-time in-full % | SCM-001, SCM-002, XD-003 |
| KPI-SCM-005 | Forecast accuracy | SCM-001, SCM-003 |
| KPI-SCM-008 | On-time % | SCM-002 |
| KPI-SCM-018 | In-full % | SCM-002 |
| KPI-SCM-009 | Stockout impact % | SCM-002 |
| KPI-SCM-011 | Penalty amount | SCM-002 |
| KPI-SCM-010 | Expedite cost | SCM-002 |
| KPI-SCM-017 | Forecast MAPE | SCM-003 |
| KPI-SCM-006 | Forecast bias | SCM-003 |
| KPI-SCM-012 | Forecast impact on service | SCM-003 |

---

## Experience & Service (XD)

| KPI ID | Short purpose | Used in |
|--------|----------------|---------|
| KPI-SVC-004 | SLA attainment % | XD-001, XD-002, XD-003 |
| KPI-SVC-005 | First contact resolution % | XD-001 |
| KPI-SVC-006 | Average handling time (min) | XD-001 |
| KPI-SVC-007 | Backlog count | XD-001, XD-002 |
| KPI-SVC-008 | Escalation % | XD-001 |
| KPI-SVC-009 | Resource utilization % | XD-002 |
| KPI-SVC-010 | Occupancy % | XD-002 |
| KPI-SVC-011 | Overtime % | XD-002 |
| KPI-SVC-012 | Shrinkage % | XD-002 |

---

## Enterprise / People (XD-003)

| KPI ID | Short purpose | Used in |
|--------|----------------|---------|
| KPI-SVC-002 | Digital adoption % | XD-003 |
| KPI-SVC-003 | Attrition risk % | XD-003 |
| ops.otif.pct | OTIF (executive view) | XD-003 |

---

## Naming Convention

- **Format:** `KPI-<KÜRZEL>-<NNN>` (D-594; Kürzel COM, FIN, OPS, SCM, SVC, CUS, GOV, PPL, QUA, ESG — Bedeutung im Katalogfeld, nicht in der ID) (e.g. `KPI-COM-005`, `KPI-SCM-001`).
- **Kürzel (business ownership):** see `tooling/validation/_index.yaml` `kpi_domains`; the ID carries no meaning — name, unit and formula live in the catalog entry.
- **Source of truth:** `core/kpi_catalog/KPI_Catalog.md` and schema. This taxonomy is derived and may lag; always validate against the catalog.

### Cross-domain (dual-lens) measures — intentional, not duplicates

Some business concepts are deliberately surfaced as a measure in **more than one domain's
semantic model** because each domain semantic model (`core/semantic_models/domains/<Domain>/`)
owns its own measure and a cross-domain scorecard needs a local copy. These are **intentional**
and must **not** be deleted as "duplicate KPIs" — each id has its own generated measure, dictionary
entry, and downstream references (action codes, ontology registry, brackets, tests).

| Concept | Primary owner (canonical) | Cross-domain copy | Why the copy exists |
|---------|---------------------------|-------------------|---------------------|
| On-Time-In-Full | `KPI-SCM-007` (Supply Chain) | `ops.otif.pct` (Operations) | operations-lens service reference |

**Rule:** when a metric is needed in another domain's view, reference the **canonical** id where
possible; only add an explicit, documented domain-scoped copy (as above) when the per-domain
semantic model genuinely requires its own measure.

### Prefix outliers

None since D-594 (30.09.2026): the dotted prefixes (`scm.*` vs `supply.*`, `shipments.*`, `plans.*`) were retired with the numbered IDs.

