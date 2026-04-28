# Studio Token Spec — OKLCH CSS Variables

**Status:** Authoritative for the rebuild. All values extracted from the uploaded design reference (2026-04-24).

**How to read this file:**

- Tokens are exposed as **CSS custom properties** on `:root` and switched via `data-theme`, `data-density`, and `data-fonts` attributes on `<html>`.
- Accent is **dynamic** — the four `--accent*` variables are written by JavaScript from the user's tweaks (hue, chroma, lightness). All other tokens are static per theme.
- The color space is **OKLCH** exclusively. Do not introduce sRGB hex values for theme colors.

---

## 1. Theme attributes (set on `<html>`)

| Attribute | Values | Default | Purpose |
|---|---|---|---|
| `data-theme` | `dark` \| `light` | `dark` | Switches surface + ink tokens |
| `data-density` | `airy` \| `balanced` \| `dense` | `balanced` | Scales spacing + row heights |
| `data-fonts` | `inter` \| `ibm` \| `geist` \| `serif` | `inter` | Swaps `--font-display` + `--font-mono` |

These three attributes are the **only** axis of variation. Everything else is derived.

---

## 2. Static color tokens

All values are OKLCH triplets `L C H`. The slash `/` denotes alpha.

### 2.1 Dark theme (`data-theme="dark"`) — default

```css
:root[data-theme="dark"] {
  /* Surfaces (back-to-front) */
  --bg:         oklch(0.18 0.01 260);   /* app background */
  --bg-2:       oklch(0.22 0.01 260);   /* recessed, kbd, tracks */
  --panel:      oklch(0.24 0.01 260);   /* cards, modals, dropdowns */
  --panel-2:    oklch(0.27 0.01 260);   /* hovered cards, nested panels */

  /* Ink (text, foreground) */
  --ink:        oklch(0.96 0.005 260);  /* primary text */
  --ink-2:      oklch(0.86 0.005 260);  /* secondary text */
  --ink-3:      oklch(0.68 0.005 260);  /* tertiary / muted */
  --ink-4:      oklch(0.52 0.005 260);  /* hints, disabled */

  /* Lines + hover */
  --line:       oklch(0.30 0.01 260);   /* 1px borders */
  --line-2:     oklch(0.26 0.01 260);   /* divider-weight borders */
  --hover:      oklch(0.28 0.01 260 / 0.6);

  /* Shadows (dark-optimized) */
  --shadow-sm:  0 1px 2px oklch(0 0 0 / 0.35);
  --shadow-md:  0 4px 12px oklch(0 0 0 / 0.40);
  --shadow-lg:  0 12px 28px oklch(0 0 0 / 0.50);
}
```

### 2.2 Light theme (`data-theme="light"`)

```css
:root[data-theme="light"] {
  --bg:         oklch(0.985 0.003 260);
  --bg-2:       oklch(0.965 0.003 260);
  --panel:      oklch(1 0 0);
  --panel-2:    oklch(0.975 0.003 260);

  --ink:        oklch(0.18 0.01 260);
  --ink-2:      oklch(0.34 0.01 260);
  --ink-3:      oklch(0.52 0.008 260);
  --ink-4:      oklch(0.68 0.005 260);

  --line:       oklch(0.90 0.005 260);
  --line-2:     oklch(0.93 0.004 260);
  --hover:      oklch(0.94 0.005 260 / 0.8);

  --shadow-sm:  0 1px 2px oklch(0 0 0 / 0.06);
  --shadow-md:  0 4px 12px oklch(0 0 0 / 0.08);
  --shadow-lg:  0 12px 28px oklch(0 0 0 / 0.12);
}
```

---

## 3. Semantic color tokens (both themes)

These are **stable across themes** — values don't change between dark and light. They describe meaning, not hue.

```css
:root {
  --positive:        oklch(0.60 0.15 150);   /* favourable delta, certified */
  --positive-soft:   oklch(0.92 0.06 150 / 0.5);
  --negative:        oklch(0.55 0.18 25);    /* unfavourable delta, blocked */
  --negative-soft:   oklch(0.93 0.07 25 / 0.5);
  --warn:            oklch(0.70 0.15 75);    /* review, caution */
  --warn-soft:       oklch(0.94 0.06 75 / 0.6);
  --neutral:         oklch(0.62 0.02 260);   /* no-delta, info */
}
```

**Usage rule:** a favourable delta is `--positive` only when polarity + direction agree:
- `up + higher_is_better` → positive
- `down + lower_is_better` → positive
- otherwise → `--negative`

