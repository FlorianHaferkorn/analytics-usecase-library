# <USE CASE ID> – <USE CASE NAME>

---

## 0. Metadata (Mandatory)
- **Use Case ID:** <COM-001 / FIN-001 / …>
- **Domain:** <Commercial / Finance / Operations / …>
- **Owner (Business):** <Role / Name>
- **Reporting Level:** <Strategic / Tactical / Operational>
- **Analytics Stage:** <Descriptive / Diagnostic / Predictive / Prescriptive>
- **Related Data Contract:** <path/to/data_contracts/domains/...yaml>
- **Related Semantic Model:** <path/to/semantic_models/.../model_definition.yaml>

---

## 1. Summary
**Purpose:** One sentence describing the business objective.  
**Business Value:** 1–2 sentences describing concrete value (growth, margin, cost, risk, liquidity, experience).  
**Out of Scope:** 1–2 bullets for what is explicitly not covered.

---

## 2. Core Questions
List 4–7 key business questions this use case answers.

- <Business question 1>
- <Business question 2>
- <Business question 3>
- …

**Example Queries (optional):**
- “How did Net Sales vs Plan develop by Region/Channel over the last 3 months?”
- “Which customers contribute most to margin leakage?”

---

## 3. KPI Set (Business View)
Every KPI must exist in the KPI catalog.

| KPI Name | KPI ID (mandatory) | Purpose | Definition (short) | Unit / Format | Target / Threshold | Interpretation |
|----------|--------------------|---------|--------------------|----------------|--------------------|----------------|
| <KPI> | <domain.topic.metric> | <why> | <formula short> | <€, %, days, index> | <target/band/limit> | <how to read> |
| … | … | … | … | … | … | … |

> Do: minimal but complete for decisions, incl. targets/bands.  
> Don’t: add technical fields as KPIs.

---

## 4. Business Logic & Thresholds
Rules to evaluate performance and trigger actions.

- <Logic: e.g., Revenue Growth % < 0 for 2 months = critical>
- <Thresholds: e.g., GM % < 25 % in core channel>
- <Exceptions: e.g., exclude new markets < 6 months>

**Trigger Logic (formal, for automation):**
```
WHEN <KPI> <operator> <threshold>
AND  <optional condition>
THEN propose Action Code <X>
```

---

## 5. Action Codes
List all Action Codes relevant for this use case (use the global catalog).

| Code | Name | Trigger (formal, using KPIs) | Description (business action) | Expected KPI Impact |
|------|------|------------------------------|-------------------------------|----------------------|
| <X1> | <Name> | <rule from section 4> | <what is done> | <+%, ↑pp, stabilise, etc.> |
| <X2> | … | … | … | … |

> Do: reference the global Action Code catalog (no variants).  
> Don’t: vague triggers without KPI reference.

---

## 6. 3–30–300 Page Layout

### 6.1 3-Second Layer (KPI Cards – mandatory)
Pick 4–5 core KPIs as cards.

### 6.2 30-Second Layer (Main Visuals – mandatory)
Define required visuals with fields/axes (no “TBD” in rollout).

| Visual Name | Visual Type | X-Axis / Category | Y-Axis / Value | Segment / Legend | Filters / Defaults |
|-------------|-------------|-------------------|----------------|------------------|--------------------|
| <Sales Trend> | Line | Date[Month] | [Net Sales Amount] | Region | Last 12–24 months |
| <Margin Ranking> | Bar (horizontal) | Org[Channel] | [Gross Margin %] | Region | Top/Bottom N |
| … | … | … | … | … | … |

### 6.3 300-Second Layer (Diagnostics & Detail)
Describe drill paths, required fields, and exports.

---

## 7. Dependencies, Assumptions & Constraints
- **Data Dependencies:** required domains, tables, fields; Plan/Baseline available?
- **Business Assumptions:** e.g., plan values frozen after month-end.
- **Constraints:** e.g., data latency, missing dimensions, estimation logic; Owner per process.

---

## 8. Success Criteria
Define measurable outcomes and adoption.

- Leading (Adoption): e.g., “>80 % use in monthly reviews”
- Lagging (KPI): e.g., “–30 % negative ROI promos in 6 months”
- Cadence/Quality: e.g., “monthly review, no KPI-definition conflicts”
