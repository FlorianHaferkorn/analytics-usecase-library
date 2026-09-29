---
last-reviewed: 2026-09-25
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
| Massenänderung (Sweep) gegenprüfen | `pruefe_sweep.py` | Einzel-Gates |
| Showcase-Delta-Tabellen geändert | `check_showcase_delta.py` | `check_plattform.py` |
| Neues Repo mit dem Claude Repo Kit einrichten | `repo_kit_init.py` | Gates |

## 2. Register

| Skript | Art | Zweck |
|---|---|---|
| `gadw_gate.py` | Gate-Sammler | Alle ständig aktiven Tier-0-Gates in einem Aufruf |
| `check_index.py` | Drift-Gate | Hält die `_INDEX.md`-Navigation ehrlich und platzhalterfrei |
| `check_workflows.py` | Gate | Jede Workflow-Datei ist gültiges YAML und deklariert Jobs |
| `check_dataarch_mirror.py` | Sensor | Drift des gespiegelten Meridian-Dataarch-Vertrags (ADR-0051) und der vendorten Power-BI-Themes aus Freelancing `products/pbi_theme` (`--write-themes`, seit 29.09.2026) |
| `check_superversion_pins.py` | Sensor | Pin-Drift der Superversion (ADR-0005 Regel 6) |
| `check_plattform.py` | Ratchet | Sperrklinke gegen Annahmen, die nur auf Linux stimmen (`plattform_baseline.json`) |
| `pruefe_sweep.py` | Gegenprobe | Prüft mechanische Massenänderungen nach |
| `check_showcase_delta.py` | Gate | Konsistenz der Showcase-Delta-Tabellen |
| `repo_kit_init.py` | Werkzeug | Erkennungs- und Scaffold-Engine des Claude Repo Kits |

Datendateien: `plattform_baseline.json` (Stand der Plattform-Ratchet),
`kundendaten-sperrliste.beispiel.json` (Beispiel-Sperrliste für CI ohne lokale Liste).
