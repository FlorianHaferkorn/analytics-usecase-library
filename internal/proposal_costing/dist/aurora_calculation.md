# Aurora – Beispielkalkulation

# Cost summary – compact

**Pricing:** Pay-as-you-go

| Item | USD/month | USD/year |
|------|-----------|----------|
| Fabric capacity | 1839.60 | 22075.20 |
| Power BI licenses | 42.00 | 504.00 |
| OneLake Storage (estimate) | — | — |
| **Total** | **1881.60** | **22579.20** |

*Warum:* Diese Übersicht bildet die monatlichen und jährlichen Plattformkosten (Capacity + Lizenzen) ab; optional ergänzt um Storage. Implementierung und Wartung erscheinen in den Bausteinen und in der TCO.

## Kosten nach Bausteinen
| Baustein | Kategorie | USD/month | USD/year |
|----------|-----------|-----------|----------|
| Fabric Capacity | Operating | 1839.60 | 22075.20 |
| Power BI (Pro / PPU) | Operating | 42.00 | 504.00 |
| OneLake Storage | Operating | 0.00 | 0.00 |
| Implementation (one-time) | Acquisition | 0.00 | 0.00 |
| Maintenance (per year) | Operating | 3000.00 | 36000.00 |

*Warum:* Die Aufteilung nach Bausteinen zeigt, wo die Kosten entstehen, und erleichtert die Abstimmung mit Fachbereichen sowie die Prüfung durch Einkauf/Controlling.

## Scope – Included
- Fabric Capacity (Pay-as-you-go or reservation)
- Power BI Pro / PPU licenses as specified

## Scope – Not included
- Implementation / Professional Services
- Training
- OneLake Storage (unless estimated via --storage-gb)
- Network egress
- Local taxes and currency conversion

*Warum:* Nur die unter „Included“ genannten Leistungen sind in dieser Kalkulation abgedeckt. Alles Weitere (z. B. Schulung, individuelle Anpassungen) ist separat zu kalkulieren.

## Daten-Rollen / FTE
| Role | Domain | FTE | Phase | Person / Ansprechpartner |
|------|--------|-----|-------|---------------------------|
| Sales BI Lead | Commercial | 0.5 | implementation | — |
| Finance BI Lead | Finance | 0.3 | implementation | — |
| Sales BI Lead | Commercial | 0.2 | maintenance | — |
| Finance BI Lead | Finance | 0.1 | maintenance | — |

*Warum:* Die FTE-Zuordnung zeigt, wer die Plattform aufbaut (Implementation) und wer sie dauerhaft betreut (Maintenance). Konkrete Personen/Ansprechpartner sollten spätestens beim Kick-off benannt werden, damit Verantwortung und Kapazität klar sind.

## Kundenbeiträge / Voraussetzungen
- Benennung fachlicher und technischer Ansprechpartner
- Bereitstellung von Testdaten bzw. Zugang zu Quellsystemen
- Freigabe von Meilensteinen und Teilnahme an Review-Terminen
- Kick-off und regelmäßige Abstimmungstermine

*Warum:* Damit Implementierung und Zeitplan halten, sind folgende Beiträge des Kunden erforderlich.

## Implementierung / Meilensteine
| Phase | Deliverable | Dauer |
|-------|-------------|-------|
| Kick-off & Anforderung | Anforderungsdokument, Abnahme Kriterien | Woche 1–2 |
| Aufbau & Konfiguration | Umgebungen, erste Reports | Woche 3–8 |
| Test & Go-Live | UAT, Schulung, Go-Live | Woche 9–12 |

*Warum:* Überblick über Phasen und Deliverables für Planung und Abnahme.

## Viewer / Licenses
With production capacity below F64, report viewers require Power BI Pro.

*Warum:* Die Lizenzierung der Viewer hängt von der gewählten Production-Capacity ab (F64+ = Free Viewer; darunter benötigen Viewer Pro). Das beeinflusst Gesamtkosten und Nutzerakzeptanz.

## Capacity-Overage
- SKU F8: 192 CU hours per day
- Rolling 24-hour threshold: 48 CU hours (Microsoft default at capacity creation (25 %), not yet confirmed by the customer); Microsoft recommends staying below 64 (one third of the daily CU hours)
- Maximum overage cost per day ≈ threshold × 3 × PAYG price per CU hour ≈ 25.92 USD (derived, not measured; can be exceeded because the threshold is checked every 5 minutes and running operations continue)
- Additional Fabric quota required: 2 CU

*Warum:* Microsoft schaltet Overage bei neuen F-Kapazitäten standardmäßig ein und rechnet Last über der Kapazität zum dreifachen Pay-as-you-go-Satz ab. Die Tagesobergrenze ist hergeleitet und keine harte Grenze.

## Fabric Planning
—

*Warum:* Planning-Sessions verbrauchen CU der Produktionskapazität. Der Anteil steckt bereits im Kapazitätspreis und muss neben den übrigen Workloads Platz haben.

## Offene Kundenfragen
- Capacity overage: switch it off, or set a rolling 24-hour threshold of X CU hours? It is on by default for new F capacities (threshold 25 % = 48 CU hours/day on F8) and is billed at 3x the pay-as-you-go rate.

## Capacity breakdown
dev: F2 262.80 USD/mo | test: F4 525.60 USD/mo | prod: F8 1051.20 USD/mo

## License breakdown
PRO: 3 users, 42.00 USD/mo

*Warum:* Die Aufteilung nach Umgebungen (Dev/Test/Prod) bzw. Lizenzen ermöglicht die Nachvollziehbarkeit der Kalkulation und spätere Anpassungen (z. B. Skalierung Prod).

## Cost projection (horizons)
| Horizon | Years | USD/year (platform) | USD/year (maintenance) |
|---------|-------|---------------------|------------------------|
| Year 1 (short-term) | 1 | 22579.20 | 36000.00 |
| Year 2–3 (medium-term) | 2 | 35529.60 | 36000.00 |
| Year 4–5 (long-term) | 2 | 61262.40 | 36000.00 |

*Warum:* Die Projektion zeigt die erwartete Kostenentwicklung bei Skalierung (z. B. mehr Nutzer, größere Capacity). Sie dient der mittel- bis langfristigen Planung.

## TCO
- TCO (3 years): 201638.40 USD
- TCO (5 years): 396163.20 USD

*Warum:* TCO über 3 bzw. 5 Jahre unterstützt die Investitionsentscheidung und den Vergleich mit Alternativen; inkl. einmaliger Implementierung und laufender Wartung.

## Sensitivität
Änderungen bei Nutzerzahl, Capacity oder Region beeinflussen die TCO; bei Abweichung bitte neu kalkulieren.

*Warum:* Transparenz zu den Annahmen; bei Änderung der Treiber (Nutzer, Capacity, Region) das Ergebnis neu bewerten.

## Assumptions
- Contract term: 12 months
- Region: West Europe
- Price basis: Microsoft list price (USD)
- Prices as of 2025-02-01. Quote valid until 2025-03-03.

*Warum:* Alle Angaben basieren auf diesen Annahmen. Änderungen (Region, Laufzeit, Preisstand) beeinflussen das Ergebnis; bei Abweichung bitte neu kalkulieren.
