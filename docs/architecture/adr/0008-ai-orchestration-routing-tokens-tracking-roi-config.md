# ADR 0008 — AI-Orchestrierung: Modell-Routing, Token-Optimierung, Tracking, ROI über eine geschichtete Config

- **Status:** Proposed (zur Ratifikation)
- **Date:** 2026-06-24
- **Scope:** Wie die **Studio-Produkt-KI** ihr Modell je Task wählt, Tokens optimiert, Verbrauch/Kosten trackt und ROI ausweist — gesteuert durch **eine geschichtete, LLM- und kundenagnostische Config**. Synthetisiert die fünf I-6.6-Research-Drafts (`../research/I6-6/T1…T5`) in Entscheidungen. Ratifiziert die **Architektur + Schema-Form**; die konkrete Implementierung ist I-6.6-Folgearbeit.
- **Supersedes:** —
- **Related:** [`../studio-model-routing-research-charter.md`](../studio-model-routing-research-charter.md) (I-6.6 Charter), [`0005-superversion-home-and-meridian-vendoring.md`](0005-superversion-home-and-meridian-vendoring.md) (neutraler Core), [`0006-superversion-target-adapter-contract.md`](0006-superversion-target-adapter-contract.md) (Adapter-Naht-Pattern), [`0007-studio-generate-docks-onto-superversion-core.md`](0007-studio-generate-docks-onto-superversion-core.md), Research: [`../research/I6-6/T1-routing.md`](../research/I6-6/T1-routing.md), [`T2`](../research/I6-6/T2-token-optimization.md), [`T3`](../research/I6-6/T3-tracking-observability.md), [`T4`](../research/I6-6/T4-roi.md), [`T5`](../research/I6-6/T5-config-architecture.md)

---

## Context

Die Studio-Produkt-KI wählt ihr Modell heute hartcodiert (`studio/src/lib/ai/orchestrator.ts`:
`DEFAULT_MODELS` + feste Provider-Priorität Google→Anthropic→OpenAI). Das koppelt *generell-optimale*
Engineering-Entscheidungen an *kundenindividuelle* (Budget, Provider-Sperren, Domänen-Qualität) und
verletzt — anders als die Agent-Ebene mit `UMSETZUNGSPLAN §0.45` — das Neutral-Core-Prinzip.

Maintainer-Vorgabe (I-6.6): **LLM- und kundenagnostisch**, geschichtete Config (universal vs.
kundenindividuell je Domäne), **Per-Task-Modellwahl für max. Qualität/Zuverlässigkeit bei min.
Kosten**, mit **Token-Optimierung, Tracking und ROI** als zentralen Punkten. Fünf grounded
Research-Drafts (T1–T5, Multi-Provider Claude/Google/OpenAI, Quellen + Abrufdatum 2026-06-24) liefern
die Grundlage; dieses ADR entscheidet daraus.

## Decision

**Adoptiere eine geschichtete, deterministisch aufgelöste Config (L0/L1/L2) als alleinige Quelle für
Modellwahl, Token-Politik, Eval-Schwellen, Telemetrie und ROI-Gewichte. `orchestrator.ts` liest nur
die *aufgelöste* effektive Config und kennt **keine** Provider-/Modell-IDs. Verbrauch wird lokal-first
je Schritt getrackt; ROI wird ehrlich aus getrackten Kosten und kundendefinierten Wert-Proxys
berechnet.**

Neun Festlegungen:

1. **Geschichtete Config L0/L1/L2 (aus T5).** L0 universal-optimal (ALUCA, versioniert, read-only für
   Kunden) · L1 Kunde · L2 Domäne. **Präzedenz L2 > L1 > L0.** Auflösung ist eine **reine, deterministische**
   Funktion `resolveAiConfig(layers, ctx)` (kein I/O/Clock/RNG; Laden getrennt vom Auflösen).

2. **Merge-Semantik = Sicherheits-Invariante (aus T5).** Pro Feld ein Merge-Kind: `override` (nur für
   Felder ohne Sicherheits-Dimension), `clamp` (restriktiverer Wert gewinnt — Budgets/Token/Eval),
   `intersect` (Provider-Allow-List verengt sich nach unten), `true-sticky`/OR (PII-Redaction,
   Human-Review). **Regierende Regel: Kunde/Domäne kann L0 nur *verschärfen*, nie *lockern*.** Maschinell
   geprüft (Property-Tests: effektives Budget ≤ L0; effektive Provider ⊆ L0).

