# Connector Specification — 3-30-300 Framework

> **Authority:** This document defines the **contract** that any tool-specific connector must fulfill to implement the 3-30-300 page template framework.
>
> **Governs:** All connector implementations under `products/*/` and `core/templates/page_templates/connectors/`.
>
> **Abstract spec:** `layout_330300_design_spec.md` · `Abstract_Visual_Types.md`

---

## 1. What a Connector Is

A **connector** is a tool-specific implementation layer that translates the abstract 3-30-300 page specification into the native objects, formats, and APIs of a specific BI or visualization tool.

The abstract spec defines **what** to show and **where** (slots, zones, grid coordinates, color semantics, visual types). A connector defines **how** to represent that in a given tool.

```
Abstract Spec (tool-agnostic)
  └── Connector (tool-specific translation layer)
        └── Tool-native output (report, dashboard, notebook)
```

Connectors are independently versioned and maintained. Changes to the abstract spec require a connector update only if the abstract contract changes — not for every tooling release.

---

## 2. What the Abstract Spec Provides to Connectors

Every connector receives the following from the abstract spec:

### 2.1 Slot IDs and Semantics

Slots are named positions on a page with a fixed semantic purpose. They do not prescribe a specific visual — they prescribe what analytical question the visual must answer.

| Slot ID | Zone | Semantic Purpose |
|---|---|---|
| `KPI_Cards` | 1 (3s) | Status signal — KPI value + delta + reference |
| `Slicer_Date` | 2 (filter) | Temporal context filter |
| `Slicer_Cat_1/2` | 2 (filter) | Categorical context filters (optional) |
| `Main_1` | 3 (30s) | Trend — time development of KPI |
| `Main_2` | 3 (30s) | Variance — deviation from reference |
| `Main_3` | 3 (30s) | Ranking / Mix — entity comparison or composition |
| `Slicer_Pane` | 4 (300s) | Context switch — all detail-page filters |
| `Smart_Narrative` | 4 (300s) | Summary text — current filter context |
| `Detail_Matrix` | 4 (300s) | Entity-grain detail table with delta columns |
| `ActionPanel` | 4 (300s, T4) | Recommendation — action, owner, impact |
| `Focus_Area` | Investigator | Dominant analysis visual (alternative overview) |
| `Support_1/2` | Investigator | Supporting context visuals |

Full semantics: `governance/Slot_Definitions.md`

### 2.2 Grid Coordinates (12×12 LU System)

Grid positions use logical units (LU) on a 12-column × 12-row grid. Connectors translate LU to native pixel or % coordinates using the formulas in `governance/Layout_Grid_System.yaml §Master Grid`.

Standard grid positions per layout template: `grid_templates/pulse.json`, `action_matrix.json`, `investigator.json`.

### 2.3 Color Semantic Roles

| Abstract Role | Meaning | Default (light theme) |
|---|---|---|
| `semantic.positive` | Favourable delta | Green (accessible) |
| `semantic.negative` | Unfavourable delta, alert | Red |
| `semantic.warning` | Near threshold | Amber / Orange |
| `semantic.neutral` | No signal, informational | Gray |
| `brand.primary` | First data series | Brand color 1 |
| `brand.secondary` | Second data series | Brand color 2 |
| `brand.data_colors[0–7]` | Categorical series | Palette array |

Connectors must map these roles to their tool's theming system. Colors must never be hard-coded.

### 2.4 Abstract Visual Type Vocabulary

All visual types in this spec use abstract identifiers from `Abstract_Visual_Types.md`. Connectors map abstract types to tool-native components. See §3 of this document.

### 2.5 Interaction Patterns

| Pattern | Abstract Definition |
|---|---|
| `drillthrough` | Navigation from overview page to detail page, passing filter context |
| `slicer_cascade` | All slicers on a page filter all visuals on that page |
| `tooltip_on_hover` | Show metric name, value, reference, delta, and period on data point hover |
| `cross_filter` | Optional — visual selection filters other visuals (connector may enable/disable) |

---

## 3. Connector Mandatory Implementations

A connector implementation is **compliant** only when all items below are satisfied.

### 3.1 Slot Coverage

| Requirement | Rule |
|---|---|
| All mandatory slots implemented | `KPI_Cards`, `Slicer_Date`, at least one `Main_*` slot on overview; `Slicer_Pane`, `Smart_Narrative`, `Detail_Matrix` on detail page |
| Optional slots handled | If `UseCase_Bracket.yaml` activates an optional slot, the connector must render it |
| Slot positions within 5% of LU grid | Pixel placement may deviate ≤5% from computed grid position |
| No additional slots introduced | Connectors may not add undeclared slots |

### 3.2 Color Semantics

| Requirement | Rule |
|---|---|
| All 4 semantic roles implemented | `positive`, `negative`, `warning`, `neutral` must be distinct and consistent |
| No hard-coded colors | All colors via tool's theme/token system |
| WCAG AA contrast | Minimum 4.5:1 for text on all semantic colors; 3:1 for large text |
| Colorblind safety | Semantic signals always paired with icon or shape (never color alone) |

