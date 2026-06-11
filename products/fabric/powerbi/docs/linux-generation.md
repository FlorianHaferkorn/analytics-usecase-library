# Linux generation (B3)

Goal: make Power BI artifact generation runnable on Linux/CI so `dist/` can be
rebuilt from source on a standard runner (the prerequisite for a "golden build"
regeneration) instead of only on Windows.

## Proven: the canonical generator runs on Linux

PowerShell Core (pwsh) is cross-platform, and the measure generator
`tooling/generator/generate_tmdl_measures.ps1` runs on Linux unchanged:

- It uses custom regex YAML parsers (no `powershell-yaml` dependency).
- `Join-Path` and the parsers are line-ending tolerant (the catalog is LF, the
  regexes use `(?m)` / `\r?\n`); no Windows backslash paths leak into output.
- Verified locally on Ubuntu 24.04 with PowerShell 7.4.6 (installed from the
  official tarball) and on GitHub `ubuntu-latest` (pwsh is pre-installed).

CI capability: [`.github/workflows/linux-generation.yml`](../../../../.github/workflows/linux-generation.yml)
builds the registry (Python) and generates measures (pwsh) into a scratch dir,
asserting output is produced and committed `dist/` is untouched.

## Known gap: standalone vs. full-pipeline output

A **standalone** `generate_tmdl_measures.ps1` run resolves measure *names* to the
dotted `kpi_id` (e.g. `margin.gm.pct`) and only the directly-passed use case,
rather than the display names (`Gross Margin %`) and cumulative domain set that
the committed `dist/` carries. The correct, display-named, cumulative output is
produced only through the **full orchestrator pipeline**
(`orchestrate_full_model.ps1`: registry → IR → measures → tables → relationships
→ reports), which resolves names via the catalog/IR.

This matters for the golden-build regen, not for the capability itself. Two
threads feed it and should be consolidated:

1. There are **two IR implementations** (`tooling/ir/` and
   `tooling/generator_core/ir/`). The Python `BracketCompiler`
   (`generator_core`) was fixed to resolve display names (ADR-adjacent A2); the
   PowerShell standalone path does not use it.
2. The orchestrator has steps that are **not** Linux-safe yet (e.g. Power BI
   Desktop readiness, Fabric/Azure deploy). The Linux generation path should be
   scoped to the source→TMDL/PBIR steps and skip Desktop/Fabric.

## Path to the golden-build regeneration

1. Make the orchestrator's source→artifact subset run end-to-end on pwsh-linux
   (skip Desktop/Fabric phases behind a flag).
2. Reconcile the IR paths so display-named measures are produced on Linux.
3. Run the enricher (`enrich_measure_docs.py`) so `///` blocks project the
   AI-description standard.
4. Re-baseline `dist/` + golden fixtures in one reviewed commit, with every gate
   green (pytest, `pbi-quality validate` 0 criticals, H7, scorecard).

Until then: keep converging incrementally; `dist/` stays consistent with the
tests, and the Linux generator is proven runnable.