3. **Routing über Fähigkeits-Rollen + Adapter-Naht (aus T1).** Task-Klassen (KPI-Draft-Extraktion,
   Bracket-Synthese, Source-Discovery, Doku, Gate-Repair, …) mappen auf **abstrakte Fähigkeits-Rollen**
   (`fast-cheap` · `balanced` · `deep-reasoner` · `long-context`). Eine **Provider-Adapter-Registry/Contract**
   (Pattern wie ADR-0006 `targets/base.py`) löst Rolle×Provider auf. Die **Fähigkeits-Rolle→konkretes-Modell-Map
   ist die EINZIGE Stelle, an der ein Modell-ID-Literal vorkommt** — sie lebt in L0 (von ALUCA versioniert).
   Jede Rolle muss von **≥2 Providern** bedienbar sein (kein Lock-in).

4. **Quality×Reliability + Eskalation (aus T1).** Der primäre Qualitätsschätzer ist ALUCAs **deterministisches
   Gate** (Golden-Thread I-3.4 + E2E-Smoke I-3.5 + Value-/Comp-Gate I-4) — provider-blind. Default-Routing =
   Regel je Rolle; optionale **Kaskade** (günstig→eskalieren) nur wo der erwartete Kostenvorteil die
   Eskalationswahrscheinlichkeit überwiegt. LLM-as-judge nur als Tie-Breaker (mit dokumentiertem
   Zuverlässigkeits-Caveat).

5. **Token-Optimierung (aus T2).** **Prompt-Caching ist der primäre, qualitätsneutrale L0-Hebel** (ALUCA
   ist system-prompt-/JSON-lastig); Provider-Caching-Divergenzen (Anthropic Write-Premium + Breakpoints
   vs. Auto-Caching OpenAI/Gemini) werden **hinter der Adapter-Naht** abstrahiert. Structured Output = L0.
   **Batch (−50%, async)** = L1-Opt-in. JIT-Retrieval = L1/L2 hinter einem Recall-Gate (nicht qualitätsneutral).

6. **Tracking lokal-first (aus T3).** Eine **einzelne `llm_step_events`-Tabelle** in der bestehenden
   Studio-SQLite (`studio/data/studio.db`), kein Cloud-Zwang. Token-Counts kommen aus dem schon
   provider-normalisierten `result.usage` des Vercel-AI-SDK; **Rohwerte (`raw_usage_json`) mitschreiben**
   (bekannte Mapping-Ungenauigkeiten). **OTel-GenAI definiert keine Kostenmetrik** → Kosten werden lokal
   gerechnet. L0-Pflichtfelder: Tokens in/out, Latenz, Fehler, Attribution (`project_id`/`use_case_id`/`domain`);
   optionaler OTel-Export-Seam. Prompt-/Response-*Inhalt* nicht (PII).

7. **ROI ehrlich (aus T4).** `ROI = (V − C) / C` mit `C = C_llm + C_human + C_platform` (objektiv, aus T3:
   Tokens × **versionierter Preistabelle**) und `V = Attribution × (Zeit + Qualität + KPI + Time-to-Market)`
   — **alle Wert-Proxys sind L2-Daten je Kunde/Domäne, nie hartcodiert.** Ehrlichkeitsregeln: **missing ≠ zero**
   (UNCOMPUTED ausweisen wie die Eval-Suite), kalibrierte Bandbreiten statt Scheinpräzision, kein
   No-Double-Counting über die Proxys.

8. **Preise sind versionierte Config-Daten, nicht Code.** Die Fähigkeits-Rolle→Modell-Map **und** die
   Preistabelle leben als versionierte L0-Daten und werden **out-of-band gepflegt + live verifiziert**.
   Forschungs-Caveat ist bindend: **Google/OpenAI-Preise sind unverifiziert (HTTP 403, T1/T2/T4)** und vor
   produktiver Bindung live zu bestätigen; Anthropic/Claude-Preise wurden verifiziert. Kein Preis-Literal im Core.

9. **Governance + Agnostik-Invarianten.** L1/L2-Änderungen laufen durch die **bestehende Freigabe-Schleuse**
   (`approval-workflow.ts`: draft→review→approved, Zwei-Personen-Regel, Append-only-Audit); der Audit-Eintrag
   hält authored `schema_version` + effektiven Config-Hash. **Akzeptanzkriterien:** (a) kein Core-Pfad nennt
   eine Modell-ID außer der L0-Map; (b) Kunden/Domänen existieren nur als Daten in L1/L2, nie als Code-Sonderfall;
   (c) jede Rolle ≥2 Provider.

### Aufgelöste offene Punkte (aus den Research-Drafts)

- **Schema-Heimat (T5-Flag):** Der in `studio/CLAUDE.md` deklarierte Pfad `tooling/ai/schemas/` **existiert
  physisch nicht** — die realen Schemas liegen in `tooling/generator/schemas/`. **Entscheidung:**
  `ai_config.schema.json` unter das **bestehende `tooling/generator/schemas/`** (Realität vor Doku), Hausstil
  (draft-07, `additionalProperties:false`, `schema_version` const, `owner_role`/`steward_role`), Typen via
  `npm run generate:types`. `studio/CLAUDE.md` ist in der Implementierung anzugleichen (Doku-Drift).
