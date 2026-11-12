# preview — reference formula only

The Vite/React mockup of the page templates that lived here (not part of CI) was archived on
12.11.2026 to `_archiv/core/templates/page_templates/preview/`.

What stays is `src/grid/slot-pos.ts`: the TypeScript form of the slot-to-pixel formula.
`tooling/tests/test_logical_units.py` reads it as the reference that
`tooling/generator_core/ir/compiler.py` and `tooling/superversion/layer_tools/layout_grid.py`
mirror. Change the formula there and here together.
