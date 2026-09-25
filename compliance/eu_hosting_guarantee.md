# EU Hosting Guarantee and Subprocessor Data Localization Policy

**Regulation:** DSGVO Articles 44–49 (International Data Transfers); Art. 28(2) (Genehmigung von Unterauftragsverarbeitern) und Art. 28(4) (Weitergabe der Pflichten) – korrigiert 2026-09-25[^1]  
**Document Type:** Data Localization Policy  
**Version:** 1.0  
**Effective Date:** (to be completed by legal team)  
**Last Updated:** 2026-04-22  
**Inhaltliche Durchsicht (ohne Legal-Sign-off):** 2026-09-25 – siehe Abschnitt 13

---

## 1. Executive Summary

This document establishes the technical and contractual requirements for data localization within the European Union, ensuring compliance with DSGVO restrictions on international data transfers (Art. 44–49).

**Key principle:** All personal data must remain within the EU/EEA at rest and in transit, unless the organization has executed Standard Contractual Clauses (SCCs, Art. 46(2)(c) DSGVO) or the third country has been granted an adequacy decision (Art. 45 DSGVO).

This policy covers:

- **Allowed cloud regions** (EU-only; Terraform-enforced)
- **Subprocessor localization requirements** (SaaS vendors, cloud providers, APIs)
- **Data transfer risk assessment** (Art. 44–49 compliance checklist)
- **Contractual safeguards** (SCCs, DPA amendments, supplementary measures)
- **Monitoring and audit procedures** (quarterly subprocessor review)

⚠️ TO BE COMPLETED BY LEGAL: Confirm the organization's data transfer strategy (no transfers vs. SCCs-based transfers) and the approval process for any exceptions.

---

## 2. Allowed EU/EEA Cloud Regions

### 2.1 Approved Regions by Cloud Provider

| Cloud Provider | Service | Approved Region(s) | Code | Notes |
|---|---|---|---|---|
| **AWS** | EC2, RDS, S3, Lambda, Glue | EU (Frankfurt) | `eu-central-1` | Germany; no egress to US |
| **AWS** | EC2, RDS, S3, Lambda | EU (Ireland) | `eu-west-1` | Ireland; GDPR-compliant data center |
| **Azure** | Virtual Machines, SQL Database, Storage | West Europe (Netherlands) | `westeurope` | Amsterdam; Microsoft EU Data Boundary: laut Microsoft seit Februar 2025 abgeschlossen (Phase 3). Gilt für regionale Azure-Dienste in EU-Regionen, für nicht-regionale nur nach Konfiguration; begrenzte Übermittlungen in Sicherheitsfällen bleiben möglich[^2] |
| **Azure** | Database, Compute | North Europe (Ireland) | `northeurope` | Dublin; backup region for redundancy |
| **Google Cloud** | Compute Engine, BigQuery, Cloud Storage | EU (Belgium) | `europe-west1` | Brussels; EU data center |
| **Google Cloud** | Compute Engine, Cloud Storage | EU (Netherlands) | `europe-west4` | Eemshaven; backup region for redundancy |
| **On-premise** | Data center / private infrastructure | Germany / EU country | (N/A) | Fully controlled; no third-party transfer risk |

### 2.2 Prohibited Regions

⚠️ **STRICTLY PROHIBITED — do not use:**

| Provider | Region | Reason |
|---|---|---|
| AWS | us-east-1, us-west-1, us-west-2 | United States – interne Policy-Entscheidung (EU-only). Rechtsstand korrigiert 2026-09-25: Schrems II (Juli 2020) hob den Privacy Shield auf. Seit dem Angemessenheitsbeschluss (EU) 2023/1795 vom 10.07.2023 (EU-US Data Privacy Framework) sind Übermittlungen an **DPF-zertifizierte** US-Organisationen ohne SCC zulässig; für nicht zertifizierte Empfänger gelten weiter Art. 46 (SCC + Transfer Impact Assessment)[^3] |
| AWS | ap-southeast-1, ap-east-1, ap-northeast-1 | Singapore, Hong Kong, Tokyo; outside EU; transfers require SCCs |
| Azure | eastus, westus, centralus | United States; restricted per Schrems II ruling |
| Google Cloud | us-central1, us-east1, us-west1 | United States; restricted per Schrems II ruling |
| Any provider | Any region outside EU/EEA (unless approved exception) | Art. 44–49 DSGVO |

