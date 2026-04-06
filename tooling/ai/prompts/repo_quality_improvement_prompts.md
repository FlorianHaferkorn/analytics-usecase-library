# Prompts zur inhaltlichen Qualitaetsverbesserung

> Generiert auf Basis eines vollstaendigen Repo-Reviews (Stand: 2026-04-06).
> Jeder Prompt ist als eigenstaendiger Claude-Code-Auftrag formuliert und kann direkt ausgefuehrt werden.

---

## Uebersicht der identifizierten Qualitaetsbereiche

| # | Bereich | Schweregrad | Betroffene Dateien |
|---|---------|-------------|-------------------|
| 1 | KPI Catalog: Selbstreferenzierende Abhaengigkeiten | Kritisch | 40 KPIs in `core/kpi_catalog/KPI_Catalog.md` |
| 2 | KPI Catalog: Fehlende Lineage | Hoch | 33 KPIs mit `lineage: []` |
| 3 | KPI Catalog: Abgeschnittene Beschreibungen | Hoch | 5 KPIs mit truncated Descriptions |
| 4 | Business Factsheets: Sektion 4 leer (Action Codes Summary) | Mittel | Alle Core-Factsheets |
| 5 | Business Factsheets: 300s-Layer unvollstaendig | Mittel | Mehrere Factsheets (z.B. OPS-001) |
| 6 | Action Codes: Fehlende `impact_valuation` | Mittel | Alle 49 Action Codes |
| 7 | KPI Catalog: Inkonsistente Formelnotation | Niedrig | Gesamter Katalog |
| 8 | Use Case Inventory: Sync mit tatsaechlichen Dateien | Niedrig | `UseCase_Inventory.md` |
| 9 | Cross-Referenzen: Bidirektionale Konsistenz | Niedrig | Action Codes + Factsheets |

---

## Prompt 1 — KPI Selbstreferenzen bereinigen (KRITISCH)

```
Aufgabe: Bereinige alle selbstreferenzierenden `depends_on_measures` im KPI-Katalog.

Kontext: 40 KPIs in `core/kpi_catalog/KPI_Catalog.md` verweisen in ihrem
`depends_on_measures`-Feld auf ihre eigene `kpi_id`. Das ist ein logischer Fehler —
ein KPI kann nicht von sich selbst abhaengen.

Vorgehen:
1. Lies `core/kpi_catalog/KPI_Catalog.md` vollstaendig.
2. Identifiziere alle KPIs, deren `depends_on_measures`-Liste die eigene `kpi_id`
   enthaelt (z.B. `inv.dio.days` haengt ab von `inv.dio.days`).
3. Fuer jeden betroffenen KPI:
   a) Wenn der KPI eine Formel hat, die andere KPIs referenziert → ersetze die
      Selbstreferenz durch die tatsaechlichen Abhaengigkeiten aus der Formel.
   b) Wenn der KPI ein Basis-/Blattkennzahl ist (keine Formel aus anderen KPIs)
      → setze `depends_on_measures: []`.
   c) Nutze die `formula`-Felder und `calc_type` als Hinweis:
      - `calc_type: ratio` → besteht typischerweise aus Zaehler/Nenner-KPIs
      - `calc_type: rate` → besteht aus Basis-KPI und Bezugsgroesse
      - `calc_type: amount` oder `count` → oft Blatt-KPIs ohne Abhaengigkeiten
4. Aktualisiere `completeness_score` wo noetig.
5. Fuehre `.\tooling\run_stage1_checks.ps1` aus und behebe etwaige Fehler.

Bekannte betroffene KPIs (nicht abschliessend):
inv.dio.days, inv.stockout.pct, inv.obsolete.pct, plan.forecast.accuracy.pct,
plan.forecast.bias.pct, supply.otif.pct, supply.on_time.pct, ops.pm.task.count,
ops.production.volume, ops.quality.defect_rate.pct, ops.safety.incident.count,
ops.yield.pct, svc.fcr.pct, svc.aht.minutes, svc.nps.index, svc.escalation.pct,
res.occupancy.pct, res.overtime.pct, people.digital_adoption.pct,
enterprise.action_outcome_rate.pct, sales.units (ca. 40 Stueck insgesamt)

Wichtig: Aendere NUR `depends_on_measures` — keine anderen Felder modifizieren.
```

---

## Prompt 2 — KPI Lineage vervollstaendigen (HOCH)