Copied from `Report_Templates.html` KPI card logic (preserve exactly).

---

## 4. Accent tokens (JS-driven)

These three variables are **written at runtime** by the shell based on the user's accent-hue slider (Settings panel). Do **not** set them statically.

```js
// src/app/(studio)/layout.tsx or an equivalent client effect
const L = tweaks.accentLightness ?? 0.62;
const C = tweaks.accentChroma    ?? 0.13;
const H = tweaks.accentHue       ?? 250;          // Indigo default

root.style.setProperty('--accent',      `oklch(${L} ${C} ${H})`);
root.style.setProperty('--accent-soft', `oklch(${L} ${C} ${H} / 0.14)`);
root.style.setProperty('--accent-ink',
  tweaks.theme === 'dark' ? `oklch(0.12 0.02 ${H})` : `oklch(0.98 0.01 ${H})`);
```

**Preset hue palette** (mirrors the Settings swatch grid):

| Name      | H   | C    | L    |
|-----------|-----|------|------|
| Indigo    | 250 | 0.13 | 0.62 |
| Emerald   | 150 | 0.13 | 0.62 |
| Amber     | 75  | 0.13 | 0.62 |
| Rose      | 20  | 0.13 | 0.62 |
| Violet    | 290 | 0.13 | 0.62 |
| Teal      | 190 | 0.13 | 0.62 |
| Graphite  | 250 | 0.01 | 0.38 |

Fine-tune slider: hue 0–360°, step 1. Chroma + lightness stay at preset values unless the user drags the Graphite (monochrome) preset.

---

## 5. Density

`data-density` scales spacing and row heights. Tailwind v4 `@theme` block:

```css
@theme {
  --spacing-density-airy:     1.25;
  --spacing-density-balanced: 1.0;
  --spacing-density-dense:    0.8;

  --row-height-airy:     44px;
  --row-height-balanced: 36px;
  --row-height-dense:    30px;
}

[data-density="airy"]     { --row: var(--row-height-airy);     --pad: 16px; }
[data-density="balanced"] { --row: var(--row-height-balanced); --pad: 12px; }
[data-density="dense"]    { --row: var(--row-height-dense);    --pad: 8px;  }
```

- Tables use `--row` for `<tr>` height.
- Cards use `--pad` for inner padding.
- Sidebar collapsed/expanded widths do **not** change with density (fixed at 68 / 248 px, matches mockup).

---

## 6. Font pairings

`data-fonts` selects the pairing. Load all four via `next/font` (tree-shaking keeps this cheap).

```css
[data-fonts="inter"] {
  --font-display: 'Inter', ui-sans-serif, system-ui, sans-serif;
  --font-body:    'Inter', ui-sans-serif, system-ui, sans-serif;
  --font-mono:    'JetBrains Mono', ui-monospace, 'SFMono-Regular', monospace;
}
[data-fonts="ibm"] {
  --font-display: 'IBM Plex Sans', system-ui, sans-serif;
  --font-body:    'IBM Plex Sans', system-ui, sans-serif;
  --font-mono:    'IBM Plex Mono', ui-monospace, monospace;
}
[data-fonts="geist"] {
  --font-display: 'Geist', system-ui, sans-serif;
  --font-body:    'Geist', system-ui, sans-serif;
  --font-mono:    'Geist Mono', ui-monospace, monospace;
}
[data-fonts="serif"] {
  --font-display: 'Instrument Serif', ui-serif, serif;
  --font-body:    'Inter', ui-sans-serif, system-ui, sans-serif;
  --font-mono:    'JetBrains Mono', ui-monospace, monospace;
}
```

**Rule:** headings (H1–H3) and brand mark use `--font-display`; body text and UI use `--font-body`; numeric data, tokens, code, kbd chips use `--font-mono`.

---

## 7. Radius, motion, z-index

```css
:root {
  --radius-sm: 4px;    /* pills, chips */
  --radius-md: 7px;    /* buttons, inputs */
  --radius-lg: 12px;   /* panels, modals */
  --radius-xl: 16px;   /* hero cards */

  --motion-fast:    120ms;
  --motion-normal:  240ms;
  --motion-slow:    420ms;
  --ease-standard:  cubic-bezier(.2,.8,.2,1);  /* used by sidebar collapse */

  --z-sidebar:      20;
  --z-topbar:       30;
  --z-dropdown:     50;
  --z-tweaks:       80;   /* only exists in Report Templates tool */
  --z-modal:        90;   /* Wizard, Settings, Command Palette */
  --z-toast:        100;
}
```

