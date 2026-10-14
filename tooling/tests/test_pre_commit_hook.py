"""Der eine pre-commit-Hook: `.githooks/pre-commit` (zusammengelegt am 07.10.2026).

Bis dahin gab es zwei Hooks mit verschiedenen Toren; aktiv war je nach Klon der eine oder der
andere. Diese Tests halten fest, dass es nur noch einen gibt, dass er jedes Tor des alten
`tooling/git-hooks/pre-commit` traegt und dass der SessionStart einen alten `core.hooksPath`
umstellt, statt die Tore stillzulegen.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_HOOK = _REPO / ".githooks" / "pre-commit"
_ACTIVATE = _REPO / ".claude" / "hooks" / "activate_git_hooks.sh"


def _text() -> str:
    return _HOOK.read_text(encoding="utf-8")


def test_there_is_exactly_one_pre_commit_hook():
    assert _HOOK.is_file()
    assert not (_REPO / "tooling" / "git-hooks" / "pre-commit").exists()


@pytest.mark.parametrize(
    "aufruf",
    [
        "scripts/check_index.py --strict || exit 1",
        "tooling/validation/check_kundendaten.py --staged --leise",
        "secret_scan_gate.py --baseline --staged",
        "scripts/check_lint_ratchet.py",
        "tooling/ontology/registry_builder.py --out-dir tooling/ontology/out --strict || exit 1",
    ],
)
def test_every_gate_of_the_former_second_hook_is_wired(aufruf):
    assert aufruf in _text()


def test_customer_identifier_gate_reports_unchecked_without_blocklist():
    text = _text()
    block = text[text.index("KUNDENDATEN_SPERRLISTE:-") : text.index("secret_scan_gate.py")]
    assert "[UNGEPRUEFT] Kundendaten" in block
    assert block.count("|| exit 1") == 2  # mit Sperrliste (Umgebung oder Datei) blockiert ein Fund


def test_registry_runs_only_for_staged_core_and_the_hook_ends_green():
    text = _text()
    block = text[text.index("registry_builder.py") - 300 :]
    assert "grep -qE '^core/'" in block
    assert text.rstrip().endswith("exit 0")
    assert "exec " not in text  # ein exec vor dem Ende liesse spaetere Tore aus


def test_hook_prefers_the_windows_launcher_and_forces_utf8():
    text = _text()
    assert 'PY="py -3"' in text
    assert "export PYTHONUTF8=1" in text
    assert '"$PY"' not in text  # "py -3" in Anfuehrungszeichen waere ein Programmname


@pytest.mark.skipif(
    sys.platform == "win32" or not shutil.which("bash") or not shutil.which("git"), reason="braucht bash und git"
)
@pytest.mark.parametrize(
    ("vorher", "nachher"),
    [
        (None, ".githooks"),
        ("tooling/git-hooks", ".githooks"),  # alter Wert zeigte nach dem Zusammenlegen ins Leere
        (".githooks", ".githooks"),
        ("eigener/ordner", "eigener/ordner"),  # bewusst gesetzt: unangetastet
    ],
)
def test_session_start_activates_or_migrates_hooks_path(tmp_path, vorher, nachher):
    git = ["git", "-C", str(tmp_path)]
    subprocess.run([*git, "init", "-q"], check=True)
    (tmp_path / ".githooks").mkdir()
    (tmp_path / ".githooks" / "pre-commit").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    if vorher:
        subprocess.run([*git, "config", "core.hooksPath", vorher], check=True)
    env = {
        "CLAUDE_PROJECT_DIR": str(tmp_path),
        "PATH": os.environ.get("PATH", ""),
        "HOME": str(tmp_path),
        "GIT_CONFIG_NOSYSTEM": "1",
    }
    bash = shutil.which("bash")
    assert bash
    res = subprocess.run([bash, str(_ACTIVATE)], env=env, capture_output=True, text=True, encoding="utf-8")
    assert res.returncode == 0, res.stderr
    wert = subprocess.run(
        [*git, "config", "--get", "core.hooksPath"], capture_output=True, text=True, encoding="utf-8"
    ).stdout.strip()
    assert wert == nachher
