# T4 – Prescriptive Recommendation

> **Design basis:** Munzner (2014) nested model — domain task (decide and act) → data abstraction (trigger condition, recommended action, owner, expected impact) → visual encoding (action_card + detail matrix). Shneiderman (1996): this page implements the *details-on-demand* tier — reached via drillthrough from T1/T2/T3.

## Purpose

The Prescriptive Recommendation page converts insights into **clear, accountable decisions**.

It answers **what should be done next**, **by whom**, and **with what expected impact**.
T4 is the **only page type** where the framework intentionally prescribes actions.

This page is designed for **decision owners** who are responsible for choosing and triggering actions,
not for continuous monitoring or explanation.

---

## Primary Decision Question

**What is the best next action, for which entity, with what expected impact?**

If this question cannot be answered within **30 seconds**, the page is not done.

---

## When to Use This Page Type

Use **T4 – Prescriptive Recommendation** when:

- a decision must be made, not just observed or explained
- multiple options exist and prioritization is required
- ownership can be clearly assigned
- expected impact can be estimated

Typical usage rhythm:

- After escalation from T2 (tactical) or T3 (operational)
- As part of focused decision or steering meetings
- For exception resolution and opportunity realization

---

## When NOT to Use This Page Type

Do **not** use T4 if:

- the situation is still unclear → use **T2**
- execution must be monitored → use **T3**
- decisions are strategic or directional → use **T1**

T4 must never be used as a generic “action dashboard”.

---

## Analytical Scope (3–30–300 Rule)

### 3 Seconds – Recommendation

- One primary recommended action
- Clear owner and priority
- Immediate sense of urgency or opportunity

### 30 Seconds – Evidence

- Why this action is recommended
- Key supporting metrics
- Comparison to alternatives (if any)

### 300 Seconds – Validation

- Detailed records or assumptions
- Sensitivity or scenario checks
- No exploratory analysis

---

## Allowed Slots

| Slot | Purpose | Mandatory |
|-----|--------|-----------|
| Prescriptive | Recommendation and prioritization | Yes |
| KPI Summary | Context of the decision | Optional |
| Trend | Recent development | Optional |
| Ranking | Affected entities or options | Optional |
| Root Cause | Contextual explanation | Optional |
| Detail Matrix | Validation data | Optional |

---

## Slot-Specific Rules

### Prescriptive (Mandatory)

- Must be based on governed Action Codes
- Exactly one **primary** recommendation must be highlighted
- Alternatives may be shown, but clearly secondary

### Root Cause (Optional)

- Context only, not full analysis
- Must not contradict the recommendation

---

## Disallowed Slots

The following slots are **not allowed** on T4 pages:

- Variance bridges
- Exception-only monitoring views
- Funnels without an explicit decision context

If explanation is required, move back to **T2**.
If monitoring is required, move to **T3**.

---

## Visual Governance (Summary)

- Recommendation tables or cards
- Ranked lists with priority and impact
- Scatter plots (impact vs. effort or risk)
- Supporting KPI cards

Disallowed:

- Dense operational tables
- Exploratory visuals
- Visuals without decision relevance

Visuals must support **choice**, not discovery.

---

## Action Panel (Mandatory)

Every T4 page must include a **full Action Panel**.

Minimum requirements:

- Action title
- Owner role
- Trigger condition
- Recommended steps
- Expected impact (range acceptable)
- Priority

If ownership or impact cannot be defined, no recommendation must be shown.

---

## User Experience Rules

- Focused layout, minimal distractions
- One clear “best next action” visible without scrolling
- Alternatives collapsed by default
- Maximum of 2–3 slicers (context only)

---

## Success Criteria (Definition of Done)

A T4 page is complete when:

- the recommended action is unambiguous
- ownership is clear
- expected impact is understood
- decision makers can confidently choose or reject the action

---

## Narrative Arc

### The Big Idea

One sentence that every T4 page must communicate:

> “[Trigger condition] in [context]. Recommended: [action] by [owner] — expected impact [impact] by [deadline].”

Example: *”GM% in DACH has been below the 18% threshold for 3 consecutive months. Recommended: reduce promotional depth by 15% — expected recovery of +0.8pp GM% by end of October, owned by Commercial Manager DACH.”*

The Big Idea on a T4 page is a commitment, not an observation. If it cannot be stated this specifically, the action code is not ready.

### Story Structure

**Act 1 — Recommendation Signal (3 seconds, Zone 1)**
The Action Panel header or a featured recommendation card is the opening signal.
- The primary recommendation is visible immediately — title, owner, and magnitude.
- The KPI status provides the trigger context: “Here is the situation that demands this action.”
- The reader must know *what to do* before they look at the supporting evidence.

**Act 2 — Evidence (30 seconds, Driver Zone)**
The driver visuals support the recommendation with the minimum evidence required to build confidence:
- `Main_1` (Trend): *”This is the trend that triggered the recommendation — the pattern is clear.”*
- `Main_2` (Ranking / Impact-Effort): *”These are the affected entities / these are the options ranked.”*
- `Main_3` (optional, Root Cause context): *”This is why this action and not another.”*

Evidence must support the recommendation — not open a debate. If the evidence undermines the recommendation, the action code is wrong, not the page.

**Act 3 — Validation (300 seconds, Detail Page)**
The detail page provides the data to validate the recommendation at entity level.
- The Action Panel is always present (full panel, not teaser).
- The detail matrix shows affected entities, sorted by impact relevance.
- The reader arrives ready to decide: approve, reject, or escalate.

### Visual Title Narrative

| Slot | Narrative Role | Example Title |
|---|---|---|
| `Main_1` (Trend) | “Why now?” | “How has GM% developed vs threshold over the last 6 months?” |
| `Main_2` (Ranking/Options) | “Where / what are the options?” | “Which accounts are most impacted by the promotional depth issue?” |
| `Main_3` (optional) | “What explains the trigger?” | “What drives the GM% decline — volume, price, or mix?” |

### Action Panel Contract

The Action Panel on T4 is mandatory and must be fully populated. It is the resolution of the narrative arc.

```
RECOMMENDED ACTION                ← Bold, prominent — the Big Idea in 3 words
[Action title]

WHY                               ← Trigger evidence in 1–2 sentences
[Condition that triggered this]

WHAT TO DO                        ← Ordered steps; max 4
1. [Step]
2. [Step]
3. [Step]

OWNER          [Role name]        ← Who is accountable
DUE            [Date / cycle]     ← When this must be decided
IMPACT         [+/- magnitude]    ← What we expect if action is taken
PRIORITY       [High / Medium]    ← Relative urgency
```

If any of these fields cannot be populated from the Action Code YAML, the action is not ready and must not appear.

### What Makes This Page Fail the Narrative

| Failure | Cause | Fix |
|---|---|---|
| Action Panel is empty or vague | Action code not authored | Author the Action Code before building the T4 page |
| Recommendation is uncertain (“consider...”) | Insufficient confidence | Return to T2/T3 for more analysis; T4 must commit |
| Evidence contradicts recommendation | Data model inconsistency | Investigate data discrepancy before proceeding |
| Multiple recommendations with no priority | Missing action prioritization | Mark exactly one as primary; others are secondary |
| Page is used as a generic action dashboard | Wrong page type | T4 is for one specific decision context; rebuild as T3 |

---

## Key Principle
>
> **T4 answers “What should we do now?” – and commits to it.**

If the page hesitates to recommend, it is not prescriptive.