---

## 8. Contrast verification (WCAG)

Run the contrast check in CI as part of Phase 1 acceptance. Targets:

| Pair | Required | Dark theme | Light theme |
|---|---|---|---|
| `--ink` on `--bg` | ≥ 7:1 (AAA body) | pass | pass |
| `--ink-2` on `--bg` | ≥ 4.5:1 (AA body) | pass | pass |
| `--ink-3` on `--bg` | ≥ 4.5:1 (AA body) | pass | pass |
| `--ink-4` on `--bg` | ≥ 3:1 (AA large only) | **limit** | **limit** |
| `--accent-ink` on `--accent` | ≥ 4.5:1 | pass for all preset hues | pass |
| `--positive` / `--negative` / `--warn` on `--panel` | ≥ 3:1 (icon) | pass | pass |

If a preset hue fails contrast in one theme, adjust `--accent-ink` (keep body-text ink unchanged).

---

## 9. Data Series Palette

8-Farben-Palette für Chart-Rendering. OKLCH-Werte sind Konvertierungen der Microsoft Fluent UI Palette aus dem ursprünglichen Mockup (`docs/rebuild/MOCKUP_REFERENCE/tokens.js` Zeile 15).

```css
:root {
  --data-1: oklch(0.60 0.20 243.5);  /* Indigo — formerly #0078D4 */
  --data-2: oklch(0.90 0.14 203.6);  /* Cyan — formerly #50E6FF */
  --data-3: oklch(0.59 0.16 276.1);  /* Violet — formerly #8661C5 */
  --data-4: oklch(0.64 0.26 77.6);   /* Orange — formerly #F7630C */
  --data-5: oklch(0.58 0.11 169.3);  /* Teal — formerly #008575 */
  --data-6: oklch(0.56 0.23 344.1);  /* Magenta — formerly #E3008C */
  --data-7: oklch(0.65 0.17 58.5);   /* Coral — formerly #EF6950 */
  --data-8: oklch(0.82 0.34 104.1);  /* Gold — formerly #FFB900 */
}
```

**Rationale:** Das Mockup nutzt statische HEX-Werte für Datenserien (nicht theme-abhängig). Phase-1-Token nutzen OKLCH durchgängig für Konsistenz. Datenserien sind kategorial (keine semantische Bedeutung wie positive/negative), daher werden die 8 Farben als statische OKLCH-Werte deklariert — nicht über Theme-Switching variiert. Die gleichen Werte gelten für Light und Dark Theme.

**Verwendung in Charts:**
- Reihe 1 → `var(--data-1)`
- Reihe 2 → `var(--data-2)`
- …
- Reihen > 8: Fallback auf modulo-8 oder Gradient-basierte Erweiterung

**Tailwind-Mapping:** Die Farben sind via `--color-data-1` bis `--color-data-8` in der `@theme`-Sektion zugänglich (z.B. `bg-data-1`, `text-data-3`).

---

## 10. Tailwind v4 mapping

Map Tailwind utility classes to the tokens above so existing `text-foreground`, `bg-background`, etc. work:

```css
@theme {
  --color-background:         var(--bg);
  --color-background-muted:   var(--bg-2);
  --color-foreground:         var(--ink);
  --color-foreground-muted:   var(--ink-2);
  --color-foreground-subtle:  var(--ink-3);
  --color-border:             var(--line);
  --color-border-subtle:      var(--line-2);
  --color-panel:              var(--panel);
  --color-panel-elevated:     var(--panel-2);
  --color-accent:             var(--accent);
  --color-accent-soft:        var(--accent-soft);
  --color-accent-ink:         var(--accent-ink);
  --color-positive:           var(--positive);
  --color-negative:           var(--negative);
  --color-warn:               var(--warn);

  --font-display:             var(--font-display);
  --font-body:                var(--font-body);
  --font-mono:                var(--font-mono);

  --radius:                   var(--radius-md);
  --radius-lg:                var(--radius-lg);
}
```

---

## 11. Do / Don't

- **Do** read any color via `var(--…)` or Tailwind utility — never hard-code OKLCH in components.
- **Do** put all theme logic in `src/styles/tokens.css`, imported once from `app/layout.tsx`.
- **Don't** introduce new surface levels (`--bg-3`, `--panel-3`). If you feel the need, it's a missing primitive — open a discussion with Flo.
- **Don't** use `hsl()` or hex for theme colors. OKLCH only.
- **Don't** write tokens inline on components. Tokens live in one file.
