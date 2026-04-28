# Typography & Spacing Specification
## Source of Truth: MOCKUP_REFERENCE

> Generated 2026-04-28 from reading all six mockup source files and the ten Phase-1 implementation files.
> "Mockup" = values extracted literally from `Studio.html` CSS `:root`, `shell.jsx`, `library.jsx`, `detail.jsx`, and `primitives.jsx`.
> "Phase-1-Ist" = values found in `tokens.css`, `globals.css`, `Sidebar.tsx`, `LibraryTabs.tsx`, `MetricsTable.tsx`, and `library-client.tsx`.

---

## 1. Font Tokens

### 1a. Font Families

The mockup declares fonts via Google Fonts + CSS variables. Three pairing presets exist:

| Preset | `--font-ui` / `--font-display` | `--font-mono` | Active default |
|---|---|---|---|
| `inter` (default) | `"Inter", system-ui, -apple-system, sans-serif` | `"JetBrains Mono", ui-monospace, monospace` | ✓ (no `data-fonts` attr = inter) |
| `ibm` | `"IBM Plex Sans", sans-serif` | `"IBM Plex Mono", monospace` | — |
| `geist` | `"Geist", sans-serif` | `"Geist Mono", monospace` | ✓ (`__TWEAKS__.fontPairing: "geist"`) **PRIMÄR** |
| `serif` | `"Inter"` (ui) + `"Instrument Serif"` (display) | `"JetBrains Mono", monospace` | — |

> **Note:** `window.__TWEAKS__` defaults to `fontPairing: "geist"` in `Studio.html`, so the rendered mockup uses **Geist / Geist Mono**.
> Phase-1 `tokens.css` defaults to `Inter / JetBrains Mono` and mirrors the same four `[data-fonts]` overrides. The variable names and preset structure are **identical** — no delta.

| Element | Mockup family (active) | Phase-1-Ist family | Delta |
|---|---|---|---|
| Body / UI text | `"Geist"` (via `var(--font-ui)`) | `"Inter"` (default `:root`) | **Different default** — both support Geist via `[data-fonts="geist"]`; needs `data-fonts` attr set at runtime |
| Display headings (`.display`) | `"Geist"` (via `var(--font-display)`) | `"Inter"` (default `:root`) | Same delta as above |
| Monospace / code (`.mono`) | `"Geist Mono"` (tweaks active) | `"JetBrains Mono"` (default `:root`) | Same delta; both support Geist Mono via `[data-fonts="geist"]` |

---

### 1b. Font Sizes, Weights, Line-Heights, Letter-Spacings per Hierarchy Level

All values are inline px/em from JSX (no Tailwind class abstraction in mockup).
Phase-1 uses Tailwind utility classes; pixel equivalents shown in parentheses (Tailwind v4 default scale, `1rem = 16px`).

| Element | Mockup Size | Mockup Weight | Mockup Line-Height | Mockup Letter-Spacing | Phase-1-Ist | Delta |
|---|---|---|---|---|---|---|
| **Page title (h1) — Library** | `28px` (`fontSize: 28`) | `500` | default (~1.2) | `-0.02em` | `text-2xl` = 24px, `font-semibold` = 600 | **−4px size; +100 weight; spacing missing** |
| **Detail h1 (metric name)** | `36px` | `500` | default | `-0.025em` | not yet implemented | — |
| **KPI value / large number** | `24px` (KpiCard) · `48px` (Detail overview) | `700` (KpiCard) · `500` (Detail) | `1.05` (KpiCard) | `-0.5px` / `-0.03em` | not yet implemented | — |
| **Card title (h3-equivalent)** | `11px` (primitives Card title) · `13px` (primitives ActionPanel) | `600` | `1.2` | — | — | — |
| **Body / default text** | `13px` (shell, library rows, detail body) | `400` | ~1.4–1.6 | default | `text-sm` = 14px | **+1px (14 vs 13)** |
| **Body description** | `14.5px` (detail description) | `400` | `1.6` | — | `text-sm` = 14px | **−0.5px** |
| **Small / caption** | `11px` (brand subtitle, footer user role, table count badge) | `400–500` | `1.1` | — | `text-2xs` (undefined in standard Tailwind; custom) | needs verification |
| **Extra-small / meta** | `10.5px` (nav section header, KBD label) | `500` | — | `0.08em` (uppercase labels) | `text-2xs` | needs verification |
| **Code / mono inline (`.mono`)** | `0.82em` of parent | `inherit` | `0` letter-spacing | — | `0.82em` | **Match** |
| **Pre / code block** | `12.5px`, `lineHeight: 1.7` | `400` | `1.7` | — | not yet in Phase-1 | — |
| **Button / label** | `13px` (primary CTA "Ask Studio", "New element") | `500` | — | — | `text-xs` = 12px | **−1px** |
| **Tab label (active/inactive)** | `13px` | `500` (active) / `400` (inactive) | — | — | `text-xs` = 12px | **−1px** |
| **Table header (th)** | `11px`, uppercase | `500` | — | `0.06em` | `text-2xs`, `font-semibold` (600), uppercase | **+100 weight; spacing missing** |
| **Table body (td)** | `13px` | `400` (body) / `500` (name col) | — | — | `text-sm` = 14px | **+1px** |
| **Nav section header** | `10.5px`, uppercase | `500` | — | `0.08em` | `text-2xs font-medium` | spacing missing |
| **Pill / badge label** | `11.5px` | `500` | — | `-0.005em` | not yet implemented as component | — |
| **KBD shortcut** | `10.5px` | `500` | — | — | `text-2xs font-mono` | needs pixel check |
| **Breadcrumb** | `13px` | `400`/`500` (active segment) | — | — | `text-sm` = 14px | **+1px** |

