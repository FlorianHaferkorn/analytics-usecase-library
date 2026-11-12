---
last-reviewed: 2026-11-12
status: gemessen
---
# Entschlacken ALUCA: Runde vom 12.11.2026

Branch `runde/2026-11-12-entschlacken`, Basis `origin/main` @ 44120d97. Grundlage ist das Inventar vom selben Tag (IDs C01–C28). Florian hat den Plan am 12.11.2026 freigegeben. Jeder Punkt wurde vor der Aktion auf dem aktuellen Stand nachgeprüft. Wo der Beleg nicht mehr trug, ist der Punkt übersprungen.

## Ergebnis

| | Dateien (`git ls-files`) | Bytes |
|---|---:|---:|
| vorher (44120d97) | 4.504 | 36.192.212 |
| nachher, ganzes Repo | 4.325 | 34.447.895 |
| davon in `_archiv/` | 64 | 802.920 |
| nachher, aktiver Baum (ohne `_archiv/`) | 4.261 | 33.644.975 |
| Differenz aktiver Baum | −243 | −2.547.237 |

**Methode:** `git ls-files` und `os.path.getsize` je Datei, vorher auf 44120d97 und nachher auf dem Kopf des Branches gemessen. „Aktiver Baum“ zieht `_archiv/` ab.

**Kaputte relative Markdown-Links:** 94 vorher, 80 nachher, kein neuer. Gemessen mit einem Linkprüfer über alle `*.md` außer `dist/` und `_archiv/`.

## Je Punkt

| ID | Aktion | Stand | Beleg / Grund |
|---|---|---|---|
| C02 | `framework_evolution.md`, `ACTIONREADY_HOLISTIC_MANIFESTO.md` → `_archiv/internal/archive/…` | erledigt | 7 Links nachgezogen (core/strategy_operating_model, Agent-Regel, generierte Copilot-Instruktionen) |
| C01 | Rest von `internal/archive/` gelöscht (112 Dateien) | erledigt | kein Code-Aufrufer; Ausschlussfilter in 23 PS1-Prüfungen, markdownlint, `kpi_id_migration.py` und Secrets-Baseline auf `_archiv/` umgestellt |
| C04 | `core/templates/page_templates/_archive/` gelöscht | erledigt | `layout_330300_300s_layer.md` erklärt sich selbst als abgelöst durch `Design_Spec_3_30_300.md` §5.4; die Form bleibt in `layout_330300.schema.json`. `preview_v1/` ist durch `preview/` ersetzt, die Slot-Map durch `tokens/visual_slot_mapping.yaml`. `fabric_powerbi.md` umverlinkt |
| C05 | `studio/docs/design-bundle/`, `design-reference/` gelöscht | erledigt | 17 Dateien blob-gleich mit `rebuild/MOCKUP_REFERENCE/`; einziger Unterschied ist `Studio.html` (`fontPairing` inter statt geist), im neuen README dort vermerkt; 5 Verweise umgestellt |
| C06 | Wurzel-`skills/` gelöscht | erledigt | kein Konsument in ALUCA oder Freelancing (grep 12.11.2026). Der Generator schreibt nur noch `.claude/skills/` und meldet einen SKILL.md unter `skills/` als `retired`. Test angepasst und erweitert |
| C08 | `orchestrate_oss.py` repariert | erledigt | dokumentierter Aufruf lief nicht (`No module named 'tooling'`), Importe zeigten auf `products.oss…`; neuer Test fährt den Aufruf, Gegenprobe mit altem Skript: 4 von 7 rot |
| C14 | tote Pfade in Skripten repariert | erledigt | Supervisor nutzt `run_quality_gate.ps1` (mit pwsh 7.4.6 gegen ein Stub-Gate geprüft); 2 VS-Code-Tasks entfernt; `kpi_catalog_SCHEMA.md` (Groß/Klein); `Layout_Grid_System.md`; `suggester.py` (+ Test, Gegenprobe rot); `blueprints/*.yaml`; zwei Skills |
| C23 | `internal/proposal_costing` → `products/proposal_costing` | erledigt | 55 Tests laufen jetzt in der Suite; `run_cost_delta.py` umgestellt (19 Tests grün) |
| C15 | 4 Pläne → `_archiv/docs/plans/` | erledigt | `UMSETZUNGSPLAN_SUPERVERSION` ist bis auf I-9.2 (gehostete Topologie) und I-9.3 (Prämisse widerlegt) abgeschlossen. ADR-Links und Code-Kommentare zeigen auf `_archiv/` |
| C17 | `research/I6-6/` + Routing-Charter → `_archiv/` | erledigt | ADR-0008 ist accepted |
| C19 | 9 interne Dokumente, `ci/`, `vision/` → `_archiv/internal/` | erledigt | Agent-Regeln lesen statt des Status 04/2026 jetzt `CHANGELOG.md` |
| C26 | `page_templates/preview/` → `_archiv/` | erledigt, außer `src/grid/slot-pos.ts` | `test_logical_units.py` liest die Datei; neues README dort |
| C16 | `KONZEPT_LAYOUT_SYSTEM.md` | **übersprungen** | Beleg „veraltet“ trägt nicht: §9 ist ein lebendes Ledger (L1/L6 teilweise, L9/L10 offen), und Freelancing `Strategie/OFFENE_PUNKTE_I20.md` verweist darauf als Statusquelle |
| C18 | `ibcs.yaml`, `ibcs_summary.md` | **übersprungen** | Freelancing `docs/konzepte/2026-10-09_Konzept_Reporting-Profile.md` zitiert `ibcs_summary.md` als Korpus; das Inventar hatte nur `ibcs_v2.yaml` gefunden |
| C27 | 4 ADRs „Proposed“ | **übersprungen** | ADRs werden nicht verschoben; der Status ist eine Entscheidung (annehmen, ablehnen oder historisch) |

