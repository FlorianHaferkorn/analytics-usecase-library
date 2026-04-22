# Auftragsverarbeitungsvertrag (AVV) – Data Processing Agreement Template

**Regulation:** DSGVO Article 28  
**Document Type:** DPA / Processor Agreement  
**Version:** 1.0  
**Effective Date:** (to be completed by legal team)  
**Last Updated:** 2026-04-22

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

---

## 5. Sub-Processors (Unterfertiger)

### 5.1 Initial List of Sub-Processors

⚠️ TO BE COMPLETED BY LEGAL: Maintain current sub-processor inventory:

| Sub-Processor Name | Service/Role | Location | Data Categories | Contract Status |
|---|---|---|---|---|
| Amazon Web Services (AWS) | Cloud infrastructure | EU (westeurope, eu-central-1) | All | DPA in place |
| Microsoft Azure | (if applicable) | EU regions only | (to be completed by legal team) | (to be completed by legal team) |
| (Third-party API vendor) | (to be completed by legal team) | (to be completed by legal team) | (to be completed by legal team) | (to be completed by legal team) |

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

### 6.3 Organizational Measures

| Measure | Specification |
|---|---|
| **Personnel Training** | Annual DSGVO + data protection training; training records maintained |
| **Confidentiality Agreements** | All employees sign NDA before data access |
| **Access Authorization** | Granted only to identified, trained personnel; revoked immediately on termination |
| **Incident Response** | Written procedure; breach notification within 72 hours (Art. 33) |
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
4. Assist Controller in responding within statutory timeline (30 days per Art. 12)
5. Cooperate in supervisory authority investigations

⚠️ TO BE COMPLETED BY LEGAL: Define escalation procedure if Processor receives direct data subject requests.

---

## 8. Auditing and Compliance Verification

### 8.1 Controller Right to Audit

The Controller (or independent auditor on controller's behalf) has the right to:

- Audit Processor compliance with this DPA and DSGVO at least annually
- Conduct unannounced inspections (≥2 weeks' notice)
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
- **Termination for convenience** (30/60/90 days' notice)

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
