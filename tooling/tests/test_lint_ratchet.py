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


def test_strict_fails_on_increase_and_advisory_does_not(monkeypatch, tmp_path):
    ziel = tmp_path / "lint_baseline.json"
    ziel.write_text(json.dumps({"gemessen": "2026-09-29", "regeln": {"F401": 1}}), "utf-8")
    monkeypatch.setattr(mod, "BASELINE", ziel)
    monkeypatch.setattr(mod, "ruff_befunde", lambda: collections.Counter({"F401": 2}))
    assert mod.main(["--strict"]) == 1
    assert mod.main([]) == 0


def test_update_baseline_only_lowers_and_stamps_today(monkeypatch, tmp_path):
    ziel = tmp_path / "lint_baseline.json"
    ziel.write_text(json.dumps({"gemessen": "1999-01-01", "regeln": {"F841": 30, "E501": 5}}), "utf-8")
    monkeypatch.setattr(mod, "BASELINE", ziel)
    monkeypatch.setattr(mod, "ruff_befunde", lambda: collections.Counter({"F841": 29, "E501": 9}))
    assert mod.main(["--update-baseline"]) == 0
    d = json.loads(ziel.read_text("utf-8"))
    assert d["gemessen"] == dt.date.today().isoformat()
    assert d["regeln"] == {"E501": 5, "F841": 29}, "sinkt mit, steigt nie"


def test_missing_baseline_is_red_under_strict(monkeypatch, tmp_path):
    monkeypatch.setattr(mod, "BASELINE", tmp_path / "fehlt.json")
    monkeypatch.setattr(mod, "ruff_befunde", lambda: collections.Counter({"E501": 1}))
    assert mod.main(["--strict"]) == 1


def test_a_missing_ruff_is_a_loud_skip(monkeypatch, capsys):
    monkeypatch.setattr(mod, "ruff_befunde", lambda: None)
    assert mod.main(["--strict"]) == 0
    assert "SKIP (nicht gelaufen)" in capsys.readouterr().out


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
