# Page Spec 3-30-300

Reference document for **where which visual is placed and why** on the two standard report pages (Overview = 3–30 seconds, Detail = 300 seconds). See [Slot_Definitions.md](governance/Slot_Definitions.md) for slot semantics and [ActionPanel_Spec.md](components/ActionPanel_Spec.md) for the Action Panel.

---

# Tool-agnostisches 3-30-300 Page Template (Whitelist-basiert)

## 1. Use Case Summary
Use Case Name: <Platzhalter>
Business Objective: <Platzhalter>
Target User: <Platzhalter>
Primary Decision: <Platzhalter>

## 2. Core Business Questions
- Frage 1: <Platzhalter>
- Frage 2: <Platzhalter>
- Frage 3: <Platzhalter>

## 3. Standard 3-30-300 Page Structure

> **Research basis:** The 3-30-300 reading layer model operationalises the Visual Information-Seeking Mantra of Shneiderman (1996, "The Eyes Have It: A Task by Data Type Taxonomy for Information Visualizations"): *overview first, zoom and filter, then details on demand.* The SQLBI 3-30-300 rule adapts this principle for BI time-budgets. The layer sequence also reflects Sweller (1988, Cognitive Load Theory): presenting overview before detail minimises extraneous cognitive load.

### 3-Second Layer
- Zweck: Status/Signal (Was ist passiert?)
- KPI/Status: Headline-KPIs
- Empfohlenes Visual: kpi_card (Whitelist)
- Warum dieses Visual: Sofortiger Überblick über Zielerreichung und Abweichung

### 30-Second Layer
- Zweck: Treiber, Vergleich, Segmentierung (Warum ist es passiert?)
- Treiber / Vergleich / Segmentierung: Trend, Ranking, Abweichung
- Empfohlenes Visual: trend_line, bar_chart, waterfall (Whitelist)
- Warum dieses Visual: Zeigt Entwicklung, Treiber und Segmentunterschiede klar auf

### 300-Second Layer
- Zweck: Diagnose, Ursachen, Drilldown (Was bedeutet es? Was tun?)
- Diagnose / Ursachen / Drilldown: Detaildaten, operative Liste, Maßnahmen
- Empfohlenes Visual: matrix, smart_narrative, ranking (Whitelist)
- Warum dieses Visual: Ermöglicht gezielte Analyse und Ableitung von Maßnahmen

## 4. Slicers and Defaults
- Pflichtslicer: slicer (Whitelist) – z.B. Zeitraum, Region, Produkt
- Default Filter: <Platzhalter>
- Kontext, der immer sichtbar sein muss: Aktueller Filterkontext, ggf. Smart Narrative

## 5. Storytelling Logic
- Signal: kpi_card
- Treiber: trend_line, bar_chart, waterfall
- Ursache: matrix, ranking
- Konsequenz: smart_narrative, ggf. ActionPanel
- Entscheidung: Ableitung aus den Visuals, ggf. ActionPanel

## 6. Exceptions to Standard Layout
Nur falls notwendig: <Platzhalter für Begründung und Alternative>

## 7. Design Rules
- Weniger ist mehr.
- Jede Visualisierung muss einen klaren Zweck haben.
- Keine redundanten Charts.
- Jede Ebene muss auf die nächste vorbereiten.
- Die Story muss den User zur Entscheidung führen, nicht nur zur Beobachtung.

---

**Hinweis:**
- Es dürfen ausschließlich Visualtypen aus der [Visual Whitelist](visual_whitelist.md) verwendet werden.
- Die konkrete Visualauswahl pro Use Case erfolgt nach Story-Funktion, nicht nach Standard.
- Für die Umsetzung in Power BI oder Evidence werden die Visualtypen per Übersetzer gemappt.

## Purpose by layer

- **3 seconds:** One glance — headline KPIs and status vs. target.
- **30 seconds:** Explanation — why we are off target; drivers, variance, trend.
- **300 seconds:** Validation and action — detail data and prescribed next steps (T4).

---

## Page 3-30 (Overview — "The Pulse")

| Slot ID      | Visual Type    | Purpose |
|-------------|----------------|---------|
| **KPI_Cards** | KPI Card (multiple measures) | All KPIs designated for the 3-second layer in one band. One glance: status and deviation. |
| **Slicer_Date** | Slicer | Time filter; applies to all downstream visuals. |
| **Main_1**  | e.g. Line Chart | 30s: Trend — how does the metric develop over time? |
| **Main_2**  | e.g. Waterfall / Bar | 30s: Variance or Ranking — where do we deviate, or who drives what? |
| **Main_3**  | e.g. Bar / Stacked Bar | 30s: Drivers or distribution (Mix / Ranking). |

No actions on the Overview page — signal and explanation only.

---

## Page 300 (Detail — "The Action Matrix")

| Slot ID         | Visual Type  | Purpose |
|-----------------|--------------|---------|
| **Slicer_Pane** | Slicer       | Fast context switch (time, region, segment); filters Detail and Action Panel. |
| **Smart_Narrative** | Text / Narrative | One-sentence summary for the current filter context ("What is true here?"). |
| **Detail_Matrix**   | Table / Matrix | Operative list — entities, metrics, deltas; basis for "where to intervene?"; optional data bars on delta columns. An **ActionCode** / **Recommended Action** column may be added when the semantic model provides a row-level recommendation per entity (Phase 2). |
| **ActionPanel** | Text / Card (from Action Codes) | T4 only: recommendation, owner, trigger, steps, impact. Phase 1: data from Action Code YAML (build time); Phase 2: optional from semantic model table. |

The 300s page serves validation and action: Smart_Narrative (context), Detail_Matrix (data), ActionPanel (what to do, by whom, with what impact).

**Drillthrough:** The Detail page is configured as a **drillthrough target** (`type: "Drillthrough"`, `visibility: "AlwaysVisible"`, `pageBinding`). It appears both as a standalone page in the page list and as the target for right-click → Drill through from Overview visuals; filter context is passed automatically.

---

## Alternative Overview: "The Investigator"

| Slot ID       | Visual Type | Purpose |
|---------------|-------------|---------|
| **Slicer_Pane** | Slicer   | Vertical slicer bar for fast context switching. |
| **Focus_Area**  | One dominant analysis visual | 30s: Focus on "Why?" — e.g. driver hierarchy, decomposition. |
| **Support_1**   | Small context visual | Temporal or regional context for the Focus_Area. |
| **Support_2**   | Like Support_1 | Second context (different dimension or metric). |

When KPIs are also required in the Investigator layout, a **KPI_Cards** slot may be added (same semantics as Pulse).
