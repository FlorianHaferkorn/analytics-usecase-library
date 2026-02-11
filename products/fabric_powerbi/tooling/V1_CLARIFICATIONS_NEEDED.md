# V1 Finalization — Clarifications Needed

## Overview

This document lists **unclear points and missing topics** that need to be defined before implementing the page scaffold generator and report documentation generator. For each item, we propose whether to:
- **Research best practices** (industry standards, Power BI guidance, UX principles)
- **Define together** (framework-specific decisions that require your input)
- **Both** (research first, then define together)

---

## 1. Visual-to-Slot Mapping (Formal Governance)

**Status:** ⚠️ Partially defined in scaffold spec, but needs formal governance file

**Current State:**
- Table exists in `page_scaffold_spec.md` (lines 46-57)
- Not yet a governed artifact that can be validated

**Missing:**
- Should this be a YAML/JSON file in `framework/templates/page_templates/governance/`?
- Should it be validated in Stage 1 CI?
- Are there edge cases (e.g., "if both Trend and Variance exist, combine in one visual?")?

**Recommendation:** **Define together** — Framework-specific decision on where this lives and how it's governed.

---

## 2. Layout Grid System

**Status:** ⚠️ Examples provided, but no systematic grid system

**Current State:**
- Concrete examples for T2 and T4 in scaffold spec
- No general rules for all templates

**Missing:**
- Standard grid dimensions (12-column? 16-column? pixel-based?)
- Spacing rules (gaps between visuals, padding from edges)
- Responsive behavior (what happens on smaller screens?)
- Z-order rules (which visuals can overlap?)

**Recommendation:** **Research best practices** — Power BI has standard page dimensions and visual positioning. Research:
- Power BI default page sizes and visual positioning
- Industry standards for dashboard grid systems
- Then **define together** — Framework-specific spacing and layout rules

---

## 3. Slicer Placement and Behavior

**Status:** ⚠️ Mentioned but not fully defined

**Current State:**
- Scaffold spec mentions "top" or "side" slicers
- No rules on when to use which

**Missing:**
- When to use top slicers vs side slicers?
- Default slicer width/height?
- Collapsible behavior (always collapsed? always expanded?)
- Default values (current month? last 3 months? all?)
- Multi-select vs single-select defaults?

**Recommendation:** **Research best practices** — Power BI UX guidance on slicer placement. Then **define together** — Framework defaults.

---

## 4. Visual Sizing and Spacing

**Status:** ⚠️ Basic sizes defined, but incomplete

**Current State:**
- KPI Card: 280×140px (standard), 200×120px (compact)
- Trend/Variance: min 800×400px
- No spacing rules

**Missing:**
- Standard gaps between visuals (10px? 20px? 30px?)
- Padding from page edges (20px? 40px?)
- When to use compact vs standard KPI cards?
- Max visual count per row/column?
- Visual aspect ratios (should charts maintain 16:9? 4:3?)

**Recommendation:** **Research best practices** — Power BI visual sizing standards, dashboard design principles. Then **define together** — Framework-specific spacing rules.

---

## 5. Color Semantics and Formatting Rules

**Status:** ❌ Not defined

**Missing:**
- **Color semantics:**
  - Red = below target? negative variance? exception?
  - Green = above target? positive variance? good?
  - Yellow/Orange = warning? near threshold?
  - Gray = neutral? no data?
- **KPI Card formatting:**
  - When to show trend arrow (up/down)?
  - When to show percentage vs absolute value?
  - Format for currency, percentages, large numbers?
- **Chart formatting:**
  - Default color palette (from theme? framework default?)
  - Target line color/style?
  - Grid lines (show/hide? color?)
  - Axis labels (font size, rotation?)

**Recommendation:** **Research best practices** — Data visualization color semantics, Power BI formatting best practices. Then **define together** — Framework-specific color rules aligned with theme generator.

---

## 6. Exception Table Structure

**Status:** ⚠️ Mentioned but not defined

**Current State:**
- T3 template says "exception tables or lists"
- No column definitions

**Missing:**
- Required columns (entity, threshold, actual, deviation, owner, severity?)
- Optional columns (trend? last updated? action taken?)
- Formatting rules (how to highlight critical vs warning?)
- Max rows before pagination (20? 50? 100?)
- Sorting defaults (by severity? by deviation? by owner?)

**Recommendation:** **Define together** — Framework-specific decision based on use case requirements. Can reference existing use cases (OPS-001, OPS-002, GOV-001) for examples.

---

## 7. Prescriptive Table Structure

**Status:** ⚠️ Mentioned but not defined

**Current State:**
- T4 template says "recommendation tables or cards"
- No structure defined

**Missing:**
- Required columns (action, owner, impact, priority, confidence, due date?)
- Optional columns (alternatives? dependencies? cost?)
- Formatting rules (how to highlight "best next action"?)
- Max recommendations shown (top 5? top 10? all?)
- Sorting defaults (by priority? by impact? by confidence?)

