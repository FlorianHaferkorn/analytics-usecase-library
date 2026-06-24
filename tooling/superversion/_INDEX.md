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
| Status | Phase-0-Spike ✅; I-1.1–I-1.5 ✅ (Adapter gehärtet an 5 UCs; CLI + Golden-Snapshots); I-2.x ✅; I-3.1 Vertrag ✅, I-3.2 TMDL ✅, I-3.3 PBIR (official-first) ✅, I-3.4 Golden-Thread-Gate ✅, I-3.5 E2E-Smoke ✅ (I-3 komplett); übrige I-4..I-9 im Umsetzungsplan |
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
`e2e_smoke.py` (+ `tests/test_e2e_smoke.py`)
sowie der vendored Meridian-Subtree unter
`vendor/meridian/` (+ `PIN.json`) sind kein `*.md` und unterliegen nicht dem
Index-Gate; sie sind über das Routing in §1 erreichbar.)*

## 3. Verwandte Top-Level-Artefakte (Repo-Root, kein lokaler Index-Owner)

Die folgenden Planungsdokumente liegen im Repo-Root (von keinem `_INDEX.md` regiert)
und steuern diesen Bereich — hier als Pointer registriert, damit der Bezug nicht driftet:

- UMSETZUNGSPLAN_SUPERVERSION.md — der I-1..I-9-Bauplan (Single Source of Truth für Status, Ledger §6).
- PRODUCT_PLAN.md — Produkt-Zielbild, Phasen, Premium-Floors F1–F6.
- SYNERGY_ALUCA_MERIDIAN.md — Vergleich + Zielarchitektur + Code-Tiefenanalyse.
