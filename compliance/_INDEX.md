---
last-reviewed: 2026-06-16
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
| Auth-Stack (Studio-Login) DSGVO/EU-Hosting/AVV prüfen — ADR-0016 Option A | `auth_stack_data_residency.md` | Analytics-Deliverable-PII (anderer Kontext) |

## Dokument-Register (vollständig — Drift-Gate erzwingt das)

| Doc | Zweck | Lies-wenn |
|---|---|---|
| `README.md` | Paket-Übersicht, DSGVO-Artikel-Mapping, Quickstart für Legal | Erstkontakt; verschafft den Gesamtüberblick |
| `DPIA.md` | Datenschutz-Folgenabschätzung (Art. 35): PII-Scope, Risiko, Rechtsgrundlage | Du klassifizierst Tabellen oder bewertest Verarbeitungs-Risiken |
| `AVV_Template.md` | Auftragsverarbeitungsvertrag-Vorlage (Art. 28) inkl. Checkliste | Du setzt einen DPA mit einem Prozessor/Vendor auf |
| `retention_policy.md` | Aufbewahrungs-/Löschrichtlinie (Art. 5(1)(e)): Tiers 3y/7y/indef | Du legst Lebenszyklus/Löschung von Analytics-Outputs fest |
| `eu_hosting_guarantee.md` | EU-Hosting-Zusicherung + Subprozessor-Liste (Art. 44–49, 28(4)) | Du prüfst Datensouveränität oder onboardest einen Cloud-Dienst |
| `data_processing_record.md` | Verzeichnis von Verarbeitungstätigkeiten (Art. 30) | Eine neue Use Case / ein Report greift auf personenbezogene Daten zu |
| `auth_stack_data_residency.md` | Auth-Stack (next-auth+OpenFGA, ADR-0016 Option A): PII-Inventar, Data-Residency (100% self-hosted EU), AVV-Bedarf (nur Hosting-Provider), Art.-30-Entwurf, Gate-Ergebnis T1 | Du prüfst DSGVO/EU-Hosting des Studio-Logins vor der Auth-Umsetzung |

## Offene Punkte (Ledger — hier abhaken)

| ID | Punkt | Status | Datum |
|---|---|---|---|
| C-1 | Auth-Stack (ADR-0016 Option A) DSGVO/EU-Hosting-Gate (Backlog-T1) | **erledigt** (`auth_stack_data_residency.md`): T1 grün mit 3 Bau-Auflagen (kein Social-IdP im Default, AVV mit EU-Host, OpenFGA nur pseudonyme IDs). **Legal offen:** Rechtsgrundlage Art. 6, Art.-30-Zeile in `data_processing_record.md` übernehmen, AVV abschließen | 2026-07-15 |
