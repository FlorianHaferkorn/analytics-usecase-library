# T4 – Prescriptive Recommendation

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

## Key Principle
> **T4 answers “What should we do now?” – and commits to it.**

If the page hesitates to recommend, it is not prescriptive.
