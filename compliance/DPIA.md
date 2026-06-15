# Data Protection Impact Assessment (DPIA)

**Regulation:** DSGVO Article 35  
**Document Version:** 1.0  
**Last Updated:** 2026-04-22  
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
| **Accidental data export:** Unmasked PII in exports | Low | High | PII detection; export governance; DLP | Low |
| **Retention violation:** Data not deleted after expiry | Medium | Medium | Automated prune job; audit trail | Medium |
| **Unauthorized international transfer:** Data moved to non-EU region | Low (with constraints) | Critical | Terraform enforcement; subprocessor audit | Low |

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
| **Automated deletion** | Nightly prune job: `tooling/generator/maintenance/prune_expired_rows.py` |

### 6.2 Organizational Measures

| Measure | Implementation |
|---|---|
| **DPA (Data Processing Agreement)** | Art. 28 DSGVO compliant with all processors |
| **Data protection training** | Annual DSGVO training for all data-access personnel |
| **Incident response plan** | Breach detection, reporting, remediation within 72 hours (Art. 33) |
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
- [ ] DPO confirms supervisory authority consultation is NOT required under Art. 36(4) DSGVO
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

**Document prepared by:** Analytics Team  
**Legal review pending:** Yes  
**Next review date:** (to be scheduled by DPO)
