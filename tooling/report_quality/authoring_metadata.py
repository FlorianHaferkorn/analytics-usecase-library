"""Reader for the vendored authoring-metadata snapshot (ADR 0001).

Pure stdlib. Lets the Tier 0 floor (and the report generator) read authoritative
visual-type role metadata that was captured from Microsoft's official CLI -- WITHOUT
requiring the CLI at runtime. A missing or unreadable snapshot degrades gracefully
to empty results, so callers fall back to their own defaults.

The snapshot is produced by ``refresh_authoring_metadata.py``.
"""

from __future__ import annotations

import functools
import json
from pathlib import Path

# tooling/report_quality/authoring_metadata.py -> tooling/schemas/pbir/...
DEFAULT_SNAPSHOT_PATH = Path(__file__).resolve().parents[1] / "schemas" / "pbir" / "authoring_metadata_snapshot.json"


@functools.lru_cache(maxsize=8)
def _load_visual_types(path_str: str) -> dict | None:
    """Return the ``visualTypes`` map, or ``None`` if the snapshot is unavailable."""
    path = Path(path_str)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data.get("visualTypes") or {}


def _visual_types(path: Path | str | None) -> dict:
    return _load_visual_types(str(path or DEFAULT_SNAPSHOT_PATH)) or {}


def is_available(path: Path | str | None = None) -> bool:
    """Whether a readable snapshot exists at ``path`` (default: vendored snapshot)."""
    return _load_visual_types(str(path or DEFAULT_SNAPSHOT_PATH)) is not None


def required_roles(visual_type: str, path: Path | str | None = None) -> list[str]:
    """Authoritative required (mandatory) roles for ``visual_type`` (empty if unknown)."""
    return list((_visual_types(path).get(visual_type) or {}).get("requiredRoles") or [])


def roles(visual_type: str, path: Path | str | None = None) -> dict[str, str]:
    """All known roles for ``visual_type`` mapped to their kind (empty if unknown)."""
    return dict((_visual_types(path).get(visual_type) or {}).get("roles") or {})


def is_known_role(visual_type: str, role: str, path: Path | str | None = None) -> bool:
    """Whether ``role`` is a valid role on ``visual_type`` per the official metadata."""
    return role in roles(visual_type, path)


def known_visual_types(path: Path | str | None = None) -> list[str]:
    """Sorted list of every visual type present in the snapshot."""
    return sorted(_visual_types(path).keys())
