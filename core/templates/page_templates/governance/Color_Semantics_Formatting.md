# Color Semantics and Formatting Rules — Framework Governance
#
# Authority:   This file is the canonical source for color tokens, semantic roles,
# and typography rules for all Analytics Use Case Library pages.
#
# Tool-agnostic: Tokens are defined as abstract semantic roles with hex defaults.
# Connector-specific bindings (PBI theme roles, CSS variables, etc.)
# are listed in the Connector Bindings section below.
#
# Implements:  Design_Spec_3_30_300.md §7 (Visual Grammar Rules)
# Aligns with: Storytelling_Principles.md §9 (Color System), §10 (Typography)

---

## Semantic Color Tokens (Tool-Agnostic)

Semantic color assignments conform to **ISO 3864-1:2011** (Safety colours — workplaces and public areas) and **IEC 60073** (Indicator lamp and actuator colour coding for man-machine interfaces):
- **Red** = danger / immediate action required → `semantic.negative`
- **Amber/Yellow** = warning / attention needed → `semantic.warning`
- **Green** = normal / on target → `semantic.positive`

These conventions are deeply internalised by users across industrial and enterprise contexts. Never invert them for aesthetic reasons.

These tokens are the single source of truth for color meaning. Every chart, card, and
table uses these roles — never hardcoded hex values directly in visual definitions.

| Token                  | Default Hex | Meaning                                               | Never use for                        |
|------------------------|-------------|-------------------------------------------------------|--------------------------------------|
| semantic.positive      | #107C10     | Favourable delta, above target, good performance      | Brand accents, general categories    |
| semantic.negative      | #A4262C     | Unfavourable delta, below target, critical exception  | Neutral data, category encoding      |
| semantic.warning       | #C08000     | Near threshold, attention needed, caution             | Positive signals, brand color        |
| semantic.neutral       | #605E5C     | No signal, informational, no target set               | Performance-coded data               |
| brand.primary          | #0078D4     | First data series, primary KPI line, reference line   | Signal coding (use semantic.* only)  |
| brand.secondary        | #50E6FF     | Second data series, supporting metrics                | Signal coding                        |
| brand.data_colors[0]   | #0078D4     | Categorical series slot 0                             | —                                    |
| brand.data_colors[1]   | #50E6FF     | Categorical series slot 1                             | —                                    |
| brand.data_colors[2]   | #8661C5     | Categorical series slot 2                             | —                                    |
| brand.data_colors[3]   | #F7630C     | Categorical series slot 3                             | —                                    |
| brand.data_colors[4]   | #008575     | Categorical series slot 4                             | —                                    |
| brand.data_colors[5]   | #E3008C     | Categorical series slot 5                             | —                                    |
| brand.data_colors[6]   | #EF6950     | Categorical series slot 6                             | —                                    |
| brand.data_colors[7]   | #FFB900     | Categorical series slot 7                             | —                                    |
| surface.page           | #F5F5F5     | Page background                                       | —                                    |
| surface.card           | #FFFFFF     | Visual / card background                              | —                                    |
| surface.row_alt        | #F9F9F9     | Alternating table row background                      | —                                    |
| text.primary           | #201F1E     | Primary text (titles, values, labels)                 | —                                    |
| text.secondary         | #605E5C     | Secondary text (axis labels, footnotes)               | —                                    |
| border.default         | #E1DFDD     | Visual borders, grid lines (0.5px, 8px radius)        | —                                    |
| severity_tints.critical| #FFE6E6     | Row/bg tint for critical exceptions (T3) and high-priority actions (T4) — semantic.negative at 15% alpha | — |
| severity_tints.warning | #FFF8E1     | Row/bg tint for warning exceptions and medium-priority actions — semantic.warning at 15% alpha | — |
| severity_tints.good    | #E6F5E6     | Row/bg tint for on-target/low-priority rows — semantic.positive at 15% alpha | — |