> **Primär-Empfehlung für Body/UI-Text**: `13px` (mockup uses `13` consistently for interactive rows, buttons, nav items). Phase-1 Tailwind `text-sm = 14px` is uniformly 1px too large for these elements.

---

## 2. Spacing Tokens (Grid)

### 2a. Mockup Grid Definition (`tokens.js`)

```
canvas: 1280 × 720
outer:   32px  (viewport-edge to first content column)
gutter:  16px  (between logical-unit columns)
pad:      8px  (inner card padding base unit)
zoneGap: 40px  (between top-level page zones/sections)
luW: (1280 - 64 - 11×16) / 12 ≈ 86.67px  (logical-unit width)
luH:  (720 - 64 - 11×16) / 12 ≈ 39.67px  (logical-unit height)
```

### 2b. Mockup CSS Variable Tokens (`Studio.html` `:root`)

| CSS Variable | Mockup Default | Airy | Balanced | Dense | Phase-1 Equivalent | Delta |
|---|---|---|---|---|---|---|
| `--pad` | `24px` | `28px` | `20px` | `16px` | `--pad` = `16px` (airy) / `12px` (balanced) / `8px` (dense) | **Phase-1 airy = 16px vs mockup airy = 28px: −12px** |
| `--gap` | `24px` | `28px` | `18px` | `14px` | not declared as standalone token | **Missing** |
| `--h-row` | `44px` | `48px` | `40px` | `36px` | `--row-height-airy: 44px` / `--row-height-balanced: 36px` / `--row-height-dense: 30px` | balanced: 36 vs 40 (**−4px**); dense: 30 vs 36 (**−6px**) |
| `--radius` | `10px` | — | — | — | `--radius-md: 7px` (maps to `--radius`) | **−3px** |

> The mockup `--pad` default (non-density) is `24px`; Phase-1 does not define a non-density default for `--pad` — it only exists inside `[data-density]` blocks.

### 2c. Density Variants Comparison

| Density Mode | `--pad` Mockup | `--pad` Phase-1 | `--gap` Mockup | `--gap` Phase-1 | `--h-row` Mockup | `--h-row` Phase-1 |
|---|---|---|---|---|---|---|
| airy | `28px` | `16px` | `28px` | n/a | `48px` | `44px` |
| balanced (default) | `20px` | `12px` | `18px` | n/a | `40px` | `36px` |
| dense | `16px` | `8px` | `14px` | n/a | `36px` | `30px` |

---

## 3. Component-Level Spacing

### 3a. Sidebar

