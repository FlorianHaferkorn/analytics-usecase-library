# Visual Library — live-render acceptance

**Three of the four tool tracks are proven by an actual headless render** (recorded in
`validation_matrix.json`); only Power BI native genuinely can't be, and its reason is structural.

| Track | Proof | How |
| --- | --- | --- |
| **deneb_vegalite** | ✅ rendered | vl-convert rasterizes every golden across 5 data scenarios — `test_deneb_goldens_rasterize_to_png` |
| **powerbi_svg_dax** | ✅ rendered | vl-convert `svg_to_png` rasterizes the emitted SVG — `test_svg_dax_goldens_rasterize_to_png` |
| **web_recharts** | ✅ rendered | real React + Recharts headless render, 27/27 — `render_recharts.mjs` (Node) |
| **powerbi_native** | 🔶 Desktop-gated | PBIR is a visual *config*, no headless renderer exists — a Desktop load |

## deneb_vegalite — proven headlessly

`render_acceptance.py png <out_dir>` rasterizes every Deneb golden; the suite asserts it. Eyeball
`deneb_png/waterfall_pvm.deneb.png`.

## powerbi_svg_dax — proven headlessly (the emitted SVG)

The report artefact is the SVG string the DAX measure emits. `render_acceptance.render_svg_dax_png`
substitutes representative values into that exact SVG and rasterizes it via vl-convert — proof the
SVG renders. The DAX-computed *values* stay engine-checked separately:

- `products/fabric/powerbi/tooling/dax_udf/validate/acceptance.dax` — paste into DAX query view, Run.

## web_recharts — proven headlessly (real React render)

```bash
cd tooling/visual_library/acceptance
npm i react react-dom recharts esbuild playwright
node render_recharts.mjs        # bundles + mounts every golden; asserts a populated <svg> (27/27)
```

## powerbi_native — Desktop-gated (by nature)

Representative: `bar_ranking.visual.json`. PBIR is a Power BI visual configuration — there is **no**
OSS/headless renderer for it; it only renders inside Power BI Desktop / Service.

1. Drop the fragment into a PBIR page (`.../<page>/visuals/<id>/visual.json`) or use the `pbir` CLI.
2. Bind its projections to a real measure + category (the fragment carries HITL placeholders).
3. Open in Power BI Desktop. **Pass** = the visual renders with data and no repair prompt.

## Record

Note the tools/versions and confirm the native Desktop load against the current library HEAD; the
other three tracks are proven automatically by the suite (with vl-convert) + `render_recharts.mjs`.
