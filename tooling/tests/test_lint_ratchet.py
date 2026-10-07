"""Tests der Ruff-Sperrklinke (``scripts/check_lint_ratchet.py``, portiert aus Freelancing).

Ein Waechter, der nur auf dem sauberen Repo gruen wird, ist von einem ``return 0`` nicht zu
unterscheiden. Die Tests pruefen deshalb, dass die Sperrklinke **ausloest** — und dass sie je
Regel ausloest, nicht als Summe.
"""
from __future__ import annotations

import collections
import datetime as dt
import importlib.util
import json
import pathlib
import sys

import pytest

_PFAD = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "check_lint_ratchet.py"
_spec = importlib.util.spec_from_file_location("check_lint_ratchet", _PFAD)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)


def test_a_new_finding_in_a_frozen_rule_is_reported():
    gestiegen, _ = mod.vergleich(collections.Counter({"F821": 13}), {"F821": 12})
    assert gestiegen == ["F821: 12 -> 13 (+1)"]


def test_a_rule_that_stays_put_is_silent():
    gestiegen, gesunken = mod.vergleich(collections.Counter({"E501": 1180}), {"E501": 1180})
    assert not gestiegen and not gesunken


def test_a_brand_new_rule_counts_as_an_increase():
    """Ein bisher unbekannter Regelcode hat Baseline 0 — sonst waere jede neue Klasse frei."""
    gestiegen, _ = mod.vergleich(collections.Counter({"B008": 1}), {})
    assert gestiegen == ["B008: 0 -> 1 (+1)"]


def test_progress_in_one_rule_cannot_pay_for_a_regression_in_another():
    jetzt = collections.Counter({"W293": 985, "F821": 13})
    gestiegen, gesunken = mod.vergleich(jetzt, {"W293": 1015, "F821": 12})
    assert sum(jetzt.values()) < 1015 + 12, "die Summe sinkt — genau darum geht es"
    assert gestiegen == ["F821: 12 -> 13 (+1)"]
    assert gesunken == ["W293: 1015 -> 985"]


def _ruff_da(monkeypatch, befunde, version="0.16.9", pin="0.16.9"):
    """Ruff als gefunden vortaeuschen (Pin-Version), Befunde fest vorgeben."""
    monkeypatch.setattr(mod, "ruff_pin", lambda workflow=None: pin)
    monkeypatch.setattr(mod, "finde_ruff", lambda p: (["ruff"], version, [f"ruff ({version})"]))
    monkeypatch.setattr(mod, "ruff_befunde", lambda befehl=None: befunde)


def test_an_increase_is_red_with_and_without_strict(monkeypatch, tmp_path):
    """Bis 29.09.2026 endete ein Anstieg ohne --strict mit 0 (gemessen: E402 67 -> 70, Exit 0)."""
    ziel = tmp_path / "lint_baseline.json"
    ziel.write_text(json.dumps({"gemessen": "2026-09-29", "regeln": {"F401": 1}}), "utf-8")
    monkeypatch.setattr(mod, "BASELINE", ziel)
    _ruff_da(monkeypatch, collections.Counter({"F401": 2}))
    assert mod.main(["--strict"]) == 1
    assert mod.main([]) == 1
    assert mod.main(["--pin-pflicht"]) == 1


def test_update_baseline_only_lowers_and_stamps_today(monkeypatch, tmp_path):
    ziel = tmp_path / "lint_baseline.json"
    ziel.write_text(json.dumps({"gemessen": "1999-01-01", "regeln": {"F841": 30, "E501": 5}}), "utf-8")
    monkeypatch.setattr(mod, "BASELINE", ziel)
    _ruff_da(monkeypatch, collections.Counter({"F841": 29, "E501": 9}))
    assert mod.main(["--update-baseline"]) == 0
    d = json.loads(ziel.read_text("utf-8"))
    assert d["gemessen"] == dt.date.today().isoformat()
    assert d["regeln"] == {"E501": 5, "F841": 29}, "sinkt mit, steigt nie"


def test_missing_baseline_is_red(monkeypatch, tmp_path):
    monkeypatch.setattr(mod, "BASELINE", tmp_path / "fehlt.json")
    _ruff_da(monkeypatch, collections.Counter({"E501": 1}))
    assert mod.main(["--strict"]) == 1
    assert mod.main([]) == 1


