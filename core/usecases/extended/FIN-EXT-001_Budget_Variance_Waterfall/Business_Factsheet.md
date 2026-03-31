# FIN-EXT-001 — Budget Variance Waterfall (P&L Bridge)

**Status:** Draft scaffold — not yet build-ready
**Domain:** Finance
**Prerequisites:** FIN-002 (Cost Performance)

---

## Business Problem

Finance teams need to explain *why* EBIT deviated from budget — not just *by how much*. Standard variance reports show the total gap but do not decompose it into controllable contributors (revenue shortfall vs. cost overrun vs. mix shift). Without a P&L bridge, leadership cannot direct corrective action to the right cost centre or revenue driver.

## Strategic KPI

**EBIT vs. Budget %** — the percentage deviation of Earnings Before Interest and Tax from the approved annual budget for the reporting period.

## Value Driver Logic

The P&L bridge decomposes the EBIT variance into three primary bridges:

1. **Revenue bridge** — price effect + volume effect + mix effect vs. budget
2. **COGS bridge** — input cost variance + volume-driven COGS vs. budget
3. **OpEx bridge** — fixed cost overrun + discretionary spend vs. budget

Each bridge is further drillable to cost centre and GL account level.

## Key Actions

| Action Code | Description |
|---|---|
| F-C1.2 | Cost containment — freeze discretionary spend in overspending cost centres |
| F-C1.1 | Budget reforecast — update rolling forecast with confirmed variance |

## Scope & Limits

- Requires GL-level data (grain: `gl_posting_line`) with budget actuals
- Waterfall visual requires Power BI waterfall chart visual type
- Period-end close latency applies (T+3 business days typical)
- FX impact shown as a separate bridge component when multi-currency

## Notes for Implementation

The waterfall chart in Power BI requires measures structured as running subtotals. Reference the measure dictionary for `finance.ebit.bridge.*` measure patterns.