### 2.3 Terraform Infrastructure-as-Code Enforcement

⚠️ TO BE COMPLETED BY TECH: All cloud resources must be deployed with region constraints enforced at the Terraform level. Example:

```hcl
# Terraform constraint for AWS
provider "aws" {
  region = "eu-central-1"  # OR eu-west-1
  
  default_tags {
    tags = {
      Compliance = "EU_ONLY"
      DSGVO      = "REQUIRED"
    }
  }
}

# Validation: reject non-EU regions
variable "allowed_regions" {
  type        = list(string)
  description = "EU-only regions per DSGVO Art. 44–49"
  default     = ["eu-central-1", "eu-west-1", "westeurope", "northeurope"]
  
  validation {
    condition     = contains(var.allowed_regions, var.aws_region)
    error_message = "Region ${var.aws_region} is outside EU. Use eu-central-1 or eu-west-1."
  }
}

# Example S3 bucket (regional)
resource "aws_s3_bucket" "data_warehouse" {
  bucket = "org-data-warehouse-eu"
  region = "eu-central-1"  # LOCKED to EU
  
  tags = {
    DataClassification = "Personal"
    Compliance         = "DSGVO"
  }
}

# Block accidental cross-region replication
resource "aws_s3_bucket_replication_configuration" "deny_us_replication" {
  bucket = aws_s3_bucket.data_warehouse.id
  
  # Explicitly forbid US replication
  # All replication targets must be eu-* regions
}
```

⚠️ Stand 2026-09-25: Im Repo gibt es keinen Terraform-Code; unter `products/open_source_stack/deploy/terraform/{aws,azure,gcp}/` liegen nur `.gitkeep`-Platzhalter. Das unten genannte Skript `tooling/ci/enforce_eu_only_regions.sh` existiert nicht. Das Beispiel oben vermischt außerdem AWS- und Azure-Regionsnamen in einer AWS-Variable. Die jq-Allowlist unten lässt `northeurope` und die GCP-Regionen aus 2.1 nicht zu. Beides ist Soll-Beschreibung, keine Kontrolle (C-08, C-14).

**CI/CD enforcement:** Every Terraform apply is validated by a linter that rejects non-EU region provisioning. Example:

```bash
#!/bin/bash
# tooling/ci/enforce_eu_only_regions.sh

terraform plan -json | jq '.resource_changes[] | 
  select(.type | test("aws_|azurerm_|google_")) | 
  .change.after.region // .change.after.location | 
  select(. != null and . != "eu-central-1" and . != "eu-west-1" and . != "westeurope")' | \
  grep -q . && {
    echo "ERROR: Non-EU regions detected in Terraform plan. Aborting."
    exit 1
  }

echo "✓ All resources in EU regions"
```

---

## 3. Subprocessor Localization Inventory

### 3.1 Approved Subprocessors (EU-Only)

All third-party vendors (SaaS, APIs, cloud services) must be reviewed and approved before use. Current approved list:

⚠️ UNKLAR (2026-09-25): Die Audit-Daten (Januar/Februar 2026) liegen vor der Erstellung dieses Pakets (2026-04-22). Für „DPA signed“ bzw. „DPO Approved: Yes“ (Abschnitt 10) gibt es im Repo keine Nachweise, und kein DSB ist benannt. Google Cloud steht in Abschnitt 10, fehlt aber hier. Es fehlen die LLM-Anbieter der Studio-KI-Funktionen sowie Microsoft Power BI/Fabric (C-01, C-06, C-09).

| Subprocessor | Service | Data Processed | Location | SCC/DPA Status | Audit Date |
|---|---|---|---|---|---|
| **Amazon Web Services (AWS)** | Cloud infrastructure (EC2, RDS, S3, KMS, Lambda, Glue, CloudTrail, CloudWatch) | All personal data at rest and in transit (encrypted) | Frankfurt (eu-central-1), Dublin (eu-west-1) | DPA: Data Processing Addendum signed | 2026-01-15 |
| **Microsoft Azure** | Cloud infrastructure (optional backup/redundancy); Virtual Machines, SQL Database | (if used) All personal data | Amsterdam (westeurope), Dublin (northeurope) | DPA: Standard Contractual Clauses included | 2026-02-01 |
| **Snowflake** | Data warehouse / BI platform | User action outcomes, aggregated metrics (pseudonymized) | EU edition: hosted on AWS eu-central-1 | DPA: Data Processing Addendum signed | 2026-01-20 |
| **Segment / mParticle** | Event data collection and routing (if used) | Event stream, user identifiers, behavioral data | EU data center (location to be verified) | DPA: Under review | ⚠️ TO BE COMPLETED |
| **(to be added)** | (to be completed by legal team) | (to be completed by legal team) | EU (to be verified) | (to be completed by legal team) | (to be completed by legal team) |

