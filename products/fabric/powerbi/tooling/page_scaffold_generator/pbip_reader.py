"""
PBIP Reader

Reads existing report PBIP structure (Ist state) for delta updates.
Does not write; used to compare with desired state from Bracket/Templates.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def read_pbip(report_path: Path) -> Optional[Dict[str, Any]]:
    """
    Read existing report structure from a .Report folder.

    Args:
        report_path: Path to .Report folder (e.g. dist/COM-001.Report) or to definition/.

    Returns:
        Dict with page_order, active_page, pages (per-page width, height, visual_names),
        or None if report does not exist / is not a valid PBIP (no pages.json or no pages).
    """
    report_path = Path(report_path).resolve()
    definition_path = report_path / "definition" if (report_path / "definition").exists() else report_path
    pages_path = definition_path / "pages"
    pages_json_file = pages_path / "pages.json"

    if not pages_json_file.exists():
        return None
    try:
        with open(pages_json_file, "r", encoding="utf-8") as f:
            pages_data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None

    page_order: List[str] = pages_data.get("pageOrder") or []
    active_page: Optional[str] = pages_data.get("activePageName")

    if not page_order:
        return None

    pages: Dict[str, Dict[str, Any]] = {}
    for page_id in page_order:
        page_dir = pages_path / page_id
        if not page_dir.is_dir():
            pages[page_id] = {"width": None, "height": None, "visual_names": []}
            continue
        width = height = None
        page_json_file = page_dir / "page.json"
        if page_json_file.exists():
            try:
                with open(page_json_file, "r", encoding="utf-8") as f:
                    page_data = json.load(f)
                width = page_data.get("width")
                height = page_data.get("height")
            except (json.JSONDecodeError, OSError):
                pass
        visuals_dir = page_dir / "visuals"
        visual_names: List[str] = []
        if visuals_dir.is_dir():
            for item in visuals_dir.iterdir():
                if item.is_dir():
                    visual_names.append(item.name)
        pages[page_id] = {"width": width, "height": height, "visual_names": visual_names}

    return {
        "page_order": page_order,
        "active_page": active_page,
        "pages": pages,
        "definition_path": definition_path,
        "pages_path": pages_path,
    }


def report_exists_for_update(report_path: Path) -> bool:
    """
    Return True if report folder has definition/pages/pages.json and at least one page folder.
    Used to decide Full Generate vs Update mode.
    """
    state = read_pbip(report_path)
    if state is None:
        return False
    return len(state.get("page_order") or []) > 0