```
Aufgabe: Vervollstaendige die leeren `lineage`-Eintraege im KPI-Katalog.

Kontext: 33 KPIs haben `lineage: []`. Lineage dokumentiert, aus welchen
Quell-Tabellen und -Spalten ein KPI berechnet wird. Ohne Lineage koennen
Data Contracts nicht validiert und Semantic Models nicht automatisch generiert werden.

Vorgehen:
1. Lies `core/kpi_catalog/KPI_Catalog.md` und identifiziere alle KPIs mit `lineage: []`.
2. Lies die zugehoerigen Data Contracts unter `core/data_contracts/domains/` fuer
   Kontext zu verfuegbaren Tabellen und Spalten.
3. Leite fuer jeden KPI die Lineage aus folgenden Quellen ab:
   a) `formula`-Feld des KPI (welche Fakten/Dimensionen werden benoetigt?)
   b) `data_requirements` der referenzierenden Use Cases
   c) Bestehende Lineage-Eintraege aehnlicher KPIs im gleichen Domain
4. Trage Lineage im Format ein, das im Katalog bereits verwendet wird:
   ```yaml
   lineage:
     - source_table: fact_xyz
       source_column: column_name
       transformation: SUM / AVG / COUNT / etc.
   ```
5. Aktualisiere `completeness_score` der betroffenen KPIs (0.8 → 1.0 wenn
   dadurch vollstaendig).
6. Fuehre `.\tooling\run_stage1_checks.ps1` aus.

Priorisiere KPIs, die in Core Use Cases (COM-001 bis XD-004) referenziert werden.
```

---

## Prompt 3 — Abgeschnittene KPI-Beschreibungen reparieren (HOCH)

```
Aufgabe: Repariere die 5 abgeschnittenen technischen Beschreibungen im KPI-Katalog.

Kontext: Folgende KPIs haben Description-Felder, die mitten im Satz enden
(erkennbar an `..."` oder abgeschnittenem Text):
1. crm.clv.amount
2. crm.retention.pct
3. crm.churned_customers.count
4. plan.forecast.service_impact.pct
5. people.digital_adoption.pct

Vorgehen:
1. Lies jeden betroffenen KPI-Eintrag in `core/kpi_catalog/KPI_Catalog.md`.
2. Rekonstruiere den vollstaendigen Text basierend auf:
   a) Dem `purpose`-Feld (Business-Beschreibung)
   b) Der `formula` (technische Definition)
   c) Vergleich mit aehnlichen KPIs im gleichen Domain
3. Vervollstaendige die `description` so, dass sie:
   - Den Berechnungsweg erklaert
   - Die Interpretation beschreibt (hoeher/niedriger = besser)
   - Die typische Granularitaet angibt
4. Halte den Stil konsistent mit vollstaendigen Beschreibungen anderer KPIs.
5. Fuehre `.\tooling\run_stage1_checks.ps1` aus.
```

---

## Prompt 4 — Sektion 4 (Action Codes Summary) in Business Factsheets befuellen (MITTEL)

```
Aufgabe: Befuelle die leere "Sektion 4 — Action Codes (Summary)" in allen
Business Factsheets mit praeegnanten Zusammenfassungen.

Kontext: Alle Core-Factsheets haben in Sektion 4 nur den Hinweis auf die YAML-Datei,
aber keinen Prose-Summary. Die Idee von Lean 2.0 ist, dass das Factsheet
Business-Kontext liefert — dazu gehoert eine verstaendliche Zusammenfassung
der Aktionen, auch wenn die technische Definition in YAML liegt.

Vorgehen:
1. Fuer jedes Factsheet unter `core/usecases/core/*/Business_Factsheet.md`:
   a) Lies die referenzierten Action Codes aus `UseCase_Bracket.yaml`
      (Feld `orchestration.action_code_ids`).
   b) Lies die YAML-Definitionen unter `core/action_codes/[Domain]/[id].yaml`.
   c) Schreibe einen Prose-Summary mit 2-4 Saetzen pro Action Code:
      - Was loest den Action Code aus (Trigger)?
      - Was passiert konkret (Schritte)?
      - Wer ist verantwortlich?
      - Welches Ergebnis wird erwartet?
