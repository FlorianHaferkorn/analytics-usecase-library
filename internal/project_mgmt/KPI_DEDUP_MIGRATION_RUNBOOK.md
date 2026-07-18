# KPI de-duplication — physical-removal migration runbook (Fabric-gated)

Status: **prepared, not executed.** The SSOT-level consolidation is already live — each twin carries
a `canonical_kpi_id` pointer and `tooling/validation/check_standard_ref.py` blocks any new duplicate.
This runbook covers the *physical* removal: delete the twin KPIs, rewire their references, rename the
duplicate measures inside the domain models, rebind the affected reports, regenerate goldens/ontology.

**Why it is a runbook and not a landed change.** The dist reports/models are a **curated,
`no_overwrite` showcase** (there is no "regenerate dist from catalog" path). The same calc is
**materialised separately in several domain semantic models** under different measure names. And the
report→model binding uses a PBIR `nativeQueryRef` that can be a **display alias differing from the
defined measure name** (e.g. XD-003/XD-004 bind `OTIF %` while the Experience model defines it as
`OTIF % (XD)` — see the `/// OTIF % - supply.otif.pct` comment). So measure resolution cannot be
certified on Linux: the only authoritative check that a renamed measure / rebound report still loads
is **Power BI Desktop**. Execute this in the Windows env, opening each edited model + report.

## Twin → canonical, and where the duplicate measure lives

| Twin KPI | Canonical KPI | Twin measure (model) | Bound in a report? |
|---|---|---|---|
| `ops.otif.pct` | `supply.otif.pct` | `Ops OTIF %` (Experience) | no |
| `scm.service_level.pct` | `supply.otif.pct` | `Supply Chain Service Level %` (Finance) | **FIN-001** Detail_Matrix |
| `ops.service_level.pct` | `supply.otif.pct` | `Operations Service Level %` (Finance) | no |
| `ops.inventory.value.amount` | `fin.liquidity.inventory.amount` | `Inventory Value Amount` (Operations) | no |
| `ops.production.volume` | `ops.throughput.units` | `Production Volume Units` (Finance) | **FIN-002** Detail_Matrix |
| `ops.yield.pct` | `ops.quality.pct` | `Yield %` (Finance) | **FIN-002** Detail_Matrix |
| `svc.nps.index` | `crm.nps.index` | *(not materialised)* | no |

Exact report-binding scope (verified via `"nativeQueryRef": "<exact name>"`, word-boundary — beware
substring matches like `First Pass Yield %` ⊃ `Yield %`): **only FIN-001 and FIN-002** bind a twin
measure. Everything else is SSOT/doc-only on the report side.

Measure-rename topology (each canonical measure currently lives in a *different* model than its twin,
so an in-model rename is collision-free) — **except** the two Finance service-level twins, which both
collapse to one `OTIF %`: rename one, delete the other, point both consumers at it. Note the
Experience model already materialises `supply.otif.pct` as `OTIF % (XD)`; reconcile names in Desktop
rather than assuming a fresh `OTIF %`.

## Per-twin SSOT checklist (Linux-safe, but must land atomically with the dist edits)

1. `core/kpi_catalog/kpis/<twin>.yaml` — delete; remove its line from `kpis/_index.yaml`.
2. Other KPIs' `technical.depends_on_measures` — replace twin→canonical + **dedupe**
   (`cost.unit.amount.yaml` lists both `ops.production.volume` and `ops.yield.pct`).
3. `core/usecases/**/UseCase_Bracket.yaml` — `orchestration.*_kpi_ids` + `value_driver_model.formula`
   prose: replace + **dedupe the list** (FIN-002 references three twins).
4. `core/usecases/**/Business_Factsheet.md` — KPI table, `### 3.1 Standards basis`, prose; drop the
   row if the canonical is already listed.
5. `core/usecases/**/Domain_Evidence_Pack.yaml` — replace.
6. `core/semantic_models/domains/*/measures/<twin>.yaml` — delete the twin measure-def.
7. `products/fabric/powerbi/specs/fabric_measure_overlay.yaml` — remove the twin key.
8. `products/fabric/powerbi/blueprints/*.yaml` — replace twin→canonical.
9. `core/action_codes/**`, docs (`extended_playbook.md`, `UseCase_Inventory.md`,
   `Measure_Dictionary_*.md`, `tooling/generator/prompts/*`) — replace.
10. `core/templates/business_case/presets/<twin>.yaml` (`ops.otif.pct.yaml`, `svc.nps.index.yaml`
    exist) — delete; ensure the canonical has a preset.
11. `studio/src/app/api/core/presets/[kpiId]/route.ts`, `studio/src/lib/core/golden20.ts` — replace.
12. Standards audit docs under `core/kpi_catalog/standards/` — leave (point-in-time record).

## Dist edits (delicate — Desktop-validate each model)

- Finance `_Measures.tmdl`: rename `Production Volume Units`→(canonical throughput name),
  `Yield %`→(canonical quality name), `Supply Chain Service Level %`→(canonical OTIF name); **delete**
  `Operations Service Level %`. Experience: reconcile `Ops OTIF %` with the existing `OTIF % (XD)`.
  Operations: rename `Inventory Value Amount`→(canonical inventory name). Keep the DAX; match the
  canonical measure's exact name **as already used in that model's report bindings**.
- Rebind **FIN-001** Detail_Matrix (`Supply Chain Service Level %`) and **FIN-002** Detail_Matrix
  (`Production Volume Units`, `Yield %`): update `Property`, `queryRef` (`_Measures.<name>`),
  `nativeQueryRef`.
- After each model edit, **open the model + its report in Power BI Desktop**; a dangling reference
  throws the columnless/`get_Islands()` load error (KNOWN_ERRORS) that no Linux gate catches.

## Regeneration + validation

- Regenerate: `tooling/codegen/kpi_catalog_files.py render`; ontology (`tooling/ir/build_ir.py`,
  `tooling/ontology/registry_builder.py`); goldens
  (`python -m tooling.superversion.from_aluca <bracket> --out tooling/superversion/tests/golden/<UC>.json`)
  for every affected UC; update `tooling/superversion/tests/test_dax_parity_legacy.py`.
- Linux (necessary, not sufficient): `bash tooling/run_local_ci_check.sh` — drift-gate,
  `check_standard_ref.py --strict` (its duplicate-set report should drop to 0),
  `check_usecase_quality.py`, pytest, `validate_bindings.py`.
- **Windows (authoritative):** Stage-1 + Fabric quality gate, and open each edited `.SemanticModel`
  and its report in Power BI Desktop.

## Gap worth closing first (measure-name resolution)

`products/fabric/powerbi/tooling/validate_bindings.py` checks projection **structure** only — it does
not resolve each report `nativeQueryRef` against a `measure '<name>'` in the model named by
`definition.pbir → datasetReference.byPath.path`. A resolution check would give this migration a real
local safety net, **but** it must account for PBIR `nativeQueryRef` being a display alias that can
differ from the defined measure name (a naive scan reports false positives — e.g. `OTIF %` vs
`OTIF % (XD)`). Build + Desktop-calibrate that check before trusting it or wiring it into CI; it is
the right long-term guard for the exact error class this migration risks.
