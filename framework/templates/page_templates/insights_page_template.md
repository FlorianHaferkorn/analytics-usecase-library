# Insights Page Template (30-second diagnostic)

Purpose:
Provide guided root-cause and “so-what” diagnostics immediately after the overview page.

Layout (3–30–300):
- 3-second anchor: miniature KPI cards repeating the overview state for continuity.
- 30-second body: 3–4 diagnostic visuals sequenced as storyline.
- 300-second hooks: links to Explorer tabs filtered to the selected segment.

Visual patterns:
- Variance decomposition: Waterfall (Plan→Actual or LY→TY) with effects (price, volume, mix, rate, FX, cost buckets).
- Correlation/driver view: Scatter or column+line to show KPI vs driver with segmentation (e.g., churn vs NPS).
- Cohort/segment deep dive: Small multiples by top 6 segments (region/channel/product/customer tier).
- Outlier table: Top/Worst 10 list with KPI, delta, contribution %, action flag.

Slicers:
- Carry-over from overview (Date, Org/Region, domain dim).
- Add scenario selector if relevant (Actual/Plan/Forecast).
- Keep slicer count ≤4; defaults documented in the page header.

Tooltips:
- Standard tooltip + driver context: KPI value, driver metric, delta vs Plan/LY, action hint when thresholds hit.

Design system:
- Grid: 12-column; prioritize left-to-right reading flow; keep white space around key visuals.
- Colors: Consistent with overview; same status chips for KPI state.
- Typography: Section headers per diagnostic; concise subtitles explaining the question answered.

Build rules:
- All visuals reference KPI IDs and measure names from the catalog.
- No custom calculations in visuals; measures live in the semantic model.
- Drillthrough targets defined for segments used in visuals.
- Performance: avoid >5000-row tables; pre-aggregate where possible.
