---
last-reviewed: 2026-06-24
shelf-life-days: 90
---
# I-6.6 Research-Charter — Modell-Routing, Token-Optimierung, Tracking & ROI

> **Freigabe-Artefakt vor teuren Deep-Research-Läufen.** Definiert pro Thema die
> präzisen Forschungsfragen, Quellen-Grounding, Erfolgskriterien und das Zielartefakt.
> **Status: Proposed — wartet auf Maintainer-Freigabe.** Nach Freigabe folgt je Thema
> ein grounded Deep-Research-Lauf, dann Synthese in **ADR-0008** + ein
> Config-Schema. Kein Code in dieser Charter.

| Feld | Wert |
|---|---|
| Stand | 2026-06-24 |
| Initiative | I-6.6 (Modell-Routing + Token-Budget je Schritt als Health-Metrik) |
| Provider-Scope | **Multi-Provider** (Claude/Anthropic, Google, OpenAI) — entschieden 2026-06-24 |
| Vorgehen | **Charter zuerst** (dieses Dok), dann Deep-Research je Thema → ADR-0008 → Schema |
| Methode | Deep-Research-Harness (web-recherchiert, quellenzitiert, adversarisch geprüft) |

---

## 1. Kontext & Lücke (warum)

Die Studio-Produkt-KI wählt ihr Modell heute **hartcodiert** in
`studio/src/lib/ai/orchestrator.ts` (`DEFAULT_MODELS`: `gemini-2.0-flash`,
`claude-sonnet-4-20250514`, `gpt-4o`) — Provider-Priorität Google→Anthropic→OpenAI,
**keine** zentrale, deklarative „Doktrin + Routing + Budget"-Quelle. Die Agent-Ebene
hat ihr Pendant (`UMSETZUNGSPLAN §0.45`-Tabelle Haiku/Sonnet/Opus), die Produkt-KI nicht.

I-6.6 soll das schließen. Maintainer-Anforderung (2026-06-24):

1. **Geschichtete Config:** *generell-optimale* Bestandteile (gelten für **jeden** Kunden)
   getrennt von *kundenindividuellen* (Unternehmenslogik **je Domäne**).
2. **Per-Task-Modellwahl** für **maximale Qualität & Zuverlässigkeit bei minimalen Kosten**.
3. **Token-Optimierung, Tracking und ROI-Berechnung** als zentrale Punkte.
4. Für **jedes Thema Deep-Research** und ein **grounded** Vorgehen.

Repo-Anschlusspunkte, an denen die Ergebnisse andocken: `orchestrator.ts` (Modellwahl),
die Bridge/Gate (ADR-0007, `e2e_smoke`) als Qualitäts-/Zuverlässigkeits-Signal, die
Eval-Suite I-4 (Value-Gate/Refdata) als **Wert-Anker** für ROI, und das
Preflight/Health (I-6.5) als Ausgabeort der Health-Metrik.

## 1a. Regierendes Prinzip — LLM- & kundenagnostisch (Pflicht)

Maintainer-Vorgabe (2026-06-24): der Ansatz ist **LLM-agnostisch und kundenagnostisch** —
dieselbe Neutral-Core-Doktrin wie ADR-0005 (neutraler Core) und ADR-0006 (Adapter-Naht).
Konkret, bindend für alle Themen:

- **LLM-agnostisch:** Der Core kennt **keine** Provider/Modell-IDs. Routing referenziert
  Modelle über **Fähigkeits-/Rollen-Abstraktionen** (z. B. „fast-cheap", „strong-reasoning",
  „long-context") und eine **Provider-Adapter-Naht** (Pattern wie `targets/base.py`:
  Registry + Contract); ein neuer Provider/ein neues Modell ist ein Adapter-Eintrag, **keine**
  Core-Änderung. Die heutigen hartcodierten IDs in `orchestrator.ts` werden hinter diese Naht
  gezogen. Kein Lock-in: jede Task-Klasse muss von ≥2 Providern bedienbar sein.
- **Kundenagnostisch:** Der Core enthält **keine** kundenspezifische Logik. Kunden/Domänen
  existieren ausschließlich als **Daten** in den Override-Schichten L1/L2 (§4) — nie als
  Sonderfall im Code. Ein neuer Kunde = neue Config, **kein** Core-Diff.

Dieses Prinzip ist Akzeptanzkriterium: jede T1–T5-Empfehlung wird daran gemessen, ob sie den
Core LLM- und kundenneutral hält.

## 2. Scope & Nicht-Ziele

**In Scope:** Multi-Provider-Routing-Strategie; Token-Optimierungstechniken;
Kosten-/Token-Tracking-Architektur; ROI-Methodik; das geschichtete Config-Modell.

**Nicht-Ziele (bewusst):** Fine-Tuning/eigene Modelle; Echtzeit-Auto-Negotiation von
Provider-Preisen; eine Trainings-Pipeline; Multi-Tenant-Server-Betrieb (das ist Z4/I-9 —
die Charter berücksichtigt aber, dass die Config-Schichtung später dorthin skaliert).

