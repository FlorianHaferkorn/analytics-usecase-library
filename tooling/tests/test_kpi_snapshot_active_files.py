"""build_kpi_snapshot liest nur die laut ``_delta_log`` aktiven Dateien (29.09.2026).

Vorher las ein ``**/*.parquet``-Glob auch die per ``remove`` verabschiedeten Dateien mit:
fact_sales 298 Dateien / 28,7 Mio. Zeilen auf der Platte gegen 60 aktive / 9,35 Mio.
Net Sales 12/2024 fiel dadurch von 1.341.190.109 auf 439.447.179 EUR.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

_PFAD = Path(__file__).resolve().parents[2] / "showcases" / "aurora_group" / "data" / "build_kpi_snapshot.py"


@pytest.fixture(scope="module")
def mod():
    pytest.importorskip("duckdb")
    spec = importlib.util.spec_from_file_location("build_kpi_snapshot", _PFAD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _tabelle(tmp_path: Path, log_pfade: list[dict]) -> Path:
    t = tmp_path / "fact"
    (t / "_delta_log").mkdir(parents=True)
    for rel in ("Fiscal Year=2024/a.parquet", "Fiscal Year=2024/b.parquet", "Fiscal Year=2024/alt.parquet"):
        (t / rel).parent.mkdir(parents=True, exist_ok=True)
        (t / rel).write_bytes(b"")
    zeilen = "\n".join(json.dumps(x) for x in log_pfade) + "\n"
    (t / "_delta_log" / "00000000000000000000.json").write_text(zeilen, "utf-8", newline="\n")
    return t


def test_removed_files_are_not_read(mod, tmp_path):
    t = _tabelle(tmp_path, [
        {"add": {"path": "Fiscal Year=2024/alt.parquet"}},
        {"add": {"path": "Fiscal Year=2024/a.parquet"}},
        {"remove": {"path": "Fiscal Year=2024/alt.parquet"}},
    ])
    assert [p.name for p in mod.active_files(t)] == ["a.parquet"]


def test_url_encoded_log_paths_resolve_to_the_plain_directory(mod, tmp_path):
    """deltalake >= 1.6.6 schreibt ``Fiscal%20Year`` ins Log, das Verzeichnis bleibt ``Fiscal Year``."""
    t = _tabelle(tmp_path, [{"add": {"path": "Fiscal%20Year=2024/b.parquet"}}])
    assert [p.name for p in mod.active_files(t)] == ["b.parquet"]


def test_an_active_file_missing_on_disk_is_an_error_not_a_smaller_sum(mod, tmp_path):
    t = _tabelle(tmp_path, [{"add": {"path": "Fiscal Year=2024/fehlt.parquet"}}])
    with pytest.raises(FileNotFoundError):
        mod.active_files(t)
