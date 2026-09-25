"""check_index ignoriert Git-Submodule (gitlinks, Modus 160000)."""
from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load():
    spec = importlib.util.spec_from_file_location("check_index", ROOT / "scripts" / "check_index.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def test_submodule_pfade_werden_ignoriert(tmp_path):
    ci = _load()
    _git(tmp_path, "init", "-q")
    (tmp_path / "a.md").write_text("x", encoding="utf-8")
    _git(tmp_path, "add", "a.md")
    # gitlink ohne echtes Submodul-Repo anlegen
    _git(tmp_path, "update-index", "--add", "--cacheinfo",
         "160000,1111111111111111111111111111111111111111,tools/sub")
    prefixes = ci._git_submodule_prefixes(tmp_path)
    assert prefixes == {(tmp_path / "tools" / "sub").resolve()}


def test_ohne_submodule_leer(tmp_path):
    ci = _load()
    _git(tmp_path, "init", "-q")
    assert ci._git_submodule_prefixes(tmp_path) == set()
