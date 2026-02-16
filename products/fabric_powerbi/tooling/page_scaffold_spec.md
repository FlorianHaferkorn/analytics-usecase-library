# Power BI Page Scaffold Specification

## Purpose

This document defines how to generate **standardized Power BI report pages** (PBIP page structure) from page templates and use case mappings. The scaffold is a **structural skeleton** that can be opened in Power BI Desktop and populated with measures and visuals; it does not generate final visuals automatically.

**Input:** Use case ID + `UseCase_Bracket.yaml` (`ux_layout_rules`) + page template definitions  
**Output:** PBIP page JSON structure (`.pbir` definition) with:
- Page metadata (name, display name, theme)
- Visual placeholders (type, position, size, basic properties)
- Slicers (type, position, default values)
- Action Panel placeholder (if T4 or `needs_action_panel = true`)

## Governance References

This specification references the following framework governance files:

- **Visual-to-Slot Mapping:** `core/templates/page_templates/governance/Visual_to_Slot_Mapping.yaml`
- **Layout Grid System:** `core/templates/page_templates/governance/Layout_Grid_System.yaml`
- **Color Semantics & Formatting:** `core/templates/page_templates/governance/Color_Semantics_Formatting.yaml`
- **Visual Whitelist:** `core/templates/page_templates/governance/Visual_Whitelist.md`
- **Slot Definitions:** `core/templates/page_templates/governance/Slot_Definitions.md`

---

## Scaffold Structure

### 1. Page Metadata

```json
{
  "name": "page_<use_case_id>_overview",
  "displayName": "<Use Case Title> - Overview",
  "displayOption": "FitToPage",
  "height": 1080,
  "width": 1920,
  "showGrid": false,
  "snapToGrid": false,
  "theme": "<theme_name>"
}
```

**Rules:**
- Page name: `page_<use_case_id>_<page_name>` (e.g. `page_COM-001_overview`, `page_COM-001_detail`)
- Display name: from Business Factsheet or Use Case Inventory
- Theme: reference to applied theme (from Theme Generator or default)

---

### 2. Visual Placeholders

Each **slot** from the use case mapping becomes one or more visual placeholders.

**Visual Type Selection (Slot → Visual):**

> **Reference:** See `core/templates/page_templates/governance/Visual_to_Slot_Mapping.yaml` for complete mapping rules and edge cases.

| Slot | Template | Preferred Visual | Fallback | Notes |
|------|----------|------------------|----------|-------|
| KPI Summary | T1, T2, T3, T4 | KPI Card | — | Always KPI Card |
| Trend | T1, T2, T3 | Line Chart | Area Chart (T1 only) | Show target line if variance slot exists |
| Variance | T1, T2 | Waterfall | Horizontal Bar | Always Waterfall for T2 |
| Ranking | T1, T2, T3 | Horizontal Bar | — | Max 20 items |
| Mix | T1, T2 | 100% Stacked Bar | — | — |
| Exceptions | T3 | Table | — | Exception table format |
| Root Cause | T3, T4 | Scatter Plot (if `needs_root_cause = true`) | Horizontal Bar | Only if slot activated |
| Prescriptive | T4 | Table (recommendation) | — | Action Panel mandatory |
| Funnel | T2 | Funnel Chart | — | Only if `needs_funnel = true` |
| Detail Matrix | All (Detail pages) | Table or Matrix | — | Only on Detail pages |

**Visual Properties (Standard):**

```json
{
  "visualType": "<visual_type>",
  "x": <pixels>,
  "y": <pixels>,
  "width": <pixels>,
  "height": <pixels>,
  "config": {
    "singleVisual": {
      "visualType": "<visual_type>",
      "objects": {
        // Placeholder: will be populated when measures are bound
      }
    }
  }
}
```

**Positioning Rules:**

> **Reference:** See `core/templates/page_templates/governance/Layout_Grid_System.yaml` for complete positioning rules, spacing, and row system.

- **KPI Cards:** Row 1 (y=0-160px), equal width, max 6 per row (wrap to row 2 if needed)
- **Trend/Variance:** Row 2 (y=180-580px), full width (minus slicer column if side slicers)
- **Ranking/Mix:** Row 3 (y=600-900px), half width (or full width if no other visual)
- **Exceptions:** Row 2 (T3), full width
- **Prescriptive:** Row 2 (T4), full width (minus Action Panel), Action Panel right side
- **Detail Matrix:** Row 4+ (y=920px+), full width (Detail pages only)

**Sizing Rules:**

> **Reference:** See `core/templates/page_templates/governance/Layout_Grid_System.yaml` for complete sizing standards.

- KPI Card: 280px width × 140px height (standard), 200px × 120px (compact)
- Trend/Variance: min 800px width × 400px height (standard), 600px × 300px (compact)
- Ranking/Mix: min 400px width × 300px height (standard), 300px × 250px (compact)
- Table/Matrix: full available width × min 300px height
- Action Panel (T4): 350px width × full page height (1080px), right side

**Spacing Rules:**
- Page padding: 20px from all edges
- Gap between visuals: 20px (horizontal and vertical)
- Gap between visual groups: 40px

---

### 3. Slicers

**Default Slicers (per use case requirements):**

- **Time:** Always present (unless use case explicitly excludes it)
  - Type: Slicer (date range or relative date)
  - Default: "Last 12 months" or from Business Factsheet
  - Position: Top row, left side
