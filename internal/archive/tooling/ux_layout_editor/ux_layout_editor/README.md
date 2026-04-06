# UX Layout Editor

Rule-based draft of `ux_layout_rules` and a small editor to choose visual types per slot without editing YAML by hand.

## Quick start

1. **Draft only (stdout):**
   ```powershell
   py -3 tooling/ux_layout_editor/draft_ux_layout.py --use-case COM-001
   ```

2. **Draft and apply to UseCase_Bracket.yaml:**
   ```powershell
   py -3 tooling/ux_layout_editor/draft_ux_layout.py --use-case COM-001 --apply
   ```
   Validation runs before writing; on failure the file is not changed.

3. **Layout editor (Streamlit):**
   ```powershell
   pip install -r tooling/ux_layout_editor/requirements.txt
   streamlit run tooling/ux_layout_editor/app.py
   ```
   In the sidebar: set repo root, select use case. Edit visual types via dropdowns (only allowed types per slot). **Live Preview** below shows the chosen chart types (line, bar, waterfall, etc.) with sample data. Click **Save** to write back to `UseCase_Bracket.yaml` (validator runs first).

## Config

- `config/slot_order_by_report.yaml` — which semantic slot each `component_30s` position has (e.g. 2-Page-Lead: Trend, Variance).
- `config/slot_to_visual_allowed.yaml` — per-slot allowed `visual_type` values and default (used for validation and dropdowns).

## Live Preview

Under the dropdowns the editor shows a **Live Preview** with real chart types (Line, Bar, Waterfall, Stacked Bar, Funnel) and sample data. No separate HTML file; preview updates as you change visual types.

## Validation

- **Draft (--apply):** `validator.validate_ux_layout_rules` runs before writing.
- **Streamlit Save:** Same validator; on success the bracket file is updated.
- Stage 1 does not yet run this validator; you can add an optional check that calls `validate_ux_layout_rules` for each use case bracket if desired.
