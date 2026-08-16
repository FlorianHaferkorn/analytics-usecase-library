"""Tests for registry.py — the versioned, cross-repo-consumable idiom index."""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library"))
import registry  # noqa: E402

_SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def test_committed_registry_is_current():
    r = registry.check()
    assert r["in_sync"], f"registry.json is stale — run `registry.py build` ({r})"


def test_every_entry_has_version_status_and_checksum():
    for e in registry.load_registry()["idioms"]:
        assert _SEMVER.match(e["version"]), f"{e['id']}: bad version {e['version']}"
        assert e["status"] in {"active", "experimental", "deprecated"}, f"{e['id']}: bad status"
        assert e["checksum"].startswith("sha256:") and len(e["checksum"]) == 7 + 64, f"{e['id']}: bad checksum"
        assert e["purpose"], f"{e['id']}: missing purpose"


def test_registry_count_matches_implemented():
    reg = registry.load_registry()
    assert reg["count"] == len(reg["idioms"]) == len(registry._implemented())


def test_checksum_is_deterministic():
    a = {e["id"]: e["checksum"] for e in registry.build_registry()["idioms"]}
    b = {e["id"]: e["checksum"] for e in registry.build_registry()["idioms"]}
    assert a == b
