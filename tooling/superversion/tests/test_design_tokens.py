"""Tests fuer den DTCG-Emitter (L5).

Der Schwerpunkt liegt auf der Abdeckungspruefung. Beim ersten Lauf hat der Emitter
still drei von zehn Gruppen verloren — `type_scale` statt `scale`, verschachteltes
`spacing` statt flacher Felder — und trotzdem „OK" gemeldet. Ein Emitter, der nichts
findet, darf nicht wie einer aussehen, der nichts zu tun hat.
"""
from __future__ import annotations

import json

import pytest

from tooling.superversion.layer_tools import design_tokens as dt


def test_emission_covers_every_mandatory_group():
    doc = dt.build()
    for gruppe in dt._PFLICHTGRUPPEN:
        assert gruppe in doc, f"Pflichtgruppe fehlt: {gruppe}"
        eintraege = [k for k in doc[gruppe] if not k.startswith("$")]
        assert eintraege, f"Pflichtgruppe leer: {gruppe}"


def test_coverage_check_fires_when_a_source_key_moves(monkeypatch):
    """Der Waechter selbst — nicht nur sein Ergebnis.

    Simuliert genau den Fehler von vorhin: eine YAML-Struktur aendert sich, der
    Emitter findet die Gruppe nicht mehr. Ohne diesen Test waere die stille
    Teil-Emission wieder moeglich.
    """
    echt = dt._load

    def ohne_scale(name):
        daten = echt(name)
        if name == "typography.yaml":
            daten = {k: v for k, v in daten.items() if k != "scale"}
        return daten

    monkeypatch.setattr(dt, "_load", ohne_scale)
    with pytest.raises(dt.TokenError) as exc:
        dt.build()
    assert "fontSize" in str(exc.value)


def test_committed_dtcg_file_is_not_stale():
    """Die eingecheckte Fassung muss zu den YAML-Quellen passen (Drift-Gate)."""
    assert dt.main([]) == 0, "DTCG-Datei veraltet — `--write` ausfuehren"


def test_emitted_json_is_valid_dtcg_shape():
    """Struktur-Zusicherungen der DTCG-Spec, soweit wir sie beanspruchen."""
    doc = json.loads(dt.render())
    for name, gruppe in doc.items():
        if name.startswith("$"):
            continue
        for schluessel, token in gruppe.items():
            if schluessel.startswith("$"):
                continue
            assert isinstance(token, dict), f"{name}.{schluessel} ist kein Objekt"
            # ibcsScenario traegt bewusst keinen $type und keine $value — es ist
            # Fuellmuster-Notation, fuer die DTCG keinen Typ kennt.
            if name != "ibcsScenario":
                assert "$value" in token, f"{name}.{schluessel} ohne $value"


def test_ibcs_scenario_carries_no_invented_type():
    """Wo DTCG keinen Typ hat, wird keiner erfunden."""
    doc = dt.build()
    assert "$type" not in doc["ibcsScenario"]
    assert set(doc["ibcsScenario"]) >= {"ac", "pl", "fc", "py"}