## 3. Grounding-Standard (für ALLE Themen verbindlich)

1. **Primärquellen zuerst:** offizielle Provider-Docs (Modell-Lineup, Pricing,
   Prompt-Caching, Batch-API, Rate-Limits) schlagen Blogs/Dritte.
2. **Live verifizieren — Wissensstand-Caveat:** Modell-IDs/Preise/Limits ändern sich;
   jede zitierte Zahl trägt Quelle **und Abrufdatum**. Keine Preise/Benchmarks aus dem
   Gedächtnis.
3. **Adversarisch prüfen:** zentrale Claims (z. B. „Modell X ist für Task-Klasse Y
   zuverlässiger/günstiger") werden gegen mind. eine Gegenquelle geprüft; unbelegte
   Claims werden als solche markiert, nicht als Fakt geführt.
4. **Repo-grounded:** jede Empfehlung nennt den konkreten Andockpunkt im Repo
   (Datei/Schema/Task), nicht nur Theorie.
5. **Ehrlichkeit v3:** Unsicherheit/fehlende Daten offen ausweisen; keine Fake-Präzision.

## 4. Das geschichtete Config-Modell (T5 — Design-Leitplanke)

Drei Schichten, klare Präzedenz (spezifischer gewinnt), alles deklarativ + versionierbar:

| Schicht | Eigentümer | Inhalt | Beispiel |
|---|---|---|---|
| **L0 Universal-Optimal** | ALUCA (Produkt) | beste Default-Routing-Regeln je Task-Klasse, Token-Defaults, Eval-Schwellen | „Draft-Extraktion → günstiges schnelles Modell; Schema-kritische Synthese → starkes Modell" |
| **L1 Kunde** | Kunde | Budget-Caps, Provider-Präferenz/-Sperre (Compliance/Region), Risiko-Appetit | „kein US-Provider", „Monatsbudget X" |
| **L2 Domäne** | Kunde, je Domäne | domänenspezifische Unternehmenslogik/Qualitätsanforderung | „Finance-KPIs: höchste Zuverlässigkeitsstufe, Kosten zweitrangig" |

Präzedenz **L2 > L1 > L0**. Die Research liefert die *Inhalte* für L0 (universal-optimal)
und die *Achsen*, entlang derer L1/L2 überschreiben dürfen.

---

## 5. Themen-Charter (T1–T5)

### T1 — Per-Task-Modell-Routing (Multi-Provider)
- **Forschungsfragen:** Welche Routing-Strategien existieren (statische Regeln, Klassifikator-Router, Confidence-/Eskalations-Kaskaden, LLM-as-router)? Wie misst man „Qualität×Zuverlässigkeit" pro Task-Klasse provider-übergreifend? Wie bildet man Task-Klassen für ALUCA (KPI-Draft, Bracket-Synthese, Source-Discovery, Doku, Gate-Repair)? Wann lohnt Kaskade (billig→eskalieren) vs. direkte starke Wahl?
- **Quellen:** Anthropic/Google/OpenAI Modell- & Capability-Docs; Routing-Forschung (z. B. RouteLLM-/Cascade-Literatur); Provider-Eval-/Cookbook-Guidance. *(live zu verifizieren)*
- **Erfolgskriterien:** eine Task-Klassen-Matrix für ALUCA, die Klassen auf **Fähigkeits-Rollen** (nicht Modell-IDs) abbildet, mit je Rolle ≥2 provider-Kandidaten **plus Begründung + Quelle**; eine **Provider-Adapter-Naht** (Registry/Contract, Pattern `targets/base.py`), die `orchestrator.ts` ablöst; ein entscheidbares Routing-Verfahren (Regeln/Kaskade) als L0-Default; klare Eskalationskriterien. **Agnostik-Check:** kein Core-Pfad nennt eine Modell-ID.
- **Feeds:** ADR-0008 §Routing; Config-Schema `routing.taskClasses[]`.

### T2 — Token-Optimierung
- **Forschungsfragen:** Welche Techniken senken Tokens ohne Qualitätsverlust (Prompt-Caching, Kontext-Kompression/Trimming, Batch-API, structured/constrained output, Wiederverwendung von System-Prompts, Retrieval statt Vollkontext)? Welche sind provider-spezifisch (Caching-Semantik je Anbieter)? Mess- und Trade-off-bar?
- **Quellen:** Provider-Caching-/Batch-Docs; Context-Engineering-Praxis. *(live zu verifizieren)*
- **Erfolgskriterien:** priorisierte Technik-Liste mit erwartetem Einsparhebel, Qualitäts-Risiko und Andockpunkt in `orchestrator.ts`/`context-builder.ts`/`prompts/*`; was als L0-Default an, was optional.
- **Feeds:** ADR-0008 §Token; Schema `tokenPolicy`.

### T3 — Tracking / Observability
- **Forschungsfragen:** Wie trackt man Tokens/Kosten **je Schritt** und attribuiert sie auf Use-Case/Domäne/Kunde? Welche Standards/Tools (OpenTelemetry-GenAI-Semconv, LLM-Observability-Tooling) passen lokal-first (I-6.5) ohne Cloud-Zwang? Welches minimale Schema deckt Health-Metrik + spätere ROI ab?
- **Quellen:** OTel-GenAI-Semconv; etablierte LLM-Observability-Projekte; Provider-Usage-/Response-Metadaten. *(live zu verifizieren)*
- **Erfolgskriterien:** ein minimales, lokal-first Telemetrie-Schema (Felder je Schritt: Modell, Provider, Tokens in/out, Kosten, Latenz, Gate-Ergebnis, Use-Case/Domäne) + Persistenz-Ansatz (passt zu SQLite-Audit des Studio).
- **Feeds:** ADR-0008 §Tracking; Schema `telemetry`; Health-Ausgabe (I-6.5-Preflight/Health).

### T4 — ROI-Berechnung
- **Forschungsfragen:** Wie rechnet man LLM-Kosten gegen erzeugten **Wert** methodisch sauber? Welche Wert-Anker sind im Repo schon vorhanden (Eval-Suite I-4: zertifizierte KPI-Werte; Gate-Pass als Qualitätsproxy; eingesparte Builder-Zeit)? Wie vermeidet man Scheinpräzision (ehrliche Bandbreiten statt erfundener €-Zahlen)?
- **Quellen:** FinOps-for-AI / Kosten-Attributions-Praxis; Value-of-Analytics-Methodik; intern: Eval-Suite I-4, PRODUCT_PLAN-Wertannahmen. *(live + repo-grounded)*
- **Erfolgskriterien:** eine ROI-Formel/-Methodik mit **explizit benannten Inputs** (Kosten aus T3; Wert-Proxys aus I-4/Zeitersparnis) und Ehrlichkeits-Regeln (fehlende Werte → ausgewiesen, nicht geraten).
- **Feeds:** ADR-0008 §ROI; Schema `roi` (Wert-Annahmen je Domäne = L2).

### T5 — Config-Architektur (Design, geringe Research-Tiefe)
- **Forschungsfragen:** Bewährte Muster für geschichtete/überschreibbare Configs (Defaults→Override), Validierung, Versionierung, Governance (wer darf L1/L2 ändern → Anschluss an die Freigabe-Schleiße I-6.4)?
- **Erfolgskriterien:** das L0/L1/L2-Schema (Felder, Präzedenz, Validierung) + wie es zu `orchestrator.ts` und zur Freigabe-Schleiße passt.
- **Feeds:** ADR-0008 §Config; das Config-Schema selbst.

---

## 6. Sequenz & Abhängigkeiten

```
T5 (Schichtungs-Skelett, leicht) ─┐
T1 Routing ───────────────────────┼─▶ ADR-0008 (Synthese) ─▶ Config-Schema ─▶ I-6.6-Implementierung
T2 Token ─────────────────────────┤
T3 Tracking ──▶ T4 ROI ───────────┘   (T4 braucht T3-Kostenmodell als Input)
```
T3 ist Voraussetzung für T4 (ohne Kosten-Tracking kein ROI). T1/T2/T5 sind unabhängig.

## 7. Aufwand/Kosten (zur Freigabe-Skalierung)

| Thema | Research-Tiefe | grobe Größenordnung |
|---|---|---|
| T1 Routing | hoch | 1 voller Deep-Research-Lauf |
| T2 Token | mittel | 1 Lauf |
| T3 Tracking | mittel | 1 Lauf |
| T4 ROI | mittel-hoch | 1 Lauf (nach T3) |
| T5 Config | niedrig | Design, kein voller Lauf |

Empfehlung: nach Charter-Freigabe **T1 zuerst** (Kern), dann T2/T3 parallel, T4 nach T3,
T5 begleitend. Jeder Lauf endet als zitiertes Research-Doc unter `docs/architecture/`.

## 8. Deliverable-Kette
Charter (dies) → je Thema ein Research-Doc (grounded, zitiert) → **ADR-0008** (Synthese
+ Entscheidungen) → Config-Schema (`tooling/ai/schemas/` o. ä.) → I-6.6-Implementierung
(`orchestrator.ts` liest die geschichtete Config; Telemetrie + Health-Ausgabe).

## 9. Vor/innerhalb der Research zu klärende Punkte
- **P-1:** Schema-Heimat — neues JSON-Schema unter `tooling/ai/schemas/` (SSOT-Konvention des Studio) vs. separater Config-Ort? (Default-Annahme: `tooling/ai/schemas/`.)
- **P-2:** ROI-Wert-Anker — primär „eingesparte Builder-Zeit" oder „zertifizierter KPI-Wert (I-4)" oder beides? (Research T4 liefert Optionen; Entscheidung im ADR.)
- **P-3:** Provider-Compliance-Achsen für L1 (Region/Hosting-Sperren) — welche sind real gefordert (Anschluss an `compliance/`)?
