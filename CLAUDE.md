# Claude-Specific Agent Instructions — ALUCA (Analytics Library of Use Cases)

> **Read [`AGENTS.md`](AGENTS.md) first.** It is the universal entry point and primary
> router for all agents (Golden Thread, use-case/framework rules, scripts/CI, TMDL,
> PBIR, OSS, skills). This file adds only Claude-specific rules plus the navigation,
> doctrine, and drift-gate wiring. On conflict: **repo rules here/AGENTS.md > GOI**.

## Globale Doktrin (Pflichtlektüre)

**Vor jeder Aufgabe lesen und befolgen:** [GOI_DOKTRIN.md](GOI_DOKTRIN.md) — die
Global Operating Instructions (Stil, Workflow, Recherche, Sicherheit). Gilt
projektübergreifend; bei Konflikt gewinnen die projektspezifischen Regeln hier.

## Navigations-Prinzip (Token-Disziplin)

Nicht ganze Ordnerbäume scannen — gezielt routen.

- **Primärer Router:** [`AGENTS.md`](AGENTS.md). Es enthält die „was-liegt-wo"-Tabellen
  (Golden Thread, Skills unter `docs/agent/skills/`, Referenzen unter
  `products/fabric/powerbi/docs/references/`). Für die meisten Aufgaben genügt
  AGENTS.md → ein Detail-Dokument.
- **Bereichs-Index:** Jeder navigierbare Bereich hat **genau ein** `_INDEX.md` als
  Pflicht-Erstkontakt, das per „lies-wenn"-Tabelle zum nötigen Doc routet — verteilt
  (ein Index pro Bereich), nicht ein zentraler Mega-Index (begründet in
  [docs/NAVIGATION_PHILOSOPHY.md](docs/NAVIGATION_PHILOSOPHY.md)). **Nicht den ganzen
  Ordner lesen** — dem Index vertrauen, gezielt navigieren.

### Bereichs-Landkarte (zentraler Einstieg → verteilte Indizes)

| Bereich | `_INDEX.md` | Wofür |
|---|---|---|
| Strategie + Operating Model | [`core/strategy_operating_model/_INDEX.md`](core/strategy_operating_model/_INDEX.md) | WHY (Zielbild, Strategic KPIs, Patterns) + HOW (Golden Thread, Semantik, Governance, UX) |
| DSGVO-Compliance | [`compliance/_INDEX.md`](compliance/_INDEX.md) | DPIA, AVV, Retention, EU-Hosting, Art.-30-Record (DE-Markt-Beschaffung) |
| Architektur + ADRs | [`docs/architecture/_INDEX.md`](docs/architecture/_INDEX.md) | Decision Records (ADR-0001–0003), Agent-Integration, Migration, Tooling-Map, Reference-Graph |
| Agent (Regeln + Skills) | [`docs/agent/_INDEX.md`](docs/agent/_INDEX.md) | Wie Agenten arbeiten: Rules, Skills, Guided Workflow (GADW), Aktivierung |
| Repo-Gates + Sensoren | [`scripts/_INDEX.md`](scripts/_INDEX.md) | Drift-Gate, CI-/Spiegel-/Plattform-Sensoren, Tier-0-Sammler `gadw_gate.py` |
| Produkte (Tool-Adapter) | [`products/_INDEX.md`](products/_INDEX.md) | Fabric/Power BI (Leitfäden, TMDL-/PBIR-Referenzen, Tooling, Deployment, Betrieb) + OSS-Stack (Evidence.dev), Adapter-Vertrag, Connectoren |
| Intern (Maintainer) | [`internal/_INDEX.md`](internal/_INDEX.md) | Fehler-Wissensbasis (`KNOWN_ERRORS_AND_FIXES.md`), Desktop-/Fabric-gated Aufgaben, v1.0-Plan, Backlogs, Doku-Audits, Metriken, Continuity-Dossier, Angebotskalkulation — kein Kunden-Deliverable (außer Continuity-Dossier); `internal/archive/` nicht navigiert |

Übrige Bereiche (`core/kpi_catalog/`, `core/action_codes/`, `core/usecases/`, …) navigieren
weiter über ihre `README.md`; ein eigenes `_INDEX.md` bekommen sie bei Bedarf. Neuer Index
= das Drift-Gate erzwingt ab dann Vollständigkeit für dessen Subtree.

## Ledger-Prinzip — `_INDEX.md` ist Single Source of Truth (Anti-Nacharbeit)

Wo ein Ledger geführt wird, ist es SoT für offene/entschiedene Punkte:
- **Vor neuer Analyse/Fragenliste zuerst das `_INDEX.md` lesen** — nichts neu ableiten
  oder erneut fragen, was dort entschieden ist.
- Beantwortete Punkte und Entscheidungen **im selben Arbeitsschritt** im Ledger
  abhaken (mit Datum/Quelle), nicht nur im Fließtext einer Notiz lassen.
- Bekannte Fehlerklassen leben in `internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md`
  (Symptom | Ursache | Fix) — bei Validierungsfehlern zuerst dort nachsehen, neue
  Klassen dort ergänzen.

## Drift-Gate (hält Indizes ehrlich)

