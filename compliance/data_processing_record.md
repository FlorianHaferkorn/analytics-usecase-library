# Verzeichnis von Verarbeitungstätigkeiten (Processing Activity Record)

**Regulation:** DSGVO Article 30  
**Document Type:** Processing Activity Register  
**Version:** 1.0  
**Last Updated:** 2026-04-22  
**Maintaining Team:** Data Protection Officer / Compliance

---

## 1. Overview

DSGVO Article 30 requires controllers and processors to maintain a record of processing activities (Verzeichnis von Verarbeitungstätigkeiten). This document serves as the organization's master inventory of all processing activities involving personal data.

Each row documents:

- **Who** processes the data (Controller/Processor)
- **What** personal data is involved
- **Where** the data is stored and processed
- **Why** the data is processed (legal basis)
- **When** the data is retained
- **How** the data is protected (technical and organizational measures)

This record is:

- **Kept on file** for supervisory authority inspection (Art. 30(1) DSGVO)
- **Updated quarterly** or when new processing activities commence
- **Reviewed annually** by the DPO/legal team
- **Made available to the supervisory authority** upon request (Art. 30 Abs. 4 DSGVO). Betroffene erhalten **nicht** das Verzeichnis, sondern Informationen nach Art. 13/14 DSGVO (siehe Abschnitt 5)[^1]. (Korrigiert 2026-09-25; vorher „Made available to data subjects … Art. 14“.)
- Hinweis Art. 30 Abs. 5 DSGVO: Die Ausnahme für Unternehmen unter 250 Beschäftigten greift nicht, wenn die Verarbeitung ein Risiko birgt, nicht nur gelegentlich erfolgt oder Art.-9/10-Daten betrifft[^1]. Ob sie anwendbar ist, entscheidet Legal.

⚠️ TO BE COMPLETED BY LEGAL: Confirm the DPO responsible and quarterly update process.

---

## 2. Master Processing Activity Register

### 2.1 Analytics Reporting and KPI Calculation

| Field | Value |
|---|---|
| **Activity ID** | ACT-001 |
| **Activity Name** | Analytics Reporting and KPI Calculation |
| **Description** | Ingest user action events, aggregate by cohort/segment, calculate business KPIs, publish dashboards and reports |
| **Controller** | (to be completed by legal team) |
| **Processor(s)** | AWS (storage, compute); Azure (if applicable); internal analytics team |
| **Categories of Data Subjects** | Employees, customers, end-users, audit subjects |
| **Types of Personal Data** | User IDs (pseudonymized), action outcomes, timestamps, cohort segments, IP addresses (aggregated) |
| **Legal Basis (Art. 6)** | ⚠️ TO BE COMPLETED BY LEGAL: (a) Consent / (b) Contract / (c) Legal obligation / (d) Vital interests / (e) Public task / (f) Legitimate interests |
| **Special Categories (Art. 9)** | ⚠️ TO BE COMPLETED BY LEGAL: None / Health / Ethnic / Political / Biometric / Genetic / Religious / Other |
| **Data Storage Location(s)** | AWS eu-central-1; ⚠️ UNKLAR: zweite Region – der ursprüngliche Eintrag „AWS westeurope“ ist ein Azure-Regionsname (AWS-Pendant laut eu_hosting_guarantee.md: eu-west-1); tatsächliche Region bestätigen (C-14). No transfers outside EU/EEA without a transfer mechanism (Art. 45/46 DSGVO) |
| **Retention Period** | 3 years (standard tier); 7 years (extended tier) |
| **Deletion Mechanism** | Automated nightly prune job: `tooling/generator/maintenance/prune_expired_rows.py` — ⚠️ Datei existiert im Repo nicht (Stand 2026-09-25, C-08) |
| **Recipient(s)** | Business analysts, product managers, executives (row-level security applied) |
| **Sub-processors** | AWS S3, AWS KMS, internal data pipeline |
| **DPA in Place?** | Yes – AWS Data Processing Addendum (DPA) executed |
| **Technical Measures** | AES-256 encryption; TLS 1.3; RBAC; MFA; audit logging; pseudonymization |
| **Organizational Measures** | Annual DSGVO training; NDA for data-access roles; incident response plan; quarterly access reviews |
| **DPO Assessment** | (to be completed by DPO) |
| **DPO Sign-Off Date** | (to be completed by DPO) |

