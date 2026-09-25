# DSGVO Compliance Documentation

## Overview

This directory contains the compliance documentation package for ALUCA (Analytics Library of Use Cases), tailored for German market procurement requirements under DSGVO (Datenschutz-Grundverordnung / EU General Data Protection Regulation).

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

- **Action names & descriptions** (from `core/action_codes/`; Pfad korrigiert 2026-09-25) – potentially PII if linked to user identity
- **User identifiers** (from dimension tables) – direct identifiers
- **Audit logs** (technical metadata) – timestamps, IPs, user session IDs
- **KPI fact tables** (e.g., `fact_action_outcome`) – aggregated analytics, may contain de-identified cohorts or direct identifiers depending on schema design

The DPIA should explicitly classify each table and determine whether masking, aggregation, or pseudonymization is required at storage or query time.

### Processing Activity Record (Art. 30)

See [data_processing_record.md](./data_processing_record.md) for a structured log of processing activities. This table should be maintained alongside the technical data dictionary and updated whenever a new use case or report accesses personal data.

### Retention Tiers

The platform defines four retention tiers (see [retention_policy.md](./retention_policy.md), Abschnitt 2; korrigiert 2026-09-25 – bisher „three“, der Tier `30d` fehlte):

- **`30d`**: Short-term (30 days); raw security/access logs
- **`3y`**: Standard retention (3 years); typical for action analytics
- **`7y`**: Extended retention (7 years); for compliance/audit trails — ⚠️ § 257 Abs. 4 HGB nennt 10/8/6 Jahre, nicht 7 (siehe retention_policy.md 2.3)[^3]
- **`indef`**: Indefinite retention; only for aggregated, anonymized data

The nightly deletion job (`tooling/generator/maintenance/prune_expired_rows.py`) will enforce these tiers. ⚠️ Stand 2026-09-25: Die Datei existiert im Repo nicht (git ls-files) – automatisierte Löschung ist derzeit nicht implementiert (Ledger C-08). ⚠️ TO BE COMPLETED BY LEGAL: Confirm retention tier classifications for each use case.

### Subprocessor Updates

Whenever a new cloud service, API, or third-party tool is onboarded, the subprocessor list in [AVV_Template.md](./AVV_Template.md) and [eu_hosting_guarantee.md](./eu_hosting_guarantee.md) must be updated and communicated to customers **before** the change takes effect. Art. 28 Abs. 2 DSGVO verlangt bei allgemeiner Genehmigung die Information über jede *beabsichtigte* Änderung mit Einspruchsmöglichkeit; eine 30-Tage-Frist steht nicht im Gesetz, sie ist eine vertragliche Festlegung (siehe AVV_Template.md 5.2)[^1]. (Korrigiert 2026-09-25; vorher „within 30 days per Art. 28(2)“.) A change-control process should be documented in project governance.

---

## Review Checklist (Legal/DPO)

- [ ] **DPIA scope confirmed:** All tables containing personal data are documented and risk-assessed
- [ ] **Legal basis identified:** Art. 6 justification is present for each processing activity
- [ ] **AVV finalized:** DPA templates have been reviewed and signed with all processors
- [ ] **Retention policy signed off:** Data lifecycle is approved by DPO and business owners
- [ ] **EU hosting locked down:** All cloud regions comply with Terraform constraints; no transfers outside EU without a transfer mechanism (Art. 45/46 DSGVO) — ⚠️ Terraform liegt im Repo nur als leere Platzhalter-Ordner vor (Ledger C-08)
- [ ] **Subprocessor list current:** All third-party tools and cloud services are listed and approved

---

## File Structure

```
compliance/
  ├── _INDEX.md (Einstieg, Register, Ledger offener Punkte)
  ├── README.md (this file)
  ├── DPIA.md
  ├── AVV_Template.md
  ├── data_processing_record.md
  ├── retention_policy.md
  └── eu_hosting_guarantee.md
```

---

## Geltungsbereich und Repo-Abgleich (Durchsicht 2026-09-25)

