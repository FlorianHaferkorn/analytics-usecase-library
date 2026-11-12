---
last-reviewed: 2026-11-12
shelf-life-days: 90
---
# tooling — Generatoren, Prüfungen, Emission (_INDEX)

> `tooling/` erzeugt und prüft, was `core/` definiert. Es ist intern und wird nie an Kunden
> ausgeliefert. Der Ordner hat fünf Familien mit je eigenem Zweck (Abschnitt 1); wer ein neues
> Werkzeug baut, legt es in die passende Familie und erweitert dort, statt eine sechste
> aufzumachen. Zuerst diese Datei, dann gezielt die README bzw. das Modul.

| Feld | Wert |
|---|---|
| Stand | 2026-11-12 |
| Rolle | L0-Navigation für `tooling/`; Register aller `.md` außer `README.md` |
| Eigener Index | `superversion/_INDEX.md` regiert seinen Teilbaum selbst |
| Veraltet | `README.md` beschreibt in Teilen einen alten Stand (nennt `ai/`, `alignment/`, `generation/`, `maintenance/` und `validation/schemas/`, die es nicht gibt). Maßgeblich für die Ordnerstruktur ist dieser Index |
| Spiegel | `visual_library/` (u. a. `resolve.py`, `render.py`, `contrast.*`, `key_message.*`, `gestaltung.py`) und `reporting/title_policy.py` spiegelt Freelancing (Meridian) per PIN; dort nur mit Spiegel-Nachzug ändern |

## 1. Familien

| Familie | Ordner | Zweck — und was sie nicht ist |
|---|---|---|
| Emissionskern | `superversion/` | Einziger Orchestrierungs- und Emissionskern: ALUCA-Bedeutung → kanonisches Modell → Ziele (TMDL, PBIR, OSI, Databricks, Architektur-Artefakte). Zielbild seit 12.11.2026; heute liegen noch drei Orchestratoren daneben (`../products/fabric/orchestrator/`, `../products/fabric/powerbi/orchestrator/`, `../products/oss_adapters/orchestrator/`), ihr Umzug ist für spätere Runden geplant |
| Erzeugung | `generator/`, `generator_core/`, `codegen/`, `ir/`, `storyline/`, `visual_library/`, `reporting/`, `brand/` | Schreibt Artefakte aus dem Golden Thread: Measures und Modellgerüst (`generator/`), Python-IR-Framework (`generator_core/`), DAX aus Action Codes und Katalog (`codegen/`), Zwischenrepräsentation (`ir/`), Storyline je Use Case (`storyline/`), Visual-Auswahl (`visual_library/`), Titel- und Formatregeln (`reporting/`), Markenableitung (`brand/`) |
| Prüfung | `validation/`, `quality/`, `report_quality/`, `linters/`, `ontology/`, `stage2_review/` | Vier Stufen, kein Doppel: `validation/` prüft die governten Quellartefakte (Katalog, Factsheets, Brackets, Action Codes, Datenverträge, TMDL/DAX) und ist Stage 1; `quality/` orchestriert das Quality-Gate und hält das Werkzeug-Manifest (`quality/tooling_manifest.yaml`) und die bekannten Fehler (`quality/known_errors.yaml`); `report_quality/` prüft erzeugte Report-Artefakte adapterneutral (PBIR-Struktur, Schema, Inhalt, Scorecards, LLM-Judge, Self-Heal); `linters/` hält Regelsätze (BPA-Regeln, `linters/lint.rules.yaml`), keine Prüflogik. Dazu `ontology/` (Registry-Audit über den ganzen Objektgraphen) und `stage2_review/` (Vertrag für die weiche Diff-Prüfung) |
| Schemas | `generator/schemas/`, `schemas/` | Zwei Dinge mit ähnlichem Namen: `generator/schemas/` ist die **Schema-Autorität** für ALUCA-Artefakte (Bracket, Action Code, Layout, Datenvertrag; Studio erzeugt daraus seine TypeScript-Typen). `schemas/pbir/` ist ein **Cache offizieller Microsoft-PBIR-Schemas** plus gepinnte Snapshots; dort wird nichts selbst geschrieben, nur nachgeladen (`schemas/pbir/README.md`) |
| Betrieb | `connectors/`, `git-hooks/`, `migration/`, `project_mgmt/`, `agentic_loop/`, `utils/`, `tests/` | Quell-Connectoren (SAP: Code und README, seit 12.11.2026 hier statt unter `products/`), Hook-Installer und Pre-Push-Gate, einmalige ID-Migrationen mit `--check`, GitHub-Project-Skripte, Einstieg der agentischen Schleife S0–S7, Hilfsmodule, die Python-Testsuite |