2. Format:

   ## 4. Action Codes (Summary)

   | Code | Name | Trigger | Erwartete Wirkung |
   |------|------|---------|-------------------|
   | C-S1.1 | Price Discipline Enforcement | GM% < Target fuer 2+ Monate | +0.5-1.5pp GM% Recovery |

   > Machine-readable KPI + Action configuration → `UseCase_Bracket.yaml` (SSOT).

3. Behalte den bestehenden Hinweis auf YAML als SSOT bei.
4. Fuehre `.\tooling\run_stage1_checks.ps1` aus.
```

---

## Prompt 5 — 300-Sekunden-Layer in Factsheets vervollstaendigen (MITTEL)

```
Aufgabe: Vervollstaendige die 300-Sekunden-Layer (Diagnostics) in allen Business
Factsheets, die aktuell nur "(optional)" oder minimale Eintraege haben.

Kontext: Das 3-30-300-Konzept ist ein Kernprinzip des Repos. Die 300s-Schicht
beschreibt die tiefgehende Diagnose-Ebene fuer Execution. In einigen Factsheets
(z.B. OPS-001, Sektion 5.4) steht nur "(optional)" — das widerspricht dem
Anspruch des Frameworks.

Vorgehen:
1. Pruefe alle `Business_Factsheet.md` unter `core/usecases/core/`
   auf unvollstaendige 300s-Layer (Sektion 5.4).
2. Fuer jedes unvollstaendige Factsheet:
   a) Lies den `UseCase_Bracket.yaml` → `component_300s` fuer Struktur-Vorgaben.
   b) Lies die Action Codes fuer den Kontext der Execution-Entscheidungen.
   c) Beschreibe die Diagnostics-Ebene mit:
      - Welche Drill-Down-Dimensionen (aus `evidence_columns`)
      - Welche Detail-Tabelle/Matrix wird angezeigt
      - Wie verlinkt die Diagnose zu Action Codes
      - Welche Smart-Narrative-Texte helfen bei der Interpretation
3. Orientiere dich am Stil von COM-001 Sektion 5.4 als Best Practice:
   - 3 konkrete Bullet Points
   - Gap-Decomposition, Guardrail-Tabelle, Top-N-Analyse beschrieben
4. Fuehre `.\tooling\run_stage1_checks.ps1` aus.
```

---

## Prompt 6 — Action Codes um Impact Valuation ergaenzen (MITTEL)

```
Aufgabe: Ergaenze die `impact_valuation`-Sektion in allen Action Codes, die sie
noch nicht haben.

Kontext: Das Schema (`tooling/ai/schemas/action_code.schema.json`) definiert eine
optionale aber wichtige `impact_valuation`-Sektion mit: method, currency,
success_window, calculation_logic und attribution. Einige Action Codes haben diese
Sektion bereits (z.B. C-S1.1), viele fehlen. Die Impact Valuation ist entscheidend
fuer die ROI-Berechnung und Priorisierung von Aktionen.

Vorgehen:
1. Lies alle Action Code YAML-Dateien unter `core/action_codes/*/`.
2. Identifiziere alle, die keine `impact_valuation` haben.
3. Ergaenze fuer jeden eine plausible `impact_valuation`:
   a) `method`: Waehle aus [DirectMarginImprovement, CostAvoidance, RevenueUplift,
      CashRelease, RiskAvoidance] basierend auf dem `impact_dimension`.
   b) `currency`: EUR
   c) `success_window`: Leite aus `impact.expected_range.time_to_effect` ab.
   d) `calculation_logic.standardized`: Beschreibe die Wertberechnung in Prosa
      (min. 10 Zeichen).
   e) `attribution.method`: Waehle aus [before_after, diff_in_diff, holdout].
4. Orientiere dich an bestehenden vollstaendigen Action Codes als Vorlage.
5. Validiere gegen das Schema.
6. Fuehre `.\tooling\run_stage1_checks.ps1` aus.
```

---

## Prompt 7 — KPI Formelnotation standardisieren (NIEDRIG)

```
Aufgabe: Standardisiere die Formelnotation im gesamten KPI-Katalog.

Kontext: Die `formula`-Felder im KPI-Katalog verwenden inkonsistente Formate:
- Manche nutzen Prosa: "Sum of expected future gross margin per customer..."
- Manche nutzen Semi-Mathematik: "(Talk + Wrap) / (Talk + Wrap + Idle)"
- Keine nutzen das im Schema vorgesehene LaTeX-Format