### 3.2 Prohibited Subprocessors (Non-EU)

⚠️ **DO NOT USE** the following services without explicit legal approval and SCC amendment:

⚠️ UNKLAR (2026-09-25): Die Anbieterangaben in dieser Tabelle (Serverstandorte, fehlende SCC, EU-Optionen) wurden nicht geprüft. Seit dem 10.07.2023 kann zudem eine DPF-Zertifizierung des US-Anbieters die Übermittlungsgrundlage sein[^3].

| Service | Reason | Alternative (EU) |
|---|---|---|
| Google Analytics (standard) | Transmits data to US servers; no SCC by default | Matomo (EU-hosted) or Plausible (EU) |
| Mixpanel | Default: US servers without SCC coverage | Amplitude (EU option available) or local tracking |
| Intercom | US-based; requires SCC review | Crisp or Zendesk (EU option) |
| Datadog (US region) | US-based by default; EU SaaS edition available | Datadog EU SaaS (Paris region) or Grafana (EU-hosted) |
| Salesforce (standard) | US servers; EU SCC available but requires review | Salesforce EU SaaS or alternative CRM |
| HubSpot (standard) | US-based; EU data processing available but limited | Pipedrive (EU) or Zoho (EU) |

⚠️ TO BE COMPLETED BY LEGAL: Any use of non-EU services requires:

1. Legal review and written approval
2. Execution of Standard Contractual Clauses (SCCs) or Binding Corporate Rules (BCRs)
3. Supplementary technical measures per Schrems II (assessment of third-country surveillance laws)
4. Documentation in Section 3.3 below (Approved Exceptions)
5. Quarterly compliance review with DPO

### 3.3 Approved Exceptions (Non-EU with SCC Coverage)

⚠️ TO BE COMPLETED BY LEGAL: If an exception is approved, document it here:

| Service | Location | Legal Basis for Transfer | SCC Effective Date | DPO Approval | Supplementary Measures | Review Date |
|---|---|---|---|---|---|---|
| (example: "US Analytics Vendor XYZ") | (US: Virginia) | SCC Module 2 (controller-processor); Art. 46(2)(c) DSGVO | (date signed) | (DPO name, date) | (encryption, pseudonymization, etc.) | (quarterly) |
| (to be completed by legal) | (to be completed by legal) | (to be completed by legal) | (to be completed by legal) | (to be completed by legal) | (to be completed by legal) | (to be completed by legal) |

**Important:** Every exception carries residual risk (see DPIA.md Section 7.2) and must be reviewed quarterly by the DPO.

---

## 4. Data Transfer Risk Assessment (Art. 44–49 Compliance)

### 4.1 Transfer Triggers

Personal data may be transferred outside the EU only if:

1. **Adequacy decision exists** (Art. 45 DSGVO) – laut EU-Kommission derzeit u. a. Andorra, Argentinien, Färöer, Guernsey, Isle of Man, Israel, Japan, Jersey, Kanada (kommerzielle Organisationen), Neuseeland, Republik Korea, Schweiz, Uruguay, Europäische Patentorganisation sowie die **USA für DPF-zertifizierte Organisationen** (Beschluss (EU) 2023/1795)[^4]. ⚠️ UNKLAR: Der Stand der Verlängerung für das Vereinigte Königreich und des Beschlussentwurfs für Brasilien ist auf der Kommissionsseite nicht eindeutig (korrigiert 2026-09-25; vorher „RARE … only a few countries“).
   - **EU-US Data Privacy Framework, Stand 25.09.2026:** Das EuG hat die Nichtigkeitsklage T-553/23 *Latombe* am 03.09.2025 abgewiesen[^5]. Rechtsmittel C-703/25 P, eingelegt am 31.10.2025[^6]. ⚠️ UNKLAR: Der aktuelle Stand beim EuGH wurde nicht an einer Primärquelle geprüft. Beim Rückgriff auf das DPF sollten Fallback-Klauseln (SCC) vorgehalten werden – Entscheidung Legal (C-20).
