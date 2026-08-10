# Visual Library — live-render acceptance

Determinism (byte-for-byte goldens), Vega-Lite compile, structural gates, and now **real Deneb
rasterization** all run in `tests/test_visual_library.py`. This is the end-to-end acceptance for the
tracks a headless test can't fully drive: one representative idiom per tool, taken to actual pixels in
its real runtime.

Generate the artifacts first:

```bash
py -3 tooling/visual_library/acceptance/render_acceptance.py materialize <out_dir>
```

This writes `<out_dir>/manifest.json`, all Deneb PNGs under `deneb_png/`, and one runnable artifact
per remaining tool. Then work each track:

## deneb_vegalite — DONE headless (un-gated)

`render_acceptance.py png <out_dir>` rasterizes **every** Deneb golden to PNG via vl-convert, and the
suite asserts it (`test_deneb_goldens_rasterize_to_png`). No Desktop, no browser. Eyeball
`deneb_png/waterfall_pvm.deneb.png` to confirm. (Data-less templates are bound to a field-covering
sample and given a fixed canvas so they draw.)

## powerbi_native — Desktop-gated

Representative: `bar_ranking.visual.json`.

1. Drop the fragment into a PBIR page (`.../<page>/visuals/<id>/visual.json`) or use the `pbir` CLI.
2. Bind its projections to a real measure + category (the fragment carries HITL placeholders).
3. Open in Power BI Desktop. **Pass** = the visual renders with data and no repair prompt.

## powerbi_svg_dax — DAX-engine-gated (harness ready)

Representative: `deviation_bar.dax`. The whole svg_dax track is packaged as the **AlucaViz** UDF
library; its engine acceptance is already prepared:

- `products/fabric/powerbi/tooling/dax_udf/validate/acceptance.dax` — paste into DAX query view, Run.
- `products/fabric/powerbi/tooling/dax_udf/validate/CHECKLIST.md` — install → measures → bind → render.

## web_recharts — browser-gated

Representative: `line.recharts.html`. Recharts/React are **not** vendored in `studio/node_modules`
(react/react-dom are, recharts is not), so this stays gated.

1. `npm i react react-dom recharts` in a scratch project (or a sandbox that provides them).
2. Transpile + mount the JSX in `line.recharts.html` (the file carries the golden JSX + sample data
   and the commented `createRoot(...).render(<Chart/>)` line).
3. **Pass** = the chart renders in the browser matching the idiom.

## Record

Note the versions/tools used and which tracks passed against the current library HEAD. Deneb is
green automatically; the other three are signed off when their gated render is confirmed.
