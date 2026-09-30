"""Speichermodus je Mandant (Meridian D-590) im dist-Codegen: beide Modi, Abbruch statt Mischen.

Die Regel ist Meridians ``storage_mode.py`` (gespiegelt). Hier wird gezeigt, dass ALUCA sie
zieht, dass ``dist/`` ohne Bauplan im bisherigen Modus (Import) bleibt und dass Direct Lake on
OneLake nicht still in ein Import-Modell gemischt wird.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from tooling.codegen import comparison_measures as CM
from tooling.codegen import model_alignment as MA
from tooling.codegen import speichermodus as SM

REPO = Path(__file__).resolve().parents[2]
DIST = REPO / "products" / "fabric" / "powerbi" / "dist"


def test_ohne_bauplan_bleibt_dist_im_import():
    dl, imp = SM.konstanten()
    assert SM.mandant_modus(None) == imp
    assert SM.mandant_modus({}) == imp
    assert SM.mandant_modus({"platform": {"stack": "fabric"}}) == dl
    assert SM.mandant_modus({"platform": {"stack": "fabric"},
                             "medallion": {"platinum": {"storage_mode": "import"}}}) == imp


def test_bauplan_datei_wird_gelesen(tmp_path):
    p = tmp_path / "bp.json"
    p.write_text(json.dumps({"blueprint": {"platform": {"stack": "fabric"}}}), encoding="utf-8")
    assert SM.mandant_modus(SM.lade_bauplan(p)) == SM.konstanten()[0]


def test_import_regeneration_ist_diff_frei():
    """Der Akzeptanztest: dist bleibt, wie es ist (beide Codegen-Module, Modus Import)."""
    imp = SM.konstanten()[1]
    assert MA.pruefe(False, imp) == []
    drift, _ = CM.pruefe(False, imp)
    assert drift == []


def test_import_partition_ist_byte_gleich_mit_dem_bestand():
    imp = SM.konstanten()[1]
    ist = (DIST / "Finance.SemanticModel" / "definition" / "tables" / "fact_target.tmdl").read_text(
        encoding="utf-8")
    assert CM.tabelle_tmdl("Finance.SemanticModel", imp) == ist
    assert CM.tabelle_tmdl("Finance.SemanticModel") == ist          # None = Import


def test_direct_lake_partition_hat_die_offizielle_form():
    dl, _ = SM.konstanten()
    z = SM.gold_partition("fact_target", "facts", dl)
    assert z == ["\tpartition fact_target = entity", "\t\tmode: directLake", "\t\tsource",
                 "\t\t\tentityName: fact_target", "\t\t\tschemaName: dbo",
                 "\t\t\texpressionSource: DL_Lakehouse"]
    expr = SM.direct_lake_expression()
    assert expr.startswith("expression DL_Lakehouse =")
    assert 'AzureStorage.DataLake("https://onelake.dfs.fabric.microsoft.com/' in expr
    for zeile in z + expr.splitlines():
        assert not zeile.startswith(" ") and ":=" not in zeile        # TMDL-Hardrules


def test_direct_lake_in_ein_import_modell_bricht_ab():
    """dist ist Import: eine Direct-Lake-Tabelle daneben waere ein stilles Mischmodell."""
    dl, _ = SM.konstanten()
    with pytest.raises(ValueError, match="stilles Mischmodell"):
        SM.pruefe_modell(DIST / "Finance.SemanticModel" / "definition", dl)
    with pytest.raises(ValueError, match="stilles Mischmodell"):
        CM.pruefe(False, dl)


def _mini_modell(root: Path, tabellen: dict[str, str], rel: str | None = None) -> Path:
    d = root / "M.SemanticModel" / "definition"
    (d / "tables").mkdir(parents=True)
    (d / "relationships").mkdir()
    (d / "expressions.tmdl").write_text(SM.direct_lake_expression(), encoding="utf-8")
    for name, text in tabellen.items():
        (d / "tables" / f"{name}.tmdl").write_text(text, encoding="utf-8")
    if rel:
        (d / "relationships" / "r.tmdl").write_text(rel, encoding="utf-8")
    return d


def test_direct_lake_modell_mit_materialisierter_spalte_bricht_ab(tmp_path):
    dl, imp = SM.konstanten()
    part = "\n".join(SM.gold_partition("fact_x", "facts", dl))
    fakt = ("table fact_x\n\tcolumn Key\n\t\tdataType: int64\n\t\tsourceColumn: Key\n"
            "\tcolumn Marge = [a] - [b]\n\t\tdataType: double\n" + part + "\n")
    d = _mini_modell(tmp_path, {"fact_x": fakt})
    with pytest.raises(ValueError, match=r"fact_x\[Marge\]"):
        SM.pruefe_modell(d, dl)
    SM.pruefe_modell(d, imp)                                         # Import traegt sie


def test_user_context_spalte_ist_erlaubt_ausser_als_schluessel(tmp_path):
    dl, _ = SM.konstanten()
    part = "\n".join(SM.gold_partition("dim_x", "dimensions", dl))
    dim = ("table dim_x\n\tcolumn Key\n\t\tdataType: int64\n\t\tsourceColumn: Key\n"
           "\tcolumn Anzeige = USERCULTURE()\n\t\tdataType: string\n\t\texpressionContext: userContext\n"
           + part + "\n")
    d = _mini_modell(tmp_path / "a", {"dim_x": dim})
    SM.pruefe_modell(d, dl)                                          # erlaubt
    d = _mini_modell(tmp_path / "b", {"dim_x": dim},
                     rel="relationship r\n\tfromColumn: fact_x.Anzeige\n\ttoColumn: dim_x.Anzeige\n")
    with pytest.raises(ValueError, match="Beziehungsschluessel"):
        SM.pruefe_modell(d, dl)


def test_model_alignment_schaltet_die_dimension_je_modus():
    import yaml
    dl, imp = SM.konstanten()
    v = yaml.safe_load((REPO / "core" / "data_contracts" / "domains" / MA.NEW_DIMENSIONS[0][2])
                       .read_text(encoding="utf-8"))
    modell, dim = MA.NEW_DIMENSIONS[0][0], MA.NEW_DIMENSIONS[0][1]
    t_imp = MA.dimension_tmdl(modell, dim, v, imp)
    t_dl = MA.dimension_tmdl(modell, dim, v, dl)
    assert t_imp == (DIST / f"{modell}.SemanticModel" / "definition" / "tables" / f"{dim}.tmdl"
                     ).read_text(encoding="utf-8")
    assert f"partition {dim} = entity" in t_dl and "mode: directLake" in t_dl
    assert "GoldDataPath" not in t_dl


def test_direct_lake_beispielmodell_besteht_die_tmdl_hardrules(tmp_path):
    """Ein kleines Direct-Lake-Modell aus den Bausteinen, geprueft wie ein Hook es tut."""
    dl, _ = SM.konstanten()
    d = _mini_modell(tmp_path, {"fact_target": CM.tabelle_tmdl("M.SemanticModel", dl)})
    SM.pruefe_modell(d, dl)
    for f in d.rglob("*.tmdl"):
        for zeile in f.read_text(encoding="utf-8").splitlines():
            assert not zeile.startswith(" "), f
            assert ":=" not in zeile, f
    shutil.rmtree(tmp_path / "M.SemanticModel")


def test_direct_lake_ohne_geteilte_expression_bricht_ab(tmp_path):
    dl, _ = SM.konstanten()
    d = _mini_modell(tmp_path, {"fact_target": CM.tabelle_tmdl("M.SemanticModel", dl)})
    (d / "expressions.tmdl").unlink()
    with pytest.raises(ValueError, match="DL_Lakehouse"):
        SM.pruefe_modell(d, dl)
