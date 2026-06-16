---
name: add-action-code-and-wire-up
description: Create or update action codes and wire them into use cases. Use when creating action code YAML files, updating orchestration.action_code_ids, or linking action codes to use cases.
version: "1.0.0"
license: MIT
source: ALUCA (Analytics Library of Use Cases) — governance overlay
---

<!-- AUTO-GENERATED from docs/agent/skills/ — do not edit; run tooling/generator/generate_tool_configs.py -->

# Add Action Code and Wire Up

Create action code YAML files in the framework, validate all references, and wire them into affected use case brackets.

## Workflow

1. **Use template and schema**:
   - Template: `core/templates/action_codes/ActionCode_TEMPLATE.md`
   - Schema: `tooling/generator/schemas/action_code.schema.json`
   - Required fields: `schema_version`, `id`, `name`, `owner_domain`, `impact_dimension`, `status`, `kpis`, `trigger`, `impact`, `operational_execution`, `governance`.
2. **Create action code file**:
   - Path: `core/action_codes/<Domain>/<ID>.yaml`
   - ID format: `<prefix>-<topic><index>` (e.g., `C-M2.1` for Commercial/Margin, `F-C1.1` for Finance/Cash, `O-A2.1` for Operations/Asset).
3. **Validate KPI references**:
   - Every `kpi_id` in `kpis.trigger_kpis`, `guardrail_kpis`, `outcome_kpis` must exist in `core/kpi_catalog/`.
   - Use `add-kpi-reference-safely` skill if KPI doesn't exist.
4. **Validate governance roles**:
   - Ensure `governance.owner_role` and `steward_role` exist in `core/organization/org_roles.yaml` (or `showcases/aurora_group/organization/org_roles.yaml` in Aurora context).
5. **Wire into use cases**:
   - For each relevant use case, add the action code ID to `orchestration.action_code_ids` in `UseCase_Bracket.yaml`.
   - Example:
     ```yaml
     orchestration:
       action_code_ids:
         - C-M2.1
         - C-M2.2
     ```
6. **Run validation**:
   ```powershell
   .\tooling\validation\check_action_codes_vs_kpi.ps1
   .\tooling\validation\check_factsheet_action_codes.ps1
   ```

## Validation

After creating action code, verify:
- [ ] All `kpi_id` references in `kpis.trigger_kpis`, `guardrail_kpis`, `outcome_kpis` exist in `core/kpi_catalog/`
- [ ] Governance roles (`owner_role`, `steward_role`) exist in `core/organization/org_roles.yaml` (or Aurora showcase path)
- [ ] Action code ID added to relevant `UseCase_Bracket.yaml` files (`orchestration.action_code_ids`)
- [ ] `check_action_codes_vs_kpi.ps1` passes
- [ ] `check_factsheet_action_codes.ps1` passes
- [ ] `check_schema_validation.ps1` passes (validates action code structure)

## Error Handling

**If KPI ID doesn't exist:**
→ Use `add-kpi-reference-safely` skill OR add to `core/kpi_catalog/` first

**If bracket missing for target use case:**
→ Run `add-usecase-scaffold` skill to create use case structure first

**If schema validation fails:**
→ Check `tooling/generator/schemas/action_code.schema.json` for required keys
→ Verify `schema_version`, `id`, `name`, `owner_domain`, `impact_dimension`, `status` are present

**If governance role doesn't exist:**
→ Add to `core/organization/org_roles.yaml` (or Aurora showcase path) before referencing in action code

**If check_factsheet_action_codes fails:**
→ Action code ID in bracket but file doesn't exist: create action code file
→ Action code file exists but not in bracket: add to `UseCase_Bracket.yaml` `orchestration.action_code_ids`

**If wiring fails (bidirectional linking broken):**
→ Ensure action code ID appears in ALL relevant use case brackets
→ Ensure brackets only reference action codes that exist in `core/action_codes/`

## Guardrails

- **Do NOT define KPI meaning** in action code YAML; only reference KPI IDs.
- **Action codes are SSOT for logic**: Use cases subscribe to action codes; they do not redefine trigger conditions.
- **Bidirectional linking**: Action code file + bracket `orchestration.action_code_ids` must be consistent.
- Schema validation catches missing required fields; run `check_schema_validation.ps1` if unsure.

## Key paths

- Action codes: `core/action_codes/<Domain>/`
- Brackets: `core/usecases/core/<UseCase>/UseCase_Bracket.yaml`
- Org roles: `core/organization/org_roles.yaml` or `showcases/aurora_group/organization/org_roles.yaml` (Aurora context)
- KPI catalog: `core/kpi_catalog/`
