# T2 – Tactical Variance & Drivers

> **Design basis:** Munzner (2014) nested model — domain task (explain gap vs. target) → data abstraction (delta, driver decomposition) → visual encoding (waterfall for variance bridge). Few (2004, *Information Dashboard Design*): variance analysis requires showing both the overall gap and its component drivers simultaneously.

## Purpose

The Tactical Variance page explains **why performance deviates from targets or expectations**.

It is designed for **management and senior domain leads** who are responsible for steering performance but do **not** operate day-to-day processes.

This page bridges the gap between:

- **Strategic direction (T1)** and
- **Operational control (T3)**

---

## Primary Decision Question

**Why are we off target, and which levers explain the gap?**

If this question cannot be answered within **30 seconds**, the page is not done.

---

## When to Use This Page Type

Use **T2 – Tactical Variance** when:

- targets, plans, or benchmarks exist
- deviations must be explained, not just observed
- decisions involve **adjusting levers**, not executing tasks
- the audience needs causal understanding, not raw details

Typical usage rhythm:

- Monthly performance reviews
- Domain or function steering meetings
- Management deep-dives after T1 escalation

---

## When NOT to Use This Page Type

Do **not** use T2 if:

- the goal is purely strategic alignment → use **T1**
- the goal is operational monitoring or alerting → use **T3**
- concrete actions must be prescribed → use **T4**

T2 must never turn into an operational dashboard or an action list.

---

## Analytical Scope (3–30–300 Rule)

### 3 Seconds – Variance Signal

- Clear KPI vs. target signal
- Direction and magnitude of deviation
- Immediate visibility of problem or outperformance

### 30 Seconds – Driver Explanation

- Variance bridge or decomposition
- Key drivers ranked by impact
- Comparison across relevant segments

### 300 Seconds – Limited Detail

- Selected drill-downs for validation
- No transactional-level exploration
- No free-form slicing or ad-hoc analysis

---

## Allowed Slots

| Slot | Purpose | Mandatory |
|-----|--------|-----------|
| KPI Summary | Performance vs. target | Yes |
| Variance | Explain deviation | Yes |
| Trend | Context and momentum | Optional |
| Ranking | Identify key contributors | Optional |
| Mix | Structural composition | Optional |
| Funnel | Process loss analysis | Optional |

---

## Disallowed Slots

The following slots are **not allowed** on T2 pages:

- Exception lists
- Root-cause analysis at record level
- Detail matrices
- Prescriptive recommendation slots

If prescriptive content is required, escalate to **T4**.

---

## Visual Governance (Summary)

- Waterfall charts for variance explanation
- KPI cards with target reference
- Line charts for trend context
- Horizontal bar charts for driver ranking
- 100% stacked bars for mix

Disallowed:

- Scatter plots
- Large tables or matrices
- Exploratory visuals

Visuals must explain **causality**, not encourage exploration.

---

## Tactical Action Signals

T2 pages may include **Tactical Action Signals** only:

- Purpose: indicate which lever requires attention
- No ownership assignment
- No execution steps

Examples:

- “Pricing effect is the dominant driver – validate assumptions”
- “Volume decline driven by Segment B – initiate focused review”

T2 does **not** replace prescriptive decision-making.

---

## User Experience Rules

- Clear left-to-right or top-down logic: signal → explanation → contributors
- Limited interactivity (no analytical playground)
- Maximum of 2–3 slicers (time, organization, one domain dimension)
- Stable layout to support recurring reviews

---

## Success Criteria (Definition of Done)

A T2 page is complete when:

- the deviation is clearly understood
- the dominant drivers are unambiguous
- management knows **where to intervene**, but not yet **how**
- escalation to T3 or T4 is obvious if required

---

## Narrative Arc

### The Big Idea

One sentence that every T2 page must communicate:

> “The [Δ] gap vs [reference] is driven by [top factor] ([magnitude]) — intervention in [area] is required.”

Example: *”The -€4.2M revenue gap vs Plan YTD is driven primarily by DACH volume decline (-€3.1M) and an adverse mix effect — intervention in DACH promotional strategy is required.”*

### Story Structure

**Act 1 — Signal the Deviation (3 seconds, KPI Band)**
The KPI delta is the first word of the T2 story. It tells the reader: “We have a gap. Here is the magnitude.”
- The primary KPI shows the deviation clearly — absolute + percentage, colored signal.
- Supporting KPIs show whether the gap is isolated or systemic.
- The reader must not need to look at the driver charts to understand that a problem exists.

**Act 2 — Explain the Gap (30 seconds, Driver Zone)**
The three driver visuals together answer “Why?”. Each adds one layer to the explanation:
- `Main_1` (Trend): *”This is the journey — when did the deviation begin, and is it accelerating?”*
  The trend answers whether this is a new problem or an ongoing one. Inflection points are annotated.
- `Main_2` (Variance Bridge / Waterfall): *”This is the breakdown — which factors explain the gap?”*
  The waterfall is the structural heart of T2. It reconciles the KPI delta into named drivers.
  Each bar = one driver (Price, Volume, Mix, FX). The bars must sum to the total deviation.
- `Main_3` (Ranking / Driver Ranking): *”These are the actors — which entities drive each factor?”*
  Sorted by magnitude of deviation. Worst-performing entity first. Immediately actionable.

**Act 3 — Limited Validation (300 seconds, Detail Page)**
The detail page validates the drivers at entity level. It does not introduce new drivers or explanations.

### Visual Title Narrative

The three driver visual titles must tell a coherent “Why?” story:

| Slot | Narrative Role | Example Title |
|---|---|---|
| `Main_1` (Trend) | “When did the problem start?” | “How has Net Sales trended vs Plan over the last 12 months?” |
| `Main_2` (Variance) | “What caused the gap?” | “Which factors explain the -€4.2M revenue gap vs Plan?” |
| `Main_3` (Ranking) | “Who/where is the gap?” | “Which regions drive the largest deviation from Plan?” |

Together they form: *”The gap started in [period], was caused by [factors], and is concentrated in [entities].”*

### Waterfall Chart Contract

The variance bridge is the most important visual on a T2 page. It must:
- Start with the reference value (Plan or Prior Year) on the left
- End with the actual value on the right
- Sum of all driver bars = (Actual − Reference)
- Each bar is labeled with absolute value and % of total gap
- Positive contributions (green), negative contributions (red), net bars (neutral)
- Maximum 7–8 bars; group smaller drivers into “Other”

### What Makes This Page Fail the Narrative

| Failure | Cause | Fix |
|---|---|---|
| Variance bridge doesn't reconcile | KPI delta ≠ sum of waterfall bars | Fix data model; validate driver logic |
| Three charts tell disconnected stories | Different time periods, different KPIs | Align all three to same KPI, same period |
| Trend inflection not annotated | Cause of deviation is not explained | Add reference line or text callout at the key date |
| Ranking sorted alphabetically | Hardest-to-scan ordering | Sort by absolute deviation magnitude, descending |

---

## Key Principle
>
> **T2 answers “Why are we off target?” – not “Who failed?” and not “What should we do?”**

If the page drifts into operational blame or prescriptive actions, it is no longer tactical.

