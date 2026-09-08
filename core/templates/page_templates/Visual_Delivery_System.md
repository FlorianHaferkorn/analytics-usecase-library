# Visual Delivery System

> **Scope:** shared product identity for generated reports and ActionReady Studio.
> **Authorities:** [`Design_Spec_3_30_300.md`](Design_Spec_3_30_300.md),
> [`tokens/color_semantics.yaml`](tokens/color_semantics.yaml),
> [`tokens/typography.yaml`](tokens/typography.yaml), and
> [`tokens/layout_grid.yaml`](tokens/layout_grid.yaml).

This brief connects the governed report system and the Studio workbench. It does not
redefine KPI meaning, action logic, page slots, or design tokens.

## Design Brief: Dual-Surface Decision System

```yaml
product_intent: premium decision accelerator
personality: minimal, restrained, precise, calm
signature:
  - single-accent discipline
  - tabular numerals for comparable values
  - question-led page and visual titles
surfaces:
  studio:
    role: authoring and governance workbench
    mode: dark
    density: balanced
  reports:
    role: customer-facing decision and action instrument
    mode: light
    density: decision-dependent
shared_grammar:
  font: Segoe UI with system fallbacks
  grid: 8px base, governed 12-by-12 report canvas
  accent: brand.primary for selection, reference, and primary action only
  status: semantic positive, warning, negative, and neutral only
  numerals: tabular where values are compared
  motion: functional and reduced-motion safe
```

## Surface Contract

| Dimension | Studio workbench | Consumer report |
|---|---|---|
| Purpose | Build, govern, validate, deliver | Understand, decide, act |
| Surface | Dark neutral, quiet borders | Light neutral, white analytical surfaces |
| Accent | Accessible light shade of `brand.primary` | Governed `brand.primary` |
| Hierarchy | Page title → workflow state → work object | Decision question → KPI signal → explanation → action |
| Density | Balanced; dense only for registries and code | T1/T2 balanced, T3/T4 information-dense |
| Color | Selection and state only | Reference and semantic meaning only |

The light/dark split is intentional. Harmony comes from shared roles and behaviour,
not from forcing authoring and consumption into the same surface colour.

## Report Composition

Every use case keeps exactly two pages:

1. **Overview (3–30 seconds):** decision question, one to four primary KPI signals,
   no more than three slicers, one dominant explanatory visual, and only the supporting
   context required to answer “why?”.
2. **Detail (300 seconds):** compact filters, governed narrative, evidence matrix, and
   an action panel where the use case is prescriptive.

Use native visuals and official connector capabilities first. Advanced visuals are
allowed only where the visual whitelist proves that the native option cannot carry the
required meaning. The same measure keeps the same reference colour within a report;
status colours never encode categories.

## Component Meaning

- KPI cards carry label, current value, comparison, target, status text plus icon, and
  period context when available. A sparkline is optional supporting evidence.
- Variance uses waterfall or deviation bars; scenarios use the governed AC/PL/FC/PY
  notation rather than additional decorative colours.
- Detail matrices use tabular numerals, restrained conditional formatting, and
  severity-sorted exceptions where action priority matters.
- Studio controls expose a visible focus state, readable secondary text, and no
  network-dependent font requirement.

## Acceptance

The product is visually complete only when:

- all Studio consumer and authoring routes render without clipped primary content;
- no normal interface text falls below the governed role minimum;
- semantic states remain understandable without colour alone;
- light and dark text contrast meets WCAG AA for the applicable text size;
- report pages fit the governed canvas without vertical scrolling;
- Studio token lint, unit tests, production build, and the official Power BI report
  validators pass.