---

### 2.2 Action Code Execution & Audit Trail

| Field | Value |
|---|---|
| **Activity ID** | ACT-002 |
| **Activity Name** | Action Code Execution and Audit Logging |
| **Description** | Execute machine-readable business rules; log all executions with actor, outcome, timestamp; maintain immutable audit trail |
| **Controller** | (to be completed by legal team) |
| **Processor(s)** | Internal analytics platform; AWS (storage); external audit/logging provider (if applicable) |
| **Categories of Data Subjects** | Employees (action performers), customers, audit subjects |
| **Types of Personal Data** | User ID, action performer name, action code ID, action outcome, execution timestamp, status |
| **Legal Basis (Art. 6)** | ⚠️ TO BE COMPLETED BY LEGAL: (b) Contract OR (c) Legal obligation |
| **Data Storage Location(s)** | Internal database (EU-based); AWS eu-central-1 for backup copies |
| **Retention Period** | 7 years (compliance/audit standard) |
| **Deletion Mechanism** | Legal hold for active audits; automated deletion after 7-year period |
| **Recipient(s)** | Audit committee, compliance team, legal counsel, supervisory authority (if requested) |
| **Sub-processors** | AWS RDS (backup storage), internal logging infrastructure |
| **DPA in Place?** | Yes – AWS DPA; internal policies cover employee access |
| **Technical Measures** | Database encryption (TLS); row-level security; immutable log structure; tamper-detection; daily integrity checks |
| **Organizational Measures** | Access control (DBA role only); confidentiality agreements; incident response; annual audit of log integrity |
| **DPO Assessment** | (to be completed by DPO) |
| **DPO Sign-Off Date** | (to be completed by DPO) |

---

### 2.3 Platform Maintenance & Security Monitoring

| Field | Value |
|---|---|
| **Activity ID** | ACT-003 |
| **Activity Name** | Platform Maintenance and Security Monitoring |
| **Description** | Monitor system performance, detect unauthorized access, identify security threats, maintain platform availability |
| **Controller** | (to be completed by legal team) |
| **Processor(s)** | Internal security team; AWS CloudTrail, CloudWatch; external SOC/SIEM provider (if applicable) |
| **Categories of Data Subjects** | Platform users, employees, administrators, automated systems |
| **Types of Personal Data** | IP addresses, session IDs, device fingerprints, user activity logs, authentication attempts, error logs |
| **Legal Basis (Art. 6)** | ⚠️ TO BE COMPLETED BY LEGAL: (f) Legitimate interests – protecting platform security |
| **Data Storage Location(s)** | AWS eu-central-1 (CloudTrail, CloudWatch); internal SIEM (if applicable) |
| **Retention Period** | 30 days (raw logs); 1 year (aggregated security events) |
| **Deletion Mechanism** | Automated log rotation/archival; logs deleted via lifecycle policies |
| **Recipient(s)** | Security team, platform engineering team, incident response team |
| **Sub-processors** | AWS CloudTrail, AWS CloudWatch, external SIEM/SOC (if applicable) |
| **DPA in Place?** | Yes – AWS DPA; internal security policies cover data handling |
| **Technical Measures** | Log encryption (at rest and in transit); access control; immutable log structure; automated anomaly detection |
| **Organizational Measures** | Security team training; incident response procedures; quarterly security audits |
| **DPO Assessment** | (to be completed by DPO) |
| **DPO Sign-Off Date** | (to be completed by DPO) |

---

### 2.4 Data Subject Rights Fulfillment (DSAR Processing)

