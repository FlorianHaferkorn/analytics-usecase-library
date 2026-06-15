# Content Quality Guide — Page Templates

> **Authority:** This document defines content quality standards for all text, labels, and narrative elements in ALUCA (Analytics Library of Use Cases) reports.
>
> **Governs:** Visual titles, KPI card labels, Smart Narrative, Action Panel copy, KPI selection criteria.
>
> **Implements:** `Storytelling_Principles.md §2, §8, §10, §12` — IBCS SAY rule, Knaflic direct-labeling, Few KPI context requirement.

---

## 1. Visual Titles

Every visual has a **question-oriented title** that states the conclusion or question the chart answers. Titles are read before the chart — they frame the reader's interpretation before a single data point is processed.

### The IBCS SAY Rule

> A chart title must be the **conclusion**, not a description of the chart type or axis.

Apply to all visual titles: "If I removed the chart and kept only the title, would the reader know what to think? Could I verify whether the title is true or false by looking at the chart?"

### Good vs. Bad — Visual Titles

| ✗ Bad (descriptive) | ✓ Good (question / conclusion) |
|---|---|
| Revenue Chart | How is Net Sales trending vs prior year? |
| Variance Analysis | Which factors explain the €4.2M revenue gap vs Plan? |
| Top Customers | Which customers drive the most revenue impact this month? |
| Exception Report | Which accounts are currently above the overdue threshold? |
| Data Table | Which regions explain the revenue shortfall? |
| Recommended Actions | What should we do to recover DACH margin by end of month? |
| KPI Overview | Are we on track for our commercial targets this quarter? |
| Monthly Trend | Has revenue recovered after the October decline? |
| Regional Performance | Which regions are underperforming vs Plan YTD? |
| Margin by Segment | In which customer segments is gross margin below threshold? |

### Title Construction Formula

```
[Question word] + [KPI name] + [comparison or context] + [period if not obvious from slicer]?
```

Examples:
- `"How has [Net Sales] trended [vs Plan] [over the last 12 months]?"`
- `"Which [regions] drive the largest [deviation from Plan YTD]?"`
- `"Where is [GM%] [currently below the 18% threshold]?"`

### Title Length Limit

- Maximum **80 characters** (including spaces)
- Maximum **2 lines** in the visual header
- Truncate at word boundaries with `…` if space requires shortening

### When a Conclusion Title Is Appropriate (IBCS SAY)

For pages where the finding is stable and known (e.g., a monthly report always showing the same pattern), use conclusion-form titles:

| Chart | Conclusion Title |
|---|---|
| Trend declining for 3 months | "Net Sales has declined consistently for 3 consecutive months" |
| DACH always underperforms | "DACH drives 74% of the total Plan deviation" |
| One action clearly dominates | "Reducing promo depth in DACH recovers +0.8pp GM%" |

Use conclusion titles when the Big Idea is already known. Use question titles when the answer may vary by filter context.

---

## 2. KPI Card Labels

KPI card labels are the names that appear above the hero value. They must be short, unambiguous, and free of redundancy.

### Rules

- Maximum **25 characters** (shorter is better)
- No period qualifiers in the label (period comes from the slicer or kpi_period field)
- No redundant words ("Total", "Grand", "Overall" — remove unless meaningful distinction required)
- Capitalize like a product name: Title Case

### Good vs. Bad — KPI Labels

| ✗ Bad | ✓ Good | Reason |
|---|---|---|
| Total Revenue (EUR) | Net Sales | "EUR" belongs in the format; "Total" is redundant |
| Gross Margin % (Actual vs Plan) | GM % | Comparison belongs in the delta field, not the label |
| Active Customer Count Q3 2025 | Active Customers | Period is set by the slicer |
| NPS Score — October | Net Promoter Score | Period from context |
| Costs (Excl. Depreciation) | Cash Costs | Move the definition to the info tooltip |
| No. of Open Exceptions | Open Exceptions | "No. of" adds no value |
| Average Order Value (AOV) | Avg Order Value | Acronym clarification → tooltip |

### KPI Label Hierarchy on the Card

```
[KPI Label]       ← 10–11pt, neutral gray, top of card
[€42.3M]          ← 28–36pt, bold, neutral dark — hero value
[▲ +8.2%]         ← 13–14pt, semantic color — delta
[vs Plan · MTD]   ← 9–10pt, muted gray — reference + period
[▬▬▬▬▬▬▬▬]       ← sparkline (optional)
```

The **KPI Label is the smallest element** on the card. The **hero value is the largest**. This hierarchy must not be inverted.

---

## 3. KPI Selection Criteria — What Goes in Zone 1

