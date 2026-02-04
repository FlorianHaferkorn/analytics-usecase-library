# Internal (Non-Customer-Facing)

## Purpose

Hold **internal-only** tooling, scripts, drafts, and archived material related to the  
**ActionReady Analytics Framework**.  
This folder is not intended to be shared with customers. It supports development, QA, and framework evolution.

## Scope

Included:

- Helper scripts (e.g., generators, validators, linting)
- Internal documentation & notes
- Drafts and experimental content
- Archive of deprecated assets

Not included:

- Customer deliverables
- Final templates, catalogs, or models
- Any confidential customer data (must live in separate project repos)

## Recommended Structure

A possible structure (may be refined as tools mature):

```yaml
_internal/
  tools/
    generation/                → Generators for measures, scaffolding (maintainer-only)
    validation/                → Validators for factsheets, KPI catalogs, action codes, maps
    linters/                   → BPA + style/encoding checks (DAX/TMDL/report)
    maintenance/               → One-off fixes, migrations, refactors (maintainer-only)
    powerbi_mcp/               → Power BI MCP automation helpers (maintainer-only)

  drafts/
    *.md                       → Concept drafts, spike documents

  archive/
    *.md / *.yaml              → Legacy versions, no longer active

  README.md                    → This file
```

### tools/

Contains automation used to:

- generate measure files from KPI Catalog  
- scaffold new use cases and factsheets  
- validate alignment between:
  - Use Case Inventory  
  - KPI Catalog  
  - Semantic Models

## Boundary (important)

`_internal/` is **maintainer-only**. It may contain tooling and notes that should not be shipped to customers.

Tool-specific, customer-mirrorable implementation assets should live under:
- `implementations/` (e.g. `implementations/microsoft_fabric_powerbi/`)

This boundary matters for:
- product packaging,
- repeatable customer delivery,
- and safe AI-assisted automation (clear “allowed surface” vs maintainer internals).

### drafts/

Contains early-stage, non-final materials.  
If a draft becomes stable and reusable, move it into the appropriate non-internal folder.

### archive/

Contains deprecated or superseded files.  
These should only be kept if they provide historical or technical context.

## Usage

### For Framework Owners / Maintainers

- Use `_internal/tools` to automate repetitive work.  
- Keep validation scripts in sync with measure_system, KPI Catalog, and factsheet templates.  
- Clean up `drafts` and `archive` regularly.

### For Delivery Teams

- Only use internal tools if explicitly approved and documented.  
- Never expose `_internal` content to customers as-is.

## Relations

- **WHY →** Internal support for maintaining the framework’s quality and evolution.  
- **HOW →** Directly implements validation for the Operating Model and Measure System.  
- **WITH WHAT →** Generates and validates artifacts used in the Framework, Use Cases, and Semantic Models.  
- **TEMPLATES →** Keeps templates and catalogs consistent via automation and checks.
