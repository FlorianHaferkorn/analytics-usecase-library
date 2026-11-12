---
last-reviewed: 2026-11-12
status: gemessen
---
# Zielbaum ALUCA, Phase 0 und 1: Runde vom 12.11.2026

Branch `runde/2026-11-12-zielbaum-phase01`, Basis `origin/main` @ 899fc5fc. Grundlage ist der Zielbaum-Vorschlag
vom 12.11.2026, Teil B (ALUCA). Florian hat Phase 0 und Phase 1 am 12.11.2026 freigegeben; Phasen 2 bis 4 sind
nicht Teil dieser Runde.

## Ergebnis

| Messgröße | vorher (899fc5fc) | nachher (Branch) | Methode |
|---|---:|---:|---|
| `_INDEX.md`-Dateien | 11 | 14 | `python scripts/check_index.py --strict`, Zusammenfassungszeile |
| harte Befunde Drift-Gate | 0 | 0 | dasselbe |
| Warnungen Drift-Gate | 9 | 11 | dasselbe; neu: Routing-Hinweis für `core/_INDEX.md`, `studio/_INDEX.md` und `docs/plans/_INDEX.md` (dieser Bericht im Flach-Register, wie seine beiden Vorgänger); weg: Staleness `scripts/_INDEX.md` |
| vom Gate erfasste Docs in `core/`, `tooling/`, `studio/` | 0 | 157 (104 + 8 + 45) | Probe mit leeren Indizes in den drei Ordnern, Zählung der Vollständigkeitsbefunde |
| Negativkontrolle | — | 3 von 3 | je eine nicht registrierte `.md` in `core/usecases/`, `tooling/linters/`, `studio/docs/` angelegt: 3 harte Befunde, Exit 1; danach entfernt, Exit 0 |

## Phase 0: drei neue Bereichs-Indizes

| Index | Inhalt |
|---|---|
| `../../core/_INDEX.md` | Golden Thread; „Lies-wenn“-Routing zu den `README.md` von `kpi_catalog/`, `action_codes/`, `usecases/`, `semantic_models/`, `templates/page_templates/`, `data_contracts/`, `brand/`; gruppiertes Register der 104 Docs; Hinweis auf den eigenen Index von `strategy_operating_model/` und auf die von Freelancing gespiegelten Teilbäume |
| `../../tooling/_INDEX.md` | fünf Familien: Emissionskern `superversion/`; Erzeugung; Prüfung mit getrenntem Zweck (`validation/` = Stage 1 auf Quellartefakten, `quality/` = Gate-Orchestrierung und Manifest, `report_quality/` = erzeugte Reports, `linters/` = Regelsätze); Schemas (`generator/schemas/` = Autorität, `schemas/pbir/` = Cache offizieller PBIR-Schemas); Betrieb. Register der 8 Docs |
| `../../studio/_INDEX.md` | ALUCA Studio als eigenständiges Nagarro-Produkt (Entscheidung Florian 12.11.2026); Register der 45 Docs. Ersetzt den Marker `studio/.claude-no-index`, der Studio bis heute vom Gate ausnahm (entfernt) |

Zusätzlich: drei Zeilen in der Bereichs-Landkarte von `CLAUDE.md`, ein Abschnitt „Navigation (area indexes)“ in
`AGENTS.md`.

## Phase 1: Umzüge

| # | von → nach | Verweise nachgezogen |
|---|---|---|
| A5 | `products/connectors/sap/README.md` → `tooling/connectors/sap/README.md` | `products/_INDEX.md` (3 Stellen, davon 1 Pfad, den das Gate sonst als tot gemeldet hätte), `CLAUDE.md` (Landkarte), `tooling/README.md` (Ordnerliste) |
| A6 | `tooling/scripts/` aufgelöst: README-Inhalt in `../../scripts/_INDEX.md` (Abschnitt 3), `fix_com001_stub.py` → `_archiv/tooling/scripts/` | `internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md` (Zeile COM-001), `docs/agent/rules/framework-architect.md` (3 Stellen) |
| A7 | `tooling/hooks/pre_push_gate.py` → `tooling/git-hooks/pre_push_gate.py` | `internal/technical_backlog.md`, `tooling/README.md` |

Alle Umzüge mit `git mv` (Ähnlichkeit 100 %). `.githooks/`, `.claude/settings.json`, Workflows und
`.secrets.baseline` nannten keinen der alten Pfade (gemessen mit `git grep`); dort war nichts zu ändern.
`pre_push_gate.py` liegt in derselben Tiefe wie vorher, sein `REPO_ROOT` stimmt weiter.

**Abweichungen vom Plan, beide benannt:**

1. `fix_com001_stub.py` hatte einen Test (`tooling/tests/test_fix_report_page_metadata.py`), der es importiert. Der
   Plan zählte ihn als Code-Verweis. Der Test ist mit dem Skript nach `_archiv/tooling/tests/` gewandert (2 Tests
   weniger in der Suite); ein Test gegen ein archiviertes Skript prüft nichts Lebendes. Den Fehler fängt weiter
   `check_pbip_report_pages.ps1` (Check 8).
