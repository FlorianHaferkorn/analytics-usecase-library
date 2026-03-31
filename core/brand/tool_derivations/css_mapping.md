# BrandSpec → CSS Custom Properties Mapping

> **Schema:** `core/brand/BrandSpec.schema.yaml`
> **Web design references:** Tremor (tremor.so), Tabler (tabler.io), Tailwind CSS conventions
> **Pattern references:** `products/fabric/powerbi/tooling/page_scaffold_generator/MOCKUP_DESIGN_SPEC.md §2`

This guide defines how BrandSpec properties map to CSS custom properties (variables) for use in web-based analytical interfaces, the open-source stack, and Studio UI components.

---

## Custom Property Naming Convention

All variables are prefixed with `--brand-`. Nested BrandSpec sections map to segments:

```
--brand-<section>-<property>-<variant>
```

Examples:
- `color.primary` → `--brand-color-primary`
- `color.semantic.positive.color` → `--brand-color-positive`
- `typography.role_map.kpi_value` → `--brand-type-kpi-value` (resolves to the scale step value)
- `spacing.scale.md` → `--brand-spacing-md`

---

## Color Variables

### Brand Colors

| BrandSpec | CSS Custom Property | Usage |
|---|---|---|
| `color.primary` | `--brand-color-primary` | Primary charts, CTAs, active state |
| `color.secondary` | `--brand-color-secondary` | Secondary charts, accent elements |
| `color.primary` (10% opacity) | `--brand-color-primary-subtle` | Hover states, subtle highlights |
| `color.secondary` (10% opacity) | `--brand-color-secondary-subtle` | Hover states on secondary elements |

### Semantic Signal Colors

| BrandSpec | CSS Custom Property | Usage |
|---|---|---|
| `color.semantic.positive.color` | `--brand-color-positive` | Good/up signal text, icons, borders |
| `color.semantic.negative.color` | `--brand-color-negative` | Bad/down signal text, icons, borders |
| `color.semantic.warning.color` | `--brand-color-warning` | Near-threshold alert |
| `color.semantic.neutral.color` | `--brand-color-neutral` | No-signal, informational |
| `color.semantic.positive.color` (15% bg) | `--brand-color-positive-bg` | KPI card positive background fill |
| `color.semantic.negative.color` (15% bg) | `--brand-color-negative-bg` | KPI card negative background fill |
| `color.semantic.warning.color` (15% bg) | `--brand-color-warning-bg` | Warning state background |

### Neutral Scale

| BrandSpec | CSS Custom Property | Usage |
|---|---|---|
| `color.neutral_scale["50"]` | `--brand-neutral-50` | Page/canvas background |
| `color.neutral_scale["100"]` | `--brand-neutral-100` | Card backgrounds, panel fills |
| `color.neutral_scale["200"]` | `--brand-neutral-200` | Borders, dividers, rule lines |
| `color.neutral_scale["400"]` | `--brand-neutral-400` | Disabled text, placeholders |
| `color.neutral_scale["700"]` | `--brand-neutral-700` | Body text, secondary labels |
| `color.neutral_scale["900"]` | `--brand-neutral-900` | Headlines, primary labels |

### Semantic Role Aliases (Mapped from Neutral Scale)

```css
--brand-color-background:     var(--brand-neutral-50);
--brand-color-surface:        var(--brand-neutral-100);
--brand-color-border:         var(--brand-neutral-200);
--brand-color-muted:          var(--brand-neutral-400);
--brand-color-body:           var(--brand-neutral-700);
--brand-color-heading:        var(--brand-neutral-900);
```

---

## Typography Variables

### Font Families

| BrandSpec | CSS Custom Property |
|---|---|
| `typography.font_family.primary` | `--brand-font-primary` |
| `typography.font_family.secondary` | `--brand-font-secondary` (falls back to `--brand-font-primary`) |
| `typography.font_family.monospace` | `--brand-font-mono` |

### Type Scale

Fluid typography uses `clamp(min, preferred, max)` for responsive behavior:

| BrandSpec step | CSS Custom Property | `clamp()` value |
|---|---|---|
| `xs` (0.625rem) | `--brand-type-xs` | `clamp(0.625rem, 0.6rem + 0.1vw, 0.75rem)` |
| `sm` (0.75rem) | `--brand-type-sm` | `clamp(0.75rem, 0.7rem + 0.15vw, 0.875rem)` |
| `md` (0.875rem) | `--brand-type-md` | `clamp(0.875rem, 0.85rem + 0.2vw, 1rem)` |
| `lg` (1.0rem) | `--brand-type-lg` | `clamp(1rem, 0.95rem + 0.25vw, 1.125rem)` |
| `xl` (1.25rem) | `--brand-type-xl` | `clamp(1.125rem, 1.1rem + 0.3vw, 1.375rem)` |
| `2xl` (1.5rem) | `--brand-type-2xl` | `clamp(1.375rem, 1.3rem + 0.5vw, 1.75rem)` |
| `3xl` (2.0rem) | `--brand-type-3xl` | `clamp(1.75rem, 1.6rem + 0.8vw, 2.5rem)` |