Das Paket (Stand 2026-04-22) beschreibt eine generische Analytics-Plattform (Fakt-/Dimensionstabellen, Action Codes, Security-Logs). Der Repo-Stand vom 2026-09-25 enthält zusätzlich Komponenten, die im Paket **nicht** abgedeckt sind – u. a. die Studio-App mit KI-Routen (Discovery-Chat, KI-Chat, Wizard, Factsheet-Entwurf), LLM-Telemetrie, Benutzer-/Organisations-/Audit-Verwaltung, Project Runner / agentic loop, Fabric-Export und Tenant-Settings sowie den SAP-Konnektor. Welche personenbezogenen Daten dabei an welche Anbieter (insbesondere LLM-Anbieter) gehen, ist im Paket nicht dokumentiert. Diese Lücken sind **nicht** ergänzt, sondern als offene Punkte im Ledger in [_INDEX.md](./_INDEX.md) erfasst (C-01 bis C-06). Abhängigkeit: Eine „AI data handling policy“ wird in einer anderen Arbeitssitzung erstellt (noch nicht committet); VVT, DSFA und AVV sind danach nachzuziehen.

**Nachtrag 2026-09-25 (Studio-KI):** Die AI data handling policy liegt im Code-Stand PR #478 vor („Govern AI data handling and contain model egress“, noch nicht gemergt). Daraus ist die Studio-KI jetzt dokumentiert: DSFA-Abschnitt 11 (Datenfluss, Kontrollen, Risiken, Fakten zum AI Act), VVT ACT-006/ACT-007, AVV 5.3 und Hosting 3.4. Kernbefund: In diesem Stand ist jede Übermittlung an LLM-Anbieter im Code gesperrt. Anbieter, Region und Transfergrundlage bleiben Platzhalter. Ledger: C-01, C-02, C-11 und C-12 teilweise erledigt; neu hinzugekommen sind C-21 bis C-23.

## Rechtsstand-Abgleich (Durchsicht 2026-09-25)

Geprüft am 25.09.2026 an den angegebenen Quellen. Dies ist eine Dokumentationsprüfung, **keine Rechtsberatung**; die Bewertung obliegt Legal/DSB.

