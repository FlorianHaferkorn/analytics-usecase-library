# TMDL Official References (Canonical)

Purpose: Single place to reference the authoritative Microsoft docs for Tabular Model Definition Language (TMDL). Use these links when implementing or reviewing anything related to the semantic model. Desktop is preview/canvas-only in our workflow; model authoring happens in TMDL.

## Canon (Microsoft)

- Overview / Spec - object types, syntax, indentation rules, compatibility  
  <https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview?view=sql-analysis-services-2025>
- Getting started - serialize/deserialize, authoring, deployment entry points  
  <https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-how-to?view=sql-analysis-services-2025>
- Power BI Desktop TMDL view - code-first editing inside Desktop  
  <https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-tmdl-view>
- PBIP semantic model folder - where TMDL lives inside a Power BI Project (PBIP)  
  <https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset>
- VS Code extension (official) - language service + diagnostics for TMDL  
  <https://marketplace.visualstudio.com/items?itemName=analysis-services.TMDL>
- GA announcement (reference) - TMDL view generally available  
  <https://powerbi.microsoft.com/de-de/blog/tmdl-view-generally-available/>

## Internal references (this repo)

- PBIP layout and TMDL usage - repo-specific structure and generators  
  `products/fabric/powerbi/docs/` (Fabric/Power BI implementation guides; PBIP layout and TMDL authoring)

## Internal usage note (1-liner)

- Policy: TMDL is the only source of truth for the semantic model in this repo (PBIP layout). Desktop is used for preview/canvas only.

---

## Sources & Grounding

This document is a **link index** to the authoritative Microsoft documentation for TMDL. The
"Canon (Microsoft)" links above were each verified to resolve to official `learn.microsoft.com`,
`marketplace.visualstudio.com`, or `powerbi.microsoft.com` pages. The primary specification and
the Tabular Object Model (TOM) it serializes are the grounding for everything in this repo's
TMDL usage:

- **Tabular Model Definition Language (TMDL) — overview & spec** (object types, syntax,
  indentation, compatibility level, TMDL API) — Microsoft Learn:
  <https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview>
- **Get started with TMDL — how-to** (serialize/deserialize via the AMO/TOM `TmdlSerializer`;
  authoring and deployment) — Microsoft Learn:
  <https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-how-to>
- **Tabular Object Model (TOM)** (the object hierarchy that TMDL is fully compatible with — every
  TMDL object exposes the same properties as TOM) — Microsoft Learn:
  <https://learn.microsoft.com/en-us/analysis-services/tom/introduction-to-the-tabular-object-model-tom-in-analysis-services-amo>
- **Work with TMDL view in Power BI Desktop** (code-first editing inside Desktop — the basis for
  the "Desktop is preview/canvas-only" policy) — Microsoft Learn:
  <https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-tmdl-view>
- **Power BI project (PBIP) semantic model folder** (where TMDL lives in a PBIP `definition/`
  folder) — Microsoft Learn:
  <https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset>
- **TMDL Visual Studio Code extension (official, `analysis-services.TMDL`)** (language service +
  diagnostics) — Visual Studio Marketplace:
  <https://marketplace.visualstudio.com/items?itemName=analysis-services.TMDL>
- **TMDL view — General Availability announcement** (reference) — Microsoft Power BI Blog:
  <https://powerbi.microsoft.com/en-us/blog/tmdl-view-generally-available/>

> All links verified to resolve as official Microsoft sources. Note: the GA-announcement link
> in the Canon list above uses the `de-de` locale; the equivalent `en-us` post is the same
> article. The `view=sql-analysis-services-2025` query parameter on the Canon links pins the
> docs to a specific Analysis Services version and is optional (the unversioned URLs above
> resolve to the current version).

---

Last updated: 15.06.2026

