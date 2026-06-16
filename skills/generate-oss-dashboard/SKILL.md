---
name: generate-oss-dashboard
description: Generate Evidence.dev dashboard pages from IR and UseCase Bracket
version: "1.0.0"
license: MIT
source: ALUCA (Analytics Library of Use Cases) — governance overlay
---

<!-- AUTO-GENERATED from docs/agent/skills/ — do not edit; run tooling/generator/generate_tool_configs.py -->

# Generate OSS Dashboard

Complete workflow for generating (or regenerating) Evidence.dev dashboard
pages for a use case. Mirrors the Fabric `generate-and-validate-pbi-report` skill.

## When to use

- When a new use case needs an OSS dashboard
- After UseCase_Bracket.yaml changes that affect UX layout
- When KPI catalog changes require page updates

## Workflow

1. **Refresh the IR** (ensures latest KPI catalog and brackets are included):

   ```powershell
   python tooling/ir/build_ir.py --kpi-catalog
   ```

   ```bash
   python tooling/ir/build_ir.py --kpi-catalog
   ```

2. **Run the Evidence Page Generator** for the target use case:

   ```powershell
   python -m products.open_source_stack.tooling.page_generator.generator `
      --use-case <USE_CASE_ID> `
      --ir-path tooling/ir/out/ir_v1.json
   ```

   ```bash
   python -m products.open_source_stack.tooling.page_generator.generator \
       --use-case <USE_CASE_ID> \
       --ir-path tooling/ir/out/ir_v1.json
   ```

   Example: `--use-case COM-001`

3. **Review generated pages** in `products/open_source_stack/evidence_app/pages/`:
   - Check that KPI cards match the bracket's `strategic_kpi_id` and `influencing_kpis`
   - Verify trend charts reference correct measures
   - For detail pages, check the 300-second layer includes diagnostic tables

4. **Run OSS validation:**

   ```powershell
   python products/open_source_stack/tooling/validate_oss.py --root .
   ```

   ```bash
   python products/open_source_stack/tooling/validate_oss.py --root .
   ```

5. **If validation passes** — commit the generated pages:

   ```bash
   git add products/open_source_stack/evidence_app/pages/
   git commit -m "feat(oss): generate Evidence pages for <USE_CASE_ID>"
   ```

6. **If validation fails** — read errors, fix in generated .md, re-run validator.

## Key paths

| Artifact | Path |
|----------|------|
| IR builder | `tooling/ir/build_ir.py` |
| Page generator | `products/open_source_stack/tooling/page_generator/generator.py` |
| Generated pages | `products/open_source_stack/evidence_app/pages/` |
| UseCase Bracket | `core/usecases/{core,extended,industry}/<ID>_*/UseCase_Bracket.yaml` |
| Evidence template | `core/templates/evidence_page_template.md` |
| Validation | `products/open_source_stack/tooling/validate_oss.py` |

## Post-generation checklist

- [ ] Page has frontmatter with `use_case` and `generated: true`
- [ ] 3-Second Layer has BigValue cards for each strategic KPI
- [ ] 30-Second Layer has trend charts for top KPIs
- [ ] 300-Second Layer (detail pages only) has DataTable
- [ ] All SQL blocks use explicit columns (no SELECT *)
- [ ] Only governed design tokens are used
- [ ] `validate_oss.py` passes with zero errors
