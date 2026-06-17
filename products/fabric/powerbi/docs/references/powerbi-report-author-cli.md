# powerbi-report-author CLI — spike findings & reference

Spike for ADR 0001 (Tier 1 oracle). Result: **adopt as an opt-in augmentation;
keep the native floor.** The official CLI and our native validator are
**complementary, not redundant.**

## Install

```bash
npm install -g @microsoft/powerbi-report-authoring-cli   # provides: powerbi-report-author
npm install -g @microsoft/powerbi-desktop-bridge-cli      # provides: powerbi-desktop (needs Desktop)
```

`powerbi-report-author` runs **fully offline** — its metadata comes from the
bundled `@microsoft/powerbi-core-visual-schema` (57 visual types, 15 VCOs). No
network or Power BI Desktop is required for `validate`, `catalog`, or `formatting`.

## Command surface (v0.1.1)

| Command | Purpose |
|---|---|
| `validate <path> [--no-schema] [--format json\|text]` | Validate a `.pbip` / `.Report` dir; structured diagnostics |
| `catalog list` / `catalog describe <visualType>` | Visual-type catalogue, incl. `roles` + `requiredRoles` |
| `formatting list-objects\|describe-object\|describe-property <visualType> …` | Formatting object/property metadata |
| `preview-visuals\|preview-pages\|preview-filters\|preview-themes <path>` | Read-only summaries |
| `doctor` | Environment self-check (node, metadata provider, schema reachability) |

Global `--out <file>` writes the full JSON envelope to a file (stdout then carries
a summary). With `--format json` and **no** `--out`, stdout carries the full
envelope — this is what the Tier 1 backend parses.

## validate envelope shape

```jsonc
{ "data": {
    "result": "passed" | "failed",
    "errorCount": 11, "warningCount": 0,
    "reportPath": "…",
    "diagnostics": {                       // keyed by diagnostic CODE
      "PBIR_ROLE_UNKNOWN": {
        "severity": "error",               // error | warning
        "items": [ { "message": "…: <abs file>", "file": "<abs file>", "path": "Data" } ]
      }
    }
} }
```

Codes observed on our `dist/` reports: `PBIR_ROLE_UNKNOWN`,
`PBIR_ROLE_MAX_EXCEEDED`, `PBIR_FORMATTING_OBJECT_UNKNOWN`,
`PBIR_FORMATTING_PROP_UNKNOWN`, `PBIR_THEME_ITEM_MISSING`,
`PBIR_THEME_NAME_MISSING_JSON_EXT`, `PBIR_SLICER_HEIGHT_BELOW_FLOOR`.

The Tier 1 backend (`tooling/report_quality/backends.py`) parses this into
`Violation`s: official `error` → `critical`, `warning` → `warning`.

## catalog metadata = the snapshot source

`catalog describe <visualType>` returns authoritative `roles` and
`requiredRoles`. These match our previously hard-coded queryState roles exactly:

| visualType | requiredRoles (official) | matches repo expectation |
|---|---|---|
| `lineChart` | `Category`, `Y` | ✓ |
| `cardVisual` | `Data` | ✓ |
| `tableEx` | `Values` | ✓ |
| `pivotTable` | `Values` (+ `Rows`, `Columns` roles) | ✓ |
| `scatterChart` | `X`, `Y` | ✓ |
| `slicer` | `Values` | ✓ |

This metadata is vendored offline by
[`refresh_authoring_metadata.py`](../../../../../tooling/report_quality/refresh_authoring_metadata.py)
into `tooling/schemas/pbir/authoring_metadata_snapshot.json` and read at runtime
by [`authoring_metadata.py`](../../../../../tooling/report_quality/authoring_metadata.py)
— so the Python floor gets authoritative roles **without** the CLI on site
(ADR 0001 snapshot pattern).

## Native vs. official — the diff (why we keep both)

Run on `COM-001_Sales_Performance.Report`:

| Validator | Finds | Blind to |
|---|---|---|
| **native** (`pbi-quality validate`) | measure references that don't resolve to any TMDL `_Measures` (Golden-Thread / KPI binding) | visual schema, role names, formatting props, theme registration |
| **official** (`powerbi-report-author validate`) | unknown/over-max roles, unknown formatting objects/props, theme & slicer-height issues | the semantic model — it never sees TMDL, so it cannot check measure existence |

They overlap on almost nothing → adopt the official CLI as a **Tier 1 oracle**
that augments the floor; never as a replacement.

### Concrete finding worth a follow-up

The official validator flags `PBIR_ROLE_UNKNOWN: Unknown role "Data" for
visualType "textbox"` on generated action-panel / smart-narrative textboxes. Our
generator currently allows the `Data` role on `textbox`. This is a real,
actionable signal to reconcile in the report generator (out of scope for the
ADR 0001 backend work; tracked here as a next step).

## Maintenance

Regenerate the snapshot whenever the CLI is bumped:

```bash
npm install -g @microsoft/powerbi-report-authoring-cli
python -m tooling.report_quality.refresh_authoring_metadata
```
