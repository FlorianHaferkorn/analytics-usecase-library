# Design Reference — Studio Rebuild

This folder contains the **target design** uploaded by the user on 2026-04-24.
It is the **visual and functional source of truth** for the studio rebuild.

## ⚠️ Filename / Content Mismatch

The uploaded JSX files have **mismatched filenames** — the export inside the file
does NOT match the filename. The table below is the **authoritative content map**.
Always open files by content purpose, not filename.

### Studio tool (the authoring UI)

| Filename                  | Actual content                         | Exports                  |
|---------------------------|----------------------------------------|--------------------------|
| `wizard.jsx`              | **Shell**: Sidebar + Topbar + Nav      | `NAV_ITEMS`, `Pill`, `Sidebar`, `Topbar`, `CommandPalette` |
| `dashboard.jsx`           | **App root**: routing, keybinds, edit-mode protocol | `App` (ReactDOM.render) |
| `detail.jsx`              | **Dashboard view**: sparklines, stats, composition | `Dashboard`, `Sparkline` |
| `data.jsx`                | **Canvas view**: node graph (pan/zoom) | `Canvas` |
| `tweaks.jsx`              | **Library view**: tabs (metrics/dimensions/sources) | `Library` |
| `library.jsx`             | **Detail view**: metric detail + right rail + Studio AI | `Detail`, `PropRow`, `OwnerChip` |
| `primitives.jsx`          | **Wizard**: 3-step modal, AI draft     | `Wizard` |
| `design-canvas.jsx`       | **Tweaks panel** (the one in Studio.html) | `Tweaks` |
| `shell.jsx`               | **Icons**: minimal SVG icon set        | `I`, `Icon` (window globals) |
| `icons.jsx`               | **FRAMEWORK data**: mock domains/metrics/dimensions/sources | `FRAMEWORK`, `GRAPH` globals |
| `app.jsx`                 | **T4 Report page** (belongs to Report Templates, not Studio) | `T4Detail` |

### Report Templates tool (T1–T4 gallery)

| Filename          | Actual content                 |
|-------------------|--------------------------------|
| `T2_overview.jsx` | T2 Tactical Variance page     |
| `T3_overview.jsx` | T3 Operational Monitoring page |
| `T4_detail.jsx`   | T4 Prescriptive Recommendation |
| `app.jsx`         | ALSO T4 (duplicate upload)    |

T1 page exists in the embedded template library inside `html/Report_Templates.html`.

### HTML host files

| Filename                     | Purpose                                                       |
|------------------------------|---------------------------------------------------------------|
| `html/Studio.html`           | Top-level host for the Studio tool (the authoring UI)         |
| `html/Report_Templates.html` | Top-level host for the T1–T4 gallery (with DesignCanvas)      |
| `html/studio_index.html`     | Backup copy of the Report Templates index (uploaded as `tokens.js` by mistake) |

## How to use these files

- **Read for design intent** — CSS variables, component structure, interactions, keyboard shortcuts, postMessage protocol.
- **Do NOT copy the JSX 1:1 into Next.js components.** These are Babel-in-browser prototypes. Port to TypeScript + React 19 + Tailwind v4 idioms.
- **Preserve**: visual system, OKLCH tokens, density modes, font pairings, slot/grid positioning for page templates, primitive component names (`PageChrome`, `Slot`, `Card`, `KpiCard`, `SmartNarrative`, `DetailMatrix`, `DataBar`, `Waterfall`, `ActionPanel`, `SlicerPane`, `Annotations`, `ExceptionTable`).
- **Replace**: mock `FRAMEWORK` / `GRAPH` globals with real data from `src/lib/core/*-loader.ts`. See `../rebuild/DATA_WIRING.md`.

## Source of truth hierarchy

1. `docs/rebuild/REBUILD_DECISIONS.md` — locked product decisions
2. `docs/rebuild/REBUILD_PLAN.md` — phase-by-phase execution plan
3. `docs/rebuild/TOKEN_SPEC.md` — CSS variable spec
4. `docs/rebuild/DATA_WIRING.md` — loader ↔ UI mapping
5. `docs/design-reference/` — original uploads (visual target)

When in doubt, the design reference wins for *look*, the decision doc wins for *behavior*.
