# Claude-Specific Agent Instructions — ALUCA (Analytics Library of Use Cases)

> **Read [`AGENTS.md`](AGENTS.md) first.** It is the universal entry point and primary
> router for all agents (Golden Thread, use-case/framework rules, scripts/CI, TMDL,
> PBIR, OSS, skills). This file adds only Claude-specific rules plus the navigation,
> doctrine, and drift-gate wiring. On conflict: **repo rules here/AGENTS.md > GOI**.

## Globale Doktrin (Pflichtlektüre)

**Vor jeder Aufgabe lesen und befolgen:** [GOI_DOKTRIN.md](GOI_DOKTRIN.md) — die
Global Operating Instructions (Stil, Workflow, Recherche, Sicherheit). Gilt
projektübergreifend; bei Konflikt gewinnen die projektspezifischen Regeln hier.

## Navigations-Prinzip (Token-Disziplin — KRITISCH)

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
- **`validate_tmdl_style.sh`** — blockt bei Tab-/`:=`-/`description:`-Verstößen in `.tmdl`.
- **`validate_pbir_structure.sh`** — blockt bei JSON-Syntaxfehlern in `.json`/`.pbir`
  innerhalb von PBIP-Verzeichnissen.

Blockt ein Hook → Verstoß **fixen und neu versuchen**, nie umgehen. Die TMDL-Hardrules
(Tabs, `=` statt `:=`, `/// Purpose:`-Kommentar statt `description:`, `summarizeBy`/
`formatString` setzen) stehen in AGENTS.md und werden so erzwungen.

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

### GitHub-Actions-CI — bekannte Usage-Limit-Bedingung (bereits zweimal aufgetreten)
Das Actions-Usage-Limit wurde erneut erreicht — diesmal bis **Anfang August**
(Stand 2026-07-09; war zuvor schon bis 1. Juli erschöpft, hat sich also **nicht**
dauerhaft von selbst gelöst, sondern tritt wiederkehrend auf). Wirkung:
GitHub-Actions-CI schlägt repo-weit fehl — **auf `main` und allen Branches
gleichermaßen**. Symptom: Jobs enden nach ~2 s mit `conclusion=failure`, **ohne
Runner** (`runner_id: 0`, leerer `runner_name`), Logs liefern HTTP 404. Das ist
**keine** Code-Ursache und durch keinen Diff zu beheben. Daher: diese roten
CI-Läufe **nicht untersuchen und nicht re-triggern**. Über das weitere Vorgehen
(z. B. Merge trotz rotem/fehlendem CI-Lauf) entscheidet der/die Maintainer:in.

**Bis die Minutes zurück sind: lokal so nah wie möglich an CI validieren.**
`pwsh` (PowerShell 7) lässt sich auch in Linux-Sandboxes installieren — der
Proxy blockt zwar `github.com`-Release-Downloads und die PowerShell-Gallery,
aber Microsofts eigenes APT-Repo (`packages.microsoft.com`) ist erreichbar:
```bash
curl -sSL -o /tmp/pwsh.deb https://packages.microsoft.com/config/ubuntu/22.04/packages-microsoft-prod.deb
dpkg -i /tmp/pwsh.deb && apt-get update && apt-get install -y powershell
```
Damit läuft der **reale CI-Befehl** lokal komplett durch:
```bash
pwsh tooling/quality/run_quality_gate.ps1        # = Stage 1 + Fabric-Gate, wie in .github/workflows/stage1.yml
python -m pytest tooling/tests/ products/ -q     # = python-checks-Job
python3 scripts/check_index.py --strict          # Drift-Gate
```
Bekannte, unvermeidbare Lücken (klar als „SKIP"/graceful-skip erkennbar, nie als
stiller Pass): `check_validate_data_contracts.ps1` (braucht `powershell-yaml`,
nur via PSGallery installierbar, dort geblockt) und `pbir-cli` selbst
(Windows-only Closed-Source-Binary, s. `r3-1-tooling-audit-and-theme-decision.md`).
Alles andere — TMDL/PBIR/DAX/Theme/fab-inspector-BPA/Markdownlint/Governance —
läuft und gated wie in echtem CI.

**Dieser erste echte Nicht-Windows-Lauf hat 2026-07-09 drei bis dahin unsichtbare,
systemische Windows-only-Bugs aufgedeckt und gefixt** (nur auf `windows-latest`
lauffähig getestet, nie auf Linux/macOS): (1) Python-Erkennungsschleife in 3
Skripten warf `Python 3 not found` trotz vorhandenem `python3` (PowerShell-
Range-Operator-Bug bei Einzelwort-Kommandos); (2) **21 Dateien** benutzten
`-notmatch '\word\'`-Excludes (z. B. `internal\archive\`, `decision_spines\`),
die auf Linux/macOS (Forward-Slash-Pfade) **nie** matchen — dadurch wurden
archivierte/ausgeschlossene Dateien fälschlich mitvalidiert (u. a. 17
Falsch-Positive in `check_schema_validation.ps1`); (3) `check_markdownlint.ps1`
hartkodierte den Windows-`.cmd`-Launcher. Alle drei Details + Fix:
`internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md` (Abschnitt „Scripts /
Generator"). **Lehre:** diese Bugs waren so lange unsichtbar, weil CI
ausschließlich auf `windows-latest` lief — ein lokaler Nicht-Windows-Lauf ist
also nicht nur ein CI-Ersatz während der Usage-Limit-Ausfälle, sondern deckt
eine ganze Klasse von Bugs auf, die reines Windows-CI strukturell nie findet.
Bei künftigen neuen `check_*.ps1`-Skripten: Path-Excludes immer `[\\/]` statt
`\` schreiben, Python-Erkennung nicht neu erfinden (bestehendes, jetzt
korrigiertes Muster kopieren).
