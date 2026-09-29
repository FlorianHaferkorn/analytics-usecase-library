# BrandSpec → Power BI Theme JSON Mapping

> **Schema:** `core/brand/BrandSpec.schema.yaml`
> **PBI theme schema:** <https://raw.githubusercontent.com/microsoft/powerbi-desktop-samples/main/Report%20Theme%20JSON%20Schema/reportThemeSchema-2.145.json>
> **Derivation tool:** `tooling/brand/derive_brand_artifacts.py` (output `products/fabric/powerbi/themes_local/brand/`) + `apply_report_theme.py`

This guide defines exactly how each BrandSpec property translates to a Power BI theme JSON property. Use it to build or validate theme generators.

---

## Theme JSON Structure

A Power BI theme JSON has three main areas:

1. **Data colors** — palette used for chart series
2. **Semantic / signal colors** — `good`, `bad`, `neutral`, `maximum`, `minimum`, `null`
3. **Visual formatting defaults** — background, foreground, fonts, table styles (via `visualStyles`)

---

## Color Mapping

| BrandSpec property | PBI theme JSON property | Notes |
|---|---|---|
| `color.primary` | `dataColors[0]` | First chart series color |
| `color.secondary` | `dataColors[1]` | Second chart series color |
| _derived palette_ | `dataColors[2..n]` | Theme generator auto-derives 6–8 colors from primary/secondary using hue rotation and lightness steps |
| `color.semantic.positive.color` | `good` | KPI card positive signal, conditional formatting |
| `color.semantic.negative.color` | `bad` | KPI card negative signal, conditional formatting |
| `color.semantic.neutral.color` | `neutral` | Neutral/no-signal state |
| `color.semantic.positive.color` (lighter) | `maximum` | Upper bound in heat maps |
| `color.semantic.negative.color` (lighter) | `minimum` | Lower bound in heat maps |
| `color.neutral_scale["100"]` | `background` | Default visual background |
| `color.neutral_scale["900"]` | `foreground` | Default text / foreground color |
| `color.primary` (10% opacity) | `tableAccent` | Table row stripe / accent |
| `color.neutral_scale["200"]` | border/separator colors (via `visualStyles`) | |

### Data Colors — Derivation Rule

The theme generator derives the full `dataColors` array from `primary` and `secondary`:

```
dataColors[0]  = primary                          # Brand primary
dataColors[1]  = secondary                        # Brand secondary
dataColors[2]  = primary, lightness +20%          # Primary tint
dataColors[3]  = secondary, lightness +20%        # Secondary tint
dataColors[4]  = primary, hue +30°               # Analogous
dataColors[5]  = secondary, hue -30°             # Complementary
dataColors[6]  = primary, lightness -20%          # Primary shade
dataColors[7]  = secondary, lightness -20%        # Secondary shade
```

For `Monochromatic` concept: all derived from primary only (saturation and lightness steps).
For `Divergent` concept: primary at one pole, secondary at other, neutral grey midpoint.

---

## Typography Mapping

