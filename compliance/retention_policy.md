# Data Retention and Deletion Policy

**Regulation:** DSGVO Article 5(1)(e) (Storage Limitation Principle)  
**Document Type:** Data Lifecycle Policy  
**Version:** 1.0  
**Effective Date:** (to be completed by legal team)  
**Last Updated:** 2026-04-22

---

## 1. Executive Summary

DSGVO Article 5(1)(e) establishes the **storage limitation principle**: personal data must be kept in a form which permits identification of data subjects for no longer than is necessary for the purposes for which the data are processed.

This retention policy defines:

- **Retention tiers** (3-year, 7-year, indefinite) and their business justifications
- **Data categories** subject to each tier
- **Deletion mechanisms** (automated nightly job + manual procedures for special cases)
- **Exceptions** (legal holds, litigation, regulatory investigations)
- **Audit trail** for all deletion operations
- **Roles and responsibilities** for retention governance

⚠️ TO BE COMPLETED BY LEGAL: Review and approve retention tier classifications for all use cases in consultation with business owners and the DPO.

---

## 2. Retention Tiers

### 2.1 Tier 1: Short-Term Retention (30 Days)

| Aspect | Details |
|---|---|
| **Tier ID** | `30d` |
| **Retention Period** | 30 calendar days from creation date |
| **Business Justification** | Real-time security monitoring and performance troubleshooting require recent logs only. Older logs are archived; raw entries are deleted after 30 days. |
| **Data Categories** | Server logs, raw access logs, session IDs, IP addresses, device fingerprints, real-time security alerts |
| **Example Tables / Fields** | `audit_log.raw_events`, `cloudwatch_logs.stream`, security monitoring systems |
| **Deletion Method** | Automated daily job; older partitions purged via lifecycle policies (AWS S3 Lifecycle, database time-based retention) |
| **Legal Basis** | Art. 5(1)(e) DSGVO (storage limitation); no longer needed for stated purpose after 30 days |
| **Exceptions** | Active security investigation (legal hold); audit trail preserved for legal discovery |
| **Responsible Team** | Infrastructure / Security team |

### 2.2 Tier 2: Standard Retention (3 Years)

| Aspect | Details |
|---|---|
| **Tier ID** | `3y` |
| **Retention Period** | 3 calendar years from creation date |
| **Business Justification** | ⚠️ TO BE COMPLETED BY LEGAL: Standard retention for operational analytics and business intelligence. Most KPIs are trended over 12–24 months; 3-year retention supports year-over-year analysis and rolling forecasts. |
| **Data Categories** | User action outcomes, aggregated cohort statistics, event timestamps, behavioral attributes (de-identified or pseudonymized) |
| **Example Tables / Fields** | `fact_action_outcome` (without personal identifiers), `fact_events` (aggregated), `dim_cohort_metrics` |
| **Deletion Method** | Automated nightly prune job: `tooling/generator/maintenance/prune_expired_rows.py` (to be implemented; see Section 5) |
| **Legal Basis** | Art. 5(1)(e) DSGVO; business need for quarterly/annual trend analysis and historical comparison |
| **Exceptions** | Active use case development (retain for use case lifetime); litigation or regulatory investigation (legal hold); see Section 3 |
| **Responsible Team** | Data engineering / Analytics team; retention governance via DPO approval |
| **Review Frequency** | Annually; business owners confirm 3-year period is still required |

### 2.3 Tier 3: Extended Retention (7 Years)