`python scripts/check_index.py` prüft: jede `*.md` ist im zuständigen `_INDEX.md`
gelistet (Subtree-Ownership), jeder Pfad/Anker zeigt auf echte Ziele, keine
ungefüllten Doppelklammer-Platzhalter in `CLAUDE.md`/`GOI_DOKTRIN.md`/`_INDEX.md`,
Staleness advisory.
Vor Commit hart: `python scripts/check_index.py --strict` (auch im pre-commit-Hook).
Das ist **zusätzlich** zum fachlichen Quality-Gate (s. u.), nicht dessen Ersatz.

---

## Projekt-spezifische Regeln

### Golden Thread — referenzieren, nicht neu definieren
Use Cases und Reports **referenzieren** governte Definitionen; sie definieren KPI-
Bedeutung, Targets, Lineage oder Action-Logik nie neu. KPI-Definitionen leben in
`core/kpi_catalog/`, Action-Logik in `core/action_codes/`, Schema-Autorität in
`tooling/generator/schemas/`. Nur KPIs referenzieren, die im Katalog existieren;
beim Ändern von Action-Code-Referenzen `orchestration.action_code_ids` in
`UseCase_Bracket.yaml` mitziehen. Business Factsheets sind prosa-only (Lean 2.0) —
alle maschinenlesbare Config gehört in `UseCase_Bracket.yaml`.

### PostToolUse-Hooks (automatisch, nicht umgehbar)
Zwei Hooks (in `.claude/settings.json`) feuern nach jedem Write/Edit:
- **`validate_tmdl_style.sh`** — blockt in `.tmdl` bei Leerzeichen-Einrückung und `:=`.
- **`validate_pbir_structure.sh`** — blockt bei JSON-Syntaxfehlern in `.json`/`.pbir`
  innerhalb von PBIP-Verzeichnissen.

Blockt ein Hook → Verstoß **fixen und neu versuchen**, nie umgehen. Die TMDL-Hardrules
(Tabs, `=` statt `:=`, Beschreibung als `///`-Block über dem Objekt, `summarizeBy`/
`formatString` setzen) stehen in AGENTS.md. `///` **ist** in TMDL die Description-Eigenschaft,
die Copilot liest (erste 200 Zeichen); ein `description:`-Schlüssel ist keine TMDL-Syntax.

### Fab CLI — non-interaktiv schalten
Vor jedem nicht-interaktiven `fab`-Aufruf in einer Claude-Session erst:
```bash
fab config set mode command_line
```
Sonst öffnet `fab` blockierende interaktive Prompts.

### Quality-Gate (muss vor Commit/PR grün sein)
```powershell
.\tooling\quality\run_quality_gate.ps1   # Stage 1 + Fabric-Validierung
```
Mindestens Stage 1 (`.\tooling\run_stage1_checks.ps1`) vor jedem Commit; Python-Suite
`python -m pytest tooling/tests/ products/ -q`. Alle Skripte aus der **Repo-Wurzel**
ausführen. Eine Aufgabe gilt nie als fertig, solange Validierung Fehler zeigt.

### GitHub-Actions-CI — bekannte Usage-Limit-Bedingung (wiederkehrend)

Volltext mit Historie, Belegen und Befehlen:
[docs/agent/ci-usage-limit.md](docs/agent/ci-usage-limit.md). Kurzregeln:

- **Rot ohne Runner ist das Kontingent, nicht der Code.** Jobs enden nach ~2 s mit
  `runner_id: 0`, leerem `runner_name`, Logs 404: Actions-Minuten des privaten Repos
  erschöpft (Reset am Monatsersten). Gemessen wird an `runner_id`, nie an einem Datum.
- **Rot hat mehr als eine Ursache.** Vor dem Abhaken eines roten Laufs
  `python3 scripts/check_workflows.py` laufen lassen: `total_count: 0` Jobs heißt
  ungültige Workflow-Datei, nicht Limit.
- **Im Limit-Fenster:** rote Läufe nicht untersuchen und nicht re-triggern, lokal
  validieren mit `bash tooling/run_local_ci_check.sh`. Über Merge entscheidet der/die
  Maintainer:in.
- **Lokal grün ist nicht CI grün.** Die CI-`pip`-Liste in einem frischen venv mit
  repo-eigenem Pfad (`/tmp/aluca_venv`, nicht Meridians venv) nachstellen und dort den
  CI-Aufruf fahren. Was im Fenster lokal grün war, wird beim ersten echten Runner erneut
  gemessen und nicht als erledigt geführt.
- **Stage 1 läuft auch unter `pwsh` auf Linux.** Vorher `npm ci` in `tooling/validation/`,
  sonst meldet `check_schema_validation.ps1` Erfolg ohne zu prüfen.
- **Auto-Fixer müssen die Hardrules kennen.** `markdownlint --fix` (MD010) hatte Tabs in
  `tmdl`-Codeblöcken ersetzt; MD010 ignoriert `tmdl` deshalb.
- **Entwurfs-PRs lösen keine CI aus** (seit 25.09.2026, #472). Erst `gh pr ready` startet
  die Läufe; das Minutenkontingent teilen sich alle privaten Repos des Kontos.
