"""AP-9: ein Einstieg über S0 bis S7. Geprüft wird die Ablaufsemantik, nicht die Werkzeuge selbst.

Der Runner ist ersetzt: jeder Aufruf wird protokolliert, Rückgabewerte sind vorgegeben. So lässt
sich zeigen, dass Tenant-Schritte ohne ``--apply`` nie aufgerufen werden, dass fehlende
Zugangsdaten vor dem Aufruf stoppen und dass ein Befund Exit 1 ergibt, nicht Exit 2.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tooling.agentic_loop import schleife as sl  # noqa: E402

LOKAL = {"S0", "S1", "S2"}


def _runner(rc_je_name=None):
    aufrufe = []

    def run(argv, cwd):
        aufrufe.append(argv)
        name = next((k for k in (rc_je_name or {}) if any(k in a for a in argv)), None)
        return (rc_je_name or {}).get(name, 0), ""
    run.aufrufe = aufrufe
    return run


@pytest.fixture()
def schritte(tmp_path):
    return sl.plan("OPS-001", "run-0001", tmp_path)


def test_plan_names_every_stage_and_resolves_the_model(schritte):
    assert {s.stufe for s in schritte} == set(sl.STUFEN)
    bericht, modell = sl.bericht_und_modell("OPS-001")
    assert bericht.name.startswith("OPS-001_") and modell.name == "Operations.SemanticModel"


def test_dry_run_never_calls_a_tenant_step(schritte):
    run = _runner()
    lauf = sl.ausfuehren(schritte, set(sl.STUFEN), False, sl.Lauf("OPS-001", "r", False), run)
    aufgerufen = " ".join(" ".join(a) for a in run.aufrufe)
    assert "sandbox.py" not in aufgerufen
    tenant = [e for e in lauf.ergebnisse if e.name.startswith("sandbox_")]
    assert tenant and all(e.status == "nicht_pruefbar" and "--apply" in e.grund for e in tenant)
    assert lauf.exit == 2


def test_apply_without_credentials_stops_before_the_call(schritte, monkeypatch):
    for n in sl.ZUGANG:
        monkeypatch.delenv(n, raising=False)
    run = _runner()
    lauf = sl.ausfuehren(schritte, {"S3", "S7"}, True, sl.Lauf("OPS-001", "r", True), run)
    assert not any("sandbox.py" in " ".join(a) for a in run.aufrufe)
    assert all("Zugangsdaten fehlen" in e.grund for e in lauf.ergebnisse if e.name.startswith("sandbox_"))


def test_a_finding_wins_over_not_checkable(schritte):
    lauf = sl.ausfuehren(schritte, set(sl.STUFEN), False, sl.Lauf("OPS-001", "r", False),
                         _runner({"report_quality": 1}))
    assert [e.name for e in lauf.ergebnisse if e.status == "befund"] == ["report_quality"]
    assert lauf.exit == 1


def test_only_local_stages_all_green_exits_zero(schritte):
    lauf = sl.ausfuehren(schritte, LOKAL, False, sl.Lauf("OPS-001", "r", False), _runner())
    assert lauf.exit == 0 and {e.stufe for e in lauf.ergebnisse} == LOKAL


def test_unbuilt_steps_say_so_instead_of_passing(schritte):
    lauf = sl.ausfuehren(schritte, {"S4", "S5"}, True, sl.Lauf("OPS-001", "r", True), _runner())
    assert all(e.status == "nicht_pruefbar" and e.grund.startswith("noch nicht gebaut") for e in lauf.ergebnisse)


def test_image_check_without_renders_is_not_checkable(schritte):
    lauf = sl.ausfuehren(schritte, {"S6"}, False, sl.Lauf("OPS-001", "r", False), _runner())
    assert lauf.ergebnisse[0].status == "nicht_pruefbar"


def test_staging_copies_exactly_report_and_model(tmp_path):
    bericht, modell = sl.bericht_und_modell("OPS-001")
    rc, _ = sl._bereitstellen(bericht, modell, tmp_path / "pbip")
    assert rc == 0 and sorted(p.name for p in (tmp_path / "pbip").iterdir()) == sorted([bericht.name, modell.name])
    pbir = json.loads((tmp_path / "pbip" / bericht.name / "definition.pbir").read_text(encoding="utf-8"))
    assert (tmp_path / "pbip" / bericht.name / pbir["datasetReference"]["byPath"]["path"]).resolve().is_dir()


def test_cli_writes_the_findings_file(tmp_path, monkeypatch):
    monkeypatch.setattr(sl, "subprocess_runner", _runner())
    monkeypatch.setattr(sl.ausfuehren, "__defaults__", (_runner(),))
    rc = sl.main(["--use-case", "OPS-001", "--run-id", "run-0001", "--stages", "S0", "--arbeit", str(tmp_path)])
    befunde = json.loads((tmp_path / "befunde.json").read_text(encoding="utf-8"))
    assert rc == befunde["exit"] == 0 and [e["name"] for e in befunde["ergebnisse"]] == ["check_index", "usecase_quality"]


def test_real_subprocess_output_with_non_utf8_bytes_keeps_exit_code():
    script = "import sys; sys.stdout.buffer.write(bytes([0x97])); sys.stderr.write('tool failed'); sys.exit(7)"
    rc, output = sl.subprocess_runner([sys.executable, "-c", script], REPO)
    assert rc == 7
    assert "\ufffd" in output
    assert "tool failed" in output