| Aspect | Details |
|---|---|
| **Tier ID** | `7y` |
| **Retention Period** | 7 calendar years from creation date |
| **Business Justification** | ⚠️ TO BE COMPLETED BY LEGAL: Compliance and audit trail requirements. Korrigiert 2026-09-25: § 257 Abs. 4 HGB schreibt **10 Jahre** (Handelsbücher, Inventare, Abschlüsse, Lageberichte u. a.), **8 Jahre** (Buchungsbelege) und **6 Jahre** (empfangene/abgesandte Handelsbriefe) vor. Die Frist beginnt mit dem Schluss des Kalenderjahres (Abs. 5)[^1]. Eine 7-Jahres-Frist ergibt sich aus § 257 HGB nicht. ⚠️ UNKLAR: Der zuvor genannte „Grundsatz der Geschäftsmäßigkeit“ ist nicht belegt; § 257 Abs. 3 HGB verweist auf die „Grundsätze ordnungsmäßiger Buchführung“. Ob Analytics-/Audit-Daten überhaupt unter § 257 HGB fallen, entscheidet Legal (C-10). Action audit logs and compliance records must be retained for regulatory inspections and legal disputes. |
| **Data Categories** | Action code execution audit trail, compliance-related events, employee approval logs, legal hold records, transaction ledgers |
| **Example Tables / Fields** | `fact_action_outcome` (with actor names), `audit_log.action_execution`, `compliance_events`, `transaction_ledger` |
| **Deletion Method** | Automated nightly prune job with legal hold verification (Section 5); manual legal approval required before deletion |
| **Legal Basis** | Art. 5(1)(e) DSGVO + Art. 6(1)(c) DSGVO (legal obligation – HGB tax/accounting records, soweit einschlägig; Fristen siehe oben); necessary for tax, legal, and regulatory compliance |
| **Exceptions** | Active litigation, regulatory investigation, or legal hold: retain indefinitely until legal team approves deletion |
| **Responsible Team** | Compliance / Legal team; DPO oversight; quarterly legal hold review |
| **Review Frequency** | Annually; legal team confirms 7-year period is still required by law |

### 2.4 Tier 4: Indefinite Retention (No Expiry)

| Aspect | Details |
|---|---|
| **Tier ID** | `indef` |
| **Retention Period** | No automatic deletion; retained until contract termination or data subject request |
| **Business Justification** | ⚠️ TO BE COMPLETED BY LEGAL: Aggregated, fully anonymized data (no individual re-identification possible) can be retained indefinitely per Art. 5 DSGVO, as anonymized data is outside DSGVO scope. |
| **Data Categories** | Fully anonymized aggregate statistics (no user-level detail), de-identified trend reports, anonymized benchmarks (k-anonymity ≥ 5 minimum cohort size) |
| **Example Tables / Fields** | `fact_kpi_summary` (no user IDs), `report_trend_anonymous` (aggregate-only), `benchmark_metrics` (industry data) |
| **Deletion Method** | No automated deletion; only deleted upon explicit data subject request (e.g., customer account deletion) or contract termination |
| **Legal Basis** | N/A – data is anonymized and outside DSGVO scope (Art. 4(1) DSGVO definition of personal data). No legal basis required. |
| **Exceptions** | If re-identification is possible (even theoretically), reclassify as `3y` or `7y` tier immediately. See Section 2.5. |
| **Responsible Team** | Analytics team; data classification review annually |
| **Review Frequency** | Quarterly (assess anonymization status; if weakened, reclassify) |

### 2.5 Data Reclassification Rule

If a data element is initially classified as `indef` (anonymized) but later found to enable re-identification:

1. **Immediately flag** the data element in the data dictionary
2. **Reclassify to `3y` or `7y`** tier (depending on legal basis for retention)
3. **Trigger a new DPIA** (Art. 35) if re-identification risk is material
4. **Notify the DPO** and legal team within 5 business days
5. **Set deletion date** to 3 or 7 years from reclassification date (not original creation date)

Example: A "cohort segment" field was anonymized (n=1000 per segment); later analysis shows that combining with external datasets enables re-identification of individuals (n<50 per segment). Reclassify from `indef` to `3y` immediately.

---

## 3. Exceptions and Legal Holds

### 3.1 Legal Hold Procedure

Notwithstanding the retention tiers above, personal data must be retained indefinitely if:

- **Active litigation or legal dispute** is pending (Rechtsstreit, Geltendmachung von Ansprüchen)
- **Regulatory investigation** is underway (Datenschutzbehörde inquiry, tax audit, labor inspection)
- **Data subject request or complaint** is pending (DSAR, objection, complaint to supervisory authority)
- **Contract dispute** with a customer or processor is unresolved

### 3.2 Legal Hold Procedure Steps

| Step | Owner | Timeline | Action |
|---|---|---|---|
| 1 | Legal team / Compliance | Upon litigation notice | Issue "legal hold" notice to all data teams; identify affected data elements and tables |
| 2 | Data engineering | Within 5 business days | Confirm data is flagged in the system; disable automated deletion for affected tables; confirm in writing to legal team |
| 3 | Legal team | Quarterly | Review legal hold status; confirm whether litigation/investigation is still active |
| 4 | Legal team | Upon resolution | Issue "legal hold release" notice; confirm in writing to data engineering team |
| 5 | Data engineering | Within 30 days of release | Resume normal retention/deletion schedule; set new deletion date (e.g., 3 years from now for `3y` tier) |

