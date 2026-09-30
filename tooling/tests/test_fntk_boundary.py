"""Notebook Toolkit boundary guard (tooling/validation/check_fntk_boundary.py, Meridian D-603).

Probes are assembled from parts so this file does not itself name the tool: it lives under
``tooling/`` and is scanned like every other tracked file there.
"""
from __future__ import annotations

import base64
import subprocess
from pathlib import Path

import pytest

from tooling.validation.check_fntk_boundary import (
    EXEMPT,
    FNTK_RE,
    find_offenders,
    in_blocked_area,
    main,
)

CLI = "fn" + "tk"
PKG = "fabric-notebook-" + "toolkit"
MOD = "fabric_notebook_" + "toolkit"


@pytest.mark.parametrize("line", [
    f"pip install {PKG}==0.0.1a10",
    f"{MOD}>=0.0.1",
    f"{CLI} init --agent claude",
    f"run: {CLI.upper()} session start",
    f"Fabric-Notebook-{'Toolkit'}",
])
def test_positive_probes_match(line: str) -> None:
    assert FNTK_RE.search(line)


def test_negative_probes_do_not_match() -> None:
    # Base64 noise: the four letters inside an encoded blob must not count.
    blob = "AAAA+" + CLI + "/BBBB=" + CLI + "=CCC" + "x" + CLI + "y"
    assert not FNTK_RE.search(blob)
    assert not FNTK_RE.search(base64.b64encode(b"\x00" * 64).decode())
    assert not FNTK_RE.search("fabric notebook toolkit")   # prose without separator
    assert not FNTK_RE.search("Notebook-Toolkit-Grenze")


@pytest.mark.parametrize("path, blocked", [
    ("products/fabric/powerbi/dist/Commercial/model.tmdl", True),
    ("tooling/generator/foo.py", True),
    ("core/usecases/COM-001/UseCase_Bracket.yaml", True),
    (".github/workflows/ci.yml", True),
    ("requirements.txt", True),
    ("tooling/requirements-dev.txt", True),
    ("docs/agent/agent-developer-tools.md", False),
    ("internal/project_mgmt/FABRIC_FABCON_EU_2026_PLAN.md", False),
    ("tooling/validation/check_fntk_boundary.py", False),
])
def test_blocked_areas(path: str, blocked: bool) -> None:
    assert in_blocked_area(path) is blocked


def test_find_offenders_reports_blocked_and_ignores_allowed() -> None:
    files = {
        "products/x/deploy.py": f"import os\nsubprocess.run(['{CLI}', 'run'])\n",
        "requirements.txt": f"pyyaml\n{PKG}==0.0.1a10\n",
        "docs/agent/agent-developer-tools.md": f"pip install {PKG}\n",
        "tooling/quality/check_upstream_sources.py": f'"package": "{PKG}"\n',
        "products/x/assets.js": "data:image/png;base64,AAAA+" + CLI + "/BBBB=\n",
        "core/x.png": f"{CLI}",   # binary suffix, not scanned
    }
    got = find_offenders(files, files.get)
    assert got == [("products/x/deploy.py", 2, CLI), ("requirements.txt", 2, PKG)]


def test_every_exemption_carries_a_reason_and_exists() -> None:
    root = Path(__file__).resolve().parents[2]
    for path, reason in EXEMPT.items():
        assert reason.strip(), path
        assert (root / path).is_file(), path


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def test_main_on_real_git_repo(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "note.md").write_text(f"{CLI} is internal\n", encoding="utf-8")
    (tmp_path / "tooling").mkdir()
    (tmp_path / "tooling" / "ok.py").write_text("print('ok')\n", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    assert main(["--repo-root", str(tmp_path)]) == 0

    (tmp_path / "requirements.txt").write_text(f"{PKG}==0.0.1a10\n", encoding="utf-8")
    _git(tmp_path, "add", "requirements.txt")
    assert main(["--repo-root", str(tmp_path)]) == 1


def test_main_reports_not_checked_outside_git(tmp_path: Path) -> None:
    assert main(["--repo-root", str(tmp_path / "missing")]) == 2


def test_repository_is_clean() -> None:
    root = Path(__file__).resolve().parents[2]
    assert main(["--repo-root", str(root)]) == 0