| Field | Value |
|---|---|
| **Activity ID** | ACT-004 |
| **Activity Name** | Data Subject Access Requests (DSAR) Processing |
| **Description** | Respond to data subject requests for access, deletion, rectification, portability, objection (Art. 12–22) |
| **Controller** | (to be completed by legal team) |
| **Processor(s)** | Data protection team, customer service, legal counsel |
| **Categories of Data Subjects** | Current and former users, customers, employees (who filed DSAR) |
| **Types of Personal Data** | Complete personal data of requesting subject; metadata: request date, type, decision, response date |
| **Legal Basis (Art. 6)** | (c) Legal obligation – Art. 12–22 DSGVO |
| **Data Storage Location(s)** | Internal DSAR tracking database (EU-based); encrypted file store |
| **Retention Period** | 3 years for DSAR records and supporting documentation |
| **Deletion Mechanism** | Deletion of exported subject data after confirmation; DSAR metadata retained 3 years |
| **Recipient(s)** | Requesting data subject; supervisory authority (if complaint filed) |
| **Sub-processors** | None (internal process) |
| **DPA in Place?** | N/A – internal activity |
| **Technical Measures** | Encryption of exported data; secure transmission (PGP/password-protected); access logging |
| **Organizational Measures** | DSAR response workflow (10-day SLA); training for DSAR handlers; legal review for complex requests |
| **DPO Assessment** | (to be completed by DPO) |
| **DPO Sign-Off Date** | (to be completed by DPO) |

---

### 2.5 Third-Party Data Integration (Customer Data Imports)

| Field | Value |
|---|---|
| **Activity ID** | ACT-005 |
| **Activity Name** | Third-Party Data Integration and ETL Processing |
| **Description** | Ingest personal data from external customer systems; transform, validate, load into analytics warehouse |
| **Controller** | External customer (data owner); organization may be joint controller or processor |
| **Processor(s)** | Internal data engineering team; AWS Glue / Lambda (ETL); data warehouse |
| **Categories of Data Subjects** | External customers' customers (end-users), employees of customer |
| **Types of Personal Data** | Varies by customer; typically: user IDs, behavioral events, transaction data, demographic attributes |
| **Legal Basis (Art. 6)** | ⚠️ TO BE COMPLETED BY LEGAL: Depends on customer's lawful basis and our processing purpose |
| **Special Categories (Art. 9)** | ⚠️ TO BE COMPLETED BY LEGAL: Assess customer data imports |
| **Data Storage Location(s)** | AWS S3 (staging); data warehouse (final); both EU-based |
| **Retention Period** | Per customer contract + retention_tier; typically 3–7 years |
| **Deletion Mechanism** | Upon customer request or contract termination; deletion confirmed in writing to customer |
| **Recipient(s)** | Customer only (via reports/dashboards); internal analytics team |
| **Sub-processors** | AWS S3, AWS Glue, data warehouse (Snowflake, BigQuery, etc.) |
| **DPA in Place?** | ⚠️ TO BE COMPLETED BY LEGAL: Confirm customer has executed DPA allowing this processing |
| **Technical Measures** | Encryption (at rest and in transit); data validation; access logging; row-level security for customer isolation |
| **Organizational Measures** | Data classification; customer communication (breach notification); data lineage tracking |
| **DPO Assessment** | (to be completed by DPO) |
| **DPO Sign-Off Date** | (to be completed by DPO) |

---

### 2.6 Nicht erfasste Verarbeitungen (Lücken, Stand 2026-09-25)

Der Repo-Stand vom 2026-09-25 enthält Verarbeitungen ohne Eintrag in diesem Verzeichnis. Sie werden **nicht** als ACT-Einträge erfunden. Sie sind hier als Lücke benannt und im Ledger in `_INDEX.md` geführt:

