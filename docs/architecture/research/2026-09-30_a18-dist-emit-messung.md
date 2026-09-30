---
last-reviewed: 2026-09-30
shelf-life-days: 60
status: gemessen
---
# A-18: dist-Reports gegen den offiziellen PBIR-Emit (Messung 30.09.2026)

**Ergebnis:** `products/fabric/powerbi/dist/*.Report` wurde **nicht** auf den offiziellen Emit
(`tooling/superversion/targets/pbir.py`) umgestellt. Der Emit meldet unter
`powerbi-report-author` 0.4.0 in allen 16 aus einem Bracket erzeugbaren Reports 0 Errors, trägt
aber nur rund die Hälfte der Visuals, bindet 94 von 133 Feldern an Objekte, die es in den
dist-Modellen nicht gibt, und lässt Theme, `.pbip`, Seitennamen und einen ganzen Report
(`COM-001_Sales_Performance_vs_Plan_LY`) fallen. Ein Umstieg wäre ein Rückschritt in allem außer
der Validator-Zahl. Die Lücken stehen unten einzeln; keine davon ist mit einem kleinen Eingriff
geschlossen. Owner-Vorgabe 30.09.2026: in diesem Fall nur Messbericht, `dist/` nicht halb umstellen.

## Methode

- Validator: `powerbi-report-author` **0.4.0** (`/tmp/claude-0/pbircli040/bin`),
  `validate <Report> --format json`, gezählt `data.errorCount` / `data.warningCount` und je
  Diagnosecode die `items`. Ohne `--no-schema` (wie die Ratsche
  `tooling/tests/test_dist_validator_ratchet.py`).
- Emit: je dist-Report das Bracket `core/usecases/core/<Ordnername>/UseCase_Bracket.yaml`
  → `from_aluca.from_bracket_file(bracket, core/kpi_catalog/kpis)` → `targets.pbir.emit()` in ein
  Arbeitsverzeichnis außerhalb des Repos; `targets.pbir.hitl_gaps()` für die Lückenliste.
- Umfang: Seiten = `definition/pages/*/page.json`, Visuals = `*/visuals/*/visual.json`,
  Projektionen = Einträge in `query.queryState.*.projections`, Bindungen = eindeutige
  `(Measure|Column, Entity, Property)` außer `_HITL`.
- Auflösbarkeit (Gegenprobe zum Validator, der Modellbindungen nicht prüft): jede Bindung gegen
  die `measure`/`column`-Zeilen der TMDL-Tabellen des Modells, auf das der **heutige** dist-Report
  per `definition.pbir` zeigt (`Commercial`, `Finance`, `Operations`, `SupplyChain`,
  `Experience`). Zeilenweiser Regex-Abgleich, kein TOM-Laden (ANNAHME, ungeprueft: Objekte mit
  ungewöhnlicher Quotierung könnten fehlen; vorher lösen damit 270 von 270 Bindungen auf).

## Validator je Report (vorher = dist heute, Emit = frisch aus dem Bracket)

