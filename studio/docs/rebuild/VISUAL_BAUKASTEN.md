# Visual Baukasten

> **Status:** Authoritative  
> **Authority:** `PAGE_TEMPLATE_DOCTRINE.md` (encoding rules, perceptual hierarchy, IBCS notation)  
> **Governs:** Which visual may fill which slot, under which conditions, with which quality rules  
> **Machine-readable registry:** `core/templates/page_templates/visual_registry.yaml`

---

## 1. Purpose and Principles

The Visual Baukasten defines **information blocks** as the atomic unit of page design.

An **information block** is not a visual. It is an analytical task: "show variance to reference", "rank entities by metric", "list exceptions with severity". Visuals are **implementations** of information blocks. Multiple visuals may implement the same block — they are substitutable if and only if:

1. The **analytical task** (what question does this block answer?) is preserved
2. The **data inputs** required are equivalent
3. The **perceptual accuracy** is at least as good per Cleveland & McGill (S2)
4. The **IBCS semantics** (variance notation, scenario labels) are preserved (S9)
5. The **Power BI native visual** is preferred over custom visuals (S12 — performance + a11y)

**Visual substitution is not a style preference. It is a contract.**

---

## 2. Information Block Registry

### Block 1: `status_signal`

**Purpose:** Immediately communicate whether a KPI is on-track, at-risk, or off-track.  
**Slot:** `KPI_Cards`  
**Primary Layer:** 3 seconds  
**Page Types:** T1, T2, T3, T4

**Required Inputs:**
- `actual_value`
- `target_value` or `reference_scenario` (PL or PY)
- `absolute_delta` (computed: actual − reference)
- `relative_delta` (computed: Δ / reference)
- `status` enum: `on_track | at_risk | off_track`

**Allowed Visuals:**

| Visual | Power BI Type | Condition |
|---|---|---|
| KPI Card with delta | `cardVisual` | Default — use when space allows |
| Bullet Graph | Custom visual (Enlighten or equiv.) | Use when ≥4 KPIs and space is constrained |

**Forbidden Visuals:**
- Gauge / speedometer (S7 — 90% non-data ink; use KPI card instead)
- Pie / donut (S2 — angle encoding, no reference encoding possible)
- Radar (S2 — angle encoding, axes non-comparable)

**Quality Rules:**
- Both absolute and relative delta must be displayed simultaneously (S9 — IBCS EXPRESS E3)
- Status color must not be the only encoding — add icon or label (S14 — WCAG colorblind)
- Favorable delta = positive convention; unfavorable = negative — never reversed
- Font size minimum 16pt for value field at 1280×720; 24pt at 1920×1080 (S12)
- Title must name the KPI and the reference scenario (e.g., "Net Sales vs Plan YTD")

---

### Block 2: `time_trend`

**Purpose:** Show the direction and momentum of a KPI over a defined time window.  
**Slot:** `Trend` (Main_1 on most page types)  
**Primary Layer:** 30 seconds  
**Page Types:** T1, T2, T3

**Required Inputs:**
- `time_dimension` (date grain: daily, weekly, monthly)
- `actual_series` (one data series)
- `reference_series` (optional: PL or PY as reference line)
- `time_window` (e.g., last 12 months)

**Allowed Visuals:**

| Visual | Power BI Type | Condition |
|---|---|---|
| Line chart | `lineChart` | Default — single KPI over time |
| Column chart | `clusteredBarChart` | Acceptable substitute when periodicity emphasis matters (e.g., monthly volumes) |
| Area chart | `areaChart` | T1 only; use sparingly; must not obscure reference line |
| Small multiples | `lineChart` with small multiples | When same KPI across 3–12 entities simultaneously |

**Forbidden Visuals:**
- Stacked column when showing a single KPI trend (hides the total)
- 3D line chart (depth encoding is non-functional, S2)
- Pie / donut (no temporal encoding, S2)

**Small Multiples Rules (S11):**
- Identical scale and axis range across all panels (without this, comparison is invalid)
- Maximum 12 panels; above this, use a ranked bar chart
- Same visual type within all panels

