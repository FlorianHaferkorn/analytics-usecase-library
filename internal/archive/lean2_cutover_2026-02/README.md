# Lean 2.0 Cutover Archive (February 2026)

These files were removed from active use during the Lean 2.0 hard cutover.

## What was removed and why

| File | Reason |
|---|---|
| `validation/check_usecase_actioncode_map.ps1` | Validated `UseCase_ActionCode_Map.yaml`, which was deleted. Action code linkage now lives in `UseCase_Bracket.yaml` `orchestration.action_code_ids`. |
| `validation/check_factsheet_actioncode_map.ps1` | Cross-checked factsheet action codes against the map file. Same map dependency. |
| `schemas/usecase_actioncode_map.schema.json` | AI mirror of the map schema. Map no longer exists. |

## What replaced them

- **UseCase_Bracket.yaml** (`core/usecases/core/*/UseCase_Bracket.yaml`) is the exclusive SSOT for use case orchestration, including action code subscriptions.
- **registry_builder.py** validates referential integrity of brackets, KPIs, and action codes in one pass.
- **Stage 1 checks** (`tooling/run_stage1_checks.ps1`) enforce the Lean 2.0 contract; `run_all_checks.ps1` was updated to skip these archived checks.
