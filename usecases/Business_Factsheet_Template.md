# <UC-ID> – Business Factsheet

## 1. Summary
- **Business Goal:** <Why does this use case matter?>
- **Target Audience:** <Executive / Sales / Operations / Finance>
- **Business Priority:** <High / Medium / Low>
- **Expected Impact:** <Value levers, expected effect on KPIs>

## 2. Core Questions
List the core business questions this use case answers.
- Question 1
- Question 2
- Question 3
(Keep questions non-technical and decision-oriented.)

## 3. KPI Set (Business View)
Describe KPIs in business language. No formulas, no DAX.

| KPI Name | Purpose | Business Definition | Interpretation | Decision Relevance |
|----------|----------|---------------------|----------------|---------------------|
| Net Sales Amount | Why is this KPI relevant? | Business definition, not technical. | Meaning of ↑ / ↓ | How does it influence decisions? |
| Gross Margin % | … | … | … | … |

## 4. Business Logic & Thresholds
Describe the logic behind “good / neutral / bad” states.
Examples:
- “Gross Margin % < 35 % for 3+ periods indicates price leakage.”
- “Revenue Growth % negative for 2 periods triggers action.”

Keep only thresholds relevant for decision-making.

## 5. Action Codes (Business Perspective)
Describe applicable action codes for this use case.

| Code | Name | Business Description | Typical Trigger | Expected Effect |
|------|------|-----------------------|-----------------|------------------|
| P2 | Price Adjustment | … | e.g. GM% drop + higher discounts | e.g. +1–2 pp GM% |
| D1 | Demand Boost | … | … | … |

(Technical trigger logic goes into the Technical Factsheet.)

## 6. 3–30–300 Page Layout
Describe how this use case should be visualized on a single page.

### 6.1 3-Second Layer (Insight)
- 4–5 KPI cards
- Which KPI + Δ vs Plan/LY?
- What should the user understand instantly?

### 6.2 30-Second Layer (Story)
Define the core visuals and what they answer:
- **Line (12–24M):** KPI trend
- **Waterfall:** Variance drivers
- **Bar Chart:** Top/Bottom segments

### 6.3 300-Second Layer (Detail)
Define diagnostics:
- Matrix: segment x product
- Detailed KPIs
- Drill paths
- Export table

## 7. Dependencies & Constraints
List non-technical dependencies:
- Required business processes
- Required data availability or frequency
- Known limitations

## 8. Success Criteria
How do we measure success?
- Leading indicators (usage, adoption)
- Lagging indicators (KPI improvements)
