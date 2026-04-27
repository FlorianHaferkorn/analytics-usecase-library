# T3 – Operational Monitoring & Exceptions

> **Design basis:** Munzner (2014) nested model — domain task (identify threshold breaches, triage, assign) → data abstraction (exception flag, deviation magnitude, entity) → visual encoding (exception table + sparkline). Shneiderman (1996): this page implements the *filter* and *zoom* tiers — users filter to exceptions and zoom to individual entity context.

## Purpose

The Operational Monitoring page ensures **stable day-to-day performance** by identifying **where operations deviate from defined thresholds** and **who must react immediately**.

It is designed for **operational managers and process owners** who are accountable for execution.

This page focuses on **control, prioritization, and timely intervention** — not explanation and not recommendation.

---

## Primary Decision Question

**Where are we currently outside operational thresholds, and who needs to act now?**

If this question cannot be answered within **30 seconds**, the page is not done.

---

## When to Use This Page Type

Use **T3 – Operational Monitoring** when:

- processes are running continuously (daily / weekly)
- clear thresholds, SLAs, or rules exist
- deviations require **immediate attention**
- responsibility is operationally assigned

Typical usage rhythm:

- Daily or weekly operational reviews
- Shift handovers
- Incident or backlog monitoring

---

## When NOT to Use This Page Type

Do **not** use T3 if:

- the goal is strategic steering → use **T1**
- deviations must be causally explained → use **T2**
- concrete actions must be recommended → use **T4**

T3 must never become a strategy or diagnosis page.

---

## Analytical Scope (3–30–300 Rule)

### 3 Seconds – Operational Status

- Clear signal: in control / out of control
- Number of open exceptions
- Immediate visibility of critical issues

### 30 Seconds – Prioritization

- Ranked list of exceptions by severity
- Grouping by owner, location, or process
- Clear indication of urgency

### 300 Seconds – Controlled Detail

- Drill-down into affected entities only
- No free exploration
- Focus on validation, not analysis

---

## Allowed Slots

| Slot | Purpose | Mandatory |
|-----|--------|-----------|
| KPI Summary | Operational health | Optional |
| Exceptions | Identify critical deviations | Yes |
| Ranking | Prioritize by severity or impact | Optional |
| Trend | Short-term stability | Optional |
| Root Cause | High-level contributing factors | Optional |
| Detail Matrix | Affected records only | Optional |

---

## Slot-Specific Rules

### Exceptions (Mandatory)

- Must be rule-based (thresholds, SLAs, limits)
- No manual filtering as substitute
- Each exception must be attributable to an entity

### Root Cause (Optional)

- Only high-level factors
- No statistical deep dives
- Purpose: contextualize, not explain fully

---

## Disallowed Slots

The following slots are **not allowed** on T3 pages:

- Variance bridges
- Prescriptive recommendation slots
- Funnels

If causal explanation is required, escalate to **T2**.
If recommendations are required, escalate to **T4**.

---

## Visual Governance (Summary)

- Exception tables or lists
- Horizontal bar charts for prioritization
- Line charts for short-term trends
- Minimal supporting visuals only

Disallowed:

- Waterfall charts
- Scatter plots (except for Root Cause slot when `needs_root_cause = true`)
- Exploratory visuals

**Note:** Scatter plots are allowed for Root Cause slot in T3 when explicitly activated (`needs_root_cause = true`), per Visual Whitelist rules.

Visuals must support **control**, not discovery.

---

## Operational Action Signals

T3 pages may include **Operational Action Signals** only:

- Purpose: trigger immediate response
- Examples:
  - “Backlog exceeds SLA – clear today”
  - “Incident count above limit – escalate to shift lead”

Rules:

- Actions must be obvious from the exception itself
- No prioritization algorithms
- No action scoring

---

## User Experience Rules

- Designed for frequent use
- Dense but readable layout
- Minimal slicers (time, org/process)
- No decorative visuals

---

## Success Criteria (Definition of Done)

A T3 page is complete when:

- exceptions are clearly visible and prioritized
- operational owners know what requires attention now
- no interpretation or explanation is required
- the page supports fast, repeatable use

---

## Narrative Arc

### The Big Idea

One sentence that every T3 page must communicate:

> “[N] [entity type] are currently outside threshold — [N_critical] require immediate attention in [area].”

Example: *”14 accounts are currently outside the overdue threshold — 3 are critical and require escalation by end of day.”*

### Story Structure

**Act 1 — Operational Status (3 seconds, KPI Band)**
The T3 3-second layer is a control panel, not a performance summary.
- The most important KPI is the **count of exceptions** (e.g., “14 accounts overdue”), not a revenue figure.
- A traffic-light summary (In Control / At Risk / Critical) serves as the opening signal.
- The reader must be able to answer “Is everything under control right now?” before their eye moves.

**Act 2 — Prioritized Exceptions (30 seconds, Driver Zone)**
The exception list and ranking visuals tell the story of “Where and how bad?”:
- `Main_1` (Exceptions Table / Alert List): *”These are the cases that require attention — prioritized by severity.”*
  Sorted: Critical first, then Warning. Each row has an entity, metric, threshold, actual, and deviation.
- `Main_2` (Trend — short-term): *”This is the recent pattern — are exceptions increasing or decreasing?”*
  Short window (last 7–30 days). Not strategic trend; operational pulse.
- `Main_3` (Ranking by severity/owner): *”This is where concentration lies — which area or owner has the most open cases?”*

**Act 3 — Controlled Detail (300 seconds, Detail Page)**
The detail page shows records that are in exception state only. Not all records.
- Filter is pre-applied: the reader arrives seeing only what needs attention.
- No free exploration. The focus is validation and assignment, not analysis.

### Visual Title Narrative

| Slot | Narrative Role | Example Title |
|---|---|---|
| `Main_1` (Exceptions) | “What needs attention now?” | “Which accounts are currently above the overdue threshold?” |
| `Main_2` (Trend) | “Is the situation improving?” | “How has the overdue account count trended over the last 30 days?” |
| `Main_3` (Ranking) | “Where is the concentration?” | “Which team owns the most critical open cases?” |

### Exception List Column Order

The exception table must be designed for fast scanning, not for completeness. Column order:

1. **Entity** — who/what (leftmost, always visible, anchors the F-pattern scan)
2. **Severity** — traffic light icon + label (Critical/Warning/Info)
3. **Metric** — which KPI is in exception
4. **Actual vs. Threshold** — how far outside (absolute + %)
5. **Owner** — who is responsible for resolution
6. **Age** — how long has this been in exception state

Do not show more than 6 columns without a toggle to “show more”.

### What Makes This Page Fail the Narrative

| Failure | Cause | Fix |
|---|---|---|
| All rows colored red/amber | No severity hierarchy | Define threshold bands; Critical ≠ Warning |
| Strategic KPIs in Zone 1 | Wrong page type applied | Replace with exception count KPI; strategic KPIs → T1 |
| Exception table unsorted | Alphabetical or insert order | Sort by severity first, then by deviation magnitude |
| Page explains “why” exceptions occur | T2 content leaked in | Remove root cause analysis; keep operational context only |

---

## Key Principle
>
> **T3 answers “Where is execution breaking right now?” – nothing else.**

If the page starts explaining *why* or recommending *how*, it is no longer operational.

