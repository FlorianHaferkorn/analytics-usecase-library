---
name: add-kpi-reference-safely
description: Add a KPI reference to a use case or action code only if the KPI exists in the catalog; otherwise add to catalog first. Use when adding kpi_id to factsheets, brackets, or action codes.
---

# Add KPI Reference Safely

Reference KPIs in use case brackets, action codes, or factsheet prose only after confirming the KPI exists in the KPI catalog. Never define KPI meaning in use cases or action codes.

## Workflow

1. **Check KPI catalog first**:
   - KPI definitions live in `core/kpi_catalog/` (SSOT).
   - Format: `domain.topic.metric` (e.g. `sales.price.realization_pct`, `plan.forecast.accuracy.pct`).
2. **If KPI exists**: Add the `kpi_id` reference in the appropriate artifact:
   - **Bracket:** `orchestration.strategic_kpi_id`, `orchestration.influencing_kpi_ids`, `value_driver_model.primary_driver`
   - **Action code:** `kpis.trigger_kpis`, `kpis.guardrail_kpis`, `kpis.outcome_kpis`
   - **Factsheet:** Prose only (no YAML blocks); reference by name or ID in text.
3. **If KPI does not exist**: Add the KPI to `core/kpi_catalog/` per catalog schema and templates first, then add the reference.
4. **Run validation**:
   ```powershell
   .\tooling\run_stage1_checks.ps1
   ```
   Relevant checks: `check_factsheet_vs_kpi.ps1`, `check_action_codes_vs_kpi.ps1`.

## Validation

After adding a KPI reference, verify:
- [ ] KPI ID exists in `core/kpi_catalog/`
- [ ] Reference uses exact `kpi_id` (no redefinition of meaning, target, or lineage)
- [ ] Stage 1 passes: `.\tooling\run_stage1_checks.ps1`

## Error Handling

**If check_factsheet_vs_kpi or check_action_codes_vs_kpi fails:**
→ KPI ID not in catalog: add to `core/kpi_catalog/` per schema, or fix typo in reference.

**If adding new KPI to catalog:**
→ Follow KPI catalog structure and templates in `core/kpi_catalog/` and `core/templates/kpi_catalog_templates/`.

## Guardrails

- **KPI catalog is SSOT**: Do not define KPI meaning, targets, or lineage in factsheets, brackets, or action codes.
- **Reference only**: Use existing `kpi_id` values; add new KPIs to the catalog first.

## Key paths

- KPI catalog: `core/kpi_catalog/`
- Brackets: `core/usecases/core/<UseCase>/UseCase_Bracket.yaml`
- Action codes: `core/action_codes/<Domain>/*.yaml`
- Validation: `tooling/validation/` (e.g. `check_factsheet_vs_kpi.ps1`, `check_action_codes_vs_kpi.ps1`)