Dazu in dieser Runde:
- `scripts/lint_baseline.json` festgeschrieben: Ruff-Befunde 2.756 → 2.490, nur durch die Löschungen.
- `generate_aurora_costing.py` schreibt `newline="\n"`. Nach dem Umzug misst die Plattform-Sperrklinke die Datei mit, die Ausgabe ist byte-gleich.
- 4 neue Fehlerklassen in `internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md`.

## Prüfungen

| Prüfung | Ergebnis |
|---|---|
| `python scripts/check_index.py --strict` | 0 harte Befunde, 9 Warnungen (Staleness, beratend) |
| `python -m pytest tooling/tests/ products/ -q` (einmal, ganze Suite) | 3.315 passed, 73 skipped, 0 failed (13:30 min, Stand Commit 3aab7f96; danach nur dieser Bericht) |
| gezielte Tests während der Runde | `tooling/tests/test_generate_tool_configs.py`, `products/oss_adapters/tests`, `tooling/generator_core/tests/test_intelligence.py`, `products/proposal_costing`, `tooling/tests/test_project_run_cost_delta.py`, `test_logical_units.py`, `test_konsolidierung.py`: alle grün |
| `generate_tool_configs.py --check` | OK, 18 Dateien |
| Secret-Baseline-Tor (pre-commit, detect-secrets 1.5.0) | 0 neue Funde je Commit |
| `check_plattform.py` | OK |
| Stage 1 | `pwsh 7.4.6` `./tooling/run_stage1_checks.ps1` nach `npm ci` in `tooling/validation`: Exit 1, rot nur durch zwei Prüfer mit Exit 2 (nicht gelaufen): `check_model_vs_gold.py` und `check_action_outcome_reconciliation.py` brauchen die Aurora-Gold-Daten (`showcases/aurora_group/data/showdaten.py`), die in dieser Sitzung nicht geholt wurden. Alle übrigen Schritte grün. Fabric-Teil (`run_quality_gate.ps1`) nicht gelaufen. |

## Bewusst nicht gemacht

- **C03, C25:** Freelancing liest diese Dateien (`dist/`-Report, Use Cases). Sie sind nicht angefasst.
- **C07, C09, C10, C11, C12, C20, C21, C28** (Lösch-Kandidaten): nicht im freigegebenen Umfang, der nur Archiv-Kandidaten umfasste. Nächste Runde.
- **C13 (BPA), C24 (Orchestrator), `studio/`:** nur analysiert (Phase 2, außerhalb des Repos). Entscheidungen stehen aus.
- **C22** (Logo verkleinern): nicht im Umfang.
- **Rückverweise:** Rund 30 Fließtext-Erwähnungen gelöschter `internal/archive/…`-Pfade in historischen Dokumenten (`CHANGELOG.md`, `KNOWN_ERRORS_AND_FIXES.md`, `KNOWN_GAPS.md`, ADR-Texte, `tooling/README.md`) sind nicht umgeschrieben. Sie beschreiben den Stand ihres Datums. Markdown-Links sind alle nachgezogen.
- **Teile des Supervisors (C14):** Das pbi-tools-Compile-Gate und die Cursor-Desktop-Log-Brücke des archivierten Wrappers sind nicht in den Supervisor übernommen.
- **Rückweg als Tag:** Der Tag `vor-entschlacken-2026-11-12` ließ sich nicht pushen. Der Proxy lehnt Tag-Pushes und die Git-Refs-API ab. Der Rückweg liegt deshalb als Branch `archiv/vor-entschlacken-2026-11-12` (= 44120d97) auf origin.

## Rückweg

```bash
git fetch origin archiv/vor-entschlacken-2026-11-12
git checkout origin/archiv/vor-entschlacken-2026-11-12 -- <pfad>   # einzelne Datei/Ordner zurückholen
git revert <commit>                                                 # einen Schritt der Runde zurücknehmen
```
