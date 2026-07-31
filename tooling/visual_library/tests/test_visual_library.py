"""Golden + determinism tests for the ALUCA Visual Library.

Guarantees the target: the same request yields the same result every time.
- byte-for-byte: each idiom x tool renders exactly its frozen golden.
- idempotent: rendering twice returns identical bytes.
- valid + fully filled: JSON tools parse; no unfilled {{...}} placeholders remain.
- schema: every idiom carries the required keys; index `implemented` files exist.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library"))
import render  # noqa: E402

LIB = REPO_ROOT / "core" / "templates" / "page_templates" / "visual_library"


def _index() -> dict:
    return yaml.safe_load((LIB / "index.yaml").read_text(encoding="utf-8"))


def _implemented() -> "list[str]":
    return _index().get("implemented", [])


def test_index_implemented_entries_exist_and_have_required_keys():
    schema = yaml.safe_load((LIB / "_schema.yaml").read_text(encoding="utf-8"))
    for idiom in _implemented():
        entry = render.load_entry(idiom)  # raises if a required key is missing
        assert entry["id"] == idiom
        for key in schema["required_keys"]:
            assert key in entry, f"{idiom} missing {key}"
        # every governed tool track is realised
        for tool in schema["tools"]:
            assert tool in entry["realizations"], f"{idiom} missing tool {tool}"


def test_every_realization_matches_its_golden_byte_for_byte():
    for idiom in _implemented():
        for tool in render.tools(idiom):
            out, ext = render.render(idiom, tool)
            gp = render.golden_path(idiom, tool, ext)
            assert gp.exists(), f"missing golden {gp.name} (run: render.py write {idiom})"
            assert out == gp.read_text(encoding="utf-8"), f"{idiom}.{tool} drifted from its golden"


def test_render_is_idempotent():
    for idiom in _implemented():
        for tool in render.tools(idiom):
            assert render.render(idiom, tool)[0] == render.render(idiom, tool)[0]


def test_no_unfilled_placeholders_and_json_is_valid():
    for idiom in _implemented():
        for tool in render.tools(idiom):
            out, ext = render.render(idiom, tool)
            assert "{{" not in out and "}}" not in out, f"{idiom}.{tool} has an unfilled placeholder"
            if ext == "json":
                json.loads(out)  # raises on invalid JSON
