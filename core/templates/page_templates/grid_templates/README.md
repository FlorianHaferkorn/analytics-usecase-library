# Grid Page Templates (Master Grid 12×12)

Page templates for the PBIP Builder Engine. Each template defines a **template_id**, optional **canvas** defaults, and **slots** with grid coordinates in logical units (LU).

- **Grid:** 12 columns × 12 rows.
- **Coordinates:** `grid: [col_start, row_start, col_span, row_span]` (0-based).
- **Spacing:** Defined at render time (e.g. 32px margin, 16px gutter); see `grid_calculator.py` and `generate_visual_containers.py`.

## Templates

| File | template_id | Use |
|------|-------------|-----|
| pulse.json | pulse | Monitoring (3s): 6 KPI slots, top filter bar, 3 main slots. |
| investigator.json | investigator | Analysis (30s): left slicer pane, focus area, 2 support visuals. |
| action_matrix.json | action_matrix | Detail (300s): left slicer pane, smart narrative row, matrix. |

## Slot IDs

Stable identifiers for placement. Examples: `KPI_1` … `KPI_6`, `Main_1`, `Main_2`, `Main_3`, `Slicer_Date`, `Slicer_Pane`, `Focus_Area`, `Support_1`, `Support_2`, `Smart_Narrative`, `Detail_Matrix`.

Slots reference **visual templates** (see `../visual_templates/`) for the actual Power BI visual type and optional `action_logic`.

## Annotation (optional — the IBCS commentary layer)

A template MAY declare an optional top-level `annotation` object reserving a **narrative commentary
region** for the page's so-what message — the management commentary that IBCS reports and tools like
Zebra BI / Inforiver ship as a first-class layer. It is a *semantic* declaration (no fixed geometry, so
it never collides with `slots`); the renderer places it per `placement`.

```json
"annotation": {
  "role": "commentary",
  "placement": "footer",          // footer | header | rail
  "content_hint": "IBCS management commentary: the page's so-what (AC vs PL/PY drivers + the action)",
  "max_chars": 280
}
```

Validated by `tooling/visual_library/tests/test_annotation.py`. It is optional — a template with no
`annotation` key simply has no reserved commentary region.