| Ledger-ID | Komponente (Repo) | Warum VVT-relevant (zu prüfen) |
|---|---|---|
| C-01 | Studio-KI-Routen (`studio/src/app/api/ai/`, Discovery-Chat unter `studio/src/app/api/projects/…/discovery/`) | **Teilweise erfasst am 2026-09-25 → ACT-006 (2.7) und ACT-007 (2.8).** Offen: Rechtsgrundlage, konkreter Anbieter, Region und Transfergrundlage (C-21), Löschfristen (C-22). Code-Stand PR #478: Egress technisch gesperrt. |
| C-02 | LLM-Telemetrie (`studio/src/lib/db/llm-events-repo.ts`) | **Teilweise erfasst am 2026-09-25 → ACT-007 (2.8):** Laut `studio/src/lib/ai/telemetry.ts` keine Prompts und kein Nutzerfeld. Speicherdauer weiterhin unbekannt |
| C-03 | Studio-Benutzer, Organisationen, RBAC, Audit-Kette, Benachrichtigungen (`studio/src/lib/db/`, Auth-Route) | Beschäftigten- bzw. Nutzerdaten von Kunden und Betreiber |
| C-04 | SAP-Konnektor (`tooling/connectors/sap/`, `studio/plugins/sap-connector/`) | Import von Kundendaten aus ERP; Verhältnis zu ACT-005 ungeklärt |
| C-05 | Project Runner / agentic loop (`tooling/agentic_loop/`, `tooling/superversion/project_package/`) | Ob personenbezogene Daten verarbeitet oder an LLMs gesendet werden: ⚠️ UNKLAR |
| C-06 | Fabric-/Power-BI-Export, Tenant-Settings | Microsoft (Power BI/Fabric) fehlt als Empfänger/Unterauftragsverarbeiter; Rollen im Kundentenant ungeklärt |
| C-07 | Rolle insgesamt | Alle „Controller“-Felder sind leer. Handelt ALUCA als Auftragsverarbeiter, ist zusätzlich ein Verzeichnis nach Art. 30 Abs. 2 DSGVO nötig; dieses Dokument folgt dem Aufbau nach Abs. 1. |

---

### 2.7 Studio-KI-Assistenz mit externen Sprachmodellen (ergänzt 2026-09-25)

> Code-Stand: PR #478, noch nicht gemergt. Alle technischen Angaben stammen aus dem Code; Details und Dateipfade stehen in `DPIA.md`, Abschnitt 11. **In diesem Stand ist die Übermittlung an LLM-Anbieter im Code gesperrt** (Default-deny-Gate, siehe `DPIA.md` 11.1). Der Eintrag beschreibt die Verarbeitung, wie sie der Code vorsieht, und die Bedingungen für eine Öffnung.

