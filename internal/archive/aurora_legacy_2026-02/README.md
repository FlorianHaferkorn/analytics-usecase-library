# Aurora legacy artifacts (Feb 2026)

Archived when consolidating Aurora (fictive company only) and Fabric (tool-specific: architecture, reports, semantic models, orchestrator).

- **semantic_models/** — Former TMDL output under Aurora. Canonical output is now `products/fabric_powerbi/dist/<Domain>.SemanticModel`.
- **reports/** — Former PBIP report output under Aurora. Canonical output is now `products/fabric_powerbi/dist/<UC>.Report`.

Do not rely on these for builds. Use `products/fabric_powerbi/orchestrator/orchestrate_full_model.ps1` and `products/fabric_powerbi/dist/`.