| Property | Mockup Value | Source | Phase-1-Ist | Source | Delta |
|---|---|---|---|---|---|
| Width expanded | `248px` | `shell.jsx` | `248px` | `Sidebar.tsx` style | **Match** |
| Width collapsed | `68px` | `shell.jsx` | `68px` | `Sidebar.tsx` style | **Match** |
| Header (brand) height | `56px` | `shell.jsx` `height: 56` | `h-14` = 56px | `Sidebar.tsx` | **Match** |
| Header horizontal padding | `0 16px` | `shell.jsx` `padding: "0 16px"` | `px-4` = 16px | `Sidebar.tsx` | **Match** |
| Header border | `1px solid var(--line-2)` | `shell.jsx` | `border-b border-border-subtle` | `Sidebar.tsx` | **Match** |
| Logo mark size | `26 × 26px` | `shell.jsx` | `w-6.5 h-6.5` = 26px | `Sidebar.tsx` | **Match** |
| Logo mark radius | `7px` | `shell.jsx` | `rounded-md` = ~6px (Tailwind default) | `Sidebar.tsx` | **~−1px** (minor) |
| Brand name font size | `13.5px` | `shell.jsx` | `text-xs` = 12px + `font-display` | `Sidebar.tsx` | **−1.5px** |
| Brand name font weight | `600` | `shell.jsx` | `font-semibold` = 600 | `Sidebar.tsx` | **Match** |
| Brand name letter-spacing | `-0.01em` | `shell.jsx` | not set | `Sidebar.tsx` | **Missing** |
| Brand subtitle font size | `11px` | `shell.jsx` | `text-2xs` (custom) | `Sidebar.tsx` | needs verification |
| Actions section padding | `14px 12px 6px` (top/h-pad/bottom) | `shell.jsx` | `px-3 py-3.5` = 12px / 14px | `Sidebar.tsx` | **top 14px vs 14px ✓; horiz 12px vs 12px ✓; bottom 6px vs 14px (py-3.5 is symmetric) ✗** |
| "New element" button height | `34px` | `shell.jsx` | `h-8.5` = 34px | `Sidebar.tsx` | **Match** |
| "New element" button h-padding | `0 10px` | `shell.jsx` | `px-2.5` = 10px | `Sidebar.tsx` | **Match** |
| "New element" font size | `13px` | `shell.jsx` | `text-xs` = 12px | `Sidebar.tsx` | **−1px** |
| "New element" font weight | `500` | `shell.jsx` | `font-medium` = 500 | `Sidebar.tsx` | **Match** |
| Search button height | `32px` | `shell.jsx` | `h-8` = 32px | `Sidebar.tsx` | **Match** |
| Search button font size | `12.5px` | `shell.jsx` | `text-xs` = 12px | `Sidebar.tsx` | **−0.5px** |
| Nav section padding | `12px 8px` | `shell.jsx` `nav padding: "12px 8px"` | `px-2 py-3` = 8px / 12px | `Sidebar.tsx` | **Match** |
| Nav section gap (between items) | `1px` | `shell.jsx` `gap: 1` | `gap-0.25` = 1px | `Sidebar.tsx` | **Match** |
| Nav item height | `32px` | `shell.jsx` | `h-8` = 32px | `Sidebar.tsx` | **Match** |
| Nav item h-padding | `0 10px` | `shell.jsx` | `px-2.5` = 10px | `Sidebar.tsx` | **Match** |
| Nav item gap (icon + label) | `10px` | `shell.jsx` | `gap-2.5` = 10px | `Sidebar.tsx` | **Match** |
| Nav item font size | `13px` | `shell.jsx` | `text-xs` = 12px | `Sidebar.tsx` | **−1px** |
| Nav item font weight active | `500` | `shell.jsx` | `font-medium` = 500 | `Sidebar.tsx` | **Match** |
| Nav item radius | `7px` | `shell.jsx` | `rounded-lg` = 8px (Tailwind default) | `Sidebar.tsx` | **+1px** |
| Nav icon size | `15px` | `shell.jsx` `IconC size={15}` | `w-3.75 h-3.75` = 15px div placeholder | `Sidebar.tsx` | **Match (placeholder size)** |
| Active indicator: left offset | `left: -8` (absolute) | `shell.jsx` | `left: '-8px'` | `Sidebar.tsx` | **Match** |
| Active indicator: width | `2px` | `shell.jsx` | `w-0.5` = 2px | `Sidebar.tsx` | **Match** |
| Active indicator: top/bottom inset | `top: 8, bottom: 8` | `shell.jsx` | `top-2 bottom-2` = 8px | `Sidebar.tsx` | **Match** |
| Domain item height | `28px` | `shell.jsx` | `h-7` = 28px | `Sidebar.tsx` | **Match** |
| Domain item font size | `12.5px` | `shell.jsx` | `text-xs` = 12px | `Sidebar.tsx` | **−0.5px** |
| Domain color dot size | `6 × 6px` | `shell.jsx` | `w-2 h-2` = 8px | `Sidebar.tsx` | **+2px** |
| Domain color dot radius | `2px` | `shell.jsx` | `rounded` = 4px (Tailwind default) | `Sidebar.tsx` | **+2px** |
| Nav section header font size | `10.5px` | `shell.jsx` `navHeader` | `text-2xs` | `Sidebar.tsx` | needs verification |
| Nav section header letter-spacing | `0.08em` | `shell.jsx` `navHeader` | not set | `Sidebar.tsx` | **Missing** |
| Nav section header padding | `8px 10px 6px` | `shell.jsx` `navHeader` | `px-2.5 py-1.5` = 10px / 6px (symmetric) | `Sidebar.tsx` | bottom 6px vs 6px ✓; top 8px vs 6px (py-1.5 symmetric) **−2px top** |
| User footer padding | `10px 12px` | `shell.jsx` | `px-3 py-3.5` = 12px / 14px | `Sidebar.tsx` | vertical: 14px vs 10px **+4px** |
| User avatar size (expanded) | `28 × 28px` | `shell.jsx` | `w-8 h-8` = 32px | `Sidebar.tsx` | **+4px** |
| User avatar size (collapsed) | `28 × 28px` | `shell.jsx` | `w-8 h-8` = 32px | `Sidebar.tsx` | **+4px** |
| User name font size | `12.5px` | `shell.jsx` | `text-xs` = 12px | `Sidebar.tsx` | **−0.5px** |
| User role font size | `11px` | `shell.jsx` | `text-2xs` | `Sidebar.tsx` | needs verification |
| Sidebar transition duration | `240ms` | `shell.jsx` | `var(--motion-normal)` = 240ms | `Sidebar.tsx` | **Match** |
| Sidebar transition easing | `cubic-bezier(.2,.8,.2,1)` | `shell.jsx` | `var(--ease-standard)` = `cubic-bezier(0.2,0.8,0.2,1)` | `Sidebar.tsx` | **Match** |

