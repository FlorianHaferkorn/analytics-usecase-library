# ADR-0025 — KI-Clients über Fabric IQ MCP gehören als eigener Abfluss in die DPIA

| Feld | Wert |
|---|---|
| Status | **Accepted** (01.10.2026) |
| Entscheider | Florian Haferkorn |
| Kontext | Signal-Register (Meridian D-623): SIG-2609-021 Fabric IQ MCP (GA), SIG-2609-002 Power-BI-Antworten in Microsoft 365 Copilot mit DLP; Entscheidungsvorlage „Paket A“ im Freelancing-Repo (`research/signale/vorschlaege/2026-10-01_Entscheidung_Paket-A-KI-Zugriff.md`) |
| Betrifft | `compliance/DPIA.md` 12.4 · `compliance/_INDEX.md` C-26 |
| Bezug | C-25 (KI-Zugriff je Semantikmodell, DPIA 12.3) · Meridian D-606 (`platform.ai_zugang`), D-644 (Zustimmungsrichtlinie, DLP-Lizenz) |

## 1. Kontext

Fabric IQ MCP ist seit September 2026 allgemein verfügbar. Jeder MCP-fähige KI-Client kann
darüber Power-BI-Berichte und Semantikmodelle lesen und DAX ausführen, mit den Rechten der
angemeldeten Person. Die DPIA kannte bisher nur die Modelleinstellung je Semantikmodell (12.3).
Dass Abfrageergebnisse an den Client und dessen Modellanbieter gehen, stand nirgends.

## 2. Entscheidung

Die DPIA führt den Weg als eigenen Abschnitt 12.4 mit drei Hebeln: Zustimmungsrichtlinie des
Tenants (gilt für den ganzen Endpunkt), Modelleinstellung je Semantikmodell (12.3) und, bei
Microsoft 365 Copilot, Labels und DLP. Die Empfehlung lautet Admin-Genehmigung, bis Kunde und DSB
eine Liste erlaubter Clients beschlossen haben. `ai_egress_measures.md` bleibt unverändert: es
regelt den KI-Abfluss aus ALUCA Studio, nicht den Zugriff fremder Clients auf Kundenmodelle.

## 3. Belege (Learn, gelesen 01.10.2026)

- `fabric/iq/connectors/fabric-iq-mcp`, Abschnitt „Authenticate“: drei delegierte Berechtigungen,
  ab Werk ohne Admin-Zustimmung, vom Admin einschränkbar, für den ganzen Endpunkt.
- `fabric/iq/connectors/microsoft-365-copilot-overview`, Abschnitt „Sensitivity labels“.
- Microsoft Purview Service Description, Abschnitt „DLP for Microsoft Copilot“: Label-DLP auf
  Copilot erst ab Microsoft 365 E5 bzw. Purview-Suite.

## 4. Folgen

- C-26 im Compliance-Register, Status teilweise.
- Offen: ob jeder MCP-Aufruf im Fabric-Aktivitätsprotokoll erscheint (⚠️ UNKLAR); die
  Entscheidung je Kunde trifft dessen DSB.
