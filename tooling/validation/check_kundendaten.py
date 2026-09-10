#!/usr/bin/env python3
"""Prueft versionierte Dateien auf Kundenkennungen.

Das Skript selbst enthaelt keine Kundennamen. Es liest sie aus einer Sperrliste,
die bewusst ausserhalb der Versionsverwaltung liegt.

Aufruf:
    python3 tooling/validation/check_kundendaten.py                    # alle getrackten Dateien
    python3 tooling/validation/check_kundendaten.py --staged           # nur was committet werden soll
    python3 tooling/validation/check_kundendaten.py --repo ../anderes  # anderes Repository
    python3 tooling/validation/check_kundendaten.py --bericht b.md     # Befunde als Markdown

Rueckgabewert 1, sobald ein Treffer gefunden wird.

Sperrliste: .kundendaten-sperrliste.json im Repowurzelverzeichnis, gitignoriert.
Fehlt sie, bricht das Skript ab statt still zu bestehen. Ein Pruefer, der ohne
seine Regeln gruen meldet, ist schlimmer als keiner.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SPERRLISTE = ".kundendaten-sperrliste.json"

# Dateiendungen, die nicht als Text geprueft werden
BINAER = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".gz", ".7z",
    ".xlsx", ".xls", ".docx", ".doc", ".pptx", ".ppt", ".woff", ".woff2",
    ".ttf", ".eot", ".mp4", ".mov", ".pbix", ".pbip",
}

MAX_BYTES = 2_000_000


def repo_wurzel(start: Path) -> Path:
    r = subprocess.run(
        ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
        capture_output=True, text=True,
        encoding="utf-8", errors="replace")
    if r.returncode != 0:
        sys.exit(f"kein Git-Repository: {start}")
    return Path(r.stdout.strip())


def sperrliste_laden(wurzel: Path) -> dict:
    p = wurzel / SPERRLISTE
    if not p.exists():
        sys.exit(
            f"Sperrliste fehlt: {p}\n"
            "Ohne Sperrliste prueft dieses Skript nichts und meldet deshalb keinen Erfolg.\n"
            "Vorlage: scripts/kundendaten-sperrliste.beispiel.json (ALUCA)"
        )
    try:
        daten = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"Sperrliste ist kein gueltiges JSON: {e}")
    if not daten.get("begriffe") and not daten.get("muster"):
        sys.exit("Sperrliste enthaelt weder 'begriffe' noch 'muster'")
    return daten


def regeln_bauen(daten: dict) -> list[tuple[str, re.Pattern]]:
    """Ein kombiniertes Muster je Kategorie.

    Einzelne Muster je Begriff waeren lesbarer, sind bei einigen hundert Dateien
    aber zu langsam: die Laufzeit waechst mit Zeilen mal Regeln. Die Alternation
    laesst die Regex-Maschine einmal ueber den Text laufen.
    """
    regeln: list[tuple[str, re.Pattern]] = []

    for kategorie, begriffe in (daten.get("begriffe") or {}).items():
        teile = [re.escape(b) for b in begriffe if b]
        if not teile:
            continue
        # Wortgrenze aus Buchstaben und Ziffern - bewusst OHNE `_` und `-`.
        #
        # Die erste Fassung nahm `(?<![\w-])...(?![\w-])`. Die Absicht war richtig
        # (ein kurzer Name soll nicht mitten in einem Wort treffen: `HTI` in
        # "richtig"), die Umsetzung liess aber genau die haeufigste Schreibweise
        # durch, in der Kundenkennungen tatsaechlich auftauchen - als Namensteil
        # zwischen Trennern: `HTF-Import`, `htf_ledger_package_1_0`,
        # `NicLen_Auftragseingaenge`, `check_contoso.py`.
        #
        # Gemessen am 04.09.2026 in diesem Repo: die enge Fassung meldete 0 Treffer,
        # die hier verwendete 3 - alle drei echt, kein Fehlalarm. `HTI` in "richtig"
        # bleibt blockiert, weil davor ein Buchstabe steht.
        teile.sort(key=len, reverse=True)
        regeln.append(
            (kategorie,
             re.compile(rf"(?<![A-Za-z0-9])(?:{'|'.join(teile)})(?![A-Za-z0-9])", re.I))
        )

    for kategorie, muster in (daten.get("muster") or {}).items():
        teile = [m for m in muster if m]
        if not teile:
            continue
        try:
            regeln.append((kategorie, re.compile("|".join(f"(?:{m})" for m in teile), re.I)))
        except re.error as e:
            sys.exit(f"ungueltiges Muster in Sperrliste [{kategorie}]: {e}")

    return regeln


def dateien(wurzel: Path, nur_staged: bool) -> list[str]:
    if nur_staged:
        cmd = ["git", "-C", str(wurzel), "diff", "--cached", "--name-only", "--diff-filter=ACMR"]
    else:
        cmd = ["git", "-C", str(wurzel), "ls-files"]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return [z for z in r.stdout.splitlines() if z.strip()]


def pruefen(wurzel: Path, nur_staged: bool, daten: dict, teil: str = "alle") -> list[dict]:
    """Sucht ueber `git grep`.

    Die Dateien in Python einzeln zu lesen ist ueber ein eingehaengtes
    Netzlaufwerk zu langsam. `git grep` kennt die versionierten Dateien,
    ueberspringt Binaerdateien mit -I und ist in C geschrieben.
    """
    regeln = regeln_bauen(daten)
    ausnahmen = [re.compile(p) for p in (daten.get("ausnahmen_pfade") or [])]
    erlaubt = set(x.lower() for x in (daten.get("erlaubte_treffer") or []))

    if nur_staged:
        # Nur die Dateien dieses Commits. `git grep --cached` allein durchsucht den
        # ganzen Index, also auch alles, was der Commit gar nicht anfasst. Ein Hook,
        # der daran scheitert, blockiert jeden Commit bis zur vollstaendigen
        # Altbereinigung und wird nach dem zweiten Mal umgangen.
        geaendert = dateien(wurzel, True)
        if not geaendert:
            return []
        ausschluss = ["--"] + geaendert
    else:
        ausschluss = ["--", ".",
                      ":(exclude)node_modules/**", ":(exclude).venv/**",
                      ":(exclude)**/node_modules/**", ":(exclude)**/*.lock",
                      ":(exclude)package-lock.json", ":(exclude)**/dist/**"]

    rohzeilen: list[str] = []

    # Zwei Laeufe. Feste Zeichenketten sind mit -F deutlich schneller als eine
    # Alternation, und die Muster mit Ziffernklassen sind der teure Teil.
    if teil in ("alle", "begriffe"):
        begriffe = [b for gruppe in (daten.get("begriffe") or {}).values() for b in gruppe if b]
        if begriffe:
            cmd = ["git", "-C", str(wurzel), "grep", "-nIiF", "--no-color"]
            if nur_staged:
                cmd.append("--cached")
            for b in begriffe:
                cmd += ["-e", b]
            rohzeilen += _git_grep(cmd + ausschluss)

    if teil in ("alle", "muster"):
        muster = [m for gruppe in (daten.get("muster") or {}).values() for m in gruppe if m]
        if muster:
            cmd = ["git", "-C", str(wurzel), "grep", "-nIiE", "--no-color"]
            if nur_staged:
                cmd.append("--cached")
            cmd += ["-e", "|".join(f"({m})" for m in muster)]
            rohzeilen += _git_grep(cmd + ausschluss)

    befunde: list[dict] = []
    gesehen: set[tuple] = set()

    for zeile in rohzeilen:
        teile = zeile.split(":", 2)
        if len(teile) < 3 or not teile[1].isdigit():
            continue
        rel, nr, inhalt = teile[0], int(teile[1]), teile[2]
        if any(a.search(rel) for a in ausnahmen):
            continue
        if Path(rel).suffix.lower() in BINAER:
            continue

        # git grep sucht bewusst grob. Die genaue Zuordnung samt Wortgrenzen
        # passiert hier, sonst schlaegt ein kurzer Name mitten in einem Wort an.
        for kategorie, muster in regeln:
            m = muster.search(inhalt)
            if not m:
                continue
            treffer = m.group(0)
            if treffer.lower() in erlaubt:
                continue
            schluessel = (rel, nr, kategorie, treffer.lower())
            if schluessel in gesehen:
                continue
            gesehen.add(schluessel)
            befunde.append({
                "datei": rel,
                "zeile": nr,
                "kategorie": kategorie,
                "treffer": treffer,
                "text": inhalt.strip()[:160],
            })

    befunde.sort(key=lambda b: (b["datei"], b["zeile"], b["kategorie"]))
    return befunde


def _git_grep(cmd: list[str]) -> list[str]:
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace", encoding="utf-8")
    if r.returncode not in (0, 1):
        raise RuntimeError(f"git grep endete mit {r.returncode}: {r.stderr.strip()[:300]}")
    return r.stdout.splitlines()


def bericht_schreiben(pfad: Path, befunde: list[dict], wurzel: Path) -> None:
    nach_kategorie: dict[str, list[dict]] = {}
    for b in befunde:
        nach_kategorie.setdefault(b["kategorie"], []).append(b)

    zeilen = [
        "# Befunde: Kundenkennungen in versionierten Dateien",
        "",
        f"**Repository:** `{wurzel.name}`",
        f"**Treffer gesamt:** {len(befunde)} in {len({b['datei'] for b in befunde})} Dateien",
        "",
    ]
    for kategorie in sorted(nach_kategorie):
        eintraege = nach_kategorie[kategorie]
        dateien_k = sorted({e["datei"] for e in eintraege})
        zeilen += [
            f"## {kategorie}",
            "",
            f"{len(eintraege)} Treffer in {len(dateien_k)} Dateien.",
            "",
            "| Datei | Zeile | Treffer | Kontext |",
            "|---|---|---|---|",
        ]
        for e in eintraege:
            ktx = e["text"].replace("|", "\\|")
            zeilen.append(f"| `{e['datei']}` | {e['zeile']} | `{e['treffer']}` | {ktx} |")
        zeilen.append("")

    pfad.write_text("\n".join(zeilen), encoding="utf-8", newline="\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="Prueft versionierte Dateien auf Kundenkennungen")
    ap.add_argument("--repo", default=".", help="Pfad in das zu pruefende Repository")
    ap.add_argument("--staged", action="store_true", help="nur die zum Commit vorgemerkten Dateien")
    ap.add_argument("--sperrliste", help="abweichender Pfad zur Sperrliste")
    ap.add_argument("--bericht", help="Befunde zusaetzlich als Markdown ablegen")
    ap.add_argument("--leise", action="store_true", help="nur die Zusammenfassung ausgeben")
    ap.add_argument("--teil", choices=["alle", "begriffe", "muster"], default="alle",
                    help="Teillauf. Ueber langsame Dateisysteme getrennt ausfuehren")
    args = ap.parse_args()

    wurzel = repo_wurzel(Path(args.repo).resolve())

    if args.sperrliste:
        quelle = Path(args.sperrliste)
        if not quelle.exists():
            sys.exit(f"Sperrliste nicht gefunden: {quelle}")
        daten = json.loads(quelle.read_text(encoding="utf-8"))
    else:
        daten = sperrliste_laden(wurzel)

    try:
        befunde = pruefen(wurzel, args.staged, daten, args.teil)
    except RuntimeError as e:
        # Ein Pruefer, der nach einem Fehler gruen meldet, ist gefaehrlicher als keiner.
        print(f"[ABBRUCH] {e}", file=sys.stderr)
        return 2

    if args.bericht:
        bericht_schreiben(Path(args.bericht), befunde, wurzel)

    if not befunde:
        print(f"[OK] {wurzel.name}: keine Kundenkennungen in versionierten Dateien")
        return 0

    if not args.leise:
        for b in befunde:
            print(f"{b['datei']}:{b['zeile']}: [{b['kategorie']}] {b['treffer']}  {b['text']}")
        print()

    dateien_gesamt = len({b["datei"] for b in befunde})
    kategorien = sorted({b["kategorie"] for b in befunde})
    print(f"[FEHLER] {len(befunde)} Treffer in {dateien_gesamt} Dateien: {', '.join(kategorien)}")
    print("Kundenkennungen gehoeren nicht in dieses Repository.")
    print("Herkunftsvermerke behalten Datum und Methode und verlieren die Zuordnung.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
