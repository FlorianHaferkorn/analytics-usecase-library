# R1 Strang "di" — Decision-Intelligence-Fähigkeiten für ein Fabric-Steuerungscockpit (30.09.2026)

Daten: `capability_di.yaml`, 37 Einträge (22 `fetched` über Microsoft Learn, 15 `search_index`; 21 `from_source`,
16 `inferred`). `user_value`/`must_have_for_di` sind durchgehend eigene Einschätzung.
## Kernaussage
DI unterscheidet sich von BI durch die Entscheidungsschleife: Befund, Entscheidung, Maßnahme, Wirkung, Lernen
(Gartner-Definition di-001, Pratt di-004). Fabric liefert fast alle technischen Bausteine (Write-back, Regeln mit
Aktionen, Agenten mit Freigabe, Planung), aber kein Objekt "Entscheidung" und keine Wirkungsmessung. Diese Schicht
muss das Cockpit bauen.

## Rangliste nach Nutzen (Top 12, eigene Wertung)
| Rang | id | Fähigkeit | Fabric/PBI |
|---|---|---|---|
| 1 | di-006 | Entscheidungslog (wer, was, warum, erwartete Wirkung) | absent, baubar mit di-035 |
| 2 | di-008 | Wirkungsmessung der Maßnahme (Closed Loop) | absent |
| 3 | di-035 | Maßnahme direkt aus dem Bericht erfassen (translytical task flow) | fabric_feature (GA 03/2026) |
| 4 | di-022 | Zustandsbehaftete Regel mit Aktion (Activator) | fabric_feature (Report-Alerts Preview) |
| 5 | di-016 | Automatische Ursachen-/Treiberanalyse | native |
| 6 | di-028 | Werttreiberbaum mit Simulation | absent |
| 7 | di-033 | Treiberbasierte Planung mit Write-back | fabric_feature (Fabric Planning) |
| 8 | di-031 | Szenarien versionieren und vergleichen | fabric_feature |
| 9 | di-011 | Freigabe durch den Menschen (Human in the Loop) | fabric_feature (Operations Agent) |
| 10 | di-026 | Prognose mit Konfidenzintervall | native, nur visuell |
| 11 | di-023 | Schutz vor Alert-Fatigue | fabric_feature; Dashboard-Alerts ohne |
| 12 | di-013 | Erklärbare Empfehlung mit Konfidenz | absent |

## Native vs. Fabric-Feature vs. Eigenbau
- native (10): Treiberanalyse, Zerlegung, Key Influencers, Anomalie-/Forecast-Band, Error Bars, What-if, Schwellwert-Alarm
  (nur Dashboard-Kacheln), Scorecards mit Check-in-Historie, Kommentare mit Filterkontext; mehrere nur mit Pro/F64+.
- fabric_feature (14): Activator, Operations Agent, Data Agent, Ontologie/Graph (Preview), Fabric Planning (Szenarien,
  Zielsuche, Freigabe, Write-back mit Änderungshistorie), translytical task flows.
- premium (2): Copilot-Zusammenfassung und Digest (bezahlte Capacity, keine Trial-SKU).
- absent = Eigenbau (11): Entscheidung als Objekt, Log/Journal, Wirkungsmessung, kontrafaktische Schätzung,
  KPI-zu-Aktion-Kopplung, kausales Entscheidungsdiagramm, DMN, Werttreiberbaum-Darstellung, Konfidenz je Empfehlung.

## Lücken
- Kein Werttreiberbaum-Visual/-Item in Power BI oder Fabric gefunden (gesucht; Custom Visuals nicht geprüft).
- Forecast und Anomalien sind nur visuell (Liniendiagramm), nicht als Measure: nicht alarmierbar, nicht in
  IBCS-Varianztabellen nutzbar. Belastbare Prognosen gehören ins Notebook/Planning und als Daten ins Modell.
- Keine Quelle dokumentiert Wirkungsmessung pro Maßnahme mit Kontrollgruppe; Aera und Operations Agent nennen
  "Lernen aus Ergebnissen" ohne Methodik.
- Activator: Zustandswechsel + Occurrence, aber keine Priorisierung/Bündelung über Regeln.

## Widersprüche
- Activator-Report-Alerts: Power-BI-Doku verlangt F64+/Premium und nennt Preview; Activator-Doku nur "Fabric capacity".
- Translytical task flows: Update März 2026 meldet GA, die Cosmos-DB-Anleitung "public preview" (wohl nur diese Variante).
- Microsoft nennt Fabric Planning "enterprise decision intelligence"; im Gartner-MQ DIP 2026 ist Microsoft laut
  Suchauszug nicht unter den 17 Anbietern. Selbstetikett ist keine Analystenkategorie.
- "Warum": Anomalie-Erklärung/Key Influencers liefern korrelative Kandidaten; der Data Agent schließt kausale Analyse aus.

## Offene Fragen
1. Welche Capacity hat der Zielkunde? Entscheidet über Activator-Report-Alerts, Scorecards/Kommentare für Free-User, Copilot.
2. Sind Fabric Planning und Operations Agent (Preview-Anteile, eigene Meter) freigegeben, oder bleibt es bei
   translytical task flows + SQL DB?
3. Dockt das Entscheidungslog an `core/action_codes/` an (Golden-Thread-konforme KPI-zu-Aktion-Kopplung, di-005)?
4. Alert-Fatigue-Zahlen nur aus Suchauszügen (Klinik) — Primärstudie lesen, bevor sie in ein Kundendokument gehen.

## Bewusst nicht gemacht
- Gartner-Volltext, Tableau-, ThoughtSpot-, SAP-, Aera-, OMG-, arXiv-, PMC-Seiten: Egress-gesperrt, nur Suchauszüge.
- Keine AppSource-Recherche zu Treiberbaum/Write-back-Visuals und keine Anbieterpreise: nicht beauftragt.
