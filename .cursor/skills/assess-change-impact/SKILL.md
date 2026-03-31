<!-- AUTO-GENERATED from docs/agent/ — do not edit directly. Run: python tooling/agent/generate_tool_configs.py -->

---
name: assess-change-impact
description: Assess blast radius before renaming, deleting, or deprecating KPI IDs, action code IDs, or governance roles. Use when making changes that could break downstream references.
---

# Assess Change Impact (Lean 2.0)

Pre-flight analysis to identify all downstream references before making breaking changes to governed artifacts (KPIs, action codes, roles).

## Workflow

1. **Identify what's being changed**:
   - KPI ID (rename/delete/deprecate)
   - Action code ID (rename/delete/deprecate)
   - Governance role ID (rename/delete)
2. **Scan for all references** (use Grep or search tools):
   - **KPI ID** → search in:
     - `core/usecases/**/UseCase_Bracket.yaml` (`orchestration.strategic_kpi_id`, `influencing_kpi_ids`, `value_driver_model.primary_driver`)
     - `core/action_codes/**/*.yaml` (`kpis.trigger_kpis`, `guardrail_kpis`, `outcome_kpis`)
   - **Action code ID** → search in:
     - `core/usecases/**/UseCase_Bracket.yaml` (`orchestration.action_code_ids`)
   - **Role ID** → search in:
     - `core/usecases/**/UseCase_Bracket.yaml` (`governance.owner_role`, `governance.steward_role`)
     - `core/action_codes/**/*.yaml` (`owner_role`, `steward_role` — top-level fields in Lean 2.0)
3. **Report blast radius**:
   - Count affected artifacts: "This change will affect X use cases, Y action codes, Z brackets"
   - List specific files and line numbers
   - Estimate effort: "Requires updates in N files across M use cases"
4. **Propose fix strategy**:
   - **Option A (safe)**: Update all references (use find-and-replace with validation)
   - **Option B (gradual)**: Deprecate gracefully (keep old ID, add new, mark old as deprecated in schema, remove after migration period)
   - **Option C (risky)**: Delete without migration (only if zero references found)
5. **Ask for confirmation** before proceeding with any changes

## Search patterns

Use these exact patterns when scanning for references:

### KPI ID references
```bash
# Brackets (orchestration)
rg "<kpi_id>" core/usecases/ --glob "UseCase_Bracket.yaml"

# Action codes (kpis section)
rg "<kpi_id>" core/action_codes/ --glob "*.yaml"
```

### Action code ID references
```bash
# Brackets (orchestration.action_code_ids)
rg "<action_code_id>" core/usecases/ --glob "UseCase_Bracket.yaml"
```

### Role ID references
```bash
# Brackets (governance)
rg "owner_role.*<role_id>|steward_role.*<role_id>" core/usecases/ --glob "UseCase_Bracket.yaml"

# Action codes (top-level in Lean 2.0)
rg "^owner_role:.*<role_id>|^steward_role:.*<role_id>" core/action_codes/ --glob "*.yaml"
```

## Output format

Present findings in this structure:

```markdown
## Impact Assessment: <artifact_type> "<artifact_id>"

### Blast Radius
- **Use cases affected**: X
- **Action codes affected**: Y
- **Brackets affected**: Z
- **Total files requiring updates**: N

### Affected Artifacts

#### Use Cases
- `core/usecases/core/COM-001_Sales_Performance/UseCase_Bracket.yaml` (line 18: orchestration.strategic_kpi_id)
- ...

#### Action Codes
- `core/action_codes/Commercial/C-M2.1.yaml` (line 12: kpis.trigger_kpis)
- ...

### Recommended Strategy

**Option A (Recommended)**: Update all references
- Effort: ~N minutes (Y files to edit)
- Risk: Low (all references updated atomically)
- Steps:
  1. Update KPI catalog definition
  2. Find-and-replace "<old_id>" → "<new_id>" in affected files
  3. Run Stage 1 to verify

**Option B**: Deprecate gracefully
- Effort: ~M minutes (add deprecation marker + new ID)
- Risk: Medium (requires migration period management)
- Steps:
  1. Keep old KPI ID in catalog, mark as deprecated
  2. Add new KPI ID in catalog
  3. Update high-priority use cases to new ID
  4. Remove old ID after 30-day grace period

Proceed? (y/n)
```

## Validation

After making changes (if user confirms), verify:
- [ ] All affected files updated
- [ ] Old ID removed from all references (or marked deprecated)
- [ ] New ID exists in SSOT (catalog/framework)
- [ ] Stage 1 passes: `.\tooling\run_stage1_checks.ps1`
- [ ] No orphaned references remain

## Guardrails

- **Bracket is SSOT**: All machine-readable KPI IDs, action code IDs, and governance roles live in `UseCase_Bracket.yaml`.
- **No factsheet YAML blocks**: Business factsheets are human-readable only.
- **Registry validation**: `registry_builder.py --strict` enforces referential integrity (KPI Catalog, Action Codes, Org Roles).

## Key paths

- Templates: `core/usecases/templates/usecase_factsheet_business.md`, `UseCase_Bracket_TEMPLATE.yaml`
- Schemas: `tooling/validation/schemas/usecase_bracket.schema.json`
- KPI catalog: `core/kpi_catalog/`
- Action codes: `core/action_codes/`
- Org roles: `core/organization/org_roles.yaml` or `showcases/aurora_group/organization/org_roles.yaml` (Aurora context)
