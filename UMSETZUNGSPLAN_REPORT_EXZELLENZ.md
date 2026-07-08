# Umsetzungsplan — Report-Exzellenz (Use Case → aussagekräftiger Report)

> **Loop-Anleitung:** Dieses Dokument ist die Single Source of Truth für die
> Report-Qualitäts-Initiative. Tasks werden im Ledger (§6) abgehakt; der Loop läuft
> wie beim Superversion-Plan: „nächster Task" / „merge + R-X.Y". Grundlage: die
> Deep-Research-Synthese vom 2026-07-03 (23 adversarial verifizierte Claims;
> Quellen-Referenzen `[n]` unten beziehen sich darauf) plus Maintainer-Review.

---

## 1. Zielbild (North Star)

**Aus jedem governten Use Case generiert ALUCA ohne Handarbeit einen Report, der
gleichzeitig einheitlich, aussagekräftig und maschinell abgenommen ist:**

| Dimension | Messgröße (prüfbar) |
|---|---|
| **Einheitlich** | 100 % Slot-Grid-Konformität — jede Seite folgt den festen Zonen (3-30-300, Kopf/KPI/Haupt/Evidenz); bestehende Layout-Checks bleiben Pflicht-Gate |
| **Aussagekräftig** | 5-Sekunden-Test bestanden: Big Idea + KPI-Zustand ohne Erklärung erfassbar (visuelle Abnahme); jedes `big_idea`-/`message`-Feld aus dem Bracket ist im gerenderten Report nachweisbar (Treue-Check) |
| **Messbar gut** | Scorecard-Gate im CI: ≥ 70 % Punkte und 0 Knock-outs je Report (IBCS-Muster [23]) — erst für den Piloten COM-002, dann 17/17 Reports |
| **Abgenommen** | Visueller Close-Loop etabliert: Desktop-Screenshot je Report, dokumentierte Abnahme (strukturelle Validierung allein reicht belegt nicht [8][9]) |

## 2. Leitplanken (Maintainer-Review eingearbeitet)

1. **Einheitlichkeit ist nicht verhandelbar.** Feste Seitenzonen und Slot-Grid
   bleiben normativ — Wiedererkennbarkeit über Reports hinweg ist ein Produktziel,
   kein Legacy. Analytische Qualität kommt **obendrauf**, ersetzt das Grid nicht.
2. **Template + Regeln, keine freie LLM-Generierung.** Mehrstufig-verifiziert schlägt
   One-Shot belegt [15]; unser deklarativer Bracket-Ansatz ist das richtige Muster
   (Inforiver-Prinzip: Standard einmal kodieren, nie pro Report [5]).
3. **Golden Thread bleibt Gesetz.** Alle neuen Felder/Regeln referenzieren governte
   KPIs/Action-Codes; nichts wird im Report neu definiert.
4. **Native Power-BI-Features zuerst.** Keine Custom-Visual-Zukäufe (Inforiver/Zebra)
   in diesem Plan; neue Card-Visuals, native Sparklines, Datenbalken, bedingte
   Formatierung decken den Bedarf.
5. **Kein Fake-Green.** Ein Task ist erst DoD-erfüllt, wenn die genannte Prüfung
   real gelaufen ist (Deserializer-Probe, CI-Gate, Screenshot-Abnahme).

**Nicht-Ziele:** kompletter Theme-Umbau; Causal-/Insight-ML; Custom-Visual-Framework;
Umbau der Studio-App (separater Plan).

## 3. Modell-Zuordnung (Komplexitäts-Prinzip)

- **Opus** — Design-/Architektur-Entscheidungen, Schema-Governance, analytische
  Kuration, Discovery/ADR, komplexe PBIR-Komposition (bedingte Formatierung,
  Small Multiples), Audit-/Rückbau-Urteile.
- **Sonnet** — mechanische Umsetzung nach klarem Muster, CI-Verdrahtung,
  Massen-Nachzüge über viele Dateien, Skript-/Doku-Tasks.

## 4. Cuts und Tasks

### C1 · Pilot COM-002 — Aussage sichtbar machen (dünner vertikaler Schnitt)
**Cut-Ziel:** Eine Seite beweist das Zielniveau Ende-zu-Ende; sichtbare Wirkung sofort,
bevor in Infrastruktur investiert wird.