| Field | Value |
|---|---|
| **Activity ID** | ACT-006 |
| **Activity Name** | Studio-KI-Assistenz (KI-Chat, Discovery-Chat, Wizard, Factsheet-Entwurf und -Abgleich) |
| **Description** | Studio-Nutzer lassen Entwürfe für KPI-, Bracket-, Action- und Source-Definitionen sowie Factsheets erzeugen und Vorschläge aus Projektdokumenten ableiten. Dafür würden Prompt, Kontext und gegebenenfalls Quelldokumente an ein externes Sprachmodell gesendet (`DPIA.md` 11.2). Zuvor prüft der Server jeden Aufruf mit Policy und Payload-Scanner und protokolliert ihn ohne Inhalt (ACT-007) |
| **Status (Code)** | Egress gesperrt: `requireApprovedAiEgress` blockiert jede Route vor der Modellauflösung. Ein Freigabeweg per Konfiguration existiert nicht; auch ein genehmigter AI-Policy-Review öffnet den Egress nicht |
| **Controller** | (to be completed by legal team) – Rolle Kunde/ALUCA ungeklärt (C-07) |
| **Processor(s)** | ALUCA-Studio-Betrieb (⚠️ Hosting der Studio-Instanz: UNKLAR); nach einer Öffnung zusätzlich der LLM-Anbieter als (Unter-)Auftragsverarbeiter: [**LLM-ANBIETER**] (Kandidaten laut Code: Anthropic, Google, OpenAI) |
| **Categories of Data Subjects** | Studio-Nutzer (Beschäftigte von Kunde oder Betreiber); Dritte, die in eingebrachten Projektdokumenten vorkommen (⚠️ UNKLAR, kundenabhängig) |
| **Types of Personal Data** | Freitext-Eingaben und Chat-Nachrichten; Inhalte von Quelldokumenten (Discovery-Chat, vollständig im System-Prompt); Factsheet-Prosa und Bracket-YAML (je bis 4000 Zeichen); Core-Artefakt-Metadaten (KPI-Definitionen, DAX). **Nicht** im Modell-Payload: Nutzer-E-Mail und Nutzerkennung |
| **Datenklassen (Policy)** | Nie an ein Modell: `unknown`, `restricted`, `secret`. `customer_confidential` nie an `external_cloud`. Nicht-öffentliche Daten an `external_cloud` nur redigiert [Code, `studio/src/lib/ai/data-handling-policy.ts`]. Welche Klassen je Projekt erlaubt sind: [Konfig], Project-Package-Modul `ai_data_handling` → [**KUNDENSPEZIFISCH**] |
| **Legal Basis (Art. 6)** | ⚠️ TO BE COMPLETED BY LEGAL |
| **Special Categories (Art. 9)** | ⚠️ TO BE COMPLETED BY LEGAL. Technisch nicht ausgeschlossen: Der Scanner erkennt nur Secrets, E-Mail, Telefon, IBAN, UUID, Home-Pfade und Sperrbegriffe |
| **Data Storage Location(s)** | Studio-Server: ⚠️ UNKLAR. Beim LLM-Anbieter: [**REGION**]. Der Code sichert keine EU-Residenz zu (`PROVIDER_RESIDENCY` = `any` für alle Anbieter); `eu-only` führt zu „kein Anbieter“ |
| **Drittlandübermittlung** | Nach einer Öffnung wahrscheinlich (US-Anbieter, SDK-Standard-Endpunkte) → [**TRANSFERGRUNDLAGE: DPF-Zertifizierung / SCC 2021/914 Modul …**] ⚠️ TO BE COMPLETED BY LEGAL (C-20, C-21) |
| **Retention Period** | Studio: Prompts und Antworten werden in den geprüften Routen nicht gespeichert (Ausnahme Discovery-Persistenz, siehe C-03; ⚠️ nicht geprüft). Anbieter: [**PROMPT-AUFBEWAHRUNG LAUT VERTRAG**]; im Code nur als `prompt_retention_days` deklariert, nicht überprüft (C-21) |
| **Deletion Mechanism** | Beim Anbieter: vertraglich (⚠️ UNKLAR). Im Studio: nicht zutreffend (keine Speicherung des Payloads) |
| **Recipient(s)** | Anfragender Studio-Nutzer; nach einer Öffnung: [**LLM-ANBIETER**] |
| **Sub-processors** | [**LLM-ANBIETER**], siehe `AVV_Template.md` 5.3 und `eu_hosting_guarantee.md` 3.4 |
| **DPA in Place?** | ⚠️ TO BE COMPLETED BY LEGAL. Ohne AVV bzw. Anbieterbedingungen mit Nachweis darf der Egress nicht geöffnet werden |
| **Technical Measures** | Default-deny-Egress-Gate mit Fail-closed (`studio/src/lib/ai/egress-gate.ts`); Datenklassen-Policy (`studio/src/lib/ai/data-handling-policy.ts`); Payload-Scanner mit Blockierung (`studio/src/lib/ai/egress-preflight.ts`); Residenz-/Anbieterfilter (`studio/src/lib/ai/config/route-model.ts`); Rollenprüfung pro Route; inhaltsfreier, verketteter Nachweis (ACT-007). **Fehlt:** Redaktion, Prüfung von Ausgaben und Tool-Ergebnissen (C-23) |
| **Organizational Measures** | AI-Policy-Review im Vier-Augen-Prinzip (Editor reicht ein, ein anderer Admin entscheidet, Begründung ist Pflicht; `studio/docs/design/AI_POLICY_REVIEW.md`); Freigabe der Kunden-KI-Konfiguration L1/L2 nur durch Admin |
| **DPIA** | `DPIA.md` Abschnitt 11 (vorsorglich; Pflicht nach C-12 von Legal zu entscheiden) |
| **DPO Assessment** | (to be completed by DPO) |
| **DPO Sign-Off Date** | (to be completed by DPO) |

---

### 2.8 Nachweis-, Freigabe- und Telemetrieprotokolle der Studio-KI (ergänzt 2026-09-25)