2. **Standard Contractual Clauses (SCCs)** are in place (Art. 46(2)(c) DSGVO) – COMMON
3. **Binding Corporate Rules (BCRs)** are in place (Art. 46(2)(b) i. V. m. Art. 47 DSGVO; korrigiert 2026-09-25, vorher „Art. 46(4)“)[^1] – applies to multinational groups
4. **Codes of Conduct or Certification** (Art. 46(2)(e)/(f)) – RARE

**Default rule:** NO transfers outside EU. Any exception requires written legal approval.

### 4.2 SCC Types

Die SCC nach Durchführungsbeschluss (EU) 2021/914 haben vier Module (korrigiert 2026-09-25, vorher „two main SCC modules“)[^7]:

| Module | Use Case | Example |
|---|---|---|
| **Module 1** | Controller → Controller (unilateral) | Sharing analytics data with a business partner in Canada |
| **Module 2** | Controller → Processor (unilateral) | Sending data to a US SaaS vendor for processing |
| **Module 3** | Processor → Processor (data sub-processing) | AWS (EU) outsources backup to a US vendor |
| **Module 4** | Processor → Controller (data return) | Processor returns data to controller in different country |

⚠️ TO BE COMPLETED BY LEGAL: Every SCC must include:

- [ ] **Importer obligations** (e.g., "You may not share data with US government without seeking legal remedy first")
- [ ] **Supplementary measures** (encryption, pseudonymization, access restrictions)
- [ ] **Right to object** if importer believes local law prevents DSGVO compliance
- [ ] **Competent Supervisory Authority** contact — ⚠️ korrigiert 2026-09-25: Der frühere Verweis auf Art. 46(3)(b) DSGVO war falsch; dieser betrifft Verwaltungsvereinbarungen zwischen Behörden[^1]. Die maßgebliche Klausel in den SCC 2021/914 bestimmt Legal.

### 4.3 Schrems II Supplementary Measures Checklist

Following the Schrems II judgment (C-311/18), any transfer to the US or countries with broad surveillance laws requires:

⚠️ TO BE COMPLETED BY LEGAL: Assess each US-based service:

- [ ] **Data minimization:** Only necessary fields transferred; aggregated/anonymized where possible
- [ ] **Encryption:** Data encrypted with keys held outside the jurisdiction (EU custody)
- [ ] **Access controls:** Contractual limits on third-country government access (e.g., "US company will seek to limit government requests")
- [ ] **Transparency:** Company commits to disclosing government data requests to the organization
- [ ] **Legal remedy:** Company commits to initiating legal action against US government requests that violate GDPR
- [ ] **Contractual fallback:** If encryption key is surrendered to US government, company must notify immediately and organization may terminate service

Example supplementary measures language:

> "Importer shall not disclose personal data to any third-country government authority (including law enforcement) without first seeking to obtain a court order, legal authorization, or explicit written consent from the Controller. Importer shall notify Controller immediately if any data is disclosed and shall challenge any demand it deems unlawful."

---

## 5. Contractual Safeguards

### 5.1 DPA Amendments for Subprocessors

Every subprocessor contract (SaaS, cloud provider, API vendor) must include or reference:

| Contractual Element | Section in AVV_Template.md | Responsibility |
|---|---|---|
| **Data Processing Agreement (DPA)** | Section 2–9 | Vendor signs or references their standard DPA |
| **EU/EEA Data Localization** | Section 5.1 (Subprocessor location; Verweis korrigiert 2026-09-25) | Vendor commits to EU-only storage and processing |
| **Data Sub-processing Restrictions** | Section 5 (Sub-processors of sub-processors) | Vendor may not sub-process without written approval |
| **Standard Contractual Clauses (SCCs)** | ⚠️ im AVV_Template.md nicht geregelt (5.2 ist Change Control) – C-13 | Vendor provides SCC documentation or certifies EU-only processing |
| **Data Breach Notification** | Section 6.3 (incident response) | Vendor (als Auftragsverarbeiter) meldet dem Verantwortlichen unverzüglich (Art. 33 Abs. 2); die 72 Stunden betreffen die Meldung des Verantwortlichen an die Aufsichtsbehörde (Art. 33 Abs. 1)[^1] |
| **Data Subject Rights Assistance** | Section 7 | Vendor assists with data access, deletion, portability requests (Art. 12–22) |
| **Audit Rights** | Section 8 | Organization may audit vendor SOC 2 / ISO 27001 compliance |
| **Data Deletion/Return** | Section 9 | Upon termination, vendor deletes or returns all personal data |