Report-wide fonts are set by the four primary **text classes** (`textClasses.callout`, `title`,
`header`, `label`); the secondary classes derive from them. `visualStyles` then overrides
single visual types, each card as `[{"<propertyName>": <value>}]`
([Create custom report themes](https://learn.microsoft.com/power-bi/create-reports/report-themes-create-custom), checked 29.09.2026).

A custom theme layers on top of the report's base theme; anything it leaves out comes from
the base theme. New reports start on the **Fluent 2** base theme since August 2026, generated
ALUCA reports pin `CY25SU10`
([Visual defaults](https://learn.microsoft.com/power-bi/create-reports/power-bi-reports-visual-defaults)).
The derivation therefore always writes all four primary text classes, so the brand font does
not depend on which base theme a report has (`tooling/tests/test_pbi_theme_base_independence.py`).

| BrandSpec property | PBI theme approach | Notes |
|---|---|---|
| `typography.font_family.primary` | `textClasses.{callout,title,header,label}.fontFace` + `fontFamily` in the `visualStyles` overrides | Colour of all four classes: `color.neutral_scale["900"]` |
| `typography.tool_minimums.powerbi.body_pt` | `textClasses.title`/`header` and `fontSize` in `textbox`, `tableEx`, `matrix` | Minimum 12pt for body |
| `typography.tool_minimums.powerbi.label_pt` | `textClasses.label` and `fontSize` in axis labels, legend | Minimum 10pt |
| `typography.tool_minimums.powerbi.kpi_pt` | `textClasses.callout` and `fontSize` in `cardVisual` callout value | Minimum 18pt |

### Font Size Conversion

`rem → pt` for Power BI (PBI uses 12px = 1rem as base):

| Scale step | rem | pt (rem × 9) | PBI minimum override |
|---|---|---|---|
| `xs` | 0.625 | 5.6pt → **10pt** (minimum) | 10pt |
| `sm` | 0.75  | 6.75pt → **10pt** (minimum) | 10pt |
| `md` | 0.875 | 7.9pt → **12pt** (minimum) | 12pt |
| `lg` | 1.0   | 9pt → **12pt** (minimum) | 12pt |
| `xl` | 1.25  | 11.25pt → **12pt** | 12pt |
| `2xl` | 1.5  | 13.5pt | 14pt |
| `3xl` | 2.0  | 18pt | 18pt |

> **Canvas scale compensation:** When using `powerbi_production` canvas (1920×1080), add `font_size_delta_pt: +2` to all sizes above (as defined in BrandSpec `canvas_profiles`).

---

## Canvas Profile → PBI Page Settings

| BrandSpec canvas profile | PBI page JSON properties |
|---|---|
| `powerbi_design_base` (1280×720) | `"width": 1280, "height": 720, "displayOption": "FitToPage"` |
| `powerbi_production` (1920×1080) | `"width": 1920, "height": 1080, "displayOption": "FitToPage"` |

`FitToPage` is mandatory. Never use `ActualSize` for standard report pages (prevents scroll and ensures consistent display across screen sizes).

---

## Shape → PBI Visual Formatting

| BrandSpec property | PBI context | Mapped value |
|---|---|---|
| `border.radius.sm` (2px) | Visual border radius | Not natively supported; use 0 (no radius) |
| `border.radius.md` (4px) | Card visual border | Use `backgroundImage` workaround or ignore |
| `border.width.thin` (1px) | Visual borders | `border: { show: true, width: 1 }` |
| `border.width.medium` (2px) | Emphasis borders | `border: { show: true, width: 2 }` |

> Power BI does not support CSS border-radius on visuals natively. Use background shapes/rectangles for rounded card effects.

---

## Elevation / Shadow → PBI

Power BI does not support native box shadows on visuals. Substitute:

| Shadow level | PBI alternative |
|---|---|
| `none` | No border, no background tint |
| `low` | Thin border (1px, neutral_scale[200]) + white background |
| `medium` | Thin border + neutral_scale[100] background fill |
| `high` | Medium border + neutral_scale[100] background + z-order on top |

---

## Semantic Colors — Conditional Formatting

Power BI conditional formatting rules reference `good` and `bad` theme colors. When applying conditional formatting to KPI delta columns in Detail Matrix visuals:

- Positive delta (▲) → `color.semantic.positive.color`
- Negative delta (▼) → `color.semantic.negative.color`
- Within threshold → `color.semantic.neutral.color`
- Near threshold → `color.semantic.warning.color`

Set these in `visualStyles.cardVisual.*.*.calloutValue` and in `tableEx`/`matrix` conditional formatting rules.

---

## BPA Compliance

Generated themes must comply with `tooling/linters/powerbi/REPORT_BEST_PRACTICES.md`:

- `ENSURE_THEME_COLOURS` — no hardcoded hex in visuals; always reference theme colors
- All data series colors come from `dataColors` array, never from custom visual settings
- Semantic colors (`good`, `bad`) are set at theme level, never per-visual

---

## Example Theme JSON Skeleton

```json
{
  "name": "<BrandName>__<Concept>__<Mode>__<PrimaryHex>",
  "$schema": "https://raw.githubusercontent.com/.../reportThemeSchema-2.145.json",
  "dataColors": [
    "<primary>",
    "<secondary>",
    "<derived[2]>",
    "<derived[3]>",
    "<derived[4]>",
    "<derived[5]>",
    "<derived[6]>",
    "<derived[7]>"
  ],
  "good":        "<semantic.positive.color>",
  "bad":         "<semantic.negative.color>",
  "neutral":     "<semantic.neutral.color>",
  "maximum":     "<semantic.positive.color lightened>",
  "minimum":     "<semantic.negative.color lightened>",
  "null":        "<neutral_scale[400]>",
  "background":  "<neutral_scale[100]>",
  "foreground":  "<neutral_scale[900]>",
  "tableAccent": "<primary @ 10% opacity>",
  "visualStyles": {
    "*": {
      "*": {
        "fontFamily": [{ "value": "<typography.font_family.primary>" }]
      }
    }
  }
}
```

---

## References

- Power BI theme schema: see `$schema` URL in example above
- Theme generator implementation: Freelancing `products/pbi_theme` (canonical engine; ALUCA vendors its theme JSONs into `products/fabric/powerbi/themes/`)
- Theme application: `products/fabric/powerbi/tooling/apply_report_theme.py`
- BPA rules: `tooling/linters/powerbi/REPORT_BEST_PRACTICES.md`
- Aurora Group theme output: `showcases/aurora_group/company/Aurora_Theme_Color_Proposal.md`