---

### 3b. Topbar / Header

| Property | Mockup Value | Source | Phase-1-Ist | Source | Delta |
|---|---|---|---|---|---|
| Height | `56px` | `shell.jsx` `height: 56` | not yet implemented as separate component | — | — |
| Horizontal padding | `0 20px` | `shell.jsx` `padding: "0 20px"` | — | — | — |
| Gap (items) | `12px` | `shell.jsx` `gap: 12` | — | — | — |
| Breadcrumb font size | `13px` | `shell.jsx` | — | — | — |
| Search button height | `30px` | `shell.jsx` | — | — | — |
| Search button h-padding | `0 10px` | `shell.jsx` | — | — | — |
| Search button font size | `12.5px` | `shell.jsx` | — | — | — |
| Search button radius | `7px` | `shell.jsx` | — | — | — |
| Icon button size | `30 × 30px` | `shell.jsx` `iconBtn` | — | — | — |
| Icon button radius | `7px` | `shell.jsx` `iconBtn` | — | — | — |
| Primary CTA button height | `30px` | `shell.jsx` | — | — | — |
| Primary CTA h-padding | `0 12px` | `shell.jsx` | — | — | — |
| Primary CTA radius | `7px` | `shell.jsx` | — | — | — |
| Primary CTA font size | `12.5px` | `shell.jsx` | — | — | — |
| Avatar stacked overlap | `-8px` margin-left | `shell.jsx` | — | — | — |
| Avatar border (stacked) | `2px solid var(--bg)` | `shell.jsx` | — | — | — |

---

### 3c. Library Tab-Bar

