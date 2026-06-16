---
name: oss-stack-validation
description: Validate OSS stack artifacts (Evidence pages, adapter manifest, theme tokens, SQL style)
version: "1.0.0"
license: MIT
source: ALUCA (Analytics Library of Use Cases) — governance overlay
---

<!-- AUTO-GENERATED from docs/agent/skills/ — do not edit; run tooling/generator/generate_tool_configs.py -->

# OSS Stack Validation

Run all validation checks for the open-source Evidence.dev stack.

## When to use

- After generating or editing Evidence pages
- Before committing OSS stack changes
- As a pre-merge quality gate

## Workflow

1. **Run the OSS validation runner:**

   ```powershell
   python products/open_source_stack/tooling/validate_oss.py --root .
   ```

   ```bash
   python products/open_source_stack/tooling/validate_oss.py --root .
   ```

2. **Review results.** The runner executes these checks in order:
   - `validate_adapter_manifest` — adapter.json exists and has required keys
   - `validate_evidence_pages` — page structure, SQL blocks, Evidence components
   - `validate_theme_tokens` — only governed design tokens used
   - `validate_sql_style` — no SELECT *, explicit column names
   - `check_metrics_vs_kpi` — dbt metrics cover orchestrated bracket KPIs

3. **If checks fail:**
   - Read the error messages — each references a specific file and rule
   - Fix the issue in the source file
   - Re-run the validator

4. **For JSON output (CI):**

   ```powershell
   python products/open_source_stack/tooling/validate_oss.py --root . --json
   ```

   ```bash
   python products/open_source_stack/tooling/validate_oss.py --root . --json
   ```

## Key paths

| Artifact | Path |
|----------|------|
| Validation runner | `products/open_source_stack/tooling/validate_oss.py` |
| Page validator | `products/open_source_stack/tooling/page_generator/page_validator.py` |
| Adapter manifest | `products/open_source_stack/adapter.json` |
| Evidence pages | `products/open_source_stack/evidence_app/pages/` |
| Governed tokens | `fill-primary`, `text-brand-header`, `bg-surface` |

## Common errors

| Error | Fix |
|-------|-----|
| Missing page title | Add `# Title` as first heading in .md |
| No SQL query blocks | Add at least one ```` ```sql query_name ```` block |
| No Evidence components | Add `<BigValue>`, `<LineChart>`, etc. referencing a SQL block |
| SELECT * not allowed | Replace with explicit column names |
| Non-governed token | Use only `fill-primary`, `text-brand-header`, `bg-surface` |
