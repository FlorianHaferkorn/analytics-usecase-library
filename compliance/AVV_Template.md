# Auftragsverarbeitungsvertrag (AVV) – Data Processing Agreement Template

**Regulation:** DSGVO Article 28  
**Document Type:** DPA / Processor Agreement  
**Version:** 1.0  
**Effective Date:** (to be completed by legal team)  
**Last Updated:** 2026-04-22  
**Inhaltliche Durchsicht (ohne Legal-Sign-off):** 2026-09-25 – siehe Abschnitt 14

---

## 1. Executive Summary

This Data Processing Agreement (Auftragsverarbeitungsvertrag – AVV) establishes the terms governing the processing of personal data when [**PROCESSOR NAME**] acts as a processor on behalf of [**CONTROLLER NAME**] (the controller).

Under DSGVO Article 28, any entity processing personal data on behalf of a controller must enter into a binding agreement that specifies controller instructions, processor obligations, and technical/organizational measures protecting personal data.

⚠️ TO BE COMPLETED BY LEGAL: Customize Sections 2–8 with organization-specific language and operational details before signing.

---

## 2. Parties

### 2.1 Data Controller

| Field | Details |
|---|---|
| **Legal Name** | (to be completed by legal team) |
| **Address** | (to be completed by legal team) |
| **Jurisdiction** | (to be completed by legal team) |
| **Contact Person (DPO/Legal)** | (to be completed by legal team) |

**Responsibilities:** Determines purposes and means of processing; issues instructions; ensures DSGVO Art. 5–7 compliance.

### 2.2 Data Processor

| Field | Details |
|---|---|
| **Legal Name** | (to be completed by legal team) |
| **Address** | (to be completed by legal team) |
| **Jurisdiction** | (to be completed by legal team) |
| **Data Protection Officer (if applicable)** | (to be completed by legal team) |

**Responsibilities:** Processes only on controller instructions; implements technical/organizational measures; assists with data subject rights (Art. 12–22).

---

## 3. Subject Matter and Duration of Processing

### 3.1 Processing Activities

⚠️ TO BE COMPLETED BY LEGAL: List all processing activities in scope:

| Activity | Purpose | Duration |
|---|---|---|
| Analytics reporting and KPI calculation | Business intelligence and decision-making | 3–7 years (per retention tier) |
| Action code execution and audit logging | Execute business rules; maintain audit trail | 7 years (compliance standard) |
| Platform maintenance and security monitoring | Detect abuse, prevent unauthorized access | 30 days (raw logs); 1 year (aggregated) |
| Studio-KI-Assistenz (VVT ACT-006; ergänzt 2026-09-25) | Entwürfe für KPI-, Bracket-, Action- und Factsheet-Definitionen; Vorschläge aus Projektdokumenten mit externem Sprachmodell. Im Code-Stand PR #478 technisch gesperrt, siehe `DPIA.md` 11.1 | Anbieterseitige Speicherung: [**FRIST LAUT LLM-ANBIETERVERTRAG**] – ⚠️ TO BE COMPLETED BY LEGAL |
| Nachweis- und Freigabeprotokolle der Studio-KI (VVT ACT-007) | Nachweis jeder KI-Egress-Entscheidung, Vier-Augen-Review | ⚠️ UNKLAR – im Code keine Löschfrist (C-22) |
| (Additional activities) | (to be completed by legal team) | (to be completed by legal team) |

### 3.2 Duration of Agreement

| Timeline | Details |
|---|---|
| **Effective Date** | (to be completed by legal team) |
| **Initial Term** | (to be completed by legal team) – typically 12 months |
| **Renewal Terms** | (to be completed by legal team) |
| **Termination for Cause** | 30 days' notice if material breach not cured within 15 days |
| **Termination for Convenience** | (to be completed by legal team) – typically 60–90 days' notice |

---

## 4. Nature, Scope, Context, and Purposes of Processing

### 4.1 Legal Basis for Processing (Art. 6 DSGVO)

⚠️ TO BE COMPLETED BY LEGAL: Select applicable basis:

