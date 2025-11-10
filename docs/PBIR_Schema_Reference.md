# PBIR Schema Reference (Official Links & Structure)
Purpose: Single reference for **PBIP reports using PBIR** (enhanced report format). This file lists the canonical folder structure and points to the **public JSON schemas** you should rely on. It is safe to reference in docs/PRs and for MCP prompts.

> Source of truth: Microsoft Learn states PBIR is publicly documented and each JSON file declares its **$schema** URL, enabling validation and IntelliSense in editors.

## Applicability
- Applies to **Power BI Projects (PBIP)** saved with the **Power BI enhanced report format (PBIR)**.
- Replaces legacy `report.json` with a `definition/` folder containing multiple JSON files.
- The **definition.pbir** file sits alongside the `definition/` folder and references the semantic model via `datasetReference`.

## Report Folder (PBIP) — Key Files
These files live inside the **report folder** of a PBIP project:

- `definition.pbir` — overall report definition + semantic model reference (`datasetReference` via `byPath` or `byConnection`). Declares a public `$schema` URL.
- `mobileState.json` — report mobile layout (no external editing).
- `report.json` — *legacy* PBIR-legacy definition (no external editing) — only applicable when not using PBIR.
- `definition/` — **PBIR** folder replacing `report.json` (see contents below).

### PBIR `definition/` Folder Structure
```
definition/
â”œâ”€ bookmarks/
â”‚  â”œâ”€ [bookmarkName].bookmark.json
â”‚  â””â”€ bookmarks.json
â”œâ”€ pages/
â”‚  â”œâ”€ [pageName]/
â”‚  â”‚  â”œâ”€ visuals/
â”‚  â”‚  â”‚  â”œâ”€ [visualName]/
â”‚  â”‚  â”‚  â”‚  â”œâ”€ mobile.json
â”‚  â”‚  â”‚  â”‚  â””â”€ visual.json
â”‚  â”‚  â””â”€ page.json
â”‚  â””â”€ pages.json
â”œâ”€ version.json
â”œâ”€ reportExtensions.json
â””â”€ report.json
```

## Public JSON Schemas (how to reference)
Every PBIR JSON file starts with a `$schema` property that points to a **public schema URL**. Use these URLs as the authoritative reference.

### Examples
**`definition.pbir` (example from Microsoft Learn):**
```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
  "version": "4.0",
  "datasetReference": {
    "byPath": { "path": "../Sales.Dataset" }
  }
}
```
- `datasetReference.byPath.path` is a relative path to the semantic model folder (forward slash `/` separator).
- `datasetReference.byConnection` is used to connect to a semantic model in a Fabric workspace (required for REST deployments).

**Other PBIR files**
Each JSON under `definition/` declares its own `$schema`, for example:
- `definition/report.json` → `$schema` points to the **report-level** schema.
- `definition/pages/[pageName]/page.json` → `$schema` points to the **page** schema.
- `definition/pages/[pageName]/visuals/[visualName]/visual.json` → `$schema` points to the **visual** schema.
- `definition/bookmarks/[bookmarkName].bookmark.json` and `definition/bookmarks.json` → **bookmark** schemas.
- `definition/pages/pages.json` → **pages collection** schema.
- `definition/version.json` → **version** schema.
- `definition/reportExtensions.json` → **report extensions** schema.

> Tip: Open any file and copy the `$schema` URL at the top to inspect the exact properties for that file type. These URLs are maintained by Microsoft and provide up-to-date structure definitions.

## Notes & Policies (project-local)
- We **author reports in PBIR**. Always keep `$schema` headers intact.
- Use `byPath` for local co-development; use `byConnection` for REST/API deployments where required.
- When renaming page/visual folders or the `name` inside JSON, follow Microsoft’s naming rules to avoid broken references.
- Treat **schema validation errors** in editors/CI as **blocking** until fixed.

## Official Documentation (for maintainers)
- PBIP Report Folder & PBIR structure (Microsoft Learn)
- PBIR is publicly documented; each file has a public JSON schema
- `definition.pbir` versions and `datasetReference` rules (byPath vs byConnection)

(Keep this reference short; use the `$schema` URLs inside files for the authoritative, versioned property sets.)

