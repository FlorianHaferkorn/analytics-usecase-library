"""DAX-Laufzeitprüfung (AP-4, 24.09.2026): Plan ohne Tenant, Lauf gegen einen Stub.

Der echte Lauf braucht ein veröffentlichtes Modell. Diese Tests halten fest, dass der Plan zum
Modell passt, dass die Klassen richtig vergeben sind und dass die Bewertung jede Abweichung
meldet, die sie melden soll.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tooling.codegen import dax_smoke as ds  # noqa: E402


def _plan(modell: str = "Operations") -> dict:
    return json.loads((ds.PLAN / f"{modell}.json").read_text(encoding="utf-8"))


def test_plans_match_the_shipped_models():
    assert ds.pruefe_plan() == [], "python -m tooling.codegen.dax_smoke plan --write"


def test_every_measure_of_every_model_is_planned():
    for m in sorted(ds.DIST.glob("*.SemanticModel")):
        plan = _plan(m.name.removesuffix(".SemanticModel"))
        assert {x["measure"] for x in plan["messungen"]} == set(ds.measures(m))


def test_one_measure_per_summarizecolumns():
    """Mehrere Measures in einer SUMMARIZECOLUMNS liefern still Nullen (Belegpflicht, Punkt 2)."""
    for f in ds.PLAN.glob("*.json"):
        for m in json.loads(f.read_text(encoding="utf-8"))["messungen"]:
            assert m["abfragen"]["je_monat"].count('"v"') == 1


def test_only_measures_on_the_empty_target_table_are_expected_blank():
    for f in ds.PLAN.glob("*.json"):
        for m in json.loads(f.read_text(encoding="utf-8"))["messungen"]:
            if m["klasse"] == "leer_begruendet":
                assert m["grund"].startswith("fact_target"), m
                assert re.search(r"\b(Target|Plan \(Target Table\))\b", m["measure"]), m["measure"]


def test_dependency_on_the_empty_table_is_followed_through_other_measures():
    """`<M> vs Target` nennt `fact_target` nicht selbst, sondern über `<M> Target`."""
    plan = _plan("Operations")
    vs = next(m for m in plan["messungen"] if m["measure"].endswith("% vs Target"))
    assert vs["klasse"] == "leer_begruendet"


def test_text_measures_are_allowed_blank():
    plan = _plan("Operations")
    assert all(m["klasse"] == "text" for m in plan["messungen"] if m["measure"].startswith("Action_"))


def _stub(werte_je_abfrage):
    def transport(url, kopf, koerper):
        assert kopf["Authorization"] == "Bearer t"
        antwort = werte_je_abfrage(koerper["queries"][0]["query"])
        if isinstance(antwort, Exception):
            raise antwort
        return {"results": [{"tables": [{"rows": [{"[v]": w} for w in antwort]}]}]}
    return transport


def _mini_plan():
    return {"modell": "X.SemanticModel", "quelle_sha256": "abc", "gegenproben": [], "messungen": [
        {"measure": "Umsatz", "klasse": "zahl", "abfragen": {"gesamt": "g1", "je_monat": "m1"}},
        {"measure": "Ziel", "klasse": "leer_begruendet", "abfragen": {"gesamt": "g2", "je_monat": "m2"}},
        {"measure": "Text", "klasse": "text", "abfragen": {"gesamt": "g3", "je_monat": "m3"}},
    ]}


def test_a_clean_run_has_no_findings():
    plan = _mini_plan()
    antworten = {"g1": [10.0], "m1": [4.0, 6.0], "g2": [None], "m2": [None, None], "g3": [None], "m3": [None]}
    lauf = ds.lauf(plan, "w", "d", "t", transport=_stub(antworten.get))
    assert ds.bewerten(plan, lauf, {"X.SemanticModel::Umsatz": 10.0}) == []


def test_each_kind_of_deviation_is_reported():
    plan = _mini_plan()
    antworten = {"g1": [9.0], "m1": [None], "g2": [1.0], "m2": [1.0], "g3": RuntimeError("DAX kaputt"), "m3": [None]}
    lauf = ds.lauf(plan, "w", "d", "t", transport=_stub(antworten.get))
    befunde = {(b["measure"], b["befund"]) for b in ds.bewerten(plan, lauf, {"X.SemanticModel::Umsatz": 10.0})}
    assert ("Umsatz", "kein Monat gefüllt") in befunde
    assert ("Umsatz", "Gegenprobe weicht ab") in befunde
    assert ("Ziel", "gefüllt, obwohl als leer begründet") in befunde
    assert ("Text", "gesamt: fehler") in befunde


def test_a_run_against_a_changed_model_is_refused():
    plan = _mini_plan()
    lauf = ds.lauf(plan, "w", "d", "t", transport=_stub(lambda q: [1.0]))
    lauf["quelle_sha256"] = "anders"
    assert ds.bewerten(plan, lauf)[0]["befund"].startswith("Lauf passt nicht")


def test_budget_stops_querying():
    plan = _mini_plan()
    lauf = ds.lauf(plan, "w", "d", "t", budget=2, transport=_stub(lambda q: [1.0]))
    assert lauf["abfragen"] == 2
    assert lauf["ergebnisse"][1]["gesamt"]["status"] == "budget"


def test_run_without_token_is_not_checkable(monkeypatch):
    env = {k: v for k, v in __import__("os").environ.items() if k != "POWERBI_ACCESS_TOKEN"}
    r = subprocess.run([sys.executable, "-m", "tooling.codegen.dax_smoke", "run", "--model", "Operations",
                        "--out", "/dev/null"], cwd=REPO, env=env, capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 2 and "nicht prüfbar" in r.stderr