Not every metric belongs in the 3-second layer. Zone 1 is for the KPIs that, when red, demand immediate decision-maker attention.

### Inclusion Criteria (all must be true)

| Criterion | Test |
|---|---|
| **Strategic relevance** | Is this a top-level outcome KPI? (Revenue, Margin, NPS — not input/driver) |
| **Decision relevance** | Does the status of this KPI change what a decision maker does today? |
| **Target availability** | Can we show a reference value? (Without a target, we cannot signal on/off track) |
| **Data freshness** | Is data current enough for the reporting rhythm? (Daily KPI on a monthly report → wrong) |
| **Audience alignment** | Is this KPI meaningful to this page's audience without explanation? |

### Disqualifiers — Move to 30s Layer or Remove

| Disqualifier | Action |
|---|---|
| KPI is a driver / input metric (e.g., "Promo Depth %") | Move to Main_2 or Main_3 — it explains the outcome, not the status |
| KPI is a dimension attribute (e.g., "Region Count") | Remove — not a performance metric |
| No reference value exists | Remove from Zone 1; use informational KPI card in Zone 3 |
| Redundant with another Zone 1 KPI | Remove the less important one |
| Requires explanation for the audience to interpret | Remove — Zone 1 metrics must be self-evident |

### Maximum KPIs by Template

| Template | Max Zone 1 KPIs | Notes |
|---|---|---|
| T1 — Strategic | 4 | Hero card occupies 1/3 of the band; max 2 additional strategic KPIs |
| T2 — Tactical | 5 | Primary KPI + 4 influencing KPIs |
| T3 — Operational | 6 (compact) | Exception count is one mandatory KPI |
| T4 — Prescriptive | 3–4 | Focus on trigger context only |

---

## 4. Smart Narrative Templates

The Smart Narrative is a 1–3 sentence summary of what is true in the current filter context. It must be written as a conclusion, not a description of the visuals on the page.

### Rules

- **Maximum 2 sentences** (ideally 1)
- **Present tense** — "is", not "was" or "will be"
- **Quantified** — always include the key number and the deviation
- **Context-aware** — changes automatically with filter (dynamic Smart Narrative) or is authored per use-case context (static)
- **Does not describe the visuals** — "The chart above shows..." → remove

### Templates by Page Type

**T2 — Tactical Variance:**
```
[KPI] of [value] is [Δabs] ([Δ%]) vs [reference] [period],
primarily driven by [top driver] ([driver magnitude]) and [second driver if material].
```

Example: *"Net Sales of €38.1M is -€4.2M (-10%) vs Plan YTD, primarily driven by DACH volume decline (-€3.1M) and an adverse product mix effect (-€0.8M)."*

**T3 — Operational Monitoring:**
```
[N] [entity type] are currently outside [threshold name] —
[N_critical] critical, [N_warning] warning. [Most urgent entity] requires immediate action.
```

Example: *"14 accounts are currently outside the 60-day payment threshold — 3 are critical (>90 days). Account GmbH & Co. KG requires escalation by end of day."*

**T4 — Prescriptive Recommendation:**
```
[Trigger condition] in [context] — [threshold value] threshold crossed.
Recommended action: [action title] by [owner] — expected impact [impact] by [deadline].
```

Example: *"GM% in DACH has been below 18% for 3 consecutive months. Recommended: reduce promotional depth by 15% — expected recovery of +0.8pp GM% by end of October, owned by Commercial Manager DACH."*

**T1 — Strategic Overview (Detail page):**
```
[Domain] is [on/off] track as of [period] — [primary KPI] at [value] ([Δ vs target]).
[One strategic observation about momentum or concentration.]
```

Example: *"Commercial performance is off track as of Q3 2025 — Net Sales at €118M, -8% vs Plan. Declining momentum in DACH drives the majority of the strategic gap."*

---

## 5. Decision Question Banner

The decision question banner appears at the top of the page (above or directly below the KPI band) and states the question this page answers. It is visible at all times and does not scroll away.

### Rules

- **One question** only — the page's primary decision question
- **Present tense or present perfect** — "Are we..." / "Where are we..."
- **Audience-specific language** — executive language for T1, operational language for T3
- **Maximum 80 characters** (one line at any font size used)

### Examples by Template

| Template | ✓ Good Banner |
|---|---|
| T1 | "Are we meeting our strategic targets this quarter?" |
| T2 | "Why are we off Plan, and which levers explain the gap?" |
| T3 | "Where is execution currently outside operational thresholds?" |
| T4 | "What is the best next action to recover GM% in DACH?" |

---

## 6. Action Panel Copy

The Action Panel is the final resolution of the T4 narrative arc. Every word must be precise, actionable, and confident. No hedging.

