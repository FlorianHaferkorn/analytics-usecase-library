---
last-reviewed: 2026-06-23
shelf-life-days: 90
---
# Superversion — Bereichs-Index (_INDEX)

> **Erstkontakt für den Superversion-Layer** (ALUCA × Meridian). Eine neue
> Claude-Code-Session liest **zuerst** `AGENTS.md` → `CLAUDE.md` → den eigenen
> Task-Block in `UMSETZUNGSPLAN_SUPERVERSION.md` (Repo-Root) → dann von hier gezielt
> die nötige Detail-Datei. **Nicht** den ganzen Ordner scannen.

| Feld | Wert |
|---|---|
| Stand | 2026-06-23 |
| Rolle | Bereichs-Index des Superversion-Source-Adapters (ALUCA-Bedeutung → kanonisches Modell) |
| Status | Phase-0-Spike ✅; I-1.1–I-1.5 ✅ (Adapter gehärtet an 5 UCs; CLI + Golden-Snapshots); I-2.x ✅; I-3.1 Vertrag ✅, I-3.2 TMDL ✅, I-3.3 PBIR (official-first) ✅, I-3.4 Golden-Thread-Gate ✅, I-3.5 E2E-Smoke ✅ (I-3 komplett); I-4.1 Value-Eval-Referenzdaten ✅, I-4.2 Value-Gate ✅, I-4.3 ≥2 Ontologien/Regression ✅, I-4.4 COMP-DSGVO ✅ (I-4 komplett); I-5.1 Visual-Library ✅, I-5.2 Report-Documenter ✅, I-5.3 gov/eng/arch-Engines (Beta) ✅, I-5.4 Tool-Domänen-Packs ✅ (Stufe I-5 komplett); I-6.1 Studio-Inventur ✅ + E-1/ADR-0007 ✅, I-6.2 „Vor dem Core"-Bridge ✅; übrige I-6.3..I-9 im Umsetzungsplan |
| Verlinkt von | Umsetzungsplan (Repo-Root), PRODUCT_PLAN |

## 1. „Lies-wenn"-Routing (nur das Nötige lesen)