### 3.3 Legal Hold Register

Maintain a register of all active legal holds:

| Hold ID | Affected Table(s) | Legal Issue | Effective Date | Expected Resolution Date | Owner |
|---|---|---|---|---|---|
| LH-2026-001 | `fact_action_outcome`, `audit_log.action_execution` | (to be completed by legal team) | (to be completed by legal team) | (to be completed by legal team) | (to be completed by legal team) |
| (to be added as needed) | (to be completed by legal team) | (to be completed by legal team) | (to be completed by legal team) | (to be completed by legal team) | (to be completed by legal team) |

---

## 4. Schema Implementation

### 4.1 Retention Tier Column

All fact tables containing personal data (or quasi-identifiers) must include a `retention_tier` column:

```sql
CREATE TABLE fact_action_outcome (
  action_id UUID PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,  -- pseudonymized user ID
  action_code_id VARCHAR(100) NOT NULL,
  outcome VARCHAR(50) NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  retention_tier VARCHAR(10) NOT NULL DEFAULT '3y',  -- '30d', '3y', '7y', 'indef', or 'hold'
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  legal_hold_id VARCHAR(50),  -- reference to legal hold (if applicable)
  -- ... other columns
);
```

### 4.2 Retention Tier Values

| Value | Meaning | Deletion Date Calculation |
|---|---|---|
| `30d` | Short-term (30 days) | `created_at` + 30 days |
| `3y` | Standard (3 years) | `created_at` + 3 years |
| `7y` | Extended (7 years) | `created_at` + 7 years |
| `indef` | Indefinite (anonymized) | Never delete (unless data subject request) |
| `hold` | Legal hold (indefinite) | Never delete until legal_hold_id is cleared |

### 4.3 Default Retention Assignment

⚠️ TO BE COMPLETED BY TECH: Define how retention_tier is assigned at record creation:

- **Option A:** Application logic assigns tier based on use case ID and data classification
- **Option B:** Default to `3y` for all new records; legal/DPO reclassifies to `7y` or `indef` after review
- **Option C:** Batch assignment at ETL load time based on data dictionary

**Current approach:** (to be completed by tech team)

---

## 5. Automated Deletion Mechanism

### 5.1 Prune Job Overview

⚠️ TO BE COMPLETED BY TECH: The nightly prune job (`tooling/generator/maintenance/prune_expired_rows.py`) is responsible for identifying and deleting expired personal data.

⚠️ Stand 2026-09-25: Weder das Skript noch die Konfiguration `core/config/retention_policy.yaml` existieren im Repo (git ls-files). Abschnitt 5 beschreibt ein **Soll**, keinen Ist-Zustand (C-08).

| Aspect | Specification |
|---|---|
| **Script location** | `tooling/generator/maintenance/prune_expired_rows.py` |
| **Execution schedule** | Nightly at [**02:00 UTC / 03:00 UTC / Other**] (to be defined by ops team) |
| **Dry-run mode** | Enabled by default; `--confirm-delete` flag required to actually delete data (prevents accidents) |
| **Logging** | All deletion operations logged to `compliance.deletion_audit_log` table; includes: table name, row count deleted, retention tier, timestamp, operator |
| **Deletion method** | Hard delete (not soft delete); cryptographic erasure if PII is not already pseudonymized |
| **Backup handling** | Deleted rows are NOT recoverable from database backups after 30 days (backup retention aligned with deletion completion) |

### 5.2 Prune Job Algorithm

```
For each fact table containing retention_tier column:
  1. Identify all rows where retention_tier != 'hold'
  2. Calculate expiry date: created_at + retention_tier_duration
  3. Filter: expiry_date <= TODAY
  4. Verify legal_hold_id is NULL (no active legal hold)
  5. Log deletion operation (table, row count, tier, timestamp)
  6. IF --confirm-delete flag is set:
       DELETE rows from table
       Log successful deletion to compliance.deletion_audit_log
     ELSE:
       Print preview (row count, example rows) and exit
  7. Verify deletion with SELECT COUNT(*) on affected date range
  8. Alert ops/compliance if deletion fails or row count mismatch detected
```

