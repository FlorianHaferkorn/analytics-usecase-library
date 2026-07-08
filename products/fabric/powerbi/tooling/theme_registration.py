"""Helpers for registering custom themes in PBIP RegisteredResources."""

from __future__ import annotations

import json
import re
from pathlib import Path


def safe_theme_stem(name: str) -> str:
    """Return a safe filename stem (no path, no .json extension)."""
    stem = Path(name).stem if name else "theme"
    return re.sub(r"[^\w\-]", "_", stem) or "theme"


def registered_theme_filename(stem: str) -> str:
    """Return RegisteredResources filename for a sanitized theme stem."""
    return f"{safe_theme_stem(stem)}.json"


def custom_theme_collection_name(stem: str) -> str:
    """Return themeCollection.customTheme.name (logical name, no .json extension)."""
    return safe_theme_stem(stem)


def find_registered_custom_theme_item(package: dict, logical_name: str) -> dict | None:
    """Resolve resourcePackages CustomTheme item from themeCollection logical name."""
    stem = custom_theme_collection_name(logical_name)
    filename = registered_theme_filename(stem)
    for item in package.get("items", []):
        if item.get("type") != "CustomTheme":
            continue
        item_name = item.get("name", "")
        item_path = item.get("path", "")
        if item_name in {stem, filename} or Path(item_path).stem == stem:
            return item
    return None


def align_theme_name_to_registered_stem(payload: dict, registered_stem: str) -> bool:
    """Set theme JSON ``name`` to match the RegisteredResources filename stem."""
    stem = safe_theme_stem(registered_stem)
    if payload.get("name") == stem:
        return False
    payload["name"] = stem
    return True


def prepare_registered_theme_bytes(source_path: Path) -> tuple[str, bytes]:
    """Load theme JSON, align internal name to sanitized stem, return (filename, bytes)."""
    payload = json.loads(source_path.read_text(encoding="utf-8"))
    registered_stem = safe_theme_stem(source_path.stem)
    align_theme_name_to_registered_stem(payload, registered_stem)
    filename = f"{registered_stem}.json"
    content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    return filename, content.encode("utf-8")


def write_registered_theme(source_path: Path, dest_path: Path) -> Path:
    """Write theme to RegisteredResources with internal name aligned to sanitized dest stem."""
    payload = json.loads(source_path.read_text(encoding="utf-8"))
    registered_stem = safe_theme_stem(dest_path.stem)
    align_theme_name_to_registered_stem(payload, registered_stem)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    output_path = dest_path.parent / registered_theme_filename(registered_stem)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output_path
