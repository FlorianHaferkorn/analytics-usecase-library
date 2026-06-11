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

## Diagnostic: the generator cannot currently reproduce `dist/` from source

Running the canonical generator on Linux surfaced concrete, **platform-agnostic**
correctness bugs — the committed `dist/` is NOT reproducible from the current
sources today:

- **Fixed here:** `Get-ChunkValue` only matched *double-quoted* YAML scalars
  (`key: "value"`), but the catalog stores `kpi_key: Gross Margin %` unquoted, so
  every measure name fell back to the dotted `kpi_id`. Added an unquoted-scalar
  fallback → display names now resolve on any platform.
- **Still open:** measure DAX comes out `BLANK()`. The KPI catalog carries no DAX
  (only `technical.measure_name`/lineage); the DAX lives in the **measure
  overlay** (`products/fabric/powerbi/specs/fabric_measure_overlay.yaml`) and the
  measure dictionaries. The correct path is the IR:
  `build_ir.py --kpi-catalog … --fabric-overlay …` produces an IR with both the
  display name and the DAX, but the generator's `-IrFile` path does not propagate
  `dax_expression` into the emitted measure (and several overlay entries are still
  `-- TBD: see Measure Dictionary`).

### Correct Linux generation pipeline (target)

```bash
python tooling/ir/build_ir.py --kpi-catalog core/kpi_catalog \
  --fabric-overlay products/fabric/powerbi/specs/fabric_measure_overlay.yaml \
  --out ir_v1.json
pwsh ./tooling/generator/generate_tmdl_measures.ps1 -IrFile ir_v1.json \
  -TargetTablesDir <domain tables dir> -OverwriteExisting
```

## Path to the golden-build regeneration

1. Fix `dax_expression` propagation in the generator's IR path and backfill the
   overlay's `TBD` entries from the measure dictionaries (single DAX source).
2. Make the orchestrator's source→artifact subset run end-to-end on pwsh-linux
   (skip Desktop/Fabric phases behind a flag).
3. Run the enricher (`enrich_measure_docs.py`) so `///` blocks project the
   AI-description standard.
4. Re-baseline `dist/` + golden fixtures in one reviewed commit, with every gate
   green (pytest, `pbi-quality validate` 0 criticals, H7, scorecard).

Until then a clean `rm -rf dist && regenerate` would **not** reproduce the current
artifacts — keep converging incrementally; `dist/` stays consistent with the
tests, and the Linux generator is proven runnable.
