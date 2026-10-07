---
last-reviewed: 2026-10-01
shelf-life-days: 90
owns: "*.py"
---
# scripts — Repo-Gates und Sensoren (_INDEX)

> Einzelskripte, die aus der Repo-Wurzel laufen: Drift-Gates, Sensoren, Ratchets.
> Fachliche Generatoren und Validatoren liegen unter `tooling/`, nicht hier.
> `owns: *.py` — jedes Skript hier muss im Register stehen (hart geprüft).

## 1. „Lies-wenn"-Routing

| Deine Aufgabe ist … | Lies | NICHT nötig |
|---|---|---|
| Vor dem Commit alle Tier-0-Gates fahren | `gadw_gate.py` | Einzel-Gates |
| `_INDEX.md` oder `CLAUDE.md` geändert | `check_index.py` | `check_workflows.py` |
| CI ist rot, Ursache unklar | `check_workflows.py` | `check_index.py` |
| Meridian-Spiegel nachziehen oder prüfen | `check_dataarch_mirror.py`, `check_superversion_pins.py` | `check_showcase_delta.py` |
| Test oder Skript nimmt Linux an (Pfade, Encoding) | `check_plattform.py` | `check_dataarch_mirror.py` |
| Ruff-Sperrklinke rot oder Lint aufgeräumt | `check_lint_ratchet.py` | `check_plattform.py` |
| Massenänderung (Sweep) gegenprüfen | `pruefe_sweep.py` | Einzel-Gates |
| Showcase-Delta-Tabellen geändert | `check_showcase_delta.py` | `check_plattform.py` |
| Semantic Model gegen Gold-Daten prüfen (fehlende `sourceColumn`, Ledger A-24) | [`../tooling/validation/check_model_vs_gold.py`](../tooling/validation/check_model_vs_gold.py) (liest `_metadata`/`_active_paths` von hier) | `check_plattform.py` |
| Secret-Baseline-Tor rot (CI `python-checks` oder pre-commit), neuer Fund oder Pin-Hash gemeldet | [`../products/fabric/powerbi/deployment/scripts/secret_scan_gate.py`](../products/fabric/powerbi/deployment/scripts/secret_scan_gate.py) `--baseline` (Doku: [`../products/fabric/powerbi/deployment/.azure-pipelines/README.md`](../products/fabric/powerbi/deployment/.azure-pipelines/README.md) „Secret Baseline Gate“) | `check_index.py` |
| Neues Repo mit dem Claude Repo Kit einrichten | `repo_kit_init.py` | Gates |

## 2. Register

| Skript | Art | Zweck |
|---|---|---|
| `gadw_gate.py` | Gate-Sammler | Alle ständig aktiven Tier-0-Gates in einem Aufruf |
| `check_index.py` | Drift-Gate | Hält die `_INDEX.md`-Navigation ehrlich und platzhalterfrei |
| `check_workflows.py` | Gate | Jede Workflow-Datei ist gültiges YAML und deklariert Jobs |
| `check_dataarch_mirror.py` | Sensor | Drift des gespiegelten Meridian-Dataarch-Vertrags (ADR-0051) der vendorten Power-BI-Themes aus Freelancing `products/pbi_theme` (`--write-themes`, seit 29.09.2026) und des gespiegelten Copilot-Readiness-Kerns aus `products/meridian_copilot_readiness/generator` (`--write-copilot`, seit 30.09.2026) |
| `check_superversion_pins.py` | Sensor | Pin-Drift der Superversion (ADR-0005 Regel 6) |
| `check_plattform.py` | Ratchet | Sperrklinke gegen Annahmen, die nur auf Linux stimmen (`plattform_baseline.json`) |
| `check_lint_ratchet.py` | Ratchet | Ruff-Befunde je Regel eingefroren (`lint_baseline.json`), dürfen nur sinken; Exit 0 OK / 1 gestiegen / 2 nicht gelaufen; Ruff aus PATH, dann `python -m ruff`, Pin aus `stage1.yml`; CI `python-checks` (`--pin-pflicht`, hart) + pre-commit `.githooks/pre-commit` (seit 07.10.2026) und `tooling/git-hooks/pre-commit` Gate 1.6, je nur bei gestagtem `.py` (1 = Abbruch, 2 = `[UNGEPRUEFT]` auf stderr) |
| `pruefe_sweep.py` | Gegenprobe | Prüft mechanische Massenänderungen nach |
| `check_showcase_delta.py` | Gate | Konsistenz der Showcase-Delta-Tabellen; stellt den Delta-Log-Replay (`_active_paths`, `_metadata`: Schema + Partitionsspalten) für andere Tore bereit |
| `repo_kit_init.py` | Werkzeug | Erkennungs- und Scaffold-Engine des Claude Repo Kits |

Datendateien: `plattform_baseline.json` (Stand der Plattform-Ratchet), `lint_baseline.json`
(Stand der Ruff-Ratchet),
`kundendaten-sperrliste.beispiel.json` (Beispiel-Sperrliste für CI ohne lokale Liste).
