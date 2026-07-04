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
| Superversion Stack-Targets emittieren (Adapter-Vertrag, Registry, render) | `adr/0006-superversion-target-adapter-contract.md` → `../../tooling/superversion/targets/base.py` | ADR-0001/0002/0003 |
| Studio-Cockpit: Ist-Stand + Soll-Schnitt für I-6 (Generate-Naht-Entscheidung) | `studio-capability-inventory.md` → `adr/0007-studio-generate-docks-onto-superversion-core.md` | ADRs (außer 0005/0006/0007) |
| Studio-Generate-Naht: dockt auf Python-Core (E-1 ratifiziert) | `adr/0007-studio-generate-docks-onto-superversion-core.md` → `../../tooling/superversion/e2e_smoke.py` | ADR-0001/0002/0003/0004 |
| AI-Orchestrierung: Modell-Routing/Token/Tracking/ROI über geschichtete Config (I-6.6) | `adr/0008-ai-orchestration-routing-tokens-tracking-roi-config.md` → `research/I6-6/T5-config-architecture.md` | ADR-0001/0002/0003/0004 |
| Wirkungs-Loop verstehen: Action → KPI-Delta → Attribution (I-8, Discovery) | `adr/0009-wirkungs-loop-action-kpi-attribution.md` → `../../core/action_codes/` | ADR-0001/0002/0003/0004 |
| KPI-Formel-DSL + DAX-Synthese verstehen (I-10.0, Rechenfähigkeit statt BLANK()) | `adr/0010-kpi-calculation-dsl-and-dax-synthesis.md` → `../../tooling/superversion/targets/dax_synth.py` | ADR-0001/0002/0003/0004 |
| KPI-Formel-DSL-Grammatik-Erweiterung verstehen (13-KPI-Closure: mul/delta_chain/distinctcount/count_threshold/round/sumx_over_key/avgx_over_key/pvm_*, rekursiver calc_ref) | `adr/0011-kpi-calculation-dsl-grammar-extension.md` → `../../tooling/superversion/targets/dax_synth.py` | ADR-0010 |
| KPI-Formel-DSL → SQL-Synthese verstehen (Databricks Metric Views + OSI DATABRICKS-Dialekt, `sql_synth.py`) | `adr/0012-kpi-calculation-dsl-sql-synthesis.md` → `../../tooling/superversion/targets/sql_synth.py` | ADR-0010/0011 |
| KPI-Formel-DSL: restliche 11 UCs verstehen (Full-Catalog-Closure, add/abs/avg_filtered/not_blank, alle 16 UCs) | `adr/0013-kpi-calculation-dsl-remaining-11-use-cases.md` → `../../tooling/superversion/targets/dax_synth.py` | ADR-0010/0011/0012 |
| I-6.6 Modell-Routing/Token/ROI scopen (Research-Charter, LLM-/kundenagnostisch) | `studio-model-routing-research-charter.md` | ADRs (vor Synthese in ADR-0008) |
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
| `adr/0006-superversion-target-adapter-contract.md` | ADR: Superversion Target-(Stack-)Adapter-Vertrag (emit(canonical)→{Pfad:Inhalt}, Registry, render; Vertrag-only) (Accepted) | Stack-Target-Emit |
| `adr/0007-studio-generate-docks-onto-superversion-core.md` | ADR: Studio-Generate dockt auf die Python-Superversion (E-1 ratifiziert; TS-Adapter = Preview-only, Gate-Report sichtbar, ehrliche Degradation) (Accepted) | Studio-Generate-Naht / I-6.2-6.3 |
| `adr/0008-ai-orchestration-routing-tokens-tracking-roi-config.md` | ADR: AI-Orchestrierung — Modell-Routing (Fähigkeits-Rollen + Adapter-Naht), Token-Opt., lokal-first-Tracking, ROI, gesteuert über geschichtete L0/L1/L2-Config; LLM-/kundenagnostisch; Synthese der I-6.6-Research T1–T5 (Accepted) | I-6.6 / AI-Config-Architektur |
| `adr/0009-wirkungs-loop-action-kpi-attribution.md` | ADR: Wirkungs-Loop (Decision Intelligence) — Action → KPI-Snapshot-Delta → Attribution (before_after/diff_in_diff/holdout), Feedback als reviewbarer Vorschlag (kein Auto-Mutate); Discovery für I-8 auf Action-Code-/Eval-Primitiven (Accepted; I-8.2 `before_after` implementiert) | I-8 / Wirkungs-Loop |
| `adr/0010-kpi-calculation-dsl-and-dax-synthesis.md` | ADR: governte KPI-`technical.calculation`-DSL (sum/ratio/delta/delta_pct/rate/count/hitl) + deterministische DSL→DAX-Synthese (`from_aluca.py` resolvt, `../../tooling/superversion/targets/tmdl.py` + `../../tooling/superversion/targets/dax_synth.py` materialisieren); schließt Review-Befund A1 (BLANK()-Quote); Legacy-PS-Generator warn-deprecated (Accepted) | I-10.0 / Rechenfähigkeit |
| `adr/0011-kpi-calculation-dsl-grammar-extension.md` | ADR: Grammatik-Erweiterung (mul/delta_chain/distinctcount/count_threshold/round/sumx_over_key/avgx_over_key/pvm_volume_effect/pvm_price_effect) + rekursiver `calc_ref` — schließt die letzten 13 `hitl`-KPIs der 5 MVP-UCs (0 verbleibende Gaps); inkl. Lineage-Korrekturen (dim_customer→fact_customer_events, fact_plan_sales→fact_sales, u.a.) (Accepted) | I-10.0-Folgeauftrag / 13-KPI-Closure |
| `adr/0012-kpi-calculation-dsl-sql-synthesis.md` | ADR: sql_synth.py (Databricks-SQL-Pendant zu dax_synth.py) — 11 von 16 Ops synthetisieren echtes SQL (TRY_DIVIDE, MEASURE(), CASE WHEN-Filter); 4 Ops (sumx_over_key/avgx_over_key/pvm_volume_effect/pvm_price_effect) explizit HITL (kein flaches Metric-View-expr-SQL-Shape); verdrahtet in databricks.py (NULL-Placeholder + comment: HITL:) und osi.py (zusätzlicher DATABRICKS-Dialekt neben MDX) (Accepted) | I-10.0-Folgeauftrag / DSL→SQL |
| `adr/0013-kpi-calculation-dsl-remaining-11-use-cases.md` | ADR: schließt die restlichen 11 UCs (COM-004, OPS-001/002/003, FIN-001, SCM-001/003, XD-001/002/003/004) — 4 neue Grammatik-Ergänzungen (add/abs/avg_filtered/not_blank-Filter); 9 eindeutige, individuell begründete `hitl`-KPIs bleiben über alle 16 UCs (4× Legacy-BLANK()-Placeholder, 2× Grammatik-Limit, 3× Neuland/unterspezifiziert); inkl. Lineage-/Business-Doku-Korrekturen und Paritätstest-Normalizer-Fix (Accepted) | I-10.0-Folgeauftrag / Full-Catalog-Closure |
| `migration-ingest-adapter.md` | Hub-and-Spoke N-zu-M-Migration (Sketch) | Migration entwerfen |
| `prior-art-agentic-integration-and-migration.md` | Recherche + Quellen zu Agentic-Integration & Migration | Belege/Hintergrund |
| `quality-tooling-map.md` | Welches Tooling welche Qualitäts-/Validierungsaufgabe abdeckt | Tooling-Übersicht |
| `reference_graph.md` | Repo-Referenzgraph / Abhängigkeiten | Abhängigkeiten |
| `skills-retire-vs-keep.md` | Skill-Docs: KEEP (Governance) vs. THIN (Mechanik → Upstream) (ADR-0002) | Skill-Scope entscheiden |
| `studio-capability-inventory.md` | I-6.1 Studio-Inventur + Soll-Schnitt; legt Generate-Naht-Entscheidung (E-1) für I-6.2/6.3 offen | Studio-/I-6-Scoping |
| `studio-model-routing-research-charter.md` | I-6.6 Research-Charter (Proposed): Fragen/Quellen/Erfolgskriterien für Modell-Routing, Token-Opt., Tracking, ROI; LLM-/kundenagnostisch; geschichtete Config L0/L1/L2 → ADR-0008 | I-6.6-Scoping |
| `research/I6-6/T1-routing.md` | I-6.6 Research (Draft): Per-Task-Modell-Routing (Multi-Provider) — Strategien, Task-Klasse→Rolle-Matrix, L0-Routing/Kaskade, agnostische Naht | ADR-0008-Synthese (Routing) |
| `research/I6-6/T2-token-optimization.md` | I-6.6 Research (Draft): Token-Optimierung — Caching/Batch/structured output, Provider-Divergenzen, L0/L1-Empfehlung | ADR-0008-Synthese (Token) |
| `research/I6-6/T3-tracking-observability.md` | I-6.6 Research (Draft): Token-/Kosten-Tracking — `llm_step_events`-Schema (lokal-first SQLite), OTel-GenAI-Mapping, Attribution | ADR-0008-Synthese (Tracking) |
| `research/I6-6/T4-roi.md` | I-6.6 Research (Draft): ROI-Methodik (Kosten vs. Wert-Proxys: Zeit, Gate, KPI, Time-to-Market) als L2, Ehrlichkeitsregeln, T3-Plug-in | ADR-0008-Synthese (ROI) |
| `research/I6-6/T5-config-architecture.md` | I-6.6 Research (Draft): geschichtete Config L0/L1/L2, Merge-Semantik (override/clamp/intersect/sticky), Schema-Skelett, Governance-Anschluss | ADR-0008-Synthese (Config) |

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
| A-9 | Superversion Target-(Stack-)Adapter-Vertrag ratifizieren (UMSETZUNGSPLAN I-3.1 [QA/SA]) | **erledigt** (ADR-0006): `emit(canonical)→{Pfad:Inhalt}` + Registry + `render`-Dispatch in `tooling/superversion/targets/base.py`, feldgleich zu Meridian (ADR-0036), Vertrag-only (Registry leer; Adapter folgen I-3.2/3.3) | 2026-06-23 |
| A-10 | Studio-Inventur I-6.1 (`studio-capability-inventory.md`) | **erledigt** (Agent-Inventur): Studio real; 4 Soll-Bereiche EXISTS, aber Generate läuft über TS-Shadow-Pfad statt Python-Core | 2026-06-24 |
| **E-1** | Generate-Naht entscheiden (I-6.2/6.3-Blocker): Studio-Generate auf Python-Core andocken vs. TS-Pfad behalten | **erledigt** (ADR-0007): **andocken** — Studio ruft `from_aluca`→`targets.render`→Gate (I-3.4/I-3.5) über dünne Brücke; TS-Adapter = Preview-only/nicht-autoritativ; Gate-Report sichtbar; ehrliche Degradation offline | 2026-06-24 |
| A-11 | I-6.6 Modell-Routing/Token/ROI: Research-Charter erstellen (vor teuren Läufen) | **erledigt** (`studio-model-routing-research-charter.md`, Proposed): Multi-Provider, LLM-/kundenagnostisch, T1–T5 mit Quellen/Erfolgskriterien, geschichtete Config L0/L1/L2 → ADR-0008 | 2026-06-24 |
| **E-2** | Research-Charter I-6.6 freigeben + Läufe starten | **erledigt** (freigegeben, alle 5 parallel): fünf grounded Research-Drafts T1–T5 (Verzeichnis `research/I6-6/`, Quellen + Abrufdatum 2026-06-24; Ehrlichkeits-Flags: Google/OpenAI-Pricing 403 → unverified-official, Claude-Pricing verifiziert) | 2026-06-24 |
| **E-3** | I-6.6 Synthese: ADR-0008 aus den 5 Research-Drafts | **erledigt** (ADR-0008, Proposed): geschichtete L0/L1/L2-Config als alleinige Steuerung; Routing über Fähigkeits-Rollen + Adapter-Naht (kein Modell-ID im Core); Caching-L0/Batch-L1; lokal-first `llm_step_events`; ROI=(V−C)/C mit L2-Wert-Proxys + Ehrlichkeitsregeln; Preise=versionierte Config (Google/OpenAI unverifiziert); 3 offene Punkte aufgelöst (Schema-Pfad=`tooling/generator/schemas/`, `x-merge` in-Schema, neue Governance-Zeile) | 2026-06-24 |
| **E-4** | ADR-0008 ratifizieren (Accepted) + I-6.6 implementieren | **teil-erledigt** (ratifiziert; V1 **Schema+Resolver** ✅: `tooling/generator/schemas/ai_config.schema.json` + reiner `studio/src/lib/ai/config/resolve.ts` + Property-Tests der Tighten-Invariante + Schema↔MERGE_SPEC-Parität; V2 **orchestrator-Refactor** ✅: `studio/src/lib/ai/config/defaults.ts` L0 + Fähigkeits-Rolle→Modell-Map (einzige Modell-ID-Stelle), `studio/src/lib/ai/config/route-model.ts` `chooseModel`, `studio/src/lib/ai/orchestrator.ts` config-getrieben (keine `DEFAULT_MODELS`), Source-Scan-Test „kein Modell-ID im Core"; V3 **Telemetrie** ✅: `llm_step_events`-Tabelle (lokal-first, kein PII-Inhalt), versionierte Preistabelle `studio/src/lib/ai/pricing.ts` (Anthropic verifiziert, Google/OpenAI `verified:false`), `studio/src/lib/db/llm-events-repo.ts` (`recordLlmStep`/`summarizeUsage`, missing≠zero), `studio/src/lib/ai/telemetry.ts` `recordAiStep`; V4 **ROI+Health** ✅: reines `studio/src/lib/ai/roi.ts` `computeRoi` (ROI = Netto durch Kosten; Wert-Proxys = L2-Daten, missing≠zero → UNCOMPUTED, Attribution-Default-Note, Cost-0-Guard), `studio/src/lib/ai/health.ts` `buildAiHealth` (Telemetrie-Summary + ROI + ehrliche Warnungen unvollständig/unverifiziert), Route `studio/src/app/api/ai-health/route.ts`; V5 **L1/L2 + Governance** ✅: Tabelle `ai_config_layers`, `studio/src/lib/db/ai-config-repo.ts` (Ajv-Validierung gegen `ai_config.schema.json`, Lifecycle draft→review→approved + Zwei-Personen-Regel + Audit, nur `approved` wird ausgeliefert, Edit→reset-to-draft), Loader `studio/src/lib/ai/config/load-layers.ts`, `createServerModel(taskRole, {projectId,domainId})` zieht approved L1/L2 ein; E2E-Test: approved L1-Provider-Ban entfernt anthropic aus dem Routing). **ADR-0008-Stack komplett.** V6 **Call-Site-Verdrahtung + Doku-Fix** ✅: `resolveServerModel` (Modell + Choice), `extractUsage`/`safeRecordAiStep` (Telemetrie best-effort, bricht nie den Request); die AI-Routen (wizard: kind→task-role, chat: streamText `onFinish`, factsheet-draft: beide generateText-Calls) zeichnen jetzt echten Verbrauch auf; `studio/CLAUDE.md` Schema-Pfad auf `tooling/generator/schemas/` korrigiert. V7 **UI** ✅: Health-Dashboard (`studio/src/components/ai/ai-health-panel.tsx` + Seite `studio/src/app/(studio)/ai-health/page.tsx`) + **Config-Editor** (`studio/src/components/ai/ai-config-panel.tsx` + Seite `studio/src/app/(studio)/ai-config/page.tsx` + API `studio/src/app/api/ai-config/route.ts`; L1/L2-Editor mit Freigabe-Schleuse, Buttons via geteiltem `studio/src/lib/ai/config/governance-types.ts` `allowedActions`, Server erzwingt Ajv + Zwei-Personen-Regel). **I-6.6 inkl. UI komplett.** | 2026-06-25 |
| A-12 | I-8.1 Wirkungs-Loop Discovery/ADR ([QA/SA]) | **erledigt** (ADR-0009, Proposed): Loop-Modell ActionEvent→KPI-Snapshot(t0,t1)→Effekt-Delta→AttributionRecord→Refinement-Vorschlag; auf vorhandenen Action-Code-`outcome_kpis`/`impact_valuation` + Eval-`refcalc`-Snapshots + ADR-0008-Attributions-Enum; Honesty (UNCOMPUTED, Assoziation≠Kausalität, kein Auto-Mutate, Feedback via Freigabe-Schleuse) | 2026-06-25 |
| **E-5** | ADR-0009 ratifizieren (Accepted) + I-8.2/8.3 implementieren | **erledigt** (ratifiziert; I-8.2 ✅ `tooling/superversion/eval/wirkung.py` deterministisches `before_after`-Effekt-Tracking, Snapshots via `refcalc`, missing≠zero, Assoziation≠Kausalität; I-8.3 ✅ `tooling/superversion/eval/refinement.py` `derive_refinements` = reviewbare Vorschläge `pending_review`, **nie Auto-Mutate**, kein Vorschlag aus uncomputed/0-Baseline). **Stufe I-8 komplett.** Rest-offen für spätere Vertiefung: `diff_in_diff`/`holdout`-Kontroll-Segment + O-1..O-4 (Snapshot-Quelle/Wirkungsfenster/Speicher/Studio-Approval-Verdrahtung) | 2026-06-25 |