### 5.2 Template DPA Amendment for EU-Only Localization

⚠️ TO BE COMPLETED BY LEGAL: Add this clause to all subprocessor contracts:

> **Data Localization Clause (EU-Only)**
> 
> The Processor commits to the following data localization requirements:
> 
> (a) **Primary Commitment:** All personal data shall be stored, processed, and backed up exclusively within the European Union and European Economic Area (EEA). No transfers of personal data outside the EU/EEA are permitted without prior written approval from the Controller and execution of appropriate Standard Contractual Clauses (SCCs) per Art. 46(2)(c) DSGVO.
> 
> (b) **Geographic Restriction:** All cloud infrastructure, databases, and backup systems must be located in the following approved regions:
> - AWS: eu-central-1 (Frankfurt) or eu-west-1 (Dublin)
> - Azure: westeurope (Amsterdam) or northeurope (Dublin)
> - Google Cloud: europe-west1 (Brussels) or europe-west4 (Netherlands)
> - On-premises: Germany or other EU member states
> 
> (c) **Sub-processor Restriction:** The Processor may not engage any sub-processor located outside the EU/EEA without:
> i. At least 30 days' prior written notice to the Controller
> ii. Execution of SCCs between the Processor and the sub-processor
> iii. Execution of an amendment to this DPA incorporating the sub-processor
> iv. Written approval from the Controller
> 
> (d) **Verification:** The Processor shall provide quarterly certifications (signed by an officer of the company) confirming:
> - All data remains within EU regions per subsection (b) above
> - No unauthorized sub-processors have been engaged
> - No data has been disclosed to non-EU governments except as required by law with prior legal challenge
> 
> (e) **Breach of Localization:** If the Processor violates this data localization clause, the Controller may immediately terminate this DPA without notice and pursue remedies per Section [X].

### 5.3 SCC vs. Non-SCC Compliance Status

| Vendor | Service | SCC Required? | SCC Status | Compliance Owner |
|---|---|---|---|---|
| AWS | Cloud infrastructure (eu-central-1, eu-west-1) | ⚠️ Conditional (only if processor is US-based company) | AWS DPA includes SCC Module 3 (processor-to-processor) | AWS / Procurement |
| Azure | Cloud infrastructure (westeurope, northeurope) | ⚠️ Conditional (Microsoft is US-based) | Microsoft DPA includes SCC modules | Microsoft / Procurement |
| Google Cloud | Cloud infrastructure (europe-west1/4) | ⚠️ Conditional (Google is US-based) | Google DPA includes SCC modules | Google / Procurement |
| Snowflake | Data warehouse (EU edition on AWS) | ✓ Required | Snowflake DPA + Addendum A (Standard Contractual Clauses) signed | Snowflake / Procurement |
| (Matomo / on-premises analytics) | Web analytics (self-hosted) | ✗ Not required (EU location) | N/A | Internal / No vendor |
| (To be added) | (to be completed by legal team) | (to be completed by legal team) | (to be completed by legal team) | (to be completed by legal team) |

---

## 6. Monitoring and Audit Procedures

### 6.1 Quarterly Subprocessor Compliance Review

Every quarter (Jan, Apr, Jul, Oct), the compliance team shall:

1. **Request localization attestation** from each subprocessor:
   - Data storage location (actual regions, not just "EU")
   - Backup location (must be EU)
   - Any new sub-processors engaged (require SCC approval)
   - Any government data requests received (with summary of response)

2. **Verify cloud region compliance** via infrastructure audit:
   - Query Terraform state files for region configuration
   - Run CI/CD linter to confirm no non-EU regions
   - Sample recent deployments to verify compliance

3. **Review SCC status:**
   - Confirm all SCC documents are current and signed
   - Check for any changes in vendor's data processing practices
   - Flag any vendors where SCC expires soon (renewal required)

4. **Audit logs review:**
   - Download access logs from cloud providers (CloudTrail, Activity Log, Audit Logs)
   - Verify no data exfiltration to non-EU IPs
   - Confirm encryption keys are retained in EU regions

5. **Report to DPO:**
   - Summary of compliance findings
   - Any non-compliance issues (with remediation plan)
   - Updated subprocessor list (Section 3.1)
   - Recommended actions (e.g., "Terminate service X if SCC cannot be executed")

### 6.2 Annual Third-Party Audit

