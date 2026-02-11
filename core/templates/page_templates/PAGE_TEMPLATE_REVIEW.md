# Page Template Review — Completeness and Visual Alignment

## Purpose

This document reviews whether the four page templates (T1–T4) fulfill their roles perfectly, including visual specifications, and identifies any gaps or improvements needed before creating standardized Power BI page scaffolds.

---

## Review Summary

### Overall Assessment

**Strengths:**
- Clear decision-oriented purpose per template (T1: strategic, T2: tactical variance, T3: operational, T4: prescriptive)
- 3-30-300 rule is explicit and enforced
- Visual Whitelist is restrictive and clear
- Slot definitions are semantic (not visual), allowing flexibility within constraints
- Action Panel spec is clear for T4

**Gaps Identified:**
1. **Visual-to-slot mapping is incomplete** — Templates list allowed visuals per slot, but there's no explicit "which visual type for which slot" matrix that a generator can use.
2. **Layout structure is abstract** — `overview_drivers_details.json` exists but is very abstract; no concrete layout grid/positioning for Power BI scaffolds.
3. **Slicer placement and defaults** — Templates mention slicer limits but not placement (top, side, collapsible) or default values.
4. **Visual sizing and positioning** — No guidance on visual dimensions, spacing, or responsive behavior.
5. **Color and formatting rules** — Visual Whitelist doesn't specify color semantics (e.g. red = below target, green = above target) or formatting standards (e.g. KPI cards always show delta, trend charts always show target line if variance slot exists).

---

## Template-by-Template Review

### T1 — Strategic Overview

**Purpose:** ✅ Clear — "Are we on track?"

**Slots:** ✅ Well-defined
- KPI Summary (mandatory)
- Trend (mandatory)
- Variance (optional)
- Ranking (optional)
- Mix (optional)

**Visuals:** ⚠️ **Gap**
- Templates say "KPI Cards with target / delta" but don't specify:
  - Format: always show target line? Always show % delta?
  - Color: green/red semantics or neutral?
  - Size: how many KPIs fit in one row?
- "Line charts for trends" — no guidance on:
  - Should target/plan line be included if variance slot is active?
  - Multi-series (e.g. Actual vs Plan vs LY) allowed?
- "Horizontal bar charts for rankings" — no guidance on:
  - Max items shown (top 10? top 20?)
  - Sorting (always descending? configurable?)

**Layout:** ⚠️ **Gap**
- No concrete grid structure (e.g. "KPI cards row 1, Trend visual row 2, Ranking row 3")
- No guidance on responsive behavior (what if screen is narrow?)

**Action Signals:** ✅ Clear — Strategic only, max 1–2 callouts, no Action Panel

---

### T2 — Tactical Variance

**Purpose:** ✅ Clear — "Why are we off target?"

**Slots:** ✅ Well-defined
- KPI Summary (mandatory)
- Variance (mandatory) — this is the key differentiator
- Trend (optional)
- Ranking (optional)
- Mix (optional)
- Funnel (optional, non-default)

**Visuals:** ⚠️ **Gap**
- "Waterfall charts for variance explanation" — no guidance on:
  - Structure: always start from Plan/Target? Always end at Actual?
  - Color: positive vs negative effects (green/red or neutral?)
  - Labels: show absolute values? percentages? both?
- "KPI cards with target reference" — same gaps as T1
- Funnel charts are "non-default" but no criteria for when to use them

**Layout:** ⚠️ **Gap**
- No guidance on "variance bridge first, then drivers" vs "drivers first, then bridge"
- No guidance on whether variance and trend can share space

**Action Signals:** ✅ Clear — Tactical only, no ownership assignment

---

### T3 — Operational Monitoring

**Purpose:** ✅ Clear — "Where are issues emerging right now?"

**Slots:** ✅ Well-defined
- Exceptions (mandatory) — key differentiator
- KPI Summary (optional)
- Ranking (optional)
- Trend (optional)
- Root Cause (optional)
- Detail Matrix (optional, Detail pages only)

**Visuals:** ⚠️ **Gap**
- "Exception tables or lists" — no guidance on:
  - Columns: what must be shown (entity, threshold, actual, deviation, owner)?
  - Formatting: how to highlight critical vs warning?
  - Max rows before pagination?
- "Scatter plots (except in T4)" — but T3 allows Root Cause slot; should scatter plots be allowed for Root Cause in T3? Visual Whitelist says scatter plots are T3/T4 only, but T3 summary says "disallowed: scatter plots". **Contradiction needs resolution.**
- "Horizontal bar charts for prioritization" — same gaps as T1/T2

**Layout:** ⚠️ **Gap**
- No guidance on "exceptions first" vs "KPI summary first"
- No guidance on exception grouping (by owner? by severity?)

**Action Signals:** ✅ Clear — Operational only, immediate response triggers

---

### T4 — Prescriptive Recommendation

**Purpose:** ✅ Clear — "What should we do next?"

