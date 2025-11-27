# Page Template – Slot to Visual Mapping

This document defines which Power BI visuals are used for each page slot in the Aurora Template Factory.  
It is the reference for report designers, automation scripts (PBIP/TMDL), and AI agents.

- Scope: Core templates T1–T4, all use cases in `UseCase_PageTemplate_Map_3-30-300.yaml`.
- Basis: Visual whitelist, 3-30-300 concept, Apple/iOS design principles.

> Note: Only visuals from the official Visual Whitelist are allowed.  
> Detailed list: see `Visual_Whitelist.md`.

---

## 1. Slot to Visual Mapping (Global)

The table below defines the primary visual for each slot and, where useful, an allowed alternative.

| Slot                | Primary visual                 | Alternative visual         | Usage notes                                                                 |
|---------------------|--------------------------------|----------------------------|------------------------------------------------------------------------------|
| `needs_trend`       | `lineChart`                   | `clusteredColumnChart`     | Time axis (Date) on X, 1–2 measures, 12–24 periods max. No area charts.     |
| `needs_variance`    | `waterfallChart`              | –                          | 3–7 steps, clear labels (Plan, FX, Price, Volume, Mix, Other, Actual).      |
| `needs_ranking`     | `clusteredBarChart`           | –                          | Horizontal bar, Top/Bottom 5–10, single measure per visual.                 |
| `needs_mix`         | `hundredPercentStackedBarChart` | –                        | Max 6 categories, always sorted, used for share-of and mix analyses.        |
| `needs_exceptions`  | `tableEx`                     | –                          | Conditional formatting for L1–L3 thresholds, sort by severity first.        |
| `needs_detail_matrix` | `tableEx` / `pivotTable`    | –                          | Main 300s layer. Hierarchies, drill, export. No heavy formatting.           |
| `needs_root_cause`  | `tableEx` + `clusteredBarChart` | –                        | Combination: matrix for breakdown + focused ranking on key driver.          |
| `needs_funnel`      | `tableEx` + `lineChart`       | –                          | No funnel visual. Use stage table + trend of key conversion metric.         |
| `needs_prescriptive`| `tableEx`                     | `scatterChart`             | Table for recommended actions; scatter only for T4 driver/relationship view.|

All other slot-specific behavior (tooltips, reference lines, conditional formatting) is defined in the page templates (T1–T4) and follows the same mapping.

---

## 2. Layer-Specific Guidance (3-30-300)

Slots are used differently across the 3-30-300 layers:

### 2.1 Overview layer (3 + 30 seconds)

- Pages: `layer: [3, 30]` in `UseCase_PageTemplate_Map_3-30-300.yaml`
- Goal: fast understanding of status and main drivers.
- Recommended slot usage:
  - `needs_trend`: active where time evolution matters (trend line or daily/weekly columns).
  - `needs_variance`: active for gap-/bridge-focused use cases (waterfall).
  - `needs_ranking`: almost always active (Top/Bottom bar).
  - `needs_mix`: only if mix or share-of is part of the core question.
  - `needs_exceptions`: only small, focused lists (Top N issues), not full incident logs.
  - `needs_detail_matrix`: disabled on overview pages (matrix belongs to 300s).

Visual density rule:
- Max 4 data visuals (excluding slicers, cards, textboxes).
- Max 3 slicers.

### 2.2 Detail layer (300 seconds)

- Pages: `layer: [300]` in `UseCase_PageTemplate_Map_3-30-300.yaml`
- Goal: drill into details, export, and root-cause analysis.
- Recommended slot usage:
  - `needs_detail_matrix`: always `true`, main visual (tableEx/pivotTable).
  - `needs_exceptions`: extended exception lists, including filters for severity, region, product, etc.
  - `needs_root_cause`: optional, as additional matrix + ranking combo.
  - `needs_ranking`: can stay active for segmented breakdowns.
  - `needs_trend`, `needs_variance`, `needs_mix`, `needs_funnel`: normally `false` on detail-only pages to avoid clutter.

---

## 3. Template-Specific Notes (T1–T4)

The same slots behave slightly differently per template type:

### 3.1 T1 – Strategic View

- Typical layers:
  - `overview` → [3, 30]
  - `detail` → [300] (optional)
- Slot emphasis:
  - Strong focus on `needs_trend` and `needs_ranking`.
  - `needs_variance` optional (only for high-level bridges).
  - `needs_detail_matrix` usually only on a separate detail page.
- Visual pattern overview:
  - Top: card visuals (3–5 KPIs).
  - Middle: `lineChart` + `clusteredBarChart`.
  - Bottom (optional): small matrix.

### 3.2 T2 – Tactical Variance View

- Typical layers:
  - `overview` → [3, 30] with strong variance focus.
  - `detail` → [300] with matrix + exceptions.
- Slot emphasis:
  - `needs_variance` + `needs_ranking` meist aktiv.
  - `needs_mix` aktiv für share-of / mix KPIs.
  - `needs_exceptions` nur wenn Ausreißer relevant.
- Visual pattern overview:
  - Top: KPI cards.
  - Middle: `waterfallChart` (Plan/Forecast vs Actual).
  - Right/Bottom: `clusteredBarChart` (Top/Bottom dimensions).

### 3.3 T3 – Operational Exception View

- Typical layers:
  - `overview` → [3, 30] mit Fokus auf heutige/aktuelle Probleme.
  - `detail` → [300] mit vollständiger Exception-Matrix.
- Slot emphasis:
  - `needs_trend`: kurz, aber meist aktiv (last 7–30 days).
  - `needs_exceptions`: klar aktiv.
  - `needs_root_cause`: optional, falls Use Case es fordert.
- Visual pattern overview:
  - Top: KPIs (today vs target).
  - Middle: daily `clusteredColumnChart` + exception list.
  - Detail: full incident matrix.

### 3.4 T4 – Prescriptive / Next-Best-Action View

- Typical layers:
  - `overview` → [3, 30] with KPIs and high-level explanation of model outputs.
  - `detail` → [300] with recommended actions table and optional driver views.
- Slot emphasis:
  - `needs_prescriptive`: always `true`.
  - `needs_ranking`: ranking of recommendations or entities.
  - `needs_trend` optional, `needs_variance` rarely needed.
- Visual pattern:
  - Overview: cards, short trend, ranking of entities by opportunity.
  - Detail: `tableEx` for recommendations + optional `scatterChart` for driver relationships.

---

## 4. Implementation Notes

1. The actual slot configuration per use case and page is defined in  
   `UseCase_PageTemplate_Map_3-30-300.yaml`.
2. This document defines only **which visual type** is used when a slot is `true`.
3. Visual styling (theme, colors, fonts) is provided by the custom Power BI theme:
   - cards, charts, tables, slicers styled centrally
   - no local overrides unless strictly necessary.
4. New slots must be:
   - added to `UseCase_PageTemplate_Map_3-30-300.yaml`,
   - mapped in this file,
   - and aligned with the Visual Whitelist.

---

## 5. Maintenance

- Owner: Template Factory / BI Design Lead.
- Update rules:
  - Only extend slots if a new analytic pattern cannot be expressed with existing ones.
  - Avoid introducing new visual types outside of the Visual Whitelist.
  - Review this mapping when:
    - new T-templates are added, or
    - new Action Code patterns require different visual treatment.

This mapping is the single source of truth for slot-to-visual choices in all Aurora Group template-based reports.
