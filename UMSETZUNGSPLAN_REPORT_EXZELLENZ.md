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
| **R1.3** Evidence-Tabelle kuratieren | **Opus** | Detail_Matrix: ≤ 8 kuratierte Spalten (nach `decision_question`), Standard-Sortierung nach größter Plan-Abweichung, Top-N (20), Datenbalken auf GM-Varianz, semantische Ampel-Formatierung aus Theme-Farben | PBIR enthält `sortOrder` + Formatierungs-`objects`; Spaltenzahl ≤ 8; User-Screenshot bestätigt: „Wo ist das Problem?" in 5 Sek. beantwortbar |
| **R1.4** Mixed-Scale auflösen | **Opus** | Main_3 (%, €, Stückkosten gemischt) in „eine Einheit pro Achse" überführen: getrennte Charts oder Small-Multiples-Muster; Bracket COM-002 entsprechend anpassen | Kein Chart der Seite mischt Einheiten; Bracket bleibt schema-valide; Deserializer + Bindings grün |
| **R1.5** KPI-Karten aufwerten | Sonnet | Neue Card-Visuals: Wert + Sparkline + Delta vs. Plan (Referenzbild-Muster), Slot-Positionen unverändert | 4 KPI-Cards zeigen Wert/Trend/Delta; Slot-Grid unverändert (Einheitlichkeits-Leitplanke); Deserializer grün |
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
| **R3.1** Tooling-Audit + Rückbau-Entscheidung | **Opus** | Überlappungs-Audit eigene Checks vs. `pbir --qa`/BPA [6][7] vs. PBI-Inspector **V2** [20–22]; Entscheidungs-Doc inkl. Theme-Namens-Konflikt (#7) | Doc in `docs/architecture/` (Index-registriert); je Check Verbleib/Rückbau begründet; Theme-Konflikt entschieden |
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
| R1.1 Big Idea rendern | ✅ | 2026-07-03 | Neue Zone 0 „Header" kanonisch in `Layout_Grid_System.md` + `Visual_Whitelist.md` ergänzt (nicht nur Pixel auf einer Seite geschoben — Governance-Autorität bleibt intakt); `Storytelling_Principles.md` §"Where the Big Idea Lives" korrigiert (Header zeigt die Aussage selbst, nicht nur die Frage). COM-002 Overview: neue `Header`-Textbox-Visual mit `bracket.ux_layout_rules.page_1_summary.big_idea` verdrahtet; KPI_Cards/Slicer_Date/Main_1-3 um 72px nach unten verschoben (Main-Charts entsprechend gekürzt, unterer Rand unverändert bei y=1048). **Restrisiko:** `textbox`-Visual-Typ war nirgends im Repo real deployt (nur experimenteller Adapter-Code) — Schema gegen vendortes PBIR-JSON-Schema geprüft (kein Typ-Constraint dort, da visualType-spezifische Objects nicht schema-typisiert sind), Best-Evidence-Struktur verwendet. **Prüfung:** `validate_bindings.py --strict` 0 Fehler, `report_quality.cli` 0 critical/warning/info, kein Overlap (16px Abstand Header→KPI), Drift-Gate + 949 Tests + H7=100% grün. **Offen für R1.6:** visuelle Bestätigung, dass die Textbox in Desktop korrekt rendert (Restrisiko oben). |
| R1.2 Narrative verdrahten | ⬜ offen | | |
| R1.3 Evidence-Tabelle kuratieren | ⬜ offen | | |
| R1.4 Mixed-Scale auflösen | ⬜ offen | | |
| R1.5 KPI-Karten aufwerten | ⬜ offen | | |
| R1.6 Visuelle Abnahme Pilot | ⬜ offen | | |
| R2.1 Bracket-Schema erweitern | ⬜ offen | | |
| R2.2 design_rules.yaml | ⬜ offen | | |
| R2.3 Generator erzwingt Regeln | ⬜ offen | | |
| R2.4 17 Brackets nachziehen | ⬜ offen | | |
| R3.1 Tooling-Audit + Rückbau-Entscheidung | ⬜ offen | | |
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
