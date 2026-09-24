"""Die Sandbox-Datenscheibe (AP-3, 24.09.2026): deterministisch, gedeckelt, nie leer.

Gegen eine kleine synthetische Gold-Schicht, damit die Tests die Regeln pruefen und nicht die
1,7 GB. Der Lauf gegen die echte Schicht ist im Ledger gemessen (65 Tabellen, 26,3 MB).
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

REPO = Path(__file__).resolve().parents[2]
SKRIPT = REPO / "showcases" / "aurora_group" / "data" / "scripts" / "slice_gold.py"
spec = importlib.util.spec_from_file_location("slice_gold", SKRIPT)
sg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sg)


def _delta(tabelle: Path, dateien: dict[str, pa.Table], entfernt: tuple[str, ...] = ()):
    tabelle.mkdir(parents=True)
    for name, tab in dateien.items():
        (tabelle / name).parent.mkdir(parents=True, exist_ok=True)
        pq.write_table(tab, str(tabelle / name))
    log = tabelle / "_delta_log"
    log.mkdir()
    zeilen = [json.dumps({"add": {"path": n}}) for n in dateien]
    zeilen += [json.dumps({"remove": {"path": n}}) for n in entfernt]
    (log / "00000000000000000000.json").write_text("\n".join(zeilen) + "\n", encoding="utf-8")


@pytest.fixture()
def gold(tmp_path):
    g = tmp_path / "gold"
    _delta(g / "dimensions" / "dim_org", {"part-0.parquet": pa.table({"OrgKey": [1, 2, 3]}),
                                          "part-alt.parquet": pa.table({"OrgKey": [9]})},
           entfernt=("part-alt.parquet",))
    tage = [20230115, 20231015, 20240110, 20241231]
    _delta(g / "facts" / "fact_klein", {"Fiscal Year=2024/part-0.parquet":
                                        pa.table({"DateKey": tage, "Wert": [1, 2, 3, 4]})})
    viele = [20241201 + (i % 28) for i in range(5000)]
    _delta(g / "facts" / "fact_gross", {"part-0.parquet":
                                        pa.table({"DateKey": viele, "Wert": list(range(5000))})})
    _delta(g / "facts" / "fact_alt", {"part-0.parquet":
                                      pa.table({"DateKey": [20190110, 20200131], "Wert": [7, 8]})})
    _delta(g / "facts" / "fact_ohne_datum", {"part-0.parquet": pa.table({"Wert": [5]})})
    return g


def _manifest(out: Path) -> dict:
    return {e["tabelle"]: e for e in json.loads((out / "_slice_manifest.json").read_text(encoding="utf-8"))["tabellen"]}


def test_window_is_anchored_per_table_so_no_table_goes_blank(gold, tmp_path):
    m = sg.schneiden(gold, tmp_path / "out", monate=15, max_rows=10_000)
    t = _manifest(tmp_path / "out")
    assert t["facts/fact_klein"]["zeilen_aus"] == 3            # 20230115 liegt vor dem Fenster
    assert t["facts/fact_klein"]["fenster"]["anfang"] == 20231001
    assert t["facts/fact_alt"]["zeilen_aus"] == 2              # eigenes Fenster, nicht leer
    assert t["facts/fact_ohne_datum"]["zeilen_aus"] == 1
    assert m["leer_geworden"] == []


def test_the_log_decides_which_files_count(gold, tmp_path):
    sg.schneiden(gold, tmp_path / "out")
    dim = pq.read_table(str(tmp_path / "out" / "dimensions" / "dim_org" / "part-00000.parquet"))
    assert sorted(dim["OrgKey"].to_pylist()) == [1, 2, 3]       # die entfernte Datei fehlt


def test_partition_folders_do_not_add_columns(gold, tmp_path):
    sg.schneiden(gold, tmp_path / "out")
    f = pq.read_table(str(tmp_path / "out" / "facts" / "fact_klein" / "part-00000.parquet"))
    assert f.column_names == ["DateKey", "Wert"]                # kein "Fiscal Year" aus dem Pfad


def test_row_cap_thins_deterministically(gold, tmp_path):
    sg.schneiden(gold, tmp_path / "a", max_rows=1000)
    sg.schneiden(gold, tmp_path / "b", max_rows=1000)
    ta, tb = _manifest(tmp_path / "a"), _manifest(tmp_path / "b")
    assert ta["facts/fact_gross"]["jede_n_te"] == 5
    assert 0 < ta["facts/fact_gross"]["zeilen_aus"] < 5000
    assert ta == tb                                             # gleiche Auswahl, gleiche Bytes


def test_two_processes_write_identical_bytes(gold, tmp_path):
    for ziel in ("a", "b"):
        subprocess.run([sys.executable, str(SKRIPT), "--gold", str(gold), "--out", str(tmp_path / ziel)],
                       check=True, capture_output=True, text=True, encoding="utf-8")
    for f in (tmp_path / "a").rglob("*"):
        if f.is_file():
            assert f.read_bytes() == (tmp_path / "b" / f.relative_to(tmp_path / "a")).read_bytes(), f


def test_cap_is_enforced(gold, tmp_path):
    r = subprocess.run([sys.executable, str(SKRIPT), "--gold", str(gold), "--out", str(tmp_path / "o"),
                        "--cap-mb", "0.000001"], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 1 and "Deckel" in r.stderr


def test_a_table_that_goes_blank_fails_the_run(gold, tmp_path, monkeypatch):
    # Gegenprobe zur Regel "keine Tabelle wird leer": ein globales Fenster wie im ersten Entwurf.
    monkeypatch.setattr(sg, "max_datekey", lambda _tabelle: 20241231)
    r = sg.schneiden(gold, tmp_path / "o", monate=15)
    assert r["leer_geworden"] == ["facts/fact_alt"]


def test_never_overwrites(gold, tmp_path):
    ziel = tmp_path / "o"
    ziel.mkdir()
    (ziel / "etwas").write_text("x", encoding="utf-8")
    with pytest.raises(SystemExit, match="nicht leer"):
        sg.schneiden(gold, ziel)
