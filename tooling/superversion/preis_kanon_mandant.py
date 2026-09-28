#!/usr/bin/env python3
"""Mandantenwerte fuer den Preis-Kanon `nagarro` (ADR-0019, Aufgaben N-2 und N-4).

Was hier passiert und was ausdruecklich nicht:

* **Rechnen tut diese Datei nicht.** Der Rechenkern ist Meridians `core/preis_kanon.py`,
  gespiegelt nach `vendor/meridian_dataarch/preis_kanon.py` (ADR-0019 §2.4, Aufgabe N-3).
  Hier steht das Laden, das Pruefen und die Weigerung — kein zweiter Kalkulator
  (Tool-Reuse-Pflicht).
* **Werte liegen nie im Repo.** `preis_kanon_schema.yaml` traegt die Form mit Platzhaltern
  `<...>`; die Zahlen kommen aus `$PREIS_KANON_MANDANTEN_DIR/preis_kanon.yaml` an der
  Nagarro-Ablage (ADR-0019 §2.3, dieselbe Regel wie fuer Kundenmaterial).
* **Ohne Verzeichnis wird nicht gerechnet, sondern gemeldet.** Ein Preis aus Platzhaltern
  waere eine Zahl ohne Herkunft; genau davor steht `MandantenwerteFehlen`.

Drei Ausgaenge, nicht zwei — dieselbe Zusage wie `check_dataarch_mirror.py`, und aus
demselben Grund: ein Tor, das „nichts gefunden" und „nicht gelaufen" gleich misst, misst
beides als Erfolg.

===  ==========================================================================
0    geprueft: Werte geladen, alle Regeln erfuellt
1    Befund: Werte geladen, aber eine Regel verletzt (Platzhalter, fehlender Beleg, ...)
2    konnte nicht pruefen: kein `PREIS_KANON_MANDANTEN_DIR`, kein `preis_kanon.yaml`
===  ==========================================================================

CLI::

    python3 tooling/superversion/preis_kanon_mandant.py schema     # Platzhalter-Pfade
    python3 tooling/superversion/preis_kanon_mandant.py check      # Werte pruefen
    python3 tooling/superversion/preis_kanon_mandant.py preis A1 report=23
    python3 tooling/superversion/preis_kanon_mandant.py vorlage [--ziel DIR]  # Vorlage ausserhalb des Repos
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

SCHEMA_PFAD = Path(__file__).resolve().parent / "preis_kanon_schema.yaml"
ENV_DIR = "PREIS_KANON_MANDANTEN_DIR"
MANDANT = "nagarro"
#: Der Dateiname folgt ADR-0020 (`commercial.authority_path`). Der Mandant steht im Inhalt
#: (`mandanten.nagarro`), nicht im Namen: ein Repo, ein Mandant (ADR-0019). Meridians
#: `core/preis_kanon.yaml` bleibt der Freelancing-Mandant; dies ist der Weg fuer Nagarro.
DATEINAME = "preis_kanon.yaml"
ANNAHME = "ANNAHME, ungeprueft"

#: Ein Platzhalter ist ein String in spitzen Klammern. Bewusst eng: ein Wert wie
#: `<= 5` waere kein Platzhalter, und ein leeres `<>` auch keiner.
_PLATZHALTER = re.compile(r"^<[^<>]+>$")

EXIT_OK = 0
EXIT_BEFUND = 1
EXIT_UNGEPRUEFT = 2

MELDUNG_OHNE_WERTE = (
    f"Mandant {MANDANT}: keine Werte geladen. Das Repo traegt nur das Schema mit "
    f"Platzhaltern (ADR-0019 §2.3); die Saetze liegen an der Nagarro-Ablage. "
    f"${ENV_DIR} auf das Verzeichnis mit {DATEINAME} setzen. Mit Platzhaltern wird nicht "
    f"gerechnet."
)


class MandantenwerteFehlen(RuntimeError):
    """Kein Mandantenverzeichnis, keine Mandantendatei. Kein Preis."""


# ── Schema und Platzhalter ──────────────────────────────────────────────────────────────


def ist_platzhalter(wert: object) -> bool:
    return isinstance(wert, str) and bool(_PLATZHALTER.match(wert.strip()))


def schema() -> dict:
    return yaml.safe_load(SCHEMA_PFAD.read_text(encoding="utf-8"))


def platzhalter_pfade(obj: object, pfad: str = "") -> list[str]:
    """Alle Punktpfade, deren Wert ein Platzhalter ist — Schluessel wie Werte.

    Ein Schluessel wie `<paket-id>` ist selbst ein Platzhalter: er sagt „hier stehen die
    Pakete", nicht „es gibt ein Paket namens <paket-id>".
    """
    out: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            hier = f"{pfad}.{k}" if pfad else str(k)
            if ist_platzhalter(k):
                out.append(hier)
            out.extend(platzhalter_pfade(v, hier))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.extend(platzhalter_pfade(v, f"{pfad}[{i}]"))
    elif ist_platzhalter(obj):
        out.append(pfad)
    return out


# ── Laden ───────────────────────────────────────────────────────────────────────────────


def mandanten_dir() -> Path | None:
    roh = os.environ.get(ENV_DIR)
    if not roh:
        return None
    p = Path(roh).expanduser()
    return p if p.is_dir() else None


def mandanten_datei() -> Path | None:
    d = mandanten_dir()
    if d is None:
        return None
    f = d / DATEINAME
    return f if f.is_file() else None


def lade_mandant(datei: Path | None = None) -> dict:
    """Der Mandantenblock `nagarro`. Wirft `MandantenwerteFehlen`, wenn nichts da ist."""
    f = datei or mandanten_datei()
    if f is None:
        alt = mandanten_dir() / "nagarro.yaml" if mandanten_dir() else None
        if alt is not None and alt.is_file():
            raise MandantenwerteFehlen(
                f"{alt} gefunden, erwartet wird {DATEINAME} (ADR-0020, 26.09.2026). "
                f"Datei umbenennen; der Inhalt bleibt gleich.")
        raise MandantenwerteFehlen(MELDUNG_OHNE_WERTE)
    daten = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
    mandanten = daten.get("mandanten") or {}
    if MANDANT not in mandanten:
        raise MandantenwerteFehlen(
            f"{f}: kein Mandant {MANDANT!r}; gefunden: {sorted(mandanten)}")
    return mandanten[MANDANT]


def kanon(datei: Path | None = None) -> dict:
    """Die Form, die der gespiegelte Rechenkern erwartet: `{'mandanten': {...}}`."""
    return {"mandanten": {MANDANT: lade_mandant(datei)}}


def rechenkern():
    """Meridians `preis_kanon` aus dem Spiegel. Kein Nachbau, kein Fallback."""
    from tooling.superversion import _dataarch_vendor as vendor
    return vendor.load_module("preis_kanon")


# ── Pruefen ─────────────────────────────────────────────────────────────────────────────


def _beleg(befunde: list[str], wo: str, block: dict, herkunft_pflicht: bool = True) -> None:
    """Belegpflicht R1 an einem Block: Status und Herkunft, und `gemessen` nur mit Methode."""
    if "status" not in block:
        befunde.append(f"{wo}: kein `status` (Belegpflicht R1)")
        return
    status = str(block.get("status", ""))
    if herkunft_pflicht and "herkunft" not in block:
        befunde.append(f"{wo}: kein `herkunft` (Belegpflicht R1)")
        return
    herkunft = str(block.get("herkunft", ""))
    if status != ANNAHME and herkunft_pflicht and "gemessen" not in herkunft:
        befunde.append(f"{wo}: Status {status!r} ohne 'gemessen' in der Herkunft "
                       f"(R1: Zahl und Methode im selben Satz)")


def pruefe_mandant(m: dict) -> list[str]:
    """ALUCAs Regeln fuer den Team-Mandanten; leer = in Ordnung.

    Bewusst **nicht** `pruefe_kanon()` aus dem Spiegel: die Funktion erzwingt genau einen
    Mandanten `freelancing` (Freelancing D-357) und wuerde `nagarro` per Konstruktion
    zurueckweisen. Die Formel-Regeln sind dieselben, die Mandanten-Regel ist eine andere.
    """
    befunde: list[str] = []

    offen = platzhalter_pfade(m)
    if offen:
        befunde.append(f"{len(offen)} Platzhalter unbefuellt: {', '.join(offen[:5])}"
                       + (" …" if len(offen) > 5 else ""))

    rollen = set(m.get("rollen") or [])
    standorte = set(m.get("standorte") or [])
    if not rollen:
        befunde.append("keine Rollen (ADR-0019 §2.2: Satzklasse = Rolle × Standort)")
    if not standorte:
        befunde.append("keine Standorte (ADR-0019 §2.2)")

    _beleg(befunde, "marge_m", m.get("marge_m") or {})
    _beleg(befunde, "risikozuschlag_r", m.get("risikozuschlag_r") or {})

    klassen = m.get("satzklassen") or {}
    if not klassen:
        befunde.append("keine Satzklassen")
    for k, sk in klassen.items():
        rolle, standort = sk.get("rolle"), sk.get("standort")
        if rolle not in rollen:
            befunde.append(f"Satzklasse {k}: Rolle {rolle!r} steht nicht in `rollen`")
        if standort not in standorte:
            befunde.append(f"Satzklasse {k}: Standort {standort!r} steht nicht in `standorte`")
        if rolle and standort and k != f"{rolle}_{standort}":
            befunde.append(f"Satzklasse {k}: Schluessel muss `<rolle>_<standort>` sein "
                           f"({rolle}_{standort})")
        if "kostensatz_eur_h" not in sk:
            befunde.append(f"Satzklasse {k}: kein `kostensatz_eur_h`")
        _beleg(befunde, f"Satzklasse {k}", sk)

    # Team-Kapazitaet (ADR-0019 §2.5): jede Rolle, die eine Satzklasse traegt, muss auch
    # verfuegbar sein — sonst plant der Kalender mit einer Rolle, die niemand besetzt.
    verf = m.get("verfuegbarkeit") or {}
    for rolle in sorted({sk.get("rolle") for sk in klassen.values() if sk.get("rolle")}):
        if rolle not in verf:
            befunde.append(f"Rolle {rolle!r} hat eine Satzklasse, aber keine Verfuegbarkeit "
                           f"(ADR-0019 §2.5)")
    for rolle, v in verf.items():
        fehlend = [f for f in ("koepfe", "fakturierbare_stunden_je_tag",
                               "fakturierbare_tage_je_woche", "arbeitstage_je_woche",
                               "arbeitswochen_je_jahr") if f not in v]
        if fehlend:
            befunde.append(f"Verfuegbarkeit {rolle}: fehlt {', '.join(fehlend)}")

    for pid, p in (m.get("pakete") or {}).items():
        kalk = p.get("kalkulation") or {}
        _beleg(befunde, f"{pid} Kalkulation", kalk)

        treiber = set((kalk.get("mengentreiber") or {}))
        for a in kalk.get("aufgaben") or []:
            if a.get("klasse") not in klassen:
                befunde.append(f"{pid}: Aufgabe {a.get('name')!r} nennt Satzklasse "
                               f"{a.get('klasse')!r}, die es nicht gibt")
            if "stunden" not in a and "stunden_je" not in a:
                befunde.append(f"{pid}: Aufgabe {a.get('name')!r} ohne Stunden")
            if "stunden_je" in a and a.get("treiber") not in treiber:
                befunde.append(f"{pid}: Aufgabe {a.get('name')!r} nennt Treiber "
                               f"{a.get('treiber')!r} ohne Mengentreiber")

        bet = kalk.get("beteiligung") or {}
        for rolle in bet:
            if rolle not in rollen:
                befunde.append(f"{pid}: Beteiligung nennt Rolle {rolle!r}, die es nicht gibt")
        if bet:
            summe = sum(float(v) for v in bet.values() if not ist_platzhalter(v))
            if abs(summe - 100.0) > 1e-6:
                befunde.append(f"{pid}: Beteiligung summiert auf {summe:g} % statt 100 (D-355)")
        elif not kalk.get("aufgaben"):
            befunde.append(f"{pid}: weder Beteiligung noch Aufgaben — kein Blatt")

        tm = p.get("abrechnung") == "tm"
        if tm and p.get("festpreis"):
            befunde.append(f"{pid}: T&M-Paket mit Festpreis")
        if not tm and not p.get("festpreis"):
            befunde.append(f"{pid}: weder Festpreis noch `abrechnung: tm`")
        for t in ((p.get("festpreis") or {}).get("je_einheit_eur") or {}):
            if t not in treiber:
                befunde.append(f"{pid}: Festpreis-Treiber {t!r} ohne Mengentreiber")

        lz = p.get("lieferzeit") or {}
        if p.get("tier") == 2 and "band_at" not in lz:
            befunde.append(f"{pid}: Tier 2 ohne Lieferzeit-Band (D-355)")
        if not lz:
            befunde.append(f"{pid}: keine Lieferzeit (Kanon-Regel: Preis und Lieferzeit zusammen)")
        elif "status" not in lz:
            befunde.append(f"{pid} Lieferzeit: kein `status` (Belegpflicht R1)")

    return befunde


# ── Personentage mit Herkunft (ADR-0019 §4) ─────────────────────────────────────────────


def personentage(m: dict, paket_id: str, mengen: dict | None = None) -> list[dict]:
    """Kanon-Tage je Rolle: Lieferzeit-Band × Beteiligung, jede Zahl mit Herkunft.

    Keine Schaetzung je Kunde (ADR-0019 §4) — beide Faktoren stehen im Kanon. Das Band
    bleibt ein Band; wer eine einzelne Zahl will, muss sagen, welches Ende er meint.
    """
    pk = rechenkern()
    p = pk.paket(m, paket_id)
    lo, hi = pk.lieferzeit_band(p, mengen)
    bet = ((p.get("kalkulation") or {}).get("beteiligung") or {})
    return [{
        "rolle": rolle,
        "beteiligung_pct": float(anteil),
        "tage_min": lo * float(anteil) / 100.0,
        "tage_max": hi * float(anteil) / 100.0,
        "herkunft": (f"Paket {paket_id}, Lieferzeit-Band {lo:g}–{hi:g} AT "
                     f"({pk.lieferzeit_status(p)}) × Beteiligung {float(anteil):g} % (D-355)"),
    } for rolle, anteil in sorted(bet.items())]


# ── Team-Kapazitaet statt Ein-Personen-Sequenz (ADR-0019 §2.5, Aufgabe N-5) ──────────────


def kapazitaet_je_rolle(m: dict) -> dict[str, dict]:
    """Verfuegbare Stunden je Rolle und Kalender-Arbeitstag.

    Die Formel wird nicht nachgebaut: `stunden_je_kalender_at()` aus dem gespiegelten Kern
    rechnet sie bereits, sie liest ihren Block unter `auslastung`. Hier steht derselbe Block
    je Rolle unter `verfuegbarkeit`, also bekommt der Kern ihn genau so gereicht. Der
    Unterschied zum Freelancing-Repo ist der Faktor `koepfe` — dort ist er eins und heisst
    nicht so (D-357).
    """
    pk = rechenkern()
    out: dict[str, dict] = {}
    for rolle, v in (m.get("verfuegbarkeit") or {}).items():
        je_kopf = pk.stunden_je_kalender_at({"auslastung": v})
        koepfe = float(v.get("koepfe", 1))
        out[rolle] = {
            "koepfe": koepfe,
            "stunden_je_at_und_kopf": je_kopf,
            "stunden_je_at": je_kopf * koepfe,
            "stunden_je_jahr": pk.fakturierbare_stunden_je_jahr({"auslastung": v}) * koepfe,
        }
    return out


def _rolle_je_klasse(m: dict) -> dict[str, str]:
    return {k: sk.get("rolle") for k, sk in (m.get("satzklassen") or {}).items()}


def stunden_je_rolle(m: dict, paket_id: str, mengen: dict | None = None) -> dict[str, float]:
    """Die Paketstunden aus dem Kern, von Satzklassen auf Rollen zusammengezogen."""
    pk = rechenkern()
    zuordnung = _rolle_je_klasse(m)
    out: dict[str, float] = {}
    for klasse, h in pk.stunden(pk.paket(m, paket_id), mengen).items():
        rolle = zuordnung.get(klasse, klasse)
        out[rolle] = out.get(rolle, 0.0) + h
    return out


def kapazitaetspruefung(m: dict, pakete: list[tuple[str, dict | None]]) -> dict:
    """Passt der Stundenbedarf mehrerer Pakete in die Verfuegbarkeit des Teams?

    Der Unterschied zur Ein-Personen-Sequenz steht in einer Zeile: dort addieren sich die
    Lieferzeit-Baender, weil eine Person nacheinander liefert; hier laufen die Pakete
    parallel, das Fenster ist also das **laengste** Band, nicht ihre Summe (ADR-0019 §2.5).
    Beide Zahlen werden ausgewiesen, damit der Unterschied ablesbar bleibt.

    Gemeldet wird ein Vermerk, keine gebogene Zahl: wenn der Bedarf nicht passt, ist die
    Frage, ob Koepfe dazukommen oder das Fenster waechst, und das entscheidet ein Mensch.
    """
    pk = rechenkern()
    kap = kapazitaet_je_rolle(m)

    bedarf: dict[str, float] = {}
    baender: list[tuple[float, float]] = []
    for pid, mengen in pakete:
        for rolle, h in stunden_je_rolle(m, pid, mengen).items():
            bedarf[rolle] = bedarf.get(rolle, 0.0) + h
        baender.append(pk.lieferzeit_band(pk.paket(m, pid), mengen))

    fenster_parallel = max((hi for _, hi in baender), default=0.0)
    fenster_seriell = sum(hi for _, hi in baender)

    zeilen = []
    for rolle in sorted(bedarf):
        k = kap.get(rolle)
        if k is None:
            zeilen.append({"rolle": rolle, "stunden": bedarf[rolle], "passt": None,
                           "vermerk": f"Rolle {rolle!r} hat keine Verfuegbarkeit in der "
                                      f"Mandantendatei — nicht pruefbar"})
            continue
        angebot = k["stunden_je_at"] * fenster_parallel
        passt = bedarf[rolle] <= angebot + 1e-9
        zeilen.append({
            "rolle": rolle,
            "stunden": bedarf[rolle],
            "verfuegbar_im_fenster": angebot,
            "koepfe": k["koepfe"],
            "passt": passt,
            "vermerk": ("" if passt else
                        f"{bedarf[rolle]:.0f} h Bedarf gegen {angebot:.0f} h in "
                        f"{fenster_parallel:g} AT bei {k['koepfe']:g} Kopf/Koepfen — "
                        f"mehr Koepfe oder laengeres Fenster, keine gebogene Zahl"),
        })

    return {
        "fenster_at_parallel": fenster_parallel,
        "fenster_at_seriell": fenster_seriell,
        "rollen": zeilen,
        "vermerke": [z["vermerk"] for z in zeilen if z["vermerk"]],
    }


# ── Vorlage fuer die Nagarro-Ablage ─────────────────────────────────────────────────────


def vorlage(ziel: Path | None = None) -> Path:
    """Schreibt das Schema mit Platzhaltern als `preis_kanon.yaml` in die Mandantenablage.

    Der Weg fuer Nagarro: Verzeichnis anlegen, Vorlage erzeugen, Platzhalter an der
    Nagarro-Ablage befuellen, `check` laufen lassen. Nie ins Repo, nie ueberschreiben.
    """
    roh = ziel if ziel is not None else os.environ.get(ENV_DIR)
    if not roh:
        raise MandantenwerteFehlen(f"Kein Ziel: --ziel angeben oder ${ENV_DIR} setzen.")
    d = Path(roh).expanduser().resolve()
    repo = REPO_ROOT.resolve()
    if d == repo or repo in d.parents:
        raise ValueError(f"{d} liegt im Repository; Mandantenwerte gehoeren an die Nagarro-Ablage (ADR-0019 §2.3).")
    d.mkdir(parents=True, exist_ok=True)
    f = d / DATEINAME
    if f.exists():
        raise FileExistsError(f"{f} existiert bereits; eine Vorlage ueberschreibt keine Werte.")
    kopf = ("# Preis-Kanon Mandant nagarro (ADR-0019/0020). Vorlage aus tooling/superversion/"
            "preis_kanon_schema.yaml.\n# Platzhalter <...> ersetzen; danach: preis_kanon_mandant.py check\n")
    f.write_text(kopf + SCHEMA_PFAD.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    return f


# ── CLI ─────────────────────────────────────────────────────────────────────────────────


def _cmd_schema() -> int:
    pfade = platzhalter_pfade(schema().get("mandanten") or {})
    print(f"[preis-kanon-mandant] {SCHEMA_PFAD.relative_to(REPO_ROOT)}: {len(pfade)} Platzhalter")
    for pf in pfade:
        print(f"  {pf}")
    return EXIT_OK


def _cmd_check() -> int:
    try:
        m = lade_mandant()
    except MandantenwerteFehlen as e:
        print(f"[preis-kanon-mandant] {e}")
        print("[preis-kanon-mandant] KONNTE NICHT PRUEFEN — das ist kein bestandener Test")
        return EXIT_UNGEPRUEFT
    befunde = pruefe_mandant(m)
    if befunde:
        print(f"[preis-kanon-mandant] {len(befunde)} Befund(e) in {mandanten_datei()}:")
        for b in befunde:
            print(f"  {b}")
        return EXIT_BEFUND
    pakete = len(m.get("pakete") or {})
    print(f"[preis-kanon-mandant] OK — Mandant {MANDANT}: {len(m.get('satzklassen') or {})} "
          f"Satzklasse(n), {pakete} Paket(e), geladen aus {mandanten_datei()}")
    return EXIT_OK


def _cmd_preis(paket_id: str, mengen_roh: list[str]) -> int:
    try:
        m = lade_mandant()
    except MandantenwerteFehlen as e:
        print(f"[preis-kanon-mandant] {e}")
        return EXIT_UNGEPRUEFT
    mengen = {}
    for teil in mengen_roh:
        k, _, v = teil.partition("=")
        mengen[k] = float(v)
    pk = rechenkern()
    p = pk.paket(m, paket_id)
    blatt = pk.kalkulation(m, p, mengen or None)
    for zeile, wert in blatt.items():
        print(f"  {zeile}: {wert}")
    for t in personentage(m, paket_id, mengen or None):
        print(f"  Personentage {t['rolle']}: {t['tage_min']:.1f}–{t['tage_max']:.1f} AT "
              f"— {t['herkunft']}")
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("schema", help="Platzhalter-Pfade des Repo-Schemas")
    sub.add_parser("check", help="Mandantenwerte laden und pruefen")
    pr = sub.add_parser("preis", help="Kalkulationsblatt eines Pakets")
    pr.add_argument("paket")
    pr.add_argument("mengen", nargs="*")
    vo = sub.add_parser("vorlage", help="Vorlage mit Platzhaltern in die Mandantenablage schreiben")
    vo.add_argument("--ziel", type=Path)
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    if a.cmd == "schema":
        return _cmd_schema()
    if a.cmd == "vorlage":
        try:
            print(f"[preis-kanon-mandant] Vorlage geschrieben: {vorlage(a.ziel)}")
            return EXIT_OK
        except (MandantenwerteFehlen, ValueError, FileExistsError) as e:
            print(f"[preis-kanon-mandant] {e}")
            return EXIT_UNGEPRUEFT
    if a.cmd == "check":
        return _cmd_check()
    return _cmd_preis(a.paket, a.mengen)


if __name__ == "__main__":
    raise SystemExit(main())
