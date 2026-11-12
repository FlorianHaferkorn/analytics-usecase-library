# Page Template Preview v2

Interactive, governance-grade preview layer for the analytics page templates
(T1 Strategic Overview, T2 Tactical Variance, T3 Operational Monitoring,
T4 Prescriptive Recommendation).

**Status:** Phase 1 complete — foundation (tokens + grid + slot API + validator + smoke test).
Phase 2 (real page templates T1–T4) lands next.

---

## Design principles

1. **Single source of truth.** Every size, spacing, color and font value lives in
   `src/tokens/tokens.css` as a CSS custom property. Components consume tokens
   only — inline pixel values are blocked by ESLint.
2. **One positioning API.** `<Slot col row cs rs slotId />` is the only way to
   place content on a page. It emits `calc()`-based CSS that references
   `--lu-w`, `--lu-h`, `--outer`, `--gutter` — so everything reflows when tokens
   change, with no JavaScript re-render.
3. **Density & scale are real.** Switching `airy` / `balanced` / `dense`
   updates `--density`, which cascades through spacing + grid math. Zoom updates
   `--scale`, which cascades through typography.
4. **CI enforces the rules.** `npm run validate:grid` scans all `<Slot>` usages
   for overflow (col+cs > 12, row+rs > 12) and overlap. ESLint blocks
   `style={{ fontSize: 11 }}` and friends. `npm run check` runs the lot.

---

## Architecture

```
preview/
  index.html                 # Vite entry point
  package.json               # scripts: dev / build / test / validate:grid / check
  tsconfig.json              # strict TS, path aliases
  vite.config.ts             # dev server on :5180
  vitest.config.ts           # jsdom + coverage
  eslint.config.js           # no-inline-pixel rule

  src/
    tokens/
      tokens.css             # CSS custom properties — THE source of truth
      tokens.ts              # typed mirror + runtime controller
      index.ts
    grid/
      slot-pos.ts            # slotPos(), validateSlot(), slotsOverlap()
      Slot.tsx               # the <Slot> primitive
      Canvas.tsx             # <Canvas> host with optional anatomy overlay
      slot-pos.test.ts       # Vitest unit tests for the grid math
      index.ts
    demo/
      DemoApp.tsx            # smoke test with live density/canvas/zoom toggles
      demo.css

  tooling/
    validate-grid.ts         # scans src/**/*.tsx, fails CI on violations

  # coming in Phase 2:
  # src/primitives/           reusable KPI cards, charts, tables
  # src/pages/                T1, T2, T3, T4 page implementations
  # src/app/                  the DesignCanvas (pan / zoom / focus)
```

---

## Commands

```bash
npm install
npm run dev           # Vite dev server on http://localhost:5180
npm run build         # tsc + vite production build
npm run test          # Vitest run
npm run typecheck     # tsc --noEmit
npm run lint          # ESLint (no-inline-pixel)
npm run validate:grid # grid overflow + overlap scan
npm run check         # all of the above in sequence
```

---

## Token layers

| Layer | Variables | Scales with |
|---|---|---|
| Base | `--canvas-w`, `--canvas-h`, `--density`, `--scale` | runtime input |
| Grid | `--outer`, `--gutter`, `--lu-w`, `--lu-h` | density + canvas |
| Typography | `--fs-xs` … `--fs-display`, weights, leading, tracking | scale |
| Spacing | `--sp-0` … `--sp-12` | density |
| Color | `--c-surface-*`, `--c-ink-*`, `--c-line-*`, `--c-accent`, status | theme |
| Radius | `--r-sm` … `--r-pill` | — |
| Shadow | `--shadow-sm` … `--shadow-xl` | theme |
| Motion | `--motion-fast` … `--ease-in-out` | — |

---

## Governance rules

- **No inline pixels.** ESLint `no-restricted-syntax` blocks
  `style={{ fontSize: 11 }}`, `style={{ padding: "10px 14px" }}`, etc.
  Use `var(--fs-sm)`, `var(--sp-3)`, or `slotPos()`.
- **No positioning outside `<Slot>`.** `position: absolute` with inline top/left
  is forbidden in page code. Build-time grid validator enforces this implicitly
  by only scanning `<Slot>` calls for layout violations.
- **No new raw tokens in components.** Add to `tokens.css` first, then consume.

---

## Migration from v1

The static HTML previews (`page_t1_strategic.html`, etc.) were archived to
`../_archive/preview_v1/` on 2026-04-24. See that folder's README for
the rationale.
