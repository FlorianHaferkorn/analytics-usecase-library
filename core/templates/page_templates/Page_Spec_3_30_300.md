# Page Spec 3-30-300

Reference document for **where which visual is placed and why** on the two standard report pages (Overview = 3–30 seconds, Detail = 300 seconds). See [Slot_Definitions.md](governance/Slot_Definitions.md) for slot semantics and [ActionPanel_Spec.md](components/ActionPanel_Spec.md) for the Action Panel.

---

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
