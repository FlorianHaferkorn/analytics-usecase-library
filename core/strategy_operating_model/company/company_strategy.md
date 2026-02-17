# Company Strategy (Canonical Placeholder)

## Purpose

Define the company-level strategic direction that anchors the Golden Thread:

Strategy -> KPIs -> Use Cases -> Semantic Models -> Reports -> Actions

## How to use this document

- Keep this file concise and executive-level.
- Link strategic priorities to KPI topics (not technical implementation details).
- Do not define DAX, semantic model specifics, or report layouts here.

## Strategic priorities (example structure)

1. Profitable growth
2. Cash and liquidity resilience
3. Operational reliability
4. Customer value and service quality
5. Governance and accountability

## KPI alignment

For each priority, reference governed KPI IDs in:

- `core/kpi_catalog/KPI_Catalog.md`

## Ownership

- Strategy owner: executive sponsor
- KPI governance owner: finance/performance office
- Analytics enablement owner: data/analytics leadership

## Review cadence

- Quarterly strategy review
- Monthly KPI target and exception review
- Continuous refinement through use case outcomes

## 5. Strategic KPIs

Strategic KPIs express what success means and must be actively steered. Definitions and IDs are governed in:

- `core/kpi_catalog/KPI_Catalog.md`

The operational mapping of Strategic KPIs to use cases is in `core/usecases/UseCase_Inventory.md` (Strategic KPI column). Do not duplicate KPI definitions here.

## 6. Executive key questions

Key questions structure the transition from strategic steering signals to decision logic. They are operationalized in Use Case Business Factsheets (e.g. "Core Business Questions" per use case).

Examples (to be refined per organization):

- Why is performance deviating from plan in the most material areas?
- Where should we act first to protect margin and cash?

## 7. Strategic alignment inputs to the Golden Thread

The alignment map (Strategy → KPIs → Use Cases → Action Codes) is maintained in:

- `core/usecases/UseCase_Inventory.md` — operational master list (status, domain, owners, Strategic KPI, Influencing KPIs, Action Codes)
- Golden Thread narrative: `core/strategy_operating_model/operating_model/golden_thread_strategy_to_action.md`

Use the Inventory as the single reference for which use cases support which strategic KPIs.
