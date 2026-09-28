---
last-reviewed: 2026-09-26
shelf-life-days: 90
---
# Studio-KI: Maßnahmenentwurf für C-21, C-22 und C-23

> **Status: Entwurf vom 26.09.2026, ohne Legal-/DSB-Sign-off. Keine Rechtsberatung.**
> Dieses Dokument beschreibt, was vor einer Öffnung des KI-Egress in Studio technisch, vertraglich
> und organisatorisch umzusetzen und nachzuweisen ist. Es ändert keinen Code. Die Ledger-Punkte
> C-21 bis C-23 in [`_INDEX.md`](_INDEX.md) bleiben **offen**, bis die Umsetzung mit Tests belegt
> und von Legal/DSB abgenommen ist.

## 0. Geltung, Legende und Ausgangslage

- **Code-Stand:** `origin/main` am 26.09.2026 (Merge von PR #479; die AI data handling policy aus
  PR #478 ist darin enthalten). Alle Pfade sind relativ zur Repo-Wurzel.
- **Legende:** [Code] = im Quelltext belegt · [Quelle] = Primärquelle mit Abrufdatum ·
  [Vorschlag] = Entwurf dieses Dokuments · ⚠️ UNKLAR = nicht belastbar geprüft.
- **Rechtsstand:** Die am 25.09.2026 geprüften Daten zu DSGVO, AI Act (inkl. VO (EU) 2026/1744),
  DPF und SCC stehen in [`README.md`](README.md), Abschnitt „Rechtsstand-Abgleich“. Sie werden hier
  nicht wiederholt, nur ergänzt.
- **Ausgangslage [Code]:** Alle drei KI-Routen rufen vor der Modellauflösung
  `requireApprovedAiEgress()` auf (`studio/src/app/api/ai/chat/route.ts`,
  `studio/src/app/api/ai/wizard/route.ts`, `studio/src/app/api/ai/factsheet-draft/route.ts`).
  Das Gate setzt `approvalGranted: false` fest und antwortet mit 403 `AI_EGRESS_NOT_APPROVED`
  (`studio/src/lib/ai/egress-gate.ts`). Keine Route übergibt `projectId`, `profile` oder `context`;
  es greifen daher das Default-Profil (`provider: 'unresolved'`) und der Default-Kontext
  (`classification: 'unknown'`, `redacted: false`). Der Nachweis landet unter `project_id = 'default'`.
- **Folge:** Im Betrieb verlässt heute kein Inhalt Studio in Richtung LLM-Anbieter. Die drei Punkte
  beschreiben daher **Bedingungen für jede künftige Freischaltung** (C-21, C-23) sowie eine Lücke,
  die **schon heute** personenbezogene Daten betrifft (C-22).

### 0.1 Reihenfolge (Vorschlag)

1. **C-22 zuerst**, weil heute schon bei jedem blockierten KI-Aufruf eine E-Mail-Adresse gespeichert
   wird (Abschnitt 2).
2. **C-21 und C-23 parallel**, beide sind Voraussetzung für eine Öffnung. Das Gate darf erst dann
   von der Konstante `false` auf eine abgeleitete Freigabe umgestellt werden (C-23, M-23.7), wenn
   alle Abnahmekriterien in 1.5 und 3.5 grün sind.

---

## 1. C-21: EU-Verarbeitung, Training und Aufbewahrung beim Anbieter

### 1.1 Ist-Zustand (Code-Belege)

| Befund | Beleg |
|---|---|
| Die Residenz der Anbieter ist statisch `['any']` für `anthropic`, `google` und `openai` | `studio/src/lib/ai/config/defaults.ts` (`PROVIDER_RESIDENCY`) |
| Die Anbieter werden ohne `baseURL`, Region oder Standort gebaut: `createAnthropic({ apiKey })`, `createGoogleGenerativeAI({ apiKey })`, `createOpenAI({ apiKey })`. Es gelten die Standard-Endpunkte der SDKs | `studio/src/lib/ai/orchestrator.ts` (`createModel`) |
| `@ai-sdk/google` spricht die Gemini Developer API an, nicht Vertex AI. Ein Vertex- oder Bedrock-Provider ist nicht installiert | `studio/package.json` (`@ai-sdk/anthropic`, `@ai-sdk/google`, `@ai-sdk/openai`) |
| `dataResidency: 'eu-only'` lässt `chooseModel` keinen Anbieter finden; die KI bleibt aus (Fail-closed), statt EU-Verarbeitung zu ermöglichen | `studio/src/lib/ai/config/route-model.ts`, `studio/src/lib/ai/config/resolve.ts` (`clampStrictResidency`) |
| `provider_training_allowed: false` und `prompt_retention_days` sind Pflichtfelder, werden aber nur als Deklaration geprüft, nicht gegen Vertrag oder Laufzeit | `studio/src/lib/ai/data-handling-policy.ts`; `tooling/generator/schemas/ai_data_handling_policy.schema.json` |
| Die Projektroute verlangt `provider_region`, `provider_geography`, `credential_ref`, `provider_terms_evidence_refs`, `expires_at`. Das Review prüft nur, dass die Felder gefüllt sind | `tooling/generator/schemas/project_ai_data_handling.schema.json`; `studio/src/lib/ai/policy-review.ts` |
| Kein Abgleich zwischen der Region in der Route und dem Endpunkt, den der Orchestrator tatsächlich nutzt | `studio/src/lib/ai/orchestrator.ts` liest keine Route; `studio/docs/design/AI_POLICY_REVIEW.md` („not runtime proof of provider location“) |
| Die Modell-IDs für Google/OpenAI sind laut Kommentar nicht verifiziert (`gemini-2.0-flash`, `gpt-4o`, `gpt-4o-mini`) | `studio/src/lib/ai/config/defaults.ts` (`CAPABILITY_MODEL_MAP`) |

### 1.2 Anforderung und Rechtsgrundlage

- **Art. 28 Abs. 1 und 3 DSGVO:** Der Anbieter verarbeitet als (Unter-)Auftragsverarbeiter nur auf
  dokumentierte Weisung. Training mit Kundendaten und eine Aufbewahrung über die Weisung hinaus
  müssen vertraglich ausgeschlossen bzw. begrenzt sein (lit. a, g). Der Nachweis ist Vertragsinhalt,
  keine Konfigurationsbehauptung.
- **Art. 44 ff. DSGVO:** Jede Verarbeitung außerhalb des EWR, auch nur die Inferenz, ist eine
  Übermittlung. Grundlage: DPF-Zertifizierung des Empfängers (Angemessenheitsbeschluss
  (EU) 2023/1795) oder SCC nach (EU) 2021/914 mit Transfer Impact Assessment (siehe C-20).
- **Art. 5 Abs. 1 lit. c/e, Art. 25 DSGVO:** Datenminimierung und Speicherbegrenzung beim Anbieter;
  Voreinstellungen, die die Aufbewahrung minimieren (ZDR, kein `store`, kein Request-Logging).
- **Art. 5 Abs. 2, Art. 24 DSGVO:** Rechenschaftspflicht. Die Zusage muss belegbar sein
  (Vertrag, Datum, Version) und zur Laufzeit zum tatsächlich genutzten Endpunkt passen.
- **Art. 28 Abs. 2/4 DSGVO:** Der Anbieter gehört in die Subprozessorliste
  (`eu_hosting_guarantee.md` 3.4) mit Informationspflicht bei Änderung.

### 1.3 Was heute je Anbieter nachprüfbar ist (Stand 26.09.2026)

Nur Primärquellen des Anbieters; Abrufdatum 26.09.2026. Alle Angaben sind Angebotsbeschreibungen,
**kein** Nachweis für einen konkreten Vertrag. Der gilt erst, wenn er unterschrieben und als
`provider_terms_evidence_refs` im Project Package abgelegt ist.

| Anbieter / Weg | EU-Verarbeitung (Inferenz) | Speicherung „at rest“ | Training | Aufbewahrung / ZDR | Quelle |
|---|---|---|---|---|---|
| **Anthropic, Claude API (1st party)**, heute im Code | **Nein.** `inference_geo` kennt nur `"global"` (Standard) und `"us"`; `"us"` kostet 1,1× und gilt ab Claude 4.6 | Workspace geo: nur `"us"` | „Retained data is never used for model training without your express permission.“ | Standard: Löschung von Inputs/Outputs „within 30 days“; bei Richtlinienverstoß bis 2 Jahre (Inhalte) bzw. 7 Jahre (Klassifikations-Scores). ZDR nur per Vereinbarung mit Sales, je Organisation; Batch, Files, Code Execution u. a. sind nicht ZDR-fähig; auch mit ZDR Aufbewahrung „where required by law“ oder bei Trust-&-Safety-Flag möglich | [^a1] [^a2] [^a3] |
| **Claude über Google Cloud (Vertex AI)** | Laut Google-Tabelle Spalten „EU multi-region“, „europe-west1“, „europe-west4“ für Claude-Modelle; welches Modell in welcher Spalte verfügbar ist, ist grafisch markiert → ⚠️ UNKLAR je Modell | Region nach Kundenauswahl | Google: kein Training ohne Erlaubnis (Service Specific Terms, gilt für „all managed models“) | Abuse-Monitoring von Google betrifft laut Seite „Google models“; für Partner-Modelle ⚠️ UNKLAR | [^g1] [^g2] [^a1] |
| **Claude über Amazon Bedrock** | Laut Anthropic bestimmt die Endpoint-URL bzw. das Inference Profile die Region; EU-Details nicht geprüft → ⚠️ UNKLAR | ⚠️ UNKLAR | ⚠️ UNKLAR | ⚠️ UNKLAR | [^a1] |
| **Google, Gemini Developer API** (`@ai-sdk/google`), heute im Code | **Keine** Residenzzusage dokumentiert → ⚠️ UNKLAR, als „nicht EU“ zu behandeln | ⚠️ UNKLAR | Paid Services: „Google doesn't use your prompts … or responses to improve our products“. Für Nutzer im EWR/CH/UK gilt die Paid-Regel für alle Dienste | Prompts/Antworten werden „for a limited period of time“ für Missbrauchserkennung geloggt; Dauer ⚠️ UNKLAR. Kein ZDR-Angebot dokumentiert | [^g3] |
| **Google, Gemini auf Vertex AI** | **Ja**, mit regionalem Endpunkt: `eu`-Multiregion („strictly … within EU member states“, ohne UK/CH) oder z. B. `europe-west3`/`europe-west4`. Globale Endpunkte (`aiplatform.googleapis.com`) „don't provide any data residency guarantees“. `gemini-2.0-flash` steht **nicht** in der Tabelle (gelistet sind u. a. Gemini 2.5 und 3.x) | in der gewählten Region | „Google won't use your data to train or fine-tune any AI/ML models without your prior permission“ | ZDR erreichbar, wenn: Ausnahme vom Abuse-Monitoring-Logging beantragt, In-Memory-Caching (24 h TTL) auf Projektebene abgeschaltet, Request-Response-Logging aus, Interactions API mit `store = false`, keine Google-Search-Grounding (3 Tage Log) und kein Maps-Grounding (30 Tage) | [^g1] [^g2] |
| **OpenAI API** (`@ai-sdk/openai`), heute im Code | **Ja, nach Freigabe:** Region „Europe (EEA + Switzerland)“ mit Speicherung **und** Verarbeitung über `eu.api.openai.com`. Voraussetzung: Eignung über Sales, Region wird für **neue** Projekte gesetzt, für Nicht-US-Regionen „you must be approved for abuse monitoring controls“. Nicht alle Endpunkte/Modelle in der EU verfügbar | Region des Projekts | „data sent to the OpenAI API is not used to train or improve OpenAI models (unless you explicitly opt in)“ | Abuse-Monitoring-Logs „retained for up to 30 days“. ZDR / Modified Abuse Monitoring nur nach Freigabe; zustandsbehaftete Endpunkte (Conversations, Assistants, Threads, Vector Stores) speichern „until deleted“ | [^o1] [^o2] |

**Schlussfolgerung [Vorschlag]:**

- Mit dem **heutigen Code** ist keine EU-Verarbeitung erreichbar: Anthropic 1st party bietet keine
  EU-Inferenz, die Gemini Developer API keine dokumentierte Residenz, und OpenAI wird ohne
  EU-Endpunkt angesprochen.
- Belastbar EU-fähig sind nach heutigem Stand **Gemini auf Vertex AI (EU-Endpunkt)** und
  **OpenAI mit EU-Datenresidenz (`eu.api.openai.com`, freigegebenes Projekt)**. Claude über Vertex
  in EU-Regionen ist möglich, die Modellverfügbarkeit je Region ist aber vor einer Entscheidung am
  Stichtag zu prüfen.
- Auch bei EU-Verarbeitung bleibt ein **US-Mutterkonzern** Vertragspartner bzw. Unterauftragsverarbeiter.
  Fernzugriffe (Support, Abuse-Review) können Übermittlungen sein. Die Transfergrundlage (C-20)
  bleibt deshalb nötig; EU-Residenz ersetzt sie nicht.

### 1.4 Maßnahmen

**Vertrag und Organisation**

| ID | Maßnahme | Verantwortlich |
|---|---|---|
| M-21.1 | Je freizugebendem Anbieter: AVV/DPA abschließen, Unterauftragsverarbeiter-Liste des Anbieters einholen, Transfergrundlage festlegen (DPF-Zertifizierung am Stichtag prüfen und ablegen, SCC 2021/914 als Rückfallebene, vgl. C-20) | Legal |
| M-21.2 | Aufbewahrung beim Anbieter schriftlich fixieren: ZDR bzw. Modified Abuse Monitoring (OpenAI), ZDR-Vereinbarung (Anthropic), Abuse-Logging-Ausnahme plus Caching-Abschaltung (Vertex). Der vereinbarte Wert wird zu `prompt_retention_days` (0 nur mit ZDR-Nachweis; sonst der Vertragswert, z. B. 30) | Legal + Maintainer |
| M-21.3 | Nachweise versioniert ablegen: Vertrag/DPA, ZDR-Bestätigung, Regionseinstellung (Screenshot oder Admin-API-Auszug) mit Datum. Die Referenzen gehen in `provider_terms_evidence_refs` der Route; `expires_at` höchstens 12 Monate oder bis Vertragsende | Maintainer |
| M-21.4 | `eu_hosting_guarantee.md` 3.4 je Anbieter vervollständigen (Region, Transfergrundlage, DPF-Status, Freigabe) und in 3.1 oder 3.3 übernehmen | Legal |
| M-21.5 | Anbieterstand halbjährlich und bei jeder Änderung der Anbieterseiten neu prüfen (die Angebote in 1.3 haben sich 2025–2026 mehrfach geändert) | Maintainer |

**Code (Umsetzung in einem späteren PR)**

| ID | Maßnahme | Fundstelle heute |
|---|---|---|
| M-21.6 | Residenz nicht mehr statisch je Anbieter, sondern je **Endpunktprofil** führen: Tabelle `provider × endpoint → geography` (z. B. `openai@https://eu.api.openai.com/v1 → eu`, `vertex@europe-west4 → eu`, `vertex@eu → eu`, `anthropic@api.anthropic.com → global/us`). `PROVIDER_RESIDENCY` wird daraus abgeleitet | `studio/src/lib/ai/config/defaults.ts` |
| M-21.7 | Orchestrator baut den Client aus der **freigegebenen Route**: `baseURL`/Region kommen aus dem Endpunktprofil, nicht aus SDK-Defaults. Für Vertex einen eigenen Provider aufnehmen (`@ai-sdk/google-vertex` mit `location`; Paketname und Optionen vor Umsetzung prüfen, ⚠️ UNKLAR in diesem Stand). Globale Vertex-Endpunkte sind für `eu-only` verboten | `studio/src/lib/ai/orchestrator.ts` (`createModel`) |
| M-21.8 | Laufzeitprüfung vor jedem Aufruf: Host der effektiven `baseURL` ∈ Allowlist der Route; `provider_geography` der Route = Geografie des Endpunktprofils; sonst Block mit Grund `provider_region_mismatch` im Egress-Nachweis | `studio/src/lib/ai/egress-preflight.ts` (`block_reasons`) |
| M-21.9 | Wo der Anbieter die tatsächliche Region zurückmeldet, diese prüfen und im Nachweis speichern (Anthropic: `usage.inference_geo`). Für OpenAI und Vertex gibt es laut geprüften Seiten kein solches Antwortfeld → ⚠️ UNKLAR; dort genügt die Endpunktprüfung M-21.8 | neu |
| M-21.10 | `prompt_retention_days` und `provider_training_allowed` nur akzeptieren, wenn die Route mindestens eine Nachweisreferenz vom Typ „provider_terms“ mit Datum hat, das nicht älter als `expires_at` ist; sonst `data_handling_policy`-Block | `studio/src/lib/ai/policy-review.ts`, `studio/src/lib/ai/data-handling-policy.ts` |
| M-21.11 | Zustandsbehaftete Anbieterfunktionen technisch ausschließen: OpenAI `store: false`, keine Assistants/Threads/Vector Stores/Files; Vertex ohne Grounding mit Google Search/Maps; Anthropic ohne Batch/Files/Code Execution. Umsetzung als Allowlist erlaubter SDK-Aufrufe (`generateText`, `streamText` ohne Provider-Tools) | Routen unter `studio/src/app/api/ai/` |
| M-21.12 | Modell-IDs je Region verifizieren und `CAPABILITY_MODEL_MAP` so erweitern, dass nur Modelle wählbar sind, die im gewählten EU-Endpunkt gelistet sind (heute: `gemini-2.0-flash` nicht in der Vertex-Residenztabelle) | `studio/src/lib/ai/config/defaults.ts` |

### 1.5 Abnahmekriterien (Tests, die eine Umsetzung belegen muss)

| ID | Kriterium | Test (Vorschlag) |
|---|---|---|
| A-21.1 | Mit `dataResidency: 'eu-only'` wählt `chooseModel` nur Endpunktprofile mit Geografie `eu`; ohne solches Profil `null` | `studio/tests/lib/ai-route-model.test.ts` erweitern |
| A-21.2 | Kein Modellaufruf ohne explizite `baseURL`/Region aus der freigegebenen Route; ein SDK-Default-Endpunkt führt zu Block | Unit mit gemocktem `createModel` |
| A-21.3 | Weicht die Laufzeit-Region von `provider_region`/`provider_geography` der Route ab, blockiert das Gate mit `provider_region_mismatch`; der Nachweis enthält den Grund, aber keinen Inhalt | `studio/tests/lib/ai-egress-preflight.test.ts` erweitern |
| A-21.4 | Eine Route ohne gültige, unabgelaufene `provider_terms_evidence_refs` lässt sich nicht freigeben | `studio/tests/lib/ai-policy-review.test.ts` erweitern |
| A-21.5 | Ein Aufruf mit Provider-Tools, `store: true` oder Batch/Files-Endpunkt wird abgewiesen | Route-Test `studio/tests/api/ai-egress-route.test.ts` erweitern |
| A-21.6 | Anthropic-Antwort mit `usage.inference_geo` außerhalb der Route (sofern Anthropic genutzt wird) → Ergebnis verwerfen, Nachweis `provider_region_mismatch` | Unit mit Fixture-Antwort |
| A-21.7 | Nicht-technisch: je freigegebenem Anbieter liegen DPA, Transfergrundlage und ZDR-/Aufbewahrungsnachweis mit Datum vor und sind in `eu_hosting_guarantee.md` 3.4 eingetragen | Review-Checkliste Legal |

### 1.6 Offene Entscheidungen (Legal / Maintainer)

- **E-21.1** Welcher Weg wird angestrebt: (a) Gemini auf Vertex EU, (b) OpenAI mit EU-Residenz,
  (c) Claude über Vertex/Bedrock in EU-Regionen, (d) lokales Modell (`processing_boundary: local`,
  heute vom Orchestrator nicht unterstützt), oder (e) bewusst kein EU-Zwang mit SCC/DPF? Die
  Hausdoktrin „default to latest Claude“ kollidiert mit (a)/(b); das entscheidet der Maintainer.
- **E-21.2** Genügt EU-Residenz bei einem US-Anbieter mit DPF/SCC, oder verlangen Kunden eine
  EU-Gesellschaft als Vertragspartner? (Beschaffungsfrage, kundenabhängig.)
- **E-21.3** Ist `prompt_retention_days = 30` (Anbieter-Standard) für `internal_generic` tragbar, oder
  wird ZDR für jede Freigabe Pflicht?
- **E-21.4** Wer ist Vertragspartner des Anbieters (Betreiber oder Kunde mit eigenem Schlüssel,
  `credential_ref`)? Hängt an C-07.

---

## 2. C-22: Löschfristen für KI-Nachweise und AI-Policy-Reviews

### 2.1 Ist-Zustand (Code-Belege)

| Speicher | Personenbezug | Beleg |
|---|---|---|
| `audit_events` mit `entity_type = 'ai_egress'` | `actor` = E-Mail des angemeldeten Nutzers (`user!.email` in allen drei KI-Routen), `created_at`; `diff_json` enthält den inhaltsfreien Nachweis inkl. `payload_sha256` (pseudonym, vgl. `DPIA.md` 11.5). Geschrieben bei **jedem** KI-Aufruf, auch blockiert, unter `project_id = 'default'` | `studio/src/lib/ai/egress-gate.ts`, `studio/src/lib/ai/egress-preflight.ts` (`persistAiEgressEvidence`), `studio/src/lib/db/audit-repo.ts` |
| `ai_policy_reviews` | `submitted_by`, `reviewed_by` (E-Mail), `submitted_at`, `reviewed_at`, `rationale` (Freitext) | `studio/src/lib/db/sqlite.ts` (Tabellendefinition), `studio/src/lib/db/ai-policy-review-repo.ts` |
| `audit_events` mit `entity_type = 'ai_policy_review'` | `actor` (E-Mail), bei Entscheidung `justification` = Begründungstext im `diff_json` | `studio/src/lib/db/ai-policy-review-repo.ts` (`finishAiPolicyReview`) |
| Löschung | Keine Delete- oder Ablauffunktion in beiden Repositories; `audit-repo.ts` hat nur Insert und Select | `studio/src/lib/db/audit-repo.ts`, `studio/src/lib/db/ai-policy-review-repo.ts` |
| Verkettung | Jeder Hash schließt `actor` und `diff_json` sowie den Vorgänger-Hash ein. `verifyChain` prüft ab dem ersten Ereignis eines Projekts; das Löschen oder Ändern eines Ereignisses bricht die Prüfung aller Nachfolger | `studio/src/lib/db/audit-chain.ts` (`computeEventHash`, `verifyChain`) |
| Retention-Modell | `retention_policy.md` kennt die Tiers 30 Tage / 3 Jahre / 7 Jahre / unbefristet; die Studio-SQLite-Tabellen sind keinem Tier zugeordnet (vgl. C-03, C-08, C-15) | `compliance/retention_policy.md` Abschnitt 2 |

### 2.2 Anforderung und Rechtsgrundlage

- **Art. 5 Abs. 1 lit. e DSGVO (Speicherbegrenzung):** Personenbezogene Daten nur so lange, wie es
  für den Zweck erforderlich ist. Eine unbefristete Speicherung von E-Mail-Adressen in
  Sicherheitsnachweisen ist ohne Frist nicht begründbar.
- **Art. 5 Abs. 2, Art. 24, Art. 32 Abs. 1 lit. d DSGVO:** Die Nachweise selbst dienen der
  Rechenschaft und der Überprüfung der Sicherheitsmaßnahmen. Das trägt eine **befristete**
  Aufbewahrung (Rechtsgrundlage Art. 6 Abs. 1 lit. c bzw. f; Festlegung durch Legal).
- **Art. 17 Abs. 1 lit. a, Abs. 3 lit. e DSGVO:** Nach Zweckwegfall ist zu löschen; die Ausnahme
  „Geltendmachung, Ausübung oder Verteidigung von Rechtsansprüchen“ trägt eine längere Frist nur für
  Freigabeentscheidungen, nicht für jeden blockierten Aufruf.
- **Art. 25 Abs. 2 DSGVO:** Voreinstellung mit minimaler Speicherdauer; Pseudonymisierung, wo die
  Identität für den Zweck nicht nötig ist (Art. 4 Nr. 5, Art. 32 Abs. 1 lit. a).
- **Orientierung, nicht unmittelbar anwendbar:**
  - § 76 Abs. 4 BDSG (Protokolle im Anwendungsbereich der JI-Richtlinie): „Die Protokolldaten sind am
    Ende des auf deren Generierung folgenden Jahres zu löschen.“ [^l1] Gilt nicht für Studio, ist aber
    ein gesetzgeberischer Anhaltspunkt für die Dauer von Zugriffsprotokollen.
  - Art. 26 Abs. 6 VO (EU) 2024/1689 verlangt für Betreiber von **Hochrisiko**-KI eine
    Log-Aufbewahrung von „at least six months“ [^l2]. Studio ist nach den Fakten in `DPIA.md` 11.8
    voraussichtlich kein Hochrisiko-System (Einordnung durch Legal, C-11); die Frist dient nur als
    Untergrenze-Orientierung. Ob VO (EU) 2026/1744 Art. 26 geändert hat: ⚠️ UNKLAR (konsolidierte
    Fassung nicht geprüft).
  - §§ 195, 199 Abs. 1 BGB: regelmäßige Verjährung drei Jahre ab Schluss des Entstehungsjahres [^l3].
    Trägt die Aufbewahrung von Freigabeentscheidungen als Beleg für Sorgfalt.

### 2.3 Fristvorschlag [Vorschlag, Entscheidung Legal/DSB]

| Datenkategorie | Frist | Fristbeginn | Begründung |
|---|---|---|---|
| **A. `ai_egress`-Nachweise, Entscheidung `block`** (heute der einzige Fall) | **13 Monate**, danach Löschung des ganzen Monatssegments | `created_at` | Zweck: Nachweis, dass das Gate wirkt, und Erkennung von Missbrauchsmustern. Ein Jahresvergleich (Jahresreview, `retention_policy.md` 7.1) braucht 12 Monate plus einen Monat Puffer für den Löschlauf. Liegt unter der BDSG-Orientierung (bis zu 24 Monate) |
| **B. `ai_egress`-Nachweise, Entscheidung `allow`** (erst nach Öffnung) | **13 Monate**; bei laufendem Sicherheitsvorfall oder Betroffenenanfrage Legal Hold nach `retention_policy.md` 3 | `created_at` | Wie A. Zusätzlich ist die Personenbeziehbarkeit über `actor` für die Aufklärung einer Fehlübermittlung (Art. 33/34) nötig; ein Jahr deckt übliche Meldefristen und Prüfzyklen |
| **C. `actor` in A und B** | **90 Tage** im Klartext, danach nur noch Pseudonym | `created_at` | Die Identität ist für die Vorfallaufklärung kurzfristig nötig, für Statistik und Wirksamkeitsnachweis nicht. Umsetzung M-22.3 |
| **D. `ai_policy_reviews` mit Status `approved` und die zugehörigen Audit-Ereignisse** | **Gültigkeit der Route + 3 Jahre**, gerechnet ab Ende des Kalenderjahres, in dem die Route abläuft oder ersetzt wird | `expires_at` bzw. Ersetzung durch neue Revision | Beleg, auf welcher Grundlage Daten übermittelt wurden (Art. 5 Abs. 2); Verjährung §§ 195, 199 BGB; Art. 17 Abs. 3 lit. e |
| **E. `ai_policy_reviews` mit Status `rejected`** | **13 Monate** | `reviewed_at` | Nachvollziehbarkeit abgelehnter Anträge im Jahresreview; kein Übermittlungsbezug |
| **F. `ai_policy_reviews` mit Status `pending` ohne Entscheidung** | **6 Monate**, dann automatisch als verfallen schließen und nach E behandeln | `submitted_at` | Verwaiste Anträge haben keinen Zweck |
| **G. `rationale` / `justification` (Freitext)** | wie D bzw. E; zusätzlich Hinweis im UI und Längenprüfung: keine personenbezogenen Angaben Dritter | wie D/E | Freitext kann Namen enthalten; Minimierung an der Quelle |
| **H. Projektlöschung / Vertragsende** | Löschung aller Kategorien A–G des Projekts nach `retention_policy.md` 6.2; D nur, wenn Legal keine längere Frist festlegt | Vertragsende | Art. 28 Abs. 3 lit. g |

Einordnung in `retention_policy.md`: A, B, E sind ein neues Tier **13 Monate** (bisher nicht
vorhanden); F ein neues Tier **6 Monate**; D entspricht Tier 2 (3 Jahre) mit abweichendem
Fristbeginn. Die Aufnahme ins Tier-Modell entscheidet Legal zusammen mit C-10 und C-15.

### 2.4 Maßnahmen

| ID | Maßnahme | Fundstelle heute |
|---|---|---|
| M-22.1 | **Segmentierte Hash-Kette:** Die Kette wird je Projekt und Kalendermonat abgeschlossen. Ein Anker-Datensatz (neue Tabelle, z. B. `audit_chain_anchors`: `project_id`, `segment`, `first_event_id`, `last_hash`, `event_count`, `closed_at`) hält den letzten Hash des Segments. Das nächste Segment startet mit diesem Hash als `prev_hash`. `verifyChain` beginnt beim ältesten **noch vorhandenen** Anker. So lassen sich ganze abgelaufene Segmente löschen, ohne die Prüfbarkeit des Rests zu verlieren | `studio/src/lib/db/audit-chain.ts` |
| M-22.2 | **Löschlauf (Prune):** ein Server-Job, der je Kategorie A–G die Frist aus 2.3 anwendet, nur ganze Segmente bzw. ganze Review-Datensätze löscht und das Ergebnis inhaltsfrei protokolliert (Anzahl, Segment, Zeitpunkt, keine E-Mail). Legal Hold (`retention_policy.md` 3) sperrt Segmente. Dry-Run-Modus Pflicht | neu; ersetzt für Studio das in C-08 fehlende `prune_expired_rows.py` |
| M-22.3 | **Pseudonymer Actor:** Statt der E-Mail wird im Hash und in `actor` ein Schlüssel-Pseudonym `HMAC-SHA256(k_projekt, lower(email))` gespeichert; die Zuordnung E-Mail ↔ Pseudonym liegt in einer eigenen Tabelle, die nach 90 Tagen (Kategorie C) gelöscht wird. Für neue Ereignisse ab Umsetzung; Altbestand wird mit dem ersten Löschlauf nach Ablauf entfernt. Der Schlüssel liegt im Secret-Store (`@/lib/secrets`), nicht in der Datenbank | `studio/src/lib/ai/egress-gate.ts` (`actor`), `studio/src/lib/db/audit-repo.ts` |
| M-22.4 | **Zuordnung der KI-Nachweise zum Projekt:** Die KI-Routen übergeben `projectId`, damit Löschung bei Projektende (Kategorie H) greift; der Sammelbestand `project_id = 'default'` wird als eigenes Segment nach Kategorie A gelöscht | Routen unter `studio/src/app/api/ai/`; `studio/src/lib/ai/egress-gate.ts` |
| M-22.5 | **Review-Lebenszyklus:** `ai_policy_reviews` um `expires_at` der Route und `retention_until` ergänzen; `pending` nach 6 Monaten automatisch `expired`; Status-Constraint in `studio/src/lib/db/sqlite.ts` erweitern | `studio/src/lib/db/sqlite.ts`, `studio/src/lib/db/ai-policy-review-repo.ts` |
| M-22.6 | **Freitext minimieren:** Hinweis im Review-Dialog („keine Namen Dritter, keine Kundendaten“); die Begründung vor dem Speichern durch den Scanner aus `studio/src/lib/ai/egress-preflight.ts` (`scanSensitiveData`) prüfen und E-Mail/Telefon/IBAN-Funde abweisen | `studio/src/app/api/projects/[projectId]/ai-policy-reviews/route.ts` |
| M-22.7 | **Betroffenenrechte:** Auskunft (Art. 15) über Pseudonym-Zuordnung beantwortbar machen; Löschersuchen (Art. 17) durch Entfernen der Zuordnung (M-22.3) erfüllen, soweit Kategorie D nicht Art. 17 Abs. 3 lit. e unterliegt | Verfahren in `retention_policy.md` 6.1 ergänzen |
| M-22.8 | **Dokumentation:** Kategorien A–H in `retention_policy.md` und im VVT (ACT-006/ACT-007) eintragen; `DPIA.md` 11.5 und R-KI-6 aktualisieren, sobald umgesetzt | `compliance/` |

### 2.4a Umsetzungsstand (27.09.2026)

Technisch umgesetzt, **Fristen weiter Vorschlag** (E-22.1 offen). Der Ledger-Punkt C-22 bleibt offen.

| Maßnahme | Stand | Code |
|---|---|---|
| M-22.1 | **Umgesetzt mit Abweichung:** statt Monatssegmenten ein **Löschvermerk**. Ein Projekt-Chain enthält KI-Nachweise und alle anderen Audit-Ereignisse gemischt; ein ganzes Monatssegment zu löschen hätte Bracket-, Projekt- und Rollenereignisse mitgenommen. Der Löschlauf bescheinigt jede entstandene Lücke (Folgeereignis + erwarteter Vorgänger-Hash) in seinem eigenen, verketteten `audit_retention`-Ereignis; `verifyChain` akzeptiert eine Lücke nur dort. Gilt auch für den Altbestand | `studio/src/lib/db/audit-chain.ts`, `studio/src/lib/db/ai-retention.ts` |
| M-22.2 | **Umgesetzt:** Kategorien A/B (13 Monate), E (13 Monate), F (6 Monate → `expired`), D (Jahresende des Routenablaufs + 3 Jahre). Dry-Run ist Voreinstellung; ein echter Lauf braucht `confirm: true`. Legal Hold je Projekt mit Aktenzeichen statt Freitext. Ein Projekt mit bereits gebrochener Kette wird nicht bereinigt, sondern gemeldet. Fristen per Umgebungsvariable überschreibbar (`STUDIO_AI_RETENTION_*`) | `studio/src/lib/db/ai-retention.ts`, `studio/src/app/api/audit/retention/route.ts` |
| M-22.3 | **Offen.** Bis dahin steht die E-Mail bis zum Ablauf von Kategorie A (13 Monate) im Klartext, nicht nur 90 Tage | — |
| M-22.4 | **Offen.** KI-Nachweise liegen weiter unter `project_id = 'default'` | — |
| M-22.5 | **Teilweise:** `route_expires_at` wird beim Einreichen gespeichert, Status `expired` mit Migration. Genehmigte Altbestände ohne `route_expires_at` bleiben erhalten und werden im Bericht gezählt (`approved_without_route_expiry`). Ersetzung durch eine neue Revision als Fristbeginn ist nicht umgesetzt | `studio/src/lib/db/sqlite.ts`, `studio/src/lib/db/ai-policy-review-repo.ts` |
| M-22.6 bis M-22.8 | **Offen** | — |

Abnahme: A-22.1, A-22.2, A-22.3, A-22.5 und A-22.7 sind durch `studio/tests/lib/audit-retention.test.ts` belegt; A-22.4 (90 Tage) und A-22.6 (Freitextprüfung) nicht. Der Löschvermerk macht die Kette nicht fälschungssicherer als vorher: wer die Datenbank schreiben kann, kann die ungeschlüsselte Kette neu berechnen (E-22.3, WORM).

### 2.5 Abnahmekriterien

| ID | Kriterium | Test (Vorschlag) |
|---|---|---|
| A-22.1 | Nach Löschung eines abgelaufenen Monatssegments liefert `verifyChain` `valid: true` für den Rest; Manipulation eines verbleibenden Ereignisses wird weiterhin erkannt | `studio/tests/lib/audit-chain.test.ts` erweitern |
| A-22.2 | Löschen eines **einzelnen** Ereignisses innerhalb eines offenen Segments bleibt als Manipulation erkennbar | `studio/tests/lib/audit-chain.test.ts` |
| A-22.3 | Der Löschlauf entfernt `ai_egress`-Ereignisse älter als 13 Monate, lässt jüngere und Legal-Hold-Segmente unberührt; Dry-Run löscht nichts | neuer Test `studio/tests/lib/audit-retention.test.ts` (mit injizierter Uhr) |
| A-22.4 | Nach 90 Tagen ist aus `audit_events` und Zuordnungstabelle keine E-Mail-Adresse mehr für `ai_egress` ermittelbar (Volltextsuche nach `@` im Datenbestand der Fixture) | `studio/tests/lib/audit-retention.test.ts` |
| A-22.5 | Genehmigte Reviews bleiben bis `expires_at` + Jahresende + 3 Jahre erhalten und werden danach samt Audit-Ereignissen gelöscht; abgelehnte nach 13 Monaten; `pending` wird nach 6 Monaten `expired` | `studio/tests/lib/ai-policy-review.test.ts` erweitern |
| A-22.6 | Eine Begründung mit E-Mail-Adresse oder Telefonnummer wird mit 400 abgewiesen | `studio/tests/api/ai-policy-reviews-route.test.ts` erweitern |
| A-22.7 | Das Protokoll des Löschlaufs enthält keine E-Mail-Adresse und keinen Freitext | `studio/tests/lib/audit-retention.test.ts` |

### 2.6 Offene Entscheidungen

- **E-22.1** Fristen A–H bestätigen oder ändern (insbesondere 13 Monate für A/B und die
  Drei-Jahres-Frist für D). Verhältnis zur Audit-Trail-Frist von ACT-002 (7 Jahre) klären (C-15).
- **E-22.2** Rechtsgrundlage der Nachweisspeicherung: Art. 6 Abs. 1 lit. c (Art. 32) oder lit. f.
  Bei lit. f Interessenabwägung dokumentieren; für Beschäftigte § 26 BDSG bzw. dessen
  Anwendbarkeit nach EuGH C-34/21 prüfen (⚠️ UNKLAR, hier nicht geprüft).
- **E-22.3** Genügt die segmentierte lokale Kette (M-22.1), oder wird ein externes, unveränderliches
  Log (WORM) verlangt? `studio/docs/design/AI_POLICY_REVIEW.md` stellt klar, dass die SQLite-Kette
  kein WORM-Log ist.
- **E-22.4** Ob `payload_sha256` nach Ablauf von Kategorie C ebenfalls entfernt wird (er kann bei
  kurzen, erratbaren Eingaben einen Inhalt bestätigen; `DPIA.md` 11.5).

---

## 3. C-23: Redaktion, Namenserkennung und Ausgabeprüfung vor einer Öffnung

### 3.1 Ist-Zustand (Code-Belege)

| Befund | Beleg |
|---|---|
| Das Gate ist konstant geschlossen: `approvalGranted: false`; ein genehmigtes AI-Policy-Review ändert daran nichts | `studio/src/lib/ai/egress-gate.ts`; `studio/docs/design/AI_POLICY_REVIEW.md` („An approved review does not enable AI egress“) |
| Der Scanner erkennt nur Muster: Private Key, Bearer, JWT, Secret-Zuweisungen, E-Mail, Telefon (nur mit `+`/`00`-Präfix), UUID, Home-Pfade, IBAN (mit Prüfsumme) und konfigurierte Sperrbegriffe. **Keine** Namen, Anschriften, Geburtsdaten, nationale Telefonnummern ohne Ländervorwahl, Steuer- oder Sozialversicherungsnummern, Art.-9-Angaben | `studio/src/lib/ai/egress-preflight.ts` (`RULES`, `IBAN`, `scanSensitiveData`) |
| Der Scanner **redigiert nicht**, er zählt Funde und blockiert. Die Allowlist maskiert nur für die Prüfung | `studio/src/lib/ai/egress-preflight.ts` (`maskAllowlist`, `buildAiEgressEvidence`) |
| `redacted` ist ein vom Aufrufer gesetztes Flag im Kontext, keine vom System erzeugte Eigenschaft; heute setzt es keine Route (Default `false`) | `studio/src/lib/ai/data-handling-policy.ts`; `studio/src/lib/ai/egress-gate.ts` |
| Keine Route übergibt `profile` oder `context`; die Datenklasse ist immer `unknown` | Routen unter `studio/src/app/api/ai/` |
| Der KI-Chat übergibt dem Scanner nur die **Namen** der Tools. Die Tools lesen KPI-Katalog, Brackets und Action Codes (`lookup_kpi`, `list_brackets`, `suggest_actions`) bzw. erzeugen/validieren YAML; ihre Ergebnisse gehen ungeprüft zurück in den Modellkontext bzw. zum Client | `studio/src/app/api/ai/chat/route.ts`; `studio/src/lib/ai/tools/discovery-tools.ts` |
| Modellausgaben werden ungeprüft gestreamt (`toTextStreamResponse()`) bzw. als JSON geparst und zurückgegeben; es gibt keine Prüfung auf zurückgespiegelte Daten, Secrets oder Schema-Konformität außer `JSON.parse` | `studio/src/app/api/ai/chat/route.ts`, `studio/src/app/api/ai/wizard/route.ts`, `studio/src/app/api/ai/factsheet-draft/route.ts` |
| Fehlertexte des SDK gehen im Wizard in Telemetrie und Antwort (`AI generation failed: …`) und können Eingabefragmente enthalten | `studio/src/app/api/ai/wizard/route.ts` |
| Kennzeichnung von KI-Ausgaben: nur `engine: 'ai'` in der Factsheet-Route; keine maschinenlesbare Markierung | `studio/src/app/api/ai/factsheet-draft/route.ts` |

### 3.2 Anforderung und Rechtsgrundlage

- **Art. 25 Abs. 1 DSGVO:** Datenschutz durch Technikgestaltung, ausdrücklich mit Pseudonymisierung
  und Datenminimierung. Die Policy verlangt für nicht-öffentliche Daten an `external_cloud` bereits
  `redacted: true`; das setzt eine echte Redaktionsstufe voraus.
- **Art. 5 Abs. 1 lit. c, f; Art. 32 Abs. 1 und 2 DSGVO:** nur erforderliche Daten übermitteln;
  Schutz gegen unbefugte Offenlegung, dem Risiko angemessen (Stand der Technik).
- **Art. 35 Abs. 7 lit. d DSGVO:** Die DSFA (`DPIA.md` 11.7, R-KI-3/R-KI-4) nennt Redaktion und
  Ausgabeprüfung als fehlende Abhilfemaßnahmen.
- **EDPB:** Der Bericht „AI Privacy Risks & Mitigations – Large Language Models“ (Support Pool of
  Experts, April 2025) beschreibt Filterung von Ein- und Ausgaben und die Minimierung von Prompts als
  Maßnahmen für LLM-Nutzung [^e1]. Die Leitlinien 01/2025 zur Pseudonymisierung (zur Konsultation
  angenommen im Januar 2025) beschreiben Pseudonymisierung als Maßnahme mit Restrisiko, die
  zusätzliche Informationen getrennt halten muss [^e2]; finale Fassung ⚠️ UNKLAR.
- **Art. 50 Abs. 2 VO (EU) 2024/1689:** Anbieter von KI-Systemen, die synthetischen Text erzeugen,
  sorgen für eine maschinenlesbare Markierung; Ausnahme u. a. bei „assistive function for standard
  editing“ [^l2]. Gilt seit 02.08.2026, Übergangsfrist nach VO (EU) 2026/1744 siehe `README.md`.
  Ob Studio Anbieter i. S. d. AI Act ist, entscheidet Legal (C-11).

### 3.3 Zielbild der Egress-Pipeline [Vorschlag]

Jeder Modellaufruf durchläuft serverseitig und in dieser Reihenfolge:

1. **Kontext bestimmen** (M-23.1): Projekt, Route, Datenklasse, Datenform, Zweck aus der Quelle,
   nicht aus dem Request-Body.
2. **Redigieren** (M-23.2, M-23.3): Muster und erkannte Namen/Anschriften durch typisierte
   Platzhalter ersetzen.
3. **Nachprüfen** (M-23.4): Scanner auf den **redigierten** Payload; jeder Restfund blockiert.
4. **Policy und Freigabe** (M-23.7): `evaluateAiDataHandling` mit `redacted` aus Schritt 2 und eine
   abgeleitete Freigabe statt `false`.
5. **Modellaufruf** mit Endpunkt aus C-21.
6. **Tool-Ergebnisse** (M-23.5) vor Rückgabe an das Modell durch Schritt 2–3.
7. **Ausgabeprüfung** (M-23.6) vor Auslieferung an den Client; Platzhalter werden nur für den
   berechtigten Nutzer serverseitig zurückgesetzt, nie im Modellkontext.

### 3.4 Maßnahmen

| ID | Maßnahme | Fundstelle heute |
|---|---|---|
| M-23.1 | **Pflichtkontext:** `requireApprovedAiEgress` bekommt `projectId`, Routen-ID und einen serverseitig ermittelten `context` (`classification`, `data_form`, `purpose`). Ermittlung aus der Quelle: Katalog-/Bracket-Inhalte `internal_generic`, hochgeladene Quelldokumente mindestens `customer_confidential`, unbekannt → `unknown` (blockiert). Der Request-Body darf die Klasse nicht setzen | `studio/src/lib/ai/egress-gate.ts`, Routen unter `studio/src/app/api/ai/` |
| M-23.2 | **Deterministische Redaktion** für alle vorhandenen Regeln plus Ergänzungen: nationale Telefonnummern (DE-Formate), Postanschrift (Straße + Hausnummer, PLZ + Ort), Geburtsdaten im Personenkontext, Steuer-ID/USt-IdNr., Kfz-Kennzeichen, IP-Adressen. Ersetzung durch `<EMAIL_1>`, `<PERSON_2>` usw.; die Zuordnung liegt nur im Arbeitsspeicher der Anfrage und wird nie gespeichert oder übermittelt | `studio/src/lib/ai/egress-preflight.ts` (`RULES`) |
| M-23.3 | **Namenserkennung:** zweistufig. (a) **Wörterbuch** aus bekannten Personen des Projekts (Studio-Nutzer, Projektmitglieder, konfigurierte Sperrbegriffe in `scan_policy.blocked_terms`) mit Flexionsvarianten. (b) **NER-Modell lokal** innerhalb der Verarbeitungsgrenze (z. B. ein deutsch-/englischsprachiges spaCy- oder Presidio-Setup als Sidecar); das Modell darf selbst keinen externen Aufruf machen. Schwellwert und Sprachen konfigurierbar; Fehlklassifikationen landen als `PERSON`, nicht als Durchlass | neu; Anbindung in `studio/src/lib/ai/egress-preflight.ts` |
| M-23.4 | **`redacted` wird vom System gesetzt:** nur wenn M-23.2/M-23.3 gelaufen sind und die Nachprüfung (Scanner auf redigiertem Text) null personenbezogene Funde ergibt. Ein vom Aufrufer gesetztes `redacted` wird ignoriert. Der Nachweis speichert Redaktionsanzahl je Typ und die Version des Regelsatzes/NER-Modells, keinen Inhalt | `studio/src/lib/ai/data-handling-policy.ts`, `studio/src/lib/ai/egress-preflight.ts` |
| M-23.5 | **Tool-Ergebnisse prüfen:** jedes `execute` in `discoveryTools` wird von einem Wrapper umschlossen, der das Ergebnis durch M-23.2–M-23.4 schickt, bevor es in den Modellkontext geht; Mehrschritt-Aufrufe (`stopWhen`) nur mit diesem Wrapper. Blockiert der Wrapper, erhält das Modell eine neutrale Fehlermeldung ohne Inhalt | `studio/src/lib/ai/tools/discovery-tools.ts`, `studio/src/app/api/ai/chat/route.ts` |
| M-23.6 | **Ausgabeprüfung:** (a) Streaming über einen Transform-Stream mit gleitendem Puffer, der Secrets, nicht zurückgesetzte Platzhalter-Muster und personenbezogene Funde erkennt und den Stream abbricht bzw. maskiert; (b) strukturierte Ausgaben (Wizard, Factsheet) gegen ein JSON-Schema validieren statt nur `JSON.parse`; (c) Ausgaben nie automatisch speichern, Übernahme nur über `wizard/save` durch den Menschen; (d) SDK-Fehlertexte nicht an Client oder Telemetrie weitergeben, sondern auf einen Fehlercode abbilden | Routen unter `studio/src/app/api/ai/`; `studio/src/lib/ai/telemetry.ts` |
| M-23.7 | **Abgeleitete Freigabe:** `approvalGranted` ist `true` nur, wenn für Projekt und Route ein `approved` Review existiert, das Review nicht abgelaufen ist, der Routen-Hash dem Laufzeitprofil entspricht und die C-21-Prüfungen (Endpunkt, Nachweise) grün sind. Umstellung nur mit Feature-Flag, standardmäßig aus | `studio/src/lib/ai/egress-gate.ts`, `studio/src/lib/db/ai-policy-review-repo.ts` |
| M-23.8 | **Kennzeichnung (Art. 50):** alle KI-Antworten tragen `engine: 'ai'`, Modell und Anbieter in den Metadaten; die UI zeigt einen sichtbaren Hinweis; gespeicherte Entwürfe erhalten ein Herkunftsfeld (z. B. `provenance: ai-draft`). Umfang abhängig von E-23.3 | Routen unter `studio/src/app/api/ai/`; UI ⚠️ UNKLAR (nicht geprüft) |
| M-23.9 | **Change-Control:** Pflicht-Review durch Maintainer für `studio/src/lib/ai/**` und `studio/src/app/api/ai/**` (z. B. per CODEOWNERS; dieser PR ändert `.github/` bewusst nicht), weil eine Code-Änderung das Gate entfernen kann (`DPIA.md` 11.7, R-KI-1) | Repo-Konfiguration |

### 3.5 Abnahmekriterien

| ID | Kriterium | Test (Vorschlag) |
|---|---|---|
| A-23.1 | Ohne serverseitig ermittelten Kontext (Klasse `unknown`) blockiert jede KI-Route; eine im Request-Body gesetzte Klasse oder `redacted: true` ändert nichts | `studio/tests/api/ai-egress-route.test.ts` erweitern |
| A-23.2 | Redaktions-Korpus (synthetisch, ohne echte Personen; neu unter `core/fixtures/neutral/ai-egress-preflight/`): E-Mail, Telefon (international und national), IBAN, Anschrift, Geburtsdatum, Steuer-ID werden zu 100 % ersetzt; der redigierte Payload enthält keine Originalwerte | `studio/tests/lib/ai-egress-preflight.test.ts` erweitern |
| A-23.3 | Namenserkennung: Wörterbuch-Treffer (inkl. Flexion) 100 %; NER auf einem synthetischen deutsch-/englischen Korpus mit Recall ≥ 0,95 für `PERSON` (Zielwert, Entscheidung E-23.2); Messwert wird im Test ausgegeben und darf nicht sinken | neuer Test mit Korpus-Fixture |
| A-23.4 | `redacted` im Nachweis ist `true` nur nach erfolgreicher Redaktion und fundfreier Nachprüfung; der Nachweis enthält Anzahl je Typ und Regelsatz-Version, aber keinen Originalwert und keinen Platzhalter-Mapping-Eintrag | `studio/tests/lib/ai-egress-preflight.test.ts` |
| A-23.5 | Ein Tool, das eine E-Mail-Adresse zurückgibt, erreicht das Modell nur redigiert; ein Tool mit Secret im Ergebnis führt zu Block | Unit für den Tool-Wrapper mit gemocktem Modell |
| A-23.6 | Eine gemockte Modellausgabe mit Secret oder personenbezogenem Fund wird im Stream abgebrochen bzw. maskiert; ungültiges JSON oder Schemaverstoß im Wizard führt zu 422 ohne Rohausgabe | Route-Tests mit gemocktem `streamText`/`generateText` |
| A-23.7 | SDK-Fehlertexte erscheinen weder in der Antwort noch in `llm_step_events` | Route-Test Wizard, Telemetrie-Test |
| A-23.8 | `approvalGranted` wird `true` nur bei gültigem, unabgelaufenem, hash-gleichem Review **und** grünen C-21-Prüfungen; jede Abweichung blockiert. Ohne Feature-Flag bleibt das Gate geschlossen | `studio/tests/api/ai-egress-route.test.ts`, `studio/tests/lib/ai-policy-review.test.ts` |
| A-23.9 | Alle KI-Antworten tragen die Kennzeichnung nach M-23.8 | Route-Tests |

### 3.6 Offene Entscheidungen

- **E-23.1** Welche Datenklassen sollen überhaupt an ein externes Modell gehen? Die Policy lässt
  `customer_confidential` an `external_cloud` nie zu (`studio/src/lib/ai/data-handling-policy.ts`).
  Für den Discovery-Chat mit Quelldokumenten heißt das: nur über `customer_managed_cloud` oder
  `local`. Bestätigung durch Legal und Maintainer.
- **E-23.2** Zielwert für die Namenserkennung (Recall-Schwelle) und ob eine Rest-Fehlerquote bei
  `internal_generic` tragbar ist. Eine 100-%-Erkennung von Namen in Freitext ist technisch nicht
  garantierbar; das ist ein Restrisiko für die DSFA (R-KI-3).
- **E-23.3** AI-Act-Rolle und Umfang der Kennzeichnung (Art. 50 Abs. 1/2; Ausnahme „assistive
  function for standard editing“?), zusammen mit C-11.
- **E-23.4** Betrieb des NER-Modells (Sidecar-Container, Ressourcen, Update-Prozess) und wer es
  pflegt.

---

## 4. Zusammenfassung und Rückverfolgung

| Ledger | Kernempfehlung | Heute umsetzbar ohne Öffnung? | Abhängigkeiten |
|---|---|---|---|
| C-21 | Endpunktprofile mit geprüfter Geografie statt `PROVIDER_RESIDENCY: any`; EU-fähig belegt sind Gemini auf Vertex (EU-Endpunkt) und OpenAI mit EU-Residenz; Anthropic 1st party bietet keine EU-Inferenz. Vertrag, ZDR und Transfergrundlage je Anbieter | Vertrag/Auswahl ja; Code erst mit Öffnung sinnvoll | C-07, C-20, E-21.1 |
| C-22 | Fristen 13 Monate (Egress-Nachweise), 90 Tage Klartext-Actor, Route + 3 Jahre (genehmigte Reviews), 13 Monate (abgelehnt), 6 Monate (verwaist); segmentierte Hash-Kette und Löschlauf | **Ja, sollte zuerst kommen** (Daten entstehen heute) | C-03, C-08, C-10, C-15 |
| C-23 | Pipeline Kontext → Redaktion → Nachprüfung → Policy/Freigabe → Tool- und Ausgabeprüfung; `redacted` vom System gesetzt; abgeleitete Freigabe hinter Feature-Flag | Ja (bei geschlossenem Gate testbar) | C-11, C-12, C-21 |

Betroffene Dokumente nach Umsetzung: `DPIA.md` 11.4/11.5/11.7, `eu_hosting_guarantee.md` 3.4,
`retention_policy.md` 2/5/6, `data_processing_record.md` ACT-006/ACT-007, `AVV_Template.md` 5.3.

---

## 5. Quellen (abgerufen am 26.09.2026)

[^a1]: Anthropic, Claude Platform Docs, „Data residency“ (ohne Datumsangabe): https://platform.claude.com/docs/en/manage-claude/data-residency
[^a2]: Anthropic, Claude Platform Docs, „API and data retention“ (ohne Datumsangabe): https://platform.claude.com/docs/en/manage-claude/api-and-data-retention
[^a3]: Anthropic Privacy Center, „How long do you store my organization's data?“ (aktualisiert 01.07.2026): https://privacy.claude.com/en/articles/7996866-how-long-do-you-store-my-organization-s-data
[^g1]: Google Cloud, „Data residency“, Gemini Enterprise Agent Platform (Last updated 2026-09-25 UTC): https://docs.cloud.google.com/gemini-enterprise-agent-platform/resources/data-residency
[^g2]: Google Cloud, „Gemini Enterprise Agent Platform and zero data retention“ (Last updated 2026-09-25 UTC): https://docs.cloud.google.com/gemini-enterprise-agent-platform/resources/zero-data-retention
[^g3]: Google, „Gemini API Additional Terms of Service“ (zuletzt aktualisiert 28.04.2026): https://ai.google.dev/gemini-api/terms
[^o1]: OpenAI, „Data controls in the OpenAI platform“ (ohne Datumsangabe): https://developers.openai.com/api/docs/guides/your-data
[^o2]: OpenAI Help Center, „Data residency for the OpenAI API“ (Verweisseite): https://help.openai.com/en/articles/10503543-data-residency-for-the-openai-api
[^l1]: § 76 BDSG: https://www.gesetze-im-internet.de/bdsg_2018/__76.html
[^l2]: VO (EU) 2024/1689 (AI Act), ABl. L vom 12.07.2024, Art. 26 Abs. 6 und Art. 50 Abs. 2 im Originaltext: https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=OJ:L_202401689 (Änderungen durch VO (EU) 2026/1744 in diesen Absätzen nicht geprüft, ⚠️ UNKLAR)
[^l3]: §§ 195, 199 BGB: https://www.gesetze-im-internet.de/bgb/__195.html, https://www.gesetze-im-internet.de/bgb/__199.html
[^e1]: EDPB Support Pool of Experts, „AI Privacy Risks & Mitigations – Large Language Models (LLMs)“, April 2025: https://www.edpb.europa.eu/documents/support-pool-of-experts/ai-privacy-risks-mitigations-large-language-models-llms_en
[^e2]: EDPB, „Guidelines 01/2025 on Pseudonymisation“ (Fassung zur Konsultation): https://www.edpb.europa.eu/our-work-tools/documents/public-consultations/2025/guidelines-012025-pseudonymisation_en

DSGVO-Artikel nach VO (EU) 2016/679: https://eur-lex.europa.eu/eli/reg/2016/679/oj/deu (Abgleich der
Artikelzitate wie in `README.md`, Abschnitt „Rechtsstand-Abgleich“).

### 5.1 ⚠️ UNKLAR (gesammelt)

- Verfügbarkeit einzelner Claude-Modelle in `eu`/`europe-west1`/`europe-west4` auf Vertex (Tabelle
  nur grafisch markiert) sowie Aufbewahrung/Abuse-Monitoring für Partner-Modelle auf Vertex.
- Claude über Amazon Bedrock in EU-Regionen: nicht geprüft.
- Gemini Developer API: Verarbeitungsort und Dauer des Abuse-Loggings.
- OpenAI EU-Residenz: Verfügbarkeit der im Code genutzten Modelle (`gpt-4o`, `gpt-4o-mini`) in der
  EU-Region; Rückmeldung der tatsächlichen Region in der Antwort.
- Paketname und Optionen eines Vertex-Providers für das AI SDK (`@ai-sdk/google-vertex`).
- Änderungen an Art. 26 und Art. 50 AI Act durch VO (EU) 2026/1744; finale Fassung der
  EDPB-Leitlinien 01/2025; Beschäftigtendatenschutz (§ 26 BDSG nach EuGH C-34/21).
- DPF-Status der Anbieter am Stichtag (C-20).
