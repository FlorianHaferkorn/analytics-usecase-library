# Page Spec 3-30-300

Reference document for **where which visual is placed and why** on the two standard report pages (Overview = 3–30 seconds, Detail = 300 seconds). See [Slot_Definitions.md](governance/Slot_Definitions.md) for slot semantics and [ActionPanel_Spec.md](components/ActionPanel_Spec.md) for the Action Panel.

---

## Purpose by layer

- **3 seconds:** One glance – headline KPIs and status vs. target.
- **30 seconds:** Explanation – why we are off target; drivers, variance, trend.
- **300 seconds:** Validation and action – detail data and prescribed next steps (T4).

---

## Seite 3–30 (Overview – "The Pulse")

| Slot-ID      | Visual-Typ     | Zweck |
|-------------|----------------|--------|
| **KPI_Cards** | New KPI Card (cardVisual, multiple measures) | Alle als KPI angezeigten Kennzahlen (strategic + influencing) in einem Visual. Ein Blick: Status und Abweichung. |
| **Slicer_Date** | Slicer | Zeitfilter; gilt für alle nachgelagerten Visuals. |
| **Main_1**  | z. B. Line Chart | 30s: Trend – wie entwickelt sich die Kennzahl über die Zeit? |
| **Main_2**  | z. B. Waterfall / Bar | 30s: Variance oder Ranking – wo weichen wir ab bzw. wer treibt was? |
| **Main_3**  | z. B. Bar / Stacked Bar | 30s: Treiber oder Verteilung (Mix/Ranking). |

Keine Actions auf der Overview-Seite; nur Signal und Erklärung.

---

## Seite 300 (Detail – "The Action Matrix")

| Slot-ID         | Visual-Typ   | Zweck |
|-----------------|--------------|--------|
| **Slicer_Pane** | Slicer       | Schneller Kontextwechsel (Zeit, Region, Segment); filtert Detail und Action Panel. |
| **Smart_Narrative** | Textbox / Smart Narrative | Ein Satz Zusammenfassung zum aktuellen Filterzustand („Was gilt hier?“). |
| **Detail_Matrix**   | Tabelle/Matrix (tableEx) | Operative Liste – Einheiten, Kennzahlen, Deltas; Basis für „wo eingreifen?“; optional Data Bars für Delta-Spalten. |
| **ActionPanel** | Text/Card (aus Action Codes) | Nur bei T4: Empfehlung, Owner, Trigger, Schritte, Impact. Daten aus Action-Code-YAML. |

Die 300s-Seite dient der Validierung und der Handlung: Smart_Narrative (Kontext), Detail_Matrix (Daten), ActionPanel (was tun, von wem, mit welchem Impact).

**Drillthrough:** Die Detail-Seite ist im PBIP als **Drillthrough-Ziel** konfiguriert (`type: "Drillthrough"`, `visibility: "AlwaysVisible"`, `pageBinding`). Sie erscheint damit sowohl als eigene Seite in der Seitenliste als auch als Ziel für „Rechtsklick → Drill through“ von Visuals der Overview-Seite; der Filterkontext wird dabei übergeben.

---

## Alternative Overview: "The Investigator"

| Slot-ID       | Visual-Typ | Zweck |
|---------------|------------|--------|
| **Slicer_Pane** | Slicer   | Vertikale Slicer-Leiste für schnellen Kontextwechsel. |
| **Focus_Area**  | Ein dominantes Analyse-Visual | 30s: Fokus auf „Warum?“ – z. B. Treiber-Hierarchie, Decomposition. |
| **Support_1**   | Kleines Kontext-Visual | Zeitlicher oder regionaler Kontext zur Focus_Area. |
| **Support_2**   | Wie Support_1 | Zweiter Kontext (andere Dimension oder Metrik). |

Wenn KPIs auch im Investigator-Layout gezeigt werden sollen, kann ein Slot **KPI_Cards** ergänzt werden (gleiche Semantik wie bei Pulse).
