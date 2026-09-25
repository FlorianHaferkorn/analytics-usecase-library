# Framework Expert (tool-agnostic)

When editing under `core/`, `tooling/ir/`, `data_contracts/`, `tooling/validation/`, or `tooling/ontology/`, you are in **Framework** context. Only framework artifacts apply; no tool-specific syntax.

## Scope

- **Use cases:** Business Factsheets, UseCase_Bracket.yaml — [artifacts-factsheets.md](docs/agent/rules/artifacts-factsheets.md).
- **KPI catalog:** core/kpi_catalog/ — governed definitions only.
- **Action codes:** core/action_codes/ — YAML per [artifacts-yaml.md](docs/agent/rules/artifacts-yaml.md).
- **Data contracts:** data_contracts/domains/, data_contracts/sources/.
- **IR (Intermediate Representation):** tooling/ir/ — adapter ABI; no tool-specific fields.
- **Validation / ontology:** tooling/validation/, tooling/ontology/ — scripts and schema-driven checks.

## Do not use here

- No TMDL, DAX, LookML, or other BI-tool syntax.
- No edits under `products/<tool>/` (those are tool-adapter scope).

## Skills to use

- edit-factsheet-safely, edit-usecase-bracket-safely
- add-kpi-reference-safely, add-action-code-and-wire-up
- assess-change-impact (for renames/removals)
- stage1-pre-commit, fix-stage1-failure

Follow [framework-conventions.md](docs/agent/rules/framework-conventions.md) and [stage1-awareness.md](docs/agent/rules/stage1-awareness.md). Run Stage 1 before committing.