Once annually (or after major infrastructure change), commission an independent audit:

| Audit Type | Scope | Provider | Frequency | Cost |
|---|---|---|---|---|
| **SOC 2 Type II** (recommended) | Security, availability, data confidentiality | Big 4 or specialized firm (Deloitte, EY, etc.) | Annual | €10,000–50,000 |
| **ISO 27001 Certification** | Information security management system | Accredited certification body | Annual | €5,000–30,000 |
| **GDPR-specific audit** | DSGVO compliance checklist | Law firm or DPA consultant | Biennial | €5,000–20,000 |

Audit findings must be reviewed by the DPO and compliance team; any deficiencies must be remediated within 90 days.

### 6.3 Incident Reporting (Data Transfer Risk)

If any of the following occurs, notify the DPO immediately:

- [ ] Data is discovered outside the EU (e.g., accidental S3 bucket in us-east-1)
- [ ] A subprocessor discloses data to a non-EU government authority
- [ ] A Terraform deployment bypasses region restrictions
- [ ] A new SaaS vendor is added without localization verification
- [ ] A cloud provider announces closure of an EU data center

Procedure:

1. **Immediate containment:** Stop any ongoing transfers; prevent recurrence
2. **Root cause analysis:** What went wrong? Why did controls fail?
3. **Notification:** Alert DPO within 4 hours; alert supervisory authority if necessary (Art. 33 DSGVO if data breach)
4. **Corrective action:** Implement technical/process improvements
5. **Documentation:** Log incident in compliance system; reference in next quarterly review

---

## 7. Change Control for Subprocessors

### 7.1 Subprocessor Onboarding Checklist

Before engaging any new subprocessor (cloud provider, SaaS vendor, API), complete:

⚠️ TO BE COMPLETED BY PROCUREMENT/LEGAL:

| Step | Owner | Checklist | Approval |
|---|---|---|---|
| 1 | Tech team | Identify data processing use case and data categories involved | Product manager |
| 2 | Legal team | Review vendor's DPA and localization terms; assess SCC need | General Counsel |
| 3 | Compliance | Verify vendor operates only in EU regions; obtain written attestation | DPO |
| 4 | Security | Review vendor's SOC 2 / ISO 27001 certification; assess security measures | CISO |
| 5 | Legal | Negotiate and execute DPA amendments (Section 5.2 above); obtain SCC if needed | General Counsel |
| 6 | Compliance | Add vendor to approved subprocessor list (Section 3.1); notify customers if applicable | DPO |
| 7 | Tech team | Deploy service; configure Terraform constraints to enforce EU-only regions | DevOps lead |
| 8 | Compliance | Quarterly monitoring begins (Section 6.1) | DPO |

**Approval gates:** At least TWO of [Legal, Compliance, Security] must approve before deployment.

### 7.2 Change Notification (Art. 28(2) DSGVO)

Before a subprocessor change takes effect (new or replacement), notify all customers in advance so they can object. Art. 28 Abs. 2 DSGVO verlangt die Information über **beabsichtigte** Änderungen[^1]. Die Vorlaufzeit (AVV_Template.md 5.2: ≥ 30 Tage) ist vertraglich. (Korrigiert 2026-09-25; vorher „When a change occurs … notify within 30 days“, im Widerspruch zu AVV 5.2.)

**Email template:**

> **Subprocessor Change Notification**
> 
> Dear [Customer],
> 
> We are writing to inform you of a change to our Data Processing Agreement, effective [DATE].
> 
> **New subprocessor:** [Vendor Name]  
> **Service:** [Description]  
> **Data categories:** [PII, action outcomes, etc.]  
> **Location:** [EU region]  
> **Effective date:** [Date]  
> **Right to object:** You have the right to object to this change within 30 days. Please contact [DPO email].
> 
> **Updated list of subprocessors:** [link to AVV_Template.md Section 5 or public subprocessor list]
> 
> Sincerely,  
> [DPO Name]

---

## 8. Contractual Compliance Checklist

### 8.1 Vendor Contract Review Template

⚠️ TO BE COMPLETED BY LEGAL: When reviewing a new vendor contract, verify:

- [ ] **Data Processing Agreement (DPA)** is included or attached as Exhibit A (mandatory)
- [ ] **EU/EEA data localization** is explicitly stated (no transfers outside EU)
- [ ] **Sub-processor clause** allows controller to authorize/object to sub-processors
- [ ] **Standard Contractual Clauses (SCCs)** are included if vendor is outside EU
- [ ] **Data breach notification** clause (72 hours per Art. 33 DSGVO)
- [ ] **Data subject rights** assistance clause (Art. 12–22 support)
- [ ] **Audit rights** for security audits, SOC 2 reports, or compliance verification
- [ ] **Term and termination** includes data deletion/return on termination
- [ ] **Liability and indemnification** for DSGVO breach (realistic caps, not $1)
- [ ] **Governing law** is EU law (preferably German law for DSGVO compliance)
- [ ] **Dispute resolution** includes escalation to supervisory authority if disagreement

If a critical clause is missing, DO NOT sign. Negotiate amendment or select alternative vendor.

---

## 9. Review Checklist (Legal/DPO)

- [ ] **Cloud regions locked down:** All resources deployed to approved EU regions only; Terraform enforces constraint
- [ ] **Subprocessor list current:** Section 3.1 includes all active vendors with EU-only confirmation
- [ ] **SCCs in place:** All non-EU subprocessors have executed SCCs with supplementary measures
- [ ] **DPA amendments negotiated:** Section 5.2 data localization clause is in all vendor contracts
- [ ] **Quarterly review scheduled:** Compliance team has calendar reminder to audit subprocessors Q1–Q4
- [ ] **Incident procedure defined:** Clear escalation path if data found outside EU
- [ ] **Customer notification process:** Subprocessor changes communicated in advance (≥ 30 days per AVV 5.2)
- [ ] **Terraform CI/CD enforced:** Region validation is automated in every deployment pipeline
- [ ] **No prohibited vendors:** Section 3.2 prohibited services are not used without formal exception and SCC
- [ ] **Audit documentation maintained:** SOC 2 / ISO 27001 reports from all subprocessors are retained for 3 years

---

## 10. Approved Vendors Quick Reference

| Vendor | Service | Region | Status | DPO Approved |
|---|---|---|---|---|
| AWS | Cloud infrastructure | eu-central-1, eu-west-1 | ✓ Approved (DPA in place) | Yes |
| Azure | Cloud infrastructure | westeurope, northeurope | ✓ Approved (DPA in place) | Yes |
| Google Cloud | Data analytics | europe-west1, europe-west4 | ✓ Approved (DPA in place) | Yes |
| Snowflake | Data warehouse | EU-hosted (on AWS) | ✓ Approved (DPA + SCC Addendum A) | Yes |
| (Matomo or Plausible) | Web analytics | Self-hosted EU | ✓ Approved (no vendor involved) | Yes |
| (To be added) | (to be completed by legal) | EU | ⏳ Pending | (to be completed by legal) |

---

## 11. Appendices

### 11.1 Related Documents

- [DPIA.md](./DPIA.md) – Data Protection Impact Assessment (Section 5 risk table „Unauthorized international transfer“, Section 7.2 – Verweis korrigiert 2026-09-25)
- [AVV_Template.md](./AVV_Template.md) – Data Processing Agreement (Section 5 covers sub-processors)
- [data_processing_record.md](./data_processing_record.md) – Processing activity register (each activity specifies location)
- core/config/retention_policy.yaml – Technical configuration (backup location, region enforcement) — ⚠️ existiert im Repo nicht (C-08)

### 11.2 External References

- **DSGVO Art. 44–49** (International Transfers): https://eur-lex.europa.eu/eli/reg/2016/679/oj/deu
- **EDPB Guidance on SCCs**: https://edpb.ec.europa.eu/our-work-tools/publications_en
- **Schrems II Decision (C-311/18)**: https://curia.europa.eu/juris/document/document.jsf?text=&docid=228677&pageIndex=0&doclang=EN
- **Standard Contractual Clauses für Drittlandübermittlungen (2021/914)**: https://eur-lex.europa.eu/eli/dec_impl/2021/914/oj/eng — korrigiert 2026-09-25: Der frühere Link führte auf 2021/915, die SCC zwischen Verantwortlichem und Auftragsverarbeiter nach Art. 28 Abs. 7 (kein Transferinstrument): https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32021D0915
- **EU-US Data Privacy Framework** – Angemessenheitsbeschlüsse der Kommission: https://commission.europa.eu/law/law-topic/data-protection/international-dimension-data-protection/adequacy-decisions_en
- **Terraform AWS region validation example**: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/guides/regions-and-azs

### 11.3 Glossary

