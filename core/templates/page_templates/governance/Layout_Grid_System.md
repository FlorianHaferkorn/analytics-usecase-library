# Layout Grid System — Framework Governance
#
# Authority:   This file is the canonical source for all visual positioning,
# spacing, and grid calculations across ALUCA (Analytics Library of Use Cases).
#
# Implements:  Design_Spec_3_30_300.md §3 (Canvas & Grid)
# Aligns with: Storytelling_Principles.md §11 (White Space)
#
# Rule: Values in this file supersede pixel values stated anywhere else.
# All slot coordinates use the 1280×720 design-base canvas.
# Connectors translate to their native canvas via the LU formulae below.

---

## Canvas Standards

| Mode             | Width  | Height | Aspect Ratio | Purpose                                           |
|------------------|--------|--------|--------------|---------------------------------------------------|
| Design base      | 1280px | 720px  | 16:9         | Reference for all slot coordinates in this file   |
| Production (PBI) | 1920px | 1080px | 16:9         | Default for deployed Fabric/Power BI reports      |
| Export / PDF     | 1920px | 1080px | 16:9         | +2pt font compensation required per connector     |
| Web / fluid      | —      | —      | viewport     | Use rem/clamp; defined per connector spec         |

Rule: Scaffold generators read canvas from UseCase_Bracket.yaml → report_canvas.
      When unset, default is 1280×720 (design base).

---

## Master Grid Parameters (Canonical)

| Parameter        | Value | Description                                              |
|------------------|-------|----------------------------------------------------------|
| Grid             | 12×12 | Columns × rows, logical units (LU)                      |
| Outer margin     | 32px  | Safety gap from all canvas edges                        |
| Gutter           | 16px  | Gap between visuals within the same zone                |
| Internal padding | 8px   | Padding inside visual containers (cards, panels)        |
| Zone gap         | 40px  | Gap between zone groups (overrides gutter between zones)|

Spacing hierarchy:
  Zone gap (40px) > Gutter (16px) > Internal padding (8px)

- Between visuals in the same zone  →  16px  (gutter)
- Between different zone groups     →  40px  (zone gap)
- Inside a card or panel container  →   8px  (internal padding)
- Canvas edge to first visual       →  32px  (outer margin)

Source authority: Storytelling_Principles.md §11

---

## Grid Formulae

For any canvas (W × H):

  content_width   = W − 2 × outer_margin
  content_height  = H − 2 × outer_margin
  lu_width        = (content_width  − 11 × gutter) / 12
  lu_height       = (content_height − 11 × gutter) / 12

  slot(col_start, row_start, col_span, row_span):
    x      = outer_margin + col_start × (lu_width  + gutter)
    y      = outer_margin + row_start × (lu_height + gutter)
    width  = col_span  × lu_width  + (col_span  − 1) × gutter
    height = row_span  × lu_height + (row_span  − 1) × gutter

Computed values at 1280×720 design base:
  content_width   = 1216px
  content_height  =  656px
  lu_width        ≈  86.67px  (1040 / 12)
  lu_height       =  40px     (480  / 12)
  col_step        ≈ 102.67px  (lu_width  + gutter)
  row_step        =  56px     (lu_height + gutter)

Implementation: products/fabric/powerbi/tooling/page_scaffold_generator/grid_calculator.py

---

## Zone System

Zones map to LU rows. Zone gap (40px) is achieved by leaving an empty LU row between zones
OR by applying explicit offset in the scaffold generator.

| Zone   | LU Rows | Purpose                                      | Reading Pattern |
|--------|---------|----------------------------------------------|-----------------|
| Zone 1 | 0–1     | 3-second layer: KPI band (no slicers)        | Both            |
| Zone 2 | 2       | 30-second filter: slicer bar (top placement) | Z-pattern pages |
| Zone 3 | 3–8     | 30-second drivers: trend, variance, ranking  | Both            |
| Zone 4 | 0–11    | 300-second detail: full-page (detail pages)  | F-pattern pages |

Zone 4 occupies the full grid of the Detail page — it does not share a page with Zones 1–3.

---

## Named Slot Coordinates

All coordinates at 1280×720 design base. Connectors scale proportionally.

### Overview Page (Z-pattern — T1, T2, T3 overview)

| Slot ID       | col | row | col_span | row_span | x (px) | y (px) | w (px) | h (px) |
|---------------|-----|-----|----------|----------|--------|--------|--------|--------|
| KPI_Cards     |   0 |   0 |       12 |        2 |     32 |     32 |   1216 |     96 |
| Slicer_Date   |   0 |   2 |       12 |        1 |     32 |    144 |   1216 |     40 |
| Main_1 (Trend)|   0 |   3 |        4 |        6 |     32 |    200 |    395 |    320 |
| Main_2 (Var.) |   4 |   3 |        4 |        6 |    443 |    200 |    395 |    320 |
| Main_3 (Rank) |   8 |   3 |        4 |        6 |    853 |    200 |    395 |    320 |

