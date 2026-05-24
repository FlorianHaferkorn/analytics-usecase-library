"""
Generate visual container structures for PBIP (Fabric 3.0).

Uses Master Grid 12×12 with 32px margin, 16px gutter. All visuals aligned to grid.
Two layout modes: render_pulse_investigator() (Top Filter Bar), render_action_matrix() (Left Slicer Pane).
Conditional formatting uses Brand Blue Dark theme colors (good, neutral, bad).
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Allow running as script or from tooling
if __name__ == "__main__":
    import sys
    _parent = Path(__file__).resolve().parent
    # _parent.parent  = tooling/  — needed for `page_scaffold_generator` package
    # _parent.parents[4] = workspace root — needed for `products.*` absolute imports
    if str(_parent.parent) not in sys.path:
        sys.path.insert(0, str(_parent.parent))
    _workspace_root = str(_parent.parents[4])
    if _workspace_root not in sys.path:
        sys.path.insert(0, _workspace_root)

from page_scaffold_generator.grid_calculator import GridCalculator, GridPosition
from page_scaffold_generator.config_loader import ConfigLoader

from products.fabric.powerbi.tooling.schema_registry import VISUAL_SCHEMA

# Semantic color fallbacks (canonical tokens, used when token files are unavailable).
# Source authority: Storytelling_Principles.md §9 · tokens/color_semantics.yaml
_COLOR_DEFAULTS = {
    "good":    "#107C10",  # semantic.positive
    "neutral": "#C98A00",  # semantic.warning
    "bad":     "#A4262C",  # semantic.negative
}

# Framework fallback data palette (used when no brand spec is configured).
_DATA_COLOR_DEFAULTS = [
    "#0078D4", "#50E6FF", "#8661C5", "#F7630C",
    "#008575", "#E3008C", "#EF6950", "#FFB900",
]


def _load_resolved_tokens() -> dict:
    """
    Load fully resolved color tokens via ConfigLoader.resolve_color_tokens().
    Merges framework semantic defaults with active showcase brand overrides.
    Falls back to hardcoded defaults on any error.
    """
    try:
        loader = ConfigLoader()
        return loader.resolve_color_tokens()
    except Exception:
        return {}


_RESOLVED_TOKENS = _load_resolved_tokens()

# Default grid: 1920×1080, 32px margin, 16px gutter
DEFAULT_CANVAS_WIDTH = 1920
DEFAULT_CANVAS_HEIGHT = 1080
DEFAULT_MARGIN = 32
DEFAULT_GUTTER = 16


def _build_visual_container(
    name: str,
    position: GridPosition,
    visual_type: str,
    tab_order: int = 3000,
    z_order: int = 10000,
    query_projections: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Build a single visual container dict compatible with Fabric 3.0 visual.json."""
    return {
        "$schema": VISUAL_SCHEMA,
        "name": name,
        "position": {
            "x": position.x,
            "y": position.y,
            "z": z_order,
            "height": position.height,
            "width": position.width,
            "tabOrder": tab_order,
        },
        "visual": {
            "visualType": visual_type,
            "query": {
                "queryState": {
                    "Data": {
                        "projections": query_projections or []
                    }
                }
            },
            "drillFilterOtherVisuals": True,
        },
    }


def render_pulse_investigator(
    canvas_width: int = DEFAULT_CANVAS_WIDTH,
    canvas_height: int = DEFAULT_CANVAS_HEIGHT,
    outer_margin: int = DEFAULT_MARGIN,
    gutter: int = DEFAULT_GUTTER,
    kpi_slot_count: int = 6,
    has_top_filter_bar: bool = True,
    main_slot_count: int = 3,
) -> List[Dict[str, Any]]:
    """
    Layout with Top Filter Bar: KPI row (row 0-1), then filter/slicer bar (row 2),
    then main area (e.g. 3 large slots for Pulse, or focus + support for Investigator).

    Returns list of visual container dicts for PBIP definition/pages/.../visuals/.
    """
    calc = GridCalculator(
        canvas_width=canvas_width,
        canvas_height=canvas_height,
        outer_margin=outer_margin,
        gutter=gutter,
    )
    visuals: List[Dict[str, Any]] = []
    tab = 3000

    # Row 0-1: 6 KPI slots (each 2 cols × 2 rows)
    for i in range(kpi_slot_count):
        pos = calc.calculate_visual_rect(col_start=i * 2, row_start=0, col_span=2, row_span=2)
        vis = _build_visual_container(f"KPI_{i + 1}", pos, "cardVisual", tab_order=tab + i)
        visuals.append(vis)

    # Row 2: Top filter bar (full width, 1 row)
    if has_top_filter_bar:
        pos = calc.calculate_visual_rect(0, 2, 12, 1)
        vis = _build_visual_container("Slicer_Date", pos, "slicer", tab_order=tab + 10)
        visuals.append(vis)
        row_main_start = 3
    else:
        row_main_start = 2

    # Main body: 3 slots (4 cols × 10 rows each) or 2 slots for Investigator
    rows_main = 12 - row_main_start
    cols_per_slot = 12 // main_slot_count
    for i in range(main_slot_count):
        pos = calc.calculate_visual_rect(
            col_start=i * cols_per_slot,
            row_start=row_main_start,
            col_span=cols_per_slot,
            row_span=rows_main,
        )
        vis = _build_visual_container(f"Main_{i + 1}", pos, "lineChart", tab_order=tab + 20 + i)
        visuals.append(vis)

    return visuals