**Quality Rules:**
- Time axis must be labeled with explicit period markers (year, quarter, or month)
- If a reference line is shown (PL, PY), it must be labeled with the scenario abbreviation (S9)
- Inflection points of material significance may be annotated (text callout, not shape overlay)
- Y-axis must start at zero for volume/absolute metrics; may be truncated for rate/index metrics only with explicit explanation (S11)
- Visual title must state: metric name + time window (e.g., "Net Sales vs Plan — last 12 months")

---

### Block 3: `variance_explanation`

**Purpose:** Decompose a KPI gap into named driver contributions.  
**Slot:** `Variance` (Main_2 on T2 pages)  
**Primary Layer:** 30 seconds  
**Page Types:** T2 only

**Required Inputs:**
- `reference_value` (start: PL or PY)
- `actual_value` (end)
- `driver_contributions[]`: array of `{driver_name, absolute_contribution, direction: favorable|unfavorable}`
- sum(driver_contributions) == actual_value − reference_value (reconciliation contract)

**Allowed Visuals:**

| Visual | Power BI Type | Condition |
|---|---|---|
| Waterfall chart | `waterfallChart` | Default — canonical variance explanation visual |
| Variance bar | `clusteredBarChart` configured as deviation chart | Acceptable substitute when waterfall is not feasible in native PBI |
| Contribution table | `tableEx` or `matrix` | 300s layer only — not for the 30s variance slot |

**Forbidden Visuals:**
- Pie / donut (cannot show signed contributions, S2)
- Area chart (cannot reconcile start/end values)
- Line chart (does not encode categorical driver contributions)

**Waterfall Contract (mandatory when waterfall is used):**
- Start bar = reference value (PL or PY) — always leftmost, labeled
- End bar = actual value — always rightmost, labeled
- Intermediate bars = one per driver — labeled with absolute contribution + % of total gap
- Sum of all intermediate bars = actual − reference (engine must validate this)
- Maximum 7–8 intermediate bars; smaller drivers grouped as "Other"
- Favorable contributions: accent color (not raw green — colorblind safety, S14)
- Unfavorable contributions: warning color (not raw red — colorblind safety, S14)
- Net/subtotal bars: neutral (gray)

---

### Block 4: `entity_ranking`

**Purpose:** Rank entities by performance to identify concentration of gap or opportunity.  
**Slot:** `Ranking` (Main_2 or Main_3 on T1, T2; Main_3 on T3)  
**Primary Layer:** 30 seconds  
**Page Types:** T1, T2, T3

**Required Inputs:**
- `entity_dimension` (region, product, customer, etc.)
- `metric_value` (actual value per entity)
- `reference_value` (optional: PL or PY per entity, for deviation encoding)
- `sort_order`: descending by magnitude of deviation or absolute value

**Allowed Visuals:**

| Visual | Power BI Type | Condition |
|---|---|---|
| Horizontal bar chart | `clusteredBarChart` (horizontal) | Default — best for entity names on y-axis (readability) |
| Dot plot | Custom or scatter workaround | Acceptable when showing deviation from center line |
| Ranked table | `tableEx` | 300s layer only; not for the 30s ranking slot |
| Column chart | `clusteredBarChart` (vertical) | T3 only — acceptable for short entity lists (≤8) |

**Forbidden Visuals:**
- Pie / donut (ranking requires position encoding, S2)
- Unsorted bar charts (alphabetical ordering destroys ranking purpose)

**Quality Rules:**
- Sort descending by deviation magnitude (largest gap first) — never alphabetical (S7)
- Axis labels must be readable — truncate entity names at 20 chars with tooltip
- If reference is shown, encode deviation as a separate series or bar segment (S9)
- Maximum 15 entities before "Top 10 / Bottom 10" filter is recommended (S5)

---

### Block 5: `exception_list`

**Purpose:** Display entities that breach defined thresholds, ranked by severity and priority.  
**Slot:** `Exceptions` (Main_1 on T3)  
**Primary Layer:** 30 seconds  
**Page Types:** T3 only

