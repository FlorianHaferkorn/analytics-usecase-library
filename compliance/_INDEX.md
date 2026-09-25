---
last-reviewed: 2026-09-25
shelf-life-days: 90
---
# compliance — Zentraler Anlaufpunkt (_INDEX)

> Einstieg in `compliance/`. Zuerst diese Datei lesen, dann gezielt zum Doc —
> nicht den ganzen Ordner. DSGVO-Dokumentationspaket für DE-Markt-Beschaffung;
> `⚠️ TO BE COMPLETED BY LEGAL`-Platzhalter füllt die Rechtsabteilung, nicht der Agent.

## „Lies-wenn"-Routing (Token-Disziplin)

| Deine Aufgabe ist … | Lies | NICHT nötig |
|---|---|---|
| Überblick / DSGVO-Mapping / Legal-Quickstart | `README.md` | Rest |
| PII-Tabellen klassifizieren, Risiko + Rechtsgrundlage (Art. 6) | `DPIA.md` | AVV, Hosting |
| Auftragsverarbeiter-Vertrag (Cloud/Vendor) aufsetzen | `AVV_Template.md` | DPIA, Retention |
| Aufbewahrungsdauer/Löschung einer Datenkategorie klären | `retention_policy.md` | AVV, DPIA |
| Cloud-Region oder Subprozessor prüfen/hinzufügen | `eu_hosting_guarantee.md` | DPIA, Retention |
| Verarbeitungstätigkeit dokumentieren (Art. 30) | `data_processing_record.md` | AVV, Hosting |

## Dokument-Register (vollständig — Drift-Gate erzwingt das)

| Doc | Zweck | Lies-wenn |
|---|---|---|
| `README.md` | Paket-Übersicht, DSGVO-Artikel-Mapping, Quickstart für Legal | Erstkontakt; verschafft den Gesamtüberblick |
| `DPIA.md` | Datenschutz-Folgenabschätzung (Art. 35): PII-Scope, Risiko, Rechtsgrundlage | Du klassifizierst Tabellen oder bewertest Verarbeitungs-Risiken |
| `AVV_Template.md` | Auftragsverarbeitungsvertrag-Vorlage (Art. 28) inkl. Checkliste | Du setzt einen DPA mit einem Prozessor/Vendor auf |
| `retention_policy.md` | Aufbewahrungs-/Löschrichtlinie (Art. 5(1)(e)): Tiers 30d/3y/7y/indef | Du legst Lebenszyklus/Löschung von Analytics-Outputs fest |
| `eu_hosting_guarantee.md` | EU-Hosting-Zusicherung + Subprozessor-Liste (Art. 44–49, 28(4)) | Du prüfst Datensouveränität oder onboardest einen Cloud-Dienst |
| `data_processing_record.md` | Verzeichnis von Verarbeitungstätigkeiten (Art. 30) | Eine neue Use Case / ein Report greift auf personenbezogene Daten zu |

## Offene Punkte (Ledger — hier abhaken)

> Durchsicht 2026-09-25 (inhaltlich, ohne Legal-Sign-off). Rechtsstand und Quellen stehen in `README.md`, Abschnitt „Rechtsstand-Abgleich“. Abhängigkeit für C-01 bis C-03: Eine „AI data handling policy“ entsteht in einer anderen Sitzung (noch nicht committet); danach VVT, DSFA, AVV und Subprozessorliste nachziehen.

