# `pbi` — agent-read ergonomics over `dist/` (Epic D)

In-house read/bulk-edit commands for the generated PBIP output, built for agents.
**No third-party runtime dependency.** This is the in-house parity for the useful
parts of [`pbir.tools`](https://github.com/maxanatsko/pbir.tools) — a capability
**benchmark only**: its non-commercial license rules it out as a shipped dependency
(consistent with "no third-party install requirement for customers").

Module: [`products/fabric/powerbi/tooling/pbi.py`](../tooling/pbi.py). It reuses the
same PBIR parser H7 trusts (`tooling/report_quality/pbir.py`).

## `pbi inspect` — list pages/visuals/bindings and model tables/measures

```bash
python3 -m products.fabric.powerbi.tooling.pbi inspect --model Commercial
python3 -m products.fabric.powerbi.tooling.pbi inspect --report COM-001_Sales_Performance
python3 -m products.fabric.powerbi.tooling.pbi inspect --all --json
```

- `--model <Domain>` → tables (column count + hidden count), the full measure list, relationship count.
- `--report <id|glob>` → each page → each visual (`type @ position`) → its **bindings**
  (the measures/columns each field-well role references).
- `--json` → machine-readable for agents.

## `pbi set` — wildcard bulk-set a visual property

```bash
# dry-run (default): show what would change
python3 -m products.fabric.powerbi.tooling.pbi set \
  'visual.objects.legend[0].properties.show={"expr":{"Literal":{"Value":"true"}}}' \
  --report COM-00 --type lineChart

# write it
python3 -m ... pbi set '<PATH>=<JSON value>' --type lineChart --apply
```

- Select with `--report` / `--page` / `--visual` / `--type` globs; set a JSON value at a
  dotted path (`a.b[0].c`, intermediates created).
- **Dry-run by default**; `--apply` writes via the shared `write_json`.
- **H7-protected:** `set` refuses any path under `visual.query` (bindings), so a bulk-set
  is binding-invariant by construction — Report Binding Integrity (H7) cannot regress.
  Verified: a format bulk-set across all Commercial line charts leaves H7 at 100%.

## `pbir.tools` parity (benchmark, not a dependency)

| `pbir.tools` | `pbi` (here) |
|---|---|
| `ls` / `tree` | `inspect --report` / `--all` |
| `model` | `inspect --model <Domain>` |
| `set` (wildcard) | `set <path>=<value> --type/--report/... [--apply]` |

Non-goal: bundling or importing `pbir.tools` (N1 in the plan).
