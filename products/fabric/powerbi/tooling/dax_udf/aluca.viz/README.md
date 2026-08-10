# AlucaViz — governed SVG micro-chart DAX UDFs

A [daxlib.org](https://daxlib.org)-format DAX **User-Defined Function** library that packages the
ALUCA Visual Library's `powerbi_svg_dax` idioms as reusable, model-independent functions. Install
once into a semantic model, then call from any table/matrix/card measure — the governed "10× the
same result" guarantee moves from pasted measures to versioned functions.

> **Source of truth:** `core/templates/page_templates/visual_library/<idiom>.yaml` (the
> `powerbi_svg_dax` realizations). These UDFs are the same governed micro-charts, parameterized.

## Functions (v0.1.0)

| Function | Idiom | House vs IBCS |
|---|---|---|
| `AlucaViz.DeviationBar(delta, [colPos], [colNeg], [fullScale], [colTrack], [colZero])` | `deviation_bar` | IBCS = prominent ink reference: pass `colZero = "#201F1E"` |
| `AlucaViz.Bullet(actual, target, [showBands], [bandOk], [bandGood], [colActual], [colTarget])` | `bullet` | IBCS = clean, no bands: pass `showBands = 0`, `colTarget = "#605E5C"` |

Both return an `data:image/svg+xml;utf8,...` string — set the measure's data category to **ImageUrl**
and bind it in a table/matrix/card (new `cardVisual`). The measure arguments are `NUMERIC EXPR`
(lazy) so they evaluate in the row/filter context of the visual.

### Example

```dax
GM vs Plan (bar) = AlucaViz.DeviationBar ( [Gross Margin % vs Plan] )
GM vs Plan (IBCS) = AlucaViz.DeviationBar ( [Gross Margin % vs Plan], colZero = "#201F1E" )
SLA Bullet (IBCS) = AlucaViz.Bullet ( [SLA Attainment %], [SLA Target %], showBands = 0, colTarget = "#605E5C" )
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
and Few-bullet forms, and the house/IBCS notation discipline as parameters. Build the context-heavy
idioms (`bar_ranking`, `line`, `lollipop`, …) on DaxLib.SVG primitives in a later version.

## Status / validation

Determinism + structure are unit-tested (`tests/test_aluca_viz.py`). **Live-model validation is
Desktop/engine-gated** (same as the rest of the svg_dax track): evaluate each function in a model and
confirm the returned SVG renders in a cardVisual — the acceptance step for a Desktop-free session.
