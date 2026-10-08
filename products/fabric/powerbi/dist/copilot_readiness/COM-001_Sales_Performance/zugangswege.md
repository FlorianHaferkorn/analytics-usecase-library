# Zugang über Microsoft 365 Copilot (Chat und Cowork) — COM-001

Quelle: ALUCA (Adapter über den Meridian-Kern), Felder aus dem gespiegelten Meridian-Modul `zugangswege` (D-681, SIG-2609-001).

Fachanwender fragen die Power-BI-Daten dieses Use Case auch außerhalb von Power BI ab. Beide Wege sind Kriterien der Copilot-Readiness. Sie sind nicht dasselbe wie Copilot im Copilot-Bereich des Berichts.

| Kriterium | Microsoft 365 Copilot Chat | Microsoft 365 Copilot Cowork (Fabric-IQ-Plugin) |
|---|---|---|
| Status bei Microsoft | GA (allgemein verfügbar) | GA (allgemein verfügbar) |
| Lizenz je Nutzer | Microsoft 365 Copilot Premium | Microsoft 365 Copilot mit nutzungsbasierter Cowork-Abrechnung |
| Zugriff in Power BI | Berechtigung und Lizenz für Bericht und Semantic Model | mindestens Leserecht auf Bericht und Semantic Model |
| Zeilen- und Objektsicherheit gilt | RLS, OLS | RLS |
| Unterstützte Kapazitäten | Pro, PPU, Premium, Fabric | laut Quelle offen |
| Nicht unterstützte Kapazitäten | Embedded A, Embedded EM | laut Quelle offen |
| Eigene Fabric-Kapazität nötig | laut Quelle offen | nein |
| Regionen nur mit Power BI | nein | laut Quelle offen |
| DLP wirkt | ja | nein |
| Antwort nennt den Bericht | laut Quelle offen | nein |
| Verified Answers und Schema-Auswahl wirken | laut Quelle offen | ja |
| Datenstand der Antwort | letzter erfolgreicher Refresh des Semantic Models | laut Quelle offen |

„Laut Quelle offen“ heißt: Die Microsoft-Seite des Zugangswegs sagt dazu nichts.

## Verified Answers

- Im Copilot-Bereich eines Power-BI-Berichts liefert Copilot keine Verified Answers, wenn dort Fabric IQ eingeschaltet ist.
- Cowork unterstützt Verified Answers und die Schema-Auswahl.
- Für Copilot Chat nennt Learn dazu nichts.

Quelle: https://learn.microsoft.com/power-bi/create-reports/copilot-prepare-data-ai-verified-answers (gelesen 2026-10-07).

## DLP auf Microsoft 365 Copilot (Lizenzstufe)

- Eine DLP-Richtlinie kann Copilot die Verarbeitung gelabelter Power-BI-Inhalte verbieten. Das setzt Microsoft 365 E5 oder die Purview-Suite voraus.
- Mit E3 oder Business Premium wirkt DLP nur auf Prompts.
- In Cowork wird DLP laut Learn nicht unterstützt (Zeile „DLP wirkt“).

Einordnung und Quelle: `compliance/DPIA.md, Abschnitt 12.4` (ADR-0025, SIG-2609-002).

## Tenant-Einstellungen

Microsoft 365 Copilot Chat:

- Microsoft 365 Admin Center: „Fabric data available in M365 Copilot“ (nötig: immer, ab Werk an)
- Fabric-Verwaltungsportal: „Share Fabric data with your Microsoft 365 services“ (nötig: Berichte in Suche und Anhang-Menü, sonst nur per Link oder Name)
- Fabric-Verwaltungsportal: „Data sent to Azure OpenAI can be processed outside your capacity's geographic region, compliance boundary, or national cloud instance“ (nötig: Fabric-Tenant außerhalb USA und EU)

Quelle: https://learn.microsoft.com/fabric/iq/connectors/microsoft-365-copilot-overview (gelesen 2026-10-02, gegengeprüft 2026-10-07)

Microsoft 365 Copilot Cowork (Fabric-IQ-Plugin):

- Microsoft 365 Admin Center: „Fabric data available in M365 Copilot“ (nötig: immer, ab Werk an)
- Fabric-Verwaltungsportal: „Share Fabric data with your Microsoft 365 services“ (nötig: Berichte in Suche und Anhang-Menü, sonst nur per Link oder Name)

Quelle: https://learn.microsoft.com/fabric/iq/connectors/cowork-overview (gelesen 2026-10-02, gegengeprüft 2026-10-07)
