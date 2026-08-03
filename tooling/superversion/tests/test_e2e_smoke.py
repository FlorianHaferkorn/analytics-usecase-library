"""Tests for the E2E smoke pipeline (task I-3.5).

DoD: one command drives Bracket → model → TMDL+PBIR → validate and exits 0 when
green, non-zero when any stage is red.
"""
from __future__ import annotations

from pathlib import Path

from tooling.superversion import e2e_smoke

REPO = Path(__file__).resolve().parents[3]
COM001 = REPO / "core/usecases/core/COM-001_Sales_Performance/UseCase_Bracket.yaml"


def _by_name(results):
    return {r.name: r for r in results}


def test_run_com001_no_stage_fails():
    results = e2e_smoke.run(COM001)
    stages = _by_name(results)
    # All five stages are present and none failed (pbir may SKIP without the CLI).
    assert set(stages) == {"source", "golden_thread", "page_slots", "tmdl", "pbir"}
    assert not any(r.failed for r in results), [str(r) for r in results]
    assert stages["source"].status == "PASS"
    assert stages["golden_thread"].status == "PASS"
    assert stages["tmdl"].status == "PASS"
    assert stages["pbir"].status in {"PASS", "SKIP"}
    # page_slots is HARD since 2026-08-02 — all 40 pages carry every mandatory slot
    # and each resolves its own grid template. WARN stays possible for manifest gaps
    # (no template_variant / no grid template for a level); FAIL means the emission
    # dropped a slot and is excluded here rather than tolerated.
    assert stages["page_slots"].status in {"PASS", "WARN"}


def test_main_exits_zero_on_default_uc(capsys):
    assert e2e_smoke.main([]) == 0
    out = capsys.readouterr().out
    assert "[e2e] OK" in out


def test_pbir_skips_without_cli_but_does_not_fail(monkeypatch):
    monkeypatch.setattr(e2e_smoke.shutil, "which", lambda _cli: None)
    results = e2e_smoke.run(COM001)
    pbir = _by_name(results)["pbir"]
    assert pbir.status == "SKIP"
    assert not any(r.failed for r in results)


def test_require_cli_turns_missing_cli_into_failure(monkeypatch):
    monkeypatch.setattr(e2e_smoke.shutil, "which", lambda _cli: None)
    results = e2e_smoke.run(COM001, require_cli=True)
    pbir = _by_name(results)["pbir"]
    assert pbir.failed
    assert any(r.failed for r in results)


def test_tmdl_stage_falls_back_when_bash_absent(monkeypatch):
    """I-10.1: on plain Windows (no WSL/Git Bash), `bash` isn't on PATH — the TMDL
    stage must degrade to the structural fallback check, not crash with
    FileNotFoundError (WinError 2 on Windows)."""
    monkeypatch.setattr(e2e_smoke.shutil, "which", lambda _cli: None)
    results = e2e_smoke.run(COM001)
    tmdl_stage = _by_name(results)["tmdl"]
    assert tmdl_stage.status == "PASS"
    assert "bash absent" in tmdl_stage.detail
    assert not any(r.failed for r in results)


def test_resolve_bash_prefers_path_over_git_bash_fallback(monkeypatch):
    monkeypatch.setattr(e2e_smoke.shutil, "which", lambda _cli: "/usr/bin/bash")
    assert e2e_smoke.resolve_bash() == "/usr/bin/bash"


def test_resolve_bash_falls_back_to_git_for_windows_default_path(monkeypatch, tmp_path):
    """I-10.1 follow-up: Git for Windows' installer doesn't always add bash to
    PATH — resolve_bash() must still find it at the documented default location
    instead of reporting bash absent."""
    fake_git_bash = tmp_path / "Git" / "bin" / "bash.exe"
    fake_git_bash.parent.mkdir(parents=True)
    fake_git_bash.touch()

    monkeypatch.setattr(e2e_smoke.shutil, "which", lambda _cli: None)
    monkeypatch.setattr(e2e_smoke, "_GIT_BASH_FALLBACK_PATHS", [fake_git_bash])
    assert e2e_smoke.resolve_bash() == str(fake_git_bash)


def test_resolve_bash_returns_none_when_nothing_found(monkeypatch, tmp_path):
    monkeypatch.setattr(e2e_smoke.shutil, "which", lambda _cli: None)
    monkeypatch.setattr(e2e_smoke, "_GIT_BASH_FALLBACK_PATHS", [tmp_path / "nope" / "bash.exe"])
    assert e2e_smoke.resolve_bash() is None


def test_main_returns_one_for_missing_bracket(capsys):
    assert e2e_smoke.main([str(REPO / "does_not_exist.yaml")]) == 1
    assert "FAIL" in capsys.readouterr().out


def test_keep_writes_artifacts(tmp_path):
    e2e_smoke.run(COM001, keep=tmp_path)
    # TMDL semantic model + PBIR report were both materialized under keep dir.
    assert list(tmp_path.glob("*.SemanticModel/definition/tables/*.tmdl"))
    assert list(tmp_path.glob("*.Report/definition.pbir"))


def test_page_slots_is_a_hard_gate_and_can_actually_fail():
    """Der Slot-Gate ist seit 02.08.2026 hart — und das muss beweisbar sein.

    Er lief zwei Schritte lang bewusst advisory, damit er auf einem Repo landet, das
    ihn bestehen kann (39/40 Seiten hatten anfangs eine Luecke). Jetzt bestehen alle
    40. Ein Gate, das nur deshalb gruen ist, weil es nichts prueft, waere aber genau
    die Fehlerklasse, gegen die dieser Wachhund gebaut wurde — deshalb hier der
    Nachweis, dass ein fehlender Pflicht-Slot ihn ROT macht.
    """
    from tooling.superversion import e2e_smoke as m

    echt = m._stage_slots(COM001, m._KPIS)
    assert echt.status == "PASS", str(echt)

    def luecke(_bracket, _kpis):
        return [{"use_case": "X", "page": "page_2_execution", "variant": "T4_ActionDecision",
                 "missing": ["ActionPanel"], "emitted": ["Detail_Matrix"],
                 "raster": "action_matrix", "raster_default": False}]

    import tooling.superversion.from_aluca as fa
    original = fa.slot_luecken
    try:
        fa.slot_luecken = luecke
        rot = m._stage_slots(COM001, m._KPIS)
    finally:
        fa.slot_luecken = original
    assert rot.failed, "fehlender Pflicht-Slot macht den Gate nicht rot"
    assert "ActionPanel" in rot.detail


def test_manifest_gaps_stay_advisory_not_hard():
    """Eine Luecke im MANIFEST darf den Adapter nicht rot machen.

    Fehlt einer Variante das Raster fuer ihre Ebene, oder deklariert ein Bracket gar
    keine Variante, ist das Governance — nicht Emission. Den Adapter dafuer haften zu
    lassen, verschoebe die Schuld an die Stelle, die sie nicht beheben kann.
    """
    from tooling.superversion import e2e_smoke as m

    def rueckfall(_bracket, _kpis):
        return [{"use_case": "X", "page": "page_2_execution", "variant": "T1_Trend",
                 "missing": [], "emitted": ["Slicer_Pane"],
                 "raster": None, "raster_default": True}]

    import tooling.superversion.from_aluca as fa
    original = fa.slot_luecken
    try:
        fa.slot_luecken = rueckfall
        r = m._stage_slots(COM001, m._KPIS)
    finally:
        fa.slot_luecken = original
    assert r.status == "WARN" and not r.failed, str(r)
