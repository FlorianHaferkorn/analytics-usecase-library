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
    env["PYTHONIOENCODING"] = "utf-8"  # der Test liest UTF-8; unter Windows schriebe das Kind cp1252
    r = subprocess.run([sys.executable, "-m", "tooling.codegen.dax_smoke", "run", "--model", "Operations",
                        "--out", "/dev/null"], cwd=REPO, env=env, capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 2 and "nicht prüfbar" in r.stderr


# ------------------------------------------------------------------ RI je Beziehung (I-21 W5.12 b)

def test_every_relationship_of_every_model_has_one_ri_query():
    """Zweite Zählung: Dateien unter `relationships/` gegen die Einträge im Plan."""
    for m in sorted(ds.DIST.glob("*.SemanticModel")):
        dateien = sorted((m / "definition" / "relationships").glob("*.tmdl"))
        plan = _plan(m.name.removesuffix(".SemanticModel"))
        assert len(plan["beziehungen"]) == len(dateien) > 0, m.name
        for b in plan["beziehungen"]:
            assert b["erwartet"] == 0
            assert b["abfrage"].count("EXCEPT(DISTINCT(") == 1 and "VALUES" not in b["abfrage"]


_REL = """relationship r_sales_customer
\tfromColumn: fact_sales.CustomerKey
\ttoColumn: dim_customer.CustomerKey

relationship 'r quoted'
\tisActive: false
\tfromColumn: 'fact sales'.'Ship Date'
\ttoColumn: dim_date.DateKey

relationship r_many
\ttoCardinality: many
\tfromColumn: fact_sales.Region
\ttoColumn: dim_region.Region
"""


def _modell(tmp_path: Path) -> Path:
    m = tmp_path / "Fix.SemanticModel"
    (m / "definition" / "tables").mkdir(parents=True)
    (m / "definition" / "relationships.tmdl").write_text(_REL, encoding="utf-8")
    return m


def test_relationships_are_read_with_quotes_inactive_and_without_many_to_many(tmp_path):
    rel = {b["name"]: b for b in ds.beziehungen(_modell(tmp_path))}
    assert set(rel) == {"r_sales_customer", "r quoted"}
    assert rel["r quoted"]["aktiv"] is False
    assert rel["r quoted"]["abfrage"] == (
        "EVALUATE ROW(\"v\", COUNTROWS(EXCEPT(DISTINCT('fact sales'[Ship Date]), "
        "DISTINCT('dim_date'[DateKey]))) + 0)")


_RI = re.compile(r"EXCEPT\(DISTINCT\('((?:[^']|'')+)'\[([^\]]+)\]\), DISTINCT\('((?:[^']|'')+)'\[([^\]]+)\]\)\)")


def _motor(daten: dict[str, dict[str, list]]):
    """Rechnet genau die RI-Abfrageform auf Fixture-Daten nach (DISTINCT, EXCEPT, COUNTROWS + 0)."""
    def werte(q: str):
        m = _RI.search(q)
        f = set(daten[m.group(1)][m.group(2)])
        d = set(daten[m.group(3)][m.group(4)])
        return [len(f - d) + 0]
    return werte


_DATEN = {
    "fact_sales": {"CustomerKey": [1, 2, 2, 3]},
    "dim_customer": {"CustomerKey": [1, 2, 3]},
    "fact sales": {"Ship Date": [20260101]},
    "dim_date": {"DateKey": [20260101]},
}


def test_clean_keys_pass_the_ri_check(tmp_path):
    plan = ds.plan_fuer(_modell(tmp_path))
    lauf = ds.lauf(plan, "w", "d", "t", transport=_stub(_motor(_DATEN)))
    assert lauf["abfragen"] == 2
    assert ds.bewerten(plan, lauf) == []


def test_an_orphaned_key_turns_the_ri_check_red(tmp_path):
    plan = ds.plan_fuer(_modell(tmp_path))
    daten = {**_DATEN, "fact_sales": {"CustomerKey": [1, 2, 3, 99, 98]}}   # 99, 98 verwaist
    lauf = ds.lauf(plan, "w", "d", "t", transport=_stub(_motor(daten)))
    befunde = ds.bewerten(plan, lauf)
    assert [(b["measure"], b["befund"]) for b in befunde] == [
        ("fact_sales[CustomerKey] -> dim_customer[CustomerKey]", "verwaiste Schlüssel")]
    assert befunde[0]["detail"].startswith("2 Wert(e)")


def test_a_failed_or_skipped_ri_query_is_a_finding_not_a_pass(tmp_path):
    plan = ds.plan_fuer(_modell(tmp_path))
    lauf = ds.lauf(plan, "w", "d", "t", transport=_stub(lambda q: RuntimeError("DAX kaputt")))
    assert {b["befund"] for b in ds.bewerten(plan, lauf)} == {"RI: fehler"}
    lauf = ds.lauf(plan, "w", "d", "t", budget=0, transport=_stub(_motor(_DATEN)))
    assert {b["befund"] for b in ds.bewerten(plan, lauf)} == {"RI: budget"}


def test_orphan_fk_on_gold_parquet_agrees_on_the_same_fixture(tmp_path, monkeypatch):
    """Zweite Messung: `check_data_model.py` ORPHAN-FK liest dieselben Schlüssel aus Parquet."""
    import importlib.util

    import pyarrow as pa
    import pyarrow.parquet as pq
    spec = importlib.util.spec_from_file_location(
        "_check_data_model_ri", REPO / "tooling" / "validation" / "check_data_model.py")
    cdm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cdm)
    for sub, name, col, vals in (("facts", "fact_sales", "CustomerKey", [1, 2, 3, 99, 98]),
                                 ("dimensions", "dim_customer", "CustomerKey", [1, 2, 3])):
        (tmp_path / sub / name).mkdir(parents=True)
        pq.write_table(pa.table({col: vals}), tmp_path / sub / name / "part-0.parquet")
    monkeypatch.setattr(cdm, "GOLD", tmp_path)
    modell = {"facts": [{"domain": "fix", "name": "fact_sales", "refs": [("CustomerKey", "dim_customer")]}],
              "dims": [{"domain": "fix", "name": "dim_customer", "key": "CustomerKey"}]}
    orphan = cdm.check_referential_integrity(modell)
    assert len(orphan) == 1 and orphan[0].startswith("ORPHAN-FK") and ": 2 value(s)" in orphan[0]
