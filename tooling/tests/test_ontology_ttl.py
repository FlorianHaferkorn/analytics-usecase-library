"""
test_ontology_ttl.py — the library's business-object layer as a Fabric IQ ontology (Meridian D-617).

The emitter is Meridian's mirrored ``ontologie_kern``; these tests check the ALUCA inputs: one entity
type per business object, counts against the YAML, a clean import profile, KPI names from the
catalog, valid Turtle.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tooling.generator import business_objects as bo
from tooling.generator import ontology_ttl as ot
from tooling.superversion._dataarch_vendor import available

pytestmark = pytest.mark.skipif(not available(), reason="Meridian mirror unavailable")


@pytest.fixture(scope="module")
def built():
    return ot.build()


def test_counts_match_the_layer(built):
    _kern, model = built
    objects = bo.load()["business_objects"]
    assert len(model.klassen) == len(objects)
    assert len(model.eigenschaften) == sum(len(o["attributes"]) for o in objects)
    assert len(model.beziehungen) == sum(len(o["relationships"]) for o in objects)


def test_import_profile_is_clean(built):
    kern, model = built
    assert kern.profil_befunde(model) == []


def test_kpi_names_come_from_the_catalog(built):
    _kern, model = built
    names = ot.kpi_names()
    with_kpi = next(k for k in model.klassen if "Kennzahlen" in k.beschreibung)
    kid = with_kpi.beschreibung.split("Kennzahlen ", 1)[1].split(" ", 1)[0]
    assert f"{kid} ({names[kid]})" in with_kpi.beschreibung


def test_turtle_parses_and_names_aluca(built, tmp_path: Path):
    rdflib = pytest.importorskip("rdflib")
    out = tmp_path / "ontology.ttl"
    assert ot.main(["--out", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert "ALUCA Analytics Library — ALUCA-Ontologie" in text
    graph = rdflib.Graph().parse(data=text, format="turtle")
    assert len(graph) > 0


def test_check_mode_writes_nothing(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert ot.main(["--check"]) == 0
    assert list(tmp_path.iterdir()) == []