| Report | Validator vorher (E/W) | Emit (E/W) | Visuals vorher → Emit | Projektionen | Bindungen vorher → Emit | davon im dist-Modell auflösbar (Emit) | HITL-Platzhalter |
|---|---|---|---|---|---|---|---|
| COM-001_Sales_Performance | 25/12 | 0/7 | 14 → 7 | 28 → 18 | 18 → 14 | 6/14 | 0 |
| COM-001_Sales_Performance_vs_Plan_LY | 25/9 | — (kein Bracket) | 8 → — | 26 → — | 19 → — | — | — |
| COM-002_Margin_Price_Performance | 25/12 | 0/7 | 15 → 7 | 25 → 15 | 16 → 8 | 3/8 | 3 |
| COM-003_Customer_Value | 25/12 | 0/7 | 15 → 7 | 27 → 16 | 17 → 9 | 2/9 | 4 |
| COM-004_Promotion_Effectiveness | 25/12 | 0/7 | 13 → 6 | 24 → 14 | 16 → 7 | 1/7 | 5 |
| FIN-001_Cash_Liquidity_Performance | 23/14 | 0/7 | 13 → 7 | 28 → 19 | 23 → 11 | 1/11 | 5 |
| FIN-002_Cost_Performance | 25/12 | 0/7 | 13 → 6 | 25 → 14 | 15 → 10 | 4/10 | 0 |
| OPS-001_Operations_Performance | 25/12 | 0/7 | 14 → 7 | 27 → 16 | 16 → 9 | 3/9 | 0 |
| OPS-002_Asset_Performance | 25/12 | 0/7 | 13 → 7 | 25 → 14 | 16 → 8 | 2/8 | 3 |
| OPS-003_Quality_Yield | 25/12 | 0/7 | 13 → 7 | 25 → 14 | 14 → 7 | 1/7 | 3 |
| SCM-001_Inventory_Performance | 25/12 | 0/7 | 14 → 7 | 29 → 19 | 16 → 8 | 2/8 | 6 |
| SCM-002_Supply_Reliability_OTIF | 25/12 | 0/7 | 13 → 6 | 25 → 16 | 15 → 8 | 2/8 | 4 |
| SCM-003_Forecast_vs_Actual | 25/12 | 0/7 | 13 → 6 | 24 → 14 | 13 → 6 | 2/6 | 4 |
| XD-001_Service_Level_Performance | 25/12 | 0/7 | 12 → 6 | 23 → 15 | 15 → 5 | 1/5 | 8 |
| XD-002_Resource_Utilization | 25/12 | 0/7 | 12 → 7 | 24 → 13 | 13 → 7 | 2/7 | 2 |
| XD-003_Executive_KPI_Overview | 25/12 | 0/7 | 12 → 6 | 23 → 14 | 13 → 7 | 2/7 | 4 |
| XD-004_Executive_Action_Governance | 25/12 | 0/7 | 12 → 6 | 20 → 12 | 15 → 9 | 5/9 | 0 |
| **Summe** | **423 E** | **0 E** (16 Reports) | **219 → 105** (ohne LY: 211 → 105) | | | **39/133** (vorher 270/270) | **58** |

Seiten: 2 je Report vorher und im Emit. Die 7 Emit-Warnungen sind alle `PBIR_SCHEMA_UNREACHABLE`
(Schema-URLs offline nicht abrufbar).

**Woraus die 423 Errors heute bestehen:** 391 in der mitgelieferten Theme-Datei
(`StaticResources/RegisteredResources/Aurora_Group__Monochromatic__Light___*.json`:
306 × `PBIR_THEME_VISUAL_PROP_UNKNOWN`, 85 × `PBIR_FORMATTING_OBJECT_UNKNOWN`), 32 in
`visual.json` (16 × `calloutValue` auf `cardVisual`, 15 × `text.text` auf `textbox`, 1 ×
`dataLabels` auf `clusteredBarChart`). Das deckt sich mit 0.1.1 (29.09.2026: 16 × 25, 1 × 23).
Der Emit ist sauber, weil er **kein** Custom-Theme und keine dieser Formatierungen schreibt —
nicht, weil er dieselben Inhalte korrekt schreibt.

## Lücken des Emits gegenüber dem dist-Bestand

