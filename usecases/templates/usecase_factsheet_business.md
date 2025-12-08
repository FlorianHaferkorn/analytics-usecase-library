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
List 4–7 key business questions that this use case answers.

- <Business question 1>  
- <Business question 2>  
- <Business question 3>  
- …

**Example Queries (optional but recommended):**

- “How did Net Sales vs Plan develop by Region and Channel over the last 3 months?”  
- “Which customers contribute most to margin leakage?”

---

## 3. KPI Set (Business View)
Every KPI must exist in the KPI catalog.

| KPI Name | KPI ID (mandatory) | Purpose | Definition (short) | Unit / Format | Target / Threshold | Interpretation |
|----------|--------------------|---------|--------------------|----------------|--------------------|----------------|
| <KPI> | <domain.topic.metric> | <why> | <formula short> | <€, %, days, index> | <target, band, limit> | <how to read> |
| … | … | … | … | … | … | … |

> Do: keep KPI list minimal, but complete für Entscheidungen.  
> Don’t: mischen von technischen Feldern (Columns) mit KPIs.

---

## 4. Business Logic & Thresholds
Describe the rules used to evaluate performance and trigger actions.

- <Logic: e.g. Revenue Growth % < 0 for 2 consecutive months = critical trend>  
- <Thresholds: e.g. GM % < 25 % in core channel = margin issue>  
- <Exceptions: e.g. exclude new markets < 6 months>

**Trigger Logic (formal, for automation):**

```text
WHEN <KPI> <operator> <threshold>
AND  <optional condition>
THEN propose Action Code <X>
```

---

## 5. Action Codes
List all Action Codes relevant for this use case.

| Code | Name | Trigger (formal, using KPIs) | Description (business action) | Expected KPI Impact |
|------|------|------------------------------|-------------------------------|----------------------|
| <X1> | <Name> | <rule from section 4> | <what is done> | <+%, −%, stabilise, etc.> |
| <X2> | … | … | … | … |

> Do: refer to the global Action Code catalog.  
> Don’t: erfinden abweichende Namen für bestehende Codes.

---

## 6. 3–30–300 Page Layout (Apple-style UX)

### 6.1 3-Second Layer (KPI Cards – mandatory)
Choose 4–5 core KPIs as cards.

- <KPI Card 1>  
- <KPI Card 2>  
- <KPI Card 3>  
- <KPI Card 4>  
- <optional 5>  

### 6.2 30-Second Layer (Main Visuals – mandatory table)
Define the core visuals, including fields and axes.

| Visual Name | Visual Type | X-Axis / Category | Y-Axis / Value | Segment / Legend | Filters / Defaults |
|-------------|-------------|-------------------|-----------------|------------------|--------------------|
| <Sales Trend> | Line | Date[Month] | [Net Sales Amount] | Region | Last 12–24 months |
| <Margin Ranking> | Bar (horizontal) | Org[Channel] | [Gross Margin %] | Region | Top/Bottom N |
| … | … | … | … | … | … |

### 6.3 300-Second Layer (Diagnostics & Detail)
Describe deeper analysis and export needs.

- Detail Matrix (dimensions, KPIs, drill path)  
- Typical drilldown flows (e.g. Region → Country → Customer)  
- Export views for Controlling / Sales / Ops  

---

## 7. Dependencies, Assumptions & Constraints
- **Data Dependencies:** required domains, tables, fields.  
- **Business Assumptions:** e.g. “Plan values are frozen after month-end”.  
- **Constraints:** e.g. data latency, missing dimensions, estimation logic.

---

## 8. Success Criteria
Define measurable outcomes and adoption.

- <Impact on KPIs, e.g. “reduce negative-margin promotions by 30 % in 6 months”>  
- <Adoption: e.g. “used in monthly steering for segment X”>  
- <Quality: e.g. “no conflicting KPI definitions across domains”>  

