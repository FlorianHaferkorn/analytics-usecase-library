"""Offline reader for the vendored formatting catalogue of the official PBIR CLI.

The snapshot ``tooling/schemas/pbir/formatting_metadata_snapshot.json`` is written by
``python -m tooling.report_quality.refresh_authoring_metadata --formatting-only`` from
``powerbi-report-author formatting effective-properties`` / ``formatting list-vcos`` (Pin
0.4.0). It lets tests and generators tell a known formatting object/property from an unknown
one without the CLI (ADR 0001, metadata snapshot pattern).

``unknown_theme_entries`` mirrors the two theme rules of ``powerbi-report-author validate``
(``PBIR_THEME_VISUAL_PROP_UNKNOWN`` and the theme form of ``PBIR_FORMATTING_OBJECT_UNKNOWN``).
Calibrated 07.10.2026: on the Aurora theme that dist/ shipped until then it returns exactly
the 23 findings the CLI reported per report (18 properties, 5 objects); on every vendored
engine theme it returns none.

``unknown_visual_objects`` does the same for ``visual.objects`` of a visual.json
(``PBIR_FORMATTING_OBJECT_UNKNOWN`` / ``PBIR_FORMATTING_PROP_UNKNOWN``).
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

DEFAULT_SNAPSHOT_PATH = (
    Path(__file__).resolve().parents[1] / "schemas" / "pbir" / "formatting_metadata_snapshot.json"
)

WILDCARD = "*"


@lru_cache(maxsize=4)
def _load(path_str: str) -> dict[str, Any]:
    return json.loads(Path(path_str).read_text(encoding="utf-8"))


def snapshot(path: Path | str | None = None) -> dict[str, Any]:
    """The parsed snapshot (cached)."""
    return _load(str(path or DEFAULT_SNAPSHOT_PATH))


def _object_props(visual_type: str, obj: str, snap: dict[str, Any]) -> set[str] | None:
    """Property names of ``obj`` on ``visual_type``; ``None`` when the object is unknown.

    A visual's own object wins over the shared container object of the same name (e.g.
    ``advancedSlicerVisual.padding`` is a visual object without ``left``/``right``).
    """
    vcos: dict[str, list[str]] = snap["visualContainerObjects"]
    if visual_type == WILDCARD:
        props: set[str] = set()
        found = False
        for objects in snap["visualTypes"].values():
            if obj in objects:
                props.update(objects[obj])
                found = True
        if obj in vcos:
            props.update(vcos[obj])
            found = True
        return props if found else None
    objects = snap["visualTypes"].get(visual_type)
    if objects is None:
        return None
    if obj in objects:
        return set(objects[obj])
    if obj in vcos:
        return set(vcos[obj])
    return None


def is_known_visual_type(visual_type: str, path: Path | str | None = None) -> bool:
    return visual_type == WILDCARD or visual_type in snapshot(path)["visualTypes"]


def unknown_theme_entries(theme: dict[str, Any], path: Path | str | None = None) -> list[str]:
    """Unknown objects/properties in a theme's ``visualStyles``, as ``vt:object[.property]``.

    Visual types the catalogue does not know are skipped (the CLI reports those under a
    different rule); ``$id``-style keys inside an object entry are ignored.
    """
    snap = snapshot(path)
    findings: list[str] = []
    for visual_type, states in sorted((theme.get("visualStyles") or {}).items()):
        if not is_known_visual_type(visual_type, path):
            continue
        for _state, objects in sorted((states or {}).items()):
            for obj, entries in sorted((objects or {}).items()):
                known = _object_props(visual_type, obj, snap)
                if known is None:
                    findings.append(f"{visual_type}:{obj}")
                    continue
                for entry in entries or []:
                    for prop in sorted(entry or {}):
                        if prop.startswith("$"):
                            continue
                        if prop not in known:
                            findings.append(f"{visual_type}:{obj}.{prop}")
    return sorted(set(findings))


def unknown_visual_objects(visual_json: dict[str, Any], path: Path | str | None = None) -> list[str]:
    """Unknown ``visual.objects`` entries of one visual.json, as ``object[.property]``."""
    visual = visual_json.get("visual") or {}
    visual_type = visual.get("visualType") or ""
    snap = snapshot(path)
    if visual_type not in snap["visualTypes"]:
        return []
    own: dict[str, list[str]] = snap["visualTypes"][visual_type]
    findings: list[str] = []
    for obj, entries in sorted((visual.get("objects") or {}).items()):
        if obj not in own:
            findings.append(obj)
            continue
        for entry in entries or []:
            for prop in sorted((entry or {}).get("properties") or {}):
                if prop not in own[obj]:
                    findings.append(f"{obj}.{prop}")
    return findings


def iter_findings(items: Iterable[tuple[str, list[str]]]) -> list[str]:
    """Flatten ``(label, findings)`` pairs into ``label: finding`` lines (for assertion text)."""
    return [f"{label}: {f}" for label, found in items for f in found]
