---
last-reviewed: 2026-09-25
shelf-life-days: 90
---
# Agent-Skills — Register (_INDEX)

> Navigations-Index der Agent-**Skills** (aufgabenspezifische Prozeduren). Diese
> `*.md` sind die **Skill-Inhalte**; Metadaten (name, version, description) in
> `_index.yaml`, das die Generierung tool-spezifischer `SKILL.md` steuert.
> Generierungs-Mechanismus: `../README.md`.

| Skill (`*.md`) | Zweck |
|---|---|
| `add-usecase-scaffold.md` | Neuen Use Case scaffolden (Factsheet + Bracket, Lean 2.0) |
| `add-kpi-reference-safely.md` | KPI-Referenz nur bei Catalog-Existenz hinzufügen |
| `add-action-code-and-wire-up.md` | Action Codes anlegen + in Use Cases verdrahten |
| `edit-factsheet-safely.md` | Factsheets ohne Stage-1-Bruch editieren |
| `edit-usecase-bracket-safely.md` | `UseCase_Bracket.yaml` (SSOT) sicher editieren |
| `assess-change-impact.md` | Blast-Radius vor Rename/Delete/Deprecate prüfen |
| `generate-and-validate-pbi-report.md` | Iterativer, fehlerfreier PBI-Report-Workflow |
| `recommend-fabric-capacity.md` | Kapazität empfehlen: SKU-Floor, Reserved/PAYG, Region, Zuschnitt |
| `fabric-powerbi-validation.md` | Fabric/PBI-Output validieren (TMDL/DAX/Measures) |
| `run-agentic-loop.md` | Agentische Schleife S0–S7: ein Kommando, Trockenlauf als Standard |
| `fix-pbi-report-errors.md` | PBI-Report-/Modell-Fehler diagnostizieren + fixen |
| `generate-oss-dashboard.md` | Evidence.dev-Pages aus IR/Bracket generieren |
| `oss-stack-validation.md` | OSS-Stack-Artefakte validieren |
| `fix-oss-dashboard-errors.md` | Evidence.dev-/OSS-Fehler fixen |
| `stage1-pre-commit.md` | Stage-1-Checks vor Commit ausführen |
| `fix-stage1-failure.md` | Stage-1-CI-Fehler diagnostizieren + fixen |
| `visual-library.md` | Governed Chart-Wahl (Purpose→Idiom, Notation, Min-Größe) + Audit bestehender Visuals gegen die Deny-Liste |

<!-- check_index.py erzwingt: jede *.md in skills/ ist hier gelistet. _index.yaml = Metadaten (kein .md → nicht gate-pflichtig). -->
