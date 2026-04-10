"""
Report Sync (Delta Update)

Builds desired state from Bracket/Templates, computes diff against existing PBIP (Ist),
and applies add/remove/update actions for visuals plus layout updates. Used when report already exists.
"""

import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .pbip_reader import read_pbip
from .pbip_writer import PBIPWriter
from .scaffold_generator import PageScaffoldGenerator
from .apply_page_layout import apply_layout_to_page


# Action types for diff/apply
ADD_PAGE = "add_page"
ADD_VISUAL = "add_visual"
REMOVE_VISUAL = "remove_visual"
UPDATE_VISUAL = "update_visual"
UPDATE_POSITION = "update_position"


def _load_current_visual_data(definition_pages_path: Path, page_id: str, visual_name: str) -> Optional[Dict[str, Any]]:
    visual_path = definition_pages_path / page_id / "visuals" / visual_name / "visual.json"
    if not visual_path.is_file():
        return None
    try:
        with open(visual_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _json_equal(left: Dict[str, Any], right: Dict[str, Any]) -> bool:
    return json.dumps(left, sort_keys=True, ensure_ascii=False) == json.dumps(right, sort_keys=True, ensure_ascii=False)


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
    definition_pages_path = current.get("pages_path")

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
        to_update_existing = desired_visuals & current_visuals

        for name in to_add:
            actions.append((ADD_VISUAL, {"page_id": page_id, "visual_name": name, "desired_page": desired}))
        for name in to_remove:
            actions.append((REMOVE_VISUAL, {"page_id": page_id, "visual_name": name}))
        if definition_pages_path:
            definition_pages_path = Path(definition_pages_path)
            for name in to_update_existing:
                desired_visual = _get_visual_data_by_name(desired, name)
                current_visual = _load_current_visual_data(definition_pages_path, page_id, name)
                if desired_visual and current_visual and not _json_equal(current_visual, desired_visual):
                    actions.append((UPDATE_VISUAL, {"page_id": page_id, "visual_name": name, "desired_page": desired}))
        if to_update_existing and (desired.get("grid_blueprint") or desired.get("report_canvas")):
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
    Execute add_page, add_visual, update_visual, remove_visual, update_position.
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
        elif action_type == UPDATE_VISUAL:
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


def _ensure_drillthrough_metadata_on_detail_pages(
    definition_pages_path: Path,
    desired_pages: List[Dict[str, Any]],
) -> None:
    """
    For each desired page that is a Detail page, merge drillthrough metadata (type, visibility, pageBinding)
    into existing page.json so that existing reports get the Drillthrough config on next sync.
    """
    for desired in desired_pages:
        page_id = desired.get("page_id") or ""
        if "Detail" not in page_id:
            continue
        metadata = desired.get("metadata") or {}
        if "type" not in metadata or metadata.get("type") != "Drillthrough":
            continue
        page_json_path = definition_pages_path / page_id / "page.json"
        if not page_json_path.is_file():
            continue
        try:
            with open(page_json_path, "r", encoding="utf-8") as f:
                page_data = json.load(f)
        except Exception:
            continue
        for key in ("type", "visibility", "pageBinding"):
            if key in metadata:
                page_data[key] = metadata[key]
        try:
            with open(page_json_path, "w", encoding="utf-8") as f:
                json.dump(page_data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass


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
    definition_pages_path = current.get("pages_path")
    if not definition_pages_path or not Path(definition_pages_path).exists():
        return False
    if actions:
        apply_actions(output_path, actions, Path(definition_pages_path))
    _ensure_drillthrough_metadata_on_detail_pages(Path(definition_pages_path), desired_pages)
    return True