| Property | Mockup Value | Source | Phase-1-Ist | Source | Delta |
|---|---|---|---|---|---|
| Container gap (between tabs) | `2px` | `library.jsx` `gap: 2` | `gap-1` = 4px | `LibraryTabs.tsx` | **+2px** |
| Container bottom border | `1px solid var(--line)` | `library.jsx` | `border-b border-border` | `LibraryTabs.tsx` | **Match** |
| Container margin-bottom | `16px` | `library.jsx` `marginBottom: 16` | `mb-4` = 16px | `LibraryTabs.tsx` | **Match** |
| Tab h-padding | `14px` | `library.jsx` `padding: "10px 14px"` | `px-3.5` = 14px | `LibraryTabs.tsx` | **Match** |
| Tab v-padding | `10px` | `library.jsx` | `py-2.5` = 10px | `LibraryTabs.tsx` | **Match** |
| Tab font size | `13px` | `library.jsx` `fontSize: 13` | `text-xs` = 12px | `LibraryTabs.tsx` | **−1px** |
| Tab font weight active | `500` | `library.jsx` | `font-medium` = 500 | `LibraryTabs.tsx` | **Match** |
| Tab font weight inactive | `400` | `library.jsx` | `font-medium` = 500 (class applied to all) | `LibraryTabs.tsx` | **+100 weight (should be 400 inactive)** |
| Tab gap (icon + label) | `8px` | `library.jsx` `gap: 8` | `gap-2` = 8px | `LibraryTabs.tsx` | **Match** |
| Active underline thickness | `1.5px` | `library.jsx` `borderBottom: "1.5px solid..."` | `2px` | `LibraryTabs.tsx` inline style | **+0.5px** |
| Active underline color | `var(--accent)` | `library.jsx` | `var(--accent)` | `LibraryTabs.tsx` | **Match** |
| Inactive underline | `transparent` | `library.jsx` | `transparent` | `LibraryTabs.tsx` | **Match** |
| Tab count badge font size | `10.5px` | `library.jsx` `.mono fontSize: 10.5` | `text-2xs font-mono` | `LibraryTabs.tsx` | needs `text-2xs` px check |
| Tab count badge color | `var(--ink-4)` | `library.jsx` | opacity 0.7 via style | `LibraryTabs.tsx` | **Different approach (opacity vs explicit color)** |
| Negative margin-bottom (underline alignment) | `-1px` | `library.jsx` `marginBottom: -1` | `style marginBottom: '-2px'` | `LibraryTabs.tsx` | **−1px difference** |

---

### 3d. Metrics Table Row

| Property | Mockup Value | Source | Phase-1-Ist | Source | Delta |
|---|---|---|---|---|---|
| Cell v-padding | `14px` | `library.jsx` `tdStyle padding: "14px var(--pad)"` | `py-3` = 12px | `MetricsTable.tsx` | **−2px** |
| Cell h-padding | `var(--pad)` = 24px (default) | `library.jsx` | `px-4` = 16px | `MetricsTable.tsx` | **−8px** |
| Row font size | `13px` (tableStyle) | `library.jsx` | `text-sm` = 14px (table) / `text-xs` = 12px (td cells) | `MetricsTable.tsx` | **mixed: +1px or −1px depending on cell** |
| Name cell weight | `500` | `library.jsx` | `font-medium` = 500 | `MetricsTable.tsx` | **Match** |
| Ref/mono cell font | `var(--font-mono)`, `.mono` class | `library.jsx` | `font-mono` + `text-2xs` | `MetricsTable.tsx` | **Match** |
| Row divider | `1px solid var(--line-2)` | `library.jsx` `tdStyle borderBottom` | `divide-y divide-border` | `MetricsTable.tsx` | **Slightly different — divide-border = --line; mockup uses --line-2 (lighter)** |
| Row hover | transition 120ms | `library.jsx` `rowStyle` | `hover:bg-hover transition-colors` | `MetricsTable.tsx` | **Match** |
| Header cell v-padding | `12px` | `library.jsx` `thStyle padding: "12px var(--pad)"` | `py-2.5` = 10px | `MetricsTable.tsx` | **−2px** |
| Header cell h-padding | `var(--pad)` = 24px | `library.jsx` | `px-4` = 16px | `MetricsTable.tsx` | **−8px** |
| Header font size | `11px` | `library.jsx` `thStyle fontSize: 11` | `text-2xs` | `MetricsTable.tsx` | needs `text-2xs` px check |
| Header font weight | `500` | `library.jsx` | `font-semibold` = 600 | `MetricsTable.tsx` | **+100 weight** |
| Header letter-spacing | `0.06em` | `library.jsx` | not set | `MetricsTable.tsx` | **Missing** |
| Header text-transform | `uppercase` | `library.jsx` | `uppercase` | `MetricsTable.tsx` | **Match** |
| Header border-bottom | `1px solid var(--line)` | `library.jsx` | `border-b border-border` | `MetricsTable.tsx` | **Match** |

---

### 3e. Library Client (Search / Filter Area)

