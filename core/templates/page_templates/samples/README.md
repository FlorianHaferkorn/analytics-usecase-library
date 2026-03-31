# 3-30-300 Layout Samples

Annotated wireframes and samples for each layer of the 3-30-300 design model.

These samples are **design references**, not generated artifacts. They show what each layer looks like, what content goes where, and how components relate.

---

## Files

| File | What it shows |
|---|---|
| `layer_3s_kpi_band.md` | 3-second layer — KPI card band with signal logic and variants |
| `layer_30s_diagnostics.md` | 30-second layer — Trend, Variance, Ranking slots with data samples |
| `layer_300s_detail.md` | 300-second layer — Smart Narrative, Detail Matrix, Action Panel |
| `page_pulse_full.md` | Complete Overview page (3s + 30s combined) — "The Pulse" |
| `page_action_matrix_full.md` | Complete Detail page (300s) — "The Action Matrix" (with and without T4) |
| `page_investigator_full.md` | Alternative Overview — "The Investigator" (focus layout) |

---

## How to Read the Wireframes

```
┌──────────────────────┐
│ SLOT_ID              │  ← Named slot (maps to UseCase_Bracket.yaml)
│ Visual type          │
│                      │
│ [Actual content]     │  ← Representative sample data
│                      │
└──────────────────────┘
```

- Grid positions are annotated as `[col, row, col_span, row_span]` in LU (logical units)
- Signal colors are shown as text: `[GREEN]`, `[RED]`, `[AMBER]`, `[GREY]`
- Font roles are annotated: `← kpi_value`, `← chart_title`, etc.

---

## Reference

Full design spec: `core/templates/page_templates/layout_330300_design_spec.md`
