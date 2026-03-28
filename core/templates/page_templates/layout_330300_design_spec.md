# 3-30-300 Layout Design Specification

> **Governing authority:** [`reporting_principles.md`](../../strategy_operating_model/company/reporting_principles.md) · [`ux_design_system.md`](../../strategy_operating_model/operating_model/ux_design_system.md)
> **BPA rules:** [`REPORT_BEST_PRACTICES.md`](../../../tooling/linters/powerbi/REPORT_BEST_PRACTICES.md)
> **Web design references:** Tremor, Tabler, SQLBI (see §2)
> **Implements:** `Page_Spec_3_30_300.md` · `governance/Layout_Grid_System.yaml` · `governance/Slot_Definitions.md`

This document is the authoritative **tool-agnostic** layout design specification for all analytical pages built with the Analytics Use Case Library. It is written for frontend designers and layout engineers who implement the 3-30-300 framework across tools (Power BI, web, export).

Do not redefine content here that is already owned by the governing documents above. Reference by path instead.

---

## 1. Design Philosophy

### 1.1 Reporting as a Decision Instrument

A page has one job: lead the reader to a decision or action within their horizon. Design supports that job; it does not compete with it.

From `reporting_principles.md §3`:
> Every report must answer at least one of: *What is happening? Why is it happening? What should we do about it?*

### 1.2 Progressive Disclosure — The 3-30-300 Model

