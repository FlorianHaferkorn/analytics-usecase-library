"""
Apply page layout (positions only) to an existing PBIP from a grid blueprint.

Reads definition/pages/<PageId>/page.json and visuals/*/visual.json; updates position
from a grid template (and optional canvas size). Does not create or remove visuals;
slot_id in blueprint must match visual name where applicable.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import argparse
import json
import sys

# Allow running as script
if __name__ == "__main__":
    _parent = Path(__file__).resolve().parent
    if str(_parent.parent) not in sys.path:
        sys.path.insert(0, str(_parent.parent))

from page_scaffold_generator.grid_calculator import GridCalculator


def load_blueprint(path: Path) -> Dict[str, Any]:
    """Load grid template JSON."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def apply_layout_to_page(
    definition_pages_path: Path,
    page_id: str,
    blueprint: Dict[str, Any],
    canvas_width: Optional[int] = None,
    canvas_height: Optional[int] = None,
    outer_margin: int = 32,
    gutter: int = 16,
) -> int:
    """
    Update position in each visual under definition_pages_path/page_id/visuals/
    to match blueprint slots (by visual name = slot_id). Optionally update page.json width/height.

    Returns number of visuals updated.
    """
    canvas = blueprint.get("canvas") or {}
    w = canvas_width or canvas.get("width") or 1920
    h = canvas_height or canvas.get("height") or 1080
    calc = GridCalculator(canvas_width=w, canvas_height=h, outer_margin=outer_margin, gutter=gutter)

    page_dir = definition_pages_path / page_id
    if not page_dir.is_dir():
        return 0

    slots_list = blueprint.get("slots") or []
    slot_positions: Dict[str, Dict[str, float]] = {}
    for slot_def in slots_list:
        slot_id = slot_def.get("slot_id")
        grid = slot_def.get("grid")
        if not slot_id or not grid or len(grid) != 4:
            continue
        pos = calc.calculate_visual_rect(grid[0], grid[1], grid[2], grid[3])
        slot_positions[slot_id] = {"x": pos.x, "y": pos.y, "width": pos.width, "height": pos.height}

    # Update page.json
    page_json = page_dir / "page.json"
    if page_json.exists():
        with open(page_json, "r", encoding="utf-8") as f:
            page_data = json.load(f)
        page_data["width"] = w
        page_data["height"] = h
        with open(page_json, "w", encoding="utf-8") as f:
            json.dump(page_data, f, indent=2, ensure_ascii=False)

    # Update each visual that matches a slot
    visuals_dir = page_dir / "visuals"
    updated = 0
    if not visuals_dir.is_dir():
        return 0
    for vis_dir in visuals_dir.iterdir():
        if not vis_dir.is_dir():
            continue
        visual_file = vis_dir / "visual.json"
        if not visual_file.exists():
            continue
        name = vis_dir.name
        if name not in slot_positions:
            continue
        with open(visual_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        pos = slot_positions[name]
        if "position" not in data:
            data["position"] = {}
        data["position"]["x"] = pos["x"]
        data["position"]["y"] = pos["y"]
        data["position"]["width"] = pos["width"]
        data["position"]["height"] = pos["height"]
        with open(visual_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        updated += 1
    return updated


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply grid layout (positions) to existing PBIP page.")
    parser.add_argument("--definition", type=Path, required=True, help="Path to report definition folder (e.g. .../Report/definition)")
    parser.add_argument("--page-id", type=str, required=True, help="Page folder name (e.g. Page_COM001_Overview)")
    parser.add_argument("--blueprint", type=Path, required=True, help="Path to grid template JSON (e.g. pulse.json)")
    parser.add_argument("--canvas-width", type=int, default=None)
    parser.add_argument("--canvas-height", type=int, default=None)
    parser.add_argument("--margin", type=int, default=32)
    parser.add_argument("--gutter", type=int, default=16)
    args = parser.parse_args()

    pages_path = args.definition / "pages"
    if not pages_path.is_dir():
        print(f"Error: not a definition folder (no pages): {args.definition}", file=sys.stderr)
        return 1
    blueprint = load_blueprint(args.blueprint)
    n = apply_layout_to_page(
        pages_path,
        args.page_id,
        blueprint,
        canvas_width=args.canvas_width,
        canvas_height=args.canvas_height,
        outer_margin=args.margin,
        gutter=args.gutter,
    )
    print(f"Updated {n} visual positions and page.json for {args.page_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
