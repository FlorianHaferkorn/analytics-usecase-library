"""Repository-wide secret baseline gate (``secret_scan_gate.py --baseline``, 07.10.2026).

Pins the wiring (CI step, pre-commit hook, version pin), the structural hash-line filter that
the baseline stores, and the exit-code contract 0 clean / 1 finding / 2 not run. The last test
is the counter-check with the real tool: a planted key turns red, a new PIN.json hash stays
green. Secret-looking values are built at runtime, so this file itself stays clean.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

_SCRIPTS = Path(__file__).resolve().parents[1]
_REPO = _SCRIPTS.parents[4]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import secret_scan_gate as gate  # noqa: E402

_BASELINE = json.loads((_REPO / gate.BASELINE).read_text(encoding="utf-8"))
_STAGE1 = _REPO / ".github" / "workflows" / "stage1.yml"
_HOOK = _REPO / ".githooks" / "pre-commit"
_AZURE_BUILD = _SCRIPTS.parent / ".azure-pipelines" / "_template_build_solution.yml"


def _line_filters(baseline: dict) -> list:
    return [f for f in baseline["filters_used"]
            if f["path"] == "detect_secrets.filters.regex.should_exclude_line"]


# -- wiring ------------------------------------------------------------------------------


def test_baseline_stores_exactly_the_gate_hash_patterns():
    filters = _line_filters(_BASELINE)
    assert len(filters) == 1
    assert filters[0]["pattern"] == list(gate.HASH_LINE_PATTERNS)


def test_baseline_has_no_file_exclusion():
    """The filter is line-based on purpose: other strings in PIN/lock files stay scanned."""
    assert not [f for f in _BASELINE["filters_used"] if f["path"].endswith("should_exclude_file")]


def test_every_baseline_entry_is_reviewed():
    entries = [e for hits in _BASELINE["results"].values() for e in hits]
    assert entries and all(e.get("is_secret") is False for e in entries)


def test_detect_secrets_pin_is_the_baseline_version_everywhere():
    pinned = _BASELINE["version"]
    for path in (_STAGE1, _AZURE_BUILD):
        pins = re.findall(r"detect-secrets==([0-9][0-9.]*)", path.read_text(encoding="utf-8"))
        assert pins == [pinned], path.name


def test_stage1_runs_the_baseline_gate_after_installing_the_tool():
    steps = yaml.safe_load(_STAGE1.read_text(encoding="utf-8"))["jobs"]["python-checks"]["steps"]
    install = next(i for i, s in enumerate(steps) if "detect-secrets==" in s.get("run", ""))
    gate_step = next(i for i, s in enumerate(steps)
                     if "secret_scan_gate.py --baseline" in s.get("run", ""))
    assert install < gate_step
    assert not steps[gate_step].get("continue-on-error", False)
    assert "--staged" not in steps[gate_step]["run"]


def test_pre_commit_hook_blocks_on_findings_and_reports_not_run():
    text = _HOOK.read_text(encoding="utf-8")
    assert "secret_scan_gate.py --baseline --staged" in text
    assert 'if [ "$rc" -eq 1 ]; then exit 1; fi' in text
    assert "[UNGEPRUEFT]" in text


# -- structural hash-line filter ---------------------------------------------------------

_HEX64 = "0123456789abcdef" * 4
_HEX40 = _HEX64[:40]
_COLOR = "1f0a" * 96


@pytest.mark.parametrize("line", [
    f'      "sha256": "{_HEX64}"',
    f'  "sha256": "{_HEX64}",',
    f'  "quelle_sha256": "{_HEX64}",\r',
    f'  "source_commit": "{_HEX40}",',
    f'    "commit": "{_HEX40}"',
    f'      "dhash": "{_HEX64}",',
    f'      "color": "{_COLOR}",',
    f'  "_regelstand": "{_HEX64[:12]}"',
])
def test_hash_lines_are_filtered(line):
    assert any(re.search(p, line) for p in gate.HASH_LINE_PATTERNS)


@pytest.mark.parametrize("line", [
    f'  "api_key": "{_HEX64}",',                      # hash shape, but not a hash key
    f'  "client_secret": "{_HEX40}",',
    f'  "sha256": "{_HEX64[:63]}",',                  # wrong length
    f'  "sha256": "{_HEX64.upper()}",',               # not hexdigest output
    f'  "commit": "{_HEX64}",',                       # commit with a 64-char value
    f'  "sha256": "{_HEX64}", "token": "{_HEX40}"',   # second value on the line
    f'  "color": "{"2f0a" * 96}",',                   # byte > 0x1f is no 5-bit colour grid
    f'  sha256: "{_HEX64}",',                         # code, not a JSON line
])
def test_other_lines_are_not_filtered(line):
    assert not any(re.search(p, line) for p in gate.HASH_LINE_PATTERNS)


# -- exit-code contract (hook faked) -------------------------------------------------------


def _repo_with_baseline(tmp_path: Path, version: str = "1.5.0") -> Path:
    (tmp_path / gate.BASELINE).write_text(json.dumps({"version": version, "results": {}}),
                                          encoding="utf-8")
    (tmp_path / "a.txt").write_text("x\n", encoding="utf-8")
    return tmp_path


def _fake(monkeypatch, *, hook=("hook",), version="1.5.0", files=("a.txt",), result=(0, "", "")):
    monkeypatch.setattr(gate, "_hook_command", lambda: list(hook) if hook else None)
    monkeypatch.setattr(gate, "_installed_version", lambda h: version)
    monkeypatch.setattr(gate, "_git_files", lambda root, staged: list(files))
    monkeypatch.setattr(gate, "_run_chunk", lambda h, t, root, chunk: result)


@pytest.mark.parametrize("kwargs,expected", [
    ({}, 0),
    ({"result": (1, f"ERROR: {gate.HOOK_FINDING_MARK} to git repo!", "")}, 1),
    ({"result": (1, "", "Traceback ...")}, 2),        # hook crashed: not run, not a finding
    ({"result": (3, "The baseline file was updated.", "")}, 0),
    ({"hook": None}, 2),                                # tool missing
    ({"version": "1.4.0"}, 2),                          # other version than the baseline pin
    ({"files": ()}, 2),                                 # nothing tracked: did not run
])
def test_baseline_gate_exit_codes(monkeypatch, tmp_path, kwargs, expected):
    _fake(monkeypatch, **kwargs)
    assert gate.baseline_main(_repo_with_baseline(tmp_path)) == expected


def test_no_staged_files_is_clean_not_an_error(monkeypatch, tmp_path):
    _fake(monkeypatch, files=())
    assert gate.baseline_main(_repo_with_baseline(tmp_path), staged=True) == 0


def test_missing_baseline_is_not_run(tmp_path):
    assert gate.baseline_main(tmp_path) == 2


# -- counter-check with the real tool -------------------------------------------------------


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-c", "user.email=t@example.invalid", "-c", "user.name=t", *args],
                   cwd=repo, check=True, capture_output=True)


def test_real_hook_reds_a_planted_key_and_keeps_a_new_pin_hash_green(tmp_path):
    pytest.importorskip("detect_secrets")
    if shutil.which("git") is None:
        pytest.skip("git missing")
    if gate._installed_version(gate._hook_command()) != _BASELINE["version"]:
        pytest.skip("detect-secrets version differs from the baseline pin")
    repo = tmp_path / "repo"
    repo.mkdir()
    shutil.copy(_REPO / gate.BASELINE, repo / gate.BASELINE)
    _git(repo, "init", "-q")
    pin = {"source_commit": "ab" * 20, "files": [{"path": "x.py", "sha256": "cd" * 32}]}
    (repo / "PIN.json").write_text(json.dumps(pin, indent=2) + "\n", encoding="utf-8")
    _git(repo, "add", "PIN.json", gate.BASELINE)
    assert gate.baseline_main(repo) == 0
    assert gate.baseline_main(repo, staged=True) == 0
    key = "AKIA" + "ZQ7T" * 4
    (repo / "settings.py").write_text(f'AWS_ACCESS_KEY_ID = "{key}"\n', encoding="utf-8")
    _git(repo, "add", "settings.py")
    assert gate.baseline_main(repo, staged=True) == 1
    assert gate.baseline_main(repo) == 1


def test_a_crash_reads_not_run_never_finding(monkeypatch):
    def boom(**kwargs):
        raise RuntimeError("unexpected")
    monkeypatch.setattr(gate, "baseline_main", boom)
    assert gate.cli(["--baseline"]) == 2


def test_missing_version_cli_reads_as_unknown_version(tmp_path):
    assert gate._installed_version([str(tmp_path / "detect-secrets-hook")]) == ""
