# 300-Second Layer (layout_330300)

**Purpose:** Defines the structure of the **300-second (diagnostics + action)** layer for 3-30-300 page layouts. This is the formal definition referenced by `layout_330300` in Use Case brackets and by the page scaffold generator. Schema: [tooling/ai/schemas/layout_330300.schema.json](../../../../tooling/ai/schemas/layout_330300.schema.json).

---

## Role in 3-30-300

- **3 seconds:** KPI cards (headline metrics) — defined by `kpi_cards` in the schema.
- **30 seconds:** Main visuals (drivers, variance, rankings) — defined by `visuals_30s`.
- **300 seconds:** Diagnostics (drill-down, evidence table, action context) — defined by `diagnostics_300s`, `evidence_table`, and optionally `action_panel`.

The 300s layer is the **detail** page. It answers "Why?" and "What should we do?" with tables, breakdowns, and action text/evidence sourced from action-code YAML.

---

## Visual Slots on the 300s (Detail) Page

| Slot | Visual | Always | Notes |
|---|---|---|---|
| **Slicer_Pane** | Slicer | ✓ | Time / context switch; synced with overview |
| **Smart_Narrative** | textbox/Smart Narrative | ✓ | One-sentence state summary for current filter |
| **Detail_Matrix** | tableEx / pivotTable | ✓ | Operative drill-down; columns from `evidence_table.columns` |
| **ActionPanel** | textbox (Phase 1) | T4 only | Prescribed actions from `action_panel.action_code_ids` |

---

## Schema: diagnostics_300s

Each item in `diagnostics_300s` has:

| Field | Type | Meaning |
|-------|------|---------|
| `name` | string | Display name of the visual/section. |
| `visual_type` | string | Allowed type: `table`, `matrix`, `detail_table`. |
| `columns` | array (optional) | Column names for tables. |
| `sort_by` | string (optional) | Default sort column. |
| `limit` | integer (optional) | Row limit for performance (max 10 000). |

---

## Schema: evidence_table

Structured config for the **Detail_Matrix** visual slot. Generated at scaffold time from `UseCase_Bracket.yaml › ux_layout_rules.page_2_execution.component_300s`.

```yaml
evidence_table:
  grain: invoice_line        # Row grain (entity key)
  columns:
    - entity                 # Dimension key(s) first
    - period
    - margin.gm.pct          # KPI IDs; mapped to measure names at build time
  measures:
    - Gross Margin %         # Resolved measure names from semantic model
  sort_by: margin.gm.pct
  limit: 500
  data_bars: true            # Show data bars on variance columns
```

**Column resolution:** KPI IDs in `columns` are resolved to semantic model measure names via the KPI catalog (`kpi_key` or `technical.dax_name`). The scaffold generator performs this mapping automatically.

**Grain principle:** The grain must match the evidence grain in the data contract (`overrides.data_contract_ref`). Mismatched grain causes incorrect aggregation in the Detail_Matrix.

---

## Schema: action_panel

Configuration for the **ActionPanel** visual slot (T4 pages only).

```yaml
action_panel:
  enabled: true
  action_code_ids:           # From orchestration.action_code_ids in UseCase_Bracket
    - C-M2.1
    - C-S1.1
  payload_mode: full         # full | summary | minimal
  title: "Recommended actions (from action codes)"
```

### payload_mode options

| Mode | Content shown |
|---|---|
| `full` | Name, owner, trigger condition, impact summary, first 3 steps |
| `summary` | Name, owner, trigger condition, impact summary |
| `minimal` | Name, owner only |

### Phase 1 vs Phase 2

**Phase 1 (current):** The panel renders as a textbox visual with content built **at scaffold time** from action-code YAML. Content is static in the PBIP file. No execution from the report.

**Phase 2 (future):** Panel driven from a semantic model table (e.g. `ActionRecommendation`) populated by a trigger-evaluation pipeline. Field: `action_panel.phase2_table: "ActionRecommendation"`. See [ActionPanel_Spec.md](../components/ActionPanel_Spec.md).

---

## Relationship to UseCase_Bracket.yaml

The bracket's `ux_layout_rules.page_2_execution.component_300s` maps directly to these schema fields:

| Bracket field | Schema field |
|---|---|
| `component_300s.evidence_grain` | `evidence_table.grain` |
| `component_300s.evidence_columns` | `evidence_table.columns` |
| `component_300s.action_panel` | `action_panel.enabled` |
| `component_300s.payload_mode` | `action_panel.payload_mode` |
| `orchestration.action_code_ids` | `action_panel.action_code_ids` |

Generators (page scaffold, report documentation) must conform to [layout_330300.schema.json](../../../../tooling/ai/schemas/layout_330300.schema.json).

---

## Slicers and Drillthrough

- **slicers:** Applied to 300s visuals so drill-down stays consistent with the overview context.
- **Drillthrough:** The detail page is configured as a drillthrough target (`type: "Drillthrough"` in page.json) so users can right-click any overview visual and navigate directly to the filtered detail.

---

## Standalone CLI: generate_action_payload.py

For agents and pipelines that need to regenerate the ActionPanel content independently of the full scaffold generator:

```bash
python products/fabric/powerbi/tooling/generate_action_payload.py \
  --use-case COM-001 \
  --mode full \
  [--repo-root .]
```

Outputs the formatted action panel text to stdout. Pipe into a script to update an existing `ActionPanel/visual.json`.
