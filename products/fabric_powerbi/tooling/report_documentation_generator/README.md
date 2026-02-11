# Report Documentation Generator

Generates **human-readable report documentation** (Markdown) from a PBIP report and use case factsheets. Aligns with [report_documentation_generator_spec.md](../report_documentation_generator_spec.md).

## Purpose

- **Traceability** — What the report contains and why
- **Onboarding** — How users understand and use the report
- **Governance** — KPIs, action codes, use case references

## Usage

From the repository root or from this directory:

```powershell
# From repo root (recommended)
python products/fabric_powerbi/tooling/report_documentation_generator/generate_report_documentation.py --report showcases/aurora_group/reports/COM-001.Report

# With explicit use case and output path
python products/fabric_powerbi/tooling/report_documentation_generator/generate_report_documentation.py --report path/to/Report --use-case COM-001 --output path/to/Report_Documentation_COM-001.md
```

**Arguments:**

| Argument | Required | Description |
|----------|----------|-------------|
| `--report` | Yes | Path to the `.Report` folder (PBIP) |
| `--use-case` | No | Use case ID (e.g. COM-001). Inferred from report path or page names if omitted |
| `--output` | No | Output Markdown path. Default: `reporting/Report_Documentation_<id>.md` next to the report parent, or alongside the report |
| `--repo-root` | No | Repository root; auto-detected if omitted |

## Output

The generator produces Markdown containing:

1. **Report metadata** — Use case, domain, owner, version, theme, purpose, target audience, usage rhythm
2. **Business questions answered** — From Business Factsheet section 2
3. **Strategic alignment** — Required KPIs, decision type
4. **Per-page documentation** — Page display name, type (T1–T4), layer (3/30/300), visuals (name, type, slot)
5. **Traceability** — Links to use case factsheets, KPI catalog, action codes, page templates

Inputs are read from:

- PBIP: `definition/report.json`, `definition/pages/pages.json`, each `definition/pages/<PageName>/page.json` and `visuals/*/visual.json`
- Framework: Business Factsheet (from `core/usecases/core/<id>_*/Business_Factsheet.md`), `UseCase_PageTemplate_Map.yaml`

## Where output is stored

- If the report is under `showcases/<name>/reports/`, output defaults to `showcases/<name>/reporting/Report_Documentation_<UseCaseId>.md`.
- Otherwise, output is written next to the report folder or to the path given by `--output`.

## See also

- [report_documentation_generator_spec.md](../report_documentation_generator_spec.md) — Full specification
- [fabric_powerbi.md](../../docs/fabric_powerbi.md) — Implementation guide (section on Report Documentation Generator)
