"""Prognose-Measures aus den Forecast-Ausloesern (C-M2.4, ADR-0028 §7 Nachtrag, 30.10.2026).

`tooling/codegen/forecast_measures.py` erzeugt Punkt, unteren und oberen Rand; die Tests halten
das ausgelieferte Modell daran fest und pruefen, dass `action_trigger_dax` den Ausloeser damit
erzeugen kann (ohne die Measures: Fehler).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tooling.codegen import action_trigger_dax as atd  # noqa: E402
from tooling.codegen import comparison_measures as cm  # noqa: E402
from tooling.codegen import forecast_measures as fm  # noqa: E402

COM = fm.DIST / "Commercial.SemanticModel"


def test_the_forecast_trigger_is_read_from_the_action_code():
    ps = fm.prognosen()
    assert [(p.code, p.kpi_id, p.level) for p in ps] == [("C-M2.4", "KPI-COM-033", 0.8)]
    p = ps[0]
    assert (p.punkt, p.unten, p.oben) == ("Private Label Penetration % Forecast",
                                          "Private Label Penetration % Forecast Lower",
                                          "Private Label Penetration % Forecast Upper")


def test_models_carry_exactly_the_generated_forecast_layer():
    assert fm.pruefe() == [], "python -m tooling.codegen.forecast_measures --write"


def _measure(text: str, name: str) -> str:
    m = re.search(rf"^\tmeasure '{re.escape(name)}' = (.*)$", text, re.M)
    assert m, name
    return m.group(1)


def test_the_dax_follows_the_decided_method():
    """Punkt = Mittel der letzten 3 Monate; Band = Punkt + 10./90. Perzentil der Ein-Monats-Fehler
    der letzten 24 Monate, mindestens 12 Fehler (Entscheidung 30.10.2026)."""
    text = (COM / "definition/tables/_Measures.tmdl").read_text(encoding="utf-8")
    punkt = _measure(text, "Private Label Penetration % Forecast")
    assert "GENERATESERIES ( _idx - 2, _idx )" in punkt and "= 3, AVERAGEX ( _v, [@v] )" in punkt
    assert "[Private Label Penetration %]" in punkt
    for name, q in (("Private Label Penetration % Forecast Lower", "0.1"),
                    ("Private Label Penetration % Forecast Upper", "0.9")):
        d = _measure(text, name)
        assert "GENERATESERIES ( _idx - 23, _idx )" in d
        assert "GENERATESERIES ( _k - 3, _k - 1 )" in d
        assert ">= 12" in d and f"PERCENTILEX.INC ( _e, [@e], {q} )" in d
        assert "VAR _p = [Private Label Penetration % Forecast]" in d
    assert text.count('annotation ALUCA_Generated = "forecast_measures"') == 3


def test_forecast_names_stay_outside_the_comparison_exemption():
    """Die Prognose-Measures sind keine Vergleichs-Measures: das Namensmuster der Drift-Checks
    (comparison_measures.ABGELEITET) darf sie nicht treffen."""
    for p in fm.prognosen():
        for n in (p.punkt, p.unten, p.oben):
            assert not cm.ABGELEITET.match(n), n


def test_insertion_is_stable_next_to_the_comparison_layer():
    text = (COM / "definition/tables/_Measures.tmdl").read_text(encoding="utf-8")
    # beide Generatoren nacheinander, in beiden Reihenfolgen: keiner verschiebt den anderen
    ps, loader = fm.prognosen(), cm._loader()
    assert fm.soll(COM, ps, loader) == text
    assert cm._einfuegen(text, cm.soll_measures(COM, *cm.vergleiche()[:1], cm._katalog())) == text
    i_f = text.index('annotation ALUCA_Generated = "forecast_measures"')
    i_c = text.index('annotation ALUCA_Generated = "comparison_measures"')
    assert i_f < i_c


def _kontext():
    loader = atd._loader()
    namen = loader.measure_map_for_model(COM)
    definiert = set(loader._model_symbols_for_dir(COM).measure_names)
    return namen, definiert


def test_action_trigger_dax_can_build_the_forecast_trigger():
    namen, definiert = _kontext()
    dax, offen = atd.dax_fuer(atd.action_codes()["C-M2.4"], namen, atd._kpi_formate(), definiert, atd._kpi_plan())
    assert dax.startswith("VAR _v0 = [Private Label Penetration % Forecast Lower]")
    assert "persistence" in offen  # Persistenz eines Forecast-Ausloesers wird nicht ausgewertet


def test_without_the_forecast_measures_the_trigger_is_an_error():
    namen, definiert = _kontext()
    ohne = definiert - {p.unten for p in fm.prognosen()}
    with pytest.raises(atd.Fehler, match="Prognose-Measure"):
        atd.dax_fuer(atd.action_codes()["C-M2.4"], namen, atd._kpi_formate(), ohne, atd._kpi_plan())