| Task | Modell | Inhalt | DoD |
|---|---|---|---|
| **R1.1** Big Idea rendern | Sonnet | `bracket.big_idea` als Untertitel-Textbox in fester Kopfzone der Overview-Seite | Textbox vorhanden, Text == Bracket-`big_idea`, Position im Slot-Grid der Kopfzone; TOM-Deserializer + Bindings-Check grün |
| **R1.2** Narrative verdrahten | Sonnet | Leeres `smartNarrativeVisual` durch Visual mit governter `Narrative Text (COM)`-Measure ersetzen (chart-grounded [13]) | Visual trägt die Measure in `queryState`; kein unkonfiguriertes Narrative-Visual mehr auf der Seite; Bindings-Check grün |
| **R1.3** Evidence-Tabelle kuratieren | **Opus** | Detail_Matrix: ≤ 8 kuratierte Spalten (nach `decision_question`), Standard-Sortierung nach größter Plan-Abweichung, Top-N (20), Datenbalken auf GM-Varianz — Ampel-Zellfarbe nur falls Schema real verifizierbar, sonst dokumentierter Scope-Cut | PBIR enthält `sortDefinition` + Formatierungs-`objects`; Spaltenzahl ≤ 8; Deserializer + Bindings grün |
| **R1.4** Mixed-Scale auflösen | **Opus** | Main_3 (%, €, Stückkosten gemischt) auf Ranking-Slot-Zweck zurückgeführt: eine Einheit, ein Measure, entitäten-gerankt | Kein Chart der Seite mischt Einheiten; Bracket bleibt schema-valide; Deserializer + Bindings grün |
| **R1.5** KPI-Karten aufwerten | Sonnet | Neue Card-Visuals: Wert + Sparkline + Delta vs. Plan (Referenzbild-Muster), Slot-Positionen unverändert — Sparkline nur wenn Schema real verifizierbar, sonst Wert+Delta mit dokumentiertem Scope-Cut | 4 KPI-Cards zeigen Wert/Delta (Trend nur wenn verifiziert); Slot-Grid unverändert (Einheitlichkeits-Leitplanke); Deserializer grün |
| **R1.6** Visuelle Abnahme Pilot | User + Opus | Desktop-Öffnung + Screenshot; Review gegen 5-Sek.-Test und Referenzbild | Abnahme-Ergebnis im Ledger dokumentiert; offene Punkte als konkrete Folgetasks erfasst |

**Sequenz:** R1.1 ∥ R1.2 ∥ R1.5 → R1.3 → R1.4 → R1.6.

### C2 · Intent-Schicht härten — Regeln statt Prosa
**Cut-Ziel:** Die Aussage-Absicht ist maschinenlesbare Pflicht; der Generator *kann*
nicht mehr still dumpen (Draco-Prinzip: Constraints statt Guidelines [17]).

| Task | Modell | Inhalt | DoD |
|---|---|---|---|
| **R2.1** Bracket-Schema erweitern | **Opus** | `component_300s`: Pflichtfelder `sort_by`, `top_n`, `highlight_rule`; `component_30s`-Einträge: `message` (1 Satz) + `unit`-Deklaration | Schema erweitert + dokumentiert; Stage-1-Schema-Check erzwingt Felder (Übergangsregel für Bestand definiert); Drift-Gate grün |
| **R2.2** design_rules.yaml | **Opus** | Storytelling_Principles als formale Constraint-Datei: one-message-per-chart (max 1 Einheit/Achse), max Farbrollen, max Evidence-Spalten, Pflicht-Sortierung, Big-Idea-Kopfzone | Datei existiert; jede Regel hat `id`/`severity`/prüfbare Bedingung; von R2.3 konsumierbar |
| **R2.3** Generator erzwingt Regeln | **Opus** | `page_scaffold_generator` liest design_rules + erweitertes Bracket; verweigert Emit mit Regel-ID-Fehlermeldung bei Verstoß | Unit-Tests: Verstoß-Bracket → Fehler mit Regel-ID; konformes Bracket → Emit grün; COM-002-Regenerat == R1-Ergebnis (Golden-Fixture aktualisiert) |
| **R2.4** 17 Brackets nachziehen | Sonnet | `sort_by`/`top_n`/`message`/`unit` für alle Bestands-Use-Cases kuratiert befüllen (Muster: COM-002) | Alle Brackets schema-valide; Registry `--strict` grün; Generator-Lauf ohne Regel-Fehler |

