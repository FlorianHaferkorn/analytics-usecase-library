# Use Cases

This folder contains all business use case one-pagers.  
Each file describes a single analytical scenario in a consistent Markdown format, focusing on business logic, KPIs, and actions — without technical implementation details.

## Structure
| File | Purpose |
|------|----------|
| **UC-000_Template.md** | Base template (Fact Sheet) for new use cases; save as `FactSheet.md` inside each UC folder. |
| **COM-001_Sales_Performance.md** | Example of a fully documented use case. |
| **COM-002_Gross_Margin.md** | Example for a profitability analysis. |
| **UC-XXX_*.md** | Each additional use case follows the same naming and layout rules. |

## Naming Convention
- Folder name format: `{PREFIX}-###_Short_Title/` (e.g., `COM-005_Inventory_Health/`)
- Inside each folder, the main document is `FactSheet.md` (not `README.md`).
- `{PREFIX}` is a cluster code such as `COM`, `OPS`, `CST`, `COR`.
- Use hyphens (`-`) for separation, no spaces or special characters.
- IDs are sequential and unique; once assigned, never reused.

## Authoring Rules
1. Always copy the base template `UC-000_Template.md` to create a new file.  
2. Fill in all mandatory sections (Business Goal, Context, KPIs, Actions, Impact).  
3. Use relative links to refer to glossary, KPI catalog, or related use cases.  
4. Follow naming standards for all KPIs (`Δ`, `Δ%`, `%`, Amount, Qty, Count).  
5. Keep the text concise and business-focused.

## Review & Governance
- Each new or updated use case requires a Pull Request.  
- At least one **business** and one **technical** reviewer must approve.

_Last updated: 07.10.2025_
