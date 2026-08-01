#!/usr/bin/env python3
"""check_workflows — jede Workflow-Datei muss gültiges YAML sein und Jobs deklarieren.

Der Anlass ist gemessen, nicht theoretisch. Am 31.07.2026 war
`.github/workflows/source-updates.yml` **kein gültiges YAML**: ein `python -c "…"` im
`run: |`-Block stand auf Spaltenposition 0 und beendete damit den Blockskalar. Alle 30 Läufe
seit dem 29.07. schlugen fehl — und die Ursache war von aussen nicht von der gleichzeitig
laufenden Actions-Usage-Limit-Bedingung zu unterscheiden: beide melden `conclusion=failure`.

Unterscheiden lassen sie sich nur an einer Stelle, und die ist der Grund für dieses Skript:

    Usage-Limit          -> Jobs werden angelegt, aber ohne Runner (`runner_id: 0`, ~2 s).
    Ungültiges YAML      -> es entstehen ÜBERHAUPT KEINE Jobs (`total_count: 0`).

Solange das Limit-Fenster offen ist, ist jeder rote Lauf „erklärt" — und ein echter Defekt
versteckt sich dahinter. Dieser Prüfer nimmt die Frage von der CI weg: er beantwortet lokal
und in Sekunden, ob eine Workflow-Datei überhaupt laufen KANN.

Zwei Stufen, Official-First:

  1. **`actionlint`**, wenn im PATH — der etablierte Actions-Linter (rhysd/actionlint). Er
     kennt die Actions-Grammatik, nicht nur YAML, und ist damit die genauere Aussage. Am
     31.07.2026 an beiden Ständen geprüft: alte Datei ``:57:0: could not parse as YAML``,
     reparierte Datei sauber — derselbe Befund wie PyYAML, mit Zeilennummer.
  2. **Eigenprüfung** sonst (PyYAML + Struktur): parst als YAML · hat ``jobs`` · jeder Job
     hat ``runs-on`` und ``steps``. Kein Soft-Skip — die Frage ist zu wichtig, um sie
     unbeantwortet zu lassen, nur weil ein Werkzeug fehlt.

Exit 1 bei jedem Befund. Kein Netz nötig; ohne actionlint ausser PyYAML keine Abhängigkeit.
"""
from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys

import yaml

WORKFLOW_DIR = pathlib.Path(".github/workflows")


def _actionlint(root: pathlib.Path) -> list[str] | None:
    """Befunde von ``actionlint``, oder ``None`` wenn es nicht installiert ist.

    ``-shellcheck=`` / ``-pyflakes=`` schalten die beiden optionalen Unterprüfer ab: sie
    melden Stilfragen in eingebetteten Skripten und würden diesen Wächter von seiner Frage
    ablenken — kann dieser Workflow überhaupt laufen?
    """
    exe = shutil.which("actionlint")
    if not exe:
        return None
    r = subprocess.run([exe, "-shellcheck=", "-pyflakes=", "-oneline"],
                       cwd=root, capture_output=True, text=True)
    # rc 0 = sauber, rc 1 = Befunde. Alles andere heisst: das Werkzeug hat NICHT geprüft
    # (z. B. rc 3 „no project was found" ausserhalb eines Git-Repos). Dann ``None``
    # zurückgeben statt einer leeren Befundliste — sonst meldet der Aufrufer „[actionlint]"
    # für eine Prüfung, die gar nicht stattgefunden hat. Genau diese stille Verwechslung von
    # „nichts gefunden" mit „nicht geschaut" ist der Fehler, gegen den dieses Skript existiert.
    if r.returncode not in (0, 1):
        grund = (r.stderr or r.stdout).strip().splitlines()
        print(f"[check-workflows] actionlint nicht nutzbar (rc={r.returncode}"
              + (f": {grund[0]}" if grund else "") + ") — Eigenprüfung übernimmt.")
        return None
    return [l for l in r.stdout.splitlines() if l.strip()]


def findings(root: pathlib.Path) -> list[str]:
    """Alle Befunde über die Workflow-Dateien unter ``root``; leere Liste = in Ordnung."""
    out: list[str] = []
    wf_dir = root / WORKFLOW_DIR
    if not wf_dir.is_dir():
        return out
    for wf in sorted(list(wf_dir.glob("*.yml")) + list(wf_dir.glob("*.yaml"))):
        rel = wf.relative_to(root)
        try:
            doc = yaml.safe_load(wf.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            erste = str(exc).splitlines()[0]
            out.append(f"{rel}: kein gültiges YAML — {erste}. GitHub legt dafür NULL Jobs an; "
                       f"der Lauf ist rot und sieht aus wie jeder andere rote Lauf.")
            continue
        if not isinstance(doc, dict):
            out.append(f"{rel}: die Datei ist kein YAML-Mapping")
            continue
        jobs = doc.get("jobs")
        if not isinstance(jobs, dict) or not jobs:
            out.append(f"{rel}: kein einziger Job deklariert — der Workflow kann nichts tun")
            continue
        for jid, job in jobs.items():
            if not isinstance(job, dict):
                out.append(f"{rel}: Job '{jid}' ist kein Mapping")
                continue
            if "uses" in job:          # reusable workflow: runs-on/steps liegen dort
                continue
            if not job.get("runs-on"):
                out.append(f"{rel}: Job '{jid}' hat kein runs-on")
            if not job.get("steps"):
                out.append(f"{rel}: Job '{jid}' hat keine steps")
    return out


def main(argv: list[str]) -> int:
    root = pathlib.Path(argv[0]) if argv else pathlib.Path(".")
    n = len(list((root / WORKFLOW_DIR).glob("*.y*ml"))) if (root / WORKFLOW_DIR).is_dir() else 0

    al = _actionlint(root)
    quelle = "actionlint" if al is not None else "Eigenprüfung (actionlint nicht installiert)"
    # Die Eigenprüfung läuft IMMER mit: actionlint prüft die Grammatik, sie prüft zusätzlich,
    # dass überhaupt ein Job deklariert ist — ein Workflow ohne Jobs ist grammatisch korrekt
    # und trotzdem wirkungslos.
    befunde = (al or []) + findings(root)

    if befunde:
        print(f"[check-workflows] {len(befunde)} Befund(e) in {n} Workflow-Datei(en) [{quelle}]:")
        for b in befunde:
            print(f"  ✗ {b}")
        return 1
    print(f"[check-workflows] OK — {n} Workflow-Datei(en) parsen und deklarieren Jobs [{quelle}].")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
