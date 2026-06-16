---
last-reviewed: 2026-06-16
shelf-life-days: 90
---
# Agent-Rules — Register (_INDEX)

> Navigations-Index der Agent-**Rules** (Verhaltens-/Zuständigkeitsregeln). Diese
> `*.md` sind die **Regel-Inhalte**; die Metadaten (description, globs, alwaysApply)
> liegen in `_index.yaml` und steuern die Generierung tool-spezifischer Configs
> (z. B. `.cursor/rules/*`). Inhalt = diese Dateien, Metadaten = `_index.yaml`.
> Generierungs-Mechanismus: `../README.md`.

| Rule (`*.md`) | Zweck | alwaysApply |
|---|---|---|
| `agent-workflow.md` | Ausführungs-Workflow für zugewiesene Issues/PRs | ja |
| `framework-conventions.md` | Golden-Thread-/SSOT-Konventionen bei `core/`-Edits | ja |
| `artifacts-factsheets.md` | Business Factsheets / `UseCase_Bracket.yaml` governen | nein |
| `artifacts-yaml.md` | YAML-Artefakte (Action Codes, Data Contracts, KPI-YAML) | nein |
| `framework-expert.md` | `core/`, `tooling/ir`, `data_contracts`, Validation (tool-agnostisch) | nein |
| `framework-architect.md` | Kernstruktur, Connector-Contracts, Hub-Strategie | nein |
| `fabric-expert.md` | TMDL/DAX/PBIP/Fabric-Artefakte + Checks | nein |
| `oss-stack-expert.md` | Evidence.dev / DuckDB / dbt / OSS-Pages | nein |
| `tmdl-dax.md` | TMDL/DAX-Hard-Rules (keine Tabs, kein `:=`, kein `description:`) | nein |
| `stage1-awareness.md` | Stage-1-Gate-Bewusstsein (Edits Stage-1-grün halten) | nein |
| `reviewer-agent.md` | PR-/Change-Review gegen Rules/Skills/Stage-1 | nein |
| `router-agent.md` | Aufgaben an passende Rolle/Skill routen | nein |
| `pm-agent.md` | Backlog/Priorisierung/Intake | nein |
| `assistant-agent.md` | Briefings, Pläne, Entscheidungs-Summaries | nein |

<!-- check_index.py erzwingt: jede *.md in rules/ ist hier gelistet. _index.yaml = Metadaten (kein .md → nicht gate-pflichtig). -->
