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

  **Nachtrag 03.08.2026 — der Reset ist eine Atempause, keine Lösung.** Er kam wie
  vorhergesagt, und am 03.08. liefen um **14:14/14:15 UTC** echte Läufe (201 s bzw.
  257 s, reale Runner, reale Assertions — die 13 Testfehler daraus sind echt). Ab
  **14:25 UTC desselben Tages** trägt jeder Job wieder `runner_id: 0`. Das
  Monatskontingent war binnen eines halben Tages aufgebraucht. Die Vorhersage „am
  1. August wird es grün" war für einen halben Tag richtig — als Planungsgrundlage
  taugt sie nicht.

  Der eigentliche Ertrag dieses Tages ist deshalb die **Unterscheidung**, nicht die
  Ursache: an einem Vormittag gab es beide Sorten Rot auf demselben Branch. Genau
  dafür steht die Tabelle unten — sie ist keine Formalie, sondern der einzige
  Unterschied zwischen „erklärt" und „verstanden".

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

Der Folgelauf zeigte zwei weitere — und beide waren **Wiederholungen derselben zwei Klassen**,
nur eine Schicht tiefer:

| Symptom | Ursache |
|---|---|
| `ModuleNotFoundError: pandas` | dieselbe Lücke wie bei `pyarrow`, dahinter versteckt: erst als pyarrow da war, kam der Import überhaupt bis zur nächsten Zeile |
| `use_case_storylines.md is stale` | dieselbe Klasse wie `reference_graph`: `_action_related()` las `*_business_case.yaml` als Action-Code. Beide tragen dieselbe `id`, nur einer hat `use_case_links` — wer gewinnt, entschied `rglob`. 22 Action-Codes betroffen, ihre `Connects to`-Kanten wurden still gelöscht |

Die gemeinsame Lehre: ein Test ist nur so aussagekräftig wie die Gleichheit der beiden
Umgebungen. Wo die CI weniger installiert, prüft sie etwas anderes; wo sie ungepinnt
installiert, prüft sie etwas Unvorhersehbares; und wo ein Generator vom Dateisystem abhängt,
prüft er ein Münzwurfergebnis. Alle fünf sind behoben — die Klasse bleibt. Und: eine gefundene
Ausprägung ist kein Beweis, dass die Klasse erledigt ist — beide kamen im nächsten Lauf wieder.

Gegen die Umgebungs-Ungleichheit hilft nur Gleichheit, nicht Sorgfalt. Deshalb wird die
CI-`pip`-Liste **in einem frischen venv** nachgestellt und die CI-Kommandozeile darin gefahren,
statt sich auf die lokal ohnehin installierten Pakete zu verlassen:

```bash
python3 -m venv /tmp/civenv
/tmp/civenv/bin/pip install pyyaml jsonschema pytest typer rich referencing python-docx pyarrow pandas
/tmp/civenv/bin/python -m pytest --tb=short -q      # exakt der CI-Aufruf
```

Daher — für die Dauer jedes solchen Fensters: diese roten CI-Läufe **nicht
untersuchen und nicht re-triggern**; stattdessen **lokal** validieren. Für die
konsolidierte lokale Prüfung: `bash tooling/run_local_ci_check.sh` (führt
Drift-Gate, Python-Testsuite, Fabric-Bindings-Validator, PBI-Quality-Tools,
Health-Scorecard sowie die Studio-Checks — tsc/vitest/Playwright — in einem
Durchlauf aus und meldet alle Ergebnisse statt beim ersten Fehler
abzubrechen). Über das weitere Vorgehen (z. B. Merge) entscheidet der/die Maintainer:in.

**Die Stage-1-PowerShell-Suite ist nicht Windows-gebunden — das war eine Annahme, kein Befund.**
Am 01.08.2026 gemessen: `pwsh` 7.4.6 unter Linux fährt `tooling/run_stage1_checks.ps1` komplett
durch (20 Checks, rc=0), Pfade inklusive. Damit ist der zuvor hier dokumentierte „Windows-only"-
Blindfleck geschlossen:

```bash
pwsh -NoProfile -File tooling/run_stage1_checks.ps1     # setzt pwsh im PATH voraus
```

Zwei Randbedingungen, gemessen statt vermutet:
- `check_schema_validation.ps1` ist ein **Node**-Validator und macht ohne Deps einen
  Soft-Skip mit rc=0 — also einmal `npm ci` in `tooling/validation/`, sonst prüft er nichts
  und meldet trotzdem Erfolg.
- `check_validate_data_contracts.ps1` wird ohne das Modul `powershell-yaml` **übersprungen**
  (das Skript sagt das selbst: „SKIPPED, not passed"). Ist die PowerShell Gallery nicht
  erreichbar, deckt sein Python-Delegat dieselbe Logik ab:
  `python3 tooling/validation/check_validate_data_contracts.py --root .`

Dabei fiel eine dritte Sache auf, und die ist keine Randbedingung, sondern ein Regelkonflikt:
`check_markdownlint.ps1` fährt `markdownlint-cli2 --fix`, und MD010 („no hard tabs") ersetzt
Tabs **auch in Code-Blöcken** — ein Tab pro Leerzeichen. Genau in den ```tmdl-Blöcken, deren
Hardrule Tabs *verlangt*. Der Check hat damit still die Doku umgeschrieben, die er schützen
sollte: `tmdl_best_practices.md` und `pbir-rename-cascade.md` lehrten bereits Leerzeichen,
`AI_Description_Standard.md` wurde beim ersten Lauf mit installierten npm-Deps erwischt. Der
Konflikt ist an der Wurzel gelöst — `MD010: { "ignore_code_languages": ["tmdl"] }` in beiden
markdownlint-Konfigurationen, MD010 bleibt also für Fließtext scharf — und die Tabs sind in
allen drei Dokumenten wiederhergestellt. Lehre für neue Auto-Fixer: ein Formatierer, der
schreiben darf, muss die Hardrules kennen, sonst gewinnt der Formatierer.
