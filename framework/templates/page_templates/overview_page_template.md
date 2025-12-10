# Overview Page Template (3–30–300)

Purpose:
Deliver the fastest “what/so-what/now-what” storyline for an executive audience with zero setup friction.

Layout (3–30–300):
- 3-second layer: 4–5 KPI cards (sparkline + vs Plan/LY + status chip + action hint).
- 30-second layer: 3–4 visuals telling the core narrative (trend, variance bridge, contribution, segment split).
- 300-second layer: link-out to Insights/Explorer for diagnostics; no heavy tables here.

Visual patterns:
- KPI cards: Title, KPI value, delta vs Plan/LY, status chip (↑/→/↓), action code badge.
- Trend visual: Line/column combo, x-axis = month, y-axis = KPI, segment = region/channel optional.
- Variance bridge: Waterfall for Plan→Actual with effects (price/volume/mix, rate/volume).
- Contribution: Stacked column or 100% bar for top segments (product/customer/channel).
- No raw tables; only compact lists for “Top/Worst 5 drivers” if needed.

Slicers:
- Always: Date (month), Org/Region.
- Domain slicer: e.g., Customer/Channel/Product/Asset depending on UC.
- Keep slicers pinned; max 3; default to “All” with clearly visible current selection.

Tooltips:
- Standard tooltip template: KPI value, delta vs Plan/LY, segment, action code hint if threshold breached.

Design system:
- Grid: 12-column; reserve top row for KPI cards.
- Colors: Neutral base; green for positive, red for negative (domain-aware if inverted KPI).
- Typography: Heading for page title, strong labels for KPI names, no decorative fonts.
- Legends on the right; avoid redundant labels; keep y-axis zero-based unless % change.

Build rules:
- Every visual ties to a KPI ID and a measure from the catalog.
- No bi-directional relationships; slicers must come from conformed dims.
- Default filters: current FYTD, last 12–24 months for trends.
- Performance: limit visuals; prefer Import/DirectLake optimized measures.
