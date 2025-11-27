# Visual Whitelist – Aurora Template Factory

This document defines which Power BI visuals are allowed in the Aurora Template Factory and how they should be used across templates T1–T4.

Goals:
- Enforce a modern, minimal, Apple-like UI.
- Align all pages with the 3-30-300 concept.
- Keep the visual palette small, predictable, and automation-friendly.

---

## 1. Scope

- Applies to all report pages generated from the Template Factory (T1–T4).
- Applies to all use cases listed in `UseCase_Inventory.md`.
- Slot → Visual mapping is defined in `PageTemplate_SlotVisual_Map.md`.
- This whitelist must be respected by:
  - manual report design,
  - PBIP/TMDL automation,
  - and AI/Copilot-based generation.

---

## 2. Allowed Visuals (Core)

These visuals are allowed as **data visuals** in template pages.

| Visual type                    | Internal name                    | Typical use                                |
|--------------------------------|----------------------------------|--------------------------------------------|
| Card                           | `card` / `cardVisual`           | KPI tiles (3s layer)                       |
| Line chart                     | `lineChart`                     | Time trends (12–24 periods)                |
| Clustered bar chart            | `clusteredBarChart`             | Rankings, Top/Bottom                       |
| Clustered column chart         | `clusteredColumnChart`          | Daily/weekly operational trends            |
| 100% stacked bar chart         | `hundredPercentStackedBarChart` | Mix / share-of analyses                    |
| 100% stacked column chart      | `hundredPercentStackedColumnChart` | Vertical share-of (only if needed)     |
| Waterfall chart                | `waterfallChart`                | Variance bridges (Plan/Forecast vs Actual) |
| Scatter chart (T4 only)        | `scatterChart`                  | Driver relationships, T4 only              |
| Table / matrix                 | `tableEx`                       | Detail tables, exception lists             |
| Matrix / pivot                 | `pivotTable`                    | Hierarchical drill (300s layer)            |
| Slicer                         | `slicer` / `listSlicer` / `advancedSlicerVisual` | Filters (max 3 per page)       |
| Textbox                        | `textbox`                       | Titles, subtitles, annotations             |

Rules:
- No other data visuals are allowed unless explicitly added to this whitelist.
- For each slot, use the corresponding primary visual from `PageTemplate_SlotVisual_Map.md`.

---

## 3. Allowed Visuals (UI Controls – not counted as data visuals)

These elements are allowed as **UI controls**, not as analytical visuals:

| Element            | Internal name        | Purpose                                  |
|--------------------|----------------------|------------------------------------------|
| Shape              | `shape`              | Simple separators, lines, containers     |
| Page navigator     | `pageNavigator`      | Navigation across pages                  |
| Bookmark navigator | `bookmarkNavigator`  | State switching, simple scenarios        |
| Action button      | `actionButton`       | Links to details, external systems, etc. |
| Page               | `page`               | Layout container                         |

Rules:
- These elements should not be used to encode quantitative information.
- Use them to guide navigation and focus, not to decorate.

---

## 4. Blocked Visuals (Not Allowed)

The following visuals are **not allowed** in template-based reports, even if available in Power BI or in the theme:

| Visual type               | Reason (short)                                               |
|---------------------------|--------------------------------------------------------------|
| Area chart                | Low information density, overplotting, unclear baselines     |
| Pie chart                 | Hard to compare angles, low precision                        |
| Donut chart               | Same issues as pie, center wastes space                      |
| Funnel chart              | Misleading, hard to read, better done as table + line        |
| Gauge / KPI gauge         | Very low data-ink ratio, hard to compare multiple units      |
| Decomposition tree        | Over-complex, breaks 3-30-300, heavy interaction required    |
| Ribbon chart              | Hard to read, unstable perception                            |
| Map / filled map          | Only useful for true geo-analytics (not in current scope)    |
| Treemap                   | Difficult comparison, poor readability                       |
| Custom visuals (generic)  | Not governed by theme, unpredictable UX/performance          |

Rationale:
- All blocked visuals either:
  - reduce readability,
  - break 3-30-300,
  - or tend to be misused as “eye candy” without real value.

If a future use case requires one of these, it must go through a design review and this document must be explicitly updated.

---

## 5. Usage Rules per Page

To keep pages clean and aligned with 3-30-300:

1. **Max visuals per page**
   - Max. 4 data visuals (cards, charts, tables).
   - Max. 3 slicers.
   - UI controls (buttons, navigators) are allowed but should be minimal.

2. **Layer-specific**
   - 3s / 30s pages (overview):
     - Focus on KPIs, one trend, one variance, one ranking.
     - No large detail tables.
   - 300s pages (detail):
     - Focus on matrix/table and exceptions.
     - No redundant trend/variance charts.

3. **Consistency**
   - For a given slot (e.g. `needs_trend`) always use the same visual type.
   - Avoid mixing visual types for the same analytic pattern.

---

## 6. Relation to Other Artifacts

- Slot → Visual logic:  
  `docs/templates/PageTemplate_SlotVisual_Map.md`
- Use case → pages → slots:  
  `usecases/UseCase_PageTemplate_Map_3-30-300.yaml`
- Action Codes (if active in pages):  
  `ActionCodes.md` and (planned) `UseCase_ActionCode_Map.yaml`

---

## 7. Maintenance

- Owner: BI Design Lead / Template Factory Maintainer.
- Updates:
  - Only extend the whitelist when a new analytic pattern cannot be covered with existing visuals.
  - Any new visual type must:
    - be added here,
    - be integrated into `PageTemplate_SlotVisual_Map.md`,
    - respect the 3-30-300 rules and the Aurora theme.

This whitelist is the single source of truth for which visuals are allowed in Aurora Group template-based reports.