The 3-30-300 model (authoritative reference: [SQLBI](https://www.sqlbi.com/articles/introducing-the-3-30-300-rule-for-better-reports/)) structures information by the time a reader has available:

| Layer | Time | Question answered | Design goal |
|---|---|---|---|
| **3 seconds** | Glance | *Am I on track?* | Immediate orientation — status and signal |
| **30 seconds** | Scan | *Why am I off track?* | Driver explanation — trends, variance, ranking |
| **300 seconds** | Analyse | *What exactly happened / what do I do?* | Validation and action — detail + prescription |

**Not every report implements all three layers.** Each use case explicitly declares its primary layer in `UseCase_Bracket.yaml` (`ux_layout_rules`).

### 1.3 Cognitive Simplicity

From `reporting_principles.md §6`:
> Clarity always takes precedence over completeness.

Hard limits (from `REPORT_BEST_PRACTICES.md`):
- Max **20 visible visuals** per page
- Max **6 data fields** per visual
- Max **3 slicers** per page (from `ux_design_system.md §5.1`)
- **No vertical scroll** on report pages (design to fit one screen)
- **No pie/donut charts** — use 100% stacked bars

---

## 2. Design References

### 2.1 Reading Patterns

| Pattern | Applies to | Characteristics |
|---|---|---|
| **Z-pattern** | T1 Strategic, T2 Tactical overview pages | Eyes: top-left → top-right → diagonal → bottom-right. KPI cards top-left, primary chart spans top, secondary charts bottom. |
| **F-pattern** | T3 Operational, T4 Prescriptive detail pages | Eyes: scan top, then left column down. Tables/detail dominates; slicer panel anchors left; action panel anchors right. |

Use Z-pattern for the **Overview (3s/30s) page**. Use F-pattern for the **Detail (300s) page**.

### 2.2 Authority Sources

| Source | What it governs |
|---|---|
| [SQLBI — 3-30-300 rule](https://www.sqlbi.com/articles/introducing-the-3-30-300-rule-for-better-reports/) | Zone order, slicer placement, overview-first principle |
| [Microsoft PBI design tips](https://learn.microsoft.com/en-us/power-bi/create-reports/service-dashboards-design-tips) | Top-left priority, tell a story on one screen, audience + device awareness |
| [Tremor dashboard template](https://tremor.so/) | KPI card hierarchy, chart containers, table structure — web reference |
| [Tabler layout fluid](https://tabler.io/) | Fluid 12-column grid, clean spacing — web reference |
| `MOCKUP_DESIGN_SPEC.md` (this repo) | Typography roles, spacing rules, accessibility, single layout engine principle |

---

## 3. Canvas & Grid

### 3.1 Canvas Scale Problem and Solution

Power BI fonts are defined in points and do **not** scale proportionally with FitToPage. At 1920×1080 canvas displayed on a 1366×768 screen (0.71× scale), a 9pt font becomes visually ~6pt — unreadable.

**Resolution:**

| Environment | Design canvas | Production canvas | Font adjustment |
|---|---|---|---|
| **Power BI** | 1280×720 (design at this size) | 1920×1080 (scale up) | +2pt on all roles for production canvas |
| **Power BI 4K** | 1280×720 | 2560×1440 | +4pt on all roles |
| **Web / browser** | Fluid (viewport-relative) | n/a | `clamp()` with rem units — scales automatically |
| **PDF / export** | 1920×1080 | n/a | +2pt minimum; print needs larger fonts |

> **Rule:** When defining layouts, use the **design base canvas** (1280×720 for PBI). Font sizes and spacing are correct at this size. The production canvas scales everything up, and the additional `font_size_delta_pt` compensates for the non-scaling font issue.

### 3.2 Logical 12×12 Grid

All layouts use a **12-column × 12-row logical unit (LU) grid** that scales proportionally to any canvas.

Grid parameters (from `governance/Layout_Grid_System.yaml`):

| Parameter | Default | Description |
|---|---|---|
| Outer margin | 32px | Safety margin from canvas edge |
| Gutter | 16px | Gap between all visual containers |
| Grid | 12 × 12 LU | Columns and rows |

Formulas:
```
content_width  = canvas_width  − (2 × outer_margin)
content_height = canvas_height − (2 × outer_margin)
lu_width  = (content_width  − 11 × gutter) / 12
lu_height = (content_height − 11 × gutter) / 12

slot(col, row, col_span, row_span):
  x      = outer_margin + col × (lu_width + gutter)
  y      = outer_margin + row × (lu_height + gutter)
  width  = col_span × lu_width  + (col_span − 1) × gutter
  height = row_span × lu_height + (row_span − 1) × gutter
```

Implementation: `products/fabric/powerbi/tooling/page_scaffold_generator/grid_calculator.py`

---

## 4. Zone System (SQLBI-Authoritative)

Every page is divided into **four zones** in strict top-to-bottom order. Slicer position follows the SQLBI rule: slicers belong to Zone 2 (filter/zoom), **never** in Zone 1 (3-second space).

```
┌─────────────────────────────────────────────────────┐
│  ZONE 1 — 3-SECOND  (KPI band, no slicers)          │  Grid rows 0–1
├─────────────────────────────────────────────────────┤
│  ZONE 2 — 30s FILTER  (slicer bar)                  │  Grid row 2
├─────────────────────────────────────────────────────┤
│  ZONE 3 — 30s DRIVERS  (trend · variance · ranking) │  Grid rows 3–8
├─────────────────────────────────────────────────────┤
│  ZONE 4 — 300-SECOND  (detail matrix)               │  Grid rows 9–11
└─────────────────────────────────────────────────────┘
```

Zone 4 (detail matrix) is on the **Detail page**, not the Overview page, unless the page type calls for it.

---

## 5. Layer Specifications

### 5.1 Zone 1 — The 3-Second Layer (KPI Band)

**Purpose:** Immediate orientation. Status vs. target at a glance.

**Rule:** KPI band occupies the full page width. Nothing else shares this zone. No slicers, no buttons, no logos.

**Components:**

| Component | Slot ID | Required | Notes |
|---|---|---|---|
| KPI Card(s) | `KPI_Cards` | Yes | 1–6 cards. Strategic KPI first, then influencing KPIs. |
| (Date slicer is in Zone 2) | — | — | SQLBI: do not place in Zone 1 |

**KPI Card anatomy:**

```
┌─────────────────────────┐
│ KPI Label               │  ← role: kpi_label (sm)
│ €42.3M                  │  ← role: kpi_value (3xl)
│ ▲ +8.2%  vs Plan        │  ← role: kpi_delta (md) + kpi_period (xs)
│ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ (spark) │  ← sparkline (optional)
└─────────────────────────┘
```

**Signal color rules:**
- Positive delta (favourable) → `color.semantic.positive` (default green)
- Negative delta (unfavourable) → `color.semantic.negative` (default red)
- Near threshold → `color.semantic.warning`
- No signal / neutral → `color.semantic.neutral`
- **Never use color alone** — always pair with icon (▲/▼/⚠/─) for colorblind safety

**Grid position (default, 5 cards):**

| Slot | col_start | row_start | col_span | row_span |
|---|---|---|---|---|
| `KPI_Cards` | 0 | 0 | 12 | 2 |

**Size rules:**
- Standard card: ~280px wide × 140px tall (at 1280×720 canvas)
- Compact card (6 cards): ~200px × 120px
- Max 6 per row; wrap to second KPI row only if >6 cards

---

### 5.2 Zone 2 — 30-Second Filter Layer (Slicer Bar)

**Purpose:** Contextual filtering. Slicers cascade into all downstream visuals.

**Rule:** Max 3 slicers per page. Date/time slicer goes first (leftmost). Categorical slicers follow.

**Components:**

| Component | Slot ID | Required | Notes |
|---|---|---|---|
| Date slicer | `Slicer_Date` | Usually yes | Time filter; affects all downstream visuals |
| Categorical slicer(s) | `Slicer_Cat_1/2` | Optional | Region, segment, channel — max 2 additional |

**Grid position:**

| Slot | col_start | row_start | col_span | row_span |
|---|---|---|---|---|
| `Slicer_Date` | 0 | 2 | 12 | 1 |

**Alternatively — side slicer pane (Detail page):**
For Detail (300s) pages, slicers may move to a left-side pane:

| Slot | col_start | row_start | col_span | row_span |
|---|---|---|---|---|
| `Slicer_Pane` | 0 | 0 | 2 | 12 |

---

### 5.3 Zone 3 — The 30-Second Layer (Diagnostics)

**Purpose:** Explain why. Trends, variance, ranking, mix.

**Rule:** Primary visuals fill this zone. Each visual answers one diagnostic question (per `Slot_Definitions.md`). Every visual title must be question-oriented, not generic (e.g., "Where are we off plan?" not "Waterfall Chart").

**Slot-to-visual mapping:**

| Slot | Primary question | Preferred visual | Fallback | Template |
|---|---|---|---|---|
| `Main_1` / Trend | How is the KPI developing over time? | Line chart | Area chart | T1, T2, T3 |
| `Main_2` / Variance | Where are we off plan? | Waterfall chart | Horizontal bar | T1, T2 |
| `Main_3` / Ranking | Who drives what? | Horizontal bar (sorted) | — | T1, T2, T3 |
| Mix (optional) | How is value distributed? | 100% stacked bar | — | T1, T2 |
| Exceptions (T3) | Where are abnormal cases? | Table | — | T3 |
| Prescriptive (T4) | What action should be taken? | Recommendation table | — | T4 |

**Reference visual position:** Show target/reference line on trend visuals wherever a reference value exists (target, prior year, budget).

**Default grid positions (three-column layout, Overview page):**

| Slot | col_start | row_start | col_span | row_span |
|---|---|---|---|---|
| `Main_1` (Trend) | 0 | 3 | 4 | 6 |
| `Main_2` (Variance) | 4 | 3 | 4 | 6 |
| `Main_3` (Ranking) | 8 | 3 | 4 | 6 |

**Adaptive resizing:** When fewer than 3 slots are activated, expand remaining slots to fill available width proportionally. (Implemented in `layout_calculator.py`)

---

### 5.4 Zone 4 — The 300-Second Layer (Detail / Action)

**Purpose:** Validate. Drill into individual records. Take action (T4).

**Rule:** Always on the **Detail page**. Never on the Overview page (unless use case explicitly requires a combined layout with justification). Full-page context — F-reading-pattern layout.

**Components:**

| Component | Slot ID | Required | Notes |
|---|---|---|---|
| Slicer pane (left) | `Slicer_Pane` | Yes | Context switch — time, region, segment |
| Smart Narrative | `Smart_Narrative` | Yes | 1-sentence summary of current filter context |
| Detail Matrix | `Detail_Matrix` | Yes | Operative entity list — measures, deltas, data bars |
| Action Panel | `ActionPanel` | T4 only | Recommendation, owner, trigger, impact (right side) |

**Grid positions (Detail page with action panel):**

| Slot | col_start | row_start | col_span | row_span |
|---|---|---|---|---|
| `Slicer_Pane` | 0 | 0 | 2 | 12 |
| `Smart_Narrative` | 2 | 0 | 8 | 1 |
| `Detail_Matrix` | 2 | 1 | 8 | 11 |
| `ActionPanel` | 10 | 1 | 2 | 11 |

**Without action panel (T1/T2/T3 detail pages):**

| Slot | col_start | row_start | col_span | row_span |
|---|---|---|---|---|
| `Slicer_Pane` | 0 | 0 | 2 | 12 |
| `Smart_Narrative` | 2 | 0 | 10 | 1 |
| `Detail_Matrix` | 2 | 1 | 10 | 11 |

**Detail Matrix anatomy:**
- Entity grain per row (invoice, customer, product, region — defined in `UseCase_Bracket.yaml`)
- Columns: entity identifier, key measures, delta vs plan/prior, % delta
- Delta columns use data bars for quick scanning (value and bar in same cell)
- Optional `ActionCode` column for row-level prescription (T4, Phase 2)
- Sort default: descending by delta (worst first)
- Row limit: 50–100 (more on demand, never load all by default)

**Action Panel anatomy (T4 only):**
```
┌──────────────────┐
│ RECOMMENDED      │
│ ACTION           │
│                  │
│ Reduce promo     │
│ depth in DACH    │
│                  │
│ Owner: CM DACH   │
│ Due: EOM         │
│ Impact: +€1.2M   │
│                  │
│ Steps:           │
│ 1. Cap discount  │
│ 2. Review mix    │
│ 3. Alert buyer   │
└──────────────────┘
```

---

## 6. Page Compositions

### 6.1 The Pulse (Overview — 3s + 30s)

Standard 2-zone overview for T1/T2. Z-reading pattern.

```
Grid: 12 × 12 LU  |  Canvas: 1280×720 (design) / 1920×1080 (production)

Row 0–1 │ KPI_Cards (12 wide)
Row 2   │ Slicer_Date (12 wide)
Row 3–8 │ Main_1 (4w)  │ Main_2 (4w)  │ Main_3 (4w)
Row 9–11│ (empty — detail page)
```

### 6.2 The Action Matrix (Detail — 300s)

Standard detail page. F-reading pattern.

```
Row 0–11 │ Slicer_Pane (2w) │ Smart_Narrative (8w) + ActionPanel (2w, T4)
          │                  │ Detail_Matrix (8w)   + ActionPanel (continues)
```

### 6.3 The Investigator (Alternative Overview)

Focus layout for deep-dive scenarios where a single dominant visual tells the story.

```
Row 0–11 │ Slicer_Pane (2w) │ Focus_Area (8w dominant visual)
          │                  │ Support_1 (4w) │ Support_2 (4w)
```

---

## 7. Visual Grammar Rules

### 7.1 Color Meaning

Color carries **semantic meaning**, not decoration. The same color must mean the same thing across all pages:

| Color | Meaning | Never use for |
|---|---|---|
| `semantic.positive` (green) | Favourable delta, above target | General highlighting, brand accents on charts |
| `semantic.negative` (red) | Unfavourable delta, below target | Emphasis on neutral data |
| `semantic.warning` (amber) | Near threshold, attention needed | Positive signals |
| `semantic.neutral` (grey) | No signal, informational | Performance-coded data |
| `color.primary` (brand) | First data series, primary KPI | Signal coding (use semantic only) |
| `color.secondary` (brand) | Second data series | Signal coding |

**Colorblind safety:** Never rely on red/green alone. Always pair with:
- Direction icon (▲ ▼ ⚠ ─)
- Bold/regular font weight to distinguish
- Pattern or shape variation where possible

### 7.2 Visual Titles

Every visual has a **question-oriented title** (from `MOCKUP_DESIGN_SPEC.md §9`):

| Instead of | Use |
|---|---|
| "Revenue Chart" | "How is revenue trending vs prior year?" |
| "Variance" | "Where are we off plan this month?" |
| "Top Customers" | "Which customers drive the most revenue?" |
| "Data Table" | "Which regions explain the revenue gap?" |

### 7.3 Decision Question Banner

The primary business question from the use case is displayed on the page (from `MOCKUP_DESIGN_SPEC.md §8`). Placement: page title area or subtitle bar directly below the KPI band.

### 7.4 Truncation and Overflow

- Long labels: truncate at 20 characters with tooltip showing full text
- Axis labels: show max 8 ticks; rotate 45° only if necessary
- KPI values: abbreviate with suffix (€42.3M not €42,300,000)
- Table cells: truncate at column width; never wrap mid-word

---

## 8. Interaction Patterns

### 8.1 Slicer Cascade

All slicers on a page filter all visuals on that page. Cross-page filtering via drillthrough, not via page-level filters. Active filter state must always be visible (show current slicer selection).

### 8.2 Drillthrough

Overview page → Detail page via right-click "Drill through". Filter context (date range, entity selection) passes automatically. Detail page configured as `type: "Drillthrough"` + `visibility: "AlwaysVisible"` so it is also directly accessible.

### 8.3 Tooltip Anatomy

Tooltips appear on chart hover. Minimum content:
- Measure name
- Value (formatted with unit)
- Reference value (target/PY) if applicable
- Delta (absolute + %)
- Period label

---

## 9. Accessibility

- **WCAG AA contrast minimum:** 4.5:1 for body text, 3:1 for large text (≥18pt or ≥14pt bold)
- **Colorblind safety:** Signal colors always paired with icon + optional weight change
- **Tab order:** KPI band → primary visuals → secondary visuals → slicers → action panel
- **Alt text / description:** Every visual has a descriptive title (used as alt text in accessible exports)
- **Focus states:** Interactive elements (slicers, drill buttons) have visible focus rings

---

## 10. BPA Hard Limits

All layouts must comply with `REPORT_BEST_PRACTICES.md`. Hard limits enforced by linter:

| Rule | Limit | Reason |
|---|---|---|
| Visible visuals per page | ≤ 20 | Performance and cognitive load |
| Data fields per visual | ≤ 6 | Readability |
| Slicers per page | ≤ 3 | Clutter (ux_design_system) |
| TopN filters per page | ≤ 4 | Performance |
| Page height (no scroll) | ≤ canvas height | No vertical scroll allowed |
| Hard-coded colors in visuals | 0 | Must use theme colors |
| Pie/donut charts | 0 | Not allowed (ux_design_system §5.1) |

---

## 11. Web Derivation Notes

When implementing 3-30-300 layouts in web/browser contexts:

- Use the 12-column CSS grid defined in `core/brand/tool_derivations/css_mapping.md`
- Use `--brand-*` CSS custom properties for all colors, spacing, and typography
- Zone widths collapse at breakpoints: 3-column driver zone → 1 column stacked at `sm` breakpoint
- KPI card band reflows to 2-column at `md`, 1-column at `sm`
- Detail matrix becomes horizontally scrollable at `md` and below
- Action panel moves below detail matrix on mobile (not sidebar)
- Tremor KPI card component matches the 3-second layer anatomy above
- Tabler fluid grid aligns with the 12-column system

---

## References

| Document | Location |
|---|---|
| Page Spec (slot overview) | `core/templates/page_templates/Page_Spec_3_30_300.md` |
| Slot Definitions | `core/templates/page_templates/governance/Slot_Definitions.md` |
| Layout Grid System | `core/templates/page_templates/governance/Layout_Grid_System.yaml` |
| Visual-to-Slot Mapping | `core/templates/page_templates/governance/Visual_to_Slot_Mapping.yaml` |
| Grid Templates | `core/templates/page_templates/grid_templates/` |
| Mockup Design Spec (web/PBI) | `products/fabric/powerbi/tooling/page_scaffold_generator/MOCKUP_DESIGN_SPEC.md` |
| BPA Rules | `tooling/linters/powerbi/REPORT_BEST_PRACTICES.md` |
| Brand Spec Schema | `core/brand/BrandSpec.schema.yaml` |
| PBI Theme Mapping | `core/brand/tool_derivations/powerbi_mapping.md` |
| CSS Mapping | `core/brand/tool_derivations/css_mapping.md` |
| Layer Samples | `core/templates/page_templates/samples/` |
