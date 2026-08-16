"""Tests for per-idiom lifecycle metadata (version + status).

Every implemented idiom must carry a semantic `version` and a governed `status`; a `deprecated`
idiom must name its `superseded_by` replacement (an implemented idiom). This makes an idiom revision
a trackable event and lets a consumer tell whether a report used an idiom that has since changed.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library"))
import render  # noqa: E402

LIB = REPO_ROOT / "core" / "templates" / "page_templates" / "visual_library"
_SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
_STATUS = {"active", "experimental", "deprecated"}


def _implemented():
    return yaml.safe_load((LIB / "index.yaml").read_text(encoding="utf-8"))["implemented"]


def test_every_idiom_has_semver_version_and_valid_status():
    for iid in _implemented():
        e = render.load_entry(iid)
        v = e.get("version")
        assert isinstance(v, str) and _SEMVER.match(v), f"{iid}: version must be semver x.y.z, got {v!r}"
        assert e.get("status") in _STATUS, f"{iid}: status must be one of {_STATUS}, got {e.get('status')!r}"


def test_deprecated_idioms_point_to_an_implemented_replacement():
    impl = set(_implemented())
    for iid in impl:
        e = render.load_entry(iid)
        if e.get("status") == "deprecated":
            sup = e.get("superseded_by")
            assert sup, f"{iid}: deprecated idioms require superseded_by"
            assert sup != iid and sup in impl, f"{iid}: superseded_by '{sup}' is not an implemented idiom"


def test_superseded_by_only_on_deprecated():
    for iid in _implemented():
        e = render.load_entry(iid)
        if e.get("superseded_by"):
            assert e.get("status") == "deprecated", f"{iid}: superseded_by set but status is not deprecated"
