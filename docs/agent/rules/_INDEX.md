---
last-reviewed: 2026-09-25
shelf-life-days: 90
---
# Agent-Rules — Register (_INDEX)

> Navigations-Index der Agent-**Rules** (Verhaltens-/Zuständigkeitsregeln). Diese
> `*.md` sind die **Regel-Inhalte**; die Metadaten (description, globs, alwaysApply)
> liegen in `_index.yaml` und steuern die Generierung tool-spezifischer Configs
> (z. B. `.cursor/rules/*`). Inhalt = diese Dateien, Metadaten = `_index.yaml`.
> Generierungs-Mechanismus: `../README.md`.

## 1. „Lies-wenn"-Routing

| Deine Aufgabe ist … | Lies | NICHT nötig |
|---|---|---|
| Issue/PR-Aufgabe ausführen (immer) | `agent-workflow.md`, `framework-conventions.md`, `stage1-awareness.md` | Rollen-Rules |
| `.tmdl` oder DAX schreiben | `tmdl-dax.md`, `fabric-expert.md` | `oss-stack-expert.md` |
| Factsheet oder `UseCase_Bracket.yaml` ändern | `artifacts-factsheets.md` | `tmdl-dax.md` |
| Action Code, Data Contract, KPI-YAML ändern | `artifacts-yaml.md`, `framework-expert.md` | `tmdl-dax.md` |
| Kernstruktur, Connector-Contract, Hub-Strategie | `framework-architect.md` | `artifacts-factsheets.md` |
| Evidence.dev / DuckDB / dbt | `oss-stack-expert.md` | `fabric-expert.md` |
| PR oder Change reviewen | `reviewer-agent.md` | `pm-agent.md` |
| Aufgabe einer Rolle/einem Skill zuordnen | `router-agent.md` | Fach-Rules |
| Backlog, Priorisierung, Intake | `pm-agent.md` | Fach-Rules |
| Briefing, Plan, Entscheidungs-Summary | `assistant-agent.md` | Fach-Rules |

## 2. Register

| Rule (`*.md`) | alwaysApply | Zweck |
|---|---|---|
| `agent-workflow.md` | ja | Ausführungs-Workflow für zugewiesene Issues/PRs |
| `framework-conventions.md` | ja | Golden-Thread-/SSOT-Konventionen bei `core/`-Edits |
| `stage1-awareness.md` | ja | Stage-1-Gate-Bewusstsein (Edits Stage-1-grün halten) |
| `artifacts-factsheets.md` | nein | Business Factsheets / `UseCase_Bracket.yaml` governen |
| `artifacts-yaml.md` | nein | YAML-Artefakte (Action Codes, Data Contracts, KPI-YAML) |
| `framework-expert.md` | nein | `core/`, `tooling/ir`, `data_contracts`, Validation (tool-agnostisch) |
| `framework-architect.md` | nein | Kernstruktur, Connector-Contracts, Hub-Strategie |
| `fabric-expert.md` | nein | TMDL/DAX/PBIP/Fabric-Artefakte + Checks |
| `oss-stack-expert.md` | nein | Evidence.dev / DuckDB / dbt / OSS-Pages |
| `tmdl-dax.md` | nein | TMDL/DAX-Hard-Rules (Tabs, kein `:=`, Beschreibung als `///`-Block) |
| `reviewer-agent.md` | nein | PR-/Change-Review gegen Rules/Skills/Stage-1 |
| `router-agent.md` | nein | Aufgaben an passende Rolle/Skill routen |
| `pm-agent.md` | nein | Backlog/Priorisierung/Intake |
| `assistant-agent.md` | nein | Briefings, Pläne, Entscheidungs-Summaries |

<!-- check_index.py erzwingt: jede *.md in rules/ ist hier gelistet. _index.yaml = Metadaten (kein .md → nicht gate-pflichtig). alwaysApply-Spalte = Spiegel von _index.yaml. -->