2. Die README von `tooling/scripts/` beschrieb nur `hub_sync.py` (Core-YAML nach Starlight in `docs_hub/`). Weder
   das Skript noch `docs_hub/` sind im Repo. Übernommen ist deshalb der Befund, nicht die Bedienungsanleitung. Die
   Agentenregel `framework-architect.md` verlangte an drei Stellen, `hub_sync.py` laufen zu lassen; sie sagt jetzt,
   dass es das Skript nicht gibt. Die generierten Agenten-Konfigurationen sind davon nicht betroffen
   (`generate_tool_configs.py --check`: 18 Dateien gleich).

**`git grep` auf die alten Pfade danach** (ohne `_archiv/`): `products/connectors` 0 Treffer, `tooling/hooks` 1
(Herkunftsnotiz in `tooling/README.md`), `tooling/scripts/` 2 außerhalb von `products/fabric/powerbi/tooling/scripts/`
(der archivierte Pfad in `KNOWN_ERRORS_AND_FIXES.md`, enthält die Zeichenkette; ein historischer Satz über das
2026-06 entfernte `check_brackets_schema.py` in `internal/technical_backlog.md`), `hub_sync` 0. Rundenberichte und
`CHANGELOG.md` nicht angefasst.

## Spiegel nach Freelancing

Kein Umzug berührt einen gespiegelten Pfad. Gemessen gegen Freelancing `origin/main` @ 1ad25e09e: alle `PIN.json`
dort mit ALUCA-Quelle nennen nur `core/templates/page_templates/**` (108 Einträge), `products/fabric/orchestrator`
(1), `tooling/visual_library/*` (18 Einträge, explizite Dateien) und `tooling/reporting/title_policy.py`. Die
Spiegelmenge `core/dataarch_engine/blueprint/aluca_spiegelmenge.json` betrifft den Weg Freelancing → ALUCA
(`tooling/superversion/vendor/meridian_dataarch/`), auch unberührt. Die drei neuen Indizes liegen in den Wurzeln
von `core/`, `tooling/`, `studio/`, außerhalb aller gespiegelten Teilbäume.

Hinweis zum Auftrag: `meridian/vendor/aluca/PIN.json` gibt es in Freelancing nicht; die PINs liegen unter
`core/dataarch_engine/vendor/aluca/PIN.json` und `meridian/vendor/aluca/visual_library/PIN.json`.

## Gates

| Gate | Ergebnis |
|---|---|
| `python scripts/check_index.py --strict` | 14 Indizes, 0 harte Befunde, 11 Warnungen |
| `python3 scripts/check_workflows.py` | OK, 6 Workflow-Dateien (Eigenprüfung, actionlint nicht installiert) |
| `python3 scripts/check_lint_ratchet.py --pin-pflicht` | ruff 0.16.9, 2.490 Befunde in 15 Regeln, eingefroren 2.490 |
| `secret_scan_gate.py --baseline` | 0 neue Funde in 4.359 Dateien (detect-secrets 1.5.0); der Hinweis auf verschobene Zeilennummern in `.secrets.baseline` erscheint auf `origin/main` genauso |
| `generate_tool_configs.py --check` | 18 generierte Dateien gleich |
| gezielte Tests (12 Dateien: Index-Gate, SAP-Connector, Pre-commit-Hook, Lint-Ratchet, Schema-Registry u. a.) | 280 bestanden |
| Python-Suite `python -m pytest tooling/tests/ products/ -q` | 3.358 bestanden, 73 übersprungen, 0 rot (418 s, `-n 4`). Der Lauf startete, bevor die Showdaten entpackt waren; datenabhängige Tests können deshalb unter den Übersprungenen sein |
| Stage 1 (`pwsh tooling/run_stage1_checks.ps1`, Linux, Showdaten geholt) | bestanden, Exit 0, 30 Einzelprüfungen OK. Die ausgegebenen KPI-Katalog-Hinweise (`domain_tag`, `calc_type`) betreffen `KPI_Catalog.md`, das diese Runde nicht ändert |

## Bewusst nicht gemacht

| Thema | Grund |
|---|---|
| Phasen 2 bis 4 (A4 Adapter zusammenlegen, A1 Orchestrator in `tooling/superversion/`, A2/A3 PowerShell-Ports) | nicht freigegeben für diese Runde; A1 braucht den gepaarten Freelancing-PR |
| `tooling/README.md` auf den heutigen Stand bringen | eigener Umfang; nennt Ordner, die es nicht gibt (`ai/`, `alignment/`, `generation/`, `maintenance/`, `validation/schemas/`). Der neue Index sagt das und ist maßgeblich |
| `pre_push_gate.py` verdrahten oder löschen | offener Punkt in `internal/technical_backlog.md`, nur umgezogen |
| Archivierte Dateien lauffähig machen (`REPO_ROOT` in `_archiv/`) | Archiv bleibt byte-gleich; Rückweg ist `git mv` an den alten Ort |
| Routing-Warnungen der neuen Indizes (Gruppen-Ordner in keiner Routing-Zeile) | beratend; `products/_INDEX.md` hat dieselbe Form |
| Staleness-Stempel anderer Indizes (`products/`, `docs/agent/` …) | nicht im Ganzen geprüft, Stempel deshalb nicht gesetzt |
| Eigene `_INDEX.md` für `core/kpi_catalog/`, `core/usecases/` u. a. | nicht nötig, `core/_INDEX.md` routet zu deren README |
| `showcases/` ohne Index | nicht Teil von Phase 0 |
