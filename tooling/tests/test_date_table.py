"""dim_date ist die markierte Datumstabelle, der Vorjahresvergleich rechnet darauf (13.11.2026).

Entscheidung Florian 12.11.2026: ``dim_date`` als Datumstabelle markieren (``dataCategory: Time`` an
der Tabelle, ``isKey`` an ``Date``) und den Vorjahresvergleich von einem Monatsindex-Shift auf
``SAMEPERIODLASTYEAR`` umstellen. Die Markierung schreibt ``tooling/codegen/model_alignment.py``, die
PY-Measures ``tooling/codegen/comparison_measures.py``. Diese Tests halten beides an den
ausgelieferten Modellen fest und prüfen die Schutzregeln.

Nicht gemessen ist die DAX-Laufzeit: ohne Desktop und ohne Tenant rechnet hier keine Engine. Was die
Tests belegen, ist die Form (Markierung, Ausdruck, Schutz) und, gegen die Datenscheibe, dass Gold die
Bedingungen erfüllt, die Power BI beim Markieren selbst prüft (eindeutig, ohne Null, lückenlos).
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tooling.codegen import comparison_measures as cm  # noqa: E402
from tooling.codegen import model_alignment as ma  # noqa: E402
from showcases.aurora_group.data import showdaten  # noqa: E402

braucht_showdaten = showdaten.pytest_markierung()

MODELLE = sorted(ma.DIST.glob("*.SemanticModel"))


def _dim_date(modell: Path) -> str:
    return (modell / "definition" / "tables" / "dim_date.tmdl").read_text(encoding="utf-8")


def test_the_suite_sees_all_five_models_with_a_date_table():
    """Die Schleife unten prüft so viele Modelle, wie es gibt; eine leere Schleife wäre kein Erfolg."""
    assert [m.name for m in MODELLE] == ["Commercial.SemanticModel", "Experience.SemanticModel",
                                         "Finance.SemanticModel", "Operations.SemanticModel",
                                         "SupplyChain.SemanticModel"]
    assert ma.date_table_models() == [m.name.removesuffix(".SemanticModel") for m in MODELLE]


@pytest.mark.parametrize("modell", MODELLE, ids=lambda m: m.name)
def test_every_model_marks_dim_date_as_its_date_table(modell):
    text = _dim_date(modell)
    assert len(re.findall(r"^\tdataCategory: Time$", text, re.M)) == 1
    schluessel = [k.group(1) for k in re.finditer(r"^\tcolumn (.+)\n((?:\t\t.*\n)*)", text, re.M)
                  if "\t\tisKey\n" in k.group(2)]
    assert schluessel == ["Date"]                       # genau eine Schlüsselspalte, die Datumsspalte
    assert ma.is_date_table_marked(text)
    assert re.search(r"^\t\tisHidden$", ma._column_block(text, "Date").group(0), re.M) is None  # bleibt sichtbar


def test_marking_is_idempotent_and_leaves_the_rest_untouched():
    text = _dim_date(MODELLE[0])
    assert ma.mark_date_table(text, "t") == text
    ohne = text.replace("\tdataCategory: Time\n", "").replace("\t\tisKey\n", "")
    assert ma.mark_date_table(ohne, "t") == text        # Rückweg: genau die zwei Zeilen kommen zurück


def test_marking_refuses_instead_of_guessing():
    kopf = "table dim_date\n\tcolumn {n}\n\t\tdataType: {t}\n\t\tsourceColumn: Date\n"
    with pytest.raises(ValueError, match="fehlt"):
        ma.mark_date_table(kopf.format(n="Datum", t="DateTime"), "t")
    with pytest.raises(ValueError, match="kein DateTime"):
        ma.mark_date_table(kopf.format(n="Date", t="String"), "t")
    zwei = kopf.format(n="Date", t="DateTime") + "\tcolumn DateKey\n\t\tdataType: Int64\n\t\tisKey\n"
    with pytest.raises(ValueError, match="DateKey trägt schon isKey"):
        ma.mark_date_table(zwei, "t")


def test_desktop_spelling_of_the_type_is_accepted():
    """Commercial wurde in Desktop gespeichert und schreibt ``dateTime``; das ist dasselbe TOM-Merkmal."""
    text = "table dim_date\n\tcolumn Date\n\t\tdataType: dateTime\n\t\tsourceColumn: Date\n"
    assert ma.is_date_table_marked(ma.mark_date_table(text, "t"))


def test_alignment_no_longer_reports_drift_for_the_date_table():
    assert ma.pruefe() == [], "python -m tooling.codegen.model_alignment --write"


# --- Vorjahresvergleich ------------------------------------------------------------------

def _py_measures() -> list[tuple[str, str]]:
    """(Modell, Ausdruck) jeder vom Generator erzeugten ``... PY``-Measure."""
    out = []
    for m in MODELLE:
        text = (m / "definition" / "tables" / "_Measures.tmdl").read_text(encoding="utf-8")
        for block in re.split(r"\n(?=\t(?:///|measure ))", text):
            name = re.search(r"^\tmeasure '([^']+ PY)' = (.*)$", block, re.M)
            erzeugt = f'annotation {cm.MARKE} = "comparison_measures"' in block
            if name and erzeugt and not name.group(1).endswith(" vs PY"):
                out.append((m.name, name.group(2)))
    return out


def test_generated_py_measures_use_sameperiodlastyear_on_the_marked_date_column():
    py = _py_measures()
    assert len(py) == 1, "CLV PY in Commercial ist heute die einzige erzeugte PY-Measure (COM-003)"
    for modell, ausdruck in py:
        soll = r"CALCULATE \( \[[^\]]+\], SAMEPERIODLASTYEAR \( 'dim_date'\[Date\] \) \)"
        assert re.fullmatch(soll, ausdruck), (modell, ausdruck)
        assert "MonthNumber" not in ausdruck and "REMOVEFILTERS" not in ausdruck


def test_every_time_intelligence_measure_sits_in_a_model_with_a_marked_date_table():
    """Zweite Messung: nicht nur die erzeugten, jede Measure mit Vorjahresfunktion braucht die Markierung."""
    muster = re.compile(r"\b(SAMEPERIODLASTYEAR|DATEADD|PARALLELPERIOD|DATESYTD|TOTALYTD|PREVIOUSYEAR)\s*\(")
    gefunden = 0
    for m in MODELLE:
        for f in (m / "definition" / "tables").glob("*.tmdl"):
            if muster.search(f.read_text(encoding="utf-8")):
                gefunden += 1
                assert ma.is_date_table_marked(_dim_date(m)), f"{m.name}/{f.name}"
    assert gefunden == 1


def test_the_generator_refuses_an_unmarked_date_table(tmp_path, monkeypatch):
    """Gegenprobe der Schutzregel: ein Modell ohne Markierung bekommt keine SAMEPERIODLASTYEAR-Measure."""
    ziel = tmp_path / "Commercial.SemanticModel"
    shutil.copytree(ma.DIST / "Commercial.SemanticModel", ziel)
    p = ziel / "definition" / "tables" / "dim_date.tmdl"
    p.write_text(p.read_text(encoding="utf-8").replace("\tdataCategory: Time\n", "").replace("\t\tisKey\n", ""),
                 encoding="utf-8", newline="\n")
    monkeypatch.setattr(cm, "DIST", tmp_path)
    v = cm.Vergleich(model="Commercial.SemanticModel", kpi_id="KPI-COM-025", measure="X", art="vs_py")
    with pytest.raises(ValueError, match="keine markierte Datumstabelle"):
        cm.measures_fuer(v, "ratio", None)


def test_the_generator_accepts_a_marked_date_table():
    v = cm.Vergleich(model="Commercial.SemanticModel", kpi_id="KPI-COM-025", measure="X", art="vs_py")
    bloecke = cm.measures_fuer(v, "ratio", None)
    assert any("SAMEPERIODLASTYEAR ( 'dim_date'[Date] )" in b for b in bloecke)


# --- Gold gegen die Bedingungen, die Power BI beim Markieren prüft ---------------------------

@braucht_showdaten
def test_gold_dim_date_meets_the_marking_requirements():
    """Eindeutig, ohne Null, lückenlos, ein Tag je Zeile, gleicher Zeitstempel (Microsoft Learn,
    „Set and use date tables in Power BI Desktop“). Zweite Messung zu den Modellen: Gold selbst."""
    import pyarrow.parquet as pq
    from scripts.check_showcase_delta import _active_paths
    ordner = REPO / "showcases/aurora_group/data/gold/dimensions/dim_date"
    dateien = [ordner / p for p in _active_paths(str(ordner / "_delta_log"))]
    assert dateien, "keine aktive Datei: die Prüfung wäre leer"
    tage = sorted(d for f in dateien for d in pq.read_table(f, columns=["Date"]).column("Date").to_pylist())
    assert len(tage) > 365 and all(d is not None for d in tage)
    assert len(set(tage)) == len(tage), "Date ist nicht eindeutig"
    assert all(d.hour == d.minute == d.second == 0 for d in tage), "Date trägt einen Zeitanteil"
    luecken = [(a, b) for a, b in zip(tage, tage[1:]) if (b - a).days != 1]
    assert luecken == [], f"Date ist nicht lückenlos: {luecken[:3]}"