| Field | Value |
|---|---|
| **Activity ID** | ACT-007 |
| **Activity Name** | Protokollierung von KI-Egress-Entscheidungen, AI-Policy-Reviews und LLM-Telemetrie |
| **Description** | Zu jedem KI-Aufruf wird ein inhaltsfreier Nachweis gespeichert, auch wenn der Aufruf blockiert wird. Einreichungen und Entscheidungen zu AI-Policy-Reviews werden mit Begründung protokolliert. Nach einem Modellaufruf werden Nutzung und Kosten erfasst (in diesem Stand nie erreicht) |
| **Controller** | (to be completed by legal team) (C-07) |
| **Processor(s)** | ALUCA-Studio-Betrieb (SQLite-Datenbank der Studio-Instanz; ⚠️ Hosting UNKLAR) |
| **Categories of Data Subjects** | Studio-Nutzer (Beschäftigte von Kunde oder Betreiber) |
| **Types of Personal Data** | Egress-Nachweis (`audit_events`, `ai_egress`): `actor` = Nutzer-E-Mail, Projekt-ID, Zeitstempel, Payload-Hash (SHA-256) und -Größe, Klasse, Zweck, Provider, Modell, Fundzahlen, Regel-IDs, Blockgründe; **kein Inhalt** (Inhaltsfelder werden abgewiesen). Reviews (`ai_policy_reviews`): Einreicher- und Prüfer-E-Mail, Zeitstempel, Begründung (Freitext, 20–2000 Zeichen), Revision, Routen-Hash. Telemetrie (`llm_step_events`): Rollen, Provider, Modell, Token-Zahlen, Latenz, Erfolg, Fehlertext, Kosten; kein Nutzerfeld, kein Prompt (laut `studio/src/lib/ai/telemetry.ts`) |
| **Legal Basis (Art. 6)** | ⚠️ TO BE COMPLETED BY LEGAL (z. B. Nachweis- und Rechenschaftspflicht, Art. 5 Abs. 2 / Art. 24, 32 – Einordnung Legal) |
| **Data Storage Location(s)** | Studio-Datenbank (SQLite); Standort: ⚠️ UNKLAR |
| **Retention Period** | ⚠️ UNKLAR / nicht geregelt. `studio/src/lib/db/audit-repo.ts` und `studio/src/lib/db/ai-policy-review-repo.ts` enthalten keine Lösch- oder Ablauffunktion; die Hash-Kette der Audit-Ereignisse spricht gegen Einzellöschung. Die Frist für `llm_step_events` lässt sich nicht prüfen (`llm-events-repo.ts` fehlt im Teilabbild). Kein Tier in `retention_policy.md` (C-02, C-22) |
| **Deletion Mechanism** | Keiner im Code (C-22) |
| **Recipient(s)** | Projekt-Viewer (Review-Liste über `GET …/ai-policy-reviews`), Projekt-Admins, Betrieb |
| **Sub-processors** | keine eigenen; Hosting der Studio-Instanz ⚠️ UNKLAR |
| **Technical Measures** | Inhaltsfreier Nachweis (`persistAiEgressEvidence` weist die Felder `payload`, `prompt`, `system`, `user`, `matches`, `redacted_text` ab); Verkettung zur Manipulationserkennung (`chainEvent`); rollenbasierter Zugriff |
| **Organizational Measures** | Vier-Augen-Prinzip beim Review; Löschkonzept fehlt (C-22) |
| **DPO Assessment** | (to be completed by DPO) |
| **DPO Sign-Off Date** | (to be completed by DPO) |

---

## 3. Amendment Tracking

| Date | Activity ID | Change Description | Trigger | Approved By |
|---|---|---|---|---|
| 2026-04-22 | ACT-001 to ACT-005 | Initial processing record created | Compliance requirement | (to be completed by legal team) |
| 2026-09-25 | ACT-001, Abschnitt 1, 2.6 | Durchsicht: Art.-30-Bezüge korrigiert, Regionsangabe als unklar markiert, Lücken 2.6 ergänzt (keine neuen ACT-Einträge) | Inhaltliche Durchsicht | (to be completed by legal team) |
| 2026-09-25 | ACT-006, ACT-007 (neu); 2.6 | Studio-KI und KI-Protokolle aus dem Code-Stand PR #478 abgeleitet (Ledger C-01, C-02); Platzhalter für kundenspezifische Werte | Ledger C-01/C-02 | (to be completed by legal team) |
| (to be completed by legal team) | (to be completed by legal team) | (to be completed by legal team) | (to be completed by legal team) | (to be completed by legal team) |

---

