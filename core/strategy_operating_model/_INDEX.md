---
last-reviewed: 2026-06-16
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
| Strategische Richtung / Zielbild / Strategic-KPIs verstehen | `company/company_strategy.md` | operating_model/* |
| Steuerungsmuster wählen (Margin-/Cash-/Growth-First) | `company/strategy_patterns.md` | reference/* |
| Reporting-Prinzipien / Design-DNA (3-30-300) | `company/reporting_principles.md` | lakehouse, distribution |
| Domänen-/Ownership-Struktur klären | `company/domains.md` | reference/* |
| Golden Thread Strategie→Action nachvollziehen | `operating_model/golden_thread_strategy_to_action.md` | company/* |
| Operating Model im Überblick (Rollen, Flüsse) | `operating_model/operating_model_overview.md` | reference/* |
| Stabile Artefakt-Rollen / IDs / erlaubte Kanten (Vertrag) | `operating_model/core_constitution.md` | ux, distribution |
| Semantik-/Measure-Standards, SSOT | `operating_model/semantic_layer.md`, `operating_model/measure_system.md`, `operating_model/reference/single_source_of_truth.md` | company/* |
| Daten-Layer (Silver-first) / Lakehouse | `operating_model/data_layers_standard.md`, `operating_model/lakehouse_architecture.md` | ux, company |
| Governance, Quality-Gates, Audit, Trust-Signale | `operating_model/data_governance.md` | ux, distribution |
| Ownership/RACI je Golden-Thread-Layer | `operating_model/ownership_raci_golden_thread.md` | reference/* |
| UX-/Distribution-Standards | `operating_model/ux_design_system.md`, `operating_model/distribution_architecture.md` | company/* |
| AI-first-Betrieb / AI-Readiness / Entscheidungstypen | `operating_model/ai_first_operations.md`, `operating_model/ai_readiness.md`, `operating_model/decision_taxonomy.md` | reference/* |
| Reife-Grad / Framework-Gesundheit bewerten | `operating_model/maturity_model_action_ready_analytics.md`, `operating_model/framework_health_metrics.md` | company/* |
| TMDL-Standard / Adapter-Security / Maschinen-Interface | `operating_model/reference/TMDL_Allowed_Subset.md`, `operating_model/supply_chain_security.md`, `operating_model/reference/core_abi.md` | company/* |

Empfohlene Erstlese-Reihenfolge (aus dem Bereichs-README übernommen): `company/company_strategy.md`
→ `company/reporting_principles.md` → `operating_model/operating_model_overview.md`
→ `operating_model/golden_thread_strategy_to_action.md` → `operating_model/core_constitution.md`
→ `operating_model/reference/single_source_of_truth.md` → `operating_model/reference/core_abi.md`.

## Dokument-Register (vollständig — Drift-Gate erzwingt das)

> Doc-Spalte = Dateiname; Ordner steht in der Abschnitts-Überschrift. Klickbare Pfade
> stehen im „Lies-wenn"-Routing oben.

### company/ — WHY (business-owned, tool-agnostisch)

| Doc | Zweck | Lies-wenn |
|---|---|---|
| `company_strategy.md` | Kanonische strategische Richtung: Strategic KPIs, Executive Key Questions, Alignment KPI→Use Case→Action | Primärer Business-Einstieg; Zielbild/Strategie verstehen oder verankern |
| `reporting_principles.md` | Bindende Reporting-DNA: Actionability, progressive Disclosure (3-30-300), kognitive Einfachheit | Reporting/Analytics-Outputs designen oder bewerten |
| `strategy_patterns.md` | Wiederverwendbare Steuerungsmuster (Margin-/Cash-/Growth-First) → Strategic KPIs + Use-Case-Cluster | Priorisieren, welche KPIs/Use Cases zuerst umgesetzt werden |
| `domains.md` | Business-Domänen, Scope und Ownership-Grenzen der Analytics-Verantwortung | Domänenstruktur für Use Cases/KPIs/Data Contracts klären |

### operating_model/ — HOW (methodisches Rückgrat, platform-agnostisch)

| Doc | Zweck | Lies-wenn |
|---|---|---|
| `operating_model_overview.md` | Überblick: wie Strategie in governte Analytics + Action skaliert übersetzt wird | Gesamtbild des Operating Models brauchen |
| `golden_thread_strategy_to_action.md` | Kausale Kette Strategie→KPIs→Key Questions→Use Cases→Modell→Measures→Reports→Actions | Den Golden Thread nachvollziehen oder einen Bruch diagnostizieren |
| `core_constitution.md` | Stabilitätsvertrag: Artefakt-Rollen, erlaubte Verbindungen, Naming/ID-Invarianten | Bevor du Rollen/IDs/Kanten änderst — was muss stabil bleiben |
| `data_governance.md` | Governance: Artefakt-Design-Gesetze (§7), Framework-Audit/Registry-Engine (§8), Trust-Signale (§9) | Qualität/Trust sichern oder den Registry-Build verstehen |
| `ownership_raci_golden_thread.md` | RACI je Golden-Thread-Layer: wer ist accountable/responsible | Verantwortlichkeiten zuordnen |
| `semantic_layer.md` | Struktur der semantischen Schicht: skalierbar, wiederverwendbar, action-ready | Semantik-Modell strukturieren |
| `measure_system.md` | Measure-/KPI-Implementierung gegen semantischen Drift schützen | Measures definieren/benennen/governen |
| `data_layers_standard.md` | Standard-Datenlayer (Silver-first): was definiert vs. geliefert wird | Daten-Layer-Zuordnung oder Silver/Gold-Abgrenzung |
| `lakehouse_architecture.md` | Cloud-native, tool-agnostische Lakehouse-Struktur (Silver→Gold) | Speicher-/Layer-Architektur entwerfen |
| `ux_design_system.md` | Bindende UX-Standards (operationalisiert die reporting_principles) | UX-Layer umsetzen (nicht: Prinzipien neu definieren) |
| `distribution_architecture.md` | Wie Outputs strukturiert, positioniert und konsumiert werden | Verteilung an Zielgruppen/Entscheidungsebenen planen |
| `decision_taxonomy.md` | Entscheidungstypen (wie Analytics Entscheidungen stützt) zum Taggen | Use Cases/Action Codes nach Intent klassifizieren |
| `ai_first_operations.md` | AI-first-Betrieb (Autopilot mit Human-Approval) | Den AI-first-Betriebsmodus auslegen |
| `ai_readiness.md` | Artefakte für Copilots/Agenten interpretierbar/abrufbar/vertrauenswürdig machen | AI-/Copilot-Konsumierbarkeit sicherstellen |
| `maturity_model_action_ready_analytics.md` | Fünf Reifegrade action-ready Analytics; Sprache für „wo stehen wir" | Reifegrad/Roadmap/Investment scopen |
| `framework_health_metrics.md` | Messbare Health-Indikatoren: „Ist das Framework produktionsreif?" | Framework-Gesundheit messen |
| `supply_chain_security.md` | Mindest-Security/Supply-Chain-Anforderungen für Adapter/MCP | Adapter/MCP onboarden oder absichern |

### operating_model/reference/ — kanonische Referenzen

| Doc | Zweck | Lies-wenn |
|---|---|---|
| `single_source_of_truth.md` | Welches Artefakt ist kanonisch für welches Konzept (gegen Drift/Duplikate) | Klären, wo die SoT für einen Begriff liegt |
| `core_abi.md` | Stabiles, maschinen-konsumierbares Interface zwischen Artefakten/Adaptern | Adapter/Automation gegen das Framework bauen |
| `TMDL_Allowed_Subset.md` | Minimales, konsistentes TMDL-Subset (Team-Standard, lint-/PR-fähig) | TMDL-Modelle autoren/reviewen |
| `TMDL_Official_Refs.md` | Autoritative Microsoft-TMDL-Doku-Links | Offizielle TMDL-Referenz brauchen |

## Offene Punkte (Ledger — hier abhaken)

| ID | Punkt | Status | Datum |
|---|---|---|---|
| — | — | — | — |
