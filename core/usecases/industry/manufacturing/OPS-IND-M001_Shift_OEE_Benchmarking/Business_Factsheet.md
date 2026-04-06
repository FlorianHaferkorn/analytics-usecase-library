---
id: OPS-IND-M001
factsheet_type: business
required_kpi_ids:
  - ops.oee.pct
  - ops.availability.pct
  - ops.performance.pct
  - ops.quality.pct
  - ops.throughput.units
---
# OPS-IND-M001 — Shift OEE Benchmarking across Plants

## Business Factsheet

---

## 0. Metadata (Mandatory)

- **Use Case ID:** OPS-IND-M001
- **Domain:** Operations

---

**Status:** Draft scaffold — not yet build-ready
**Vertical:** Manufacturing
**Domain:** Operations
**Prerequisites:** OPS-001 (Operations Performance), OPS-002 (Asset Performance)

---

## Business Problem

Manufacturing plants running multiple shifts and production lines lack a consistent, comparable measure of equipment productivity. Without a standardised OEE benchmark, plant managers cannot identify whether performance losses are driven by availability (downtime), speed (performance), or yield (quality) — and cannot benchmark across plants, lines, or shifts to drive improvement.

## Strategic KPI

**OEE % (Overall Equipment Effectiveness)** — the ratio of fully productive time to planned production time, decomposed into Availability × Performance × Quality.

## Value Driver Logic

OEE is multiplicative: degradation in any one component drops the composite score.

- **Availability** — unplanned stoppages are typically the largest loss category; preventive maintenance is the primary lever
- **Performance** — cycle time deviations caused by micro-stoppages or speed losses; line rebalancing is the primary lever
- **Quality** — defect and rework rate; upstream material quality and process parameter stability are the levers

Benchmarking across plants and shifts surfaces the best-performing shift teams as internal benchmarks for coaching.

## Key Actions

| Action Code | Description |
|---|---|
| O-P1.1 | Preventive maintenance trigger — schedule PM when availability trend declines |
| O-P1.2 | Line rebalancing — adjust cycle time targets when performance loss identified |

## Scope & Limits

- Requires production order line data (grain: `production_order_line`) with actual start/end timestamps
- Shift definition (e.g. 3-shift rotating) must be mapped in the semantic model
- OEE benchmarking is most meaningful when plants produce comparable product families
- Not applicable to process industries with continuous flow (→ adapt for batch OEE variant)
