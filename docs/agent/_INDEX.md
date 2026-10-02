---
last-reviewed: 2026-10-01
shelf-life-days: 90
---
# Agent — Zentraler Anlaufpunkt (_INDEX)

> **Einstieg in die Agent-Ebene** (wie Agenten in diesem Repo arbeiten). Zuerst
> diese Datei, dann gezielt weiter. `rules/` und `skills/` sind Sub-Bereiche mit
> eigenem Index. Der Generierungs-Mechanismus (kanonische `.md` + `_index.yaml`
> → tool-spezifische Configs) ist in `README.md` beschrieben.

| Feld | Wert |
|---|---|
| Stand | 2026-09-30 |
| Rolle | L0-Navigation der Agent-Ebene |
| Verlinkt von | `CLAUDE.md` (Bereichs-Landkarte) |

## 1. „Lies-wenn"-Routing

| Deine Aufgabe ist … | Lies | NICHT nötig |
|---|---|---|
| Verhaltens-/Zuständigkeitsregel finden | `rules/_INDEX.md` → passende Rule | skills/ |
| Konkrete Prozedur ausführen (Use Case, KPI, Report, Fix) | `skills/_INDEX.md` → passender Skill | rules/ |
| Offizielle Agent-Skills/Tools integrieren | `guided-agent-development-workflow.md` → `../architecture/adr/0002-official-first-agent-integration-and-guided-workflow.md` | rules/, skills/ |
| Skills for Fabric / Notebook Toolkit nutzen, Pin anheben, VFS-Modus | `agent-developer-tools.md` | rules/, skills/ |
| Aktivierung/Onboarding sicher aufsetzen | `capability-manifest.md` → `studio-activation-ux.md` | rules/, skills/ |

## 2. Dokument-Register (direkte `*.md` dieser Ebene)

| Doc | Zweck | Lies-wenn |
|---|---|---|
| `guided-agent-development-workflow.md` | GADW: stage-gated Loop (offizielle Skills + ALUCA-Gates) | Agent-Integration |
| `capability-manifest.md` | `aluca.capabilities.yaml`-Spec (Allowlist, default-off extern) | Aktivierung |
| `studio-activation-ux.md` | Studio als Aktivierungs-Control-Panel (Toggles → Manifest) | Aktivierungs-UX |
| `agent-developer-tools.md` | Agent-Entwicklerwerkzeuge (Meridian D-603): Skills for Fabric gepinnt, Notebook Toolkit nur intern (Guard), VFS-Regel | Plugin-/Pin-Fragen, Dev-Notebook-Schleife |
| `ci-usage-limit.md` | GitHub-Actions-CI: Usage-Limit, rote Läufe unterscheiden, Umgebungsgleichheit (aus `CLAUDE.md` ausgelagert) | CI rot / lokale CI-Nachstellung |

Sub-Bereiche mit eigenem Index: `rules/_INDEX.md`, `skills/_INDEX.md`.
<!-- README.md exempt; rules/ + skills/ navigieren über eigenen _INDEX. -->

## 3. Offene Punkte (Ledger)

| ID | Punkt | Status | Datum |
|---|---|---|---|
| AG-1 | GADW Stage 0 an GOI-/NAVIGATION-Einstieg angleichen | **erledigt** | 2026-06-16 |
| AG-2 | Build-vs-buy: `ruler` statt eigenem Generator (= ADR-0002 A-2) | **erledigt — shim-only** | 2026-06-16 |
| AG-3 | Skills for Fabric gepinnt (v0.3.18) + Notebook-Toolkit-Grenze (Meridian D-603) | **erledigt** | 2026-09-30 |