| Thema | Stand 25.09.2026 | Bezug im Paket | Quelle |
|---|---|---|---|
| EU AI Act (VO (EU) 2024/1689) | In Kraft seit 01.08.2024. Seit 02.02.2025 gelten die Verbote und die Pflicht zur KI-Kompetenz, seit 02.08.2025 die GPAI-Pflichten und die Governance-Regeln. Seit 02.08.2026 gilt die Verordnung allgemein, einschließlich der Transparenzpflichten nach Art. 50. | Bisher nicht erwähnt. Relevant für die KI-Funktionen in Studio → C-11 | [^4] |
| AI-Omnibus (VO (EU) 2026/1744 vom 08.07.2026) | Im ABl. am 24.07.2026, in Kraft seit 27.07.2026. Hochrisiko-Pflichten verschoben: Annex III auf 02.12.2027, Annex I auf 02.08.2028. Art. 4 wurde neu gefasst: Statt KI-Kompetenz „sicherzustellen“, sind nun Maßnahmen zu ihrer Förderung zu ergreifen. Für Art. 50 gilt eine Übergangsfrist von 4 Monaten für Systeme, die vor dem 02.08.2026 in Verkehr gebracht wurden. | wie oben | [^5] |
| EU-US Data Privacy Framework | Angemessenheitsbeschluss (EU) 2023/1795 vom 10.07.2023 gilt (nur für DPF-zertifizierte US-Organisationen). EuG, T-553/23 *Latombe*: Klage am 03.09.2025 abgewiesen. Rechtsmittel C-703/25 P (eingelegt 31.10.2025). ⚠️ UNKLAR: Der aktuelle Verfahrensstand am EuGH ließ sich nicht an einer Primärquelle prüfen (curia nicht abrufbar); die Angabe stützt sich nur auf eine Sekundärquelle. | eu_hosting_guarantee.md stützte US-Transfers nur auf SCC + Zusatzmaßnahmen → ergänzt | [^6] [^7] [^8] |
| Standardvertragsklauseln | Aktuell für Drittlandübermittlungen: Durchführungsbeschluss (EU) 2021/914 (Module 1–4); die alten SCC sind seit 27.12.2022 nicht mehr nutzbar. Die Kommission erarbeitet zusätzliche SCC für Importeure, die nach Art. 3 Abs. 2 DSGVO selbst der DSGVO unterliegen. (EU) 2021/915 regelt SCC zwischen Verantwortlichem und Auftragsverarbeiter (Art. 28 Abs. 7) und ist **kein** Transferinstrument. | eu_hosting_guarantee.md verlinkte 2021/915 als Transfer-SCC → korrigiert | [^9] [^10] |
| EU Data Act (VO (EU) 2023/2854) | In Kraft seit 11.01.2024, anwendbar seit 12.09.2025. ⚠️ UNKLAR: Gestaffelte spätere Fristen (z. B. für Produktdesign-Pflichten) ließen sich nicht an der Primärquelle prüfen, weil der EUR-Lex-Volltext nicht abrufbar war. | Nicht erwähnt → C-18 | [^11] |
| NIS2-Umsetzung (DE) | Gesetz zur Umsetzung der NIS-2-Richtlinie vom 02.12.2025, BGBl. 2025 I Nr. 301 (verkündet 05.12.2025), in Kraft seit 06.12.2025. Registrierung im BSI-Portal ab 06.01.2026. | Nicht erwähnt → C-17 | [^12] [^13] |
| TTDSG → TDDDG | Der amtliche Kurztitel lautet heute TDDDG (Telekommunikation-Digitale-Dienste-Datenschutz-Gesetz). Das Digitale-Dienste-Gesetz (DDG) ist seit 14.05.2024 in Kraft. | Nicht erwähnt → C-16 | [^14] [^15] |
| Microsoft EU Data Boundary | Phase 3 im Februar 2025 abgeschlossen. Umfasst Microsoft 365, Dynamics 365, Power Platform und Azure (regionale Dienste; nicht-regionale nur nach Konfiguration), jeweils mit dienstspezifischen Voraussetzungen. Begrenzte Übermittlungen in Sicherheitsfällen bleiben möglich. ⚠️ UNKLAR: Power BI und Microsoft Fabric werden auf der EUDB-Übersichtsseite nicht ausdrücklich genannt. | eu_hosting_guarantee.md („Microsoft committed to EU data residency“) → präzisiert; C-06 | [^16] [^17] |
| DSGVO-Artikelbezüge | Am Normtext geprüft: Art. 12 Abs. 3, Art. 28 Abs. 2/3/4, Art. 30 Abs. 4/5, Art. 33 Abs. 1/2, Art. 36 Abs. 1/4, Art. 46 Abs. 2 lit. b / Abs. 3 lit. b, Art. 47. Fehlzitate in DPIA.md, data_processing_record.md, AVV_Template.md und eu_hosting_guarantee.md wurden korrigiert. | siehe Dateien | [^1] |
| HGB § 257 | Aufbewahrungsfristen: 10 Jahre (Handelsbücher, Abschlüsse u. a.), 8 Jahre (Buchungsbelege), 6 Jahre (Handelsbriefe). Die Frist beginnt mit dem Schluss des Kalenderjahres (Abs. 5). | retention_policy.md nannte pauschal „7 Jahre“ → korrigiert; C-10 | [^3] |

---

## Contact & Governance

⚠️ TO BE COMPLETED BY LEGAL: Add contact info for the DPO and legal review team, and define the approval workflow for changes to compliance documentation.

For technical questions about data flows, schema, or infrastructure, contact the analytics engineering team. For legal interpretation of DSGVO requirements, escalate to the Data Protection Officer.

---

