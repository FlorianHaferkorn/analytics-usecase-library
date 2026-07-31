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

Prüft je Datei: parst als YAML · hat `jobs` · jeder Job hat `runs-on` und `steps`.
Exit 1 bei jedem Befund. Kein Netz, keine Abhängigkeit ausser PyYAML.
"""
from __future__ import annotations

import pathlib
import sys

import yaml

WORKFLOW_DIR = pathlib.Path(".github/workflows")


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
    befunde = findings(root)
    n = len(list((root / WORKFLOW_DIR).glob("*.y*ml"))) if (root / WORKFLOW_DIR).is_dir() else 0
    if befunde:
        print(f"[check-workflows] {len(befunde)} Befund(e) in {n} Workflow-Datei(en):")
        for b in befunde:
            print(f"  ✗ {b}")
        return 1
    print(f"[check-workflows] OK — {n} Workflow-Datei(en) parsen und deklarieren Jobs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
