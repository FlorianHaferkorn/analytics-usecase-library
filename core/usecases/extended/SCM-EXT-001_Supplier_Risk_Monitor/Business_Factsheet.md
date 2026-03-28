# SCM-EXT-001 — Supplier Risk & Dual-Sourcing Monitor

**Status:** Draft scaffold — not yet build-ready
**Domain:** Supply Chain
**Prerequisites:** SCM-002 (Supply Reliability / OTIF)

---

## Business Problem

Procurement and supply chain teams lack a consolidated view of which suppliers pose the greatest risk to supply continuity. Concentration in single-source suppliers, combined with degrading delivery or quality performance, creates hidden exposure that only surfaces when a disruption occurs. By that point, recovery costs (expediting, line stoppages, customer penalties) far exceed the cost of proactive risk mitigation.

## Strategic KPI

**Composite Supplier Risk Score (0–100)** — a weighted index combining OTIF performance, quality defect rate, delivery lead-time deviation, financial health, and single-source concentration. Higher score = higher risk.

## Value Driver Logic

Risk accumulates when:
- **OTIF drops** below contracted SLA (primary signal — historical performance indicator)
- **Concentration rises** above threshold (structural risk — single-source dependency)
- **Lead-time deviation increases** (operational signal — stress indicator)
- **Defect rate rises** (quality signal — downstream production impact)

Risk score ≥ 70 triggers a procurement escalation action. Score ≥ 85 triggers dual-source activation review.

## Key Actions

| Action Code | Description |
|---|---|
| S-P1.1 | Procurement escalation — formal supplier performance review |
| S-P1.2 | Dual-source activation — qualify and onboard alternative supplier |

## Scope & Limits

- Requires purchase order line data (grain: `purchase_order_line`) with GR/GI timestamps
- Financial health score sourced from external data provider (not in standard data contract)
- Composite score weights are configurable per organisation; defaults: OTIF 35%, concentration 30%, quality 20%, lead-time 15%
- Not a real-time monitor — refreshed on daily batch cycle
