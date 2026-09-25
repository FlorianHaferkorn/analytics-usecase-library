# Power BI / Fabric Reference Docs

Quick index — open the relevant doc for the task at hand.

## Fabric API

| Doc | Use When |
|---|---|
| [`fabric-api-core.md`](fabric-api-core.md) | Auth token audiences, REST API patterns (LRO, pagination, workspace/item CRUD), OneLake, common 401/403/404 errors |
| [`fabric-item-definitions.md`](fabric-item-definitions.md) | Building Base64 definition envelopes for SemanticModel, Report, Notebook, DataPipeline, Lakehouse, Eventhouse, KQLDatabase |
| [`fabric-powerbi-authoring.md`](fabric-powerbi-authoring.md) | Creating/updating semantic models via API; two token audiences (Fabric Items vs Power BI Datasets); TMDL mandatory parts; permission troubleshooting |

## PBIR Report Development

| Doc | Use When |
|---|---|
| [`pbir-visual-json.md`](pbir-visual-json.md) | Editing `visual.json` directly — position, visualType, query projections, expression types, `objects` vs `visualContainerObjects`, analytics lines |
| [`pbir-conditional-formatting.md`](pbir-conditional-formatting.md) | Adding conditional formatting — measure-based, gradient (linearGradient2/3), or rules-based (staticList); `dataViewWildcard matchingOption` |
| [`pbir-theme.md`](pbir-theme.md) | Modifying `theme.json` — dataColors, semantic colors, wildcard `visualStyles` inheritance, textClasses |
| [`pbir-extension-measures.md`](pbir-extension-measures.md) | Report-layer DAX in `reportExtensions.json` — when to use, `"Schema":"extension"` in SourceRef, delete-if-empty rule, promotion path |

## Semantic Model

| Doc | Use When |
|---|---|
| [`tmdl-tom-object-types.md`](tmdl-tom-object-types.md) | Programmatic model edits via PowerShell TOM — tables, columns, measures, relationships, hierarchies, RLS roles; refresh requirements per object type |
| [`powerbi-modeling-mcp-setup.md`](powerbi-modeling-mcp-setup.md) | Installing and registering the Power BI Modeling MCP server, connecting it to PBIP `definition` folders or Desktop, and the post-implementation validate → fix → learn loop |

## Validation & Visual QA

| Doc | Use When |
|---|---|
| [`powerbi-report-author-cli.md`](powerbi-report-author-cli.md) | Tier 1 oracle (`powerbi-report-author validate`) — offline, no Desktop needed |
| [`desktop-bridge-screenshot-workflow.md`](desktop-bridge-screenshot-workflow.md) | R4.1: maintainer-run Desktop Bridge screenshot capture for the visual close-loop (Windows + Desktop required, not runnable in CI/sandbox) |
