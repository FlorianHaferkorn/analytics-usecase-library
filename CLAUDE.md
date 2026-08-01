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

### GitHub-Actions-CI — bekannte Usage-Limit-Bedingung (wiederkehrend)
Das Actions-Usage-Limit ist wiederholt erschöpft — repo-weit, **auf `main` und
allen Branches gleichermaßen**. Symptom: Jobs enden nach ~2 s mit
`conclusion=failure`, **ohne Runner** (`runner_id: 0`, leerer `runner_name`),
Logs liefern HTTP 404. Das ist **keine** Code-Ursache und durch keinen Diff zu
beheben.

Historie:
- Erste Ausprägung: bis 1. Juli 2026 — hat sich am 1. Juli von selbst gelöst
  (verifiziert durch durchgehend grüne CI-Läufe mit echten `runner_id`s bis
  einschließlich PR #386).
- Zweite Ausprägung (aktuell): erneut erschöpft. **Der Mechanismus ist belegt, nicht
  vermutet** (github/docs, `billing/concepts/product-billing/github-actions.md`,
  geprüft 31.07.2026): das Repo ist **privat**, damit sind Actions-Minuten
  kontingentiert — *„If your account does not have a valid payment method on file,
  usage is blocked once you use up your quota."* Und: *„At the start of each month,
  the minutes used by the account are reset to zero."*

  Daraus folgt datiert statt geraten: das Kontingent setzt am **1. August 2026**
  zurück. Wer nicht warten will, hat genau einen Hebel — eine gültige
  Zahlungsmethode bzw. ein Spending-Limit im GitHub-Billing. Beides liegt beim
  Kontoinhaber; im Code gibt es nichts zu beheben.

**Aber: „rot" hat mehr als eine Ursache, und sie sehen von aussen gleich aus.** Am
31.07.2026 war `.github/workflows/source-updates.yml` **kein gültiges YAML** (ein
`python -c "…"` im `run: |`-Block auf Spaltenposition 0 beendete den Blockskalar). Alle 30
Läufe seit dem 29.07. waren rot — und gingen im Limit-Fenster unter, weil jeder rote Lauf
als erklärt galt. Der Unterschied ist messbar und in Sekunden zu prüfen:

| Ursache | Jobs des Laufs | Erkennung |
|---|---|---|
| Usage-Limit | vorhanden, `runner_id: 0`, ~2 s | `list_workflow_jobs` → Jobs da, kein Runner |
| Ungültige Workflow-Datei | **`total_count: 0`** | `python3 scripts/check_workflows.py` (lokal) |

Deshalb: **vor** dem Abhaken eines roten Laufs einmal `python3 scripts/check_workflows.py`
laufen lassen (steckt in `tooling/run_local_ci_check.sh` als erster Schritt). Ein Fenster,
in dem alles erklärt ist, ist das beste Versteck für einen echten Defekt.

**Und: „lokal grün" ist nicht dasselbe wie „CI grün".** Am 01.08.2026, im ersten Lauf mit
echten Runnern nach dem Reset, waren drei Tests rot, die lokal alle grün liefen. Drei
verschiedene Gründe, jeder eine eigene Fehlerklasse:

| Symptom | Ursache |
|---|---|
| `ModuleNotFoundError: pyarrow` | die CI-`pip install`-Liste kannte die Abhängigkeit nicht — das Gate **konnte** dort nie grün werden |
| `reference_graph.md is stale` (110 vs 109) | der Generator schlüsselte Measures nach **Dateinamen**; 31 Namen kollidieren über Domänen, wer gewinnt entschied die Dateisystem-Reihenfolge. 28 Measures fielen still heraus |
| `PBIR_PLATFORM_MISSING` | die CI installiert die PBIR-CLI **ungepinnt** und bekam 0.1.4 statt des Repo-Pins 0.1.1 — die neuere Fassung prüft `.platform`, unser Emitter schrieb keine |

Die gemeinsame Lehre: ein Test ist nur so aussagekräftig wie die Gleichheit der beiden
Umgebungen. Wo die CI weniger installiert, prüft sie etwas anderes; wo sie ungepinnt
installiert, prüft sie etwas Unvorhersehbares; und wo ein Generator vom Dateisystem abhängt,
prüft er ein Münzwurfergebnis. Alle drei sind behoben — die Klasse bleibt.

Daher — für die Dauer jedes solchen Fensters: diese roten CI-Läufe **nicht
untersuchen und nicht re-triggern**; stattdessen **lokal** validieren. Für die
konsolidierte lokale Prüfung: `bash tooling/run_local_ci_check.sh` (führt
Drift-Gate, Python-Testsuite, Fabric-Bindings-Validator, PBI-Quality-Tools,
Health-Scorecard sowie die Studio-Checks — tsc/vitest/Playwright — in einem
Durchlauf aus und meldet alle Ergebnisse statt beim ersten Fehler
abzubrechen). Bekannte Lücke: die Windows-only Stage-1-/Fabric-Quality-Gate-
PowerShell-Skripte (`run_stage1_checks.ps1`, `run_quality_gate.ps1`) laufen
darin **nicht** — dafür ist während des Fensters entweder eine
Windows-Umgebung nötig oder manuelle Prüfung durch den/die Maintainer:in vor
dem Merge. Über das weitere Vorgehen (z. B. Merge) entscheidet der/die
Maintainer:in.
