<!-- AUTO-GENERATED from docs/agent/ — do not edit directly. Run: python tooling/agent/generate_tool_configs.py -->

---
name: edit-factsheet-safely
description: Edit Business factsheets without breaking Stage 1 (Lean 2.0). Use when editing Business_Factsheet.md or any use case markdown. Technical Factsheets no longer exist.
version: "1.0.0"
---

# Edit Factsheet Safely (Lean 2.0)

Preserve factsheet structure, frontmatter, and required sections; keep KPI references aligned with catalog; edit machine-readable config in `UseCase_Bracket.yaml` only.

## Lean 2.0 SSOT rules

- **Business Factsheet (`Business_Factsheet.md`):** Human-readable prose only. No machine-readable YAML blocks (no `required_kpis`, no `kpi_to_measure_mapping`).
- **UseCase_Bracket.yaml:** Machine-readable SSOT for orchestration (KPI IDs, action code IDs, value driver model, UX layout rules, governance roles).
- **Technical Factsheet:** Deleted in Lean 2.0 hard-cutover; no longer part of the framework.

## Workflow

1. **Preserve frontmatter** (Business Factsheet):
   - Required: `id` (use case ID), `factsheet_type: business`
   - Must be first block in file (YAML fenced by `---`)
2. **Business factsheet sections** (prose/human context):
   - Metadata (section 0)
   - Executive Story / Business Value
   - The 3-30-300 Journey (UX Strategy)
   - Strategic Rationale & Causal Logic
   - Key Business Questions
   - Governance & Trust
3. **Machine-readable config** (edit `UseCase_Bracket.yaml` instead):
   - `orchestration.strategic_kpi_id`, `influencing_kpi_ids`, `action_code_ids`
   - `governance.owner_role`, `steward_role` (must exist in `core/organization/org_roles.yaml` or `showcases/aurora_group/organization/org_roles.yaml` when in Aurora context)
   - `value_driver_model.formula`, `primary_driver`, `impact_logic`
   - `ux_layout_rules.page_1_summary`, `page_2_execution`
4. **KPI references**:
   - All KPI IDs must exist in `core/kpi_catalog/` (SSOT).
   - No KPI definitions or metadata in factsheets; they reference KPI IDs only.
5. **Run validation**:
   ```powershell
   .\tooling\run_stage1_checks.ps1
   ```

## Validation

After editing Business Factsheet or Bracket, verify:
- [ ] Frontmatter intact in Business Factsheet (`id`, `factsheet_type: business`)
- [ ] Business Factsheet contains no machine-readable YAML blocks (no `required_kpis`, no `kpi_to_measure_mapping`)
- [ ] All KPI IDs in `UseCase_Bracket.yaml` exist in `core/kpi_catalog/`
- [ ] All action code IDs in bracket exist in `core/action_codes/`
- [ ] Governance roles exist in `core/organization/org_roles.yaml` (or `showcases/aurora_group/organization/org_roles.yaml` in Aurora context)
- [ ] Stage 1 passes: `.\tooling\run_stage1_checks.ps1`

## Error Handling

**If validate_factsheets fails:**
→ Check frontmatter is first block and properly fenced with `---`
→ Verify `id` and `factsheet_type: business` are present
→ Ensure factsheet is prose only (no YAML blocks in body)

**If check_factsheet_vs_kpi fails:**
→ KPI ID in bracket doesn't exist: add to catalog OR fix typo
→ Use exact format: `domain.topic.metric`

**If check_forbidden_content fails:**
→ Remove any embedded KPI definitions or metadata from factsheet body
→ KPI definitions belong in `core/kpi_catalog/` only

**If schema validation fails (bracket):**
→ Check bracket against `tooling/generator/schemas/usecase_bracket.schema.json`
→ Verify required keys: `id`, `title`, `domain`, `governance`, `orchestration`, `value_driver_model`, `ux_layout_rules`

## Examples

### Example 1: Business Factsheet (Lean 2.0)

**Correct structure (prose only)**:

```markdown
id: COM-001
factsheet_type: business

# Use Case: COM-001 - Sales Performance vs Plan & LY

## 0. Metadata

Use Case ID: COM-001
Domain: Commercial
Business Owner (Role): Head of Sales
Status: Active

## 1. Executive Story (The "Why")

Purpose: Enable Sales leadership to identify and address revenue gaps...

Business Value: Reduction of discount leakage by 2%, faster reaction to volume drops.

...
```

No YAML blocks in body. All machine-readable config is in `UseCase_Bracket.yaml`.

### Example 2: UseCase_Bracket.yaml (machine SSOT)

```yaml
schema_version: "2.0"
id: "COM-001"
title: "Sales Performance vs Plan & LY"
domain: "Commercial"
governance:
  owner_role: "head_of_sales"  # Must exist in org_roles.yaml
  steward_role: "sales_bi_lead"
orchestration:
  strategic_kpi_id: "margin.gm.pct"
  influencing_kpi_ids:
    - "sales.net_sales.amount"
    - "sales.price.realization_pct"
  action_code_ids:
    - "C-M2.1"
    - "C-S1.1"
value_driver_model:
  formula: "GM% = (NetSales - COGS) / NetSales"
  primary_driver: "sales.net_sales.amount"
  impact_logic: "Increase net sales to improve GM%..."
ux_layout_rules:
  page_1_summary:
    component_3s:
      - kpi_id: "margin.gm.pct"
    component_30s:
      - visual_type: "trend_line"
        kpi_ids: ["sales.net_sales.amount"]
  page_2_execution:
    component_300s:
      evidence_grain: "transaction_line"
      action_panel: true
documentation:
  business_factsheet: "Business_Factsheet.md"
```

## Guardrails

- **Business factsheets are strictly human-readable**: No YAML config blocks. Machine config belongs in `UseCase_Bracket.yaml`.
- **Reference, don't define**: Link to KPI IDs and action code IDs; do not redefine their meaning.
- **Schema compliance**: Business factsheet → minimal frontmatter; Bracket → `usecase_bracket.schema.json`.

## Key paths

- Template: `core/usecases/templates/usecase_factsheet_business.md`, `UseCase_Bracket_TEMPLATE.yaml`
- Schemas: `tooling/generator/schemas/usecase_bracket.schema.json`, `tooling/ai/schemas/layout_330300.schema.json`
- KPI catalog: `core/kpi_catalog/`
- Org roles: `core/organization/org_roles.yaml` or `showcases/aurora_group/organization/org_roles.yaml` (Aurora context)