**Slots:** ✅ Well-defined
- Prescriptive (mandatory) — key differentiator
- KPI Summary (optional)
- Trend (optional)
- Ranking (optional)
- Root Cause (optional)
- Detail Matrix (optional)

**Visuals:** ⚠️ **Gap**
- "Recommendation tables or cards" — no guidance on:
  - Structure: one primary + alternatives? ranked list?
  - Columns: action, owner, impact, priority, confidence?
  - Formatting: how to highlight "best next action"?
- "Scatter plots (impact vs. effort or risk)" — no guidance on:
  - Axes: what goes on X/Y?
  - Quadrants: should they be labeled (e.g. "Quick wins", "Strategic")?
- Action Panel is mandatory but no visual spec for how it integrates with the page layout

**Layout:** ⚠️ **Gap**
- Action Panel placement (right-side panel) is mentioned in ActionPanel_Spec but not in T4 template
- No guidance on "recommendation first" vs "context first"

**Action Panel:** ✅ Spec exists in `components/ActionPanel_Spec.md` but should be referenced from T4 template

---

## Visual Whitelist Review

**Strengths:**
- Clear allowed/disallowed list
- Template-specific rules (e.g. scatter plots only T3/T4)
- Slot-specific rules (e.g. tables/matrices only Detail pages)

**Gaps:**
1. **Color semantics** — No guidance on when to use red/green vs neutral colors. Should be: red = below target/bad, green = above target/good, neutral = informational. But this is not documented.
2. **Formatting standards** — No guidance on:
   - KPI cards: always show delta? always show target?
   - Trend charts: always show target line if variance exists?
   - Waterfall: always show absolute + %?
3. **Visual sizing** — No guidance on:
   - KPI card dimensions (e.g. min width, aspect ratio)
   - Chart dimensions (e.g. trend charts should be wide enough to show 12+ months)
   - Max items in ranking charts (top 10? top 20?)
4. **Contradiction:** T3 template says "Disallowed: Scatter plots" but Visual Whitelist says scatter plots are allowed in T3 for Root Cause slot. **Needs resolution.**

---

## Slot Definitions Review

**Strengths:**
- Semantic, not visual — slots define "what question" not "what visual"
- Clear allowed templates per slot
- Clear "not allowed when" rules

**Gaps:**
1. **Visual-to-slot mapping** — While Visual Whitelist maps visuals to slots, there's no explicit "for slot X, prefer visual Y, fallback Z" guidance that a generator can use.
2. **Slot combinations** — No guidance on which slots work well together (e.g. Variance + Ranking is common; Variance + Funnel is rare).

---

## Recommendations for Page Scaffolds

### 1. Resolve Contradictions

- **T3 scatter plots:** Decide if scatter plots are allowed for Root Cause in T3. Recommendation: **Yes, if `needs_root_cause = true`** (align with Visual Whitelist, update T3 template summary).
- **Visual Whitelist vs template summaries:** Ensure template markdown files match Visual Whitelist exactly.

### 2. Add Visual-to-Slot Mapping

Create a matrix or JSON that maps:
- Slot → Preferred visual type → Fallback visual type → Formatting rules

Example:
```yaml
slots:
  variance:
    preferred_visual: waterfall
    fallback_visual: horizontal_bar
    formatting:
      - show_absolute_values: true
      - show_percentages: true
      - color_positive: neutral_blue
      - color_negative: neutral_red
```

### 3. Add Layout Structure

Define concrete layout grids for Power BI scaffolds:
- Row/column structure (e.g. "Row 1: KPI cards (4 columns), Row 2: Trend (full width), Row 3: Variance (full width)")
- Visual dimensions (e.g. KPI card: 200px width, 120px height)
- Spacing (e.g. 10px gap between visuals)

### 4. Add Color and Formatting Standards

Document:
- Color semantics (red/green vs neutral)
- KPI card format (always show delta, always show target if available)
- Chart defaults (trend charts show target line if variance slot exists)

### 5. Add Slicer Placement Rules

Document:
- Default placement (top vs side)
- Collapsible behavior
- Default values (e.g. time slicer defaults to "Last 12 months")

---

## Next Steps

1. **Resolve contradictions** (T3 scatter plots, template vs whitelist alignment)
2. **Create visual-to-slot mapping** (JSON or YAML for generator use)
3. **Define layout structure** (concrete grid for Power BI scaffolds)
4. **Add formatting standards** (color, KPI cards, chart defaults)
5. **Create page scaffold generator spec** (input: use case + template mapping → output: PBIP page structure)

---

## References

- Page templates: `page_types/T1_Strategic_Overview.md`, `T2_Tactical_Variance.md`, `T3_Operational_Monitoring.md`, `T4_Prescriptive_Recommendation.md`
- Visual Whitelist: `governance/Visual_Whitelist.md`
- Slot Definitions: `governance/Slot_Definitions.md`
- Action Panel Spec: `components/ActionPanel_Spec.md`
- Use Case Mapping: `mappings/UseCase_PageTemplate_Map.yaml`
