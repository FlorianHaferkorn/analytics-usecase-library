# Edit UseCase_Bracket Safely (Lean 2.0)

Maintain bracket as the SSOT for use case orchestration; validate all references and ensure referential integrity with catalog, action codes, and org roles.

## Workflow

1. **Use schema as authority**:
   - Schema: `tooling/generator/schemas/usecase_bracket.schema.json`
   - Required keys: `schema_version`, `id`, `title`, `domain`, `governance`, `orchestration`, `value_driver_model`, `ux_layout_rules`
2. **Governance section**:
   - Required: `owner_role`, `steward_role`
   - All roles must exist in `core/organization/org_roles.yaml` (or `showcases/aurora_group/organization/org_roles.yaml` in Aurora context)
   - Check role availability before assigning
3. **Orchestration section**:
   - `strategic_kpi_id`: single KPI ID (must exist in `core/kpi_catalog/`)
   - `influencing_kpi_ids`: list of KPI IDs (must exist in catalog)
   - `action_code_ids`: list of action code IDs (must exist in `core/action_codes/`)
4. **Value driver model**:
   - `formula`: causal formula (e.g., `GM% = (NetSales - COGS) / NetSales`)
   - `primary_driver`: KPI ID (must be a dependency of `strategic_kpi_id` per catalog `depends_on_measures` or `causal_links`)
   - `impact_logic`: prose explanation of how primary_driver affects strategic KPI
5. **UX layout rules**:
   - `page_1_summary`: component_3s (KPI cards), component_30s (diagnostic visuals)
   - `page_2_execution`: component_300s (evidence grain, action panel)
   - To edit visual types per slot without YAML: use **UX Layout Editor** — `streamlit run tooling/ux_layout_editor/app.py` (see `tooling/ux_layout_editor/README.md`). Im Editor siehst du eine Live-Preview der gewählten Visual-Typen. Draft from orchestration: `py -3 tooling/ux_layout_editor/draft_ux_layout.py --use-case <ID> [--apply]`.
6. **Run validation**:
   ```powershell
   .\tooling\run_stage1_checks.ps1
   ```

## Validation

After editing bracket, verify:
- [ ] All required keys present per schema
- [ ] Governance roles (`owner_role`, `steward_role`) exist in `core/organization/org_roles.yaml` (or Aurora showcase path)
- [ ] All KPI IDs in `orchestration` exist in `core/kpi_catalog/`
- [ ] All action code IDs exist in `core/action_codes/`
- [ ] `primary_driver` aligns with `strategic_kpi_id` dependencies (registry will warn if misaligned)
- [ ] Stage 1 passes: `.\tooling\run_stage1_checks.ps1`
- [ ] Registry strict passes: `py -3 tooling/ontology/registry_builder.py --out-dir tooling/ontology/out --strict`

## Error Handling

**If check_schema_validation fails:**
→ Check `tooling/generator/schemas/usecase_bracket.schema.json` for required keys
→ Verify `schema_version: "2.0"`, `id`, `title`, `domain`, `governance`, `orchestration` are present

**If governance role doesn't exist:**
→ Add `owner_role` or `steward_role` to `core/organization/org_roles.yaml` (or Aurora showcase path) first
→ Role IDs are snake_case (e.g., `head_of_sales`)

**If KPI ID doesn't exist:**
→ Use `add-kpi-reference-safely` skill OR add to `core/kpi_catalog/` first
→ Affects `orchestration.strategic_kpi_id`, `influencing_kpi_ids`, `value_driver_model.primary_driver`

**If action code ID doesn't exist:**
→ Use `add-action-code-and-wire-up` skill OR create action code file first
→ Affects `orchestration.action_code_ids`

**If primary_driver validation warning:**
→ Registry warns if `primary_driver` is not a dependency of `strategic_kpi_id`
→ Fix: update `primary_driver` to a KPI from the catalog's `technical.depends_on_measures` for the strategic KPI, or add `depends_on_measures` metadata to the catalog

**If YAML syntax error:**
→ Check indentation (use spaces, not tabs for YAML)
→ Ensure lists use `-` prefix
→ Ensure strings with special chars are quoted

## Guardrails

- **Bracket is SSOT for orchestration**: Machine-readable config lives here, not in Business Factsheet.
- **Reference integrity**: All KPI IDs, action code IDs, and governance roles must resolve to governed artifacts.
- **Bidirectional consistency**: `action_code_ids` here must match action codes that reference this use case.
- **Schema compliance mandatory**: Missing required keys fail `check_schema_validation.ps1`.

## Common errors

| Error | Cause | Fix |
|-------|-------|-----|
| Missing `owner_role` | Required key absent | Add `governance.owner_role` from `org_roles.yaml` |
| Invalid KPI ID | KPI doesn't exist | Add to `core/kpi_catalog/` OR fix reference |
| Action code mismatch | ID not in framework | Add to `core/action_codes/` OR remove from bracket |
| Primary driver warning | Not in strategic KPI dependencies | Align `primary_driver` with catalog's `depends_on_measures` |

## Key paths

- Bracket: `core/usecases/core/<UseCase>/UseCase_Bracket.yaml`
- Template: `core/usecases/templates/UseCase_Bracket_TEMPLATE.yaml`
- Schema: `tooling/generator/schemas/usecase_bracket.schema.json`
- Org roles: `core/organization/org_roles.yaml` or `showcases/aurora_group/organization/org_roles.yaml` (Aurora context)
- KPI catalog: `core/kpi_catalog/`
- Action codes: `core/action_codes/`
