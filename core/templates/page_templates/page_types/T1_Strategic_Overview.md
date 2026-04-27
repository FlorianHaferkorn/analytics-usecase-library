# T1 – Strategic Overview

> **Design basis:** Munzner (2014, *Visualization Analysis & Design*) nested model — domain task (executive strategy review) → data abstraction (KPI vs. target, trend, variance) → visual encoding (position-based kpi_card + line_chart). Shneiderman (1996): this page implements the *overview* tier of the overview-first mantra.

## Purpose

The Strategic Overview page provides **executive-level clarity** on whether the organization is **on track against its strategic objectives**.

It is designed for **top management, board members, and senior leaders** who need a fast, reliable answer to one question:

> **Are we strategically on track – and where do we need to intervene at a portfolio or resource level?**

This page is **not** used for root-cause analysis, operational control, or task execution.

---

## Primary Decision Question

**Are we meeting our strategic targets, and where is strategic intervention required?**

If this question cannot be answered within **30 seconds**, the page is not done.

---

## When to Use This Page Type

Use **T1 – Strategic Overview** when:

- the audience is executive or senior management
- decisions are **directional, not operational**
- the focus is on **outcomes**, not drivers or processes
- the goal is prioritization, alignment, or escalation

Typical usage rhythm:

- Monthly / quarterly management reviews
- Executive steering committees
- Board-level reporting

---

## When NOT to Use This Page Type

Do **not** use T1 if:

- detailed explanations are required → use **T2**
- operational thresholds must be monitored → use **T3**
- concrete actions must be recommended → use **T4**

T1 must never turn into a “compressed operational dashboard”.

---

## Analytical Scope (3–30–300 Rule)

### 3 Seconds – Strategic Status

- 4–6 core KPIs only
- Clear target context (on / off track)
- Immediate visual signal of strategic health

### 30 Seconds – Strategic Context

- High-level trend over time
- Strategic comparison (portfolio, region, domain)
- No drill-down logic required

### 300 Seconds – Explicitly Out of Scope

- No detailed tables
- No transactional data
- No deep diagnostic analysis

---

## Allowed Slots

| Slot | Purpose | Mandatory |
|-----|--------|-----------|
| KPI Summary | Strategic performance snapshot | Yes |
| Trend | Direction and momentum | Yes |
| Variance | Target or prior-period deviation | Optional |
| Ranking | Portfolio-level comparison | Optional |
| Mix | Structural composition | Optional |

---

## Disallowed Slots

The following slots are **not allowed** on T1 pages:

- Exception lists
- Root-cause analysis
- Detail matrices
- Prescriptive recommendation slots
- Funnels

If such content is required, the page type is wrong.

---

## Visual Governance (Summary)

- KPI Cards with target / delta
- Line charts for trends
- Horizontal bar charts for rankings
- 100% stacked bars for mix

Disallowed:

- Tables, matrices, scatter plots, funnels
- Dense visuals or exploratory controls

Visuals must support **orientation**, not exploration.

---

## Action Signals (Strategic Only)

T1 pages do **not** contain a full Action Panel.

They may contain **Strategic Action Signals** only:

- Maximum of 1–2 short callouts
- High-level, non-operational wording
- Examples:
  - “Review pricing strategy in Region X”
  - “Reassess capacity allocation for Product Group Y”

No ownership assignment, task tracking, or execution logic.

---

## User Experience Rules

- One screen, no scrolling where possible
- No more than 2–3 slicers (time, organization)
- Consistent layout across all strategic pages
- Clear hierarchy: headline → KPI → context

---

## Success Criteria (Definition of Done)

A T1 page is complete when:

- the strategic status is immediately visible
- executives can align or escalate without further explanation
- no operational questions are triggered
- the page remains stable over time

---

## Narrative Arc

### The Big Idea

One sentence that every T1 page must communicate to the reader:

> “[Domain] is [on/off] track — [primary KPI] is [Δ vs target], and [momentum direction].”

Example: *”Commercial performance is off track — Net Sales is -8% vs Plan YTD, with declining momentum over the last three months.”*

If this sentence cannot be constructed from the page content, the page is not ready.

### Story Structure

**Act 1 — Establish (3 seconds, KPI Band)**
The KPI band is the opening statement. It answers the Big Idea question immediately.
- The hero KPI (strategic outcome) anchors the top-left position.
- Green/red signal immediately frames the narrative: “We are winning” or “We have a problem.”
- The reader must not need to go to Act 2 to understand Act 1.

**Act 2 — Contextualize (30 seconds, Driver Zone)**
The driver visuals answer “How did we get here?” — not “Why”, which belongs to T2.
- `Main_1` (Trend): *”This is the trajectory — are we improving or deteriorating?”*
- `Main_2` (Variance or portfolio comparison): *”This is where we stand across the portfolio.”*
- T1 does NOT answer “What caused it?” — that escalates to T2.

**Act 3 — Strategic Signal (optional, bottom or callout)**
At most 1–2 brief strategic callouts: high-level flags for leadership attention.
- *”Region X requires strategic review”* — direction only, no operational detail.
- No action steps. No owner assignment. No data tables.

### Visual Title Narrative

The three visual titles on a T1 page should tell a strategic story together when read in sequence:

| Slot | Narrative Role | Example Title |
|---|---|---|
| `Main_1` (Trend) | “The journey” | “How has [primary KPI] developed over the last 12 months?” |
| `Main_2` (Portfolio/Variance) | “The portfolio position” | “Which strategic units are on and off track?” |
| `Main_3` (optional, Mix/Ranking) | “The composition” | “How is [KPI] distributed across the portfolio?” |

### What Makes This Page Fail the Narrative

| Failure | Cause | Fix |
|---|---|---|
| Big Idea not visible in 3 seconds | Hero KPI buried or no status signal | Move primary KPI to top-left; add semantic color |
| Page explains “why” | T2 content leaked in | Remove driver decomposition; keep trend only |
| Too many KPIs dilute the signal | More than 6 KPIs in Zone 1 | Reduce to 4 strategic KPIs; move others to T2 |
| Charts tell disconnected stories | No common thread between visuals | Align all visuals to one strategic dimension |

---

## Key Principle
>
> **T1 answers “Are we on track?” – nothing else.**

If the page tries to explain *why* or *what to do*, it is no longer strategic.

