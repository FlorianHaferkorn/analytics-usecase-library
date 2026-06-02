<!-- AUTO-GENERATED from docs/agent/ â€” do not edit directly. Run: python tooling/agent/generate_tool_configs.py -->

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
   .\\tooling\\generator\\new_usecase.ps1 -Id "XXX-###" -Title "Use Case Title"
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
4. **Select the template variant** (required before filling `ux_layout_rules`):
   Apply the decision tree from `studio/docs/rebuild/PAGE_TYPE_TAXONOMY.md §4`:
   - "Are we on track?" → T1_Portfolio (4–6 KPIs) or T1_Trend (single KPI + momentum)
   - "Why are we off target?" → T2_DriverBridge (waterfall), T2_Comparative (segments), T2_Funnel (process loss)
   - "Where is execution breaking?" → T3_ExceptionQueue, T3_ProcessControl, T3_IncidentMonitor
   - "What should we do?" → T4_ActionDecision, T4_OptionComparison, T4_Sensitivity
   Set `ux_layout_rules.page_1_summary.template_variant` to the chosen variant ID.
   T4 variants require at least one entry in `orchestration.action_code_ids`.

5. **Complete UseCase_Bracket.yaml**:
   - Template: `core/usecases/templates/UseCase_Bracket_TEMPLATE.yaml`
   - Schema: `tooling/generator/schemas/usecase_bracket.schema.json`
   - Required keys: `schema_version`, `id`, `title`, `domain`, `governance` (owner_role, steward_role), `orchestration` (strategic_kpi_id, influencing_kpi_ids, action_code_ids), `value_driver_model`, `ux_layout_rules`
   - `ux_layout_rules.page_1_summary.template_variant` must match an entry in `template_manifest.yaml`
   - Governance roles must exist in `core/organization/org_roles.yaml` (or `showcases/aurora_group/organization/org_roles.yaml` in Aurora context)
   - KPI IDs must exist in `core/kpi_catalog/`
   - Action code IDs must exist in `core/action_codes/`
6. **Update inventory** (if registry builder exists):
   ```powershell
   py -3 tooling\ontology\registry_builder.py --out-dir tooling\ontology\out --strict
   ```
7. **Run Stage 1**:
   ```powershell
   .\tooling\run_stage1_checks.ps1
   ```

## Validation

After scaffold completion, verify:
- [ ] Both `Business_Factsheet.md` and `UseCase_Bracket.yaml` exist in `core/usecases/core/<ID>_Title/`
- [ ] Frontmatter `id` in factsheet matches bracket `id`
- [ ] Business Factsheet contains no YAML blocks in body (Lean 2.0: prose only)
- [ ] `ux_layout_rules.page_1_summary.template_variant` is set and resolves in `template_manifest.yaml`
- [ ] T4 variants have at least one `action_code_ids` entry
- [ ] All KPI IDs in bracket `orchestration` resolve in `core/kpi_catalog/`
- [ ] Governance roles (`owner_role`, `steward_role`) exist in `core/organization/org_roles.yaml` (or Aurora showcase path)
- [ ] Action code IDs (if any) exist in `core/action_codes/`
- [ ] Manifest alignment test passes: `py -3 -m pytest tooling/tests/test_template_manifest_alignment.py -v`
- [ ] Stage 1 passes: `.\tooling\run_stage1_checks.ps1`

## Error Handling

**If generation script fails or doesn't exist:**
â†’ Create directory and files manually using templates in `core/usecases/templates/`

**If KPI ID doesn't exist in catalog:**
â†’ Use `add-kpi-reference-safely` skill OR add KPI to `core/kpi_catalog/` first

**If governance role doesn't exist:**
â†’ Add role to `core/organization/org_roles.yaml` (or `showcases/aurora_group/organization/org_roles.yaml` in Aurora context) before referencing in bracket

**If action code ID doesn't exist:**
â†’ Use `add-action-code-and-wire-up` skill OR create action code in `core/action_codes/` first

**If Stage 1 fails after scaffold:**
â†’ Use `fix-stage1-failure` skill to diagnose and fix specific check

## Guardrails

- **Business Factsheet is human-readable**: Prose only (no YAML blocks in body except frontmatter).
- **UseCase_Bracket is machine-readable SSOT**: All orchestration, governance, and technical config lives here.
- **Reference only**: Do not define KPI meaning or action logic in the use case; reference existing IDs.

## Key paths

- Templates: `core/usecases/templates/usecase_factsheet_business.md`, `UseCase_Bracket_TEMPLATE.yaml`
- New use case: `core/usecases/core/<ID>_Title/`
- Schemas: `tooling/generator/schemas/usecase_bracket.schema.json`
- Org roles: `core/organization/org_roles.yaml` or `showcases/aurora_group/organization/org_roles.yaml` (Aurora context)
- KPI catalog: `core/kpi_catalog/`
- Action codes: `core/action_codes/`

