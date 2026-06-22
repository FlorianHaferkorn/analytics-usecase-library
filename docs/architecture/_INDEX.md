---
last-reviewed: 2026-06-16
shelf-life-days: 90
---
# Architektur — Zentraler Anlaufpunkt (_INDEX)

> **Einstieg in die Architektur-Ebene.** Ein neuer Chat/Agent liest **zuerst diese
> Datei** und navigiert von hier gezielt weiter — **nicht** den ganzen Ordner.
> Entscheidungen leben in den ADRs (`adr/`), Belege in `prior-art-…`, offene Punkte
> im Ledger unten — nicht verstreut im Fließtext.

| Feld | Wert |
|---|---|
| Stand | 2026-06-16 |
| Rolle | L0-Navigation der Architektur-Ebene |
| ADR-Liste | `adr/README.md` (chronologischer Index der Decision Records) |

---

## 1. „Lies-wenn"-Routing (nur das Nötige lesen)

| Deine Aufgabe ist … | Lies (in dieser Reihenfolge) | NICHT nötig |
|---|---|---|
| Agent-Skills/Tools integrieren (offiziell-first) | `adr/0002-official-first-agent-integration-and-guided-workflow.md` → `../agent/guided-agent-development-workflow.md` | Migration |
| Aktivierung/Onboarding + Capability-Gating | `adr/0003-customer-activation-and-capability-gating.md` → `../agent/capability-manifest.md` | ADR-0001 |
| Validierungs-Backends / Capability-Tiers verstehen | `adr/0001-pluggable-validation-backends-and-capability-tiers.md` | ADR-0002/0003, Migration |
| Industry-/Extension-Use-Cases anlegen (EXT/IND-Schema, Sektor-Register) | `adr/0004-industry-variant-use-case-tier-taxonomy.md` → `../../core/usecases/README.md` | ADR-0001/0002/0003 |
| Superversion-Heimat / Meridian-Core einziehen (Vendoring, Pin, Contract-Mirror) | `adr/0005-superversion-home-and-meridian-vendoring.md` → `../../tooling/superversion/_INDEX.md` | ADR-0001/0002/0003 |
| Migration zwischen BI-Tools entwerfen | `migration-ingest-adapter.md` → `prior-art-agentic-integration-and-migration.md` | ADRs |
| Welches Tooling deckt welche Aufgabe ab | `quality-tooling-map.md` | Rest |
| Repo-Referenzgraph / Abhängigkeiten | `reference_graph.md` | Rest |
| Skill-Docs retire-vs-keep entscheiden (ADR-0002) | `skills-retire-vs-keep.md` | Rest |

Faustregel: **ein L0 → (ein Detail)-Pfad genügt** für die meisten Aufgaben.

---

## 2. Dokument-Register (jede `*.md` im Bereich — Drift-Gate)

| Doc | Zweck | Lies-wenn |
|---|---|---|
| `adr/0001-pluggable-validation-backends-and-capability-tiers.md` | ADR: pluggable Validation-Backends + Capability-Tiers (Status: deferred) | Validierungsstrategie |
| `adr/0002-official-first-agent-integration-and-guided-workflow.md` | ADR: official-first Agent-Integration + GADW (Proposed) | Agent-Integration |
| `adr/0003-customer-activation-and-capability-gating.md` | ADR: Customer-Activation + Capability-Gating (Proposed) | Aktivierung/Onboarding |
| `adr/0004-industry-variant-use-case-tier-taxonomy.md` | ADR: Industry-Variant Use-Case-Tier-Taxonomie (EXT/IND-Schema, Verzeichnisbaum, Sektor-Register) (Proposed) | Use-Case-Tier/Taxonomie |
| `adr/0005-superversion-home-and-meridian-vendoring.md` | ADR: Superversion-Heimat (ALUCA) + Meridian-Core-Vendoring (gepinnt, Contract-Mirror, vendor-sync) (Accepted) | Superversion-Heimat/Meridian-Einzug |
| `migration-ingest-adapter.md` | Hub-and-Spoke N-zu-M-Migration (Sketch) | Migration entwerfen |
| `prior-art-agentic-integration-and-migration.md` | Recherche + Quellen zu Agentic-Integration & Migration | Belege/Hintergrund |
| `quality-tooling-map.md` | Welches Tooling welche Qualitäts-/Validierungsaufgabe abdeckt | Tooling-Übersicht |
| `reference_graph.md` | Repo-Referenzgraph / Abhängigkeiten | Abhängigkeiten |
| `skills-retire-vs-keep.md` | Skill-Docs: KEEP (Governance) vs. THIN (Mechanik → Upstream) (ADR-0002) | Skill-Scope entscheiden |

<!-- Ausgenommen (EXEMPT_FILES): README.md, adr/README.md, NAVIGATION_PHILOSOPHY.md.
     check_index.py erzwingt: jede nicht-exempte *.md im Subtree ist hier gelistet. -->

---

## 3. Offene Punkte (Ledger — hier abhaken, NICHT im Fließtext)

| ID | Punkt | Status | Datum |
|---|---|---|---|
| A-1 | ADR-0002/0003 reviewen + mergen | **erledigt** (#313/#314) | 2026-06-16 |
| A-2 | Build-vs-buy Overlay-Generator | **erledigt — shim-only** (2026-06-16): `ruler` für Long-Tail-Agenten (distinkte Configs); `AGENTS.md`/`CLAUDE.md` unberührt | 2026-06-16 |
| A-3 | `docs/agent/` auf `_INDEX.md`-Navigation heben | **erledigt** (#314) | 2026-06-16 |
| A-4 | Architektur-Index in `CLAUDE.md`-Routing verlinken | **erledigt** (#314) | 2026-06-16 |
| A-5 | Skill-Docs retire-vs-keep (ADR-0002) | **erledigt** (`skills-retire-vs-keep.md`: 11 KEEP, 3 THIN) | 2026-06-16 |
| A-6 | Upstream `skills-for-fabric` pin + Cadence | **erledigt**: ALLOWLIST + Cron Mo+Do (`source-updates.yml`) | 2026-06-16 |
| A-7 | Industry-Variant-Use-Case-Tier-Taxonomie ratifizieren (KNOWN_GAPS §7 Prereq #4) | **erledigt** (ADR-0004): EXT/IND-Sektor-Schema, neue Tier-Bäume unter `core/usecases/`, Sektor-Register R/L/M | 2026-06-18 |
| A-8 | Superversion-Heimat + Meridian-Einzug ratifizieren (UMSETZUNGSPLAN I-2.1 [QA/SA]) | **erledigt** (ADR-0005): ALUCA = Heimat; Meridian-Core vendored+pinned (vendor-sync default), `canonical_contract` als parity-gated Standalone-Mirror, Neutral-Core über die Naht gewahrt | 2026-06-22 |