### 3.3 Visual Type Coverage

At minimum, the connector must support the following abstract types:

| Abstract Type | Required For |
|---|---|
| `kpi_card` | All templates (3s layer) |
| `line_chart` | Trend slot (T1, T2, T3) |
| `bar_chart_horizontal` | Ranking slot (T1, T2, T3) |
| `waterfall` | Variance slot (T2) |
| `stacked_bar_100pct` | Mix slot (T1, T2) |
| `table_with_databars` | Detail Matrix (all, 300s only) |
| `slicer_dropdown` | Slicer slots (all) |
| `text_narrative` | Smart Narrative slot |
| `action_card` | Action Panel (T4) |

Full mapping: `Abstract_Visual_Types.md`

### 3.4 Framework Hard Limits

Connectors must enforce or validate these limits:

| Rule | Limit |
|---|---|
| Visible visuals per page | ≤ 20 |
| Data fields per visual | ≤ 6 |
| Slicers per page | ≤ 3 (+ optional 4th as mode switch) |
| Page height | No vertical scroll |
| Hard-coded colors | 0 |
| Pie/donut charts | 0 |

### 3.5 Drillthrough / Navigation

| Requirement | Rule |
|---|---|
| Overview → Detail navigation | Must pass filter context (at minimum: date range + entity selection) |
| Direct Detail access | Detail page must be accessible as standalone (not only via drillthrough) |
| Back navigation | Detail page provides a "back to overview" control |

### 3.6 Accessibility

| Requirement | Rule |
|---|---|
| Alt text / title | Every visual has a descriptive title (used as accessibility label) |
| Focus order | KPI band → primary visuals → slicers → action panel |
| WCAG AA | Minimum 4.5:1 contrast for all text; 3:1 for large text (≥18pt or ≥14pt bold) |

---

## 4. Connector Output Format

Each connector must produce:

1. **Layout file** — positions of all visuals in tool-native format (e.g., JSON, YAML, Python dict)
2. **Theme/token file** — color role mappings to tool's theming system
3. **Interaction config** — drillthrough, slicer cascade, cross-filter settings
4. **Compliance report** — output of the compliance checklist (§5) as machine-readable result

---

## 5. Connector Compliance Checklist

Run this checklist before a connector implementation is considered production-ready.

### Slot Coverage
- [ ] All mandatory slots implemented and positioned within 5% of LU grid
- [ ] Optional slots handled per `UseCase_Bracket.yaml` activation

### Visual Types
- [ ] All required abstract visual types mapped to tool-native components
- [ ] No disallowed visual types used (pie/donut, gauge, radar)

### Color Semantics
- [ ] All 4 semantic roles (`positive`, `negative`, `warning`, `neutral`) implemented
- [ ] No hard-coded colors — all via theme/token system
- [ ] WCAG AA contrast verified on all semantic colors
- [ ] Colorblind safety: icon+color pairing on all signal elements

### Framework Hard Limits
- [ ] Visible visuals per page ≤ 20
- [ ] Data fields per visual ≤ 6
- [ ] Slicers per page ≤ 3 (+ optional 4th mode switch)
- [ ] No vertical scroll on any page
- [ ] Pie/donut charts = 0

### Navigation and Interaction
- [ ] Drillthrough passes filter context (date + entity)
- [ ] Direct Detail page access works without drillthrough
- [ ] Back navigation exists on Detail page

### Accessibility
- [ ] Every visual has a descriptive title
- [ ] Focus order correct (KPI band → visuals → slicers → action)
- [ ] WCAG AA contrast verified

### Content Quality
- [ ] Visual titles are question- or conclusion-form (per `Content_Quality_Guide.md §1`)
- [ ] KPI labels meet label standards (per `Content_Quality_Guide.md §2`)
- [ ] Smart Narrative is populated per template (per `Content_Quality_Guide.md §4`)
- [ ] Action Panel (if T4) has all mandatory fields (per `Content_Quality_Guide.md §6`)

---

## 6. Known Connectors

| Connector | Location | Status |
|---|---|---|
| Power BI / Fabric | `connectors/PowerBI_Connector.md` + `products/fabric/powerbi/` | Active — v2.0.1 |
| OSS Stack (Superset, Grafana, Metabase) | `connectors/OSS_Connector_Guide.md` | Reference sketch |

To register a new connector, add it to this table and create a corresponding document in `connectors/<tool>_Connector.md`.

---

## 7. Connector Versioning

Connectors are versioned independently from the abstract spec. A connector version is `<abstract_spec_version>.<connector_version>` (e.g., `1.2.3` = abstract spec 1.2, connector revision 3).

When the abstract spec changes:
- Breaking changes (new mandatory slot, changed color role) → increment connector major version
- Additive changes (new optional slot, new abstract visual type) → increment minor version
- Connector-internal changes (theme update, performance fix) → increment patch version