- [ ] **(a) Consent:** Data subjects have freely given, specific, informed, and unambiguous consent
- [ ] **(b) Contract:** Processing necessary for contract performance
- [ ] **(c) Legal Obligation:** Processing required by law (specify which law)
- [ ] **(d) Vital Interests:** Necessary to protect vital interests
- [ ] **(e) Public Task:** Necessary for public interest task
- [ ] **(f) Legitimate Interests:** Necessary for legitimate interests (with balancing test)

**Justification:** (to be completed by legal team)

### 4.2 Categories of Data Subjects

⚠️ TO BE COMPLETED BY LEGAL: List all categories:

| Category | Description | Approximate Volume |
|---|---|---|
| Employees | (specify roles/departments) | (to be completed by legal team) |
| Customers | (specify: direct customers, end-users, or both) | (to be completed by legal team) |
| Agents / Representatives | (specify: intermediaries, resellers) | (to be completed by legal team) |
| Audit / Compliance Subjects | (specify: audit/compliance records) | (to be completed by legal team) |

### 4.3 Types and Categories of Personal Data

⚠️ TO BE COMPLETED BY LEGAL: Map data categories to processing tables:

| Data Type | Tables/Fields | Retention Tier | Sensitivity |
|---|---|---|---|
| Identifiers | `dim_user.user_id`, `dim_user.email_address` | 3–7y | High |
| Action performer name | `fact_action_outcome.action_actor_name` | 7y | Medium |
| IP address, device fingerprint | audit logs, event stream | 30d–1y | Medium–High |
| Action outcome, cohort segment | `fact_action_outcome.*` | 3–7y | Medium |
| Timestamps | All fact tables | 3–7y | Low |
| Technical metadata | audit logs | 30d–1y | Low–Medium |
| KI-Eingaben: Freitext, Chat-Nachrichten, Inhalte von Quelldokumenten (ergänzt 2026-09-25) | Modell-Payload der Studio-KI-Routen (`DPIA.md` 11.2); im Studio nicht gespeichert | – (beim Anbieter: [**FRIST**]) | ⚠️ kundenabhängig; kann Daten Dritter enthalten |
| Nutzer-E-Mail in KI-Nachweisen und Reviews | `audit_events` (`ai_egress`, `ai_policy_review`), `ai_policy_reviews` | ⚠️ kein Tier (C-22) | Low–Medium |

---

## 5. Sub-Processors (Unterauftragsverarbeiter)

### 5.1 Initial List of Sub-Processors

⚠️ TO BE COMPLETED BY LEGAL: Maintain current sub-processor inventory:

| Sub-Processor Name | Service/Role | Location | Data Categories | Contract Status |
|---|---|---|---|---|
| Amazon Web Services (AWS) | Cloud infrastructure | EU (eu-central-1; ⚠️ UNKLAR: „westeurope“ ist ein Azure-Regionsname – AWS-Region bestätigen, C-14) | All | DPA in place |
| Microsoft Azure | (if applicable) | EU regions only | (to be completed by legal team) | (to be completed by legal team) |
| (Third-party API vendor) | (to be completed by legal team) | (to be completed by legal team) | (to be completed by legal team) | (to be completed by legal team) |
| **Kategorie LLM-Anbieter (Studio-KI)** – [**ANBIETERNAME**] (laut Code einer von: Anthropic, Google, OpenAI; siehe 5.3) | Inferenz externer Sprachmodelle für Studio-KI (ACT-006) | [**REGION / GEOGRAFIE**] – ⚠️ Code sichert keine EU-Residenz zu | KI-Eingaben (4.3); keine Nutzer-E-Mail | [**AVV/DPA-STATUS**]; Drittland: [**DPF / SCC 2021/914 MODUL …**] – ⚠️ TO BE COMPLETED BY LEGAL. Nicht aktiv: Egress im Code-Stand PR #478 gesperrt |

### 5.2 Sub-Processor Change Control

**Processor Authorization:** Before engaging any new sub-processor, the Processor must:

