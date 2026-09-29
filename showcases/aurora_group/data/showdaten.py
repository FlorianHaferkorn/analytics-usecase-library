#!/usr/bin/env python3
"""Aurora-Showdaten: packen, holen, pruefen (Meridian D-578, 29.09.2026).

Die Gold-Daten (Parquet + ``_delta_log``) unter ``gold/dimensions``, ``gold/facts`` und
``gold/security_user_org`` liegen nicht mehr in Git. Sie kommen als **ein** Archiv aus einem
GitHub-Release; ``showdaten.lock.json`` neben diesem Skript haelt Tag, Asset-Name, SHA-256
des Archivs und die Liste jeder Datei mit Groesse und SHA-256.

Warum ein Archiv und nicht der Generator (gemessen 29.09.2026, Belege in
``scripts/README.md``): ein Neulauf der ganzen Kette trifft 47 von 66 Tabellen logisch, 16
weichen in Werten oder Zeilenzahlen ab (darunter ``fact_sales``), 3 haben keinen aktiven
Generator. Der
eingecheckte Stand ist ueber Februar bis August 2026 aus mehreren Generatorstaenden
gewachsen (spaetere Codeaenderungen verschieben die Zufallsfolge), eine Tabelle
(``fact_sales``) zuletzt von einem Transform geschrieben, der nicht im Repo liegt. Ein
Neulauf waere ein neuer Datensatz, keine Wiederherstellung.

    python showcases/aurora_group/data/showdaten.py holen            # Release laden, pruefen, entpacken
    python showcases/aurora_group/data/showdaten.py holen --datei X.tar   # dasselbe aus lokaler Datei
    python showcases/aurora_group/data/showdaten.py pruefen [--tief] # 0 da, 1 abweichend, 2 fehlt
    python showcases/aurora_group/data/showdaten.py packen --aus-dir /tmp/x --tag T [--gold D]  # Archiv + Lock

Nur aktive Dateien kommen ins Archiv: bei Delta die, deren letzte Aktion im ``_delta_log``
``add`` ist (Logik aus ``scripts/check_showcase_delta.py``, nicht nachgebaut), dazu der Log
selbst; ohne Log alle ``*.parquet``. Verwaiste Dateien bleiben draussen.

Ein Release wird hier **nicht** angelegt (nach aussen sichtbar, Entscheidung des Owners);
``packen`` gibt die ``gh``-Zeile dafuer aus. ``holen`` versucht den Download immer; fehlt der
Release oder das Asset, endet es mit Exit 2 und nennt Tag, Asset und die Zeile zum Hochladen
(``--ci`` schreibt das zusaetzlich als ``::error``-Annotation). Ein fehlender Release ist nie
gruen: die Gates danach (``check_model_vs_gold.py --strict``, ``pruefen``) enden mit Exit 2.
"""
from __future__ import annotations

import argparse
import functools
import glob
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

HIER = Path(__file__).resolve().parent
REPO = HIER.parents[2]
GOLD = HIER / "gold"
LOCK = HIER / "showdaten.lock.json"
BEREICHE = ("dimensions", "facts", "security_user_org")
REPO_SLUG = "FlorianHaferkorn/analytics-usecase-library"
BEFEHL = "python showcases/aurora_group/data/showdaten.py holen"

FEHLT, DA, ABWEICHEND = 2, 0, 1


# ---------------------------------------------------------------------------
# Dateiauswahl
# ---------------------------------------------------------------------------