**Recommendation:** **Define together** — Framework-specific decision. Can reference Action Panel spec and action codes for structure.

---

## 8. Scatter Plot Axes and Quadrants

**Status:** ⚠️ Mentioned but not defined

**Current State:**
- T4 template mentions "impact vs. effort or risk"
- No axis definitions

**Missing:**
- X-axis: effort? cost? risk? time?
- Y-axis: impact? value? priority?
- Quadrant labels (e.g., "Quick wins", "Strategic", "Avoid", "Fill-ins")?
- Color coding by quadrant?
- Max data points before aggregation?

**Recommendation:** **Research best practices** — Impact/Effort matrix best practices, decision matrix visualization. Then **define together** — Framework-specific defaults.

---

## 9. Action Panel Integration with Page Layout

**Status:** ⚠️ Spec exists but integration unclear

**Current State:**
- `ActionPanel_Spec.md` defines Action Panel structure
- Scaffold spec mentions "right side, 350px width"
- No rules on when visuals can overlap with Action Panel

**Missing:**
- Should visuals resize when Action Panel is present?
- Can visuals extend under Action Panel (with Action Panel on top)?
- Action Panel z-order (always on top? can visuals overlay?)
- Action Panel default state (collapsed? expanded? pinned?)

**Recommendation:** **Define together** — Framework-specific UX decision. Review ActionPanel_Spec.md and decide on integration rules.

---

## 10. Theme Integration with Scaffolds

**Status:** ⚠️ Mentioned but not defined

**Current State:**
- Scaffold spec mentions `"theme": "<theme_name>"` in page metadata
- No rules on how theme name is determined

**Missing:**
- How does scaffold reference theme? (theme name? theme file path? theme ID?)
- Default theme if none specified?
- Per-showcase theme vs framework default?
- Should scaffold generator validate theme exists?

**Recommendation:** **Define together** — Framework-specific decision. Review theme generator output structure and decide on reference mechanism.

---

## 11. Detail Matrix Structure

**Status:** ⚠️ Mentioned but not defined

**Current State:**
- All detail pages have `needs_detail_matrix: true`
- No structure defined

**Missing:**
- Table vs Matrix visual? (when to use which?)
- Required columns (all dimensions? all measures? selected KPIs?)
- Formatting rules (conditional formatting? heatmap?)
- Max rows/columns before pagination?
- Default sorting?

**Recommendation:** **Research best practices** — Power BI Table vs Matrix best practices. Then **define together** — Framework-specific defaults.

---

## 12. Funnel Chart Structure

**Status:** ⚠️ Mentioned but not defined

**Current State:**
- T2 template allows funnel chart for Funnel slot
- No structure defined

**Missing:**
- Required fields (stage name, value, conversion rate?)
- Optional fields (target? variance? owner per stage?)
- Formatting rules (color by conversion rate? show percentages?)
- Max stages before aggregation?

**Recommendation:** **Research best practices** — Funnel chart best practices, conversion funnel visualization. Then **define together** — Framework-specific defaults.

---

## Priority Order

### High Priority (Block Scaffold Generator)
1. **Visual-to-Slot Mapping (Formal Governance)** — Need to know where this lives
2. **Layout Grid System** — Need systematic rules, not just examples
3. **Slicer Placement and Behavior** — Need defaults for scaffold generation
4. **Visual Sizing and Spacing** — Need complete sizing rules

### Medium Priority (Block Documentation Generator)
5. **Exception Table Structure** — Need to document structure
6. **Prescriptive Table Structure** — Need to document structure
7. **Color Semantics and Formatting Rules** — Need for documentation completeness

### Lower Priority (Can Iterate)
8. **Scatter Plot Axes and Quadrants** — Can refine after initial implementation
9. **Action Panel Integration** — Can refine after initial implementation
10. **Theme Integration** — Can refine after initial implementation
11. **Detail Matrix Structure** — Can refine after initial implementation
12. **Funnel Chart Structure** — Can refine after initial implementation

---

## Next Steps

**Option A: Research First**
- I research best practices for items marked "Research best practices"
- Then we define framework-specific rules together

**Option B: Define Together First**
- We discuss and define framework-specific rules directly
- Research only if we hit unknowns

**Option C: Hybrid**
- Research high-priority items first (Layout Grid, Slicer Placement, Visual Sizing)
- Define together medium-priority items (Exception/Prescriptive Tables, Color Semantics)
- Iterate on lower-priority items after initial implementation

**Recommendation:** **Option C (Hybrid)** — Research high-priority items to ensure we follow Power BI best practices, then define framework-specific rules together.

---

## Questions for You

1. **Priority:** Which items are most critical for you? Should we focus on high-priority items first, or do you want to define all before implementation?

2. **Research vs Define:** For items marked "Research best practices", do you want me to research first, or do you have preferences already?

3. **Iteration:** Are you comfortable iterating on lower-priority items after initial scaffold generator implementation, or do you want everything defined upfront?

4. **Showcase Context:** Should we look at existing Aurora Group reports for examples, or start fresh with framework standards?
