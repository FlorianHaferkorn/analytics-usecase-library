# YAML Artifacts

## Action codes (`core/action_codes/`)

- One YAML file per action code; single root object (no multi-document streams for action codes).
- **Required (Lean 2.0):** `schema_version`, `id`, `name`, `owner_domain`, `impact_dimension`, `status`, `kpis` (IDs only: `trigger_kpis`, `guardrail_kpis`, `outcome_kpis`), `trigger`, `impact`, `operational_execution`, `governance`.
- **KPI references:** Every KPI ID in `kpis.*` must exist in `core/kpi_catalog/`.
- **Use case links:** Defined in `UseCase_Bracket.yaml` `orchestration.action_code_ids` (not in action code files).
- Template: `core/templates/action_codes/ActionCode_TEMPLATE.md`. Schema: `tooling/generator/schemas/action_code.schema.json`.
- Do not define new KPI meaning or targets in action code YAML; only reference governed KPI IDs.

## UseCase_Bracket (`core/usecases/core/*/UseCase_Bracket.yaml`)

- **SSOT** for use case orchestration. Links strategic KPI, influencing KPIs, action codes, value driver model, UX layout rules, and governance roles.
- Schema: `tooling/generator/schemas/usecase_bracket.schema.json`.
- Validated by `validate_factsheets.ps1` (bracket existence and minimum keys) and `registry_builder.py` (referential integrity).

## Decision spines

- **Path:** `core/action_codes/decision_spines/` — `DecisionSpine_UseCase_Map.yaml` and per-spine YAML files.
- Map and spine files are validated by `check_decision_spines.ps1`; keep references consistent with use cases and action codes.

## Data contracts

- **Domains:** `data_contracts/domains/*.yaml` — domain-level contract structure.
  One definition per table (Bus-Matrix): a table another domain owns is referenced with
  `conformed_from: <domain>` (+ optional `uses_columns`), never copied — see `data_contracts/domains/README.md`.
- **Sources:** `data_contracts/sources/*.yaml` — source-level mappings.
- Schema: `tooling/generator/schemas/data_contract.schema.json` — run on every contract by `tooling/validation/check_validate_data_contracts.py` (Stage 1); tables, columns, `quality_rules` and `settings` are closed, so a new field goes into the schema first.

## General

- Use spaces for YAML indentation (conventional). No inline redefinition of KPI meaning. Keep IDs stable; when deprecating action codes, set `status: deprecated` and use `lifecycle.replaced_by`.