Vorgehen:
1. Lies `core/kpi_catalog/KPI_Catalog.md` und alle `formula`-Felder.
2. Definiere ein einheitliches Format fuer alle Formeln:
   ```yaml
   formula: "NetSales_Amount - COGS_Amount) / NetSales_Amount"
   formula_latex: "\\frac{\\text{Net Sales} - \\text{COGS}}{\\text{Net Sales}}"
   ```
3. Fuer jeden KPI:
   a) Wenn die Formel in Prosa steht → extrahiere die mathematische Formel
      und schreibe sie in Semi-Mathematik-Notation.
   b) Ergaenze optional `formula_latex` fuer komplexere Formeln.
   c) Behalte die Prosa-Erklaerung als `formula_description` bei,
      wenn sie wertvolle Zusatzinformation enthaelt.
4. Stelle sicher, dass Variable-Namen in Formeln konsistent KPI-IDs oder
   deren `kpi_key`-Werte verwenden.
5. Fuehre `.\tooling\run_stage1_checks.ps1` aus.

Hinweis: Dieser Prompt hat niedrige Prioritaet. Die bestehenden Formeln sind
funktional korrekt, nur stilistisch inkonsistent.
```

---

## Prompt 8 — UseCase Inventory synchronisieren (NIEDRIG)

```
Aufgabe: Synchronisiere `core/usecases/UseCase_Inventory.md` mit dem tatsaechlichen
Dateibestand.

Kontext: Die Inventory-Datei ist die zentrale Uebersicht aller Use Cases.
Sie muss mit den tatsaechlich existierenden Verzeichnissen und Dateien
uebereinstimmen.

Vorgehen:
1. Lies `core/usecases/UseCase_Inventory.md`.
2. Scanne alle Verzeichnisse unter:
   - `core/usecases/core/`
3. Vergleiche:
   a) Sind alle existierenden Use Cases im Inventory gelistet?
   b) Sind alle Inventory-Eintraege als Verzeichnis vorhanden?
   c) Stimmen Status-Angaben (Draft/Active) mit dem Inhalt ueberein?
   d) Sind Domain-Zuordnungen korrekt?
4. Aktualisiere die Inventory-Datei bei Abweichungen.
5. Fuehre `.\tooling\run_stage1_checks.ps1` aus.
```

---

## Prompt 9 — Cross-Referenzen zwischen Use Cases validieren (NIEDRIG)

```
Aufgabe: Validiere und vervollstaendige die Cross-Referenzen zwischen Use Cases.

Kontext: Factsheets verweisen aufeinander (z.B. COM-001 "Out of Scope" verweist
auf COM-002, COM-004, COM-010). Action Codes haben `use_case_links` mit
`core_use_cases` und `related_use_cases`. Diese Verweise muessen bidirektional
konsistent sein.

Vorgehen:
1. Extrahiere alle Verweise zwischen Use Cases:
   a) Aus Business Factsheets: "Out of Scope"-Verweise, Cross-Links im Text
   b) Aus Action Codes: `use_case_links.core_use_cases` und
      `use_case_links.related_use_cases`
   c) Aus UseCase_Bracket.yaml: referenzierte Action Codes
2. Erstelle eine Abhaengigkeitsmatrix.
3. Pruefe:
   a) Existieren alle referenzierten Use Cases tatsaechlich?
   b) Sind Rueckverweise vorhanden (wenn COM-001 auf COM-002 verweist,
      verweist COM-002 auch auf COM-001)?
   c) Sind Action Code Zuordnungen konsistent (Action Code verweist auf UC
      und UC verweist auf Action Code)?
4. Erstelle einen Bericht mit allen gefundenen Inkonsistenzen.
5. Korrigiere die Inkonsistenzen in den betroffenen Dateien.
6. Fuehre `.\tooling\run_stage1_checks.ps1` aus.
```

---

## Empfohlene Reihenfolge der Ausfuehrung

| Prioritaet | Prompts | Begruendung |
|------------|---------|-------------|
| 1 (sofort) | Prompt 1, 3 | Datenfehler im KPI-Katalog — wirken sich auf alle Downstream-Artefakte aus |
| 2 (bald) | Prompt 2, 4, 5 | Vollstaendigkeit der zentralen Artefakte |
| 3 (naechste Iteration) | Prompt 6 | Action-Code-Reife (Impact Valuation) |
| 4 (bei Gelegenheit) | Prompt 7, 8, 9 | Konsistenz und Polish |
