---
last-reviewed: 2026-06-22
shelf-life-days: 90
---
# Superversion — Bereichs-Index (_INDEX)

> **Erstkontakt für den Superversion-Layer** (ALUCA × Meridian). Eine neue
> Claude-Code-Session liest **zuerst** `AGENTS.md` → `CLAUDE.md` → den eigenen
> Task-Block in `UMSETZUNGSPLAN_SUPERVERSION.md` (Repo-Root) → dann von hier gezielt
> die nötige Detail-Datei. **Nicht** den ganzen Ordner scannen.

| Feld | Wert |
|---|---|
| Stand | 2026-06-22 |
| Rolle | Bereichs-Index des Superversion-Source-Adapters (ALUCA-Bedeutung → kanonisches Modell) |
| Status | Phase-0-Spike ✅; I-1.1–I-1.5 ✅ (Adapter gehärtet an 5 UCs: COM-001/002/003, FIN-002, SCM-002; CLI + Golden-Snapshots); I-2..I-9 im Umsetzungsplan |
| Verlinkt von | Umsetzungsplan (Repo-Root), PRODUCT_PLAN |

## 1. „Lies-wenn"-Routing (nur das Nötige lesen)

| Deine Aufgabe ist … | Lies (in dieser Reihenfolge) | NICHT nötig |
|---|---|---|
| Den Adapter erweitern/härten (I-1.x) | `from_aluca.py` → `canonical_contract.py` → `tests/test_from_aluca.py` | restlicher Plan |
| Den Ziel-Vertrag verstehen (Felder, Parität) | `canonical_contract.py` (Seam) → `_canonical_mirror.py` (Standalone-Mirror) | Adapter-Logik |
| Meridian-Einzug / Vendoring verstehen (ADR-0005) | `canonical_contract.py` → `_meridian_vendor.py` → `vendor/meridian/PIN.json` | Mirror-Felder |
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
`tests/test_from_aluca.py` sowie der vendored Meridian-Subtree unter
`vendor/meridian/` (+ `PIN.json`) sind kein `*.md` und unterliegen nicht dem
Index-Gate; sie sind über das Routing in §1 erreichbar.)*

## 3. Verwandte Top-Level-Artefakte (Repo-Root, kein lokaler Index-Owner)

Die folgenden Planungsdokumente liegen im Repo-Root (von keinem `_INDEX.md` regiert)
und steuern diesen Bereich — hier als Pointer registriert, damit der Bezug nicht driftet:

- UMSETZUNGSPLAN_SUPERVERSION.md — der I-1..I-9-Bauplan (Single Source of Truth für Status, Ledger §6).
- PRODUCT_PLAN.md — Produkt-Zielbild, Phasen, Premium-Floors F1–F6.
- SYNERGY_ALUCA_MERIDIAN.md — Vergleich + Zielarchitektur + Code-Tiefenanalyse.
