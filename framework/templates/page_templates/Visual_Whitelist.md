# Visual Whitelist – 3–30–300 Templates

Purpose:
Define the allowed Power BI visuals for the ActionReady page templates (overview/insights/explorer) and how they should be used. Keep the palette small, predictable, and automation-friendly.

Scope:
- Applies to all template pages (3–30–300) and all use cases.
- Slot → visual mapping is defined in `PageTemplate_SlotVisual_Map.md`.
- Whitelist must be respected by manual design, PBIP/TMDL automation, and AI/Copilot generation.

Allowed visuals (core):

| Visual type | Internal name | Typical use |
| --- | --- | --- |
| Card | `card` / `cardVisual` | KPI tiles (3s layer) |
| Line chart | `lineChart` | Time trends (12–24 periods) |
| Clustered bar chart | `clusteredBarChart` | Rankings, Top/Bottom |
| Clustered column chart | `clusteredColumnChart` | Operational trends |
| 100% stacked bar/column | `hundredPercentStackedBarChart` / `hundredPercentStackedColumnChart` | Mix / share-of |
| Waterfall | `waterfallChart` | Variance bridges |
| Scatter (insights only) | `scatterChart` | Driver relationships (limited use) |
| Table / matrix | `tableEx` | Exception lists, detail tables |
| Pivot | `pivotTable` | Hierarchical drill (300s layer) |
| Slicer | `slicer` / `listSlicer` / `advancedSlicerVisual` | Filters (max 3–5 per page) |

Not allowed:
- Funnel, gauge, pie/donut, treemap, ribbon, key influencers, decomposition tree (unless explicitly approved), and any non-whitelisted custom visuals.

Usage rules:
- One purpose per visual; no overloaded visuals.
- Waterfall: 3–7 steps; clear labels (Plan, FX, Price, Volume, Mix, Other, Actual).
- Line/column: 1–2 measures; 12–24 periods; clear axis labels; no area charts.
- Bars: horizontal for rankings; limit to Top/Bottom 5–10; sort by value.
- Mix: 100% stacked; max 6 categories; always sorted.
- Tables: light conditional formatting; highlight L1–L3 thresholds; avoid dense formatting.
- Slicers: Date + Org mandatory; one domain slicer (e.g., Product/Customer/Asset); optional Scenario; keep ≤5.
- Tooltips: standard tooltip fields (KPI value, Δ vs Plan/LY, segment, action hint if threshold hit).

Design system:
- Grid: 12-column; consistent gutters; avoid overlap.
- Colors: neutral base; green positive, red negative (domain-aware); minimal accent colors.
- Typography: clean sans-serif; strong labels for KPI names; no decorative fonts.
- Accessibility: maintain contrast; avoid tiny fonts; ensure slicers are keyboard-focusable.

Governance:
- Only measures from the catalog; no ad-hoc calculations inside visuals.
- Slicers must use conformed dimensions; no bi-directional relationships.
- Any deviation must be marked as draft and reviewed before release.