| Property | Mockup Value | Source | Phase-1-Ist | Source | Delta |
|---|---|---|---|---|---|
| Search bar height | `34px` | `library.jsx` `height: 34` | py-2 + content ≈ ~36px | `library-client.tsx` | **~+2px** |
| Search bar h-padding | `0 12px` | `library.jsx` | `px-3` = 12px | `library-client.tsx` | **Match** |
| Search bar v-padding | explicit height 34 | `library.jsx` | `py-2` = 8px each | `library-client.tsx` | different approach |
| Search bar gap | `10px` | `library.jsx` `gap: 10` | `gap-2.5` = 10px | `library-client.tsx` | **Match** |
| Search bar border | `1px solid var(--line)` | `library.jsx` | `border border-border` | `library-client.tsx` | **Match** |
| Search bar radius | `8px` | `library.jsx` `borderRadius: 8` | `rounded-lg` = 8px | `library-client.tsx` | **Match** |
| Search bar background | `var(--panel)` | `library.jsx` | `bg-panel` | `library-client.tsx` | **Match** |
| Search input font size | `13px` | `library.jsx` `fontSize: 13` | `text-sm` = 14px | `library-client.tsx` | **+1px** |
| Filter row gap | `8px` | `library.jsx` `gap: 8` | `gap-3` = 12px | `library-client.tsx` | **+4px** |
| Filter row margin-bottom | `14px` | `library.jsx` `marginBottom: 14` | `mb-4` = 16px | `library-client.tsx` | **+2px** |
| Header margin-bottom | `20px` | `library.jsx` `marginBottom: 20` | `mb-6` = 24px | `library-client.tsx` | **+4px** |
| Page h-padding (max-width container) | `var(--pad)` = 24px | `library.jsx` `padding: "var(--pad)"` | max-w-5xl mx-auto (no explicit pad) | `library-client.tsx` | **Missing outer padding** |
| Library page title font size | `28px` | `library.jsx` | `text-2xl` = 24px | `library-client.tsx` | **−4px** |
| Library page title weight | `500` | `library.jsx` | `font-semibold` = 600 | `library-client.tsx` | **+100 weight** |
| Library page title letter-spacing | `-0.02em` | `library.jsx` | not set | `library-client.tsx` | **Missing** |
| Library subtitle font size | `13px` | `library.jsx` `fontSize: 13` | `text-sm` = 14px | `library-client.tsx` | **+1px** |

---

### 3f. Detail View

| Property | Mockup Value | Source | Phase-1-Ist | Delta |
|---|---|---|---|---|
| Content max-width | `900px` | `detail.jsx` `maxWidth: 900` | not yet implemented | — |
| Content padding | `var(--pad)` = 24px | `detail.jsx` | — | — |
| h1 font size | `36px` | `detail.jsx` | — | — |
| h1 font weight | `500` | `detail.jsx` | — | — |
| h1 letter-spacing | `-0.025em` | `detail.jsx` | — | — |
| Description font size | `14.5px` | `detail.jsx` | — | — |
| Description line-height | `1.6` | `detail.jsx` | — | — |
| Description margin-top | `12px` | `detail.jsx` | — | — |
| Tab area margin-top | `22px` | `detail.jsx` | — | — |
| Tab area margin-bottom | `20px` | `detail.jsx` | — | — |
| Card inner padding | `var(--pad)` = 24px | `detail.jsx` | — | — |
| Card head padding-v | `14px` (extended) / default 8px | `detail.jsx` | — | — |
| Right rail width | `300px` | `detail.jsx` | — | — |
| Right rail padding | `var(--pad)` = 24px | `detail.jsx` | — | — |
| Comment card padding | `14px var(--pad)` | `detail.jsx` | — | — |
| History row padding | `12px var(--pad)` | `detail.jsx` | — | — |
| Prop row grid | `90px 1fr` | `detail.jsx` | — | — |
| Prop label font size | `11.5px` | `detail.jsx` | — | — |
| Latest value display | `48px`, weight 500, spacing `-0.03em` | `detail.jsx` | — | — |
| AI panel padding | `14px` | `detail.jsx` | — | — |
| AI panel radius | `10px` | `detail.jsx` | — | — |
| Section heading (Properties) | `11px`, uppercase, spacing `0.08em` | `detail.jsx` | — | — |

---

### 3g. Command Palette / Modal

