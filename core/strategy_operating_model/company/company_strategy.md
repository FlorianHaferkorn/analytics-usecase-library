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

<a id="5-strategic-kpis"></a>
## 5. Strategic KPIs

Strategic KPIs express what success means and must be actively steered. Definitions and IDs are governed in:

- `core/kpi_catalog/KPI_Catalog.md`

The operational mapping of Strategic KPIs to use cases is in `core/usecases/UseCase_Inventory.md` (Strategic KPI column). Do not duplicate KPI definitions here.

<a id="6-executive-key-questions"></a>
## 6. Executive key questions

Key questions structure the transition from strategic steering signals to decision logic. They are operationalized in Use Case Business Factsheets (e.g. "Core Business Questions" per use case).

Examples (to be refined per organization):

- Why is performance deviating from plan in the most material areas?
- Where should we act first to protect margin and cash?

<a id="7-strategic-alignment-inputs-to-the-golden-thread"></a>
## 7. Strategic alignment inputs to the Golden Thread

The alignment map (Strategy → KPIs → Use Cases → Action Codes) is maintained in:

- `core/usecases/UseCase_Inventory.md` — operational master list (status, domain, owners, Strategic KPI, Influencing KPIs, Action Codes)
- Golden Thread narrative: `core/strategy_operating_model/operating_model/golden_thread_strategy_to_action.md`

Use the Inventory as the single reference for which use cases support which strategic KPIs.

---

## Sources & Grounding

This document is a canonical placeholder: its company-specific content is illustrative, but the
*method* it prescribes — anchoring a few strategic priorities, expressing them as a small set of
Strategic KPIs that must be actively steered, deriving executive key questions, and reviewing
them on a fixed cadence — follows established strategy and performance-management frameworks:

- **Balanced Scorecard** (translating strategic priorities into a balanced, governed set of
  measures and targets, reviewed regularly — the basis for the "Strategic priorities → KPI
  alignment → review cadence" structure) — Kaplan & Norton, *The Balanced Scorecard—Measures
  That Drive Performance*, Harvard Business Review (1992):
  <https://hbr.org/2005/07/the-balanced-scorecard-measures-that-drive-performance> · Harvard
  Business School Faculty & Research: <https://www.hbs.edu/faculty/Pages/item.aspx?num=9161>
- **Strategy Maps / strategy-to-execution** (linking priorities to measurable objectives and to
  operations so strategy is steerable, not just stated) — Kaplan & Norton, *Having Trouble with
  Your Strategy? Then Map It*, Harvard Business Review (2000):
  <https://hbr.org/2000/09/having-trouble-with-your-strategy-then-map-it> · *The Execution
  Premium: Linking Strategy to Operations for Competitive Advantage*, Harvard Business School
  Press (2008): <https://www.hbs.edu/faculty/Pages/item.aspx?num=31707>
- **Treacy & Wiersema value disciplines** (choosing a strategic focus — e.g. profitable growth
  vs. operational reliability vs. customer value — and aligning the operating model to it; the
  basis for the "Strategic priorities" list) — Michael Treacy & Fred Wiersema, *Customer
  Intimacy and Other Value Disciplines*, Harvard Business Review (1993):
  <https://hbr.org/1993/01/customer-intimacy-and-other-value-disciplines>
- **Objectives and Key Results (OKRs)** (cascading a small set of objectives into measurable
  results with a regular review rhythm — parallels the monthly KPI target/exception review and
  quarterly strategy review) — Andy Grove (origin at Intel) and John Doerr, *Measure What
  Matters*; What Matters OKR origin story:
  <https://www.whatmatters.com/articles/the-origin-story> · OKR definition:
  <https://www.whatmatters.com/faqs/okr-meaning-definition-example>

> The strategic priorities, key questions, ownership roles, and review cadence in this file are
> placeholder examples for an adopting organization to replace; only the goal-setting and
> performance-management methodology they follow is grounded above.