| # | Lücke | Umfang (gemessen) | Warum nicht klein lösbar |
|---|---|---|---|
| L1 | Measure-Bindungen zeigen auf die Faktentabelle des kanonischen Modells (`fact_ops.OEE %`), die dist-Modelle führen alle Measures in `_Measures` | 94 von 133 Emit-Bindungen lösen im dist-Modell nicht auf | Abbildung kanonisches Modell → Domänenmodell fehlt im Emit; allein lösbar (Owner-Index aus dem Zielmodell), aber nicht ohne L2 |
| L2 | `datasetReference` zeigt auf ein Modell je Use Case (`../OPS-001_Operations_Performance.SemanticModel`), dist hat fünf Domänenmodelle | 16/16 Reports | Modellname kommt aus dem kanonischen Modell; dist-Modelle werden nicht aus dem kanonischen Modell erzeugt (A-25) |
| L3 | Visuals halbiert: Slicer-Leiste (Produkt, Region, Entität, Seitenpanel) fehlt bis auf den Datums-Slicer; `Header`, `Smart_Narrative`, `Last_Refresh` fehlen; das KPI-Band trägt weniger Measures (OPS-001: `KPI_Cards.Data` 4 → 1) | Slicer 77 → 22, `cardVisual` 68 → 19, `tableEx` 22 → 18, `textbox` 16 → 13 (vorher 17 Reports inkl. LY, Emit 16) | Emit bildet nur Bracket-Slots ab; die Slicer-Leiste (Datum, Region, Produkt, Entität) und Einzelkarten sind Prototyp-Layout ohne Bracket-Quelle |
| L4 | Gesteuerte Textmeasures entfallen | `Narrative Text (<UC>)`, `Active Actions Text (<UC>)`, `Last Refresh (<UC>)` je 16 Reports | Emit kennt nur KPI-Measures aus dem Katalog; die UC-Suffix-Measures (KNOWN_ERRORS Zeile „Use-Case-Suffix“) leben nur im Modell |
| L5 | HITL-Platzhalter statt Feldern | 58 Lücken in 12 von 16 Reports: 24 × unqualifiziertes Feld (`sku`, `product_category` …), 12 × `lineChart` ohne `Category`, 7 × `clusteredBarChart` ohne `Category`, 2 × `waterfallChart` ohne `Category`, 6 × Slicer ohne Feld, 3 × Textbox ohne Inhalt | Brauchen `table.column`-Deklarationen in 12 Brackets — fachliche Bracket-Arbeit, kein Emit-Fix |
| L6 | Dimensionsbindungen entfallen | u. a. `dim_org.Region` in 15, `dim_date.CalendarYearMonth` in 14, `dim_org.OrgName` in 12, `dim_product.Category` in 8 Reports | folgt aus L3/L5 |
| L7 | Kein Custom-Theme | 17/17 Reports verlören das Aurora-Theme (`report theme … not emitted (theme packaging deferred)` in `pbir.py`) | Theme-Packaging ist im Emit bewusst offen; mit Theme kämen die 391 Theme-Errors zurück (Übergabepunkt A der Ratsche) |
| L8 | `COM-001_Sales_Performance_vs_Plan_LY` hat kein Bracket | 1 Report (8 Visuals, 19 Bindungen) | Das COM-001-Bracket emittiert unter dem Titel-Slug `COM-001_Sales_Performance_vs_Plan_LY`; dist führt zwei Reports aus einer Quelle. Welcher gilt, ist eine Owner-Frage |
| L9 | Seitennamen ändern sich (`Page_OPS001_Overview` → `page_1_summary`) | 16/16 Reports | Tests und Drillthrough lesen die Prototyp-Namen; 15 Testdateien lesen `dist/*.Report` |
| L10 | Keine `<Name>.pbip` im Report-Ordner | 16/16 | `test_dist_report_coverage.py` Regel 5 verlangt sie; Emit schreibt dafür `.platform`, das dist heute fehlt |

## Was daraus folgt

- Die Validator-Zahl allein ist kein Abnahmekriterium für `dist/`: sie prüft Struktur, nicht ob
  Bindungen im Modell existieren (Gegenprobe oben: 39/133).
- Der sinnvolle Umstieg ist kein Austausch des Renderers, sondern: (1) Emit bekommt ein Zielmodell
  (L1/L2), (2) Brackets deklarieren ihre Felder qualifiziert (L5/L6), (3) Theme-Packaging mit
  gereinigtem Theme (L7), (4) Entscheidung zu L8, (5) Slicer-Leiste und Textmeasures als
  Bracket-Slots (L3/L4). Erst dann lohnt eine Neumessung mit derselben Methode.
- Bis dahin bleibt `generate_phase5_reports.ps1` auf dem Prototyp und die Ratsche auf 25.
