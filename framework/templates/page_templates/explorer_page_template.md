# Explorer Page Template (300-second drill)

Purpose:
Enable controlled self-service exploration without breaking the governed KPI/measure system.

Layout (3–30–300):
- Header: recap of selected KPI and filters.
- Body: 2–3 exploration zones (table/pivot, visual switcher, small multiples).
- Footer: reset filters + navigation back to Insights/Overview.

Visual patterns:
- Pivot/table: KPI + key supporting drivers; sortable; conditional formatting for exceptions.
- Visual switcher: user can toggle between line/column/stacked bar for the same field set.
- Small multiples: show KPI across top 6 segments to spot distribution patterns.
- Optional decomposition tree only if performance is acceptable and logic aligns with measures.

Slicers:
- Always: Date (month), Org/Region.
- Domain slicers: Customer/Product/Channel/Asset as appropriate.
- Scenario slicer (Actual/Plan/Forecast) when applicable.
- Provide “Reset to default” button; limit to ≤5 slicers visible.

Tooltips:
- Same standard tooltip; include filter breadcrumb and Action Code hint when thresholds are crossed.

Design system:
- Grid: flexible but keep gutters; no overlapping visuals.
- Colors and typography inherit from overview/insights; keep neutral table styling with sparing conditional formatting.
- Accessibility: ensure contrast, legible fonts, keyboard focus for slicers.

Build rules:
- No ad-hoc measures in visuals; only governed measures.
- Avoid bi-directional relationships; slicers must come from conformed dimensions.
- Row limits: paginate or incremental load for large tables; consider DirectLake/Import hybrid.
- Audit: log bookmark/save states only if compliant with governance.