Note: Slicer_Date sits in Zone 2 (row 2), never in Zone 1 (rows 0–1).
      SQLBI rule: slicers never occupy the 3-second space.

### Detail Page — without Action Panel (T1/T2/T3 detail)

| Slot ID        | col | row | col_span | row_span | x (px) | y (px) | w (px) | h (px) |
|----------------|-----|-----|----------|----------|--------|--------|--------|--------|
| Slicer_Pane    |   0 |   0 |        2 |       12 |     32 |     32 |    189 |    656 |
| Smart_Narrative|   2 |   0 |       10 |        1 |    237 |     32 |   1011 |     40 |
| Detail_Matrix  |   2 |   1 |       10 |       11 |    237 |     88 |   1011 |    600 |

### Detail Page — with Action Panel (T4 prescriptive)

| Slot ID        | col | row | col_span | row_span | x (px) | y (px) | w (px) | h (px) |
|----------------|-----|-----|----------|----------|--------|--------|--------|--------|
| Slicer_Pane    |   0 |   0 |        2 |       12 |     32 |     32 |    189 |    656 |
| Smart_Narrative|   2 |   0 |        8 |        1 |    237 |     32 |    805 |     40 |
| Detail_Matrix  |   2 |   1 |        8 |       11 |    237 |     88 |    805 |    600 |
| ActionPanel    |  10 |   1 |        2 |       11 |   1058 |     88 |    189 |    600 |

---

## Slicer Placement

Slicer position follows the reading pattern of the page. This is intentional — not inconsistency.

| Page type      | Reading pattern | Slicer placement  | Rationale                                           |
|----------------|-----------------|-------------------|-----------------------------------------------------|
| Overview pages | Z-pattern       | Top bar (Zone 2)  | Eye scans horizontally; top filter visible at glance|
| Detail pages   | F-pattern       | Left pane (Zone 4)| Eye anchors left column; slicer context always visible while reading table down |

Rule: Never place a slicer in Zone 1 (KPI band). The 3-second space belongs to KPIs only.
Rule: Max 3 slicers per page (ux_design_system §5.1). Date/time first, categorical after.

---

## Visual Sizing Standards

Reference sizes at 1280×720 design base. Scale proportionally for other canvas sizes.

| Visual type          | Standard w  | Standard h | Compact w | Compact h |
|----------------------|-------------|------------|-----------|-----------|
| KPI Card             | 189px (2 LU)| 96px (2 LU)| 140px     |  80px     |
| Trend chart          | 395px (4 LU)| 320px (6 LU)| 300px    | 200px     |
| Waterfall / Variance | 395px (4 LU)| 320px (6 LU)| 300px    | 200px     |
| Horizontal bar       | 395px (4 LU)| 320px (6 LU)| 300px    | 200px     |
| Exception table      | 1216px full | 320px+     | —         | —         |
| Detail matrix        | slot width  | slot height| —         | —         |
| Slicer pane (left)   | 189px (2 LU)| 656px full | —         | —         |
| Action panel (right) | 189px (2 LU)| 600px (11 LU)| —       | —         |
| Smart narrative      | slot width  | 40px (1 LU)| —         | —         |

Aspect ratio rule: Charts target a 2:1 width:height ratio for readability.
KPI card max: 6 per row at standard size. Use compact when ≥5 cards required.

---

## Z-Order Rules

Priority (highest → lowest):
  1. Action Panel (T4) — always on top
  2. Slicers          — above visuals
  3. Visuals          — standard layer
  4. Background       — bottom layer

Rule: Visuals must not overlap. Action Panel is sized to a dedicated slot — it does not
      overlay chart area. Resize Main/Matrix slots accordingly (see slot table above).

---

## Snap and Alignment

- Grid snap: 10px increments (visuals align to 10px boundaries in PBI scaffold generator)
- Baseline alignment: all visuals in the same LU row share the same top Y coordinate
- No orphaned visuals: every visual must be assigned to a named slot ID

---

## References

| Document                                           | Relationship                            |
|----------------------------------------------------|-----------------------------------------|
| Design_Spec_3_30_300.md §3                   | Governing design spec — this file implements it |
| Storytelling_Principles.md §11                    | Authority for spacing values (16/40/8/32px) |
| grid_templates/ (pulse.json, action_matrix.json)  | Machine-readable slot configs derived from this file |
| grid_calculator.py                                | Formula implementation — reads this file's parameters |
| Visual_to_Slot_Mapping.yaml                       | Maps abstract visual types to named slots |
| Slot_Definitions.md                               | Prose definition of each slot's content rules |