## 4. Privacy Impact Notes

⚠️ TO BE COMPLETED BY LEGAL: Highlight any processing activities requiring DPIA or supervisory authority consultation:

- [ ] **High-risk activities:** Does any activity meet Art. 35(3) criteria (large-scale, systematic monitoring, automated decision-making, special categories)? If yes, DPIA is mandatory.
- [ ] **International transfers:** Are there third-country data transfers? If yes, SCCs or adequacy decision required.
- [ ] **Supervisory authority consultation:** If DPIA identifies high residual risk, consult authority per Art. 36 DSGVO.

---

## 5. Data Subject Transparency Information

⚠️ TO BE COMPLETED BY LEGAL: Use this record to generate privacy notices and transparency sheets for data subjects.

Example template:

> **What personal data do we process?**
> 
> We process the following categories of personal data:
> 
> 1. **Analytics (Activity ACT-001):** User IDs, action outcomes, timestamps, cohort segments. Retained for 3–7 years. Protected by encryption and access controls.
> 2. **Action audit logs (Activity ACT-002):** User ID, action performer name, outcome, timestamp. Retained for 7 years.
> 3. **Security monitoring (Activity ACT-003):** IP addresses, session IDs, device fingerprints. Logs retained for 30 days (raw) or 1 year (aggregated).
> 4. **KI-Assistenz im Studio (Activity ACT-006, ergänzt 2026-09-25):** Ihre Eingaben und von Ihnen eingebrachte Dokumente können an [**LLM-ANBIETER**] in [**REGION**] übermittelt werden, sobald die Funktion freigegeben ist. Grundlage der Übermittlung: [**TRANSFERGRUNDLAGE**]; Speicherdauer beim Anbieter: [**FRIST**]. ⚠️ TO BE COMPLETED BY LEGAL (inkl. KI-Transparenzhinweis, vgl. C-11)
> 
> **Your rights:** Access, rectification, deletion, restriction, portability, objection. Contact [DPO email].

---

## 6. Review Checklist (DPO/Legal)

- [ ] **All processing activities identified:** No major data processing activities are missing
- [ ] **Data categories documented:** Each activity lists personal data types and sensitivity
- [ ] **Legal basis assigned:** Every activity has documented Art. 6 basis
- [ ] **Retention periods defined:** Each activity specifies retention duration and deletion mechanism
- [ ] **Sub-processors listed:** All third-party processors have DPAs in place
- [ ] **Technical/organizational measures documented:** Section 2 includes specific, verifiable TOMs
- [ ] **High-risk activities assessed:** DPIA conducted (or in progress) for high-risk activities
- [ ] **Data subject rights procedures established:** Mechanism for handling DSAR is documented (ACT-004)
- [ ] **Transparency information provided:** Privacy notices generated from this record
- [ ] **Updates tracked:** Amendment log maintained; quarterly review scheduled

---

## 7. Version History

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-04-22 | Analytics & Legal Teams | Initial processing record skeleton; 5 key activities documented with templates |
| 1.1 | 2026-09-25 | Inhaltliche Durchsicht (kein Legal-Sign-off) | Art.-30-Bezüge korrigiert; Lückenliste 2.6 |
| 1.2 | 2026-09-25 | Inhaltliche Durchsicht (kein Legal-Sign-off) | ACT-006 (Studio-KI) und ACT-007 (KI-Protokolle) aus Code-Stand PR #478 ergänzt; C-01/C-02 teilweise |

**Last reviewed by:** (to be completed by DPO)  
**Next review date:** (to be completed by DPO – typically Q2 2026) — ⚠️ Stand 2026-09-25: überfällig (C-19)  
**Review frequency:** Quarterly or upon material processing activity change

---

**Document maintained by:** Data Protection Officer / Compliance Team  
**Confidentiality:** Internal – restricted access (supervisory authorities may request it per Art. 30(4) DSGVO; korrigiert 2026-09-25, vorher „Art. 30(2)“)

[^1]: DSGVO (EUR-Lex): https://eur-lex.europa.eu/eli/reg/2016/679/oj/deu — Wortlaut Art. 30 abgeglichen über https://dsgvo-gesetz.de/art-30-dsgvo/
