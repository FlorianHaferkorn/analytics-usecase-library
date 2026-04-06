<!-- AUTO-GENERATED from docs/agent/ — do not edit directly. Run: python tooling/agent/generate_tool_configs.py -->

---
name: fix-stage1-failure
description: Diagnose and fix Stage 1 CI check failures. Use when Stage 1 checks fail, validation errors occur, or the user asks how to fix a specific check failure.
version: "1.0.0"
---

# Fix Stage 1 Failure

Map Stage 1 check failures to root causes and propose concrete fixes without applying changes until confirmed.

## Workflow

1. **Identify the failing check** from the error output (check name appears in the script output).
2. **Map to root cause** using the table below.
3. **Propose specific file/field changes** with exact paths and values.
4. **Ask for confirmation** before applying fixes.
5. **Re-run Stage 1** after fixes to verify.

## Check failure → fix mapping

| Failing Check | Likely Cause | Fix Path |
|--------------|--------------|----------|
| `check_schema_validation` | Schema violation in action code, bracket, or org_roles | Check `tooling/ai/schemas/*.schema.json`; fix required/missing keys |
| `check_factsheet_vs_kpi` | KPI ID referenced in factsheet/bracket doesn't exist | Add KPI to `core/kpi_catalog/` OR fix KPI ID reference |
| `validate_kpi_catalog` | KPI catalog structure issue | Fix `core/kpi_catalog/` structure per templates |
| `check_action_codes_vs_kpi` | KPI ID in action code doesn't exist | Add KPI to catalog OR fix action code `kpis.*` references |
| `check_factsheet_action_codes` | Action code ID mismatch | Add action code to `core/action_codes/` OR update `UseCase_Bracket.yaml` `orchestration.action_code_ids` |
| `check_forbidden_content` | Forbidden fields in factsheet | Remove `definition`, `target`, `lineage`, `unit`, `grain`, `interpretation` from factsheets |
| `check_duplicate_ids` | Duplicate ID across artifacts | Rename or consolidate duplicate IDs |
| `check_ssot_markers` | SSOT marker in wrong location | Remove SSOT marker or move to governed artifact |
| `check_decision_spines` | Map/spine inconsistency | Fix `DecisionSpine_UseCase_Map.yaml` or spine YAML file |
| `validate_factsheets` | Missing bracket or factsheet structure issue | Add `UseCase_Bracket.yaml` OR fix factsheet frontmatter/sections |
| `check_docs_refs` | Invalid doc reference | Fix broken reference path |
| `check_validate_data_contracts` | Domain contract invalid (missing domain/dimension/fact, dimension name, fact grain) | Fix YAML in `core/data_contracts/domains/*.yaml` per schema |
| `check_registry_builder` | Registry builder governance failure (--strict) | Fix referential integrity: use cases, brackets, action codes, KPI catalog; see `tooling/ontology/registry_builder.py` |

## Guardrails

- **KPI catalog is SSOT**: Never redefine KPI meaning, targets, or lineage in use cases or action codes.
- **Action codes are SSOT for logic**: Use cases reference action code IDs; they do not define trigger logic.
- **Factsheets are human-readable**: Machine-readable config belongs in `UseCase_Bracket.yaml`.
- **Schema compliance is mandatory**: Use `tooling/ai/schemas/*.schema.json` as authority.
- Re-run Stage 1 after every fix to catch cascading issues.
