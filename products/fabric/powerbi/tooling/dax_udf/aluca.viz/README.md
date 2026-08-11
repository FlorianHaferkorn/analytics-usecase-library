# AlucaViz — governed SVG micro-chart DAX UDFs

A [daxlib.org](https://daxlib.org)-format DAX **User-Defined Function** library that packages the
ALUCA Visual Library's `powerbi_svg_dax` idioms as reusable, model-independent functions. Install
once into a semantic model, then call from any table/matrix/card measure — the governed "10× the
same result" guarantee moves from pasted measures to versioned functions.

> **Source of truth:** `core/templates/page_templates/visual_library/<idiom>.yaml` (the
> `powerbi_svg_dax` realizations). These UDFs are the same governed micro-charts, parameterized.

## Functions (v0.2.0)

Cell-scoped (one row of a table/matrix — carry their own scope, no external `[Measure]` context needed):

| Function | Idiom | House vs IBCS |
| --- | --- | --- |
| `AlucaViz.DeviationBar(delta, [colPos], [colNeg], [fullScale], [colTrack], [colZero])` | `deviation_bar` | IBCS = prominent ink reference (set `colZero` to `#201F1E`) |
| `AlucaViz.Bullet(actual, target, [showBands], [bandOk], [bandGood], [colActual], [colTarget])` | `bullet` | IBCS = clean, no bands (set `showBands` to `0`, `colTarget` to `#605E5C`) |

Context-heavy (v0.2.0 — need the **scope column** as a `COLUMNREF EXPR` so the function can
autoscale across the visible category and blank out on subtotal rows):

| Function | Idiom | Notes |
| --- | --- | --- |
| `AlucaViz.BarRanking(value, scope, [threshold], [colBar], [colBad])` | `bar_ranking` | length = `value / MAX(value)` over `ALLSELECTED(scope)`; colours below `threshold` (0..1) |
| `AlucaViz.Lollipop(value, scope, [threshold], [colDot], [colBad], [colStem])` | `lollipop` | same scaling, lighter ink weight (stem + dot) |
| `AlucaViz.Sparkline(value, dateCol, [months], [colLine])` | `line` | trailing-N-month trend polyline, autoscaled to its own min/max |

All return a `data:image/svg+xml;utf8,...` string — set the measure's data category to **ImageUrl**
and bind it in a table/matrix/card (new `cardVisual`). Measure arguments are `NUMERIC EXPR` (lazy) so
they evaluate in the row/filter context of the visual; the `scope`/`dateCol` arguments are
`COLUMNREF EXPR` — pass a bare column reference like `'dim_org'[OrgName]` (per the
[DAX UDF parameter contract](https://learn.microsoft.com/dax/best-practices/dax-user-defined-functions#parameters):
reference types must be `expr`).

### Example

> **DAX UDFs are called positionally** — there is no named-argument syntax. To pass a later
> optional, leave the earlier optionals empty (`Fn ( a, , , x )`). `colZero` is `DeviationBar`'s
> 6th param; `colTarget` is `Bullet`'s 7th.

```dax
GM vs Plan (bar)  = AlucaViz.DeviationBar ( [Gross Margin % vs Plan] )
GM vs Plan (IBCS) = AlucaViz.DeviationBar ( [Gross Margin % vs Plan], , , , , "#201F1E" )
SLA Bullet (IBCS) = AlucaViz.Bullet ( [SLA Attainment %], [SLA Target %], 0, , , , "#605E5C" )
GM Rank (bar)     = AlucaViz.BarRanking ( [Gross Margin %], 'dim_org'[OrgName], 0.441 )
GM Rank (dot)     = AlucaViz.Lollipop ( [Gross Margin %], 'dim_org'[OrgName], 0.441 )
GM Trend (12m)    = AlucaViz.Sparkline ( [Gross Margin %], 'dim_date'[Date] )
```

## Install

Requires model compatibility level **1702+**. Use the `daxlib` CLI (needs Power BI Desktop open) or
Tabular Editor:

```bash
daxlib add AlucaViz --source <this package dir>   # or publish to a private feed
```

Or paste `lib/functions.tmdl` into the model's TMDL and refresh.

## Relation to community libraries

Per the `svg-visuals` skill's "prefer existing UDF libraries" rule:

- **[DaxLib.SVG](https://daxlib.org/package/DaxLib.SVG/)** — a low-level SVG toolkit (`Element.Rect`,
  `Compound.Bars`, `Compound.ProgressBar`, …). Great primitives, but **not** governed idioms.
- **[PowerofBI.IBCS](https://daxlib.org/package/PowerofBI.IBCS/)** — IBCS bars/columns/waterfall UDFs.

AlucaViz adds the **governed** layer on top: the exact ALUCA color tokens, the deviation-from-target
and Few-bullet forms, and the house/IBCS notation discipline as parameters. As of v0.2.0 the
context-heavy idioms (`bar_ranking`, `lollipop`, `line`) ship too — self-scoping via a `COLUMNREF`
parameter rather than depending on DaxLib.SVG primitives.

## Status / validation

Determinism + structure are unit-tested (`tests/test_aluca_viz.py`, 5 tests): manifest is valid,
all five functions are declared + version-annotated, the TMDL is tab-clean, bodies balance their
`<svg>`/quotes, and the context-heavy idioms take a `COLUMNREF EXPR` scope.

**Live-model (DAX-engine) validation is Desktop-gated** and prepared as a runnable harness in
[`../validate/`](../validate/):

- `acceptance.dax` — paste into DAX query view (CL 1702+) and run. Block A evaluates the two scalar
  idioms model-independently (pass = each cell is a `data:image/svg+xml…</svg>` string); Block B is a
  fill-in-the-column template for the three context-heavy idioms.
- `CHECKLIST.md` — the end-to-end Desktop steps: install the package, create the measures, bind to a
  `cardVisual`/table, and confirm the micro-chart renders.
