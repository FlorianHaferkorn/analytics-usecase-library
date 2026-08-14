<!-- AUTO-GENERATED from docs/agent/ — do not edit directly. Run: python tooling/generator/generate_tool_configs.py -->

---
name: visual-library
description: Resolve an analytical question to a governed Power BI chart idiom (evidence-based choice, notation profile, minimum grid size) and audit existing report visuals against the ALUCA deny-list. Use when choosing a chart type, reviewing or upgrading an existing report's visuals, or generating report pages from a use case bracket.
version: "1.0.0"
---

# Visual Library — governed chart choice + audit

Resolve an analytical question to the governed Power BI chart idiom (evidence-based choice,
notation profile, minimum grid size), and audit an existing report's visuals against the ALUCA
deny-list. The library is the single source of truth; this skill routes to it and runs the
resolver — it never restates the catalog.

## IS / IS NOT

- **IS:** which idiom for a question, which notation profile, the minimum legible size, and a
  verdict on an existing visual (governed / denied / ungoverned) + the sanctioned replacement.
- **IS NOT** the authoring mechanics — writing `visual.json` / TMDL / Deneb is the Microsoft
  `powerbi-report-authoring` skill's job; the upstream chart-choice *why* is `pbi-design`. This
  skill is the ALUCA-specific *which idiom / which template / which profile* — code-generating,
  golden-tested, and the operationalization of `pbi-design`'s judgment.

## The SoT (read on demand — never restate here)

- `core/templates/page_templates/visual_library/index.yaml` — purpose→idiom chooser, `deny` list,
  notation profiles, `implemented` (30 idioms).
- `<idiom>.yaml` — encoding rationale, `realizations` per tool, `min_size` (grid units), `data_fit`
  (per-param cardinality/type contract), `version` + `status` (lifecycle), preview.
- `_anti_patterns.yaml` — the catalog defining every `anti_patterns` id (message + fix + source).
- `tokens/color_semantics.yaml` — `categorical_cvd_safe` (the governed colour-blind-safe series palette).
- `tooling/visual_library/render.py` — pure `{{param}}` renderer + grid math; `resolve.py` — the
  resolver used below; `contrast.py` — CVD-safe palette + WCAG/CIEDE2000 checks; `a11y.py` —
  alt-text + screen-reader data-table. (`visreg.py` is a CI-only perceptual-regression gate.)

## Workflow A — choosing a visual (authoring / bracket / plan)

1. Name the analytical question → its `purpose` id (`resolve.py list`).
2. `py -3 tooling/visual_library/resolve.py purpose <purpose_id> [--profile ibcs|print_safe]`
   → best idiom + candidates, each with native visualType, `min_size` (grid + px @1280/@1920), tools.
3. Validate the bound data fits: `py -3 tooling/visual_library/resolve.py fit <idiom> <param>=<n>[:type]`
   → UNFIT names the governing anti-pattern + fix; `resolve.py why-not <idiom>` lists the governed anti-patterns.
4. Read the chosen `<idiom>.yaml` for the runnable template of your tool; render with `render.py`.
5. Size the page slot **≥ the idiom's `min_size`** (grid units) on `tokens/layout_grid.yaml`.
6. For a multi-series chart, take colours from `contrast.py palette <n>` (colour-blind-safe; past its
   `series_cap` a pattern/shape channel is mandatory). Attach an accessible name with
   `a11y.py alt <idiom>` (the Deneb track sets it as the spec's `description`).

## Workflow B — auditing / upgrading an existing report (no ALUCA core)

1. Per visual: `py -3 tooling/visual_library/resolve.py audit <visual.json>` →
   **GOVERNED** (which idiom), **DENIED** (deny rule + replacement), or **UNGOVERNED** (resolve by purpose).
2. Replace denied visuals with the sanctioned idiom; inject SVG-DAX / AlucaViz micro-charts where a
   cell/card form fits; apply a notation profile (`ibcs` / `print_safe`) via the param overlay.
   Before emitting, `resolve.py fit <idiom> <param>=<n>` confirms the target's data (cardinality/type) suits it.
3. This path depends ONLY on `render.py` + `resolve.py` + the YAML — no semantic model, no bracket.
   For a drop-in bundle into a customer repo, generate it (do not hand-copy).

## Deny (never emit)

`pie_gt_4 · three_d · gauge · radar · dual_axis_no_reason · color_as_decoration · powerbi_smart_narrative`
— the live list is `index.yaml: deny`; `resolve.py audit` enforces it.

## Do NOT

- Do not pick a chart directly — resolve it from the question (`purpose`).
- Do not restate the idiom catalog in prose — it drifts; always read `index.yaml` / `<idiom>.yaml`.
- Do not use this for authoring mechanics (`powerbi-report-authoring`) or the design *why* (`pbi-design`).