**Required Inputs:**
- `entity_id`
- `metric_value`
- `threshold_value`
- `severity`: enum `critical | warning | info`
- `owner`
- `age_days` (how long has this been in exception state)
- `absolute_deviation` (metric_value − threshold_value)

**Allowed Visuals:**

| Visual | Power BI Type | Condition |
|---|---|---|
| Exception table | `tableEx` with conditional formatting | Default — column order must follow specification |
| Alert list card | Custom visual or native formatted matrix | Acceptable when severity grouping is the primary need |

**Forbidden Visuals:**
- Waterfall (no signed contribution concept for exception lists)
- Pie / donut (severity distribution pie is not actionable)
- Charts without entity-level granularity (aggregations hide the exception)

**Column Order Contract (mandatory):**
1. Entity — leftmost, always visible, anchors F-pattern scan (S7)
2. Severity — traffic-light icon + label (Critical / Warning / Info)
3. Metric — which KPI is in exception
4. Actual vs. Threshold — how far outside (absolute + %)
5. Owner — who is responsible
6. Age — how long in exception state

Maximum 6 columns without toggle. Sort: Critical first, then Warning, then by deviation magnitude descending.

---

### Block 6: `structural_mix`

**Purpose:** Show the composition of a KPI across categories.  
**Slot:** `Mix` (Main_3 on T1/T2)  
**Primary Layer:** 30 seconds  
**Page Types:** T1, T2

**Required Inputs:**
- `category_dimension`
- `actual_value` per category
- `reference_value` per category (optional)

**Allowed Visuals:**

| Visual | Power BI Type | Condition |
|---|---|---|
| 100% stacked bar | `100%StackedBarChart` | Default — best for share comparison across two periods or scenarios |
| 100% stacked column | `100%StackedColumnChart` | Acceptable substitute when time is on x-axis |

**Forbidden Visuals:**
- Pie / donut (S2 — angle encoding less accurate than length; no period comparison possible)
- Regular stacked bar/column (does not show shares, shows totals)
- Treemap (area encoding, S2 — less accurate than length)

---

### Block 7: `prescriptive_action`

**Purpose:** Present a concrete recommended action with owner, trigger, steps, and expected impact.  
**Slot:** `Prescriptive` (mandatory on T4)  
**Primary Layer:** 3 seconds (recommendation) + 30 seconds (evidence)  
**Page Types:** T4 only

**Required Inputs (from Action Code YAML):**
- `action_title`
- `owner_role`
- `trigger_condition` (the KPI condition that activated this action)
- `recommended_steps[]` (max 4 steps)
- `expected_impact` (range: min..max with unit)
- `priority`: enum `high | medium | low`
- `due_date` or `due_cycle`

**Allowed Visuals:**

| Visual | Power BI Type | Condition |
|---|---|---|
| Action panel card | Native `textbox` with structured layout | Default — see Action Panel Contract |
| Recommendation table | `tableEx` | When comparing multiple action options (T4_OptionComparison variant) |
| Impact-effort scatter | `scatterChart` | T4_OptionComparison variant only — must have `needs_prescriptive = true` |

**Forbidden Visuals:**
- Dense operational tables (not actionable at decision level)
- Exception lists (T3 content; not the same as T4 recommendation)
- Exploratory controls (slicer playground destroys decision focus)

**Action Panel Contract:**
```
RECOMMENDED ACTION        ← Bold, prominent — the Big Idea in ≤5 words
[Action title]

WHY                       ← Trigger condition in 1–2 sentences
[Trigger evidence]

WHAT TO DO                ← Ordered steps; max 4
1. [Step]
2. [Step]
3. [Step]

OWNER      [Role name]    ← Accountability
DUE        [Date/cycle]   ← When decision must be made
IMPACT     [+/- range]    ← Expected outcome if action is taken
PRIORITY   [High/Medium]  ← Relative urgency
```

If any field cannot be populated from the Action Code YAML, the action is **not ready and must not appear**. The engine must reject incomplete action panels.