def test_a_missing_ruff_is_not_run_not_ok(monkeypatch, capsys):
    """Kein ruff: Ausgang 2 (nicht gelaufen), nie 0 — auch ohne --strict."""
    monkeypatch.setattr(mod, "ruff_kandidaten", lambda: [])
    monkeypatch.setattr(mod, "ruff_befunde", lambda befehl=None: pytest.fail("darf nicht zaehlen"))
    assert mod.main(["--strict"]) == mod.NICHT_GELAUFEN == 2
    assert mod.main([]) == 2
    out = capsys.readouterr().out
    assert "NICHT GELAUFEN" in out and "pip install ruff" in out


def test_a_ruff_that_breaks_is_not_run(monkeypatch):
    _ruff_da(monkeypatch, None)
    assert mod.main([]) == 2


@pytest.mark.skipif(sys.platform == "win32", reason="Shell-Skript als Ersatz-Binary")
def test_ruff_is_found_as_a_binary_on_path(monkeypatch, tmp_path):
    """Der Befund vom 29.09.2026: ruff als Binary im PATH, nicht als Modul im Interpreter."""
    binary = tmp_path / "ruff"
    binary.write_text("#!/bin/sh\necho 'ruff 0.16.9'\n", "utf-8")
    binary.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.setattr(mod.sys, "executable", str(tmp_path / "python-ohne-ruff"))
    befehl, version, gefunden = mod.finde_ruff("0.16.9")
    assert befehl == [str(binary)] and version == "0.16.9"
    assert len(gefunden) == 1


def test_the_pinned_candidate_wins_over_the_first(monkeypatch):
    monkeypatch.setattr(mod, "ruff_kandidaten",
                        lambda: [(["/bin/ruff"], "0.15.8"), (["py", "-m", "ruff"], "0.16.9")])
    assert mod.finde_ruff("0.16.9")[:2] == (["py", "-m", "ruff"], "0.16.9")
    assert mod.finde_ruff("9.9.9")[:2] == (["/bin/ruff"], "0.15.8"), "ohne Treffer: der erste"


def test_a_version_off_the_pin_warns_locally_and_is_not_run_under_pin_pflicht(monkeypatch, capsys):
    monkeypatch.setattr(mod, "ruff_pin", lambda workflow=None: "0.16.9")
    monkeypatch.setattr(mod, "finde_ruff", lambda p: (["ruff"], "0.15.8", ["ruff (0.15.8)"]))
    monkeypatch.setattr(mod, "lade_baseline", lambda pfad=None: {"E501": 1})
    monkeypatch.setattr(mod, "ruff_befunde", lambda befehl=None: collections.Counter({"E501": 1}))
    assert mod.main([]) == 0
    assert "WARNUNG Versionsabweichung" in capsys.readouterr().out
    assert mod.main(["--pin-pflicht"]) == 2


def test_the_pin_is_read_from_the_ci_workflow():
    pin = mod.ruff_pin()
    assert pin and pin[0].isdigit(), "stage1.yml muss ruff==<version> pinnen"


def test_the_committed_baseline_matches_the_repo_today():
    """Faellt dieser Test, ist die Baseline veraltet: aufgeraeumt ohne festzuschreiben, oder
    Befunde sind dazugekommen. Ohne ruff im Interpreter: Soft-Skip wie das Tor selbst."""
    jetzt = mod.ruff_befunde()
    if jetzt is None:
        return
    gestiegen, _ = mod.vergleich(jetzt, mod.lade_baseline())
    assert gestiegen == [], gestiegen


def test_the_baseline_file_is_readable_and_names_its_measurement_date():
    d = json.loads(mod.BASELINE.read_text("utf-8"))
    dt.date.fromisoformat(d["gemessen"])
    assert all(isinstance(n, int) and n > 0 for n in d["regeln"].values())


def test_the_versioned_pre_commit_hook_runs_the_ratchet_only_for_staged_py():
    # .githooks/pre-commit ist der Hook, den der SessionStart setzt (core.hooksPath). Bis
    # 07.10.2026 rief er die Sperrklinke nicht auf, obwohl scripts/_INDEX.md es behauptete.
    text = (_PFAD.parents[1] / ".githooks" / "pre-commit").read_text(encoding="utf-8")
    block = text[text.index("scripts/check_lint_ratchet.py") - 200:]
    assert "grep -qE '\\.py$'" in block
    assert 'if [ "$rc" -eq 1 ]; then exit 1; fi' in block
    assert "[UNGEPRUEFT] Ruff-Sperrklinke" in block