def render_action_matrix(
    canvas_width: int = DEFAULT_CANVAS_WIDTH,
    canvas_height: int = DEFAULT_CANVAS_HEIGHT,
    outer_margin: int = DEFAULT_MARGIN,
    gutter: int = DEFAULT_GUTTER,
    slicer_pane_cols: int = 2,
) -> List[Dict[str, Any]]:
    """
    Layout with Left Slicer Pane: Col 0-1 = vertical slicers (full height),
    Row 0 = Smart Narrative, Col 2-11 Row 1-11 = Matrix.

    Returns list of visual container dicts for PBIP definition/pages/.../visuals/.
    """
    calc = GridCalculator(
        canvas_width=canvas_width,
        canvas_height=canvas_height,
        outer_margin=outer_margin,
        gutter=gutter,
    )
    visuals: List[Dict[str, Any]] = []
    tab = 3000

    # Left pane: Slicers (Col 0-1, Row 0-11)
    pos_slicer = calc.calculate_visual_rect(0, 0, slicer_pane_cols, 12)
    vis = _build_visual_container("Slicer_Pane", pos_slicer, "slicer", tab_order=tab)
    visuals.append(vis)

    # Row 0 (right side): Smart Narrative (Col 2-11, 1 row)
    pos_narrative = calc.calculate_visual_rect(slicer_pane_cols, 0, 12 - slicer_pane_cols, 1)
    vis = _build_visual_container("Smart_Narrative", pos_narrative, "textbox", tab_order=tab + 1)
    visuals.append(vis)

    # Row 1-11: Matrix (Col 2-11, 11 rows)
    pos_matrix = calc.calculate_visual_rect(slicer_pane_cols, 1, 12 - slicer_pane_cols, 11)
    vis = _build_visual_container("Detail_Matrix", pos_matrix, "tableEx", tab_order=tab + 2)
    visuals.append(vis)

    return visuals


def get_conditional_formatting_colors() -> Dict[str, str]:
    """Return semantic token colors for good/neutral/bad conditional formatting.
    Resolved from tokens/color_semantics.yaml merged with active brand overrides.
    Falls back to canonical hex defaults when token files are unavailable."""
    sem = _RESOLVED_TOKENS.get("semantic", {})
    return {
        "good":    sem.get("positive", _COLOR_DEFAULTS["good"]),
        "neutral": sem.get("warning",  _COLOR_DEFAULTS["neutral"]),
        "bad":     sem.get("negative", _COLOR_DEFAULTS["bad"]),
    }


def get_brand_data_colors() -> List[str]:
    """Return the 8-slot data color palette for the active showcase brand.
    Positions 0-1 are brand primary/secondary; positions 2-7 are framework defaults.
    Falls back to framework palette when no brand is configured."""
    brand = _RESOLVED_TOKENS.get("brand", {})
    data_colors = brand.get("data_colors")
    if isinstance(data_colors, list) and data_colors:
        return list(data_colors)
    return list(_DATA_COLOR_DEFAULTS)


def main() -> int:
    """CLI: generate and optionally write visual containers to a report path."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Generate PBIP visual containers from grid layouts.")
    parser.add_argument("--layout", choices=["pulse_investigator", "action_matrix"], default="pulse_investigator")
    parser.add_argument("--output", type=Path, help="Write visuals as JSON array to this file.")
    parser.add_argument("--canvas-width", type=int, default=DEFAULT_CANVAS_WIDTH)
    parser.add_argument("--canvas-height", type=int, default=DEFAULT_CANVAS_HEIGHT)
    parser.add_argument("--margin", type=int, default=DEFAULT_MARGIN)
    parser.add_argument("--gutter", type=int, default=DEFAULT_GUTTER)
    args = parser.parse_args()

    if args.layout == "pulse_investigator":
        visuals = render_pulse_investigator(
            canvas_width=args.canvas_width,
            canvas_height=args.canvas_height,
            outer_margin=args.margin,
            gutter=args.gutter,
        )
    else:
        visuals = render_action_matrix(
            canvas_width=args.canvas_width,
            canvas_height=args.canvas_height,
            outer_margin=args.margin,
            gutter=args.gutter,
        )

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(visuals, f, indent=2, ensure_ascii=False)
        print(f"Wrote {len(visuals)} visuals to {args.output}")
    else:
        print(json.dumps(visuals, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
