<!-- AUTO-GENERATED from docs/agent/ — do not edit directly. Run: python tooling/agent/generate_tool_configs.py -->

---
name: add-usecase-scaffold
description: Create a new use case with Business Factsheet and UseCase_Bracket (Lean 2.0). Use when adding a new use case, scaffolding COM-xxx or FIN-xxx, or the user asks to create a use case.
version: "1.0.0"
---

# Add Use Case Scaffold (Lean 2.0)

Generate a new use case directory with `Business_Factsheet.md` and `UseCase_Bracket.yaml` (SSOT), then validate structure.

## Workflow

1. **Use generation script** (if available):
   ```powershell
   .\tooling\generation\new_usecase.ps1 -Id "XXX-###" -Title "Use Case Title"
   ```
   - ID format: `COM-001`, `FIN-001`, `OPS-001`, `SCM-001`, `XD-001` (domain prefix + number).
2. **If script unavailable, create manually**:
   - Directory: `core/usecases/core/<ID>_Title/`
   - Files: `Business_Factsheet.md`, `UseCase_Bracket.yaml`
3. **Complete Business_Factsheet.md**:
   - Template: `core/usecases/templates/usecase_factsheet_business.md`
   - Frontmatter: `id`, `factsheet_type: business`
   - Content: Prose only (Executive Story, 3-30-300 Journey, Strategic Rationale, Key Questions, Governance).
   - **No YAML blocks in body** (Lean 2.0: all machine config in bracket).
4. **Complete UseCase_Bracket.yaml**:
   - Template: `core/usecases/templates/UseCase_Bracket_TEMPLATE.yaml`
   - Schema: `tooling/validation/schemas/usecase_bracket.schema.json`
   - Required keys: `schema_version`, `id`, `title`, `domain`, `governance` (owner_role, steward_role), `orchestration` (strategic_kpi_id, influencing_kpi_ids, action_code_ids), `value_driver_model`, `ux_layout_rules`
   - Governance roles must exist in `core/organization/org_roles.yaml` (or `showcases/aurora_group/organization/org_roles.yaml` in Aurora context)
   - KPI IDs must exist in `core/kpi_catalog/`
   - Action code IDs must exist in `core/action_codes/`
5. **Update inventory** (if registry builder exists):
   ```powershell
   py -3 tooling\ontology\registry_builder.py --out-dir tooling\ontology\out --strict
   ```
6. **Run Stage 1**:
   ```powershell
   .\tooling\run_stage1_checks.ps1
   ```

## Validation

After scaffold completion, verify:
- [ ] Both `Business_Factsheet.md` and `UseCase_Bracket.yaml` exist in `core/usecases/core/<ID>_Title/`
- [ ] Frontmatter `id` in factsheet matches bracket `id`
- [ ] Business Factsheet contains no YAML blocks in body (Lean 2.0: prose only)
- [ ] All KPI IDs in bracket `orchestration` resolve in `core/kpi_catalog/`
- [ ] Governance roles (`owner_role`, `steward_role`) exist in `core/organization/org_roles.yaml` (or Aurora showcase path)
- [ ] Action code IDs (if any) exist in `core/action_codes/`
- [ ] Stage 1 passes: `.\tooling\run_stage1_checks.ps1`

## Error Handling

**If generation script fails or doesn't exist:**
→ Create directory and files manually using templates in `core/usecases/templates/`

**If KPI ID doesn't exist in catalog:**
→ Use `add-kpi-reference-safely` skill OR add KPI to `core/kpi_catalog/` first

**If governance role doesn't exist:**
→ Add role to `core/organization/org_roles.yaml` (or `showcases/aurora_group/organization/org_roles.yaml` in Aurora context) before referencing in bracket

**If action code ID doesn't exist:**
→ Use `add-action-code-and-wire-up` skill OR create action code in `core/action_codes/` first

**If Stage 1 fails after scaffold:**
→ Use `fix-stage1-failure` skill to diagnose and fix specific check

## Guardrails

- **Business Factsheet is human-readable**: Prose only (no YAML blocks in body except frontmatter).
- **UseCase_Bracket is machine-readable SSOT**: All orchestration, governance, and technical config lives here.
- **Reference only**: Do not define KPI meaning or action logic in the use case; reference existing IDs.

## Key paths

- Templates: `core/usecases/templates/usecase_factsheet_business.md`, `UseCase_Bracket_TEMPLATE.yaml`
- New use case: `core/usecases/core/<ID>_Title/`
- Schemas: `tooling/validation/schemas/usecase_bracket.schema.json`
- Org roles: `core/organization/org_roles.yaml` or `showcases/aurora_group/organization/org_roles.yaml` (Aurora context)
- KPI catalog: `core/kpi_catalog/`
- Action codes: `core/action_codes/`