---

### Block 8: `detail_matrix`

**Purpose:** Provide record-level data for validation and drill-down.  
**Slot:** `Detail_Matrix` (300s layer only)  
**Primary Layer:** 300 seconds  
**Page Types:** All (Detail pages only)

**Required Inputs:**
- Entity-level dimension
- Primary KPI value
- Reference value (where applicable)
- Deviation

**Allowed Visuals:**

| Visual | Power BI Type | Condition |
|---|---|---|
| Table | `tableEx` | Default — simple row × column with data bars |
| Matrix | `pivotTable` | When cross-tab structure adds decision value |

**Forbidden Visuals:**
- Charts (detail pages must not introduce new insights; they validate insights from the overview)

**Quality Rules:**
- Must be pre-filtered to relevant context (T3: exceptions only; T4: affected entities only)
- Column count ≤ 8 before toggle
- Sort: descending by deviation magnitude

---

### Block 9: `root_cause_context`

**Purpose:** Provide high-level contextual factors explaining why exceptions or deviations occur.  
**Slot:** `Root_Cause` (optional, T3 only)  
**Primary Layer:** 300 seconds  
**Page Types:** T3 only; requires `needs_root_cause = true`

**Required Inputs:**
- Causal factor dimensions
- Correlation or driver metric

**Allowed Visuals:**

| Visual | Power BI Type | Condition |
|---|---|---|
| Scatter plot | `scatterChart` | Default for T3 root cause — factor vs. metric |
| Decomposition tree | `decompositionTreeVisual` | Limited use; requires decision on drill path |
| Horizontal bar | `clusteredBarChart` (horizontal) | When root cause is categorical (no correlation needed) |

---

## 3. Visual Substitution Rules

A visual substitution is valid if and only if all of the following are true:

| Rule | Check |
|---|---|
| Same information block | The replacement visual answers the same analytical question |
| Same or higher perceptual accuracy | Per Cleveland & McGill hierarchy (S2): position > length > angle > area |
| IBCS semantics preserved | Scenario notation, variance colors, reference scenarios (S9) |
| Power BI native preferred | Custom visuals require Performance + A11y governance approval (S12) |
| Quality rules preserved | All mandatory quality rules for the block still apply |

**Example valid substitution:** Line chart → Column chart for `time_trend` block.  
Rationale: Both use position (bar length) or position (point on y-axis) as primary encoding; both support reference series; IBCS notation applicable to both.

**Example invalid substitution:** Waterfall → Pie for `variance_explanation` block.  
Rationale: Pie uses angle encoding (lower accuracy, S2); cannot show signed contributions; cannot reconcile start/end values; IBCS notation not applicable to pie charts.

---

## 4. Visual Group Summary

| Group | Information Blocks | Primary Encoding |
|---|---|---|
| Status / Signal | `status_signal` | Position (bar length), color + icon |
| Time & Trend | `time_trend` | Position on common scale (y-axis) |
| Variance / Decomposition | `variance_explanation` | Signed length (waterfall bars) |
| Ranking / Prioritization | `entity_ranking` | Length on common scale (bar length) |
| Exceptions / Control | `exception_list` | Position (table row) + semantic color |
| Composition / Mix | `structural_mix` | Length (100% stacked) |
| Action / Decision | `prescriptive_action` | Text structure (action panel) |
| Validation / Detail | `detail_matrix`, `root_cause_context` | Position (table row), position + length (scatter) |

---

## 5. Definition of Done

- [ ] Every information block has: purpose, slot mapping, required inputs, allowed visuals, forbidden visuals, quality rules
- [ ] Every allowed visual has a Power BI native type mapping
- [ ] Every forbidden visual has a source-backed reason
- [ ] `visual_registry.yaml` is generated from this document's contracts
- [ ] The Studio `PageTemplatePreview` renders each block using the allowed visuals only
- [ ] The Fabric PBIR generator validates visual selection against this registry
- [ ] Any new visual addition requires updating this document + the machine-readable registry