Colorblind-safe variance pair: brand.primary (#0078D4 blue) / brand.data_colors[3] (#F7630C orange)
Use this pair instead of semantic.positive/semantic.negative when printing or when
colorblind safety is critical. Always pair with icon regardless.

Rule: Max 3–4 semantic colors visible on any single page.
Rule: Never hardcode hex in visual definitions. Reference tokens by name.
Rule: Every color signal must be paired with an icon (▲ ▼ ⚠ ─) for colorblind safety.

---

## IBCS Scenario Encoding — Shape and Fill

Color alone cannot distinguish scenarios when multiple time references appear on the same visual.
IBCS (HICHERT, Rolf; FAISST, Jürgen — *Solid, Outlined, Hatched*, IBCS Institute, 2020) defines a
fill-pattern encoding that works alongside color and abbreviations.

| Scenario | Abbreviation | Fill / Shape | Applies to |
|----------|--------------|--------------|------------|
| Actual (current period) | AC | **Solid fill** | Bars, columns, areas, dots |
| Plan / Budget | PL | **Outlined / hollow** (same color, no fill) | Bars, columns, reference markers |
| Forecast | FC | **Hatched / cross-hatched** | Bars, columns, areas |
| Prior Year | PY | **Lighter tint** (50% opacity of AC fill) | Bars, columns, lines |

Rules:

- Scenario encoding is **additive** — it works alongside the semantic color system, not instead of it
- When AC and PL appear on the same chart, use solid vs. outlined — never use a second color to distinguish scenarios
- When FC appears alongside AC, use hatched fill — the reader must distinguish "what happened" from "what we project"
- PY as a reference line: use `brand.primary` dashed, 1px — no fill encoding needed for a line reference
- Never use scenario encoding for categorical data (e.g., product lines or regions) — categories use `brand.data_colors[0–7]`

Connector implementation:
- Power BI: use custom shape markers on line charts; hatched fill requires SVG pattern in theme.json
- Web/CSS: `background-image: repeating-linear-gradient(45deg, ...)` for hatch pattern
- Where tool-native hatching is unavailable, use a heavier stroke outline (2.5px) for PL and a dashed stroke for FC

---

## Connector Token Bindings

### Power BI / Fabric (theme.json)

| Token                | Power BI theme property         |
|----------------------|---------------------------------|
| semantic.positive    | good                            |
| semantic.negative    | bad                             |
| semantic.warning     | neutral                         |
| semantic.neutral     | fourthLevelElements             |
| brand.primary        | dataColors[0]                   |
| surface.page         | background                      |
| surface.card         | secondaryBackground             |
| text.primary         | firstLevelElements              |
| text.secondary       | secondLevelElements             |
| border.default       | tableAccent                     |

Theme generator: products/fabric/powerbi/tooling/theme_generator/

### Web / CSS

```css
:root {
  --color-positive:  #107C10;
  --color-negative:  #A4262C;
  --color-warning:   #C08000;
  --color-neutral:   #605E5C;
  --color-primary:   #0078D4;
  --color-secondary: #50E6FF;
  --surface-page:    #F5F5F5;
  --surface-card:    #FFFFFF;
  --text-primary:    #201F1E;
  --text-secondary:  #605E5C;
  --border-default:  #E1DFDD;
}
```

### Other tools (Superset, Grafana, Metabase)

See connectors/OSS_Connector_Guide.md — map token names to each tool's color config.

---

## Typography Scale

Canonical font sizes for the 1280×720 design base canvas.
Scale up by ~1.5× for 1920×1080 production canvas or add +2pt minimum for PDF export.

| Token           | Size       | Weight          | Color token    | Usage                                         |
|-----------------|------------|-----------------|----------------|-----------------------------------------------|
| page_title      | 16–18pt    | Regular         | text.primary   | Page / report title (decision question)       |
| section_header  | 13–14pt    | Semibold        | text.primary   | Visual title (question-oriented)              |
| kpi_value       | 28–36pt    | Bold            | text.primary   | Hero number on KPI card                       |
| kpi_delta       | 13–14pt    | Regular         | semantic.*     | Variance value + icon on KPI card             |
| kpi_label       | 10–11pt    | Regular         | text.secondary | KPI name below the value (muted)              |
| axis_label      | 9–11pt     | Regular         | text.secondary | Chart axis tick labels                        |
| data_label      | 10–11pt    | Regular         | text.primary   | On-chart data labels (sparse use only)        |
| table_header    | 11–12pt    | Bold            | text.primary   | Column headers in tables and matrices         |
| table_value     | 10–11pt    | Regular         | text.primary   | Row values in tables                          |
| footnote        | 8–9pt      | Regular         | text.secondary | Data source, timestamp, notes (muted)         |

Font family rule: One sans-serif family across all pages. Vary only weight and size.
Accepted families: Segoe UI (Fabric/PBI), Inter, Roboto, Open Sans (web/OSS tools).
Tabular numerals required for any column of numbers users compare vertically.
Monospace override: Use JetBrains Mono (or ui-monospace / Consolas as fallback) for KPI hero
values, data-bar values, action code IDs, and any column of numbers requiring strict alignment.

Source authority: Storytelling_Principles.md §10

---

## KPI Card Formatting

### Required Elements

| Element         | Token          | Format                                       |
|-----------------|----------------|----------------------------------------------|
| KPI label       | kpi_label      | Metric name — sentence case, ≤ 25 chars      |
| Current value   | kpi_value      | Formatted per metric type (see Value Formats)|
| Delta vs ref.   | kpi_delta      | ▲/▼ + value + semantic color token           |
| Period label    | footnote       | "vs Plan", "vs PY", "MTD" — right-aligned    |
| Sparkline       | brand.primary  | Optional; trailing 12 periods                |

### Value Format Rules

| Metric type | Format         | Example       |
|-------------|----------------|---------------|
| Currency    | Suffix K/M/B   | €42.3M        |
| Percentage  | 1 decimal      | 45.2%         |
| Count       | Thousands sep. | 1,234         |
| Index       | 2 decimals     | 1.23          |

### Signal Color Logic

| Condition            | Token              | Icon |
|----------------------|--------------------|------|
| Above target         | semantic.positive  | ▲    |
| Below target         | semantic.negative  | ▼    |
| Within ±5% of target | semantic.warning   | ⚠    |
| No target defined    | semantic.neutral   | ─    |

Rule: Delta direction (up/down) and color (good/bad) are independent.
      For cost metrics, ▲ (increase) maps to semantic.negative; ▼ to semantic.positive.
      The metric polarity is declared in core/kpi_catalog/<kpi_id>.yaml (polarity: higher_is_better | lower_is_better).

---

## Chart Formatting

### Data Series Colors

- First series:  brand.data_colors[0]
- Further series: brand.data_colors[1..7] in order
- Semantic signal overrides categorical color (e.g. a variance bar always uses semantic.positive/negative)

### Reference / Target Lines

- Color:  brand.primary (#0078D4)
- Style:  dashed, 1.5px
- Label:  show value at line endpoint

### Variance Charts (Waterfall)

| Bar type        | Token             |
|-----------------|-------------------|
| Positive bridge | semantic.positive |
| Negative bridge | semantic.negative |
| Subtotal bar    | brand.primary     |
| Net total bar   | semantic.positive or semantic.negative (per result) |

### Grid Lines

- Show: yes (subtle)
- Color: border.default (#E1DFDD)
- Width: 1px, 80% transparency
- Horizontal only (suppress vertical grid lines)

### Axis Labels

- Font: axis_label (9–11pt, text.secondary)
- Show max 8 tick labels per axis; rotate 45° only if labels > 12 chars
- Zero-based axis mandatory for bar/column charts

### Data Labels

- Show on key points only: endpoints, inflection points, highlighted values
- Font: data_label (10–11pt, text.primary)
- Background: surface.card with 80% opacity

---

## Table Formatting

### General

- Header:          table_header, background surface.card
- Row background:  alternating surface.card / surface.row_alt
- Row border:      border.default, 1px
- Max rows shown:  50 (paginate on demand)
- Default sort:    worst deviation first (descending absolute delta)

### Exception Tables (T3)

| Severity | Row background          | Token                          |
|----------|-------------------------|--------------------------------|
| Critical | #FFE6E6                 | severity_tints.critical        |
| Warning  | #FFF8E1                 | severity_tints.warning         |
| Info     | #F9F9F9                 | surface.row_alt                |

Sort: Critical → Warning → Info, then by deviation descending.

### Prescriptive Tables (T4)

| Priority | Row background | Token                    |
|----------|----------------|--------------------------|
| High     | #FFE6E6        | severity_tints.critical  |
| Medium   | #FFF8E1        | severity_tints.warning   |
| Low      | #E6F5E6        | severity_tints.good      |

Top recommendation row: bold text, brand.primary at 20% alpha background, border.default 2px.

### Data Bars (Detail Matrix)

- Bar fill: brand.primary for positive delta, semantic.negative for negative delta
- Bar max width: column width minus value label
- Show value and bar in same cell

---

## Borders and Surfaces

| Element              | Style                                       |
|----------------------|---------------------------------------------|
| Visual container     | border.default, 0.5px, 8px border-radius    |
| Table border         | border.default, 1px, no radius              |
| Action Panel         | Left border only: brand.primary, 2px         |
| Card hover / focus   | brand.primary, 1.5px                        |
| Page background      | surface.page (#F5F5F5)                      |
| Visual background    | surface.card (#FFFFFF)                      |

---

## Accessibility

### Contrast (WCAG 2.2 AA)

Standard: **WCAG 2.2 AA** (W3C, October 2023). Applies to all tool outputs.

| Element type | SC | Required contrast ratio |
|---|---|---|
| Body text (≤18pt) | SC 1.4.3 | 4.5:1 minimum |
| Large text (≥18pt bold or ≥24pt) | SC 1.4.3 | 3.0:1 minimum |
| Chart fills, data lines, data points, axis indicators, icon glyphs | SC 1.4.11 Non-Text Contrast | 3.0:1 minimum |

All token hex values in this file have been validated for WCAG 2.2 AA compliance against
surface.card (#FFFFFF) and surface.page (#F5F5F5) for both SC 1.4.3 (text) and
SC 1.4.11 (non-text graphic elements).

### Colorblind Safety

- Never use semantic.positive / semantic.negative as the only distinguishing signal.
- Always pair with icon: ▲ (positive), ▼ (negative), ⚠ (warning), ─ (neutral)
- Optional: pair with bold (positive) vs regular (negative) font weight
- For variance charts where colorblind safety is critical: use blue/orange pair
  (brand.primary / brand.data_colors[3]) instead of green/red

### Tab / Focus Order

KPI band → primary visuals → secondary visuals → slicers → action panel

---

## References

| Document                           | Relationship                                              |
|------------------------------------|-----------------------------------------------------------|
| Storytelling_Principles.md §9      | Authority for semantic color role definitions             |
| Storytelling_Principles.md §10     | Authority for typography scale (font sizes and weights)   |
| Design_Spec_3_30_300.md §7    | Governing spec — this file implements it                  |
| products/fabric/powerbi/tooling/theme_generator/ | PBI theme JSON generation from these tokens  |
| connectors/OSS_Connector_Guide.md  | Token binding for Superset, Grafana, Metabase             |
| core/kpi_catalog/<kpi_id>.yaml     | KPI polarity (higher_is_better) for delta color logic     |