Einstiegsskripte im Wurzelordner: `run_stage1_checks.ps1` (Stage 1), `run_all_checks.ps1` (Stage 1 und Fabric),
`run_local_ci_check.sh` (CI lokal nachstellen), `preflight.py` (Python-Seite von Stage 1), `bootstrap.ps1`
(Node- und Python-Abhängigkeiten), `prozess.py` (Kindprozesse auf Windows), `health_scorecard.py`,
`reference_graph.py`, `priority_calculator.py`, `check_kpi_catalog_gaps.py`, `audit_pbir_issues.py`,
`export_customer_package.ps1`.

## 2. „Lies-wenn"-Routing

| Deine Aufgabe ist … | Lies | NICHT nötig |
|---|---|---|
| Stage 1 laufen lassen oder einen roten Stage-1-Check verstehen | `validation/README.md` → `run_stage1_checks.ps1`; Skill `fix-stage1-failure` | report_quality/, superversion/ |
| Erzeugten Report prüfen oder einen Report-Befund reparieren | `report_quality/cli.py` → `validation/docs/REMEDIATION_INSERTABLE_FORMAT.md` | validation/README.md |
| BPA-Regel nachschlagen oder ergänzen | `linters/powerbi/REPORT_BEST_PRACTICES.md`; Linux-Lauf `validation/check_bpa.py` | report_quality/ |
| Ein Schema ändern | `generator/schemas/` (Autorität); danach in `../studio/` `npm run generate:types` | `schemas/pbir/` (nur Cache) |
| Measures aus Action Codes oder Katalog erzeugen | `codegen/action_trigger_dax.py`; Messbasis `codegen/reports/measure_grounding.md` | generator/prompts/ |
| IR-Framework erweitern | `generator_core/FRAMEWORK_CONTRACT.md` → `ir/README.md` → `ir/urgency_derivation_spec.md` | superversion/ |
| Kanonisches Modell, Targets, Spiegel aus Meridian | `superversion/_INDEX.md` | Rest von tooling/ |
| Visual-Library-Ausgabe live abnehmen | `visual_library/acceptance/CHECKLIST.md`; Skill `visual-library` | validation/ |
| Quell-Connector anbinden | `connectors/sap/README.md` | products/ |
| Inhaltliche Repo-Qualität mit Prompts verbessern | `generator/prompts/repo_quality_improvement_prompts.md` | codegen/ |

## 3. Dokument-Register (vollständig — Drift-Gate erzwingt das)

> Pfade relativ zu `tooling/`. `README.md` ist ausgenommen, `superversion/` hat einen eigenen Index.

| Ordner | Doc — Zweck | Lies-wenn |
|---|---|---|
| `generator_core/` | `generator_core/FRAMEWORK_CONTRACT.md` — Vertrag des Python-IR-Frameworks | Das Framework erweitern |
| `ir/` | `ir/urgency_derivation_spec.md` — Spezifikation der Dringlichkeits-Ableitung | Dringlichkeit in der IR ändern |
| `codegen/` | `codegen/reports/measure_grounding.md` — Arbeitsblatt Measure-Grounding, erzeugt von `codegen/measure_grounding.py` | Prüfen, worauf ein Measure fußt |
| `validation/` | `validation/docs/REMEDIATION_INSERTABLE_FORMAT.md` — einfügbares Format für Remediation-Hinweise (SSOT) | Einen Befund mit Reparaturvorschlag ausgeben |
| `generator/` | `generator/prompts/repo_quality_improvement_prompts.md` — Prompts zur inhaltlichen Qualitätsverbesserung | Inhalte gezielt nachschärfen |
| `visual_library/` | `visual_library/acceptance/CHECKLIST.md` — Abnahme im echten Rendering<br>`visual_library/tests/golden_docs/Part_D.md` — Golden-Fixture eines Tests, nicht von Hand editieren | Visual Library abnehmen bzw. einen Golden-Test verstehen |
| `linters/` | `linters/powerbi/REPORT_BEST_PRACTICES.md` — Report-BPA-Regeln in Lesefassung | Eine BPA-Regel verstehen |
