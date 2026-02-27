"""
Report Sync (Delta Update)

Builds desired state from Bracket/Templates, computes diff against existing PBIP (Ist),
and applies only add/remove/update_position actions. Used when report already exists.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import shutil

from .pbip_reader import read_pbip
from .pbip_writer import PBIPWriter
from .scaffold_generator import PageScaffoldGenerator
from .apply_page_layout import apply_layout_to_page


# Action types for diff/apply
ADD_PAGE = "add_page"
ADD_VISUAL = "add_visual"
REMOVE_VISUAL = "remove_visual"
UPDATE_POSITION = "update_position"


def build_desired_state(
    use_case_id: str,
    repo_root: Path,
) -> List[Dict[str, Any]]:
    """
    Build desired state for overview + detail pages (in-memory, no write).
    Returns list of dicts per page: page_id, visual_names, metadata, visuals, slicers, grid_blueprint, report_canvas.
    """
    desired_pages: List[Dict[str, Any]] = []
    for page_name in ("overview", "detail"):
        gen = PageScaffoldGenerator(
            use_case_id=use_case_id,
            page_name=page_name,
            repo_root=repo_root,
        )
        gen.load_config()
        gen.generate()
        structure = gen.get_page_structure()
        visuals = structure.get("visuals") or []
        slicers = structure.get("slicers") or []
        visual_names = [v.get("name") for v in visuals if v.get("name")]
        visual_names.extend(s.get("name") for s in slicers if s.get("name"))
        page_config = gen.page_config or {}
        grid_blueprint = page_config.get("grid_blueprint")
        report_canvas = page_config.get("report_canvas")
        desired_pages.append({
            "page_id": gen.page_id,
            "visual_names": visual_names,
            "metadata": structure.get("metadata"),
            "visuals": visuals,
            "slicers": slicers,
            "grid_blueprint": grid_blueprint,
            "report_canvas": report_canvas,
        })
    return desired_pages


def compute_diff(
    current: Dict[str, Any],
    desired_pages: List[Dict[str, Any]],
) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Compute list of (action_type, params) from current (Ist) vs desired.
    Only the two Bracket pages (Overview, Detail) are diffed; other pages in current are left untouched.
    """
    actions: List[Tuple[str, Dict[str, Any]]] = []
    current_pages = current.get("pages") or {}
    current_order = current.get("page_order") or []
    desired_page_ids = [p["page_id"] for p in desired_pages]
    desired_by_id = {p["page_id"]: p for p in desired_pages}

    for desired in desired_pages:
        page_id = desired["page_id"]
        desired_visuals = set(desired["visual_names"])
        current_page = current_pages.get(page_id) or {}
        current_visuals = set(current_page.get("visual_names") or [])

        if page_id not in current_order:
            actions.append((ADD_PAGE, {"page_id": page_id, "desired": desired}))
            continue

        to_add = desired_visuals - current_visuals
        to_remove = current_visuals - desired_visuals
        to_update_position = desired_visuals & current_visuals

        for name in to_add:
            actions.append((ADD_VISUAL, {"page_id": page_id, "visual_name": name, "desired_page": desired}))
        for name in to_remove:
            actions.append((REMOVE_VISUAL, {"page_id": page_id, "visual_name": name}))
        if to_update_position and (desired.get("grid_blueprint") or desired.get("report_canvas")):
            actions.append((UPDATE_POSITION, {
                "page_id": page_id,
                "grid_blueprint": desired.get("grid_blueprint"),
                "report_canvas": desired.get("report_canvas"),
            }))
    return actions


def _get_visual_data_by_name(desired_page: Dict[str, Any], visual_name: str) -> Optional[Dict[str, Any]]:
    for v in desired_page.get("visuals") or []:
        if v.get("name") == visual_name:
            return v
    for s in desired_page.get("slicers") or []:
        if s.get("name") == visual_name:
            return s
    return None


def apply_actions(
    output_path: Path,
    actions: List[Tuple[str, Dict[str, Any]]],
    definition_pages_path: Path,
) -> None:
    """
    Execute add_page, add_visual, remove_visual, update_position.
    Does not write report.json or version.json (update mode preserves them).
    """
    writer = PBIPWriter(output_path)
    writer.create_pbip_structure()

    for action_type, params in actions:
        if action_type == ADD_PAGE:
            desired = params["desired"]
            page_id = desired["page_id"]
            writer.write_page_json(page_id, desired["metadata"])
            for v in desired.get("visuals") or []:
                writer.write_visual_json(page_id, v)
            for s in desired.get("slicers") or []:
                writer.write_visual_json(page_id, s)
            writer.write_pages_json(page_ids=[page_id], append=True)
        elif action_type == ADD_VISUAL:
            page_id = params["page_id"]
            visual_name = params["visual_name"]
            desired_page = params.get("desired_page")
            if not desired_page:
                continue
            visual_data = _get_visual_data_by_name(desired_page, visual_name)
            if visual_data:
                writer.write_visual_json(page_id, visual_data)
        elif action_type == REMOVE_VISUAL:
            page_id = params["page_id"]
            visual_name = params["visual_name"]
            visual_dir = definition_pages_path / page_id / "visuals" / visual_name
            if visual_dir.exists() and visual_dir.is_dir():
                shutil.rmtree(visual_dir)
        elif action_type == UPDATE_POSITION:
            page_id = params["page_id"]
            grid_blueprint = params.get("grid_blueprint")
            report_canvas = params.get("report_canvas")
            if not grid_blueprint:
                continue
            canvas_w = canvas_h = None
            if isinstance(report_canvas, dict):
                canvas_w = report_canvas.get("width")
                canvas_h = report_canvas.get("height")
            apply_layout_to_page(
                definition_pages_path,
                page_id,
                grid_blueprint,
                canvas_width=canvas_w,
                canvas_height=canvas_h,
            )


def sync_report(
    use_case_id: str,
    output_path: Path,
    repo_root: Path,
) -> bool:
    """
    Run delta update: read current, build desired, diff, apply.
    Does not touch report.json or version.json.
    Returns True if sync was applied, False if nothing to do (e.g. current is None).
    """
    current = read_pbip(output_path)
    if current is None:
        return False
    desired_pages = build_desired_state(use_case_id, repo_root)
    actions = compute_diff(current, desired_pages)
    if not actions:
        return True
    definition_pages_path = current.get("pages_path")
    if not definition_pages_path or not Path(definition_pages_path).exists():
        return False
    apply_actions(output_path, actions, Path(definition_pages_path))
    return True