- **`x-merge`-Annotation in-Schema vs. Resolver-Tabelle (T5):** **Entscheidung:** Merge-Kind als `x-merge`
  im Schema (eine SSOT; Validatoren ignorieren unbekannte Keywords); Resolver liest es.
- **Config-Change-Governance-Tabelle (T5):** neue Lifecycle-Zeile, die dieselbe `transition()`-Maschine
  wiederverwendet (nicht `bracket_lifecycle` überladen) — DB-Detail der Implementierung.

## What this ratifies vs. defers

- **Ratifiziert:** die Architektur (geschichtete Config als alleinige Steuerung), die Merge-Sicherheits-Invariante,
  die agnostische Routing-Naht (Fähigkeits-Rollen + Adapter), lokal-first-Tracking, die ROI-Methodik mit
  Ehrlichkeitsregeln, Preise-als-Config, Governance über die Freigabe-Schleuse, die Agnostik-Akzeptanzkriterien,
  und die drei aufgelösten offenen Punkte oben.
- **Aufgeschoben (I-6.6-Implementierung, eigene Tasks):** das konkrete `ai_config.schema.json` + generierte
  Typen; `resolveAiConfig` + Loader; das `orchestrator.ts`-Refactor (DEFAULT_MODELS → Config); die
  `llm_step_events`-Tabelle + Erfassung am Call-Site; die ROI-Berechnung + Health-Ausgabe (an I-6.5-Preflight/Health);
  die finale Feld-Taxonomie (T5 §4 ist Form-Vertrag, nicht endgültige Feldliste); der L0-Release-/Migrations-Runbook.

## Consequences

**Positiv**
- Eine Wahrheit für Modellwahl/Politik; die hartcodierten IDs verschwinden hinter die Naht — neuer Provider/Modell
  = L0-Daten-Release, kein Core-Diff. Konsistent mit ADR-0005/0006 (Neutral-Core).
- „Kunde kann nur verschärfen" ist eine *maschinell geprüfte* Invariante, kein bloßer Default — Compliance-Sperren
  sind nicht untergrabbar.
- Kosten/ROI werden je Schritt sichtbar und kundenehrlich (missing≠zero), lokal-first ohne Cloud-Zwang.

**Negativ / Kosten**
- Mehr bewegliche Teile (Schema, Resolver, Telemetrie-Tabelle, Preistabelle-Pflege) als der Status quo.
- Preis-/Modell-Daten müssen **gepflegt + live verifiziert** werden; veraltete Preise verfälschen ROI. Die
  Unverifiziert-Flags (Google/OpenAI) sind eine offene Bringschuld vor produktiver Bindung.
- Schema-Pfad-Drift (`studio/CLAUDE.md` vs. Realität) muss in der Implementierung bereinigt werden.

**Neutral**
- ROI bleibt bewusst proxy-basiert mit Bandbreiten; keine erfundenen €-Zahlen — Genauigkeit wächst mit besseren
  L2-Eingaben des Kunden.

## Alternatives considered

- **Hardcodierte Modelle behalten (Status quo).** Verworfen: koppelt universal an kundenindividuell, bricht das
  Agnostik-Prinzip, blockiert kundenseitige Compliance-Sperren.
- **Externe LLM-Observability-SaaS (Langfuse/Helicone/Phoenix) als Pflicht (T3).** Verworfen als *Pflicht*:
  verletzt lokal-first/BYO-Key (separater Dienst/Infra). Optionaler OTel-Export bleibt als Seam.
- **Provider-Lock-in auf einen Anbieter.** Verworfen: widerspricht Multi-Provider-Scope + „≥2 Provider je Rolle";
  verschenkt Kosten-/Qualitäts-Optimierung.
- **Merge-Semantik im Resolver-Code statt im Schema.** Verworfen zugunsten `x-merge` (eine SSOT, Präzedenz ist Daten).

## References

- Intern: die fünf Research-Drafts unter [`../research/I6-6/`](../research/I6-6/) (T1–T5, Quellen + Abrufdatum
  2026-06-24, mit Ehrlichkeits-Flags); [`../studio-model-routing-research-charter.md`](../studio-model-routing-research-charter.md);
  ADR-0005/0006/0007; `studio/src/lib/ai/orchestrator.ts`; `studio/src/lib/governance/approval-workflow.ts`;
  `tooling/generator/schemas/` (Hausstil); `UMSETZUNGSPLAN_SUPERVERSION.md` (I-6.6).
- Extern (in den Research-Drafts zitiert, mit Abrufdatum): Provider-Docs (Anthropic/Google/OpenAI, teils 403 →
  unverifiziert geflaggt), OTel-GenAI-Semconv, RouteLLM/FrugalGPT (Cascade-Routing), FinOps-for-AI, JSON-Schema-
  Versionierung.
