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
5. **Phase 4 (abgeschlossen 05.08.2026):** kein Overlay mehr — Formel, Anzeigename, Format und
   Ordner kommen aus dem KPI-Katalog. Stage 1 bleibt core-only.

## Wo die Fabric-Details herkommen

Der Katalog ist die Quelle, auch fuer Power-BI-Details — er traegt sie aber **semantisch**,
nicht als Power-BI-Syntax:

- **Formel** — `technical.calculation` (werkzeugneutrale Grammatik) → `dax_synth`. DAX ist
  ein Ziel davon, SQL ein zweites (`sql_synth`); ein weiteres Werkzeug heisst ein Target
  dazu, keine zweite Quelle.
- **Anzeigename** — `technical.measure_name`.
- **Format** — `business.unit_format` (geschlossenes Vokabular) über die Tabelle in
  `tooling/reporting/format_policy` (Profil `model`). `#,0.00` ist Power-BI-Syntax und
  steht deshalb im Target, nicht im Katalog.
- **Ordner** — `use_case_ref`.

`fabric_measure_overlay.yaml` ist am 05.08.2026 entfallen. Es war eine zweite Quelle fuer
Rechenvorschriften und hat einmal eine fachliche Korrektur still zurueckgedreht;
`tooling/superversion/tests/test_dax_parity_legacy.py` verhindert seine Rueckkehr.