### Semantic Role Variables

Roles resolve to scale step variables:

| BrandSpec role | CSS Custom Property | Resolves to |
|---|---|---|
| `kpi_value` | `--brand-type-kpi-value` | `var(--brand-type-3xl)` |
| `kpi_label` | `--brand-type-kpi-label` | `var(--brand-type-sm)` |
| `kpi_delta` | `--brand-type-kpi-delta` | `var(--brand-type-md)` |
| `kpi_period` | `--brand-type-kpi-period` | `var(--brand-type-xs)` |
| `chart_title` | `--brand-type-chart-title` | `var(--brand-type-md)` |
| `axis_label` | `--brand-type-axis-label` | `var(--brand-type-xs)` |
| `body` | `--brand-type-body` | `var(--brand-type-md)` |
| `caption` | `--brand-type-caption` | `var(--brand-type-xs)` |
| `heading_1` | `--brand-type-heading-1` | `var(--brand-type-2xl)` |
| `heading_2` | `--brand-type-heading-2` | `var(--brand-type-xl)` |
| `heading_3` | `--brand-type-heading-3` | `var(--brand-type-lg)` |
| `table_header` | `--brand-type-table-header` | `var(--brand-type-sm)` |
| `table_cell` | `--brand-type-table-cell` | `var(--brand-type-sm)` |

---

## Spacing Variables

| BrandSpec | CSS Custom Property | Value |
|---|---|---|
| `spacing.scale.xs` | `--brand-spacing-xs` | `4px` |
| `spacing.scale.sm` | `--brand-spacing-sm` | `8px` |
| `spacing.scale.md` | `--brand-spacing-md` | `16px` |
| `spacing.scale.lg` | `--brand-spacing-lg` | `24px` |
| `spacing.scale.xl` | `--brand-spacing-xl` | `32px` |
| `spacing.scale.2xl` | `--brand-spacing-2xl` | `48px` |
| `spacing.scale.3xl` | `--brand-spacing-3xl` | `64px` |

---

## Border Variables

| BrandSpec | CSS Custom Property | Value |
|---|---|---|
| `border.radius.none` | `--brand-radius-none` | `0px` |
| `border.radius.sm` | `--brand-radius-sm` | `2px` |
| `border.radius.md` | `--brand-radius-md` | `4px` |
| `border.radius.lg` | `--brand-radius-lg` | `8px` |
| `border.radius.full` | `--brand-radius-full` | `9999px` |
| `border.width.hairline` | `--brand-border-hairline` | `1px` |
| `border.width.thin` | `--brand-border-thin` | `1px` |
| `border.width.medium` | `--brand-border-medium` | `2px` |

---

## Shadow Variables

| BrandSpec | CSS Custom Property |
|---|---|
| `shadow.none` | `--brand-shadow-none` |
| `shadow.low` | `--brand-shadow-low` |
| `shadow.medium` | `--brand-shadow-medium` |
| `shadow.high` | `--brand-shadow-high` |

---

## Generated CSS File Structure

The generator produces a `:root` block with all variables:

```css
/* ─────────────────────────────────────────
   Brand: Aurora Group SE (aurora_group)
   Generated from: showcases/aurora_group/brand/brand_spec.yaml
   Schema: core/brand/BrandSpec.schema.yaml v1.0
   ───────────────────────────────────────── */

:root {
  /* Brand Colors */
  --brand-color-primary:          #2ECDE7;
  --brand-color-secondary:        #44B396;
  --brand-color-primary-subtle:   rgba(46, 205, 231, 0.10);
  --brand-color-secondary-subtle: rgba(68, 179, 150, 0.10);

  /* Semantic Signals */
  --brand-color-positive:         #107C10;
  --brand-color-negative:         #D13438;
  --brand-color-warning:          #F7630C;
  --brand-color-neutral:          #605E5C;
  --brand-color-positive-bg:      rgba(16, 124, 16, 0.15);
  --brand-color-negative-bg:      rgba(209, 52, 56, 0.15);
  --brand-color-warning-bg:       rgba(247, 99, 12, 0.15);

  /* Neutral Scale */
  --brand-neutral-50:             #F5FBFC;
  --brand-neutral-100:            #E8F6F9;
  --brand-neutral-200:            #C5E8EF;
  --brand-neutral-400:            #7FB8C7;
  --brand-neutral-700:            #004E7A;
  --brand-neutral-900:            #00396B;

  /* Semantic Aliases */
  --brand-color-background:       var(--brand-neutral-50);
  --brand-color-surface:          var(--brand-neutral-100);
  --brand-color-border:           var(--brand-neutral-200);
  --brand-color-muted:            var(--brand-neutral-400);
  --brand-color-body:             var(--brand-neutral-700);
  --brand-color-heading:          var(--brand-neutral-900);

  /* Typography */
  --brand-font-primary:   'Segoe UI', system-ui, -apple-system, sans-serif;
  --brand-font-mono:      'Cascadia Code', Consolas, 'Courier New', monospace;

  --brand-type-xs:       clamp(0.625rem, 0.6rem + 0.1vw, 0.75rem);
  --brand-type-sm:       clamp(0.75rem,  0.7rem + 0.15vw, 0.875rem);
  --brand-type-md:       clamp(0.875rem, 0.85rem + 0.2vw, 1rem);
  --brand-type-lg:       clamp(1rem,     0.95rem + 0.25vw, 1.125rem);
  --brand-type-xl:       clamp(1.125rem, 1.1rem + 0.3vw,  1.375rem);
  --brand-type-2xl:      clamp(1.375rem, 1.3rem + 0.5vw,  1.75rem);
  --brand-type-3xl:      clamp(1.75rem,  1.6rem + 0.8vw,  2.5rem);

  /* Role Aliases */
  --brand-type-kpi-value:    var(--brand-type-3xl);
  --brand-type-kpi-label:    var(--brand-type-sm);
  --brand-type-kpi-delta:    var(--brand-type-md);
  --brand-type-kpi-period:   var(--brand-type-xs);
  --brand-type-chart-title:  var(--brand-type-md);
  --brand-type-axis-label:   var(--brand-type-xs);
  --brand-type-body:         var(--brand-type-md);
  --brand-type-caption:      var(--brand-type-xs);
  --brand-type-heading-1:    var(--brand-type-2xl);
  --brand-type-heading-2:    var(--brand-type-xl);
  --brand-type-heading-3:    var(--brand-type-lg);
  --brand-type-table-header: var(--brand-type-sm);
  --brand-type-table-cell:   var(--brand-type-sm);

  /* Spacing */
  --brand-spacing-xs:    4px;
  --brand-spacing-sm:    8px;
  --brand-spacing-md:    16px;
  --brand-spacing-lg:    24px;
  --brand-spacing-xl:    32px;
  --brand-spacing-2xl:   48px;
  --brand-spacing-3xl:   64px;

  /* Borders */
  --brand-radius-none:   0px;
  --brand-radius-sm:     2px;
  --brand-radius-md:     4px;
  --brand-radius-lg:     8px;
  --brand-radius-full:   9999px;
  --brand-border-hairline: 1px;
  --brand-border-thin:     1px;
  --brand-border-medium:   2px;

  /* Shadows */
  --brand-shadow-none:   none;
  --brand-shadow-low:    0 1px 3px rgba(0,57,107,0.10), 0 1px 2px rgba(0,57,107,0.06);
  --brand-shadow-medium: 0 4px 12px rgba(0,57,107,0.12), 0 2px 6px rgba(0,57,107,0.08);
  --brand-shadow-high:   0 8px 24px rgba(0,57,107,0.16), 0 4px 12px rgba(0,57,107,0.10);
}
```

---

## 12-Column Grid (Layout System)

The 3-30-300 layout slots map to a 12-column CSS grid. For web implementations:

```css
.report-page {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: var(--brand-spacing-md);        /* 16px gutter */
  padding: var(--brand-spacing-xl);    /* 32px outer margin */
  background: var(--brand-color-background);
}

/* Zone 1 — 3-second KPI band: full width */
.zone-kpi-band {
  grid-column: 1 / -1;
}

/* Zone 2 — 30-second slicer bar: full width */
.zone-slicer-bar {
  grid-column: 1 / -1;
}

/* Zone 3 — 30-second drivers: three equal columns */
.zone-trend    { grid-column: span 4; }
.zone-variance { grid-column: span 4; }
.zone-ranking  { grid-column: span 4; }

/* Zone 4 — 300-second detail: full width (minus optional sidebar) */
.zone-detail-matrix { grid-column: 1 / 11; }
.zone-action-panel  { grid-column: 11 / -1; }
```

---

## Web Design Component References

The following open-source component libraries use compatible conventions (referenced in `MOCKUP_DESIGN_SPEC.md §2`):

| Library | Alignment to BrandSpec | Use |
|---|---|---|
| **Tremor** (`tremor.so`) | KPI cards, chart containers match role structure | Layout and hierarchy reference |
| **Tabler** (`tabler.io`) | Fluid grid, clean dashboard layouts | Grid system reference |
| **Flowbite / Tailwind** | 12-col grid, spacing scale (matches base-8) | Grid and spacing reference |

Map `--brand-*` variables to these libraries' CSS custom property systems or Tailwind theme extensions.

---

## References

- BrandSpec schema: `core/brand/BrandSpec.schema.yaml`
- Power BI mapping: `core/brand/tool_derivations/powerbi_mapping.md`
- Layout grid: `core/templates/page_templates/governance/Layout_Grid_System.yaml`
- Web design best practices: `products/fabric/powerbi/tooling/page_scaffold_generator/MOCKUP_DESIGN_SPEC.md §2`
- Open source themes: `products/open_source_stack/themes/`
