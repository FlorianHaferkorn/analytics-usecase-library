#!/usr/bin/env python3
"""Semantic Model gegen Gold-Daten: jede ``sourceColumn`` der ausgelieferten Modelle muss in
der Gold-Tabelle stehen, die ihre Partition liest (Ledger A-24, 29.09.2026).

Anlass: 11 von 495 ``sourceColumn`` der Modelle unter ``products/fabric/powerbi/dist/`` fehlen
laut Prototyp-Messung in ``showcases/aurora_group/data/gold`` (Ledger A-24). Ein Import-Refresh
scheitert an solchen Tabellen (hergeleitet, nicht in Fabric ausgeführt). Vorher hielt nur
``tooling/tests/test_gold_source.py`` eine Liste von 10 Lücken, per ``pyarrow`` gelesen und nur
in pytest; Stage 1 und Quality-Gate prüften Modell gegen Daten nicht. Diese Prüfung ersetzt jene
Liste (eine Sperrklinke, nicht zwei).

**Zuordnung Modelltabelle → Gold-Tabelle über die Partition**, nicht über den Tabellennamen:
``fn_DeltaCurrentFiles(GoldDataPath & "/facts/fact_cost")``. Eine Tabelle ohne solche Partition
(``_Measures``, ``Vergleich``, ``dim_supplier``, Inline-``#table`` wie ``dim_pvm_driver``) liest
kein Gold; sie steht in der eigenen Klasse *ohne Gold-Quelle*, nicht unter den Befunden. Das ist
der elfte A-24-Fall (``dim_pvm_driver[SortOrder]``): der Prototyp verband über den Namen.

**Schema = was das Modell lädt.** Welche Dateien, sagt der Delta-Log (``_active_paths``, wie
``fn_DeltaCurrentFiles``; entfernte Dateien im Ordner zählen nicht); ohne Log alle Parquet-Dateien.
Welche Spalten, sagen deren Parquet-Fußteile (eigener Thrift-Leser, stdlib — kein ``pyarrow``;
der Test stellt ihn gegen ``pyarrow``). Das Log-Schema (``metaData.schemaString``,
``scripts/check_showcase_delta._metadata``) wird dagegengestellt, aber nicht als Quelle genommen:
gemessen 29.09.2026 trägt es in 35 Fakten ``partitionColumns`` (``Fiscal Year``), die in keiner
Datei stehen und die ``Parquet.Document`` nie liefert, und bei ``dim_date`` fehlen ihm drei
Spalten, die alle aktiven Dateien haben. Abweichungen stehen als eigene Klasse im Bericht.

**Drei Ausgänge, nie still grün:**

* ``0`` — alles geprüft, Befunde genau gleich der Allowlist.
* ``1`` — neuer Befund (nicht in der Allowlist) **oder** Allowlist-Eintrag, dessen Tabelle geprüft
  wurde und der nicht mehr auftritt (Sperrklinke: behoben → Eintrag streichen).
* ``2`` — mit ``--strict``: mindestens eine Tabelle *nicht geprüft* (Gold fehlt ganz oder
  teilweise, Schema unlesbar, Partition benennt Spalten um). Ohne ``--strict`` steht das in der
  Schlusszeile als ``NICHT GEPRÜFT``, Exit 0 — Stage 1, Quality-Gate und CI fahren ``--strict``.

Allowlist: ``tooling/validation/model_vs_gold_allowlist.yaml`` (Grund und Ledger-Verweis Pflicht).

    python3 tooling/validation/check_model_vs_gold.py --strict
    python3 tooling/validation/check_model_vs_gold.py --gold <ordner> --dist <ordner>
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import struct
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DIST = REPO / "products" / "fabric" / "powerbi" / "dist"
GOLD = REPO / "showcases" / "aurora_group" / "data" / "gold"
ALLOWLIST = Path(__file__).resolve().parent / "model_vs_gold_allowlist.yaml"

# Nach AUL #498 (Meridian D-578) liegen die Showdaten nicht mehr in Git; dieser Befehl holt sie
# an dieselbe Stelle (showcases/aurora_group/data/gold/{dimensions,facts,security_user_org}).
HOLEN = "python showcases/aurora_group/data/showdaten.py holen"

EXIT_OK, EXIT_BEFUND, EXIT_NICHT_GEPRUEFT = 0, 1, 2


def _lade(name: str, pfad: Path):
    spec = importlib.util.spec_from_file_location(name, pfad)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# Tool-Reuse: Delta-Log-Replay aus scripts/check_showcase_delta.py (scripts/ ist kein Paket),
# Block-Zerlegung der Tabellen-TMDL aus tooling/codegen/dax_smoke.py.
_delta = _lade("check_showcase_delta", REPO / "scripts" / "check_showcase_delta.py")
_bloecke = _lade("dax_smoke", REPO / "tooling" / "codegen" / "dax_smoke.py")._bloecke

_TABELLE = re.compile(r"^table (?:'((?:[^']|'')+)'|(\S+))", re.M)
_SPALTE = re.compile(r"^\tcolumn (?:'((?:[^']|'')+)'|([^\s=]+))([ \t]*=)?")
_QUELLE = re.compile(r"^\t\tsourceColumn:\s*(.+?)\s*$", re.M)
_GOLD_ORDNER = re.compile(r'GoldDataPath\s*&\s*"/([^"]+)"')
# M-Schritte, nach denen ein sourceColumn nicht mehr der Parquet-Spalte entsprechen muss.
_UMFORMUNG = re.compile(
    r"Table\.(?:RenameColumns|AddColumn|TransformColumnNames|ExpandTableColumn|"
    r"ExpandRecordColumn|DuplicateColumn|CombineColumns|SplitColumn|Pivot|Unpivot)\b")


# ---------------------------------------------------------------------------
# Parquet-Fußteil ohne pyarrow (Thrift Compact Protocol, nur FileMetaData.schema)
# ---------------------------------------------------------------------------

class _Thrift:
    def __init__(self, data: bytes):
        self.d, self.i = data, 0

    def byte(self) -> int:
        b = self.d[self.i]
        self.i += 1
        return b

    def varint(self) -> int:
        n = s = 0
        while True:
            b = self.byte()
            n |= (b & 0x7F) << s
            if not b & 0x80:
                return n
            s += 7

    def zigzag(self) -> int:
        n = self.varint()
        return (n >> 1) ^ -(n & 1)

    def binary(self) -> bytes:
        n = self.varint()
        self.i += n
        return self.d[self.i - n:self.i]

    def list_header(self) -> tuple[int, int]:
        b = self.byte()
        n = b >> 4
        return (self.varint() if n == 15 else n), b & 0x0F

    def skip(self, t: int) -> None:
        if t in (1, 2):                       # bool im Feldkopf
            return
        if t == 3:
            self.i += 1
        elif t in (4, 5, 6):
            self.varint()
        elif t == 7:
            self.i += 8
        elif t == 8:
            self.binary()
        elif t in (9, 10):
            n, et = self.list_header()
            for _ in range(n):
                if et in (1, 2):
                    self.i += 1               # bool als Listenelement: ein Byte
                else:
                    self.skip(et)
        elif t == 11:
            n = self.varint()
            if n:
                kv = self.byte()
                for _ in range(n):
                    self.skip(kv >> 4)
                    self.skip(kv & 0x0F)
        elif t == 12:
            self.struct(lambda fid, ft: False)
        else:
            raise ValueError(f"unbekannter Thrift-Typ {t}")

    def struct(self, feld) -> None:
        """Liest eine Struktur; ``feld(id, typ)`` liest selbst und gibt True, sonst wird übersprungen."""
        letzte = 0
        while True:
            b = self.byte()
            if b == 0:
                return
            delta, t = b >> 4, b & 0x0F
            fid = letzte + delta if delta else self.zigzag()
            letzte = fid
            if not feld(fid, t):
                self.skip(t)


class _Fertig(Exception):
    pass


def parquet_spalten(pfad: Path) -> list[str]:
    """Spaltennamen der obersten Ebene aus dem Parquet-Fußteil (FileMetaData.schema)."""
    with open(pfad, "rb") as fh:
        fh.seek(-8, 2)
        laenge, magie = struct.unpack("<I4s", fh.read(8))
        if magie != b"PAR1":
            raise ValueError(f"{pfad}: kein Parquet-Fußteil")
        fh.seek(-8 - laenge, 2)
        r = _Thrift(fh.read(laenge))
    elemente: list[list] = []                 # [Name, num_children]

    def element(fid: int, t: int) -> bool:
        if fid == 4 and t == 8:
            elemente[-1][0] = r.binary().decode("utf-8")
            return True
        if fid == 5 and t == 5:
            elemente[-1][1] = r.zigzag()
            return True
        return False

    def metadaten(fid: int, t: int) -> bool:
        if fid != 2 or t != 9:
            return False
        n, _ = r.list_header()
        for _ in range(n):
            elemente.append(["", 0])
            r.struct(element)
        raise _Fertig                         # schema gelesen, Rest egal

    try:
        r.struct(metadaten)
    except _Fertig:
        pass
    if not elemente:
        raise ValueError(f"{pfad}: kein Schema im Fußteil")
    # elemente[0] ist die Wurzel; Kinder stehen in Vorordnung, Gruppen tragen num_children.
    namen, i = [], 1

    def ueberspringen(j: int) -> int:
        kinder = elemente[j][1]
        j += 1
        for _ in range(kinder):
            j = ueberspringen(j)
        return j

    for _ in range(elemente[0][1]):
        namen.append(elemente[i][0])
        i = ueberspringen(i)
    return namen


@dataclass
class GoldSchema:
    namen: set[str] | None                    # None = nicht lesbar
    herkunft: str                             # delta_log | ohne_log | Grund, wenn None
    log_abweichung: tuple = ()                # (nur im Log, nur in Dateien) — nur mit Log


def gold_schema(tabelle: Path) -> GoldSchema:
    """Spalten, die ``fn_DeltaCurrentFiles`` + ``Parquet.Document`` für eine Gold-Tabelle liefert.

    Welche Dateien: mit ``_delta_log`` die laut Log aktiven (``_active_paths``), ohne Log alle
    Parquet-Dateien — genau wie ``fn_DeltaCurrentFiles``. Welche Spalten: Vereinigung der
    Fußteile dieser Dateien (``Table.Combine`` vereinigt ebenso). Das Log-Schema
    (``metaData.schemaString`` ohne ``partitionColumns``) wird dagegengestellt; weicht es ab,
    steht das als eigene Klasse im Bericht (Datenpflege, kein Modellbefund).
    """
    log = tabelle / "_delta_log"
    if log.is_dir():
        dateien = [tabelle / p for p in _delta._active_paths(str(log))]
        if not dateien:
            return GoldSchema(None, "Delta-Log ohne aktive Datei")
        fehlend = [p for p in dateien if not p.is_file()]
        if fehlend:
            return GoldSchema(None, f"{len(fehlend)} aktive Datei(en) fehlen auf der Platte "
                                    f"(scripts/check_showcase_delta.py)")
    else:
        dateien = sorted(p for p in tabelle.rglob("*.parquet") if "_delta_log" not in p.parts)
        if not dateien:
            return GoldSchema(None, "weder _delta_log noch Parquet-Dateien")
    namen: set[str] = set()
    for p in dateien:
        try:
            namen |= set(parquet_spalten(p))
        except (ValueError, OSError, IndexError) as exc:
            return GoldSchema(None, f"Parquet-Fußteil unlesbar: {exc}")
    if not log.is_dir():
        return GoldSchema(namen, "ohne_log")
    meta = _delta._metadata(str(log))
    if meta is None:
        return GoldSchema(namen, "delta_log", ("Log ohne metaData.schemaString", ""))
    im_log = set(meta["columns"]) - set(meta["partitionColumns"])
    abw = (tuple(sorted(im_log - namen)), tuple(sorted(namen - im_log)))
    return GoldSchema(namen, "delta_log", abw if any(abw) else ())


# ---------------------------------------------------------------------------
# Modell lesen
# ---------------------------------------------------------------------------

@dataclass
class Modelltabelle:
    modell: str
    datei: Path
    name: str
    gold_ordner: list[str]
    umformung: bool
    quellen: list[tuple[str, str]]            # (Spalte, sourceColumn)


def _unquote(s: str) -> str:
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "'\"":
        return s[1:-1].replace(s[0] * 2, s[0])
    return s


def lies_modelle(dist: Path) -> list[Modelltabelle]:
    """Jede Tabellen-Datei jedes ``*.SemanticModel`` — per Dateiglob, unabhängig vom Dateinamen
    (der vendorte Meridian-Parser verliert Tabellen mit „relationship“ im Namen, PR #511)."""
    out = []
    for modell in sorted(dist.glob("*.SemanticModel")):
        for f in sorted((modell / "definition" / "tables").glob("*.tmdl")):
            text = f.read_text(encoding="utf-8")
            m = _TABELLE.search(text)
            if not m:
                continue
            quellen, partition = [], []
            for block in _bloecke(text):
                s = _SPALTE.match(block.lstrip("\n"))
                if s:
                    if s.group(3):             # berechnete Spalte: kein sourceColumn
                        continue
                    q = _QUELLE.search(block)
                    if q:
                        spalte = (s.group(1) or s.group(2)).replace("''", "'")
                        quellen.append((spalte, _unquote(q.group(1))))
                elif block.lstrip("\n").startswith("\tpartition "):
                    partition.append(block)
            m_text = "\n".join(partition)
            out.append(Modelltabelle(
                modell=modell.name.split(".")[0], datei=f,
                name=(m.group(1) or m.group(2)).replace("''", "'"),
                gold_ordner=sorted(set(_GOLD_ORDNER.findall(m_text))),
                umformung=bool(_UMFORMUNG.search(m_text)), quellen=quellen))
    return out


# ---------------------------------------------------------------------------
# Allowlist
# ---------------------------------------------------------------------------

def lies_allowlist(pfad: Path) -> dict[tuple[str, str, str], dict]:
    import yaml

    daten = yaml.safe_load(pfad.read_text(encoding="utf-8")) or {}
    out = {}
    for e in daten.get("eintraege") or []:
        schluessel = (e.get("modell"), e.get("tabelle"), e.get("quellspalte"))
        if not all(schluessel) or not str(e.get("grund") or "").strip() \
                or not str(e.get("ledger") or "").strip():
            raise ValueError(f"{pfad.name}: Eintrag ohne modell/tabelle/quellspalte/grund/ledger: {e}")
        if schluessel in out:
            raise ValueError(f"{pfad.name}: doppelter Eintrag {schluessel}")
        out[schluessel] = e
    return out


# ---------------------------------------------------------------------------
# Prüfen
# ---------------------------------------------------------------------------

@dataclass
class Ergebnis:
    geprueft: int = 0                                     # geprüfte sourceColumn
    tabellen_geprueft: int = 0
    befunde: set = field(default_factory=set)             # (Modell, Tabelle, sourceColumn)
    neu: list = field(default_factory=list)
    verschwunden: list = field(default_factory=list)
    ohne_gold_quelle: list = field(default_factory=list)  # (Modell, Tabelle, gleichnamiger Gold-Ordner?)
    nicht_geprueft: list = field(default_factory=list)    # (wo, Grund)
    anzahl_nicht_geprueft: int = 0                        # Modelltabellen ohne Messung
    herkunft: dict = field(default_factory=dict)          # Gold-Ordner -> delta_log | ohne_log
    log_abweichung: dict = field(default_factory=dict)    # Gold-Ordner -> (nur Log, nur Dateien)

    @property
    def rot(self) -> bool:
        return bool(self.neu or self.verschwunden)


def pruefe(dist: Path = DIST, gold: Path = GOLD, allowlist: Path = ALLOWLIST) -> Ergebnis:
    erlaubt = lies_allowlist(allowlist)
    ergebnis = Ergebnis()
    tabellen = lies_modelle(dist)
    if not tabellen:
        ergebnis.nicht_geprueft.append(("alle Modelle", f"keine Modelltabellen unter {dist}"))
        ergebnis.anzahl_nicht_geprueft = 1
        return ergebnis
    schemata: dict[str, GoldSchema] = {}
    geprueft_tabellen: set[tuple[str, str]] = set()
    gold_fehlt = not gold.is_dir()
    ohne_gold = 0
    for t in tabellen:
        if not t.gold_ordner:
            ergebnis.ohne_gold_quelle.append(
                (t.modell, t.name, any((gold / b / t.name).is_dir() for b in ("dimensions", "facts"))))
            continue
        if gold_fehlt:
            ohne_gold += 1
            continue
        if len(t.gold_ordner) > 1:
            ergebnis.nicht_geprueft.append((f"{t.modell}.{t.name}", f"mehrere Gold-Quellen {t.gold_ordner}"))
            continue
        if t.umformung:
            ergebnis.nicht_geprueft.append((f"{t.modell}.{t.name}", "Partition formt Spalten um"))
            continue
        ordner = t.gold_ordner[0]
        if ordner not in schemata:
            pfad = gold / ordner
            schemata[ordner] = gold_schema(pfad) if pfad.is_dir() else \
                GoldSchema(None, f"Gold-Tabelle {ordner} fehlt ({HOLEN})")
        gs = schemata[ordner]
        if gs.namen is None:
            ergebnis.nicht_geprueft.append((f"{t.modell}.{t.name}", gs.herkunft))
            continue
        namen = gs.namen
        ergebnis.herkunft[ordner] = gs.herkunft
        if gs.log_abweichung:
            ergebnis.log_abweichung[ordner] = gs.log_abweichung
        ergebnis.tabellen_geprueft += 1
        geprueft_tabellen.add((t.modell, t.name))
        for _spalte, quelle in t.quellen:
            ergebnis.geprueft += 1
            if quelle not in namen:
                ergebnis.befunde.add((t.modell, t.name, quelle))
    if ohne_gold:
        ergebnis.nicht_geprueft.append(
            (f"{ohne_gold} Modelltabellen", f"Gold-Ordner {gold} fehlt — holen mit: {HOLEN}"))
    ergebnis.anzahl_nicht_geprueft = ohne_gold + sum(1 for w, _ in ergebnis.nicht_geprueft
                                                     if not w.endswith(" Modelltabellen"))
    ergebnis.neu = sorted(ergebnis.befunde - set(erlaubt))
    # Nur als verschwunden werten, was geprüft wurde — eine ungeprüfte Tabelle ist nicht behoben.
    ergebnis.verschwunden = sorted(k for k in set(erlaubt) - ergebnis.befunde
                                   if (k[0], k[1]) in geprueft_tabellen)
    return ergebnis


def bericht(e: Ergebnis, strict: bool) -> int:
    print(f"Modell gegen Gold: {e.geprueft} sourceColumn in {e.tabellen_geprueft} Modelltabellen geprüft "
          f"gegen {len(e.herkunft)} Gold-Tabellen ({sum(1 for h in e.herkunft.values() if h == 'delta_log')} "
          f"mit Delta-Log, aktive Dateien; {sum(1 for h in e.herkunft.values() if h == 'ohne_log')} "
          f"ohne Log, alle Dateien).")
    print(f"  Befunde: {len(e.befunde)} (davon in der Allowlist {len(e.befunde) - len(e.neu)}, neu {len(e.neu)})")
    for k in e.neu:
        print(f"  NEU        {k[0]}.{k[1]}: sourceColumn '{k[2]}' fehlt in Gold")
    for k in e.verschwunden:
        print(f"  BEHOBEN    {k[0]}.{k[1]}: '{k[2]}' steht jetzt in Gold — aus der Allowlist streichen")
    namens_gleich = sorted({f"{m}.{t}" for m, t, g in e.ohne_gold_quelle if g})
    print(f"  Ohne Gold-Quelle (berechnet/inline, kein Befund): {len(e.ohne_gold_quelle)} Modelltabellen"
          f" — {sorted({t for _, t, _ in e.ohne_gold_quelle})}")
    if namens_gleich:
        print(f"    davon mit gleichnamigem Gold-Ordner, den das Modell nicht liest: {namens_gleich}")
    if e.log_abweichung:
        print(f"  Log-Schema ≠ aktive Dateien (Datenpflege, kein Modellbefund): {len(e.log_abweichung)} Gold-Tabellen")
        for ordner, (nur_log, nur_dateien) in sorted(e.log_abweichung.items()):
            print(f"    {ordner}: nur im Log {list(nur_log)}, nur in Dateien {list(nur_dateien)}")
    for wo, grund in e.nicht_geprueft:
        print(f"  NICHT GEPRÜFT {wo}: {grund}")
    if e.rot:
        print("ROT — Modell und Gold weichen anders ab als die Allowlist "
              "(tooling/validation/model_vs_gold_allowlist.yaml, Ledger A-24).", file=sys.stderr)
        return EXIT_BEFUND
    if e.nicht_geprueft:
        print(f"NICHT GEPRÜFT — {e.anzahl_nicht_geprueft} Modelltabelle(n) ohne Messung; das ist kein Grün.")
        return EXIT_NICHT_GEPRUEFT if strict else EXIT_OK
    print("OK — jede sourceColumn steht in ihrer Gold-Tabelle oder ist als bekannte Lücke geführt. "
          "NICHT geprüft: Datentypen und Werte.")
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dist", type=Path, default=DIST)
    ap.add_argument("--gold", type=Path, default=GOLD)
    ap.add_argument("--allowlist", type=Path, default=ALLOWLIST)
    ap.add_argument("--repo-root", type=Path, default=None,
                    help="Repo-Wurzel (Stage 1 übergibt sie); setzt --dist/--gold/--allowlist relativ dazu")
    ap.add_argument("--strict", action="store_true", help="nicht Geprüftes endet mit Exit 2")
    a = ap.parse_args(argv)
    if a.repo_root:
        r = a.repo_root.resolve()
        a.dist = r / DIST.relative_to(REPO) if a.dist == DIST else a.dist
        a.gold = r / GOLD.relative_to(REPO) if a.gold == GOLD else a.gold
        a.allowlist = r / ALLOWLIST.relative_to(REPO) if a.allowlist == ALLOWLIST else a.allowlist
    return bericht(pruefe(a.dist, a.gold, a.allowlist), a.strict)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
