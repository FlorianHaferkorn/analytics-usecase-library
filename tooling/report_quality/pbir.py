"""PBIR/PBIP report parsing helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ParsedPage:
    name: str
    display_name: str
    page_json: dict[str, Any]
    visuals: dict[str, dict[str, Any]]
    page_dir: Path


@dataclass
class ParsedReport:
    report_dir: Path
    pages_metadata: dict[str, Any]
    pages: dict[str, ParsedPage]

    def page_by_suffix(self, suffix: str) -> ParsedPage | None:
        suffix_l = suffix.lower()
        for page in self.pages.values():
            if page.name.lower().endswith(suffix_l) or page.display_name.lower().endswith(suffix_l):
                return page
        return None


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_report(report_dir: Path) -> ParsedReport:
    """Parse a `.Report` folder in PBIR layout."""

    pages_json = report_dir / "definition" / "pages" / "pages.json"
    if not pages_json.exists():
        raise FileNotFoundError(f"Not a PBIR report directory: {report_dir}")

    pages_metadata = load_json(pages_json)
    page_order = pages_metadata.get("pageOrder") or []
    pages_dir = report_dir / "definition" / "pages"
    page_names = page_order or [p.name for p in sorted(pages_dir.glob("Page_*")) if p.is_dir()]

    pages: dict[str, ParsedPage] = {}
    for page_name in page_names:
        page_dir = pages_dir / page_name
        page_file = page_dir / "page.json"
        if not page_file.exists():
            continue
        page_json = load_json(page_file)
        visuals: dict[str, dict[str, Any]] = {}
        visuals_dir = page_dir / "visuals"
        if visuals_dir.exists():
            for visual_dir in sorted(p for p in visuals_dir.iterdir() if p.is_dir()):
                visual_file = visual_dir / "visual.json"
                if visual_file.exists():
                    visuals[visual_dir.name] = load_json(visual_file)
        pages[page_name] = ParsedPage(
            name=page_name,
            display_name=page_json.get("displayName", page_name),
            page_json=page_json,
            visuals=visuals,
            page_dir=page_dir,
        )
    return ParsedReport(report_dir=report_dir, pages_metadata=pages_metadata, pages=pages)


def iter_report_dirs(dist_root: Path) -> list[Path]:
    """Return `.Report` directories under a dist root or a single report path."""

    if dist_root.name.endswith(".Report") and dist_root.is_dir():
        return [dist_root]
    return sorted(p for p in dist_root.glob("*.Report") if p.is_dir())


def visual_pointer(report_dir: Path, page: ParsedPage, visual_name: str, suffix: str = "") -> str:
    base = f"{report_dir.name}/definition/pages/{page.name}/visuals/{visual_name}/visual.json"
    return f"{base}#/{suffix.strip('/')}" if suffix else base


def page_pointer(report_dir: Path, page: ParsedPage, suffix: str = "") -> str:
    base = f"{report_dir.name}/definition/pages/{page.name}/page.json"
    return f"{base}#/{suffix.strip('/')}" if suffix else base
