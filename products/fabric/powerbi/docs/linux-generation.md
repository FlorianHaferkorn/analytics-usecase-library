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

## Linguistic schema (cultures/) — pure-Python, Linux-native

The **third projection** of the governed catalog (after the `///` block and the viz
tooltip) is the model linguistic schema — curated column synonyms emitted into
`cultures/<culture>.tmdl` for Copilot/Q&A. It is pure Python (no pwsh, no Power BI
Desktop), so it regenerates on Linux unchanged and is deterministic/idempotent:

```bash
python3 -m products.fabric.powerbi.tooling.linguistic_schema --all          # emit
python3 -m products.fabric.powerbi.tooling.linguistic_schema --all --check  # gate (exit 1 on a gap)
```

Coverage is gated by **H8 (AI-Readiness / Linguistic Coverage)** in the health
scorecard. Source/format: `core/semantic_models/AI_Description_Standard.md`.

## Known gap: standalone vs. full-pipeline output

The **IR pipeline produces correct output on Linux** — verified end to end:

```bash
python tooling/ir/build_ir.py --kpi-catalog core/kpi_catalog \
  --fabric-overlay products/fabric/powerbi/specs/fabric_measure_overlay.yaml \
  --out ir_v1.json
pwsh ./tooling/generator/generate_tmdl_measures.ps1 -IRPath ir_v1.json \
  -UseCase COM-001,COM-002,COM-003,COM-004 \
  -TargetTablesDir <domain tables dir> -OverwriteExisting
```

This regenerates the full Commercial domain on Linux: **48 measures, display
names, real DAX, 0 `BLANK()`** (`Gross Margin % = DIVIDE ( ... )`,
`Net Sales Amount = SUM ( fact_sales[Net Sales Amount] )`, the PVM effects, …).

- The IR (`build_ir.py`) merges the **measure overlay** (the DAX source — the KPI
  catalog itself carries no DAX) over the catalog, so the IR has both display
  names and DAX. Pass it with **`-IRPath`** (not `-IrFile`) and comma-separate
  multiple use cases.
- `linux-generation.yml` runs exactly this and asserts the Commercial output has
  display-named measures with real DAX and no `BLANK()`.

## Bugs found & fixed running on Linux

- **Fixed:** `Get-ChunkValue` only matched *double-quoted* YAML scalars
  (`key: "value"`), but the catalog stores `kpi_key: Gross Margin %` unquoted.
  This broke the non-IR (Core-reads) path's name resolution on **any** platform
  (measure names fell back to the dotted `kpi_id`). Added an unquoted-scalar
  fallback.
- **Not a bug:** an earlier "DAX propagation" symptom was a wrong parameter name
  (`-IrFile` vs the actual `-IRPath`), which silently fell through to the
  Core-reads path (no DAX). With `-IRPath` the DAX propagates correctly.

## Remaining for a full all-domain golden build

1. **Author missing DAX (content gap):** 51 overlay entries are still
   `-- TBD: see Measure Dictionary`, so those KPIs emit `BLANK()` in non-Commercial
   domains. They **cannot be auto-backfilled** — checking the measure dictionaries,
   only 4/51 carry real DAX in `expression.logical`; the other 47 hold prose or
   pseudo-code (e.g. `Baseline amount of …`, `COUNTIF(…)`). The DAX for these KPIs
   has not been authored yet; completing the overlay is a content task, not an
   extraction. (Commercial is complete, which is why it regenerates cleanly.)
2. **Orchestrator on Linux:** scope its source→artifact subset to run on
   pwsh-linux and gate out the non-Linux phases (Power BI Desktop readiness,
   Fabric/Azure deploy).
3. **Project the standard:** run the enricher (`enrich_measure_docs.py`) so `///`
   blocks project the AI-description standard.
4. **Re-baseline** `dist/` + golden fixtures in one reviewed commit, every gate
   green (pytest, `pbi-quality validate` 0 criticals, H7, H8 linguistic coverage,
   scorecard).

The Commercial domain is now reproducible on Linux; completing step 1 extends
this to all domains and unlocks the golden-build regeneration.
