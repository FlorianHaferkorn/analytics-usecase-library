"""Integritaet der Boutique-Craft-Rubrik — sagt sie die Wahrheit ueber sich selbst?

Anlass (03.08.2026): die Frage war nicht, ob unser System so AUSSIEHT wie IBCS, sondern
ob es qualitativ auf dem Niveau eines anerkannten Standards ist. Was einen Standard von
einer Sammlung guter Ratschlaege unterscheidet, ist nachpruefbar — und genau das wird
hier nachgeprueft:

  1. Eine Regel steht an EINER Stelle (keine Dublette mit widersprechender Severity).
  2. Was eine Regel ueber sich behauptet, stimmt (`structural` ⇒ ein Validator ist
     benannt und existiert; `judge` ⇒ keiner).
  3. Ein benannter Validator kann SCHEITERN. Ein Checker, der immer 0 zurueckgibt,
     erzeugt einen Haken ohne Pruefung — die Fehlerklasse, die in diesem Repo
     wiederholt aufgetreten ist (RequiredSlots §12, Slot-Watchdog, Drift-Guards).
  4. Die offenen Luecken sind gezaehlt, damit sie nicht still wachsen.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
_RUBRIC = REPO / "core/templates/page_templates/tokens/boutique_craft_rubric.yaml"
_DESIGN = REPO / "core/templates/page_templates/design_rules.yaml"
_VALID = REPO / "tooling/validation"


def _rules():
    doc = yaml.safe_load(_RUBRIC.read_text(encoding="utf-8"))
    return [r for dim in doc["dimensions"] for r in dim["rules"]]


def test_declared_check_kind_is_true():
    """`structural`/`both` ⇒ Validator benannt ODER als blockiert vermerkt; `judge` ⇒ keiner."""
    for r in _rules():
        art, val = r.get("check"), r.get("validator")
        if art == "judge":
            assert not val, (
                f"{r['id']}: als `judge` deklariert, aber ein Validator entscheidet es. "
                f"Dann ist die Deklaration tot — die Scorecard verwirft das Judge-Urteil.")
        elif art == "both":
            assert val, f"{r['id']}: `both` ohne Validator ist einfach `judge`"
        elif art == "structural":
            assert val or r.get("validator_blocked"), (
                f"{r['id']}: behauptet maschinelle Pruefbarkeit, nennt aber weder einen "
                f"Validator noch einen Grund (`validator_blocked`).")
        else:
            pytest.fail(f"{r['id']}: unbekannte check-Art {art!r}")


def test_named_validators_exist():
    for r in _rules():
        if v := r.get("validator"):
            assert (_VALID / v["script"]).is_file(), f"{r['id']}: {v['script']} fehlt"


def test_wired_validators_can_actually_fail():
    """Ein verdrahteter Validator MUSS einen Nichtnull-Pfad haben.

    Sonst ist die Regel per Konstruktion bestanden. Genau daran waere diese Arbeit
    beinahe gescheitert: `check_tabular_numerals.py` und `check_reference_lines.py`
    tragen ihre Regel-ID im Kopf und sahen nach fertigen Checkern aus — sie beenden
    aber immer mit 0 ('Advisory only — never gates'). Verdrahtet haetten sie die
    Abdeckung um zwei Regeln erhoeht, ohne irgendetwas zu pruefen.
    """
    for r in _rules():
        if not (v := r.get("validator")):
            continue
        quelle = (_VALID / v["script"]).read_text(encoding="utf-8")
        assert re.search(r"return 1|sys\.exit\(1\)|exit\(1\)", quelle), (
            f"{r['id']}: {v['script']} hat keinen Nichtnull-Pfad — die Regel waere "
            f"per Konstruktion bestanden.")
        assert "never gates" not in quelle, (
            f"{r['id']}: {v['script']} bezeichnet sich selbst als advisory "
            f"('never gates') und kann die Regel nicht entscheiden.")


def test_no_rule_is_stated_twice():
    """Dieselbe Regel darf nicht in zwei Speichern mit zwei Severities stehen.

    Gemessen am 03.08.2026: `MAX_SEMANTIC_COLORS_PER_PAGE` (design_rules, warning) und
    `BC-COLOR-04` (Rubrik, minor) sind wortgleich dieselbe Zusage aus derselben Quelle;
    `ONE_MESSAGE_PER_CHART` (critical) und `BC-CHART-01` (knock_out) ebenso — letztere
    sogar mit ZWEI unabhaengigen Checkern. Wer eine Dublette aufloest, verweist die
    design_rules-Seite per `implements` auf die Rubrik, statt die Aussage zu wiederholen.
    """
    design = yaml.safe_load(_DESIGN.read_text(encoding="utf-8"))
    ohne_verweis = [r["id"] for r in design["rules"]
                    if r["id"] in _BEKANNTE_DUBLETTEN and not r.get("implements")]
    assert not ohne_verweis, (
        f"Dublette ohne `implements`-Verweis auf die Rubrik: {ohne_verweis}")


#: Die beiden gemessenen Dubletten. Als benannte Liste, damit eine NEUE auffaellt,
#: statt in ihnen unterzugehen — dasselbe Muster wie bei den Varianten-Signaturen.
_BEKANNTE_DUBLETTEN = {"MAX_SEMANTIC_COLORS_PER_PAGE", "ONE_MESSAGE_PER_CHART"}


def test_open_gaps_are_counted_not_creeping():
    """Die offenen Luecken sind gezaehlt. Waechst eine, wird das hier rot.

    Kein Qualitaetsurteil — eine Bremse. Ein System, dessen ungeprueftes Drittel still
    waechst, verliert sein Niveau, ohne dass jemand es merkt.
    """
    rs = _rules()
    ohne_validator = [r["id"] for r in rs
                      if r.get("check") in ("structural", "both") and not r.get("validator")]
    assert len(ohne_validator) == 5, (
        f"{len(ohne_validator)} structural-Regeln ohne Validator (erwartet 5): "
        f"{sorted(ohne_validator)}. Weniger = Fortschritt, Zahl anpassen. Mehr = eine "
        f"neue Regel behauptet Pruefbarkeit, ohne sie zu liefern.")
