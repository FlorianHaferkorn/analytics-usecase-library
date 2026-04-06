---
id: SCM-IND-L001
factsheet_type: business
required_kpi_ids:
  - shipments.count
  - supply.on_time.pct
  - supply.otif.pct
---
# SCM-IND-L001 — Last-Mile Delivery Performance

## Business Factsheet

---

## 0. Metadata (Mandatory)

- **Use Case ID:** SCM-IND-L001
- **Domain:** Supply Chain

---

**Status:** Draft scaffold — not yet build-ready
**Vertical:** Logistics & 3PL
**Domain:** Supply Chain
**Prerequisites:** SCM-002 (Supply Reliability / OTIF), OPS-001 (Operations Performance)

---

## Business Problem

3PL operators and logistics-intensive businesses lack a unified view of last-mile delivery performance across carriers and regions. On-Time Delivery (OTD) failures are typically discovered through customer complaints rather than proactive monitoring — by which point SLA penalties have accrued and customer satisfaction has degraded. Without carrier-level benchmarking, commercial negotiations lack data leverage.

## Strategic KPI

**On-Time Delivery % (OTD)** — the percentage of deliveries completed within the committed delivery window (typically same-day, next-day, or contracted SLA window).

## Value Driver Logic

- **First-attempt success rate** is the primary driver: redelivery attempts almost always result in missed OTD windows and add direct cost
- **Average delivery days** reflects route and network efficiency
- **Returns rate** signals both delivery failure (damage, wrong address) and fulfilment quality upstream
- **Cost per delivery** reflects route utilisation and carrier mix efficiency

## Key Actions

| Action Code | Description |
|---|---|
| S-L1.1 | Carrier escalation — formal SLA breach notification and remedy plan |
| S-L1.2 | Route optimisation — rebalance routes to reduce delivery days and improve utilisation |

## Scope & Limits

- Requires delivery event data (grain: `delivery_event`) with carrier, timestamp, and outcome (success/failed/returned)
- Delivery window definition varies by carrier contract — must be normalised in ETL
- Geographic breakdown requires postcode/region mapping
- Not applicable to B2B freight (pallet/full-truck-load) — those follow SCM-002 OTIF patterns