- **Data Localization:** Requirement to keep data within a specific geographic region (EU)
- **Adequacy Decision (Art. 45):** EU determination that a third country has adequate data protection laws (rare)
- **Standard Contractual Clauses (SCCs):** Pre-approved contract language (by EU Commission) authorizing transfers to countries without adequacy decisions
- **Schrems II:** 2020 Court of Justice ruling that invalidated Privacy Shield; tightened requirements for US transfers. Seit 10.07.2023 gibt es für DPF-zertifizierte US-Empfänger einen Angemessenheitsbeschluss; sonst gelten SCC + Zusatzmaßnahmen (aktualisiert 2026-09-25)
- **EU-US Data Privacy Framework (DPF):** Angemessenheitsbeschluss (EU) 2023/1795 vom 10.07.2023; gilt nur für zertifizierte US-Organisationen
- **Supplementary Measures:** Additional technical/organizational steps (encryption, pseudonymization, access restrictions) required for transfers to high-surveillance countries like the US
- **Subprocessor:** A third party (vendor, cloud provider) who processes data on behalf of the original processor (under a contract with the processor)
- **Binding Corporate Rules (BCRs):** Internal transfer mechanism for multinational companies (alternative to SCCs)

---

## 12. Version History

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-04-22 | Analytics & Legal Teams | Initial EU hosting guarantee skeleton; 6 approved regions, 5 prohibited services, SCC framework, quarterly audit process |
| 1.1 | 2026-09-25 | Inhaltliche Durchsicht (kein Legal-Sign-off) | DPF ergänzt, SCC-/BCR-/Art.-46-Fehlzitate korrigiert, EU Data Boundary präzisiert, unbelegte Angaben und nicht existente Pfade markiert |

**Last reviewed by:** (to be completed by DPO)  
**Next review date:** (to be completed by DPO – Q2 2026) — ⚠️ Stand 2026-09-25: überfällig (C-19)

---

**Document maintained by:** Data Protection Officer / Compliance Team  
**Confidentiality:** Internal – shared with procurement and technical teams for vendor selection decisions

---

## 13. Offene Punkte (Durchsicht 2026-09-25)

IDs = Ledger in `_INDEX.md`. C-01 (LLM-Anbieter der Studio-KI: Standort, Transfergrundlage, ggf. DPF-Zertifizierung), C-06 (Power BI/Fabric: Region des Kunden-Tenants und EU Data Boundary – ⚠️ UNKLAR: Power BI und Fabric werden auf der EUDB-Übersichtsseite nicht ausdrücklich genannt[^2]), C-08 (Terraform/CI nicht implementiert), C-09 (unbelegte Freigaben), C-14 (Regionsangaben inkonsistent), C-20 (DPF-Rechtsmittel). Abhängigkeit: „AI data handling policy“ (andere Sitzung, nicht committet).

[^1]: DSGVO (EUR-Lex): https://eur-lex.europa.eu/eli/reg/2016/679/oj/deu — Wortlaut Art. 28, 33, 46, 47 abgeglichen über https://dsgvo-gesetz.de/art-46-dsgvo/ u. a.
[^2]: Microsoft, 26.02.2025: https://blogs.microsoft.com/on-the-issues/2025/02/26/microsoft-completes-landmark-eu-data-boundary-offering-enhanced-data-residency-and-transparency/ ; Microsoft Learn: https://learn.microsoft.com/en-us/privacy/eudb/eu-data-boundary-learn
[^3]: EU-Kommission, Angemessenheitsbeschlüsse (inkl. USA/DPF): https://commission.europa.eu/law/law-topic/data-protection/international-dimension-data-protection/adequacy-decisions_en
[^4]: wie [^3]
[^5]: EuGH-Pressemitteilung 106/25: https://curia.europa.eu/site/upload/docs/application/pdf/2025-09/cp250106en.pdf
[^6]: Sekundärquelle: https://digitalpolicyalert.org/event/35459-latombe-filed-appeal-against-general-court-dismissal-of-challenge-to-european-unionunited-states-data-protection-framework-adequacy-decision-in-latombe-v-commission
[^7]: Durchführungsbeschluss (EU) 2021/914: https://eur-lex.europa.eu/eli/dec_impl/2021/914/oj/eng ; SCC-Q&A der Kommission: https://commission.europa.eu/law/law-topic/data-protection/international-dimension-data-protection/new-standard-contractual-clauses-questions-and-answers-overview_en
