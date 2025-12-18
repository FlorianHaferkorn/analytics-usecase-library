# T3 – Operational Monitoring & Exceptions

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
- Scatter plots (except in T4)
- Exploratory visuals

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

## Key Principle
> **T3 answers “Where is execution breaking right now?” – nothing else.**

If the page starts explaining *why* or recommending *how*, it is no longer operational.