| Deine Aufgabe ist … | Lies (in dieser Reihenfolge) | NICHT nötig |
|---|---|---|
| Den Adapter erweitern/härten (I-1.x) | `from_aluca.py` → `canonical_contract.py` → `tests/test_from_aluca.py` | restlicher Plan |
| Den Ziel-Vertrag verstehen (Felder, Parität) | `canonical_contract.py` (Seam) → `_canonical_mirror.py` (Standalone-Mirror) | Adapter-Logik |
| Meridian-Einzug / Vendoring verstehen (ADR-0005) | `canonical_contract.py` → `_meridian_vendor.py` → `vendor/meridian/PIN.json` | Mirror-Felder |
| Pin-Drift prüfen (meldet, bumpt nie) | Repo-Root: `scripts/check_superversion_pins.py` (+ `tests/test_pin_sensor.py`) | Adapter-Logik |
| Stack-Target emittieren / neuen Adapter registrieren (ADR-0006) | `targets/base.py` (`emit(canonical)→{Pfad:Inhalt}`, Registry, `render`) → `tests/test_targets.py` | Source-Adapter |
| TMDL-Semantic-Model emittieren (I-3.2) | `targets/tmdl.py` (Dialekt→DAX hier; TMDL-Hardrules) → `tests/test_tmdl_target.py` | restliche Targets |
| PBIR-Report emittieren (I-3.3, official-first) | `targets/pbir.py` (`emit(canonical.report)`; Visual→PBIR-Typ/Rollen, HITL-Platzhalter; Gate `powerbi-report-author validate`) → `tests/test_pbir_target.py` | restliche Targets |
| Golden-Thread prüfen (jede Measure hat Anker) (I-3.4) | `golden_thread.py` (`validate_golden_thread`/`assert_golden_thread`; CLI Stage-Gate) → `tests/test_golden_thread.py` | Targets |
| E2E-Smoke fahren (Bracket→TMDL+PBIR→validate) (I-3.5) | `e2e_smoke.py` (`python -m tooling.superversion.e2e_smoke [--require-cli]`; Stage-Kette source→golden_thread→tmdl→pbir) → `tests/test_e2e_smoke.py` | Einzel-Targets |
| KPI-**Werte** zertifizieren / Referenzdaten (I-4.1) | `eval/refdata.py` (Loader) + `eval/refcalc.py` (Referenz-Aggregation) + `eval/data/` (synthetischer Fakt + erwartete Werte je UC) → `tests/test_eval_refdata.py` | Targets |
| Value-Gate: KPI-Zahl vs. Referenz (I-4.2) | `eval/value_gate.py` (`check_values`/`assert_values`; CLI `python -m tooling.superversion.eval.value_gate <UC> [--values f] [--advisory]`; FAIL bei Abweichung > Toleranz, ohne Werte advisory) → `tests/test_value_gate.py` | I-4.1-Referenzdaten |
| Eval gegen ≥2 Ontologien / Regression (I-4.3) | `eval/data/supply_deliveries.yaml` + `eval/data/expected/SCM-002.yaml` (2. Ontologie) → `tests/test_eval_regression.py` (parametrisiert über `available_use_cases()`) | — |
| COMP-DSGVO prüfen (PII ohne RLS → FAIL) (I-4.4) | `eval/comp_gate.py` (`check_compliance`/`assert_compliance`; CLI `python -m tooling.superversion.eval.comp_gate [--warn]`; liest `data_protection` je UC, RLS aus `Role.table_permissions`) → `tests/test_comp_gate.py` | — |
| Visual-Library / Visual-Spec auflösen (I-5.1) | `layer_tools/visual_library.py` (lädt `core/templates/page_templates/visual_registry.yaml`; Block/Slot→Spec, allowed/forbidden pbip_type, `is_default`; CLI `list\|describe\|resolve`; Brücke `block_for_aluca_visual`/`sanctions` → I-3.3) → `tests/test_visual_library.py` | — |
| Handover-Doku generieren (branded MD) (I-5.2) | `layer_tools/report_documenter.py` (`render_markdown(model)`; Business+Technical; CLI `python -m tooling.superversion.layer_tools.report_documenter <bracket> [--out]`; DOCX deferred=MD-only) → `tests/test_report_documenter.py` (+ Golden `tests/golden_docs/*.md`) | — |
| gov/eng/arch-Engine ausführen/registrieren (I-5.3, Beta) | `layer_tools/engines/base.py` (Contract `run(canonical,mode)→[EngineFinding]`, Registry) + Beta-Engines `layer_tools/engines/gov_engine.py`, `layer_tools/engines/dataarch_engine.py`, `layer_tools/engines/dataeng_engine.py` + `layer_tools/engines/cli.py` (`python -m …engines.cli all\|<id> <bracket> [--mode]`) → `tests/test_engines.py` | — |
| Tool-spezifisches Domänen-Regelpack ausführen (I-5.4, G7) | `layer_tools/packs/base.py` (Contract `check(canonical)→[str]` je Rule, Registry, `evaluate`; `planned`-Liste = API-abhängig „geplant", als `PACK_PLANNED` ausgegeben) + Packs `layer_tools/packs/unity_catalog.py`, `layer_tools/packs/purview.py`, `layer_tools/packs/dbt.py` + `layer_tools/packs/cli.py` (`python -m …packs.cli all\|<id> <bracket>`) → `tests/test_packs.py` | — |
| Studio→Python-Bridge (ADR-0007, Subprocess-Seam, I-6.2) | `bridge.py` (`precore <bracket>` → JSON `{ok,bracket,engines[]}` aus den gov/eng/arch-Engines; rein/deterministisch; Fehler als JSON+Exit 1; das Studio spawnt dies, Studio-seitig `studio/src/lib/bridge/superversion-bridge.ts` + `studio/src/app/api/precore/route.ts` + Panel) → `tests/test_bridge.py` | Studio-UI-Code |
| Verstehen, was geprüft wird (DoD) | `tests/test_from_aluca.py` (+ `tests/golden/*.json` Snapshots) | — |
| Modell als JSON exportieren / Snapshot regenerieren | `python -m tooling.superversion.from_aluca <bracket> --out tests/golden/*.json` | — |
| Den Gesamt-Bauplan/die Reihenfolge | Repo-Root: UMSETZUNGSPLAN_SUPERVERSION.md | Code |
| Zielbild/Phasen/Premium-Floors | Repo-Root: PRODUCT_PLAN.md | Code |
| Architektur/Wettbewerb (Hintergrund) | Repo-Root: SYNERGY_ALUCA_MERIDIAN.md | Code |

## 2. Dokument-Register (jede `*.md` im Bereich — Drift-Gate)

| Doc | Zweck | Lies-wenn |
|---|---|---|
| `_INDEX.md` | dieser Bereichs-Index | Erstkontakt |

*(Code-Dateien `from_aluca.py`, `canonical_contract.py` (Seam), `_canonical_mirror.py`
(Standalone-Mirror), `_meridian_vendor.py` (Vendor-Loader), `__init__.py`,
`tests/test_from_aluca.py`, `targets/base.py` + `targets/tmdl.py` + `targets/pbir.py` (+
`targets/__init__.py`, `tests/test_targets.py`, `tests/test_tmdl_target.py`,
`tests/test_pbir_target.py`), `golden_thread.py` (+ `tests/test_golden_thread.py`),
`e2e_smoke.py` (+ `tests/test_e2e_smoke.py`), das `eval/`-Paket
(`eval/__init__.py`, `eval/refdata.py`, `eval/refcalc.py`, `eval/value_gate.py`,
`eval/comp_gate.py`, `eval/data/*.yaml`, `eval/data/expected/*.yaml` +
`tests/test_eval_refdata.py`, `tests/test_value_gate.py`,
`tests/test_eval_regression.py`, `tests/test_comp_gate.py`), das `layer_tools/`-Paket
(`layer_tools/__init__.py`, `layer_tools/visual_library.py`,
`layer_tools/report_documenter.py`, das `layer_tools/engines/`-Paket
(`layer_tools/engines/base.py`, `layer_tools/engines/gov_engine.py`,
`layer_tools/engines/dataarch_engine.py`, `layer_tools/engines/dataeng_engine.py`,
`layer_tools/engines/cli.py` + je `__init__.py`), das `layer_tools/packs/`-Paket
(`layer_tools/packs/base.py`, `layer_tools/packs/unity_catalog.py`,
`layer_tools/packs/purview.py`, `layer_tools/packs/dbt.py`,
`layer_tools/packs/cli.py` + `__init__.py`) + `tests/test_visual_library.py`,
`tests/test_report_documenter.py`, `tests/test_engines.py`, `tests/test_packs.py`;
Doc-Snapshots unter `tests/golden_docs/`, Drift-Gate-ausgenommen wie `tests/golden/`)
sowie der vendored Meridian-Subtree unter
`vendor/meridian/` (+ `PIN.json`) sind kein `*.md` und unterliegen nicht dem
Index-Gate; sie sind über das Routing in §1 erreichbar.)*

## 3. Verwandte Top-Level-Artefakte (Repo-Root, kein lokaler Index-Owner)

Die folgenden Planungsdokumente liegen im Repo-Root (von keinem `_INDEX.md` regiert)
und steuern diesen Bereich — hier als Pointer registriert, damit der Bezug nicht driftet:

- UMSETZUNGSPLAN_SUPERVERSION.md — der I-1..I-9-Bauplan (Single Source of Truth für Status, Ledger §6).
- PRODUCT_PLAN.md — Produkt-Zielbild, Phasen, Premium-Floors F1–F6.
- SYNERGY_ALUCA_MERIDIAN.md — Vergleich + Zielarchitektur + Code-Tiefenanalyse.
