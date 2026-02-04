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
  `implementations/microsoft_fabric_powerbi/guide/` (Fabric/Power BI implementation guides; PBIP layout and TMDL authoring)

## Internal usage note (1-liner)

- Policy: TMDL is the only source of truth for the semantic model in this repo (PBIP layout). Desktop is used for preview/canvas only.

---

Last updated: 04.11.2025

