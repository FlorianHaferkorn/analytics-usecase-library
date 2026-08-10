# AlucaViz — Desktop acceptance checklist

The unit tests (`../tests/test_aluca_viz.py`) prove the package is well-formed and stays in sync with
the daxlib format. They do **not** run the DAX engine. This checklist is the Desktop-gated acceptance
that closes the loop: it confirms each UDF parses, evaluates, and renders as an SVG micro-chart.

**Prerequisites:** Power BI Desktop (June 2026 or later), a semantic model at **compatibility level
1702+** with a numeric measure, a category column, and a date column.

## 1. Engine parse + eval (no install needed)

1. Open the model → **DAX query view**.
2. Paste [`acceptance.dax`](acceptance.dax) and **Run**.
3. **Block A passes** when all five `case_*` cells are strings that start with
   `data:image/svg+xml;utf8,<svg` and end with `</svg>`. Copy any cell into a browser address bar to
   see the actual bar / bullet.
4. For **Block B**, uncomment it, replace `<MEASURE>` / `<SCOPE COLUMN>` / `<DATE COLUMN>` with real
   objects from the model, and Run. Passes when each row returns a non-blank SVG string and the
   subtotal/total row is blank (the `HASONEVALUE` guard).

## 2. Install the package into the model

- **Tabular Editor / `daxlib` CLI:** `daxlib add AlucaViz --source <aluca.viz dir>` (Desktop open), **or**
- **TMDL view:** paste `../aluca.viz/lib/functions.tmdl` and **Apply**.
- Confirm all five appear under **Model explorer → Functions**: `AlucaViz.DeviationBar`,
  `AlucaViz.Bullet`, `AlucaViz.BarRanking`, `AlucaViz.Lollipop`, `AlucaViz.Sparkline`.

## 3. Create the measures (positional calls — no named args)

Create these as report/model measures, **data category = ImageUrl**:

```dax
GM Rank (bar) = AlucaViz.BarRanking ( [Gross Margin %], 'dim_org'[OrgName], 0.441 )
GM Rank (dot) = AlucaViz.Lollipop ( [Gross Margin %], 'dim_org'[OrgName], 0.441 )
GM Trend      = AlucaViz.Sparkline ( [Gross Margin %], 'dim_date'[Date] )
GM vs Plan    = AlucaViz.DeviationBar ( [Gross Margin % vs Plan] )
GM vs Plan I  = AlucaViz.DeviationBar ( [Gross Margin % vs Plan], , , , , "#201F1E" )
SLA Bullet    = AlucaViz.Bullet ( [SLA Attainment %], [SLA Target %], 0, , , , "#605E5C" )
```

## 4. Bind + render

- **Table/matrix** keyed by `'dim_org'[OrgName]`: add `GM Rank (bar)` and `GM Rank (dot)`; set the
  column's **Image size** (grid `imageHeight`/`imageWidth`) so the SVG shows.
- **Card (new `cardVisual`)**: bind `GM Trend` / `GM vs Plan` via `callout.imageFX`.
- **Pass** = the micro-chart renders (not a broken-image icon or raw text), colours match the idiom,
  the bar/dot length tracks the value, and the subtotal row is blank.

## 5. Record the result

Note Desktop build + compat level + date run against the package version (`manifest.daxlib`). A green
run here is the sign-off that the governed idioms render live, not just deterministically.

## Fallback (no Desktop)

Per `.claude/rules/connect-pbid.md`, an offline TMDL→TOM load
(`TmdlSerializer.DeserializeDatabaseFromFolder`) catches dangling refs but **cannot** evaluate DAX or
render SVG — so it validates the model wiring, not the UDF output. The engine steps above stay gated.
