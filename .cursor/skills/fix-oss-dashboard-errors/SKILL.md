---
name: fix-oss-dashboard-errors
description: Diagnose and fix Evidence.dev dashboard / OSS validation errors
---

# Fix OSS Dashboard Errors

Workflow for diagnosing and fixing errors in Evidence pages or OSS
validation failures. Mirrors the Fabric `fix-pbi-report-errors` skill.

## When to use

- After `validate_oss.py` reports errors
- When Evidence pages fail to build (`npm run build` in evidence_app/)
- When SQL queries return unexpected results

## Workflow

1. **Run the validator and capture output:**

   ```bash
   python products/open_source_stack/tooling/validate_oss.py --root . --json > /tmp/oss_results.json
   ```

2. **Read the results** — each error has a check name, file, and message.

3. **Map error → root cause → fix:**

   | Error pattern | Root cause | Fix |
   |---------------|-----------|-----|
   | Missing page title | Markdown doesn't start with `# ` | Add `# <Use Case Name>` as first line |
   | No SQL query blocks | Page has no ```` ```sql name ```` blocks | Re-run generator or add SQL manually |
   | No Evidence components | Components missing or misspelled | Add `<BigValue>`, `<LineChart>` etc. |
   | SELECT * not allowed | Lazy SQL in a query block | Replace with explicit column list |
   | Non-governed token | Custom CSS class used | Replace with `fill-primary`, `text-brand-header`, or `bg-surface` |
   | SQL block not referenced | Orphaned query | Either add a component using `data={query_name}` or remove the block |
   | Missing 3-second layer | No KPI headline section | Add `## 3-Second Layer` with BigValue cards |

4. **Apply fixes** in the `.md` file.

5. **Re-run validation** to confirm:

   ```bash
   python products/open_source_stack/tooling/validate_oss.py --root .
   ```

6. **If the page was auto-generated** and the fix is structural, consider updating
   the generator source:
   - Component mapping: `page_generator/component_builder.py`
   - SQL generation: `page_generator/sql_builder.py`
   - Page assembly: `page_generator/markdown_writer.py`

## Key paths

| Artifact | Path |
|----------|------|
| Validation runner | `products/open_source_stack/tooling/validate_oss.py` |
| Page validator rules | `products/open_source_stack/tooling/page_generator/page_validator.py` |
| Component mapping | `products/open_source_stack/tooling/page_generator/component_builder.py` |
| SQL builder | `products/open_source_stack/tooling/page_generator/sql_builder.py` |
| Evidence pages | `products/open_source_stack/evidence_app/pages/` |

## Tips

- Errors are blocking (must fix); warnings are advisory (fix if feasible)
- The validator checks pages in alphabetical order — fix the first error first
- If the generator consistently produces bad output, fix the generator and re-run
  rather than hand-editing pages
