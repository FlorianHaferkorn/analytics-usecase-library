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
    _parent = Path(__file__).resolve().parent
    if str(_parent.parent) not in __import__("sys").path:
        __import__("sys").path.insert(0, str(_parent.parent))

from page_scaffold_generator.grid_calculator import GridCalculator, GridPosition

# Brand Blue Dark (Monochromatic) - for conditional formatting
BRAND_BLUE_DARK_GOOD = "#519872"
BRAND_BLUE_DARK_NEUTRAL = "#F6AE2D"
BRAND_BLUE_DARK_BAD = "#EC4E20"

VISUAL_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.3.0/schema.json"

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
            "objects": {},
            "drillFilterOtherVisuals": True,
        },
        "visualContainerObjects": {
            "visualHeader": [{"properties": {"showTooltipButton": {"expr": {"Literal": {"Value": "true"}}}}}]
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
    """Return Brand Blue Dark colors for good/neutral/bad (bedingte Formatierung)."""
    return {
        "good": BRAND_BLUE_DARK_GOOD,
        "neutral": BRAND_BLUE_DARK_NEUTRAL,
        "bad": BRAND_BLUE_DARK_BAD,
    }


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