| Property | Mockup Value | Source | Phase-1-Ist | Delta |
|---|---|---|---|---|
| Modal max-width | `640px` | `shell.jsx` `width: 640` | not yet implemented | — |
| Modal radius | `12px` | `shell.jsx` `borderRadius: 12` | — | — |
| Modal backdrop | `rgba(11,11,12,0.35)` + `blur(4px)` | `shell.jsx` | — | — |
| Modal padding-top (viewport) | `14vh` | `shell.jsx` | — | — |
| Search input padding | `14px 18px` | `shell.jsx` | — | — |
| Search input font size | `14px` | `shell.jsx` `fontSize: 14` | — | — |
| Search area gap | `12px` | `shell.jsx` | — | — |
| Result list max-height | `420px` | `shell.jsx` | — | — |
| Result list padding | `8px` | `shell.jsx` `padding: 8` | — | — |
| Result row padding | `8px 10px` | `shell.jsx` `paletteRow` | — | — |
| Result row gap | `10px` | `shell.jsx` | — | — |
| Result row font size | `13px` | `shell.jsx` | — | — |
| Result row radius | `7px` | `shell.jsx` | — | — |
| Section header font size | `10.5px` | `shell.jsx` `paletteHeader` | — | — |
| Section header letter-spacing | `0.08em` | `shell.jsx` | — | — |

---

### 3h. Card Component (from `primitives.jsx`)

| Property | Mockup Value | Phase-1-Ist | Delta |
|---|---|---|---|
| Card radius | `4px` | `--radius-sm: 4px` defined; component usage TBD | — |
| Card border | `0.5px solid var(--border)` | `border border-border` = 1px | **+0.5px** |
| Card title font size | `11px` | — | — |
| Card title weight | `600` | — | — |
| Card title padding | `8px 10px 4px` | — | — |
| Card body padding | `4px 10px 8px` | — | — |
| KPI card padding | `10px 12px` | — | — |
| KPI card gap (rows) | `2px` | — | — |
| KPI label font size | `10px` | — | — |
| KPI label weight | `500` | — | — |
| KPI label letter-spacing | `0.1px` | — | — |
| KPI value font | `"JetBrains Mono", monospace` | — | — |
| KPI value font size | `24px` | — | — |
| KPI value weight | `700` | — | — |
| KPI value line-height | `1.05` | — | — |
| KPI value letter-spacing | `-0.5px` | — | — |
| KPI delta font size | `11px` | — | — |
| KPI delta weight | `600` | — | — |
| KPI period font size | `10px` | — | — |
| KPI period weight | `400` | — | — |

---

## 4. CSS Variable Summary: Mockup vs Phase-1

| Variable | Mockup Studio.html (light `:root`) | Phase-1 tokens.css (dark `:root` default) | Notes |
|---|---|---|---|
| `--bg` | `#fafaf9` | `oklch(0.18 0.01 260)` ≈ very dark | **Phase-1 defaults dark; mockup defaults light** |
| `--bg-2` | `#f4f4f2` | `oklch(0.22 0.01 260)` | same inversion |
| `--panel` | `#ffffff` | `oklch(0.24 0.01 260)` | same |
| `--ink` | `#0b0b0c` | `oklch(0.96 0.005 260)` ≈ near-white | inverted |
| `--ink-2` | `#3a3a3d` | `oklch(0.86 0.005 260)` | inverted |
| `--ink-3` | `#6a6a70` | `oklch(0.68 0.005 260)` | inverted |
| `--ink-4` | `#9a9aa0` | `oklch(0.52 0.005 260)` | inverted |
| `--line` | `rgba(11,11,12,0.08)` | `oklch(0.30 0.01 260)` | different encoding |
| `--accent` | `oklch(0.62 0.13 250)` | `oklch(0.62 0.13 250)` | **Match** |
| `--accent-soft` | `oklch(0.62 0.13 250 / 0.12)` | `oklch(0.62 0.13 250 / 0.14)` | **+0.02 opacity** |
| `--font-ui` | `"Inter"` (default), `"Geist"` (tweaks) | `'Inter'` (default), `'Geist'` (data-fonts) | **Match** |
| `--font-mono` | `"JetBrains Mono"` / `"Geist Mono"` | `'JetBrains Mono'` / `'Geist Mono'` | **Match** |
| `--radius` | `10px` | `--radius-md: 7px` (the token mapped to `--radius`) | **−3px** |
| `--pad` (default) | `24px` | not declared outside density blocks | **Missing default** |
| `--gap` | `24px` (default) / density variants | not declared at all | **Entirely missing** |
| `--h-row` | `44px` (default) / density variants | per density only via `--row-height-*` | **Different structure** |

---

## 5. Prioritized Fix List

