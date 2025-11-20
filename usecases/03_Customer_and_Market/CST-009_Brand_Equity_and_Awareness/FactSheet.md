---
id: "CST-009"
title: "Brand Equity & Awareness"
domain: "Customer and Market"
owner: "Head of Brand / Marketing"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Strategic"
analytics_stage: "Descriptive"
supports_strategic_kpi: ["Brand Awareness %", "Net Promoter Score (NPS)"]
supports_strategic_kpi_ids: ["mkt.brand.awareness.pct", "crm.nps.index"]
action_codes: ["SP1", "M3", "D2"]
expected_impact: "Higher brand awareness and preference in target segments; stronger funnel performance."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Market.Region>Country",
  "Customer.Segment",
  "Channel",
  "Time.Year>Quarter"
]
filters_default: [
  "Time: Last 8Q",
  "Region: All",
  "Segment: All"
]
qa_asserts: ["RI_OK", "Survey_Base_Sufficient", "Brand_Metrics_Consistent"]
required_kpi_ids: [
  "mkt.brand.awareness.pct",
  "mkt.brand.preference.pct",
  "crm.nps.index"
]
required_kpis:
  mkt.brand.awareness.pct: "Brand Awareness %"
  mkt.brand.preference.pct: "Brand Preference %"
  crm.nps.index: "Net Promoter Score (NPS)"
data_requirements:
  facts:
    - name: fact_brand_survey
      grain: respondent
      primary_key: [RespondentID]
      required_columns:
        - { name: RespondentID, type: string, role: attribute }
        - { name: Date, type: date, role: date_key }
        - { name: Region, type: string, role: attribute }
        - { name: Country, type: string, role: attribute }
        - { name: Segment, type: string, role: attribute }
        - { name: "Brand Awareness Flag", type: bool, role: indicator }
        - { name: "Brand Preference Flag", type: bool, role: indicator }
        - { name: "NPS Score", type: int, role: attribute }
  dims:
    - name: dim_date
      grain: date
      primary_key: [Date]
      required_columns:
        - { name: Year, type: int }
        - { name: Quarter, type: int }
model_mapping:
  "Brand Awareness Flag": "fact_brand_survey[Brand Awareness Flag]"
  "Brand Preference Flag": "fact_brand_survey[Brand Preference Flag]"
  "NPS Score": "fact_brand_survey[NPS Score]"
  "Region": "fact_brand_survey[Region]"
  "Segment": "fact_brand_survey[Segment]"
  "Date": "dim_date[Date]"
---

# Brand Equity & Awareness

## 1. Business Goal
Track and improve brand awareness, preference, and advocacy over time and across key markets and segments.

---

## 2. Business Context
Brand equity metrics such as awareness and preference are leading indicators of future demand.  
They are often measured in separate survey tools without being linked to customer segments, channels, or actual performance.  
This Use Case standardizes core brand metrics and makes them visible alongside NPS and commercial outcomes.

---

## 3. Key Questions
- What is our brand awareness and preference in key markets and segments?
- How do awareness, preference, and NPS evolve over time?
- Which campaigns or initiatives correlate with improvements in brand metrics?
- Where are we underperforming vs competitors (if benchmark data is available)?

---

## 4. Key KPIs
| KPI               | Definition                                    | Unit | Format   |
|-------------------|-----------------------------------------------|------|----------|
| Brand Awareness % | Respondents aware of brand / total respondents| %    | 1 decimal |
| Brand Preference %| Respondents preferring brand / total respondents| %  | 1 decimal |
| NPS               | Net Promoter Score                            | Index| 0 decimals|

---

## 5. Required Attributes (Business-Level)
- Respondent ID, Date
- Region, Country, Segment
- Awareness flag, preference flag
- NPS Score

---

## 6. Segmentation & Hierarchies
- Market: Region > Country  
- Customer: Segment  
- Time: Year > Quarter  

---

## 7. Scope & Assumptions
- Surveys are representative for the target segments and markets.
- NPS is calculated according to standard methodology (0–10 scale).

---

## 8. Data Freshness & Cadence
- Survey waves: quarterly or semi-annually.
- Reporting cadence: after each wave; trending over multiple waves.

---

## 9. Edge Cases & QA Rules
- Minimum base size per segment (e.g., ≥ 100 respondents) before displaying metrics.
- Outlier responses or inconsistent survey versions are flagged.

---

## 10. Minimum Viable Dataset (MVD)
- Required:
  - Survey fact with awareness, preference, NPS per respondent.

---

## 11. Typical Actions
| Action                                | Code | Expected Effect             |
|---------------------------------------|------|-----------------------------|
| Focus campaigns on low-awareness segments | SP1 | Higher awareness and preference |
| Improve experience in low-NPS segments| M3   | Higher NPS, better advocacy |
| Align messaging with brand positioning| D2   | Stronger brand perception   |

---

## 12. Expected Business Impact
| Dimension | Expected Impact          | Measurement |
|-----------|--------------------------|-------------|
| Brand     | +5–10 pp awareness/preference | vs prior wave |
| Customer  | +3–5 pts NPS            | vs prior wave |

---

## 13. Related Processes
Brand Strategy → Campaign Planning → Brand Tracking → Portfolio & Channel Strategy.

---

## 14. Insights & Learnings
Typical findings include strong awareness but low preference in some segments, and clear links between service quality and NPS.

---

## 15. Cross-References
- Related Use Cases:  
  `[CST-005 NPS Analysis](../CST-005_NPS_Analysis/FactSheet.md)`  
  `[CST-006 Market Share & Competitive Position](../CST-006_Market_Share_and_Competitive_Position/FactSheet.md)`  

---

## 16. Review Information
| Field              | Value          |
|--------------------|----------------|
| Business Reviewer  | [Name / Role]  |
| Technical Reviewer | [Name / Role]  |
| Version            | v0.1           |
| Review Date        | DD.MM.YYYY     |
| Review Notes       | [Summary]      |

---

_Last updated: 19.11.2025_

