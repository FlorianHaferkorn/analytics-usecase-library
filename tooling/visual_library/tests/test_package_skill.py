"""Tests for package_skill.py — the standalone Visual Library bundle (Workflow B)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library"))
import package_skill  # noqa: E402


def test_bundle_is_complete_and_portable(tmp_path):
    m = package_skill.build(tmp_path / "b")
    b = tmp_path / "b"
    # the dependency-free surface is present
    for f in ("SKILL.md", "README.md", "manifest.json",
              "tooling/visual_library/render.py", "tooling/visual_library/resolve.py",
              "core/templates/page_templates/visual_library/index.yaml",
              "core/templates/page_templates/tokens/layout_grid.yaml"):
        assert (b / f).exists(), f"bundle missing {f}"
    assert m["idiom_yaml"] == 30 and m["golden_files"] > 90
    # portable: no ALUCA-core machinery leaked into the bundle
    assert not (b / "tooling" / "superversion").exists()
    assert not (b / "core" / "usecases").exists()


def test_bundle_resolve_runs_standalone(tmp_path):
    b = tmp_path / "b"
    package_skill.build(b)
    # smoke: the bundle's own resolve.py answers a purpose without the source tree
    first = package_skill.smoke(b)
    assert "compare_categories" in first
    # and audits a denied visual
    v = tmp_path / "v.json"
    v.write_text(json.dumps({"visual": {"visualType": "gaugeVisual"}}), encoding="utf-8")
    r = subprocess.run(
        [sys.executable, str(b / "tooling" / "visual_library" / "resolve.py"), "audit", str(v)],
        capture_output=True, text=True, timeout=60,
        encoding="utf-8", errors="replace",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    assert r.returncode == 1 and "DENIED" in r.stdout  # denied -> non-zero, useful in CI
