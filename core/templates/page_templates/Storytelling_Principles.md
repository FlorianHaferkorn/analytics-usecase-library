# Storytelling Principles — 3-30-300 Framework

> **Authority:** This document governs the narrative and content standards for all pages built with the Analytics Use Case Library. It translates established data storytelling research into binding rules for the framework.
>
> **Implements:** `layout_330300_design_spec.md` · `page_types/T1–T4` · `Content_Quality_Guide.md`
>
> **Research basis:** Knaflic (SWD), Few (Information Dashboard Design), Tufte (Visual Display of Quantitative Information), Nielsen Norman Group (Dashboard UX), IBCS (ISO/AWI 24896), MDPI Eye-Tracking Study 2024.

---

## 1. The One Job of Every Page

A page has exactly one job: **lead the reader to a decision or action within their time horizon**.

Design, content, and narrative all serve that job. Nothing else.

If a page cannot be described in one sentence as *"This page answers [question] for [audience] so they can [action]"*, the page is not ready.

---

## 2. The Big Idea (Knaflic)

Every page must communicate exactly **one central statement** — the Big Idea. Everything else on the page supports, explains, or validates that statement.

### What the Big Idea Is

The Big Idea is a single, complete sentence that:
1. States the specific business situation
2. Conveys what is at stake
3. Is a direct call for the reader's attention or action

It is **not** a title. It is the conclusion that the reader should leave the page with.

### Big Idea Templates by Page Type

| Page Type | Big Idea Template |
|---|---|
| T1 — Strategic Overview | "[Domain] is [on/off] track — [primary KPI] is [Δ vs target], [momentum direction]." |
| T2 — Tactical Variance | "The [Δ] gap vs [reference] is driven by [top factor] ([magnitude]) — intervention in [area] is required." |
| T3 — Operational Monitoring | "[N] [entity type] are currently outside threshold — [N_critical] require immediate attention in [area]." |
| T4 — Prescriptive Recommendation | "[Trigger condition] in [context]. Recommended: [action] by [owner] — expected impact [impact] by [deadline]." |

### Where the Big Idea Lives

- The page's **decision question banner** (above or below the KPI band) states the question form of the Big Idea.
- The **Smart Narrative** on the Detail page states the answer form of the Big Idea in the current filter context.
- The **KPI band** provides the evidence for the Big Idea in 3 seconds.

### The "So What?" Test

Before any visual is added to a page, apply the "So What?" test:

> *"So what? What decision or action does this enable for this audience?"*

If the answer is "it's interesting" or "it's good to know", the visual does not belong on this page. Remove it.

---

## 3. The Narrative Arc — From Signal to Action

Every page within the 3-30-300 framework follows a three-part narrative arc. The arc applies at both the page level and the report level.

### The Arc at Page Level (Overview Page)

```
ACT 1 — ESTABLISH (3 seconds, Zone 1)
  Signal the situation.
  "Here is where we stand right now."
  → KPI band with status, delta, and reference

ACT 2 — COMPLICATE (30 seconds, Zone 3)
  Introduce the tension.
  "Here is why we are off track / what changed."
  → Trend (the journey), Variance (the gap), Ranking (the actors)

ACT 3 — RESOLVE (300 seconds, Detail page)
  Provide resolution.
  "Here is what to do / where exactly it happened."
  → Smart Narrative, Detail Matrix, Action Panel (T4)
```

### The Arc at Report Level (Multi-Page)

| Page | Role in Arc | Template |
|---|---|---|
| T1 — Strategic Overview | Establish: "We are off track" | Opens the story |
| T2 — Tactical Variance | Complicate: "Here is why" | Adds tension |
| T3 — Operational Monitoring | Complicate: "Here is where" | Locates the problem |
| T4 — Prescriptive | Resolve: "Here is what to do" | Closes the arc |

A well-structured analytics product leads users through T1 → T2 → T4 (or T1 → T3 → T4) as a natural narrative chain. Each escalation tightens the story.

---

## 4. Visual Hierarchy and Attention Direction

The spatial layout of a page must mirror its information hierarchy. The most important information occupies the highest-attention zones.

### Attention Zones (Eye-Tracking Research, MDPI 2024)

| Zone | Attention Level | Content Rule |
|---|---|---|
| Top-left | Highest | First KPI (strategic or most deviated). Big Idea statement. |
| Top-right | High | Remaining KPI cards or decision question banner |
| Left column (below top) | High | Slicer pane (Detail pages). First driver visual (Overview). |
| Center body | Medium | Driver visuals, main charts |
| Bottom-right | Low | Navigation, supplementary context, export controls |

**Rule:** If the reader's first glance lands on decoration, a slicer, or a title instead of the key finding — the layout has failed. Place the signal where the eye goes first.

### Pre-Attentive Attributes — Priority and Use

These attributes are processed before conscious attention. Use exactly **one** per canvas zone to direct focus. Using multiple simultaneously cancels each other out.

