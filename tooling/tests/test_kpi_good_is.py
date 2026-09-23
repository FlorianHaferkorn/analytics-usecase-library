"""`good_is` im KPI-Katalog passt zu den Action-Codes (R6.3, 23.09.2026).

Die Richtung einer KPI steht an zwei Stellen: im Katalog (`good_is`) und implizit im
Vergleichsoperator jedes Action-Codes, der auf sie triggert (`lt` heisst: zu niedrig ist
schlecht). Widersprechen sich beide, sortiert der Report anders, als die Aktion ausloest.
"""
from __future__ import annotations

from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
KPIS = REPO / "core" / "kpi_catalog" / "kpis"
ACTION_CODES = REPO / "core" / "action_codes"

AUS_OPERATOR = {"lt": "higher", "lte": "higher", "gt": "lower", "gte": "lower",
                "lt_or_gt_band": "band", "abs_gt": "zero"}
ERLAUBT = {"higher", "lower", "band", "zero"}


def _katalog() -> dict[str, dict]:
    out = {}
    for f in sorted(KPIS.glob("*.yaml")):
        d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        if d.get("kpi_id"):
            out[d["kpi_id"]] = d
    return out


def _aus_action_codes() -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for f in sorted(ACTION_CODES.glob("*/*.yaml")):
        if f.name.endswith("_business_case.yaml"):
            continue
        d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        for lvl in (((d.get("trigger") or {}).get("levels")) or {}).values():
            c = (lvl or {}).get("condition") or {}
            if c.get("metric_kpi_id") in (None, "") or c.get("comparator") not in AUS_OPERATOR:
                continue
            out.setdefault(c["metric_kpi_id"], set()).add(AUS_OPERATOR[c["comparator"]])
    return out


def test_good_is_uses_the_governed_vocabulary():
    falsch = {k: d["good_is"] for k, d in _katalog().items() if "good_is" in d and d["good_is"] not in ERLAUBT}
    assert falsch == {}


def test_good_is_agrees_with_every_action_code_that_triggers_on_the_kpi():
    kat = _katalog()
    widerspruch = []
    for kid, richtungen in sorted(_aus_action_codes().items()):
        if kid not in kat:
            continue
        assert len(richtungen) == 1, f"{kid}: Action-Codes widersprechen sich selbst: {richtungen}"
        if kat[kid].get("good_is") != next(iter(richtungen)):
            widerspruch.append((kid, kat[kid].get("good_is"), richtungen))
    assert widerspruch == []


def test_a_kpi_an_action_triggers_on_always_carries_a_direction():
    """Eine Aktion, die bei `< Schwelle` ausloest, kennt die Richtung. Der Katalog muss sie auch
    kennen, sonst sortiert der Report ein Rangdiagramm nach Groesse statt nach Handlungsbedarf."""
    kat = _katalog()
    ohne = sorted(k for k in _aus_action_codes() if k in kat and "good_is" not in kat[k])
    assert ohne == []


def test_benchmark_direction_agrees_with_good_is():
    """Das Benchmark-Register fuehrt eine eigene `direction` -- eine dritte Quelle derselben Aussage."""
    doc = yaml.safe_load((REPO / "core/kpi_catalog/benchmarks.yaml").read_text(encoding="utf-8")) or {}
    bm = doc.get("benchmarks", []) if isinstance(doc, dict) else doc
    assert len(bm) >= 10                     # sonst prueft der Test ins Leere
    kurz = {"higher_is_better": "higher", "lower_is_better": "lower"}
    kat = _katalog()
    widerspruch = [(b["kpi_id"], b.get("direction"), kat.get(b["kpi_id"], {}).get("good_is"))
                   for b in bm if b.get("direction") in kurz
                   and kat.get(b["kpi_id"], {}).get("good_is") != kurz[b["direction"]]]
    assert widerspruch == []