@functools.lru_cache(maxsize=1)
def _delta_modul():
    spec = importlib.util.spec_from_file_location(
        "check_showcase_delta", REPO / "scripts" / "check_showcase_delta.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _active_paths(log_dir: Path) -> list[str]:
    return _delta_modul()._active_paths(str(log_dir))


def _tabellen(gold: Path) -> list[Path]:
    out = []
    for bereich in BEREICHE:
        base = gold / bereich
        if bereich == "security_user_org":
            if base.is_dir():
                out.append(base)
            continue
        out += sorted(p for p in base.glob("*") if p.is_dir())
    return out


def aktive_dateien(gold: Path = GOLD) -> list[Path]:
    """Alle Dateien, die ein Leser braucht: aktive Parquet + ``_delta_log``, sortiert."""
    dateien: list[Path] = []
    for tab in _tabellen(gold):
        log = tab / "_delta_log"
        if log.is_dir():
            dateien += sorted(p for p in log.iterdir() if p.is_file())
            dateien += [tab / rel for rel in _active_paths(log)]
        else:
            dateien += sorted(Path(p) for p in glob.glob(str(tab / "**" / "*.parquet"), recursive=True))
    return sorted(set(dateien))


def _sha256(pfad: Path) -> str:
    h = hashlib.sha256()
    with open(pfad, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Lock
# ---------------------------------------------------------------------------

def lock_lesen() -> dict:
    with open(LOCK, encoding="utf-8") as f:
        return json.load(f)


def fehlende(gold: Path = GOLD, lock: dict | None = None) -> list[str]:
    """Pfade aus dem Lock, die unter ``gold`` fehlen (schnell: nur Existenz)."""
    lock = lock or lock_lesen()
    return [rel for rel in lock["dateien"] if not (gold / rel).is_file()]


def grund_wenn_fehlend(gold: Path = GOLD) -> str | None:
    """Fuer Tests und Gates: ``None`` wenn die Showdaten da sind, sonst der Grund als Satz.

    Ein fehlender Datensatz heisst ``nicht gelaufen``, nie ``ok``. Liegen Daten da, die vom
    Lock abweichen (z. B. lokal neu generiert), laufen die Tests dagegen und melden selbst;
    die Abweichung zeigt ``pruefen``.
    """
    try:
        lock = lock_lesen()
    except FileNotFoundError:
        return f"nicht gelaufen: {LOCK.name} fehlt"
    weg = fehlende(gold, lock)
    if not weg:
        return None
    if any(next((gold / b).rglob("*.parquet"), None) for b in BEREICHE if (gold / b).is_dir()):
        return None
    return (f"nicht gelaufen: Aurora-Showdaten fehlen ({len(weg)} von {len(lock['dateien'])} "
            f"Dateien, z. B. {weg[0]}); holen mit `{BEFEHL}` (D-578)")


def pytest_markierung():
    """``skipif``-Marke fuer Tests, die die echten Showdaten lesen (Integrationstests).

    Der Grund steht im Skip-Text (``-rs``): „nicht gelaufen: … holen mit …". Unit-Tests
    bauen ihre Daten selbst (``tmp_path``) und brauchen diese Marke nicht.
    """
    import pytest

    grund = grund_wenn_fehlend()
    return pytest.mark.skipif(grund is not None, reason=grund or "")


def pruefen(tief: bool = False, gold: Path = GOLD) -> int:
    lock = lock_lesen()
    weg = fehlende(gold, lock)
    if weg:
        # Teilstand (einige Parquet da, Lock-Dateien fehlen): grund_wenn_fehlend liefert dann
        # None, weil Tests gegen vorhandene Daten laufen sollen -- hier trotzdem benennen.
        print(grund_wenn_fehlend(gold) or
              f"UNVOLLSTAENDIG: {len(weg)} von {len(lock['dateien'])} Dateien aus dem Lock fehlen, "
              f"z. B. {weg[0]}; Stand des Locks herstellen: `{BEFEHL}`")
        return FEHLT
    abw = []
    for rel, meta in lock["dateien"].items():
        p = gold / rel
        if p.stat().st_size != meta["bytes"] or (tief and _sha256(p) != meta["sha256"]):
            abw.append(rel)
    if abw:
        print(f"ABWEICHEND: {len(abw)} Datei(en) weichen vom Lock ab, z. B. {abw[0]}. "
              f"Lokal neu generiert? Stand des Locks wiederherstellen: `{BEFEHL}`")
        return ABWEICHEND
    art = "Groesse und SHA-256" if tief else "Groesse (SHA-256 mit --tief)"
    print(f"OK: {len(lock['dateien'])} Dateien wie im Lock ({lock['tag']}), geprueft: {art}.")
    return DA


# ---------------------------------------------------------------------------
# packen
# ---------------------------------------------------------------------------

def _tarinfo(name: str, groesse: int) -> tarfile.TarInfo:
    ti = tarfile.TarInfo(name)
    ti.size = groesse
    ti.mtime = 0
    ti.mode = 0o644
    ti.uid = ti.gid = 0
    ti.uname = ti.gname = ""
    return ti


def packen(aus_dir: Path, tag: str, gold: Path = GOLD) -> int:
    """Deterministisches Archiv (Reihenfolge, mtime, Besitzer fest) + Lock schreiben."""
    dateien = aktive_dateien(gold)
    if not dateien:
        print(f"nicht gelaufen: keine Showdaten unter {gold}", file=sys.stderr)
        return FEHLT
    aus_dir.mkdir(parents=True, exist_ok=True)
    asset = f"aurora_gold_{tag.removeprefix('showdaten-aurora-')}.tar"
    ziel = aus_dir / asset
    eintraege = {}
    with tarfile.open(ziel, "w", format=tarfile.PAX_FORMAT) as tar:
        for p in dateien:
            rel = p.relative_to(gold).as_posix()
            groesse = p.stat().st_size
            eintraege[rel] = {"bytes": groesse, "sha256": _sha256(p)}
            with open(p, "rb") as f:
                tar.addfile(_tarinfo(rel, groesse), f)
    gesamt = sum(e["bytes"] for e in eintraege.values())
    lock = {
        "entscheidung": "Meridian D-578 (29.09.2026): Showdaten raus aus Git",
        "tag": tag,
        "asset": asset,
        "repo": REPO_SLUG,
        "sha256": _sha256(ziel),
        "bytes": ziel.stat().st_size,
        "inhalt_bytes": gesamt,
        "dateien": eintraege,
    }
    (aus_dir / LOCK.name).write_text(json.dumps(lock, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Archiv: {ziel} ({ziel.stat().st_size / 1e6:.1f} MB, {len(eintraege)} Dateien, "
          f"Inhalt {gesamt / 1e6:.1f} MB)")
    print(f"Lock:   {aus_dir / LOCK.name} -> nach {LOCK} kopieren")
    print("Veroeffentlichen (Owner, nach aussen sichtbar):")
    print("  " + hochladen_befehl(lock, ziel))
    return 0


def hochladen_befehl(lock: dict, archiv: Path | str | None = None) -> str:
    archiv = archiv or f"<pfad>/{lock['asset']}"
    return (f"gh release create {lock['tag']} {archiv} --repo {lock['repo']} "
            f"--title \"Aurora-Showdaten {lock['tag']}\" --notes \"Gold-Daten der Aurora-Showcase, D-578\"")


# ---------------------------------------------------------------------------
# holen
# ---------------------------------------------------------------------------

class LadenFehlgeschlagen(Exception):
    pass


def _laden(lock: dict, ziel_dir: Path) -> Path:
    if not shutil.which("gh"):
        raise LadenFehlgeschlagen("gh (GitHub CLI) fehlt; alternativ `--datei <archiv>` angeben")
    # Kein Geheimnis in der Befehlszeile: gh liest GH_TOKEN aus der Umgebung.
    cmd = ["gh", "release", "download", lock["tag"], "--repo", lock["repo"],
           "--pattern", lock["asset"], "--dir", str(ziel_dir), "--clobber"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    ziel = ziel_dir / lock["asset"]
    if r.returncode != 0 or not ziel.is_file():
        grund = r.stderr.strip() or r.stdout.strip() or "Asset nicht im Release"
        raise LadenFehlgeschlagen(
            f"Release {lock['tag']} mit Asset {lock['asset']} in {lock['repo']} nicht ladbar "
            f"(gh: {grund}). Fehlt der Release, legt ihn der Owner an: "
            f"{hochladen_befehl(lock)}")
    return ziel


def holen(datei: Path | None, ci: bool = False, gold: Path = GOLD) -> int:
    lock = lock_lesen()
    if grund_wenn_fehlend(gold) is None and pruefen(gold=gold) == DA:
        return 0
    with tempfile.TemporaryDirectory(prefix="showdaten_") as tmp:
        try:
            archiv = datei if datei is not None else _laden(lock, Path(tmp))
        except LadenFehlgeschlagen as e:
            text = f"nicht gelaufen: Aurora-Showdaten nicht geholt. {e}"
            if ci:
                print(f"::error title=Showdaten fehlen::{text}")
            print(text, file=sys.stderr)
            return FEHLT
        ist = _sha256(archiv)
        if ist != lock["sha256"]:
            raise SystemExit(f"SHA-256 des Archivs passt nicht zum Lock: {ist} != {lock['sha256']}")
        with tarfile.open(archiv) as tar:
            namen = tar.getnames()
            unerwartet = sorted(set(namen) ^ set(lock["dateien"]))
            if unerwartet:
                raise SystemExit(f"Archivinhalt weicht vom Lock ab: {unerwartet[:3]}")
            for n in namen:
                teile = Path(n).parts
                if Path(n).is_absolute() or ".." in teile or teile[0] not in BEREICHE:
                    raise SystemExit(f"Unzulaessiger Pfad im Archiv: {n}")
            for bereich in BEREICHE:  # Altstand (auch verwaiste Dateien) ersetzen, nicht mischen
                if (gold / bereich).exists():
                    shutil.rmtree(gold / bereich)
            tar.extractall(gold, filter="data")
    rc = pruefen(tief=True, gold=gold)
    return rc


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    h = sub.add_parser("holen", help="Archiv laden (oder --datei), SHA-256 pruefen, entpacken")
    h.add_argument("--datei", type=Path, help="lokales Archiv statt Download")
    h.add_argument("--ci", action="store_true",
                   help="Fehler zusaetzlich als GitHub-Annotation (::error); Exit bleibt 2")
    p = sub.add_parser("pruefen", help="0 da, 1 abweichend, 2 fehlt")
    p.add_argument("--tief", action="store_true", help="zusaetzlich SHA-256 je Datei")
    k = sub.add_parser("packen", help="Archiv + Lock aus dem lokalen Gold bauen")
    k.add_argument("--aus-dir", type=Path, required=True)
    k.add_argument("--tag", required=True, help="z. B. showdaten-aurora-2026-09-29b")
    k.add_argument("--gold", type=Path, default=GOLD,
                   help="Quelle (Ordner mit dimensions/facts/security_user_org), Vorgabe: hier")
    a = ap.parse_args(argv)
    if a.cmd == "holen":
        return holen(a.datei, ci=a.ci)
    if a.cmd == "pruefen":
        return pruefen(tief=a.tief)
    return packen(a.aus_dir, a.tag, gold=a.gold)


if __name__ == "__main__":
    raise SystemExit(main())
