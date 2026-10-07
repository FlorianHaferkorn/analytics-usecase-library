# ADR-0023 — Exportwege aus Power BI werden nach Labelvererbung bewertet

| Feld | Wert |
|---|---|
| Status | **Accepted** (01.10.2026) |
| Entscheider | Florian Haferkorn |
| Kontext | Signal-Register (Meridian D-623): SIG-2609-026 Excel-Export bis 500.000 Zeilen, Folge-Signal SIG-2610-002 aus der Learn-Gegenprobe; Entscheidungsvorlage „Paket B“ im Freelancing-Repo (`research/signale/vorschlaege/2026-10-01_Entscheidung_Paket-B-Governance-Kontrollen.md`) |
| Betrifft | `compliance/DPIA.md` Abschnitt 5 und 6.1 · `compliance/_INDEX.md` C-27 |
| Bezug | Meridian D-627 (`admin_settings.py` #32 bis #35 mit Feldern `label_vererbung`, `max_zeilen`) |

## 1. Kontext

Die DPIA führte den Export nur pauschal („export governance; DLP“). Learn (gelesen 01.10.2026)
unterscheidet drei Formate mit verschiedener Labelvererbung: Excel mit Live-Verbindung erbt das
Label des Semantikmodells, statisches Excel das des Berichts, CSV trägt keines. Labelbasierte
Zugriffskontrolle greift für CSV und TXT nicht.

## 2. Entscheidung

Die DPIA bewertet Export nach Format. Empfehlung: Excel offen lassen, wie Microsoft für die meisten
Nutzer rät; CSV nur für eine Sicherheitsgruppe, wenn der Kunde Sensitivity Labels nutzt. Die vier
Tenant-Einstellungen stehen in Meridians Bauplan (`admin_settings.py`) mit Feldern, nicht als Prosa.

## 3. Belege (Learn, gelesen 01.10.2026)

- `power-bi/visuals/power-bi-visualization-export-data`: Excel live bis 500.000, Excel bis
  150.000, CSV bis 30.000; „The first two support sensitivity labels“.
- `fabric/governance/information-protection`, Abschnitt „Access control“: keine labelbasierte
  Zugriffskontrolle für Export nach .csv oder .txt.
- `fabric/admin/service-admin-portal-export-sharing`: die vier Einstellungen.
- `power-bi/guidance/powerbi-implementation-planning-info-protection`: Export für die meisten
  Nutzer offen lassen.

## 4. Folgen

- C-27, Status teilweise. Die Zeilengrenze für „Data with current layout“ bleibt ⚠️ UNKLAR
  (Feature Summary 500.000, Learn 150.000); für die Maßnahme unerheblich.
