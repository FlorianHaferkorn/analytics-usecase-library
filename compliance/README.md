# DSGVO Compliance Documentation

## Overview

This directory contains the compliance documentation package for the Analytics Use Case Library, tailored for German market procurement requirements under DSGVO (Datenschutz-Grundverordnung / EU General Data Protection Regulation).

This package addresses the primary objections from mid-size German customers during procurement: data protection impact assessment, processor agreements, retention policy, and EU hosting guarantees. All documents are designed to be completed collaboratively between the technology team and legal counsel.

**Note:** All templates reference DSGVO articles and are structured to support the legal team's workflow. Placeholders marked with **⚠️ TO BE COMPLETED BY LEGAL:** must be filled with organization-specific legal language before customer delivery.

---

## Document Map and DSGVO Alignment

| Document | Purpose | DSGVO Articles | Customer Requirement | Status |
|---|---|---|---|---|
| [DPIA.md](./DPIA.md) | Data Protection Impact Assessment | Art. 35 (DPIA requirement); Art. 5 (principles) | Risk transparency; Privacy by design review | Template structure |
| [AVV_Template.md](./AVV_Template.md) | Auftragsverarbeitungsvertrag (DPA) | Art. 28 (processing agreements) | Mandatory for all processor relationships | Template + checklist |
| [data_processing_record.md](./data_processing_record.md) | Verzeichnis von Verarbeitungstätigkeiten | Art. 30 (records of processing) | Audit trail; transparency for data subjects | Processing activity log |
| [retention_policy.md](./retention_policy.md) | Data retention & deletion policy | Art. 5(1)(e) (storage limitation) | Governs lifecycle of analytics outputs | Operational rules + implementation ref |
| [eu_hosting_guarantee.md](./eu_hosting_guarantee.md) | EU hosting constraint & subprocessor list | Art. 44–49 (transfers outside EU); Art. 28(4) | Data sovereignty; permitted locations | Cloud region allowlist |

---

## Quick Start for Legal Teams

1. **Start here:** [DPIA.md](./DPIA.md)  
   Assess the scope of personal data processing. Identify which analytics tables (`fact_action_outcome`, `dim_user`, etc.) contain PII. Document the legal basis (Art. 6) for each processing activity.

2. **Next:** [AVV_Template.md](./AVV_Template.md)  
   Use this as a template for all processor relationships (cloud providers, third-party tooling vendors). Customize Sections 2–8 with organization-specific obligations.

3. **Operational rules:** [retention_policy.md](./retention_policy.md) + [data_processing_record.md](./data_processing_record.md)  
   Define how long each data category is retained. Document who processes what, when, and why.

4. **Infrastructure:** [eu_hosting_guarantee.md](./eu_hosting_guarantee.md)  
   Constrain all cloud infrastructure to EU regions. Maintain the subprocessor list for customer audits.

---

## Implementation Notes

### Data Categories in Scope

This package assumes the analytics platform may process:

- **Action names & descriptions** (from `action_codes/`) – potentially PII if linked to user identity
- **User identifiers** (from dimension tables) – direct identifiers
- **Audit logs** (technical metadata) – timestamps, IPs, user session IDs
- **KPI fact tables** (e.g., `fact_action_outcome`) – aggregated analytics, may contain de-identified cohorts or direct identifiers depending on schema design

The DPIA should explicitly classify each table and determine whether masking, aggregation, or pseudonymization is required at storage or query time.

### Processing Activity Record (Art. 30)

See [data_processing_record.md](./data_processing_record.md) for a structured log of processing activities. This table should be maintained alongside the technical data dictionary and updated whenever a new use case or report accesses personal data.

### Retention Tiers

The platform defines three retention tiers on `fact_action_outcome` (see [retention_policy.md](./retention_policy.md)):

- **`3y`**: Standard retention (3 years); typical for action analytics
- **`7y`**: Extended retention (7 years); for compliance/audit trails
- **`indef`**: Indefinite retention; only for aggregated, anonymized data

The nightly deletion job (`tooling/generator/maintenance/prune_expired_rows.py`) will enforce these tiers. ⚠️ TO BE COMPLETED BY LEGAL: Confirm retention tier classifications for each use case.

### Subprocessor Updates

Whenever a new cloud service, API, or third-party tool is onboarded, the subprocessor list in [AVV_Template.md](./AVV_Template.md) and [eu_hosting_guarantee.md](./eu_hosting_guarantee.md) must be updated and communicated to customers (typically within 30 days per Art. 28(2) DSGVO). A change-control process should be documented in project governance.

---

## Review Checklist (Legal/DPO)

- [ ] **DPIA scope confirmed:** All tables containing personal data are documented and risk-assessed
- [ ] **Legal basis identified:** Art. 6 justification is present for each processing activity
- [ ] **AVV finalized:** DPA templates have been reviewed and signed with all processors
- [ ] **Retention policy signed off:** Data lifecycle is approved by DPO and business owners
- [ ] **EU hosting locked down:** All cloud regions comply with Terraform constraints; no transfers outside EU without SCCs
- [ ] **Subprocessor list current:** All third-party tools and cloud services are listed and approved

---

## File Structure

```
compliance/
  ├── README.md (this file)
  ├── DPIA.md
  ├── AVV_Template.md
  ├── data_processing_record.md
  ├── retention_policy.md
  └── eu_hosting_guarantee.md
```

---

## Contact & Governance

⚠️ TO BE COMPLETED BY LEGAL: Add contact info for the DPO and legal review team, and define the approval workflow for changes to compliance documentation.

For technical questions about data flows, schema, or infrastructure, contact the analytics engineering team. For legal interpretation of DSGVO requirements, escalate to the Data Protection Officer.

---

## Version History

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-04-22 | Analytics Team | Initial compliance skeleton; templates created for legal team |

---

**Last reviewed:** (to be completed by legal team)  
**Next review scheduled:** (to be completed by legal team)