| Attribute | Strength | Primary Use | Rule |
|---|---|---|---|
| **Color (semantic)** | Highest | Status signal on KPI delta, variance bars | Max 3–4 semantic colors per page; semantic role permanent |
| **Size** | High | KPI primary value (largest element per card) | Primary value ≥ 2× the size of secondary values |
| **Position** | Highest for quantity | Bar length, point position on axis | Zero-based axes mandatory for bars |
| **Bold weight** | Medium | Highlight the one key number per visual | Use for exactly one element per chart |
| **Shape / icon** | Medium | Direction indicators (▲▼⚠─) | Always paired with color — never color alone |
| **Motion** | Highest for alerting | Live operational dashboards only | Never use in analytical/report contexts |

### The 2-Second Rule (Knaflic)

Close your eyes, open them, and note where your gaze falls first. That is where the most important message must be. Run this test on every completed page.

---

## 5. Progressive Disclosure — 3-30-300 as a Design Pattern

Progressive disclosure (NNG) means: show the minimum needed at each level; reveal more detail only when the user requests it.

The 3-30-300 model is progressive disclosure applied to business reporting:

```
Level 1 (3s)  — Answer the question "Am I on track?"
                 Do NOT require the user to go to Level 2 to understand the answer.

Level 2 (30s) — Answer "Why am I off track?"
                 Do NOT require the user to go to Level 3 to understand the drivers.

Level 3 (300s) — Answer "What exactly / what should I do?"
                 Only reached by users who need validation or action detail.
```

**Violation test:** If a user at Level 1 cannot answer their headline question without drilling to Level 2, the Level 1 design has failed. Same logic applies between Level 2 and Level 3.

---

## 6. Gestalt Principles — Grouping, Flow, and Boundary

Gestalt perception rules govern how users interpret spatial relationships on a page before they read anything.

### Applied Rules

| Principle | Dashboard Rule | Violation |
|---|---|---|
| **Proximity** | Group related visuals with tight spacing (≤16px); separate unrelated groups with clear white space (≥40px) | Revenue chart placed next to Cost slicer without separation → implies false relationship |
| **Similarity** | Same color = same meaning, same chart type = same analytical purpose | Orange used for "warning KPI" and also for "West Region" bar → semantic collision |
| **Continuity** | Align chart baselines, card edges, and label positions on the grid | Misaligned chart axes across a row → perceived disorder, breaks comparison |
| **Closure** | Use white space to form visual groups; avoid unnecessary box borders | A box around a group that white space already defines → adds visual noise |
| **Common Region** | Subtle card background or shared container groups semantically related content | KPI card and its supporting trend chart share a container → reinforces their relationship |
| **Figure/Ground** | Light, neutral page background ensures data elements read as foreground | Dark background on charts only works when tested for WCAG AA contrast on all data labels |

**Audit rule:** Every visual grouping on a page implies a relationship. If two visuals are grouped (by proximity or container) but are not conceptually related, separate them explicitly.

---

## 7. Data-Ink Ratio — Eliminating Non-Data Elements

Every pixel on a page either encodes data or helps interpret data. Everything else is noise that competes for the reader's attention.

### Decluttering Priority List (apply in this order)

