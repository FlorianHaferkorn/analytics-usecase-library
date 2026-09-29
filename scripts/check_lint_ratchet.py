#!/usr/bin/env python3
"""check_lint_ratchet — Ruff-Befunde je Regel einfrieren, damit sie nur noch fallen koennen.

Portiert aus Freelancing ``scripts/check_lint_ratchet.py`` (dort seit 15.08.2026), hier
generisch gehalten: die Ruff-Konfiguration (``select``, ``extend-exclude`` …) kommt allein
aus ``[tool.ruff]`` der ``pyproject.toml``, das Skript kennt keine Pfade oder Regeln.

## Der Anlass (29.09.2026)

Ruff lief in diesem Repository nirgends. ``.pre-commit-config.yaml`` nennt ihn, aber das
Framework ist nicht installiert (der Hook unter ``tooling/git-hooks/pre-commit`` ruft es
nicht), und kein Workflow startet ihn. Gemessen mit ruff 0.16.9 und der Konfiguration aus
``pyproject.toml``: 2768 Befunde in 15 Regeln. Das auf einmal scharf zu schalten waere am
ersten Tag vierstellig rot. Deshalb **Sperrklinke statt Tor**: der Stand wird je Regel
eingefroren und darf nur sinken.

## Warum je Regel und nicht als Summe

Eine Gesamtzahl liesse sich zufaellig freikaufen: wer 30 Leerzeilen mit Leerzeichen
bereinigt, duerfte gleichzeitig ein ``F821 undefined-name`` einschleppen. Je Regel
eingefroren faellt jede neue Auspraegung auf, egal was daneben besser wurde.

Lauf: ``python3 scripts/check_lint_ratchet.py`` · ``--update-baseline`` schreibt den
erreichten Stand fest (hebt die Latte nie an).

## Drei Ausgaenge (seit 29.09.2026)

- **0** — gelaufen, keine Regel ueber ihrem eingefrorenen Stand.
- **1** — gelaufen, mindestens eine Regel gestiegen (oder keine Baseline).
- **2** — **nicht gelaufen**: kein Ruff gefunden, Ruff brach ab, oder (mit ``--pin-pflicht``)
  die gefundene Version weicht vom Pin ab.

Vorher endete ein Anstieg ohne ``--strict`` mit 0, und ein fehlendes Ruff war in jedem
Modus 0 — der pre-commit-Hook rief das Skript mit dem System-``python3`` auf, in dem Ruff
kein Modul war (das Binary lag im PATH), und meldete bei jedem Commit ``SKIP`` mit Exit 0.
Ein Tor muss „nichts gefunden" von „nicht gelaufen" unterscheiden; deshalb ist der
Anstieg jetzt immer rot und „nicht gelaufen" ein eigener Code. ``--strict`` bleibt als
wirkungsloser Schalter stehen, damit bestehende Aufrufe gueltig bleiben. Was der Aufrufer
aus 2 macht, entscheidet er: die CI und ``tooling/run_local_ci_check.sh`` werden rot, der
pre-commit-Hook schreibt ein lautes ``[UNGEPRUEFT]``.

## Wo Ruff herkommt

Zuerst ein ``ruff``-Binary im PATH, dann ``python -m ruff`` im laufenden Interpreter. Die
Zahlen haengen an der Ruff-Version; der Pin steht an genau einer Stelle, der ``pip``-Zeile
in ``.github/workflows/stage1.yml``, und wird von dort gelesen. Von den Kandidaten gewinnt
der erste mit Pin-Version, sonst der erste gefundene mit Warnung. ``--pin-pflicht`` (CI)
macht die Abweichung zu Ausgang 2.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
BASELINE = pathlib.Path(__file__).resolve().parent / "lint_baseline.json"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "stage1.yml"

NICHT_GELAUFEN = 2


def ruff_pin(workflow: pathlib.Path | None = None) -> str | None:
    """Die gepinnte Ruff-Version aus der CI-``pip``-Zeile — oder ``None``."""
    pfad = workflow or WORKFLOW
    try:
        m = re.search(r"\bruff==([0-9][0-9A-Za-z.]*)", pfad.read_text("utf-8"))
    except OSError:
        return None
    return m.group(1) if m else None


def _version(befehl: list[str]) -> str | None:
    try:
        p = subprocess.run([*befehl, "--version"], capture_output=True, text=True, timeout=30,
                           encoding="utf-8", errors="replace")
    except (OSError, subprocess.TimeoutExpired):
        return None
    m = re.match(r"ruff\s+(\S+)", (p.stdout or "").strip())
    return m.group(1) if p.returncode == 0 and m else None


def ruff_kandidaten() -> list[tuple[list[str], str]]:
    """``[(befehl, version)]`` in Suchreihenfolge: Binary im PATH, dann ``python -m ruff``."""
    befehle: list[list[str]] = []
    binary = shutil.which("ruff")
    if binary:
        befehle.append([binary])
    befehle.append([sys.executable, "-m", "ruff"])
    return [(b, v) for b in befehle if (v := _version(b))]


def finde_ruff(pin: str | None) -> tuple[list[str] | None, str | None, list[str]]:
    """``(befehl, version, alle_gefundenen)`` — Pin-Version bevorzugt, sonst der erste."""
    kandidaten = ruff_kandidaten()
    gefunden = [f"{' '.join(b)} ({v})" for b, v in kandidaten]
    for b, v in kandidaten:
        if pin and v == pin:
            return b, v, gefunden
    if kandidaten:
        return kandidaten[0][0], kandidaten[0][1], gefunden
    return None, None, gefunden


def ruff_befunde(befehl: list[str] | None = None) -> collections.Counter | None:
    """``{regel: anzahl}`` — oder ``None``, wenn Ruff fehlt oder nicht lief."""
    if befehl is None:
        befehl = finde_ruff(ruff_pin())[0]
        if befehl is None:
            return None
    try:
        p = subprocess.run([*befehl, "check", ".", "--output-format=json",
                            "--no-cache", "--exit-zero"],
                           cwd=REPO_ROOT, capture_output=True, text=True, timeout=300,
                           encoding="utf-8", errors="replace")
    except (OSError, subprocess.TimeoutExpired):
        return None
    if p.returncode != 0:
        # "No module named ruff" oder ein Konfigurationsfehler: nicht gelaufen, nicht "0 Befunde".
        return None
    try:
        befunde = json.loads(p.stdout or "[]")
    except json.JSONDecodeError:
        return None
    # Syntaxfehler tragen keinen Regelcode; sie zaehlen als eigene Klasse.
    return collections.Counter((b.get("code") or "syntax-error") for b in befunde)


def lade_baseline(pfad: pathlib.Path | None = None) -> dict[str, int]:
    pfad = pfad or BASELINE
    if not pfad.exists():
        return {}
    return json.loads(pfad.read_text("utf-8"))["regeln"]


def vergleich(jetzt: collections.Counter, basis: dict[str, int]) -> tuple[list[str], list[str]]:
    """``(gestiegen, gesunken)`` — je Regel, im Klartext. Unbekannte Regel = Basis 0."""
    gestiegen, gesunken = [], []
    for regel in sorted(set(jetzt) | set(basis)):
        ist, soll = jetzt.get(regel, 0), basis.get(regel, 0)
        if ist > soll:
            gestiegen.append(f"{regel}: {soll} -> {ist} (+{ist - soll})")
        elif ist < soll:
            gesunken.append(f"{regel}: {soll} -> {ist}")
    return gestiegen, gesunken


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Ruff-Sperrklinke (Befunde duerfen je Regel nur sinken)")
    ap.add_argument("--strict", action="store_true",
                    help="wirkungslos seit 29.09.2026 (Anstieg ist immer Exit 1); bleibt fuer Altaufrufe")
    ap.add_argument("--pin-pflicht", action="store_true",
                    help="Ruff-Version muss dem Pin in stage1.yml entsprechen, sonst Exit 2 (CI)")
    ap.add_argument("--update-baseline", action="store_true",
                    help="erreichten Stand festschreiben (hebt die Latte nie an)")
    a = ap.parse_args(argv)

    pin = ruff_pin()
    befehl, version, gefunden = finde_ruff(pin)
    installhinweis = f"`pip install ruff=={pin}`" if pin else "`pip install ruff`"
    if befehl is None:
        print("[check-lint-ratchet] NICHT GELAUFEN — kein ruff gefunden (weder `ruff` im PATH "
              f"noch `{os.path.basename(sys.executable)} -m ruff`). Installieren: {installhinweis}.")
        return NICHT_GELAUFEN
    if pin is None and a.pin_pflicht:
        print(f"[check-lint-ratchet] NICHT GELAUFEN — kein ruff-Pin in {WORKFLOW.relative_to(REPO_ROOT)} "
              "gefunden; --pin-pflicht kann die Version nicht pruefen.")
        return NICHT_GELAUFEN
    if pin and version != pin:
        text = (f"ruff {version} ({' '.join(befehl)}) statt Pin {pin}; gefunden: "
                f"{', '.join(gefunden)}. Die Zaehlung je Regel kann sich zwischen Versionen "
                f"unterscheiden. Pin installieren: {installhinweis}.")
        if a.pin_pflicht:
            print(f"[check-lint-ratchet] NICHT GELAUFEN — {text}")
            return NICHT_GELAUFEN
        print(f"[check-lint-ratchet] WARNUNG Versionsabweichung — {text}")

    jetzt = ruff_befunde(befehl)
    if jetzt is None:
        print(f"[check-lint-ratchet] NICHT GELAUFEN — ruff {version} ({' '.join(befehl)}) brach ab "
              "oder lieferte kein JSON.")
        return NICHT_GELAUFEN

    basis = lade_baseline()
    # Reihenfolge zaehlt: der Abbruch bei fehlender Baseline steht NACH dem Schreibzweig,
    # sonst koennte `--update-baseline` die Baseline nie anlegen.
    if not basis and not a.update_baseline:
        print("[check-lint-ratchet] keine Baseline — mit --update-baseline anlegen.")
        return 1

    gestiegen, gesunken = vergleich(jetzt, basis)
    print(f"[check-lint-ratchet] ruff {version}: {sum(jetzt.values())} Ruff-Befund(e) in {len(jetzt)} Regel(n); "
          f"eingefroren waren {sum(basis.values())}.")

    if a.update_baseline:
        if basis:
            neu = {r: min(jetzt.get(r, 0), basis.get(r, 0)) for r in set(jetzt) | set(basis)}
        else:
            neu = dict(jetzt)
        neu = {r: n for r, n in sorted(neu.items()) if n}
        BASELINE.write_text(json.dumps(
            {"_": "Ruff-Sperrklinke je Regel. Darf nur sinken — siehe scripts/check_lint_ratchet.py.",
             "gemessen": dt.date.today().isoformat(), "regeln": neu},
            indent=2, ensure_ascii=False) + "\n", "utf-8", newline="\n")
        print(f"  Baseline geschrieben: {sum(neu.values())} Befund(e).")
        return 0

    for z in gesunken:
        print(f"  besser  {z}")
    if gesunken:
        print("  -> mit --update-baseline festschreiben, sonst faellt der Gewinn wieder weg.")

    if gestiegen:
        print(f"\n{len(gestiegen)} Regel(n) mit mehr Befunden als eingefroren:")
        for z in gestiegen:
            print(f"  {z}")
        print("\nJe Regel eingefroren, nicht als Summe. Befund beheben "
              "(`ruff check <datei>` zeigt die Stellen) oder begruenden.")
        return 1

    print("  OK — keine Regel ueber ihrem eingefrorenen Stand.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
