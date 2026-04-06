# ARCHIVED — layout_330300_300s_layer.md

**Archived:** 2026-04-05  
**Reason:** Content superseded by `Design_Spec_3_30_300.md §5.4` (Zone 4 — 300-Second Layer) and enriched samples in `samples/`. Schema authority unchanged — see `tooling/ai/schemas/layout_330300.schema.json`.  
**Do not delete:** File kept for git history reference only.

---

<!-- original content below -->

# 300-Second Layer (layout_330300)

**Purpose:** Defines the structure of the **300-second (diagnostics)** layer for 3-30-300 page layouts. This is the formal definition referenced by `layout_330300` in Use Case brackets and by the page scaffold generator. Schema: [tooling/ai/schemas/layout_330300.schema.json](../../../../tooling/ai/schemas/layout_330300.schema.json).

---

## Role in 3-30-300

- **3 seconds:** KPI cards (headline metrics) — defined by `kpi_cards` in the schema.
- **30 seconds:** Main visuals (drivers, variance, rankings) — defined by `visuals_30s`.
- **300 seconds:** Diagnostics (drill-down, evidence table, action context) — defined by `diagnostics_300s` and optionally the Action Panel.

The 300s layer is the **detail** page or the **diagnostics** section of a combined page. It answers "Why?" and "What should we do?" with tables, breakdowns, and action text/evidence sourced from action-code YAML.

---

## Schema: diagnostics_300s

Each item in `diagnostics_300s` has:

| Field | Type | Meaning |
|-------|------|---------|
| `name` | string | Display name of the visual/section. |
| `visual_type` | string | Allowed type (e.g. `table`, `matrix`, `detail_table`). |
| `columns` | array (optional) | Column names for tables. |
| `sort_by` | string (optional) | Default sort column. |
| `limit` | integer (optional) | Row limit for performance. |

Use cases may extend this with **action text** and **evidence table** blocks that are generated from action-code YAML (action payload, evidence grain). Those are defined in the bracket and in the Action Panel spec; the layout schema defines the structural slots.

---

## Slicers and tooltips

- **slicers:** Same as for 3s/30s; applied to 300s visuals so drill-down stays consistent.
- **tooltips:** Optional extra fields for hover on 300s tables/matrices.

---

## Relationship to Use Case Bracket

Per-use-case layout (including 300s structure) is stored in `UseCase_Bracket.yaml` under the key used by the page scaffold (e.g. `layout_330300`). This document and the JSON schema are the **canonical shape** for that key. Generators (e.g. page scaffold, report documentation) must conform to [layout_330300.schema.json](../../../../tooling/ai/schemas/layout_330300.schema.json).
