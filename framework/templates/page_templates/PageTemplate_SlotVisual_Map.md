# Page Template – Slot to Visual Mapping

Purpose:
Define the primary visual type for each slot across the 3–30–300 templates to keep layouts consistent and automation-friendly.

Scope:
- Applies to overview, insights, and explorer pages.
- Must align with the visual whitelist and page templates.

Global slot mapping:

| Slot key | Primary visual | Alternative | Usage notes |
| --- | --- | --- | --- |
| needs_trend | lineChart | clusteredColumnChart | Time axis on X; 1–2 measures; 12–24 periods max |
| needs_variance | waterfallChart | – | 3–7 steps, labeled (Plan, FX, Price, Volume, Mix, Other, Actual) |
| needs_ranking | clusteredBarChart | – | Horizontal bars; Top/Bottom 5–10; single measure |
| needs_mix | hundredPercentStackedBarChart | hundredPercentStackedColumnChart | Max 6 categories; sorted; share-of analysis |
| needs_exceptions | tableEx | – | Conditional formatting for L1–L3 thresholds; sort by severity |
| needs_detail_matrix | tableEx / pivotTable | – | 300s layer; hierarchies, drill, export-friendly |
| needs_root_cause | tableEx + clusteredBarChart | — | Matrix for breakdown + focused ranking on key driver |
| needs_funnel | tableEx + lineChart | — | Stage table + trend of key conversion metric; no funnel visual |
| needs_prescriptive | tableEx | scatterChart (T4 only) | Table for recommended actions; scatter only for driver view |

Layer-specific guidance (3–30–300):
- Overview (3s + 30s): KPI cards + trend/variance/mix visuals; no heavy tables.
- Insights (30s): variance decomposition, drivers, cohorts, outliers; limited tables.
- Explorer (300s): pivot/table first, then optional ranking/small multiples; keep slicers tight.

Tooltip and formatting rules:
- Use standard tooltip fields: KPI value, Δ vs Plan/LY, segment, action hint when thresholds hit.
- Use domain color rules (green positive, red negative; invert where applicable).
- Keep axes labeled; avoid clutter; no pie/donut/funnel visuals.

### XD-003 Executive KPI Overview

**T1 Strategic Overview**
- Slot 1: KPI Card – Net Sales Growth %
- Slot 2: KPI Card – Gross Margin %
- Slot 3: KPI Card – Customer Lifetime Value
- Slot 4: KPI Card – Service Level %
- Slot 5: KPI Card – OTIF %
- Slot 6: KPI Card – CCC Days
- Slot 7: KPI Card – Digital Adoption %
- Slot 8: KPI Card – Attrition Risk %

**T2 Tactical Variance**
- Slot A: Trend Chart (12–24M)
- Slot B: Driver Variance Bar Chart
- Slot C: Domain Navigation Panel
- Slot D: Action Code Recommendation Panel
