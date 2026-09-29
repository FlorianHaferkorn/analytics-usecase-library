"""showdaten.py (Meridian D-578): Rundreise packen -> holen und das Verhalten ohne Release.

Unit-Tests mit eigenen Daten unter ``tmp_path``; die echten Showdaten braucht keiner davon.
Ein fehlender Release darf nie gruen enden: ``holen`` meldet Exit 2 und nennt Tag und Asset.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from showcases.aurora_group.data import showdaten as sd  # noqa: E402


def _mini_gold(root: Path) -> Path:
    gold = root / "gold"
    for rel, inhalt in {
        "dimensions/dim_x/part-00000.parquet": b"x" * 10,
        "facts/fact_y/Fiscal Year=2024/part-00000.parquet": b"y" * 20,
        "security_user_org/part-00000.parquet": b"z" * 5,
    }.items():
        p = gold / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(inhalt)
    return gold


def test_roundtrip_pack_then_fetch_from_file(tmp_path, monkeypatch):
    quelle = _mini_gold(tmp_path / "quelle")
    aus = tmp_path / "paket"
    assert sd.packen(aus, "showdaten-aurora-test", gold=quelle) == 0
    monkeypatch.setattr(sd, "LOCK", aus / sd.LOCK.name)
    ziel = tmp_path / "ziel"
    assert sd.pruefen(gold=ziel) == sd.FEHLT
    assert sd.holen(aus / "aurora_gold_test.tar", gold=ziel) == sd.DA
    assert (ziel / "facts/fact_y/Fiscal Year=2024/part-00000.parquet").read_bytes() == b"y" * 20
    # bytegleich reproduzierbar: zweites Paket, gleicher SHA-256
    aus2 = tmp_path / "paket2"
    sd.packen(aus2, "showdaten-aurora-test", gold=quelle)
    assert sd._sha256(aus2 / "aurora_gold_test.tar") == sd._sha256(aus / "aurora_gold_test.tar")


def test_unloadable_release_is_exit_2_never_green(tmp_path, monkeypatch, capsys):
    aus = tmp_path / "paket"
    sd.packen(aus, "showdaten-aurora-test", gold=_mini_gold(tmp_path / "quelle"))
    monkeypatch.setattr(sd, "LOCK", aus / sd.LOCK.name)
    monkeypatch.setattr(sd.shutil, "which", lambda _: None)      # kein gh -> nicht ladbar
    capsys.readouterr()                                          # packen-Ausgabe verwerfen
    assert sd.holen(None, ci=True, gold=tmp_path / "leer") == sd.FEHLT
    out = capsys.readouterr()
    assert out.out.startswith("::error title=Showdaten fehlen::nicht gelaufen")
    assert "nicht gelaufen" in out.err


def test_failed_download_names_tag_asset_and_upload_command(tmp_path, monkeypatch):
    aus = tmp_path / "paket"
    sd.packen(aus, "showdaten-aurora-test", gold=_mini_gold(tmp_path / "quelle"))
    lock = sd.json.loads((aus / sd.LOCK.name).read_text(encoding="utf-8"))

    class R:
        returncode, stdout, stderr = 1, "", "release not found"

    monkeypatch.setattr(sd.shutil, "which", lambda _: "/usr/bin/gh")
    monkeypatch.setattr(sd.subprocess, "run", lambda *a, **k: R())
    try:
        sd._laden(lock, tmp_path)
    except sd.LadenFehlgeschlagen as e:
        text = str(e)
    else:
        raise AssertionError("fehlender Release darf nicht als geladen gelten")
    assert "showdaten-aurora-test" in text and "aurora_gold_test.tar" in text
    assert "release not found" in text and "gh release create" in text
