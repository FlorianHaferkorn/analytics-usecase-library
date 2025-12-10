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
| needs_root_cause | tableEx + clusteredBarChart | – | Matrix for breakdown + focused ranking on key driver |
| needs_funnel | tableEx + lineChart | – | Stage table + trend of key conversion metric; no funnel visual |
| needs_prescriptive | tableEx | scatterChart (T4 only) | Table for recommended actions; scatter only for driver view |

Layer-specific guidance (3–30–300):
- Overview (3s + 30s): KPI cards + trend/variance/mix visuals; no heavy tables.
- Insights (30s): variance decomposition, drivers, cohorts, outliers; limited tables.
- Explorer (300s): pivot/table first, then optional ranking/small multiples; keep slicers tight.

Tooltip and formatting rules:
- Use standard tooltip fields: KPI value, Δ vs Plan/LY, segment, action hint when thresholds hit.
- Use domain color rules (green positive, red negative; invert where applicable).
- Keep axes labeled; avoid clutter; no pie/donut/funnel visuals.