### 5.3 Pre-Deletion Checklist

Before running the deletion job, verify:

- [ ] **Backup is current:** Latest backup completed within 24 hours
- [ ] **No active legal holds:** Query legal hold register (Section 3.3); confirm no holds on affected tables
- [ ] **Dry-run successful:** Run with default (dry-run) mode; review row counts and preview
- [ ] **Compliance approval:** DPO or legal team has approved deletion (if tier is `7y`)
- [ ] **Operator authority:** Only ops/compliance team members can run with `--confirm-delete` flag

### 5.4 Example Prune Job Execution

```bash
# Dry-run (preview what will be deleted)
python3 tooling/generator/maintenance/prune_expired_rows.py \
  --repo-root . \
  --config core/config/retention_policy.yaml

# Output:
# Dry-run mode enabled
# Table: fact_action_outcome
#   Rows expiring today (tier=3y): 15,432
#   Examples to delete: [row_id_1, row_id_2, ...]
# Table: audit_log.action_execution
#   Rows expiring today (tier=7y): 892
#   Examples to delete: [row_id_X, row_id_Y, ...]
# Total rows to delete: 16,324
# To confirm deletion, run with --confirm-delete flag

# Confirm deletion
python3 tooling/generator/maintenance/prune_expired_rows.py \
  --repo-root . \
  --config core/config/retention_policy.yaml \
  --confirm-delete

# Output:
# Deleting 16,324 rows...
# Deletion complete
# Log entries written to compliance.deletion_audit_log
# Deletion report: tooling/logs/prune_2026-04-22.log
```

### 5.5 Deletion Audit Log

All deletions are logged to `compliance.deletion_audit_log`:

| Column | Type | Example |
|---|---|---|
| `deletion_id` | UUID | `12345678-1234-1234-1234-123456789012` |
| `table_name` | VARCHAR | `fact_action_outcome` |
| `row_count_deleted` | INTEGER | `15432` |
| `retention_tier` | VARCHAR | `3y` |
| `date_range_affected` | DATE RANGE | `[2023-01-01, 2023-04-22]` |
| `deleted_at_timestamp` | TIMESTAMP | `2026-04-22 02:30:45 UTC` |
| `operator` | VARCHAR | `prune_automation` or username if manual |
| `legal_hold_cleared` | BOOLEAN | `false` (indicates no hold was active) |
| `backup_verified` | BOOLEAN | `true` (backup older than 30 days, safe to delete) |
| `notes` | TEXT | `Routine nightly prune; 3-year retention expiry` |

**Access control:** Only DPO, legal team, and compliance officers can query this log.

---

## 6. Manual Deletion Procedures

### 6.1 Data Subject Deletion Requests (Art. 17 DSGVO)

When a data subject requests deletion ("right to be forgotten"), follow this procedure:

| Step | Owner | Timeline | Action |
|---|---|---|---|
| 1 | Customer service / Legal | Upon request receipt | Log DSAR in DSAR tracking system (Section 2.4 / ACT-004, data_processing_record.md; Verweis korrigiert 2026-09-25) |
| 2 | Data engineering | Within 5 business days | Identify all tables containing personal data for this subject; prepare deletion plan |
| 3 | Legal team | Within 10 business days | Review deletion plan; confirm no legal hold applies; approve deletion |
| 4 | Data engineering | Within 5 days of approval | Execute deletion (hard delete or cryptographic erasure); log to deletion_audit_log |
| 5 | Data engineering | Same day | Verify deletion with SELECT COUNT(*) query; provide deletion certificate to legal team |
| 6 | Legal team | Within one month total (Art. 12 Abs. 3 DSGVO; verlängerbar um zwei Monate mit Begründung)[^2] | Respond to data subject with confirmation of deletion; include deletion certificate if requested |

⚠️ TO BE COMPLETED BY LEGAL: Document exceptions (e.g., "We cannot delete X table because legal hold LH-2026-001 applies").

### 6.2 Contract Termination Deletion

When a customer contract terminates:

