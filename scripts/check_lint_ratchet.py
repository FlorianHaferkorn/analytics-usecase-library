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

Lauf: ``python3 scripts/check_lint_ratchet.py`` · ``--strict`` macht Anstieg zu Exit 1.
``--update-baseline`` schreibt den erreichten Stand fest (hebt die Latte nie an).
Ohne Ruff: SKIP mit Exit 0, aber laut — ein Tor ohne Werkzeug meldet nicht „sauber".
Die Zahlen haengen an der Ruff-Version; die CI pinnt sie (``.github/workflows/stage1.yml``).
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import pathlib
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
BASELINE = pathlib.Path(__file__).resolve().parent / "lint_baseline.json"


def ruff_befunde() -> collections.Counter | None:
    """``{regel: anzahl}`` — oder ``None``, wenn Ruff fehlt oder nicht lief."""
    try:
        p = subprocess.run([sys.executable, "-m", "ruff", "check", ".", "--output-format=json",
                            "--no-cache", "--exit-zero"],
                           cwd=REPO_ROOT, capture_output=True, text=True, timeout=300,
                           encoding="utf-8", errors="replace")
    except (FileNotFoundError, subprocess.TimeoutExpired):
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
    ap.add_argument("--strict", action="store_true", help="Anstieg ist Exit 1")
    ap.add_argument("--update-baseline", action="store_true",
                    help="erreichten Stand festschreiben (hebt die Latte nie an)")
    a = ap.parse_args(argv)

    jetzt = ruff_befunde()
    if jetzt is None:
        print("[check-lint-ratchet] SKIP (nicht gelaufen) — ruff fehlt oder brach ab "
              "(`pip install ruff`).")
        return 0

    basis = lade_baseline()
    # Reihenfolge zaehlt: der Abbruch bei fehlender Baseline steht NACH dem Schreibzweig,
    # sonst koennte `--update-baseline` die Baseline nie anlegen.
    if not basis and not a.update_baseline:
        print("[check-lint-ratchet] keine Baseline — mit --update-baseline anlegen.")
        return 1 if a.strict else 0

    gestiegen, gesunken = vergleich(jetzt, basis)
    print(f"[check-lint-ratchet] {sum(jetzt.values())} Ruff-Befund(e) in {len(jetzt)} Regel(n); "
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
              "(`python -m ruff check <datei>` zeigt die Stellen) oder begruenden.")
        return 1 if a.strict else 0

    print("  OK — keine Regel ueber ihrem eingefrorenen Stand.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