## Version History

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-04-22 | Analytics Team | Initial compliance skeleton; templates created for legal team |
| 1.1 | 2026-09-25 | Inhaltliche Durchsicht (Agent, kein Legal-Sign-off) | Rechtsstand-Abgleich, Repo-Abgleich, Fehlzitate/Querverweise korrigiert; offene Punkte → _INDEX.md-Ledger |
| 1.2 | 2026-09-25 | Inhaltliche Durchsicht (Agent, kein Legal-Sign-off) | Studio-KI aus Code-Stand PR #478 eingearbeitet (DSFA 11, VVT ACT-006/007, AVV 5.3, Hosting 3.4); Ledger C-01/02/11/12 teilweise, neu C-21 bis C-23 |

---

**Last reviewed:** (to be completed by legal team)  
**Next review scheduled:** (to be completed by legal team)  
**Inhaltliche Durchsicht (ohne Legal-Sign-off):** 2026-09-25

---

## Quellen (Durchsicht 2026-09-25)

[^1]: DSGVO, VO (EU) 2016/679 (EUR-Lex): https://eur-lex.europa.eu/eli/reg/2016/679/oj/deu — Wortlaut der zitierten Absätze abgeglichen über die Textwiedergabe https://dsgvo-gesetz.de/art-28-dsgvo/ (bzw. art-12, art-30, art-33, art-36, art-46, art-47), da der EUR-Lex-Volltext maschinell nicht abrufbar war.
[^3]: § 257 HGB: https://www.gesetze-im-internet.de/hgb/__257.html
[^4]: EU-Kommission, AI Act – Zeitplan: https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai
[^5]: VO (EU) 2026/1744 (AI-Omnibus), ABl. L vom 24.07.2026: https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=OJ:L_202601744
[^6]: EuGH-Pressemitteilung 106/25 zu T-553/23: https://curia.europa.eu/site/upload/docs/application/pdf/2025-09/cp250106en.pdf
[^7]: EU-Kommission, Angemessenheitsbeschlüsse: https://commission.europa.eu/law/law-topic/data-protection/international-dimension-data-protection/adequacy-decisions_en
[^8]: Sekundärquelle zum Rechtsmittel C-703/25 P: https://digitalpolicyalert.org/event/35459-latombe-filed-appeal-against-general-court-dismissal-of-challenge-to-european-unionunited-states-data-protection-framework-adequacy-decision-in-latombe-v-commission
[^9]: Durchführungsbeschluss (EU) 2021/914: https://eur-lex.europa.eu/eli/dec_impl/2021/914/oj/eng ; Durchführungsbeschluss (EU) 2021/915: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32021D0915
[^10]: EU-Kommission, SCC Q&A: https://commission.europa.eu/law/law-topic/data-protection/international-dimension-data-protection/new-standard-contractual-clauses-questions-and-answers-overview_en
[^11]: EU-Kommission, Data Act: https://digital-strategy.ec.europa.eu/en/policies/data-act
[^12]: BGBl. 2025 I Nr. 301: https://www.recht.bund.de/bgbl/1/2025/301/VO.html
[^13]: BSI-Pressemitteilung 05.12.2025: https://www.bsi.bund.de/DE/Service-Navi/Presse/Pressemitteilungen/Presse2025/251205_NIS-2-Umsetzungsgesetz_in_Kraft.html
[^14]: TDDDG (gesetze-im-internet.de, Kurztitel): https://www.gesetze-im-internet.de/ttdsg/
[^15]: BfDI, Digitale Dienste (DDG seit 14.05.2024): https://www.bfdi.bund.de/DE/Buerger/Inhalte/Telemedien/Telemedien.html
[^16]: Microsoft, Abschluss EU Data Boundary (26.02.2025): https://blogs.microsoft.com/on-the-issues/2025/02/26/microsoft-completes-landmark-eu-data-boundary-offering-enhanced-data-residency-and-transparency/
[^17]: Microsoft Learn, What is the EU Data Boundary?: https://learn.microsoft.com/en-us/privacy/eudb/eu-data-boundary-learn