| Step | Owner | Timeline | Action |
|---|---|---|---|
| 1 | Procurement / Contract team | Upon termination date | Notify data engineering and legal team of contract end |
| 2 | Legal team | Within 5 business days | Determine deletion obligation per contract; check for legal holds or regulatory requirements |
| 3 | Data engineering | Within 15 days of legal approval | Execute bulk deletion or export (customer choice per DPA Section 9, AVV_Template.md) |
| 4 | Data engineering | Same day | Log deletion to deletion_audit_log; provide deletion certificate to legal team |
| 5 | Legal team | Within 30 days | Return deletion certificate to customer; confirm end of processing |

---

## 7. Monitoring and Compliance Verification

### 7.1 Quarterly Compliance Review

Every quarter, the compliance team shall:

1. **Query deletion_audit_log** for the past 90 days; verify all deletions are documented
2. **Compare** actual deletion dates to expected dates (per retention tiers); flag anomalies
3. **Check legal holds:** Verify all active legal holds are listed in Section 3.3 and are current
4. **Data classification review:** Sample 100+ rows from each tier (`3y`, `7y`, `indef`); confirm correct tier assignment
5. **Test prune job:** Run dry-run of next month's scheduled prune; verify row counts and preview
6. **Report to DPO:** Summary of deletions, compliance status, and any issues; sign-off on next month's prune

### 7.2 Audit Trail Integrity

The deletion_audit_log itself must be retained indefinitely (as it is the evidence of DSGVO compliance) and protected from tampering: ⚠️ UNKLAR (2026-09-25): widerspricht dem Punkt „archived copy retained for 7 years“ unten. Außerdem enthält das Log Operator-Namen (personenbezogen), sodass eine unbefristete Aufbewahrung zu Art. 5 Abs. 1 lit. e passen muss; Legal klärt (C-15).

- [ ] Append-only table (no UPDATE or DELETE allowed on existing rows)
- [ ] Encrypted at rest (AES-256)
- [ ] Access control: DPO + legal team only
- [ ] Monthly integrity check (hash of entire log computed and compared to previous month)
- [ ] Backed up daily; archived copy retained for 7 years

---

## 8. Exception Procedures

### 8.1 Deletion Rollback (Emergency)

If a deletion is executed by mistake (e.g., wrong date range, wrong table):

1. **STOP all further deletions immediately** (kill prune job if running)
2. **Alert DPO and legal team** within 1 hour (critical incident)
3. **Restore from backup** (preferably within 4 hours; RTO = 4 hours, RPO = 24 hours)
4. **Audit the deletion:** Determine root cause (operator error, bug in prune logic, etc.)
5. **File incident report** (Section 6.2 „Incident response plan“, DPIA.md; Verweis korrigiert 2026-09-25); notify supervisory authority if data loss is material and cannot be recovered
6. **Implement corrective action:** Update prune job logic, add additional verification, or retrain operator

### 8.2 Retention Extension (Business Request)

⚠️ TO BE COMPLETED BY LEGAL: If a business owner requests extending retention beyond the standard tier (e.g., keep `3y` data for 5 years), follow this procedure:

1. **Submit written request** to DPO / compliance team; include business justification
2. **DPO review:** Confirm extension complies with DSGVO Art. 5(1)(e) (storage limitation); verify legal basis is still valid
3. **Approval or denial:** DPO approves in writing or denies with explanation
4. **Implementation:** If approved, update retention_tier in data dictionary; add note to Section 4.2 above
5. **Audit trail:** Log approval in compliance system; include sunset date (when extension expires)

---

## 9. Review Checklist (Legal/DPO)

- [ ] **Retention tiers defined:** All four tiers (`30d`, `3y`, `7y`, `indef`) have clear business justifications and legal bases (Section 2)
- [ ] **Data classification complete:** Every fact table has a retention_tier column with appropriate default values
- [ ] **Prune job implemented:** Automated deletion mechanism is operational and tested (Section 5)
- [ ] **Legal hold procedure established:** Legal team has authority to place and release holds; register is maintained (Section 3)
- [ ] **Audit trail immutable:** Deletion_audit_log is append-only, encrypted, and retained indefinitely
- [ ] **DSGVO compliance verified:** Retention tiers comply with Art. 5(1)(e) (storage limitation) and all legal bases are documented
- [ ] **Data subject rights supported:** Procedures for Art. 17 (deletion) requests are documented and operational (Section 6.1)
- [ ] **Quarterly monitoring scheduled:** DPO has calendar reminders for compliance reviews (Section 7.1)
- [ ] **Stakeholder communication:** Business owners and teams understand the retention policy and tier assignments
- [ ] **Exception handling ready:** Legal hold, deletion rollback, and extension procedures are defined and communicated

