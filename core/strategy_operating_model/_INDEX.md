---
last-reviewed: 2026-09-25
shelf-life-days: 90
---
# strategy_operating_model — Zentraler Anlaufpunkt (_INDEX)

> Einstieg in `core/strategy_operating_model/` — das **WHY** (`company/`) und **HOW**
> (`operating_model/`) des Frameworks. Zuerst diese Datei lesen, dann gezielt zum Doc —
> nicht den ganzen Ordner. Inhalt ist Source-of-Truth für Strategie/Zielbild; nichts
> hier neu ableiten, was unten als kanonisch markiert ist.

## „Lies-wenn"-Routing (Token-Disziplin)

| Deine Aufgabe ist … | Lies | NICHT nötig |
|---|---|---|
| Strategische Richtung / Zielbild / Strategic KPIs verankern und priorisieren (Margin-/Cash-/Growth-First) | `company/company_strategy.md` → `company/strategy_patterns.md` | operating_model/* |
| Domänen-/Ownership-Grenzen klären, Verantwortlichkeiten (RACI) je Golden-Thread-Layer zuordnen | `company/domains.md` → `operating_model/ownership_raci_golden_thread.md` | reference/*, ux, lakehouse |
| Reporting-Output designen, UX-Layer umsetzen oder Verteilung an Zielgruppen/Entscheidungsebenen planen | `company/reporting_principles.md` (Prinzipien, 3-30-300) → `operating_model/ux_design_system.md` → `operating_model/distribution_architecture.md` | lakehouse, reference/* |
| Operating Model im Überblick verstehen, Golden Thread nachvollziehen oder einen Bruch diagnostizieren | `operating_model/operating_model_overview.md` → `operating_model/golden_thread_strategy_to_action.md` | reference/TMDL_*, lakehouse |
| Artefakt-Rollen / IDs / Kanten ändern — was muss stabil bleiben, wo liegt die SoT eines Begriffs | `operating_model/core_constitution.md` → `operating_model/reference/single_source_of_truth.md` | company/*, ux, distribution |
| Semantik-Modell strukturieren, Measures definieren/benennen/governen | `operating_model/semantic_layer.md` → `operating_model/measure_system.md` | company/*, distribution |
| Daten-Layer zuordnen (Silver-first, Silver/Gold-Abgrenzung) oder Lakehouse-Architektur entwerfen | `operating_model/data_layers_standard.md` → `operating_model/lakehouse_architecture.md` | ux, company/* |
| TMDL-Modelle autoren/reviewen | `operating_model/reference/TMDL_Allowed_Subset.md` (Team-Standard) → `operating_model/reference/TMDL_Official_Refs.md` (Microsoft-Canon) | company/*, distribution |
| Qualität/Trust sichern, Quality-Gates, Framework-Audit/Registry-Build verstehen | `operating_model/data_governance.md` (§7–§9) | ux, distribution |
| Adapter/Automation gegen das Framework bauen, Adapter/MCP onboarden oder absichern | `operating_model/reference/core_abi.md` → `operating_model/supply_chain_security.md` | company/*, ux |
| AI-first-Betrieb auslegen (Autopilot mit Human-Approval) oder Copilot-/Agent-Konsumierbarkeit sicherstellen | `operating_model/ai_first_operations.md` → `operating_model/ai_readiness.md` | reference/TMDL_*, lakehouse |
| Use Cases / Action Codes nach Entscheidungs-Intent (Steer/Diagnose/Allocate/Forecast/Intervene) taggen | `operating_model/decision_taxonomy.md` | lakehouse, reference/* |
| Reifegrad / Roadmap / Investment scopen oder Framework-Gesundheit (produktionsreif?) messen | `operating_model/maturity_model_action_ready_analytics.md` → `operating_model/framework_health_metrics.md` | company/*, reference/* |

Empfohlene Erstlese-Reihenfolge (aus dem Bereichs-README übernommen): `company/company_strategy.md`
→ `company/reporting_principles.md` → `operating_model/operating_model_overview.md`
→ `operating_model/golden_thread_strategy_to_action.md` → `operating_model/core_constitution.md`
→ `operating_model/reference/single_source_of_truth.md` → `operating_model/reference/core_abi.md`.

## Dokument-Register (vollständig — Drift-Gate erzwingt das)

> Gruppiertes Register: eine Zeile je Themengruppe (erste Spalte = Ordner + Thema),
> die Docs der Gruppe stehen mit vollem Pfad, Zweck und doc-spezifischem „lies wenn"
> in der zweiten Spalte. Die letzte Spalte sagt, wann die ganze Gruppe relevant ist.
> Für den Einstieg nach Aufgabe: „Lies-wenn"-Routing oben.

| Gruppe | Docs — Zweck (→ lies wenn) | Lies-wenn (Gruppe) |
|---|---|---|
| `company/` — WHY: Strategie & Zielbild (business-owned, tool-agnostisch) | `company/company_strategy.md` — Kanonische strategische Richtung: Strategic KPIs, Executive Key Questions, Alignment KPI→Use Case→Action (→ primärer Business-Einstieg; Zielbild/Strategie verstehen oder verankern)<br>`company/reporting_principles.md` — Bindende Reporting-DNA: Actionability, progressive Disclosure (3-30-300), kognitive Einfachheit (→ Reporting/Analytics-Outputs designen oder bewerten)<br>`company/strategy_patterns.md` — Wiederverwendbare Steuerungsmuster (Margin-/Cash-/Growth-First) → Strategic KPIs + Use-Case-Cluster (→ priorisieren, welche KPIs/Use Cases zuerst umgesetzt werden)<br>`company/domains.md` — Business-Domänen, Scope und Ownership-Grenzen der Analytics-Verantwortung (→ Domänenstruktur für Use Cases/KPIs/Data Contracts klären) | Es geht um das *Warum*: Strategie, Prioritäten, Reporting-Prinzipien oder Domänen — nicht um Implementierung |
| `operating_model/` — HOW: Rahmen & Stabilitätsvertrag | `operating_model/operating_model_overview.md` — Überblick: wie Strategie in governte Analytics + Action skaliert übersetzt wird (→ Gesamtbild des Operating Models brauchen)<br>`operating_model/golden_thread_strategy_to_action.md` — Kausale Kette Strategie→KPIs→Key Questions→Use Cases→Modell→Measures→Reports→Actions (→ Golden Thread nachvollziehen oder einen Bruch diagnostizieren)<br>`operating_model/core_constitution.md` — Stabilitätsvertrag: Artefakt-Rollen, erlaubte Verbindungen, Naming/ID-Invarianten (→ bevor du Rollen/IDs/Kanten änderst — was muss stabil bleiben)<br>`operating_model/ownership_raci_golden_thread.md` — RACI je Golden-Thread-Layer: wer ist accountable/responsible (→ Verantwortlichkeiten zuordnen) | Methodisches Rückgrat verstehen oder strukturelle Änderungen an Rollen, Kanten und Ownership planen |
| `operating_model/` — HOW: Semantik & Daten | `operating_model/semantic_layer.md` — Struktur der semantischen Schicht: skalierbar, wiederverwendbar, action-ready (→ Semantik-Modell strukturieren)<br>`operating_model/measure_system.md` — Measure-/KPI-Implementierung gegen semantischen Drift schützen (→ Measures definieren/benennen/governen)<br>`operating_model/data_layers_standard.md` — Standard-Datenlayer (Silver-first): was definiert vs. geliefert wird (→ Daten-Layer-Zuordnung oder Silver/Gold-Abgrenzung)<br>`operating_model/lakehouse_architecture.md` — Cloud-native, tool-agnostische Lakehouse-Struktur (Silver→Gold) (→ Speicher-/Layer-Architektur entwerfen) | Modell, Measures oder Datenfundament (Silver→Gold→Semantik) bauen oder ändern |
| `operating_model/` — HOW: Governance & Security | `operating_model/data_governance.md` — Governance: Artefakt-Design-Gesetze (§7), Framework-Audit/Registry-Engine (§8), Trust-Signale (§9) (→ Qualität/Trust sichern oder den Registry-Build verstehen)<br>`operating_model/supply_chain_security.md` — Mindest-Security/Supply-Chain-Anforderungen für Adapter/MCP (→ Adapter/MCP onboarden oder absichern) | Trust, Qualität, Audit oder Security-Anforderungen stehen im Vordergrund |
| `operating_model/` — HOW: Konsum (UX & Distribution) | `operating_model/ux_design_system.md` — Bindende UX-Standards (operationalisiert die reporting_principles) (→ UX-Layer umsetzen, nicht: Prinzipien neu definieren)<br>`operating_model/distribution_architecture.md` — Wie Outputs strukturiert, positioniert und konsumiert werden (→ Verteilung an Zielgruppen/Entscheidungsebenen planen) | Darstellung und Auslieferung von Analytics-Produkten an Nutzer gestalten |
| `operating_model/` — HOW: AI & Entscheidungslogik | `operating_model/ai_first_operations.md` — AI-first-Betrieb (Autopilot mit Human-Approval) (→ den AI-first-Betriebsmodus auslegen)<br>`operating_model/ai_readiness.md` — Artefakte für Copilots/Agenten interpretierbar/abrufbar/vertrauenswürdig machen (→ AI-/Copilot-Konsumierbarkeit sicherstellen)<br>`operating_model/decision_taxonomy.md` — Entscheidungstypen (wie Analytics Entscheidungen stützt) zum Taggen (→ Use Cases/Action Codes nach Intent klassifizieren) | AI-Autonomie-Grenzen, Maschinen-Konsum oder Entscheidungs-Intent klären |
| `operating_model/` — HOW: Reife & Framework-Gesundheit | `operating_model/maturity_model_action_ready_analytics.md` — Fünf Reifegrade action-ready Analytics; Sprache für „wo stehen wir" (→ Reifegrad/Roadmap/Investment scopen)<br>`operating_model/framework_health_metrics.md` — Messbare Health-Indikatoren: „Ist das Framework produktionsreif?" (→ Framework-Gesundheit messen) | Standort bestimmen, Roadmap begründen oder Produktionsreife belegen |
| `operating_model/reference/` — kanonische Referenzen | `operating_model/reference/single_source_of_truth.md` — Welches Artefakt ist kanonisch für welches Konzept (gegen Drift/Duplikate) (→ klären, wo die SoT für einen Begriff liegt)<br>`operating_model/reference/core_abi.md` — Stabiles, maschinen-konsumierbares Interface zwischen Artefakten/Adaptern (→ Adapter/Automation gegen das Framework bauen)<br>`operating_model/reference/TMDL_Allowed_Subset.md` — Minimales, konsistentes TMDL-Subset (Team-Standard, lint-/PR-fähig) (→ TMDL-Modelle autoren/reviewen)<br>`operating_model/reference/TMDL_Official_Refs.md` — Autoritative Microsoft-TMDL-Doku-Links (→ offizielle TMDL-Referenz brauchen) | Nachschlagen statt Lernen: SoT-Zuordnung, Maschinen-Interface oder TMDL-Regeln verbindlich prüfen |

## Offene Punkte (Ledger — hier abhaken)

| ID | Punkt | Status | Datum |
|---|---|---|---|
| — | — | — | — |
