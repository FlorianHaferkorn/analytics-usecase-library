# Data Protection Impact Assessment (DPIA)

**Regulation:** DSGVO Article 35  
**Document Version:** 1.0  
**Last Updated:** 2026-04-22  
**Inhaltliche Durchsicht (ohne Legal-Sign-off):** 2026-09-25 – siehe Abschnitt 10; Studio-KI ergänzt in Abschnitt 11 (2026-09-25, Code-Stand PR #478); Optionen der Kundenplattform Microsoft Fabric/Power BI (Schlüssel, Customer Lockbox, KI-Zugriff je Semantikmodell) in Abschnitt 12 (2026-10-01)  
**Next Review:** (to be completed by legal team)

---

## 1. Executive Summary

This Data Protection Impact Assessment (DPIA) evaluates the processing of personal data within the ALUCA (Analytics Library of Use Cases) platform. The purpose of this document is to identify, assess, and mitigate privacy and data protection risks arising from analytics processing, reporting, and action-code execution workflows.

⚠️ TO BE COMPLETED BY LEGAL: Add a summary of the overall privacy risk level (low / moderate / high) and whether further consultation with the supervisory authority (Datenschutzbehörde) is required under Art. 36 DSGVO.

---

## 2. Scope of Processing

ALUCA is a multi-tenant data analytics platform that enables organizations to:

- Ingest event data and transaction records (potentially containing personal identifiers)
- Execute machine-readable action codes that reference users and outcomes
- Generate business intelligence dashboards and reports
- Maintain audit logs and compliance records

⚠️ TO BE COMPLETED BY LEGAL: Confirm the role classification:

- Is the organization a **data controller** (defining purposes and means of processing), a **processor** (processing on behalf of customers), or both?
- If processor: which customer organizations are the controllers?
- If controller: what is the lawful basis (Art. 6) for each processing activity?

---

## 3. Data Categories and Personal Data Identification

### 3.1 Direct Identifiers

| Column / Field | Table(s) | Sensitivity |
|---|---|---|
| `user_id` | `dim_user`, `fact_action_outcome` | High (may be pseudonymized) |
| `email_address` | `dim_user` | High PII |
| `first_name`, `last_name` | `dim_user` | High PII |
| `phone_number` | `dim_user` | High PII |
| `action_actor_name` | `fact_action_outcome` | Medium (audit log) |

### 3.2 Quasi-Identifiers (High Re-identification Risk)

| Field | Re-id Risk | Mitigation |
|---|---|---|
| `ip_address` | High (combined with timestamp) | Hash; aggregate; retain <30 days |
| `device_fingerprint` | High | Pseudonymize; no direct storage |
| `cohort_segment` | Medium–High (if n < 5) | Aggregate or mask if small |

### 3.3 Special Categories (Art. 9 DSGVO)

⚠️ TO BE COMPLETED BY LEGAL: Flag whether the following are in scope:

- Health data
- Racial/ethnic origin
- Political opinions, union membership
- Biometric data
- Genetic data
- Philosophical/religious beliefs

If ANY special categories are present, Art. 9 restrictions apply (explicit consent or derogations required).

---

## 4. Legal Basis (Art. 6 DSGVO)

### 4.1 Processing Activity 1: Analytics Reporting and KPI Calculation

**Purpose:** Monitor KPIs, detect trends, inform decision-making

**Legal basis:** ⚠️ TO BE COMPLETED BY LEGAL: Select (a) Consent, (b) Contract, (c) Legal obligation, (d) Vital interests, (e) Public task, (f) Legitimate interests + justification

**Data categories:** User IDs (pseudonymized), action outcomes, timestamps, cohort segments

**Retention period:** 3–7 years (defined by retention tier)

### 4.2 Processing Activity 2: Action Code Execution & Audit Trail

**Purpose:** Execute business rules; maintain immutable audit log

**Legal basis:** ⚠️ TO BE COMPLETED BY LEGAL: (b) Contract OR (c) Legal obligation + justification

**Data categories:** User ID, action code ID, outcome, timestamp, actor name

**Retention period:** 7 years (compliance/audit standard)

### 4.3 Processing Activity 3: Platform Maintenance & Security Monitoring

**Purpose:** Detect and prevent abuse, prevent unauthorized access, maintain availability

**Legal basis:** ⚠️ TO BE COMPLETED BY LEGAL: (f) Legitimate interests (protecting platform) + balancing test

**Data categories:** IP addresses, session IDs, device fingerprints, user activity logs

**Retention period:** 30 days (raw logs); 1 year (aggregated events)

---

## 5. Risk Assessment

| Risk Scenario | Likelihood | Impact | Mitigation | Residual Risk |
|---|---|---|---|---|
| **Data breach:** Unauthorized access to pseudonymized user IDs | Medium | High | Encryption (AES-256); TLS; access logging | Medium |
| **Unauthorized re-identification:** Malicious actor links IDs to real identities | Medium | High | Encryption keys (HSM); RBAC; key separation | Medium |
| **Cross-dataset inference:** Re-identification via aggregated cohort data | Low–Med | Medium | Differential privacy; minimum n-size (n≥5) | Low |
| **Accidental data export:** Unmasked PII in exports | Low | High | PII detection; export governance; DLP; Exportwege nach Label: Excel mit Live-Verbindung erbt das Label des Semantikmodells (bis 500.000 Zeilen), statisches Excel das des Berichts (bis 150.000), CSV trägt kein Label (bis 30.000) und wird bei Labelnutzung auf eine Sicherheitsgruppe beschränkt (ergänzt 2026-10-01, C-27) | Low |
| **Retention violation:** Data not deleted after expiry | Medium | Medium | Automated prune job; audit trail — ⚠️ Prune-Job existiert im Repo nicht (C-08) | Medium |
| **Unauthorized international transfer:** Data moved to non-EU region | Low (with constraints) | Critical | Terraform enforcement; subprocessor audit | Low — ⚠️ UNKLAR: Terraform-Enforcement ist im Repo nicht implementiert (nur Platzhalter-Ordner, Stand 2026-09-25); Bewertung „Low“ derzeit nicht belegt (C-08) |
| **Studio-KI: Übermittlung an LLM-Anbieter** (ergänzt 2026-09-25) | im Code-Stand PR #478 sehr gering (Egress technisch gesperrt) | High | Default-deny-Egress-Gate, Payload-Scanner, Datenklassen-Policy, Vier-Augen-Review – Details und Pfade in Abschnitt 11.4 | Low, solange der Egress gesperrt bleibt; nach einer Öffnung offen (R-KI-2 bis R-KI-6 in Abschnitt 11.7; C-21 bis C-23) |

---

## 6. Mitigation Measures

### 6.1 Technical Measures

| Measure | Implementation |
|---|---|
| **Encryption at rest** | AES-256; keys managed by AWS KMS / Azure Key Vault |
| **Encryption in transit** | TLS 1.3; certificate pinning for critical endpoints |
| **Access control** | RBAC; MFA for sensitive operations |
| **Pseudonymization** | User IDs hashed with org-specific salt |
| **Data minimization** | Only necessary fields exposed; row-level security (RLS) |
| **Audit logging** | Immutable log of all data access/modifications; 1-year retention |
| **Network isolation** | Private subnets; API gateway for external access |
| **Kundenverwaltete Schlüssel (Option, Fabric/Power BI)** | Workspace-CMK für OneLake-Items, BYOK auf Kapazitätsebene für Import-Semantikmodelle; Entscheidung des Kunden, Verfahren und Grenzen in Abschnitt 12.1 (ergänzt 2026-10-01, C-24) |
| **Supportzugriff Microsoft (Option)** | Customer Lockbox: Zugriff eines Microsoft-Technikers auf Kundendaten nur nach Freigabe; Abschnitt 12.2 (ergänzt 2026-10-01, C-24) |
| **KI-Zugriff je Semantikmodell** | Modelleinstellung „Allow any person with only read permissions to use AI …“, ab Werk an, nicht vererbt; Abschnitt 12.3 (ergänzt 2026-10-01, C-25) |
| **KI-Clients über Fabric IQ MCP** | Zustimmungsrichtlinie des Tenants für die drei delegierten Berechtigungen, Modelleinstellung je Semantikmodell; Label-DLP auf Copilot erst ab Microsoft 365 E5; Abschnitt 12.4 (ergänzt 2026-10-01, C-26) |
| **Exportwege Fabric/Power BI** | Tenant-Einstellungen „Export to Excel“, „Users can work with semantic models in Excel using a live connection“, „Export to .csv“, „Download reports“; CSV ohne Label nur für eine Sicherheitsgruppe, wenn Labels genutzt werden; Quelle Learn `fabric/admin/service-admin-portal-export-sharing`, `power-bi/visuals/power-bi-visualization-export-data`, gelesen 2026-10-01 (C-27, ADR-0023) |
| **Automated deletion** | Nightly prune job: `tooling/generator/maintenance/prune_expired_rows.py` — ⚠️ Datei existiert im Repo nicht (Stand 2026-09-25, C-08) |

### 6.2 Organizational Measures

| Measure | Implementation |
|---|---|
| **DPA (Data Processing Agreement)** | Art. 28 DSGVO compliant with all processors |
| **Data protection training** | Annual DSGVO training for all data-access personnel |
| **Incident response plan** | Breach detection and reporting: Meldung durch den Verantwortlichen an die Aufsichtsbehörde unverzüglich und möglichst binnen 72 Stunden (Art. 33 Abs. 1); ein Auftragsverarbeiter meldet dem Verantwortlichen unverzüglich (Art. 33 Abs. 2)[^1]. Die 72-Stunden-Frist betrifft die Meldung, nicht die Behebung. (Korrigiert 2026-09-25) |
| **Data subject access requests (DSARs)** | Process for data export, deletion, rectification (Art. 12–22) |
| **Privacy by design** | DPIA review before rollout of new use cases |
| **Third-party audits** | Annual SOC 2 or ISO 27001 audit |
| **Vendor management** | Subprocessor list maintained; changes approved by DPO |

---

## 7. Residual Risk

After implementing the measures above, the following residual risks remain:

### 7.1 Insider Threat

**Risk:** Malicious employee exports data and combines with external datasets to re-identify users

**Mitigation:** Key separation, RBAC, continuous monitoring, cryptographic hashing

**Remaining exposure:** Data subjects cannot be fully assured of protection from determined, sophisticated adversaries

⚠️ TO BE COMPLETED BY LEGAL: Assess tolerance for this risk. If unacceptable, consider additional measures (complete anonymization, reduced retention, granular controls).

### 7.2 Subprocessor Data Breach

**Risk:** Third-party cloud provider suffers breach, exposing encrypted data (decryptable in future)

**Mitigation:** At-rest + in-transit encryption; keys held outside processor; EU-only subprocessors; audit contracts

**Remaining exposure:** No system is breach-proof; customers should assume non-zero probability over retention periods

⚠️ TO BE COMPLETED BY LEGAL: Confirm risk tolerance and whether to inform customers of residual breach risk.

### 7.3 Re-identification via Machine Learning

**Risk:** Aggregated statistics could be inverted using ML to infer individual attributes

**Mitigation:** Minimum cohort size (n ≥ 5); differential privacy on sensitive metrics; access controls

**Remaining exposure:** Determined actors could potentially re-identify individuals from summary statistics

⚠️ TO BE COMPLETED BY LEGAL: Determine if differential privacy is required for all public aggregates or only sensitive KPIs.

---

## 8. DPO Sign-Off

⚠️ TO BE COMPLETED BY LEGAL:

- [ ] DPO has reviewed and confirms alignment with DSGVO Art. 5 (lawfulness, fairness, transparency, purpose limitation, data minimization, accuracy, integrity/confidentiality, accountability)
- [ ] DPO confirms all identified risks have been assessed and controls are proportionate
- [ ] DPO confirms supervisory authority consultation is NOT required under Art. 36(1) DSGVO (korrigiert 2026-09-25: Art. 36 Abs. 4 betrifft die Konsultation durch Mitgliedstaaten bei Gesetzgebungsvorhaben)[^1]
- [ ] DPO has confirmed retention policy complies with Art. 5(1)(e) (storage limitation)

| Field | Value |
|---|---|
| **DPO Name** | (to be completed by legal team) |
| **DPO Contact** | (to be completed by legal team) |
| **Review Date** | (to be completed by legal team) |
| **Signature** | (to be completed by legal team) |
| **Next Review Date** | (to be completed by legal team) |

---

## 9. Review Checklist (Legal/DPO)

- [ ] **Scope confirmed:** All personal data processing activities are identified
- [ ] **Data categories classified:** Direct identifiers, quasi-identifiers, special categories explicitly listed
- [ ] **Legal basis established:** Each activity has documented Art. 6 basis (consent, contract, legal obligation, etc.)
- [ ] **Risk assessment complete:** Likelihood, impact, and residual risk scores documented
- [ ] **Mitigating controls verified:** Technical and organizational measures are in place
- [ ] **Residual risks accepted:** DPO and business stakeholders agree remaining risks are acceptable
- [ ] **DPO sign-off obtained:** DPO signature and approval date recorded
- [ ] **DPIA outcome communicated:** Outcome shared with controllers/processors and relevant stakeholders

---

## 10. Offene Punkte (Durchsicht 2026-09-25)

Diese DSFA deckt die Verarbeitungen 4.1–4.3 ab, seit 2026-09-25 außerdem die Studio-KI in Abschnitt 11 (teilweise, ohne Legal-Sign-off). Die folgenden Verarbeitungen im heutigen Repo sind **nicht** bewertet. Sie werden hier nicht ergänzt, sondern als Lücke geführt (IDs = Ledger in `_INDEX.md`):

- **C-01 Studio-KI / LLM-Anbieter:** Am 2026-09-25 teilweise bearbeitet, siehe **Abschnitt 11** (Datenfluss, Empfänger, Kontrollen, Risiken; Code-Stand PR #478). Offen sind weiterhin Rechtsgrundlage, konkrete Anbieter- und Regionswahl, Transfergrundlage und Löschfristen (C-21, C-22, C-23). Die DSK-Muss-Liste nach Art. 35 Abs. 4 DSGVO nennt unter Nr. 11 den „Einsatz von künstlicher Intelligenz zur Verarbeitung personenbezogener Daten zur Steuerung der Interaktion mit den Betroffenen oder zur Bewertung persönlicher Aspekte“[^2]. Ob dieser Tatbestand erfüllt ist, entscheidet Legal/DSB (C-12). Die Fakten dazu stehen in Abschnitt 11.6.
- **C-02 LLM-Telemetrie:** Der Inhalt ist teilweise geklärt (Abschnitt 11.5), die Löschfrist ist offen.
- **C-03 Studio-Benutzer-/Org-/Audit-Daten**, **C-04 SAP-Konnektor**, **C-05 Project Runner / agentic loop**, **C-06 Fabric-Export/Tenant-Settings:** nicht in Scope; Datenkategorien und Risiken sind nicht bewertet.
- **C-24 Schlüssel und Customer Lockbox, C-25 KI-Zugriff je Semantikmodell (ergänzt 2026-10-01):** Optionen der Kundenplattform Fabric/Power BI in **Abschnitt 12**, mit Learn-Quellen. Offen sind die Entscheidung des Kunden je Option und die Bewertung durch Legal/DSB; C-06 bleibt davon unberührt offen.
- **C-07 Rolle:** Abschnitt 2 ist offen (Verantwortlicher oder Auftragsverarbeiter). Davon hängt ab, wer die DSFA für Kundendaten schuldet.
- **C-11 EU AI Act:** Die Transparenzpflichten nach Art. 50 VO (EU) 2024/1689 gelten seit 02.08.2026. Art. 4 wurde durch VO (EU) 2026/1744 geändert. Die Einordnung der Studio-KI ist nicht vorgenommen; die Fakten aus dem Code stehen in Abschnitt 11.8. Quellen siehe README.md, „Rechtsstand-Abgleich“.

[^1]: DSGVO (EUR-Lex): https://eur-lex.europa.eu/eli/reg/2016/679/oj/deu — Wortlaut Art. 33 und 36 abgeglichen über https://dsgvo-gesetz.de/art-33-dsgvo/ und https://dsgvo-gesetz.de/art-36-dsgvo/
[^2]: DSK, Liste der Verarbeitungstätigkeiten, für die eine DSFA durchzuführen ist, Version 1.1 vom 17.10.2018: https://www.datenschutzkonferenz-online.de/media/ah/20181017_ah_DSK_DSFA_Muss-Liste_Version_1.1_Deutsch.pdf

---

## 11. Studio-KI: Übermittlung an LLM-Anbieter (C-01, C-02, C-11, C-12; Stand 2026-09-25)

Dieser Abschnitt beschreibt die Verarbeitung systematisch (Art. 35 Abs. 7 lit. a DSGVO). Er ist aus dem Code abgeleitet, nicht aus Anbieterverträgen, und ersetzt keine Bewertung durch Legal/DSB. Die zugehörigen Einträge im VVT sind ACT-006 und ACT-007 (`data_processing_record.md`, Abschnitte 2.7 und 2.8).

### 11.1 Geltung und Legende

- **Code-Stand:** PR #478 „Govern AI data handling and contain model egress“, **noch nicht gemergt**. Alle Aussagen gelten nur für diesen Stand. Wird ein anderer Stand ausgeliefert, ist dieser Abschnitt neu zu prüfen.
- **[Code]** = im Code erzwungen · **[Konfig]** = konfigurierbar (Kunde/Projekt/Admin) · **[Doku]** = nur dokumentiert oder deklariert, technisch nicht erzwungen · **⚠️ UNKLAR** = aus dem Code nicht belegbar.
- **Kernbefund [Code]:** In diesem Stand verlässt **keine** Anfrage der Studio-KI den Server in Richtung eines LLM-Anbieters. Alle fünf Aufrufstellen rufen zuerst `requireApprovedAiEgress` auf (`studio/src/lib/ai/egress-gate.ts`), also bevor ein Modell aufgelöst oder ein API-Schlüssel gelesen wird. Das Gate übergibt immer `approvalGranted: false`, deshalb endet jede Anfrage mit `block`. Die Antwort ist HTTP 403 `AI_EGRESS_NOT_APPROVED`; nur der Factsheet-Entwurf liefert stattdessen ein deterministisches Ersatzergebnis (`engine: 'deterministic'`, `aiStatus: 'not-approved'`). Weder ein Konfigurationsschalter noch ein Freigabeweg ändert das. Eine Öffnung setzt eine Code-Änderung voraus.

### 11.2 Übermittlungsstellen und Eingaben

Die folgenden Daten würden nach einer Öffnung an den Anbieter gehen. Heute werden sie nur serverseitig gescannt und gehasht (siehe 11.4).

| Funktion | Route (Datei) | Zugriff [Code] | Inhalt des Modell-Payloads | Mögliche personenbezogene Daten |
|---|---|---|---|---|
| KI-Chat (Discovery, projektlos) | `studio/src/app/api/ai/chat/route.ts`, Task-Rolle `source-discovery` | angemeldeter Nutzer (`requireAuth`) | System-Prompt; Chat-Nachrichten (Freitext); optional ein vom Client übergebener `context`-String („Source Context“); optional Entity-Kontext aus Core-Artefakten (`studio/src/lib/ai/context-builder.ts`: KPI-ID, Name, Zweck, Definition, Grain, Einheit, DAX-Ausdruck gekürzt auf 200 Zeichen, Factsheet-Zweck, Business Questions); Tools (`studio/src/lib/ai/tools/discovery-tools.ts`), deren Ergebnisse an das Modell zurückgingen (KPI-Katalog inkl. DAX, Bracket- und Action-Code-Metadaten) | Freitext der Studio-Nutzer; Inhalt des `context`-Strings. Ob Core-Artefakte personenbezogene Daten enthalten: ⚠️ UNKLAR (im Code nur Rollenbezeichnungen, keine Personen) |
| Wizard (KPI, Bracket, Action, Source) | `studio/src/app/api/ai/wizard/route.ts`, Task-Rollen `kpi-draft`, `bracket-synthesis`, `action-draft`, `source-discovery` | angemeldeter Nutzer | System-Prompt und Freitext-Prompt; max. 512 Ausgabe-Tokens | Freitext der Studio-Nutzer |
| Factsheet-Entwurf | `studio/src/app/api/ai/factsheet-draft/route.ts`, Task-Rolle `documentation` | angemeldeter Nutzer | System-Prompt und Freitext-Prompt | Freitext der Studio-Nutzer |
| Abgleich Factsheet/Bracket (`mode: reconcile`) | dieselbe Datei, Task-Rolle `bracket-synthesis` | angemeldeter Nutzer | Factsheet-Prosa und Bracket-YAML (je die ersten 4000 Zeichen), Längen, Änderungshinweis, deterministische Hinweise | Inhalt von Factsheets; ob personenbezogen: ⚠️ UNKLAR |
| Discovery-Chat (projektgebunden) | `studio/src/app/api/projects/[projectId]/discovery/chat/route.ts`, Task-Rolle `source-discovery` | Projektrolle `editor` (`requireRole`); Anfragen über 12 MiB werden abgewiesen (413) | System-Prompt mit dem **vollständigen Inhalt aller übergebenen Quellen** (ID, Name, Inhalt) sowie die Chat-Nachrichten | Inhalt eingebrachter Projektdokumente („Source evidence“). Er kann beliebige personenbezogene Daten Dritter enthalten, z. B. Namen oder Kontaktdaten in Protokollen und Konzepten. Welche Dokumente Kunden einbringen: ⚠️ UNKLAR |

- Die Identität des Nutzers (E-Mail) ist **nicht** Teil des Modell-Payloads [Code]. Sie wird nur als `actor` im Audit-Nachweis gespeichert (11.5).
- `studio/src/app/api/ai/wizard/save/route.ts` ruft kein Modell auf. Die Route speichert nur einen vom Nutzer bestätigten Entwurf.
- Weitere Aufrufer von `resolveServerModel`, `generateText` oder `streamText` gibt es in `studio/src/` nicht (Codesuche 2026-09-25). Für KI-Nutzung außerhalb von Studio siehe C-05.

### 11.3 Empfänger: Anbieter, Modelle, Endpunkte, Region

| Merkmal | Befund | Art |
|---|---|---|
| Mögliche Anbieter | `anthropic`, `google`, `openai`; angebunden über `@ai-sdk/anthropic`, `@ai-sdk/google` (`createGoogleGenerativeAI`) und `@ai-sdk/openai` in `studio/src/lib/ai/orchestrator.ts` | [Code] |
| Auswahl | Gewählt wird der erste Anbieter in `preferenceOrder` (L0: anthropic → google → openai), der erlaubt ist, die Residenzvorgabe erfüllt **und** einen API-Schlüssel hat (`ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`/`GEMINI_API_KEY`, `OPENAI_API_KEY`); siehe `studio/src/lib/ai/config/route-model.ts` | [Code] Logik, [Konfig] Schlüssel |
| Modelle (L0) | `claude-haiku-4-5-20251001`, `claude-sonnet-4-6`, `claude-opus-4-8`; `gemini-2.0-flash`; `gpt-4o-mini`, `gpt-4o`. Die Zuordnung erfolgt nach Fähigkeitsrolle (`studio/src/lib/ai/config/defaults.ts`). Die Google- und OpenAI-IDs sind laut Code-Kommentar nicht verifiziert | [Code] |
| Endpunkt | Kein `baseURL` gesetzt, es gelten die Standard-Endpunkte der SDKs. Welche Hosts und Rechenzentren das sind: ⚠️ UNKLAR (steht nicht im Code) | [Code] |
| Region/Residenz | `PROVIDER_RESIDENCY` ist für alle drei Anbieter `['any']`, der Code sichert also **keine** EU-Verarbeitung zu. Setzt ein Kunde über L1/L2 `dataResidency: 'eu-only'`, erfüllt kein Anbieter die Vorgabe: `chooseModel` liefert `null`, und die KI bleibt aus (Fail-closed) | [Code] |
| Kundenschichten L1/L2 | Freigegebene Kunden- und Domänenschichten können L0 nur verschärfen (`allowedProviders` als Schnittmenge, `dataResidency` clamp-strict; `studio/src/lib/ai/config/resolve.ts`). Freigeben kann nur die Admin-Rolle (`studio/src/lib/ai/config/governance-types.ts`) | [Konfig] |
| Projektgebundene Route | Das Project-Package-Modul `ai_data_handling` (`tooling/generator/schemas/project_ai_data_handling.schema.json`) verlangt je Route `provider_region`, `provider_geography` (`eu`/`us`/`local`/`other`), `credential_ref` (`secret://…`), `provider_terms_evidence_refs` und `expires_at` | [Konfig], nur Entscheidungsgrundlage, keine Freigabe |
| Speicherung und Training beim Anbieter | Die Policy verlangt `provider_training_allowed: false` und einen expliziten Wert für `prompt_retention_days` (`studio/src/lib/ai/data-handling-policy.ts`). Beides sind **deklarierte** Bedingungen. Ob der Anbieter sie vertraglich und tatsächlich einhält, prüft der Code nicht | [Doku] |
| Lokales Modell | Die Policy kennt die Grenze `local` mit internem Endpunkt, der Orchestrator unterstützt aber nur `anthropic`, `google` und `openai`. Ein lokales Modell ist in diesem Stand nicht nutzbar | [Code] |

### 11.4 Kontrollen (Maßnahmen nach Art. 25, 32 DSGVO)

| Kontrolle | Wirkung | Art | Fundstelle |
|---|---|---|---|
| Default-deny-Egress-Gate | Jede KI-Route wird vor der Modellauflösung blockiert (403 oder deterministischer Ersatz); `approvalGranted` ist fest `false` | [Code] | `studio/src/lib/ai/egress-gate.ts` |
| Fail-closed bei Nachweis-Fehler | Lässt sich der Audit-Nachweis nicht speichern, antwortet die Route mit 503 `AI_EGRESS_AUDIT_FAILED`; es wird nichts verarbeitet | [Code] | `studio/src/lib/ai/egress-gate.ts` |
| Datenklassen-Policy | `unknown`, `restricted` und `secret` erreichen nie ein Modell. `customer_confidential` geht nie an `external_cloud`. Nicht-öffentliche Daten gehen nur als `redacted: true` an `external_cloud`. `customer_managed_cloud` braucht einen Nachweis-Verweis. `local` ist nur mit Provider `local`/`mock` und internem Endpunkt zulässig (RFC 1918, Loopback, `.internal` u. a.). Training muss ausgeschlossen, Aufbewahrung und Redaktionspflicht müssen explizit gesetzt sein | [Code] (Evaluator) | `studio/src/lib/ai/data-handling-policy.ts`; Testvektoren `core/fixtures/neutral/ai-data-handling-policy/` |
| Wirksamer Policy-Kontext heute | Keine Route übergibt `profile` oder `context`. Das Gate nutzt daher sein Default-Profil (Provider `unresolved`, Klasse `unknown`), sodass zusätzlich zur fehlenden Freigabe auch die Policy blockiert | [Code] | `studio/src/lib/ai/egress-gate.ts` |
| Payload-Scanner (Preflight) | Erkennt Secrets (Private Key, Bearer, JWT, Zuweisungen wie `api_key=`), E-Mail, Telefonnummer, IBAN (mit Prüfsumme), UUID, Home-Verzeichnispfade und kundenspezifische Sperrbegriffe. Blockiert bei jedem Secret, bei **jedem** Fund an `external_cloud` und ab 1 MiB Payload (Standard). Die Allowlist maskiert nur Nicht-Secrets. Der Scanner **erkennt und blockiert, redigiert aber nicht** | [Code]; Sperrbegriffe, Allowlist und Größenlimit [Konfig] (`scan_policy`) | `studio/src/lib/ai/egress-preflight.ts`; Testvektoren `core/fixtures/neutral/ai-egress-preflight/` |
| Inhaltsfreier Nachweis | Gespeichert werden SHA-256 und Größe des Payloads, Klasse, Form, Zweck, Grenze, Provider, Modell, Fundzahlen je Kategorie, Regel-IDs und Blockgründe. Nachweise mit den Feldern `payload`, `prompt`, `system`, `user`, `matches` oder `redacted_text` werden abgewiesen | [Code] | `studio/src/lib/ai/egress-preflight.ts` (`persistAiEgressEvidence`) |
| Manipulationsnachweis | Audit-Ereignisse werden verkettet (`chainEvent`). Laut Design-Doku ist das lokale Manipulationsevidenz, kein externes WORM-Log | [Code] / [Doku] | `studio/src/lib/db/audit-repo.ts`; `studio/docs/design/AI_POLICY_REVIEW.md` |
| AI-Policy-Review (Vier-Augen) | Einreichen mit Rolle `editor`, Entscheidung mit Rolle `admin`; wer einreicht, darf nicht freigeben. Gebunden an Paket-Revision und Routen-Hash; geprüft werden Ablaufdatum, Provider-Region/-Geografie und Nachweise; Begründung 20–2000 Zeichen. Die Antwort enthält immer `egressEnabled: false`, **eine Freigabe öffnet keinen Egress** | [Code] | `studio/src/lib/ai/policy-review.ts`, `studio/src/lib/db/ai-policy-review-repo.ts`, `studio/src/app/api/projects/[projectId]/ai-policy-reviews/route.ts` |
| Menschliche Prüfung der Ausgaben | Die System-Prompts verlangen Entwürfe („Do not claim approval or create or change governed definitions“, „Never auto-merge silently — patch must be reviewable“). Gespeichert wird nur über die separate Route `wizard/save` | [Doku] (Prompt) / [Code] (separate Route) | Routen in 11.2 |
| Prüfung von Ausgaben und Tool-Ergebnissen, Redaktion | **Nicht vorhanden.** Gestreamte Modellausgaben und Tool-Ergebnisse durchlaufen keinen Scanner; im Preflight-Payload des KI-Chats stehen nur die Tool-**Namen**. Die Design-Doku führt das als Voraussetzung vor jeder Öffnung | — | `studio/docs/design/AI_POLICY_REVIEW.md` („Explicit non-claims“) → C-23 |

### 11.5 Protokollierung und Aufbewahrung

| Speicher | Inhalt (personenbezogene Daten **fett**) | Wann geschrieben | Löschung/Aufbewahrung |
|---|---|---|---|
| `audit_events`, `entity_type = 'ai_egress'` | Nachweis wie in 11.4 (ohne Inhalt), **`actor` = E-Mail des Nutzers**, `project_id` (bei projektlosen Routen `default`), Zeitstempel | bei **jedem** KI-Aufruf, auch bei Blockierung | Der Code hat keine Löschfunktion (`studio/src/lib/db/audit-repo.ts`: nur Insert und Select), und die Verkettung spricht gegen Einzellöschung. Frist: ⚠️ UNKLAR / keine (C-22, vgl. C-15) |
| `ai_policy_reviews` sowie `audit_events` (`ai_policy_review`) | Revision, Routen-Hash, Status, **`submitted_by` und `reviewed_by` (E-Mail)**, Zeitstempel, **Begründung (Freitext)** | beim Einreichen und bei der Entscheidung | Keine Löschfunktion im Code. Frist: ⚠️ UNKLAR (C-22) |
| `llm_step_events` (LLM-Telemetrie, C-02) | Laut `studio/src/lib/ai/telemetry.ts`: Projekt-, Use-Case- und Domänen-ID, Task-/Fähigkeitsrolle, Provider, Modell, Token-Zahlen, Latenz, Erfolg, **Fehlertext** (nur der Wizard übergibt die SDK-Fehlermeldung), Kosten, Preistabellenversion, rohes Usage-Objekt. **Kein** Prompt- oder Antwortinhalt, kein Nutzerfeld | nur **nach** einem Modellaufruf, in diesem Stand also nie | Tabellenschema und Frist liegen in `studio/src/lib/db/llm-events-repo.ts`, das im geprüften Teilabbild fehlt → ⚠️ UNKLAR. `telemetry.redactPII` und `sampleRate` (L0) werden in `telemetry.ts` nicht ausgewertet; ob das Repository sie auswertet: ⚠️ UNKLAR |
| Beim LLM-Anbieter | Prompt und Antwort | erst nach einer Öffnung | Nur deklariert (`prompt_retention_days`). Die tatsächliche Frist hängt vom Anbietervertrag ab → ⚠️ UNKLAR (C-21) |

- `payload_sha256` ist ein Hash des Inhalts. Bei kurzen, erratbaren Eingaben ließe sich damit ein vermuteter Inhalt bestätigen. Er ist daher als pseudonymes, nicht als anonymes Datum zu behandeln (Einschätzung; Bewertung durch Legal).

### 11.6 Schwellwertanalyse zur DSFA-Pflicht (C-12): Fakten aus dem Code

- **Zweck:** Hilfe beim Erstellen von Analytics-Definitionen (KPI, Bracket, Action Code, Factsheet) und beim Auswerten von Projektdokumenten. Der Code enthält keine Bewertung von Personen, kein Scoring, kein Profiling und keine automatisierte Entscheidung mit Wirkung für Betroffene. Die Ausgaben sind Entwürfe, die ein Mensch übernimmt.
- **Personenbezug:** nicht Ziel der Verarbeitung, aber möglich, etwa im Freitext der Nutzer und vor allem in Quelldokumenten im Discovery-Chat. Art und Umfang hängen vom Kunden ab (⚠️ UNKLAR). Art.-9-Daten sind technisch nicht ausgeschlossen, weil der Scanner nur die Muster aus 11.4 erkennt.
- **Interaktion:** KI-Chat und Discovery-Chat interagieren mit Studio-Nutzern, also mit Beschäftigten von Kunde oder Betreiber.
- **Neue Technologie und Drittlandbezug:** Es kommen externe Sprachmodelle von US-Anbietern ohne zugesicherte EU-Residenz in Betracht (11.3).
- **Einordnung:** Ob DSK-Muss-Liste Nr. 11 oder Art. 35 Abs. 1/3 greift, entscheidet Legal/DSB. Vorsorglich ist die Verarbeitung in diesem Abschnitt bereits nach Art. 35 Abs. 7 beschrieben.

### 11.7 Risiken und Restrisiko (Vorschlag; Bewertung durch Legal/DSB)

| Risiko | Eintritt | Schwere | Maßnahme (Code) | Restrisiko |
|---|---|---|---|---|
| **R-KI-1** Personenbezogene oder vertrauliche Daten gehen ungewollt an einen LLM-Anbieter | im Code-Stand PR #478: sehr gering | Hoch | Default-deny-Gate, Fail-closed, Policy-Evaluator (11.4) | **Niedrig**, solange PR #478 unverändert ausgeliefert wird. Eine Code-Änderung kann das Gate entfernen, und davor schützt nur das Change-Control (⚠️ ein Pflicht-Review für diese Dateien ist im Repo nicht belegt) |
| **R-KI-2** Drittlandübermittlung (USA) nach einer Öffnung | nach Öffnung: hoch | Hoch | `eu-only` führt zu „kein Anbieter“ (Fail-closed); eine Project-Package-Route verlangt `provider_region`/`provider_geography` | **Offen, hoch:** kein EU-Endpunkt im Code; Transfergrundlage (DPF/SCC) fehlt (C-20, C-21) |
| **R-KI-3** Scanner übersieht personenbezogene Daten (Namen, Anschriften, Freitext, Art.-9-Angaben) | nach Öffnung: mittel | Mittel bis hoch | Scanner (nur Muster), Sperrbegriffe [Konfig], Policy „nicht-öffentlich nur redigiert“ | **Mittel:** keine Redaktion, keine Namenserkennung; `redacted` setzt heute keine Route (C-23) |
| **R-KI-4** Tool-Ergebnisse und Modellausgaben bleiben ungeprüft | nach Öffnung: mittel | Mittel | keine | **Offen** (C-23) |
| **R-KI-5** Anbieter speichert Prompts oder trainiert damit | nach Öffnung: unbekannt | Hoch | nur deklariert (`provider_training_allowed: false`, `prompt_retention_days`) | **Offen:** hängt von Anbietervertrag und Nachweisen ab (C-21) |
| **R-KI-6** Nachweis- und Review-Protokolle (E-Mail, Begründung) werden unbefristet gespeichert | sicher (bei jedem Aufruf) | Niedrig bis mittel | Nachweis ohne Inhalt (Inhaltsfelder werden abgewiesen) | **Mittel:** keine Löschregel (C-22) |
| **R-KI-7** Freigabe durch eine Einzelperson oder ohne Nachweis | gering | Mittel | Vier-Augen-Prinzip, Rollenprüfung, Bindung an Revision und Hash, Ablaufdatum; eine Freigabe öffnet keinen Egress | **Niedrig** (Härtung von Identität und Session laut Design-Doku separat, vgl. C-16) |

⚠️ TO BE COMPLETED BY LEGAL: Rechtsgrundlage (Art. 6) für ACT-006, Rollenverteilung (C-07) und Tragbarkeit der Restrisiken R-KI-2 bis R-KI-6. Das muss **vor** einer Öffnung des Egress geklärt sein.

### 11.8 EU AI Act (C-11): Fakten aus dem Code

Die rechtliche Einordnung (Anbieter oder Betreiber, Risikoklasse, Transparenzpflichten) nimmt Legal vor. Der Code liefert dafür:

- **Modelle:** Allzweckmodelle Dritter (Anthropic Claude, Google Gemini, OpenAI GPT; 11.3), per API eingebunden. In den geprüften Dateien gibt es keinen Trainings- oder Fine-Tuning-Code.
- **Funktion:** Textgenerierung von Entwürfen (KPI, Bracket, Action, Source, Factsheet, Abgleichs-Patch) und Chat mit Studio-Nutzern. Das ist relevant für Art. 50 Abs. 1 (Interaktion mit natürlichen Personen) und Art. 50 Abs. 2 (synthetische Textausgaben).
- **Kennzeichnung:** Die Factsheet-Route liefert `engine: 'ai' | 'deterministic'`. Ob die Oberfläche KI-Ausgaben für Nutzer kennzeichnet: ⚠️ UNKLAR (UI-Komponenten nicht geprüft).
- **Hochrisiko-Bezug:** Im Code gibt es keinen Hinweis auf Zwecke nach Anhang III (z. B. Beschäftigung, Kreditwürdigkeit). Das ist eine Beobachtung, keine Einordnung.
- **Betriebszustand:** In diesem Code-Stand ist jede Modellübermittlung gesperrt (11.1). Ob das für das „Inverkehrbringen/Inbetriebnehmen“ eine Rolle spielt, bewertet Legal.

---

## 12. Kundenplattform Microsoft Fabric / Power BI: Schlüssel, Supportzugriff, KI-Zugriff (C-24, C-25; Stand 2026-10-01)

Dieser Abschnitt beschreibt **Optionen**, die der Kunde auf seiner Fabric-/Power-BI-Plattform wählt. ALUCA liefert Semantikmodelle und Berichte in diese Plattform; eingeschaltet wird keine der Optionen durch ALUCA. Alle Plattformaussagen sind gegen Microsoft Learn gelesen am 01.10.2026 (Quelle je Unterabschnitt). Was dort nicht steht, ist als ⚠️ UNKLAR oder **ANNAHME, ungeprüft** markiert. Ob eine Option für eine konkrete Verarbeitung als Maßnahme nach Art. 25 oder 32 DSGVO erforderlich ist, bewertet Legal/DSB. Das gilt auch für die Frage, ob sie als zusätzliche Maßnahme bei Übermittlungen (Abschnitt 4.3 der Hosting-Doku) taugt. Zusammenhang: C-06 (Microsoft als Empfänger nicht erfasst).

### 12.1 Kundenverwaltete Schlüssel (Option)

Ab Werk verschlüsselt Fabric alle ruhenden Daten mit Microsoft-verwalteten Schlüsseln. Es gibt zwei kundenseitige Schlüsselwege, und sie decken **verschiedene** Items ab:

| Weg | Deckt ab | Ebene | Wichtige Grenzen |
|---|---|---|---|
| **Workspace-CMK** | Lakehouse, Warehouse, Notebook, Environment, Spark Job Definition, API for GraphQL, ML model, Experiment, Pipeline, Dataflow, Copy job, Industry solutions, SQL Database, Mirrored Database, Eventhouse (Preview), Graph; damit alle OneLake-Daten des Workspace | Workspace | Tenant-Einstellung „Apply customer-managed keys“ muss an sein; Key Vault oder Managed HSM mit Soft-Delete **und** Purge-Schutz; RSA/RSA-HSM 2.048, 3.072 oder 4.096 Bit (SQL Database: kein 4.096), nur versionslose Schlüssel; nicht auf Trial-Kapazität; Mirrored Dataverse und Mirrored Azure Databricks Catalog nicht in CMK-Workspaces; einige Metadaten (Pipeline/Copy job, ML-Modell, Umgebungsbibliotheken) bleiben ohne CMK |
| **BYOK (Power BI)** | in Semantikmodelle **importierte** Daten | Kapazität | Aktivierung per PowerShell auf Tenant-Ebene, **nicht rückgängig zu machen**; nicht für Push-, Streaming-, Live-Connection-Modelle und hochgeladene Excel-/CSV-Dateien |

Folgen für ALUCA-Lieferungen:

- **Direct Lake:** Die Daten liegen in OneLake, nicht im Semantikmodell (Learn `fabric/security/power-bi-security`, Tabelle „Data Persisted in Power BI“: DirectLake „No“). Sie schützt also der Workspace-CMK des Lakehouse-Workspace, nicht BYOK.
- **Import:** Den Schutz der Modelldaten liefert BYOK der Kapazität, nicht der Workspace-CMK (Learn `fabric/security/security-scenario`: „Capacity-level BYOK encrypts Power BI semantic models, while workspace-level CMK encrypts other Fabric items“).
- **Workspace-Schnitt:** Semantikmodelle und Berichte stehen nicht in der Liste der CMK-fähigen Items. Learn sagt, die Funktion lasse sich nicht einschalten, solange der Workspace nicht unterstützte Items enthält, und danach ließen sich nur unterstützte Items anlegen. Nach diesem Wortlaut gehören Modelle und Berichte in einen Workspace ohne CMK. Diese Lesart ist **ANNAHME, ungeprüft** (im Tenant nicht gemessen).
- **Widerruf:** Wird der Schlüssel im Key Vault widerrufen, scheitern Lese- und Schreibzugriffe auf den CMK-Workspace binnen 60 Minuten; BYOK-Daten werden für den Dienst binnen 30 Minuten unlesbar. SQL Database prüft den Schlüssel nach einer Wiederherstellung nicht von selbst neu.
- **Nachweis:** Audit-Ereignisse `ApplyWorkspaceEncryption`, `DisableWorkspaceEncryption`, `GetWorkspaceEncryption`. Workspace-Admins setzen den CMK im Portal oder über die APIs Assign/Get/Reset Workspace Encryption.

Quellen (gelesen 01.10.2026): Learn `fabric/security/security-overview` (Abschnitt „Secure Data“), `fabric/security/workspace-customer-managed-keys`, `fabric/security/security-scenario` (Abschnitt „Data handling“), `fabric/enterprise/powerbi/service-encryption-byok`, `fabric/security/power-bi-security`.

⚠️ TO BE COMPLETED BY LEGAL: ob für die Verarbeitungen 4.1–4.3 kundenverwaltete Schlüssel verlangt werden. Bei Microsoft-verwalteten Schlüsseln bleibt die Zeile „Encryption at rest“ in 6.1 die geltende Maßnahme.

### 12.2 Customer Lockbox (Option)

Mit Customer Lockbox for Microsoft Azure greift ein Microsoft-Techniker nur nach Freigabe des Kunden auf Kundendaten zu, wenn er einen Supportfall mit Standardwerkzeugen nicht lösen kann.

- **Einschalten:** Azure-Portal → Customer Lockbox for Microsoft Azure → Administration → Enabled; Rolle Microsoft Entra Global Administrator.
- **Freigabe:** Die Person mit aktiver Global-Administrator-Rolle erhält die Anfrage. Die Rolle muss **vor** der Anfrage aktiv sein, sonst ist die Anfrage nicht sichtbar. Bei PIM heißt das: Rolle während eines Supportfalls aktivieren. Eine Anfrage verfällt nach vier Tagen ohne Zugriff, eine Freigabe gilt standardmäßig acht Stunden.
- **Protokolle:** Azure-Aktivitätsprotokoll (Create, Approve, Deny, Expiry) und Purview-Audit (z. B. `GetRefreshHistoryViaLockbox`, `GetQueryTextTelemetryViaLockbox`).
- **Grenzen:** Keine Lockbox-Anfrage bei Notfällen außerhalb der Standardverfahren, bei zufälligem Kontakt mit Daten während der Fehlersuche und bei **behördlichen Herausgabeverlangen** („External legal demands for data“). Für die Transferbewertung (Schrems II) ersetzt Lockbox daher keine Maßnahme gegen behördlichen Zugriff.

Quelle (gelesen 01.10.2026): Learn `fabric/security/security-lockbox`.

### 12.3 KI-Zugriff je Semantikmodell (C-25)

Die Modelleinstellung „Allow any person with only read permissions to use AI (for example, Copilot, Microsoft's MCP tools) on this model and its related reports“ steht in den Einstellungen des Semantikmodells (Abschnitt **Copilot**, auf der vollständigen Einstellungsseite unter **Explore and AI access**). Schalten darf, wer Schreibrecht auf das Modell hat.

- **Ab Werk an.** Leser erreichen das Modell dann über die Copilot-Oberflächen in Power BI (Berichtsbereich, Standalone, Apps), Microsoft 365 Copilot Chat und Cowork, Data Agent und Microsofts Remote-MCP-Werkzeuge.
- **Aus** heißt: Nutzer mit reinem Leserecht erreichen das Modell über keine dieser Oberflächen. In Oberflächen mit mehreren Modellen fällt es für **alle** Nutzer aus der Suche, auch für Nutzer mit Build- und Schreibrecht; diese erreichen es weiter direkt (URL oder manuelles Anhängen).
- **Nicht vererbt.** Ein Modell, das auf einem anderen Modell aufbaut, braucht die Einstellung eigens.
- **Setzbarkeit:** Ob die Einstellung in TMDL oder über eine API setzbar ist, ist ⚠️ UNKLAR. Learn beschreibt nur die Oberfläche (gelesen 01.10.2026). ALUCA kann sie deshalb nicht generieren; sie bleibt ein Schritt nach der Veröffentlichung.

Empfehlung (Vorschlag, Entscheidung Kunde/DSB): Für jedes Modell mit personenbezogenen Daten (Abschnitt 3) vor der Freigabe an Leser entscheiden, ob KI-Zugriff erlaubt sein soll, und die Entscheidung je Modell festhalten. Für Microsoft 365 Copilot Chat schreibt Learn, die Anbindung respektiere die bestehenden Power-BI-Berechtigungen und Sicherheitskontrollen (Learn `microsoft-365/copilot/copilot-powerbi-copilot-chat`, gelesen 01.10.2026). Ob das für jede genannte Oberfläche RLS und OLS im selben Umfang einschließt, ist hier nicht geprüft (⚠️ UNKLAR). Die Copilot-Readiness-Doku (`products/fabric/powerbi/tooling/copilot_readiness/README.md`) führt den Schritt in ihrer Checkliste.

Quelle (gelesen 01.10.2026): Learn `power-bi/create-reports/copilot-semantic-models`, Abschnitt „Control Copilot access for semantic models“.

### 12.4 KI-Clients über Fabric IQ MCP und Microsoft 365 Copilot (C-26, ADR-0022)

Fabric IQ MCP ist ein entfernter, nur lesender MCP-Server von Microsoft. Jeder MCP-fähige
KI-Client (z. B. GitHub Copilot, eigene Agenten) kann darüber Power-BI-Berichte und
Semantikmodelle finden, Metadaten lesen und DAX-Abfragen ausführen. Die Abfrage läuft immer als
angemeldete Person mit deren Rechten; RLS und OLS greifen, ein Build-Recht ist nicht nötig.
Service Principals werden nicht unterstützt.

- **Neuer Abfluss:** Abfrageergebnisse gehen an den KI-Client und dessen Modellanbieter. Für
  diesen gelten dessen Bedingungen, nicht die von Microsoft Fabric. Jeder zugelassene Client ist
  deshalb ein eigener Auftragsverarbeiter bzw. Empfänger im Sinne von Art. 28 bzw. Art. 4 Nr. 9
  DSGVO und gehört in das Verzeichnis der Verarbeitungstätigkeiten des Kunden (Vorlage `data_processing_record.md`).
- **Steuerung:** Die drei delegierten Berechtigungen (`Item.Read.All`, `Item.Execute.All`,
  `Dataset.Read.All`) brauchen ab Werk keine Admin-Zustimmung. Der Tenant-Admin kann die
  Benutzerzustimmung einschränken oder einen Admin-Genehmigungsablauf verlangen. Die Einstellung
  gilt für den ganzen Endpunkt.
- **Je Modell:** Die Modelleinstellung aus 12.3 nennt „Microsoft's MCP tools“ ausdrücklich; aus
  heißt auch hier: kein Zugriff für reine Leser.
- **Microsoft 365 Copilot:** Das Gesprächslabel übernimmt das restriktivste Label der genutzten
  Power-BI-Inhalte, Exporte erben es. Eine DLP-Richtlinie kann Copilot die Verarbeitung gelabelter
  Inhalte verbieten; das setzt Microsoft 365 E5 oder die Purview-Suite voraus. Mit E3 oder Business
  Premium wirkt DLP nur auf Prompts.
- **Protokollierung:** Ob jeder MCP-Aufruf im Fabric-Aktivitätsprotokoll erscheint, ist ⚠️ UNKLAR.

Empfehlung (Vorschlag, Entscheidung Kunde/DSB): Benutzerzustimmung für Fabric IQ MCP auf
Admin-Genehmigung stellen, bis eine Liste erlaubter Clients mit Prüfung des Modellanbieters
beschlossen ist; Modelle mit personenbezogenen Daten nach 12.3 behandeln.

Quellen (gelesen 01.10.2026): Learn `fabric/iq/connectors/fabric-iq-mcp` (Abschnitt
„Authenticate“), `fabric/iq/connectors/microsoft-365-copilot-overview` (Abschnitt „Sensitivity
labels“), Microsoft Purview Service Description (Abschnitt „DLP for Microsoft Copilot“).

---

**Document prepared by:** Analytics Team  
**Legal review pending:** Yes  
**Next review date:** (to be scheduled by DPO)