**Sequenz:** R2.1 → R2.2 → R2.3 → R2.4. Start nach R1.6 (Pilot-Erkenntnisse fließen ins Schema).

### C3 · Quality-Gate scharf schalten — Scorecard statt binär
**Cut-Ziel:** „Aussagekräftig" ist im CI messbar; redundante Eigen-Checks sind
konsolidiert statt parallel gepflegt.

| Task | Modell | Inhalt | DoD |
|---|---|---|---|
| **R3.1** Tooling-Audit + Rückbau-Entscheidung | **Opus** | Überlappungs-Audit eigene Checks vs. `pbir --qa`/BPA [6][7] vs. PBI-Inspector **V2** [20–22]; Entscheidungs-Doc inkl. Theme-Namens-Konflikt (#7) **+ Tier1-Oracle-Aktivierung** (`MicrosoftReportAuthorBackend` in `tooling/report_quality/backends.py` ist gemäß ADR-0001 implementiert, aber in keinem aktiven CLI-Pfad verdrahtet — `PBI_QUALITY_ALLOW_EXTERNAL=1` ändert nichts an `report_quality.cli`/`pbi-quality`-Ergebnissen; s. Ledger-Notiz zu R1.6-Vorbereitung) | Doc in `docs/architecture/` (Index-registriert); je Check Verbleib/Rückbau begründet; Theme-Konflikt entschieden; Entscheidung dokumentiert ob/wie Tier1-Oracle in den aktiven Pfad verdrahtet wird + Triage der damit gefundenen repo-weiten Bestandsmuster (textbox `text.text`, cardVisual `calloutValue`, Slicer-Mindesthöhe) |
| **R3.2** Inspector V2 + BPA in CI | Sonnet | PBI-Inspector V2 (PBIR-fähig) + `pbir bpa --fail-on error` als CI-Gate; JSON-Report als Artifact; 2–3 eigene JSON-Logic-Regeln (Theme-Compliance, max Visuals/Seite, kein vertikales Scrollen) | CI-Job rot bei eingebautem Test-Verstoß, grün auf R1-Stand; Report-Artifact abrufbar |
| **R3.3** Scorecard-Gate | Sonnet | Gewichtete Punkte + Knock-outs (Mixed-Scale, unsortierte Evidence = sofort rot); Schwelle ≥ 70 % [23] | Score je Report im CI-Log; Schwellen-Logik unit-getestet; Zielbild-Messgröße technisch erfüllbar |
| **R3.4** Rückbau ausführen | Sonnet | Redundante Eigen-Checks gemäß R3.1 deprecaten/entfernen | Checks entfernt/markiert; Quality-Gate weiter grün; `KNOWN_ERRORS_AND_FIXES.md` aktualisiert |

**Sequenz:** R3.1 → (R3.2 ∥ R3.3) → R3.4. R3.1 kann parallel zu C2 starten.

### C4 · Visueller Close-Loop — Desktop-Bridge
**Cut-Ziel:** Rendering-Qualität wird systematisch geprüft statt zufällig entdeckt —
strukturelle Validierung fängt Overlap/Truncation/Unlesbarkeit belegt nicht [8].

| Task | Modell | Inhalt | DoD |
|---|---|---|---|
| **R4.1** Bridge-Workflow | Sonnet | Skript + Doku für `pbir desktop refresh`/`screenshot` auf Maintainer-Rechner (Windows, external-tools Preview); Screenshots je Report in definiertem Ordner | Dokumentierter Einzeiler; vom Maintainer einmal erfolgreich ausgeführt (COM-002-Screenshot liegt vor) |
| **R4.2** LLM-Judge-Abnahme | **Opus** | 5-Dimensionen-Scorecard (Informativeness, Clarity/Coherence, Visualization Quality, Narrative Quality, Factual Correctness [16]) als versionierter Judge-Prompt über Screenshots; halbautomatisch (Judge urteilt, Mensch entscheidet) | Judge-Prompt im Repo versioniert; ein dokumentierter Durchlauf auf COM-002 mit Ergebnis im Ledger |

**Sequenz:** R4.1 → R4.2. R4.1 kann sofort nach R1.6 starten.

### C5 · Rollout + Generator v2 (Discovery)
**Cut-Ziel:** Das bewiesene Muster skaliert generativ auf alle Reports; die
Architektur-Zukunft ist entschieden statt gewachsen.

| Task | Modell | Inhalt | DoD |
|---|---|---|---|
| **R5.1** Rollout 17 Reports | Sonnet | Regenerierung aller Reports über den Generator (nicht Handarbeit) nach C1–C3; Abweichungen je Report im Ledger | 17/17 bestehen Scorecard-Gate ≥ 70 % + 0 Knock-outs; min. 1 Screenshot-Abnahme je Domäne |
| **R5.2** Discovery/ADR Generator v2 | **Opus** | Zweistufige Architektur: Analyse/Insight-Scoring (depth/correctness/specificity/actionability [11]) getrennt von Komposition [10][14], Verifikations-Stufe dazwischen | ADR (Proposed) mit Festlegungen/Alternativen/offenen Punkten; im Architektur-Index registriert |

**Sequenz:** R5.1 nach C3; R5.2 parallel möglich (Discovery blockiert Rollout nicht).

**Gesamt-Sequenz:** C1 → (C2 ∥ R3.1) → C3 → C4 → C5.

## 5. Abnahme des Gesamtziels

Das Zielbild (§1) gilt als erreicht, wenn: 17/17 Reports das Scorecard-Gate bestehen
(≥ 70 %, 0 Knock-outs), die Slot-Grid-Checks grün sind, je Domäne eine dokumentierte
Screenshot-Abnahme mit bestandenem 5-Sekunden-Test vorliegt, und der Treue-Check
(Bracket-Intent → Report nachweisbar) für alle `big_idea`/`message`-Felder erfüllt ist.

## 6. Ledger — Single Source of Truth für Status (hier abhaken)

| Task | Status | Datum | Ergebnis/Notiz |
|---|---|---|---|
| R1.1 Big Idea rendern | ✅ | 2026-07-03 | Neue Zone 0 „Header" kanonisch in `Layout_Grid_System.md` + `Visual_Whitelist.md` ergänzt (nicht nur Pixel auf einer Seite geschoben — Governance-Autorität bleibt intakt); `Storytelling_Principles.md` §"Where the Big Idea Lives" korrigiert (Header zeigt die Aussage selbst, nicht nur die Frage). COM-002 Overview: neue `Header`-Textbox-Visual mit `bracket.ux_layout_rules.page_1_summary.big_idea` verdrahtet; KPI_Cards/Slicer_Date/Main_1-3 um 72px nach unten verschoben (Main-Charts entsprechend gekürzt, unterer Rand unverändert bei y=1048). **Schema-Korrektur (im selben Task gefunden+gefixt):** erster Entwurf nutzte ein untestetes Adapter-Snippet (`objects.general[].properties.paragraphs[]`); der reale, produktiv genutzte Generator (`page_scaffold_generator/page_builder.py`) zeigt das tatsächliche Schema — `objects.text[0].properties.text.expr.Literal.Value` als DAX-artiger Quoted-String-Literal. Korrigiert und mit 3 unabhängigen Repo-Quellen gegengeprüft (`page_builder.py`, `generate_action_payload.py`, `audit_pbir_issues.py`-Erwartung). **Prüfung:** `validate_bindings.py --strict` 0 Fehler, `report_quality.cli` 0 critical/warning/info, kein Overlap (16px Abstand Header→KPI), Drift-Gate + 949 Tests + H7=100% grün. **Offen für R1.6:** trotz Generator-Abgleich bleibt eine echte Desktop-Bestätigung ausstehend (kein Rendering-Preview hier möglich). |
| R1.2 Narrative verdrahten | ✅ | 2026-07-03 | `Smart_Narrative` auf der Detail-Seite war ein komplett unkonfiguriertes `smartNarrativeVisual` (0 Bindings) — durch `cardVisual` mit `queryState`-Bindung an die bereits vorhandene, governte Measure `_Measures.'Narrative Text (COM)'` ersetzt (chart-grounded, filterkontext-live). Muster spiegelt exakt `ActionPanel` auf derselben Seite (real deployt, identische Struktur), nicht das experimentelle `pbip.py`-Snippet. **Entdeckter Konflikt dokumentiert:** ein älteres, nicht CI-gebundenes Diagnose-Skript (`audit_pbir_issues.py`) erwartete noch `textbox`/`smartNarrativeVisual` für diesen Slot (Rückstand einer früheren Migration `upgrade_measures.py`, die Smart_Narrative bewusst AUF `smartNarrativeVisual` migriert hatte) — die neue, planbestätigte Konvention (Measure-Bindung via `queryState`) ist bewusst die Ablösung davon; in `Visual_Whitelist.md` begründet dokumentiert. **Prüfung:** `validate_bindings.py --strict` 0 Fehler, `report_quality.cli` 0 critical/warning/info, Drift-Gate + 949 Tests + H7=100% grün. |
| R1.3 Evidence-Tabelle kuratieren | ✅ | 2026-07-04 | Detail_Matrix (COM-002) 12→7 Spalten kuratiert (Category, ProductCode, GM Amount, **GM % vs Plan**, Price Realization %, Mix Effect Amount, GM %) — beantwortet die decision_question „Is our gross margin holding against price and mix pressure?" direkt: Locate→Outcome→Variance-Signal→die zwei benannten Pressure-Driver. Cut: Region/Channel (bereits über Page-Slicer `dim_org.OrgName`/`dim_date.CalendarYearMonth` filterbar), List/Net-Price-Absolutwerte (redundant zu Price Realization %), COGS per Unit (Kosttreiber, nicht Price/Mix). `evidence_columns` im Bracket synchron nachgezogen (Golden Thread), Cut-KPIs bleiben über `orchestration.influencing_kpi_ids` governt. **Schema-Rigor (Lehre aus R1.1 angewandt, dieses Mal vollständig verifiziert statt nur dokumentiert):** `sortDefinition`/`isDefaultSort`/`SortDirection`, `ThemeDataColor{ColorId,Percent}` und der komplette `TopN`-Filter (inkl. Subquery-`QueryDefinition` mit `Select`/`OrderBy`/`Top`) wurden gegen die echten, öffentlich publizierten Fabric-JSON-Schemas (`visualConfiguration/2.3.0`, `semanticQuery/1.4.0`, `filterConfiguration/1.3.0` — direkt von `raw.githubusercontent.com/microsoft/json-schemas` geladen und Property für Property abgeglichen) exakt bestätigt — keine Vermutung, sondern Beleg. Einzige nicht schema-verifizierbare Stelle bleibt `objects.columnFormatting[].properties.dataBars` (tableEx-spezifische Capability, wie schon bei R1.5s Card-Visual nicht öffentlich dokumentiert) — hier auf zitierte reale Repo-Präzedenzfälle gestützt, nicht auf Schema-Beweis. **Bewusster Scope-Cut:** diskrete 3-Stufen-Ampel-Zellfarbe (rot/gelb/grün aus Theme-Tokens) — jeder gefundene reale Präzedenzfall für `FillRule`-Farben akzeptiert nur hartkodierte Hex-Literale, `ThemeDataColor` ist dort nicht belegt; eine Hex-Variante würde `Color_Semantics_Formatting.md` verletzen. Empfehlung: governte DAX-Farb-Measure statt PBIR-Hex (Folgetask). Variance-Semantik bleibt durch Datenbalken (Theme-Farben) + Worst-First-Sort abgedeckt. **Prüfung (von mir unabhängig gegen die Opus-Agent-Behauptung nachgefahren):** `validate_bindings.py --strict` 0 Fehler, `report_quality.cli` 0 critical/warning/info, Drift-Gate 0 Befunde, 949 Tests grün, H7=100%, Scorecard PASS. |
| R1.4 Mixed-Scale auflösen | ✅ | 2026-07-04 | Main_3 (COM-002 Overview) mischte 4 Measures unterschiedlicher Einheit auf einer Achse (GM% + 3× €-Beträge). Root Cause zusätzlich zum Mixed-Scale-Bug identifiziert: der Slot ist laut `Layout_Grid_System.md`/`Slot_Definitions.md` §3 kanonisch ein **Ranking**-Slot („Compare entities by performance") — die alten 3-4 Driver-Measures (auch im Bracket bereits inkonsistent zur PBIR) gehörten nie dorthin. Fix: Main_3 → einzelnes Measure `Gross Margin %` (governte `margin.gm.pct`, die Seiten-Leit-KPI), `dim_org.OrgName` absteigend sortiert — echtes Ranking statt kaputtem Multi-KPI-Cluster. Keine Analyse-Lücke: die drei entfernten Driver (Price Realization %, Mix Effect, COGS/Unit) sind bereits auf Main_2 (PVM-Bridge, alle €) bzw. in der R1.3-kuratierten Detail_Matrix vorhanden. Bracket-Main_3-Eintrag von `kpi_ids`-Liste auf singuläres `kpi_id: margin.gm.pct` umgestellt (spiegelt Main_1s Stil) inkl. Begründungskommentar. **Schema-Rigor:** neu ergänztes `sortDefinition` erneut Property-für-Property gegen `visualConfiguration/2.3.0` + `semanticQuery/1.4.0` verifiziert (identisches, bereits in R1.3 bestätigtes Muster) — keine neue unverifizierte Fläche. Inertes `layout`-Objekt (Clustered-Gap zwischen Serien) entfernt, da bei einem Measure bedeutungslos. **Superversion-Golden-Snapshot** (frisch aus R1.3 gelernt) direkt mitgezogen: `tooling/superversion/tests/golden/COM-002.json` regeneriert, Diff chirurgisch nur auf Main_3s `bound_measures` begrenzt. **Prüfung (unabhängig von mir gegengeprüft, nicht nur Agent-Bericht vertraut):** JSON valide, `validate_bindings.py --strict` 0 Fehler, `report_quality.cli` 0 critical/warning/info, Drift-Gate 0 Befunde, repo-weiter `pytest -q` 1269 Tests grün (inkl. Superversion-Suite), Scorecard PASS/H7=100%. Alle vier Overview-Visuals (KPI_Cards, Main_1, Main_2, Main_3) gegengelesen und bestätigt einheiten-sauber. |
| R1.5 KPI-Karten aufwerten | ✅ | 2026-07-04 | KPI_Cards (COM-002 Overview) kuratiert von 4 unverbundenen Absolutwerten (GM%, GM-Betrag, Listenpreis, Nettopreis) zu Wert+Delta-Paar: `Gross Margin %` (Wert) direkt neben `Gross Margin % vs Plan` (Delta, bereits governte Measure, `displayFolder: COM-002`) + `Price Realization %` (Netto/Listen-Relativmetrik) + `Gross Margin Amount` (Stützgröße). **Sparkline bewusst nicht umgesetzt (Scope-Cut, dokumentiert statt geraten):** recherchiert über Microsoft-Learn-Doku + Report-Theme-Schema (`microsoft/powerbi-desktop-samples`) — die (new) Card-Visual-„Reference Labels" sind seit Nov-2025-GA offiziell bestätigt, aber das exakte `objects`-Property-Schema für PBIR-`visual.json` (Property-Namen wie `referenceLabel`/`detail`) ist nirgends real verifizierbar (kein Repo-Präzedenzfall, keine öffentliche Beispiel-JSON gefunden) — Wiederholung des R1.1-Fehlers (gerateter Schema-Import ohne Beleg) bewusst vermieden. Zusätzlich: Sparklines sind laut Microsoft-Doku nativ nur ein Tabellen/Matrix-Feature, nicht Teil der Card-Visual-Capabilities — eine In-Card-Sparkline wäre ohnehin unbelegt. Architektonisch unproblematisch, da Zone 1 (KPI-Band, 3-Sek.-Layer) laut `Layout_Grid_System.md` bewusst nur Werte zeigt; Trend lebt in Zone 3 (Main_1, dedizierter Trend-Slot) — keine Redundanz-Lücke. **Empfehlung für R4.1/R1.6:** Reference-Label-Schema nur mit echtem Desktop-Export verifizieren, dann nachziehen. **Prüfung:** `validate_bindings.py --strict` 0 Fehler, `report_quality.cli` 0 critical/warning/info, Drift-Gate + 949 Tests + H7=100% grün, Slot-Position/-Grid unverändert. |
| R1.6 Visuelle Abnahme Pilot | ⬜ offen | | **Vorbefund (2026-07-04), noch nicht final abgenommen:** Beim Versuch, für den User eine Desktop-Bridge-Automatisierung zu prüfen, entdeckt: (1) Die Power BI Desktop Bridge (Preview, `powerbi-desktop` CLI, named-pipe-basiert) existiert real, ist aber strikt lokal (kein Remote-Zugriff aus dieser Sandbox möglich) — R4.1 bleibt wie geplant ein Maintainer-Rechner-Skript. (2) Separat davon: `@microsoft/powerbi-report-authoring-cli` (offline, kein Desktop nötig) ist bereits im Repo dokumentiert (`docs/references/powerbi-report-author-cli.md`, ADR-0001) UND in dieser Sandbox bereits installiert — aber `tooling/report_quality/backends.py`s `MicrosoftReportAuthorBackend` (Tier-1-Oracle) ist nirgends in `report_quality.cli`/`pbi-quality` verdrahtet; alle „0 critical/warning/info"-Aussagen dieser Session galten nur für die native Tier-0-Prüfung. Direkter Lauf gegen COM-002 + Alt-Bestand (COM-001) ergab: **gefixt** (`7f89ab3`) Main_3 nutzte `dataLabels` statt des korrekten `clusteredBarChart`-Formatierungsobjekts `labels`. **Echter, vorbestehender (nicht diese Session verursachter) Befund:** Main_2 (waterfallChart) hat 3 Measures in der `Y`-Rolle, obwohl `maxPerRole.Y = 1` — ein Waterfall braucht 1 Measure + eine Category-Achse für die Bridge-Stufen; relativiert die R1.4-Begründung „Main_3-Driver bereits auf Main_2 abgedeckt" und sollte bei der Desktop-Abnahme geprüft werden. **Repo-weite, nicht dieser Session zuzuordnende Bestandsmuster** (alle Textboxen inkl. `ActionPanel`/`Smart_Narrative`, alle KPI-Cards via `calloutValue`, alle Dropdown-Slicer < 76px) — nicht unilateral gefixt, an R3.1 übergeben (Tabelle oben aktualisiert). Bonus: `catalog describe cardVisual` liefert das reale `referenceLabel`-Schema — die in R1.5 als unverifizierbar zurückgestellte Delta-Reference-Label-Umsetzung ist damit grundsätzlich nachrüstbar, sobald gewünscht. **Kritischer Fund #2, Root Cause des User-Crash-Dumps (`47407e3`):** Live-Fehlerbild beim Öffnen — `dim_promo` warf einen echten Fehler ("PromoKey enthält doppelten Wert '6'"), alle anderen Tabellen zeigten den generischen HRESULT-0x80040E4E-Fehler (konsistent mit einer wegen des Relationship-Integritätsfehlers abgebrochenen/zurückgerollten Gesamt-Refresh-Transaktion — eine einzige Ursache, kein Sammelsurium). Root Cause: Der Gold-Layer ist Delta-Lake-Output mit `_delta_log` je Tabelle; der frühere Session-Fix („Table.Combine über alle Parquet-Dateien" statt „nur die erste Datei") war für echte Multi-Partitions-Fakten richtig, aber falsch für per Overwrite mehrfach neu geschriebene Tabellen — alte, im Delta-Log bereits als „remove" markierte physische Dateien blieben liegen und wurden beim naiven Combine mitgezählt. Betroffen (physische vs. tatsächlich aktive Dateien): 5 Dimensionen (u.a. `dim_customer`, `dim_product`, `dim_promo`) und 9 Fakten inkl. **`fact_sales` selbst** (238 physisch vs. 60 aktiv — stille Vervierfachung aller Commercial-Kennzahlen, ohne sichtbaren Fehler, da keine Relationship das erzwingt). Fix: neue geteilte M-Funktion `fn_DeltaCurrentFiles` (je Domain-Semantic-Model in `expressions.tmdl`) spielt den Delta-Log (add/remove in Commit-Reihenfolge) ab und kombiniert nur den aktuell gültigen Dateisatz; Fallback auf Alt-Verhalten wenn kein `_delta_log` existiert. Repo-weit auf allen 70 Gold-Tabellen angewendet (nicht nur die 14 aktuell betroffenen), um dieselbe Fehlerklasse künftig nicht erneut schleichend einzuschleppen. **Verifikation:** Kern-Algorithmus (Pfad-Matching inkl. verschachtelter Hive-Partitionen) zuerst in Python 1:1 gegen die echten Repo-Daten nachgebaut und bestätigt (dim_promo 4→1 korrekt, fact_sales 238→60 korrekt, 0 unmatched), TMDL/M-Struktur über den echten TOM-Deserializer für alle 5 Domains grün, repo-weiter `pytest -q` (1269), Bindings/Drift-Gate/Scorecard grün. **Nicht verifizierbar von hier:** M-Laufzeitverhalten in echtem Power BI Desktop (keine Power-Query-Engine in dieser Sandbox) — Bestätigung steht beim nächsten Refresh des Users noch aus. Separat zu klären, falls der Fehler nach diesem Fix fortbesteht: `GoldDataPath`-Parameter ist auf einen hartkodierten Pfad (`C:/Users/florianhaferkorn/VSCode/analytics-usecase-library/...`) gesetzt — muss mit dem tatsächlichen lokalen Klon-Pfad des Users übereinstimmen, sonst schlägt jede Tabelle unabhängig fehl. |
| R2.1 Bracket-Schema erweitern | ⬜ offen | | |
| R2.2 design_rules.yaml | ⬜ offen | | |
| R2.3 Generator erzwingt Regeln | ⬜ offen | | |
| R2.4 17 Brackets nachziehen | ⬜ offen | | |
| R3.1 Tooling-Audit + Rückbau-Entscheidung | ✅ | 2026-07-08 | Doc: `docs/architecture/r3-1-tooling-audit-and-theme-decision.md` (Index-registriert). **ADR-0001-Status korrigiert:** war als „deferred, nicht übernommen" markiert, aber PR #321 hat die Backend-/Tier-Architektur einen Tag später tatsächlich doch gemerged (`tooling/report_quality/backends.py` real im Baum) — nur die Verdrahtung in `report_quality.cli` fehlte; jetzt nachgezogen (Tier-1-Oracle fließt jetzt via `PBI_QUALITY_ALLOW_EXTERNAL=1` in die Violations-Liste ein, Default-Verhalten unverändert verifiziert). **Theme-Konflikt #7 entschieden + gefixt:** offizielles Schema war korrekt (`customTheme.name` muss `.json` führen und exakt dem `resourcePackages`-Item entsprechen), eigene Prüfung hatte das Gegenteil verlangt — 3 Schreibstellen, 17 `report.json`, 33 registrierte Theme-Dateien, eigene Prüfung + Tests korrigiert. **Überlappungs-Audit:** eigener Floor und Oracle sind komplementär (Oracle deckt Theme-/Formatting-/Rollen-Schema ab, den der Floor strukturell nicht prüfen kann; Floor deckt Golden-Thread-Bindung ab, die der Oracle nicht kennt) — kein Rückbau nötig. **Neue repo-weite Funde trianiert statt hastig gepatcht:** Main_2-Waterfall-Rollenverstoß (alle 13 Reports mit PVM-Bridge, nicht nur COM-002), ~560 nicht-schema-konforme Theme-JSON-Properties, `calloutValue` statt `value` (jede KPI-Card), `text.text` bei Textboxen (ungeklärter Oracle-vs-Generator-Konflikt) — alle vier bewusst nicht einzeln gepatcht (Generator-Fix + Vollrollout nötig, kein Ad-hoc-Diff), an R2.4/R3.2/R3.4 übergeben. **Prüfung:** volle `pytest -q` (1269), `validate_bindings.py --strict` 0 Fehler, Drift-Gate 0 Befunde, native Theme-Prüfung 0 Fehler, Oracle 0 Theme-Diagnosen (vorher 34+17), Scorecard PASS. |
| R3.2 Inspector V2 + BPA in CI | ⬜ offen | | |
| R3.3 Scorecard-Gate | ⬜ offen | | |
| R3.4 Rückbau ausführen | ⬜ offen | | |
| R4.1 Bridge-Workflow | ⬜ offen | | |
| R4.2 LLM-Judge-Abnahme | ⬜ offen | | |
| R5.1 Rollout 17 Reports | ⬜ offen | | |
| R5.2 Discovery/ADR Generator v2 | ⬜ offen | | |

---

*Research-Referenzen `[n]`: verifizierte Claims der Deep-Research vom 2026-07-03
(Finton [1–3], IBCS/Inforiver [4][5][23], pbir CLI/BPA/Desktop-Bridge [6–9],
A2P-Vis [10–13], DataNarrative [14–16], Draco [17–19], PBI-Inspector [20–22]).*