1. **Remove background fills** on charts and cards (replace with white or transparent)
2. **Remove grid lines** or reduce to very light gray (1px, 15–20% opacity)
3. **Remove chart borders and boxes** — white space is sufficient for grouping
4. **Remove legends** where direct labeling is possible
5. **Remove redundant axis labels** (e.g., don't show both an axis title and a chart title that say the same thing)
6. **Remove data labels on every point** — show only at inflection points, endpoints, or highlighted values
7. **Remove 3D effects, gradients, shadows** — they add no data information
8. **Remove decorative color** — every color must carry semantic meaning or encode a data category

### What Must Remain

After decluttering, verify these elements are still present:
- Axis reference that enables value reading (either axis tick marks or direct labels)
- A clear visual title that states the question the chart answers
- The reference value (target, prior year, plan) wherever a comparison is possible
- Signal annotation (color + icon) on the value being compared

---

## 8. Annotation and Callout Patterns

Charts must not require the reader to interpret signal from raw data. The most important finding should be highlighted directly on the visual.

### Annotation Types

| Type | When to Use | How |
|---|---|---|
| **Inflection callout** | When a trend changes direction significantly | Vertical reference line + label "Oct: promotion launched" |
| **Reference line** | When a target, threshold, or prior period exists | Dashed line, lighter weight than primary series |
| **Data callout** | When one specific value is the Big Idea for that chart | Bold the label or add a text callout box with the key number |
| **Deviation annotation** | On variance/waterfall charts | Show the absolute value and % on each bar, not just bar height |
| **Period annotation** | When the time range is not immediately obvious from axis | Label the period at top-right or in the chart subtitle |

### Direct Labeling vs. Legends

- Use direct labels at line endpoints instead of a legend wherever possible
- The eye-travel between a legend and the line it describes is a comprehension cost
- Maximum 4–5 series before direct labeling becomes unreadable; at that point, consider small multiples instead

---

## 9. Color System (Semantic Roles)

Color carries meaning before words are read. Semantic roles must be consistent across the entire report.

### Four Semantic Roles

| Role | Color (default) | Meaning | Never used for |
|---|---|---|---|
| `semantic.positive` | Green (accessible) | Favourable delta, above target | Brand accents, general category encoding |
| `semantic.negative` | Red | Unfavourable delta, below target, alert | Neutral data, category encoding |
| `semantic.warning` | Amber/Orange | Near threshold, approach with caution | Positive signals, brand color |
| `semantic.neutral` | Gray | No signal, informational, no target | Performance-coded data |

> **Accessibility rule:** Never use red/green alone. Always pair with an icon (▲▼⚠─) and optionally bold/regular weight. 8% of males have red-green color deficiency. The diverging pair **blue/orange** is the colorblind-safe alternative for variance charts — prefer this when color accessibility is critical.

### Color Count Limit

- Maximum **3–4 colors** visible on any single page
- Categorical series: use `brand.data_colors[0–7]` only
- Semantic roles take precedence over categorical colors

---

## 10. Typography Hierarchy

Typography establishes information hierarchy before the reader consciously processes content.

### Scale (design base 1280×720)

| Role | Size | Weight | Usage |
|---|---|---|---|
| `page_title` | 16–18pt | Regular | Page / report title (decision question) |
| `section_header` | 13–14pt | Semibold | Visual title (question-oriented) |
| `kpi_value` | 28–36pt | Bold | Hero number on KPI card |
| `kpi_delta` | 13–14pt | Regular | Variance value + icon on KPI card |
| `kpi_label` | 10–11pt | Regular, muted | KPI name below the value |
| `axis_label` | 9–11pt | Regular | Chart axis tick labels |
| `data_label` | 10–11pt | Regular | On-chart data labels (sparse) |
| `footnote` | 8–9pt | Regular, muted | Data source, timestamp, notes |

### Rules

- **One font family** across all pages. Vary only weight and size.
- **Sans-serif only** for digital display (Segoe UI, Inter, Roboto, Open Sans).
- **Tabular (monospaced) numerals** required for any column of numbers users will compare vertically. Prevents column-width shifts as values change.
- **No ALL CAPS** for extended text. Title case for labels; sentence case for narrative.
- Minimum 11pt for any text the reader must read; 9pt only for reference footnotes.

---

## 11. White Space

White space is not empty space — it is grouping signal, focus amplifier, and breathing room.

### Rules

- **16px** gap between visuals within the same zone
- **40px** gap between zone groups (e.g., KPI band to slicer bar, slicer bar to driver zone)
- **8px** internal padding inside card containers
- **32px** outer margin from canvas edges (all sides)
- Do not fill all available space. An isolated KPI element is perceived as important because it is not competing with adjacent content.

Research shows appropriate white space increases report comprehension by ~20% (compared to densely filled layouts).

---

## 12. IBCS Notation Principles (ISO/AWI 24896)

The SUCCESS formula from International Business Communication Standards governs chart notation:

| Letter | Rule | Implementation |
|---|---|---|
| **S**AY | Chart title = conclusion, not description | "Revenue declined 12% YoY" not "Revenue by Month" |
| **U**NIFY | Consistent abbreviations across all charts | AC = Actual, PY = Prior Year, PL = Plan, FC = Forecast |
| **C**ONDENSE | Maximum information density | Small multiples over sequential pages; integrated variance bars |
| **C**HECK | Visual integrity | Zero-based bar axes; area proportional to value; no truncated y-axis without disclosure |
| **E**XPRESS | Right chart for the message | Time → line; ranking → bar; part-whole → stacked bar; correlation → scatter |
| **S**IMPLIFY | Remove chart junk | No gradients, no 3D, no decorative borders |
| **S**TRUCTURE | Logical spatial organization | Time left → right; hierarchy top → bottom; importance left → right in bars |

---

## 13. The Narrative Contract Between Pages

In a 2-page use case (Overview + Detail), the pages must form a coherent narrative:

1. The **Overview page** poses the question and signals the answer.
2. The **Detail page** validates the answer and enables action.

A reader who sees only the Overview should understand the situation. A reader who needs to act should find all they need on the Detail page without returning to the Overview.

**Drillthrough contract:** The filter context passed from Overview to Detail must be exact. A user drilling from "DACH on the ranking chart" must land on the Detail page with DACH already filtered — not on an unfiltered Detail page where they must re-select.

---

## References

| Source | Contribution |
|---|---|
| Cole Nussbaumer Knaflic — *Storytelling with Data* | Big Idea, pre-attentive attributes, decluttering, "So What?" test |
| Stephen Few — *Information Dashboard Design* | Single-screen discipline, KPI context requirements, chart selection |
| Edward Tufte — *The Visual Display of Quantitative Information* | Data-ink ratio, small multiples, sparklines, graphical integrity |
| Nielsen Norman Group | F/Z-pattern, progressive disclosure, cognitive load |
| IBCS / ISO/AWI 24896 | SUCCESS formula, unified notation, chart type selection |
| MDPI Sensors — Eye-Tracking Study 2024 | Hierarchical layout order, attention zone empirical validation |
| SQLBI — 3-30-300 Rule | Zone order, slicer placement, progressive disclosure in reporting |
| Gestalt Psychology | Proximity, similarity, continuity, closure, common region |