Geordnet nach visuellem Impact (hoch → niedrig):

1. **`--pad` default missing + wrong values in density modes** — The mockup's `--pad` airy=28px is used everywhere as container padding in Library, Detail, and all cards. Phase-1 sets airy=16px. This causes the entire content area to look cramped. Fix: update `[data-density="airy"]` to `--pad: 28px`, balanced to `20px`, dense to `16px`. Also add `--pad: 24px` to `:root` as non-density fallback.

2. **`--gap` token entirely missing** — The mockup uses `var(--gap)` for vertical zone spacing (24px default, 28/18/14 by density). Phase-1 has no `--gap` variable. All components that need zone separation currently have ad-hoc `mb-*` classes. Fix: add `--gap: 24px` to `:root` and the three density blocks.

3. **Body/UI font size 1px too large throughout** — Mockup uses `13px` for all interactive text (nav items, table rows, buttons, search inputs, breadcrumbs). Phase-1 uses Tailwind `text-sm = 14px`. This affects Sidebar nav, LibraryTabs, MetricsTable td, search input, and library-client header. Fix: set `--text-body: 13px` and use it, or adjust base font-size to 13px.

4. **Library page title: wrong size + weight** — Mockup: `28px / 500 / letter-spacing -0.02em`. Phase-1: `text-2xl (24px) / font-semibold (600)`. Fix `library-client.tsx` h1 to `font-size: 28px; font-weight: 500; letter-spacing: -0.02em`.

5. **`--radius` 7px vs mockup 10px** — `--radius-md` is mapped as the default radius token. Mockup `:root --radius: 10px`. All cards, modals, and rounded-lg elements are 3px tighter than the design. Fix: change `--radius-md: 10px` (or add a dedicated `--radius: 10px`). Note: nav item radius in mockup is 7px, so keep `--radius-md: 7px` for interactive elements but introduce `--radius-card: 10px`.

6. **`--h-row` misalignment in balanced and dense modes** — Balanced: 36px vs 40px (−4px); Dense: 30px vs 36px (−6px). Fix: `--row-height-balanced: 40px`, `--row-height-dense: 36px`.

7. **Table cell padding too small** — Mockup `td`: `14px var(--pad)` = 14px vertical / 24px horizontal. Phase-1: `py-3 px-4` = 12px / 16px. Both dimensions are smaller. Fix `MetricsTable.tsx` td to `py-3.5 px-6` (or set via `--pad`).

8. **Table header weight 600 vs mockup 500** — `thStyle fontWeight: 500` in mockup. `MetricsTable.tsx` uses `font-semibold` (600). Fix: change to `font-medium`.

9. **Table header letter-spacing missing** — Mockup `thStyle letterSpacing: "0.06em"`. Not set in Phase-1. Fix: add `tracking-[0.06em]` to th cells.

10. **LibraryTabs inactive weight 500 vs mockup 400** — All tabs render `font-medium` (500). Mockup only applies 500 to active tab. Fix: conditionally apply `font-medium` only when active.

11. **LibraryTabs underline 2px vs mockup 1.5px** — Fix inline style `borderBottom: '1.5px solid var(--accent)'`.

12. **Sidebar brand name 12px vs mockup 13.5px + missing letter-spacing** — Fix `Sidebar.tsx` brand name to `text-[13.5px] tracking-[-0.01em]`.

13. **Sidebar domain dot 8px vs mockup 6px, radius 4px vs 2px** — Fix to `w-1.5 h-1.5 rounded-[2px]`.

14. **Sidebar user avatar 32px vs mockup 28px** — Fix to `w-7 h-7` (28px).

15. **Sidebar actions section bottom padding asymmetry** — Mockup `padding: "14px 12px 6px"`. Phase-1 `py-3.5` applies 14px symmetrically (top and bottom). Should be `pt-3.5 pb-1.5 px-3` for 14px/12px/6px.

16. **Library filter row gap 12px vs mockup 8px** — Fix `gap-3` to `gap-2` in `library-client.tsx` filter row.

17. **`--accent-soft` opacity 0.14 vs mockup 0.12** — Minor. Fix in `tokens.css`: `oklch(0.62 0.13 250 / 0.12)`.

18. **Nav section header letter-spacing missing throughout** — Mockup `navHeader letterSpacing: "0.08em"`, also `paletteHeader`. Fix: add `tracking-[0.08em]` to all nav section headers and palette headers.