### Field-by-Field Standards

**Action Title** (bold, 3–6 words max)
```
✗ "Consider reviewing promotional strategy in DACH region"
✓ "Reduce promo depth in DACH"
```
The title must be a directive, not a suggestion. Use verb-first sentence structure.

**WHY (trigger evidence, 1–2 sentences)**
```
✗ "The data shows that margins have been declining."
✓ "GM% in DACH has been below the 18% threshold for 3 consecutive months, driven by excessive promotional depth (avg 22% vs target 15%)."
```
The WHY must be quantified and specific. Vague triggers produce no commitment.

**WHAT TO DO (ordered steps, max 4)**
```
✗ "1. Review discounts  2. Talk to buyer  3. Monitor situation"
✓ "1. Cap promotional discounts at 15% in all DACH accounts  2. Renegotiate volume rebate agreement with Top-3 DACH buyers  3. Alert Category Manager to shift to higher-margin product mix"
```
Each step must be independently executable by the named owner. No step should require interpretation.

**OWNER**
- Role, not name: "Commercial Manager DACH" not "Max Muster"
- One owner only. If multiple owners are required, the action is not granular enough.

**DUE**
- Specific date or cycle: "End of October" / "By next steering meeting (Nov 5)" / "Within 5 business days"
- Never: "ASAP" / "When possible" / "TBD"

**IMPACT**
- Quantified: "+0.8pp GM%" / "+€1.2M revenue" / "Reduces exceptions from 14 to <3"
- Include confidence where relevant: "+0.8pp GM% (high confidence, based on 2023 playbook)"
- Never: "Improves performance" / "Positive impact expected"

---

## 7. Tooltip Content Standards

Tooltips appear on hover over data points, KPI cards, and table cells. They provide definition and detail-on-demand without cluttering the main canvas.

### KPI Card Info Tooltip (ⓘ icon)

```
[KPI Name]
Definition: [One sentence: what this metric measures]
Calculation: [Formula in plain language, not DAX]
Grain: [What one row in the underlying data represents]
Source: [Data source or system]
Owner: [Who is responsible for data quality]
```

### Chart Data Point Tooltip

```
[Entity name]
[KPI name]: [value] [unit]
[Reference]: [target/PY value] [unit]
[Delta]: [Δabs] ([Δ%])
[Period]: [date / period label]
```

Always show: value, reference, and delta. Do not show raw identifiers or technical field names.

---

## 8. Abbreviation and Formatting Standards

Consistent abbreviations prevent ambiguity and save space on dense visuals.

### IBCS-Aligned Reference Abbreviations

| Concept | Abbreviation | Never use |
|---|---|---|
| Actual (current period) | AC | Actual, Act, A |
| Prior Year | PY | Last Year, LY, YoY base |
| Plan / Budget | PL | Budget (in KPI labels), Target (when Plan exists) |
| Forecast | FC | Forecast (in compact labels) |
| Month-to-Date | MTD | MtD |
| Year-to-Date | YTD | YtD |
| Prior Month | PM | Last Month, LM |
| Quarter-to-Date | QTD | QtD |

### Number Formatting

| Range | Format | Example |
|---|---|---|
| < 1K | No abbreviation | 847 |
| 1K – 999K | K suffix, 1 decimal | 42.3K |
| 1M – 999M | M suffix, 1 decimal | 1.2M, 42.3M |
| ≥ 1B | B suffix, 1 decimal | 1.4B |
| Percentages | 1 decimal, % suffix | 18.4%, -1.1pp |
| Currency | Prefix with symbol, M/K suffix | €42.3M, $1.2K |
| Point change (%) | `pp` suffix | -1.1pp (not -1.1%) |

**Point vs. percentage:** Use `pp` (percentage points) when comparing two percentage values (e.g., GM% vs target GM%). Use `%` when expressing change in a non-percentage KPI (e.g., revenue +8.2%).

---

## Quick Reference Checklist

Before a page is considered content-complete:

- [ ] Every visual title is question- or conclusion-form (not descriptive)
- [ ] All KPI labels are ≤25 characters, Title Case, no period qualifiers
- [ ] Zone 1 contains only outcome KPIs with a reference value
- [ ] Smart Narrative is quantified, 1–2 sentences, present tense
- [ ] Decision question banner is visible and ≤80 characters
- [ ] Action Panel (if T4) uses directive language, quantified impact, specific owner and due date
- [ ] All abbreviations follow IBCS notation (AC, PY, PL, FC, MTD, YTD)
- [ ] All numbers use K/M/B abbreviation where ≥1000
- [ ] Tooltips are populated for all KPI cards (ⓘ icon)