1. Inform the Controller in writing with ≥30 days' advance notice
2. Provide details: name, location, processing activities, proof of DPA coverage
3. Obtain Controller approval (explicit or implicit per clause below)
4. Ensure sub-processor executes equivalent Data Processing Agreement

**Objection Process:**

- Controller may object to new sub-processors within 15–30 days of notification
- If parties cannot agree, Controller may terminate this DPA with 30 days' notice without penalty
- If Processor cannot remove the sub-processor, Controller may terminate immediately

### 5.3 Unterauftragsverarbeiter-Kategorie „LLM-Anbieter“ (Studio-KI; ergänzt 2026-09-25)

Die Tabelle leitet sich aus dem Code ab (Stand PR #478, nicht gemergt; Details in `DPIA.md` Abschnitt 11). Sie ist **keine** Freigabe. Kundenspezifische Werte sind Platzhalter.

| Merkmal | Aus dem Code belegt | Vom Vertrag/Legal auszufüllen |
|---|---|---|
| Anbieter | `anthropic`, `google` (Gemini API über `@ai-sdk/google`), `openai`; Auswahlreihenfolge L0: anthropic → google → openai; aktiv ist nur ein Anbieter mit hinterlegtem API-Schlüssel (Kunde bringt den Schlüssel selbst mit) | [**VERTRAGSPARTNER, JURISTISCHE PERSON, SITZ**] |
| Modelle | Zuordnung in `studio/src/lib/ai/config/defaults.ts` (z. B. `claude-sonnet-4-6`, `gemini-2.0-flash`, `gpt-4o`) | – |
| Endpunkt / Region | SDK-Standard-Endpunkte (kein `baseURL`). `PROVIDER_RESIDENCY` = `any` → **keine** EU-Zusicherung im Code; `eu-only` sperrt die KI (Fail-closed) | [**REGION, RECHENZENTRUMSSTANDORT, NACHWEIS**] |
| Rechtsgrundlage Drittlandübermittlung | – | [**DPF-ZERTIFIZIERUNG (Nachweis) ODER SCC 2021/914 MODUL 2/3 + TIA**] (C-20) |
| Training mit Kundendaten | Policy verlangt `provider_training_allowed: false` (nur deklariert) | [**VERTRAGLICHER AUSSCHLUSS + FUNDSTELLE**] |
| Aufbewahrung der Prompts beim Anbieter | Policy verlangt einen expliziten Wert für `prompt_retention_days` (nur deklariert) | [**FRIST LAUT ANBIETERBEDINGUNGEN**] |
| Weitere Unterauftragsverarbeiter des Anbieters | – | [**LISTE / LINK**] |
| Freigabe im Projekt | Project-Package-Route mit `provider_region`, `provider_geography`, `provider_terms_evidence_refs`, `expires_at`; Vier-Augen-Review. Öffnet den Egress **nicht** | Verweis auf die Freigabeentscheidung [**DECISION-REF**] |

⚠️ TO BE COMPLETED BY LEGAL: Nach Art. 28 Abs. 2/4 DSGVO darf ein LLM-Anbieter erst eingesetzt werden, wenn er vorher genehmigt wurde und die Pflichten vertraglich weitergegeben sind. Im Code ist der Egress gesperrt; vor einer Öffnung müssen C-21 und C-23 erledigt sein.

---

## 6. Technical and Organizational Measures (TOMs)

### 6.1 Controller Instructions

The Processor processes personal data only on documented instructions from the Controller. Instructions may be:

- Initial instructions in this DPA (Appendix A)
- Subsequent instructions via email or secure channel
- Emergency instructions (e.g., deletion, access restriction) with confirmed acknowledgment

The Processor must log all instructions. Instructions contrary to DSGVO shall not be executed; Processor must notify Controller immediately.

### 6.2 Technical Measures

| Measure | Specification |
|---|---|
| **Encryption at Rest** | AES-256; encryption keys managed by HSM or cloud KMS |
| **Encryption in Transit** | TLS 1.3 for all API calls; certificate pinning for critical endpoints |
| **Access Control** | RBAC; MFA for sensitive operations; principle of least privilege |
| **Authentication** | Strong password policy; session timeout (30 min); API key rotation (90 days) |
| **Data Minimization** | Only necessary fields exposed; row-level security (RLS) by default |
| **Pseudonymization** | User IDs hashed with org-specific salt (SHA-256+); key separation |
| **Logging & Monitoring** | Immutable audit logs of all access/modifications; 1-year retention |
| **Network Security** | Private subnets; API gateway for external access; IDS/IPS |
| **Backup & Recovery** | Encrypted backups; tested restoration (RTO = 4 hours) |
| **KI-Egress-Kontrolle (Studio; ergänzt 2026-09-25)** | Default-deny-Gate mit Fail-closed, Datenklassen-Policy, Payload-Scanner (blockiert Secrets und Fundstellen personenbezogener Muster), inhaltsfreier Nachweis je Aufruf, Vier-Augen-Review. Im Code belegt, Pfade in `DPIA.md` 11.4. Nicht vorhanden: Redaktion sowie Prüfung von Ausgaben und Tool-Ergebnissen (C-23) |

### 6.3 Organizational Measures

| Measure | Specification |
|---|---|
| **Personnel Training** | Annual DSGVO + data protection training; training records maintained |
| **Confidentiality Agreements** | All employees sign NDA before data access |
| **Access Authorization** | Granted only to identified, trained personnel; revoked immediately on termination |
| **Incident Response** | Written procedure; der Auftragsverarbeiter meldet Verletzungen dem Verantwortlichen **unverzüglich** (Art. 33 Abs. 2 DSGVO). Die 72-Stunden-Frist (Art. 33 Abs. 1) gilt für die Meldung des Verantwortlichen an die Aufsichtsbehörde[^1]. Eine vertragliche Stundenfrist legt Legal fest. (Korrigiert 2026-09-25) |
| **Data Subject Rights** | Procedures to assist with access, deletion, portability (Art. 12–22); 10-day SLA |
| **Subprocessor Management** | Sub-processor agreements reviewed annually; changes tracked |
| **Physical Security** | Access to facilities restricted; visitor logs; CCTV (if applicable) |
| **Vendor Management** | Third-party vendors audited; SOC 2 or ISO 27001 required |

---

## 7. Data Subject Rights & Controller Cooperation

### 7.1 Rights Under DSGVO (Art. 12–22)

The Processor shall assist the Controller in fulfilling:

| Right | Article | Processor Role | Timeline |
|---|---|---|---|
| **Right of access** | Art. 15 | Provide data in intelligible format | 10 business days |
| **Right of rectification** | Art. 16 | Correct inaccurate data upon instruction | 10 business days |
| **Right to erasure** | Art. 17 | Delete data and logs; confirm in writing | 10 business days |
| **Right to restrict processing** | Art. 18 | Cease processing but maintain data | 10 business days |
| **Right to data portability** | Art. 20 | Export in structured, machine-readable format | 10 business days |
| **Right to object** | Art. 21 | Cease processing if objection upheld | 10 business days |

### 7.2 Cooperation Mechanism

The Processor shall:

1. Designate a DPA contact for DSAR requests
2. Log all requests with timestamp, subject, data categories, resolution
3. Notify Controller immediately upon request receipt
4. Assist Controller in responding within statutory timeline (ein Monat, um weitere zwei Monate verlängerbar – Art. 12 Abs. 3 DSGVO[^1]; korrigiert 2026-09-25, vorher „30 days“)
5. Cooperate in supervisory authority investigations

⚠️ TO BE COMPLETED BY LEGAL: Define escalation procedure if Processor receives direct data subject requests.

---

## 8. Auditing and Compliance Verification

### 8.1 Controller Right to Audit

The Controller (or independent auditor on controller's behalf) has the right to:

- Audit Processor compliance with this DPA and DSGVO at least annually
- Conduct unannounced inspections (≥2 weeks' notice) — ⚠️ UNKLAR: widersprüchlich („unangekündigt“ vs. „≥ 2 Wochen Vorlauf“); Legal entscheidet (C-13)
- Review TOMs, personnel training records, sub-processor contracts
- Obtain SOC 2 Type II or ISO 27001 certification reports (annually)

### 8.2 Processor Obligations

The Processor shall:

- Provide all information necessary to verify DSGVO Art. 28 compliance
- Provide evidence of technical/organizational measures
- Correct deficiencies within defined timeline (typically 30–90 days)
- Reimburse reasonable audit costs if material non-compliance found

### 8.3 Audit Schedule

| Audit Type | Frequency | Scope | Evidence |
|---|---|---|---|
| **Internal Compliance Check** | Quarterly | Data security; personnel training; sub-processor review | Compliance checklist + sign-off |
| **Third-Party Security Audit** | Annually | SOC 2 Type II (preferred) or ISO 27001 | Audit report; management letter |
| **Controller Audit** | Annually (or post-incident) | Full scope | Audit findings; remediation plan |
| **DSAR Audit** | Quarterly | Request response times, accuracy, completeness | Request log; response samples |

⚠️ TO BE COMPLETED BY LEGAL: Processor provides audit evidence within 5–15 business days of request.

---

## 9. Data Deletion and Return Upon Termination

### 9.1 Termination Triggers

This DPA terminates upon:

- **Expiration of the term** (Section 3.2) without renewal
- **Mutual written agreement**
- **Termination for cause** (material breach not cured within 15 days)
- **Termination for convenience** (30/60/90 days' notice) — ⚠️ abweichend von 3.2 („typically 60–90 days“); Legal vereinheitlicht (C-13)

### 9.2 Data Handling Upon Termination

Within 30–60 days of termination, the Processor shall, at the Controller's election:

**Option A: Delete all personal data**

- Permanently delete all data (including backups) no longer required by law
- Use approved destruction methods (cryptographic erasure, physical destruction, secure deletion)
- Provide written deletion certification
- Retain only legally required data; delete upon expiration

**Option B: Return all personal data**

- Export in structured, commonly used, machine-readable format (CSV, JSON, Parquet)
- Provide in encrypted format; decryption key transmitted separately
- Confirm completeness and accuracy
- Delete all Processor copies after confirmation

⚠️ TO BE COMPLETED BY LEGAL: Controller selects Option A or B. Processor does not retain copies except where legally required.

### 9.3 Sub-Processor Wind-Down

Processor ensures all sub-processors comply with deletion/return requirements. Sub-processor contracts must include equivalent termination clauses.

---

## 10. Liability and Indemnification

⚠️ TO BE COMPLETED BY LEGAL: Define liability allocation:

| Scenario | Responsibility | Liability Cap | Insurance Required |
|---|---|---|---|
| **Processor breach of DSGVO** | Processor liable for damages | (typically € unlimited for intentional/gross negligence) | Professional liability / cyber insurance, minimum €[amount] |
| **Sub-processor breach** | Processor liable; recover from sub-processor | (to be completed) | (to be completed) |
| **Data subject claims** | Both may be jointly liable per Art. 82 DSGVO | (to be completed) | (to be completed) |

---

## 11. Entire Agreement and Amendments

This DPA, together with Appendix A (Processing Instructions), constitutes the entire agreement. Any prior communications are superseded.

Amendments require written consent from both parties per the Sub-Processor change-control procedure (Section 5.2).

---

## 12. Governing Law and Dispute Resolution

⚠️ TO BE COMPLETED BY LEGAL:

- **Governing Law:** [German law / EU law / Other]
- **Jurisdiction:** [Specify city/country]
- **Dispute Resolution:** Good-faith negotiation (60 days); if unresolved:
  - [ ] Arbitration (specify: DIS Rules / ICC Rules / Other)
  - [ ] Litigation in specified courts

---

## 13. Review Checklist (Legal/DPO)

- [ ] **Parties identified:** Controller and Processor clearly identified with contact information
- [ ] **Processing activities listed:** All relevant activities from Section 4.1 documented
- [ ] **Data categories classified:** All personal data types listed with sensitivity levels
- [ ] **Legal basis confirmed:** Lawful basis (Art. 6) documented for each activity
- [ ] **TOMs verified:** Technical and organizational measures proportionate to processing risk
- [ ] **Sub-processor list current:** All sub-processors identified; DPA coverage confirmed
- [ ] **Data subject rights procedure:** Mechanism for handling access, deletion, other requests clear
- [ ] **Termination procedure:** Data deletion/return option specified; timeline defined
- [ ] **Liability allocation:** Insurance requirements and damage caps specified
- [ ] **Signatures obtained:** Both Controller and Processor have signed and dated

---

## 14. Offene Punkte (Durchsicht 2026-09-25)

Die Vorlage bleibt eine Vorlage; Platzhalter wurden nicht gefüllt. Befunde (IDs = Ledger in `_INDEX.md`):

- **C-13 Art. 28 Abs. 3 DSGVO:** Nach Art. 28 Abs. 3 lit. a verarbeitet der Auftragsverarbeiter Daten nur auf dokumentierte Weisung, „auch in Bezug auf die Übermittlung personenbezogener Daten an ein Drittland“. Nach lit. f unterstützt er den Verantwortlichen bei den Pflichten aus Art. 32–36[^1]. Beides ist in der Vorlage nicht ausdrücklich geregelt. Optional kann Legal die Standardvertragsklauseln nach Art. 28 Abs. 7 (Durchführungsbeschluss (EU) 2021/915)[^2] als Basis nutzen.
- **C-13 Abschnitt 4.1:** Die Auswahl der Rechtsgrundlage nach Art. 6 ist Sache des Verantwortlichen und kein Pflichtinhalt nach Art. 28 Abs. 3. Legal entscheidet, ob der Abschnitt bleibt.
- **C-01 (teilweise, 2026-09-25):** Die LLM-Anbieter stehen jetzt als Kategorie mit Platzhaltern in 5.1 und 5.3, abgeleitet aus dem Code-Stand PR #478. Offen sind Vertragspartner, Region und Transfergrundlage (C-21).
- **C-06:** In 5.1 fehlt Microsoft Power BI/Fabric.
- **C-07:** Unklar ist, in welcher Rolle ALUCA diese Vorlage nutzt: als Auftragsverarbeiter gegenüber Kunden oder als Verantwortlicher gegenüber Vendoren.

[^1]: DSGVO (EUR-Lex): https://eur-lex.europa.eu/eli/reg/2016/679/oj/deu — Wortlaut abgeglichen über https://dsgvo-gesetz.de/art-28-dsgvo/, https://dsgvo-gesetz.de/art-12-dsgvo/, https://dsgvo-gesetz.de/art-33-dsgvo/
[^2]: Durchführungsbeschluss (EU) 2021/915: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32021D0915

---

## Signatures

| Party | Signature | Printed Name | Title | Date |
|---|---|---|---|---|
| **Controller** | __________________ | (to be completed by legal team) | (to be completed by legal team) | (to be completed by legal team) |
| **Processor** | __________________ | (to be completed by legal team) | (to be completed by legal team) | (to be completed by legal team) |

---

## Appendix A: Processing Instructions (Initial)

⚠️ TO BE COMPLETED BY LEGAL: Document initial controller instructions:

| Instruction # | Description | Trigger | Authority |
|---|---|---|---|
| 1 | (e.g., "Process action events daily; aggregate by cohort; apply RLS per data classification") | (Daily / on-demand / event-triggered) | Controller Operations Team |
| 2 | (to be completed by legal team) | (to be completed by legal team) | (to be completed by legal team) |

---

## Appendix B: Sub-Processor Agreements (Referenced)

⚠️ TO BE COMPLETED BY LEGAL: Reference sub-processor DPA locations:

- AWS Data Processing Agreement: [link]
- Azure Data Processing Agreement: [link]
- Other sub-processor contracts: (to be completed by legal team)

---

**Document prepared by:** Analytics & Legal Teams  
**Status:** Template – awaiting legal review and customization  
**Next review:** Annually or upon material processing activity change
