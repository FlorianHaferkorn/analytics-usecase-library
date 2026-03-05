# Tool-agnostic vs. tool-specific separation

Purpose: Short reference for the separation of framework (core) and Fabric/Power BI realisation. Full plan: see repo plan "Tool-agnostic vs tool-specific Trennung".

## Principle

- **core/** = tool-agnostic definitions only: structure, IDs, lineage, logical formulas. No DAX, format strings, or PBI visual types.
- **products/fabric/powerbi/** = Fabric-specific realisation: DAX, TMDL, formatString, PBI visualType, PBIP.

## Target state (phases)

1. **Phase 0:** Principle and Key Paths documented (framework-conventions, single_source_of_truth). Done.
2. **Phase 1:** Fabric Measure Overlay holds dax_expression, formatString, dax_name; build_ir merges core + overlay into IR measure_spec. Core KPI catalog can drop technical DAX fields.
3. **Phase 2:** Core measure dictionaries keep measure_name, kpi_id_ref, documentation; drop expression.dax and expression.formatString.
4. **Phase 3:** Bracket ux_layout_rules use only abstract visual_type (trend_line, bar_chart, …); Fabric code maps to PBI visualType.
5. **Phase 4:** CI/validation use --fabric-overlay where needed; Stage 1 remains core-only.

## Fabric overlay path

- Specs (e.g. measure overlay): `products/fabric/powerbi/specs/fabric_measure_overlay.yaml`
- build_ir: `--fabric-overlay <path>` (optional); when set, measure_spec is built from core + overlay.
- **Full Fabric builds** use the overlay: `adapter_build.ps1` passes `--fabric-overlay` when the overlay file exists. Stage 1 does not depend on the overlay (core-only).