- **Organization:** If `dim_org` or equivalent exists
  - Type: Slicer (dropdown or list)
  - Position: Top row, after Time
- **Domain-specific:** One additional slicer (e.g. Product, Customer, Region)
  - Type: Slicer (dropdown)
  - Position: Top row, after Organization

**Slicer Properties:**

```json
{
  "visualType": "slicer",
  "x": <pixels>,
  "y": <pixels>,
  "width": 200,
  "height": 50,
  "config": {
    "singleVisual": {
      "visualType": "slicer",
      "objects": {
        "general": {
          "orientation": "vertical" // or "horizontal" for top placement
        }
      }
    }
  }
}
```

**Rules:**
- Max 3 standard slicers (Time, Org, Domain)
- Optional 4th slicer only if mode switch (Scenario, Currency, Version)
- Top placement preferred; side placement allowed if space constrained

---

### 4. Action Panel (T4 or `needs_action_panel = true`)

**Placement:**
- Right side, fixed width 350px
- Collapsible (default: expanded)
- Height: full page height

**Structure:**
- Placeholder visual or custom visual reference
- Will be populated from Action Code data (not generated in scaffold)

**Properties:**

```json
{
  "visualType": "actionPanel", // or custom visual type
  "x": 1570, // right side
  "y": 0,
  "width": 350,
  "height": 1080,
  "config": {
    // Action Panel spec from components/ActionPanel_Spec.md
  }
}
```

---

## Layout Grids (Concrete Examples)

### T2 — Overview Page (COM-001 example)

```
Row 1 (y=0-140):   [KPI Card 1] [KPI Card 2] [KPI Card 3] [KPI Card 4] [Slicers: Time | Org | Product]
Row 2 (y=150-550): [Trend Chart - Full Width]
Row 3 (y=560-960): [Variance Waterfall - Full Width]
Row 4 (y=970-1270): [Ranking Bar Chart - Full Width]
```

**Visuals:**
- 4 KPI Cards: Net Sales Amount, Net Sales % vs Plan, Net Sales % vs LY, Gross Margin %
- Trend: Line chart (Net Sales Amount, Plan, LY)
- Variance: Waterfall (PVM bridge: Plan → Price → Volume → Mix → Actual)
- Ranking: Horizontal bar (Top regions/channels by Net Sales gap)

---

### T4 — Overview Page (with Action Panel)

```
Row 1 (y=0-140):   [KPI Card 1] [KPI Card 2] [Slicers: Time | Org] [Action Panel - Right Side]
Row 2 (y=150-550): [Prescriptive Table - Left 2/3] [Action Panel continues]
Row 3 (y=560-860): [Ranking/Context - Left 2/3] [Action Panel continues]
```

**Visuals:**
- 2 KPI Cards: Context KPIs
- Prescriptive: Recommendation table (Action, Owner, Impact, Priority)
- Ranking: Affected entities
- Action Panel: Right side, full height

---

## Generator Input

**Required:**
- Use case ID (e.g. COM-001)
- Page name (`overview` or `detail`)
- `UseCase_Bracket.yaml` (`ux_layout_rules`) for the use case
- Page template definition (T1/T2/T3/T4 markdown)
- Visual Whitelist rules
- Slot Definitions

**Optional:**
- Theme name (defaults to framework theme)
- Custom layout preferences (overrides defaults)

---

## Generator Output

**PBIP Page JSON** (`.pbir` definition structure):

```json
{
  "version": "1.0",
  "pages": [
    {
      "name": "page_COM-001_overview",
      "displayName": "Sales Performance vs Plan & LY - Overview",
      "displayOption": "FitToPage",
      "height": 1080,
      "width": 1920,
      "visuals": [
        // KPI Cards
        // Trend/Variance/Ranking visuals
        // Slicers
        // Action Panel (if T4)
      ],
      "slicers": [],
      "filters": []
    }
  ]
}
```

**Notes:**
- Visuals are **placeholders** — measure binding happens manually or via a separate step
- Visual types and positions are set; data binding is not
- Theme reference is included but theme application is separate

---

## Validation Rules

Before a scaffold is considered valid:

- [ ] Page name matches pattern `page_<use_case_id>_<page_name>`
- [ ] Template intent matches `UseCase_Bracket.yaml` (`ux_layout_rules`)
- [ ] All mandatory slots have visual placeholders
- [ ] No disallowed visuals are present
- [ ] Slicer count ≤ 3 (or 4 if mode switch)
- [ ] Visual positions don't overlap
- [ ] Action Panel exists if T4 or `needs_action_panel = true`
- [ ] Detail Matrix exists only on Detail pages

---

## Integration with Report Documentation Generator

The scaffold generator should output metadata that the Report Documentation Generator can consume:

- Page name, template type, slots activated
- Visual types and positions (for documentation)
- Slicer types and defaults
- Action Panel presence (for documentation)

This metadata can be stored as a JSON sidecar file or embedded in the PBIP structure.

---

## References

- Page templates: `core/templates/page_templates/page_types/`
- Visual Whitelist: `core/templates/page_templates/governance/Visual_Whitelist.md`
- Slot Definitions: `core/templates/page_templates/governance/Slot_Definitions.md`
- Use case UX SSOT: `core/usecases/core/<ID>_*/UseCase_Bracket.yaml`
- Action Panel Spec: `core/templates/page_templates/components/ActionPanel_Spec.md`