| ID | Punkt | Status | Datum |
|---|---|---|---|
| C-01 | Studio-KI (`studio/src/app/api/ai/`, Discovery-Chat, Wizard, Factsheet-Entwurf) übermittelt Kundendaten und Projektkontext an LLM-Anbieter. Das ist weder im VVT noch in der DSFA oder der AVV-/Subprozessorliste erfasst (Anbieter, Region, Transfergrundlage, Speicherdauer unbekannt). Abhängig von der AI data handling policy | offen | 2026-09-25 |
| C-02 | LLM-Telemetrie (LLM-Event-Repository unter `studio/src/lib/db/`): Inhalt (Prompts? Nutzerbezug?) und Löschfrist undefiniert; kein Retention-Tier | offen | 2026-09-25 |
| C-03 | Studio-Nutzer-, Organisations-, RBAC-, Audit- und Benachrichtigungsdaten (`studio/src/lib/db/`) haben keinen VVT-Eintrag und keine Löschregel | offen | 2026-09-25 |
| C-04 | SAP-Konnektor (`tooling/connectors/sap/`, `studio/plugins/sap-connector/`): ERP-Datenimport ohne VVT-/AVV-Abdeckung; Verhältnis zu ACT-005 klären | offen | 2026-09-25 |
| C-05 | Project Runner / agentic loop (`tooling/agentic_loop/`, `tooling/superversion/project_package/`): Ob personenbezogene Daten verarbeitet oder an LLMs gesendet werden, ist ⚠️ UNKLAR | offen | 2026-09-25 |
| C-06 | Fabric-/Power-BI-Export und Tenant-Settings: Microsoft (Power BI/Fabric) fehlt als Empfänger bzw. Unterauftragsverarbeiter. Ob die EU Data Boundary Power BI/Fabric abdeckt, ist ⚠️ UNKLAR (auf der EUDB-Übersichtsseite nicht genannt) | offen | 2026-09-25 |
| C-07 | Rolle Verantwortlicher/Auftragsverarbeiter ungeklärt (DSFA §2, VVT-„Controller“-Felder leer, ACT-005 „joint controller or processor“). Im AV-Fall fehlt das Verzeichnis nach Art. 30 Abs. 2 | offen | 2026-09-25 |
| C-08 | Beschriebene Kontrollen existieren nicht im Repo: prune_expired_rows.py, retention_policy.yaml (unter core/config), enforce_eu_only_regions.sh; Terraform nur `.gitkeep`. Die DSFA-Restrisiken („Low“) stützen sich darauf | offen | 2026-09-25 |
| C-09 | Subprozessorliste unbelegt: Audit-Daten Jan./Feb. 2026 vor der Paketerstellung, „DPO Approved: Yes“ ohne benannten DSB, Google Cloud nur in §10 der Hosting-Doku | offen | 2026-09-25 |
| C-10 | Tier `7y` passt nicht zu § 257 Abs. 4 HGB (10/8/6 Jahre). Legal klärt, ob Analytics-/Audit-Daten überhaupt unter § 257 fallen, und passt das Tier-Modell an | offen | 2026-09-25 |
| C-11 | EU AI Act: Art. 50 gilt seit 02.08.2026, Art. 4 wurde durch VO (EU) 2026/1744 geändert. Die Einordnung der Studio-KI (Anbieter/Betreiber, Transparenz) fehlt | offen | 2026-09-25 |
| C-12 | DSFA-Pflicht für die Studio-KI prüfen (DSK-Muss-Liste Nr. 11, KI) | offen | 2026-09-25 |
| C-13 | AVV-Vorlage: Art. 28 Abs. 3 lit. a (Drittland nur auf Weisung) und lit. f (Unterstützung Art. 32–36) sind nicht ausdrücklich geregelt; widersprüchliche Angaben zu Prüfungen und Kündigungsfristen; keine SCC-Regelung | offen | 2026-09-25 |
| C-14 | Regionsangaben inkonsistent: „AWS westeurope“ (Azure-Name) in VVT und AVV; die CI-Allowlist ohne northeurope/GCP weicht von den genehmigten Regionen ab | offen | 2026-09-25 |
| C-15 | Log-Aufbewahrung widersprüchlich: Audit-Logs 1 Jahr (DSFA 6.1, AVV 6.2) vs. Audit-Trail 7 Jahre (ACT-002); deletion_audit_log „indefinitely“ vs. Archiv 7 Jahre | offen | 2026-09-25 |
| C-16 | TDDDG (§ 25 Endgeräte-Zugriff): Speicherung und Zugriff im Browser durch die Studio-Web-App (Session/Auth) sind nicht bewertet | offen | 2026-09-25 |
| C-17 | NIS2 (BSIG n. F., seit 06.12.2025): Betroffenheit von Betreiber und Kunden nicht bewertet | offen | 2026-09-25 |
| C-18 | EU Data Act (seit 12.09.2025 anwendbar): Relevanz nicht bewertet; gestaffelte Fristen ⚠️ UNKLAR | offen | 2026-09-25 |
| C-19 | Review-Termine „Q2 2026“ in VVT, Retention und Hosting überfällig. Legal-/DSB-Sign-off fehlt im gesamten Paket | offen | 2026-09-25 |
| C-20 | DPF: Rechtsmittel C-703/25 P gegen EuG T-553/23 anhängig (Stand ⚠️ UNKLAR, nur Sekundärquelle). Bei US-Empfängern DPF-Zertifizierung und SCC-Fallback prüfen | offen | 2026-09-25 |