---

## 10. Appendices

### 10.1 Related Documents

- [DPIA.md](./DPIA.md) – Data Protection Impact Assessment (Section 5 risk table „Retention violation“; Section 7 residual risks – Verweis korrigiert 2026-09-25, vorher „Section 5.2“)
- [AVV_Template.md](./AVV_Template.md) – Data Processing Agreement (Section 9 covers data deletion upon termination)
- [data_processing_record.md](./data_processing_record.md) – Processing activity register (each activity specifies retention)
- core/config/retention_policy.yaml – Technical configuration file (to be created by tech team) — ⚠️ existiert nicht; der frühere Link `../../core/…` zeigte zudem aus `compliance/` heraus über die Repo-Wurzel hinaus (C-08)

### 10.2 Glossary

- **Storage Limitation (Art. 5(1)(e)):** Personal data must be kept no longer than necessary for the processing purpose
- **Right to be Forgotten (Art. 17):** Data subject's right to request erasure of personal data
- **Legal Hold:** Administrative order to retain data beyond normal retention period due to litigation, investigation, or regulatory requirement
- **Retention Tier:** Classification of personal data indicating how long it should be retained (30d, 3y, 7y, indef)
- **Prune Job:** Automated process that identifies and deletes expired personal data per retention tiers
- **Anonymization:** Irreversible processing of data so the subject is no longer identifiable (outside DSGVO scope)
- **Pseudonymization:** Processing using a salt/key so data cannot be linked to a subject without additional information (still subject to DSGVO)

### 10.3 External References

- DSGVO Art. 5(1)(e) – Storage Limitation: https://eur-lex.europa.eu/eli/reg/2016/679/oj/deu (Primärquelle; vorher nur BfDI-Startseite)
- ~~EDPB Guidelines 05/2020 – Data Protection Impact Assessment~~ — korrigiert 2026-09-25: Die EDPB-Leitlinien 05/2020 betreffen die **Einwilligung**, nicht die DSFA (https://www.edpb.europa.eu/our-work-tools/our-documents/guidelines/guidelines-052020-consent-under-regulation-2016679_en). Für die DSFA in DE: DSK-Muss-Liste nach Art. 35 Abs. 4, Version 1.1 vom 17.10.2018 (https://www.datenschutzkonferenz-online.de/media/ah/20181017_ah_DSK_DSFA_Muss-Liste_Version_1.1_Deutsch.pdf). ⚠️ UNKLAR: Die passende EDPB/WP29-DSFA-Leitlinie (vermutlich WP 248 rev.01) wurde nicht an der Primärquelle geprüft.
- Handelsgesetzbuch (HGB) § 257 – German commercial record retention (10/8/6 Jahre, nicht 7; korrigiert 2026-09-25): https://www.gesetze-im-internet.de/hgb/__257.html

---

## 11. Version History

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-04-22 | Analytics & Legal Teams | Initial retention policy skeleton; 4 tiers defined; prune job framework documented |
| 1.1 | 2026-09-25 | Inhaltliche Durchsicht (kein Legal-Sign-off) | HGB-§-257-Fristen korrigiert, EDPB-Fehlreferenz ersetzt, Querverweise repariert, nicht existente Pfade markiert |

**Last reviewed by:** (to be completed by DPO)  
**Next review date:** (to be completed by DPO – typically Q2 2026) — ⚠️ Stand 2026-09-25: überfällig (C-19)

---

**Document maintained by:** Data Protection Officer / Compliance Team  
**Confidentiality:** Internal – shared with business owners for tier assignment decisions

**Offene Punkte:** Studio-KI-Daten, LLM-Telemetrie und Studio-Nutzerdaten haben keinen Tier und keine Löschregel (C-01 bis C-03, siehe `_INDEX.md`). Abhängigkeit: „AI data handling policy“ (in Arbeit).

[^1]: § 257 HGB: https://www.gesetze-im-internet.de/hgb/__257.html
[^2]: DSGVO (EUR-Lex): https://eur-lex.europa.eu/eli/reg/2016/679/oj/deu — Wortlaut Art. 12 Abs. 3 abgeglichen über https://dsgvo-gesetz.de/art-12-dsgvo/
