"""
test_business_objects_template.py — gap template of the business-object layer (Meridian D-610).

The template logic is mirrored from Meridian (``leerstellen_vorlage``); these tests run it on the
library layer: one row per counted gap, empty template is a no-op, filled values pass the gates,
invalid values and already-set fields are refused (all or nothing).
"""
from __future__ import annotations

import copy
import csv
import io
from pathlib import Path

import pytest

from tooling.generator import business_objects as bo
from tooling.superversion._dataarch_vendor import available, load_module

pytestmark = pytest.mark.skipif(not available(), reason="Meridian mirror unavailable")


@pytest.fixture(scope="module")
def lv():
    return load_module("leerstellen_vorlage")


@pytest.fixture()
def doc() -> dict:
    return copy.deepcopy(bo.load())


def test_one_row_per_counted_gap(lv, doc) -> None:
    rows = lv.zeilen(doc)
    assert len(rows) == sum(bo.gaps(doc).values())
    assert set(lv.ZUSTAENDIG) == set(bo.GAP_FIELDS)


def test_empty_template_changes_nothing(lv, doc) -> None:
    new, problems, n = lv.uebernehme(doc, lv.als_csv(lv.zeilen(doc)))
    assert (problems, n) == ([], 0) and new == doc


def test_filled_values_pass_the_gates_and_survive_merge(lv, doc) -> None:
    rows = lv.zeilen(doc)
    for r in rows:
        if r["feld"] in ("name.de", "name.en"):
            r["wert"] = "Test"
        elif r["feld"].endswith(".personal_data"):
            r["wert"] = "nein"
    new, problems, n = lv.uebernehme(doc, lv.als_csv(rows))
    assert problems == [] and n == sum(1 for r in rows if r["wert"])
    assert bo.check(new, bo.catalog_kpi_ids(), bo.physical_columns()) == []
    assert sum(bo.gaps(new).values()) == sum(bo.gaps(doc).values()) - n
    assert bo.dump(bo.merge(bo.derive(), new)) == bo.dump(new)


def test_set_field_is_not_overwritten(lv, doc) -> None:
    o = next(o for o in doc["business_objects"] if o.get("description"))
    row = {**dict.fromkeys(lv.SPALTEN, ""), "objekt_id": o["id"], "feld": "description", "wert": "x"}
    new, problems, n = lv.uebernehme(doc, lv.als_csv([row]))
    assert problems and n == 0 and new == doc


def test_invalid_personal_data_is_refused(lv, doc) -> None:
    row = next(r for r in lv.zeilen(doc) if r["feld"].endswith(".personal_data"))
    for w in ("ja", "ja:invented", "maybe"):
        assert lv.uebernehme(doc, lv.als_csv([{**row, "wert": w}]))[1], w


def test_cli_writes_the_template(tmp_path: Path) -> None:
    out = tmp_path / "gaps.csv"
    assert bo.main(["--template", str(out)]) == 0
    rows = list(csv.DictReader(io.StringIO(out.read_text(encoding="utf-8"))))
    assert len(rows) == sum(bo.gaps(bo.load()).values())
