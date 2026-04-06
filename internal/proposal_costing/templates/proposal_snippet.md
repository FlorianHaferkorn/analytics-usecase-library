# Cost summary – {{ scenario_id }}

**Pricing:** {{ pricing_mode }}

| Item | USD/month | USD/year |
|------|-----------|----------|
| Fabric capacity | {{ capacity_month }} | {{ capacity_year }} |
| Power BI licenses | {{ license_month }} | {{ license_year }} |
| OneLake Storage (estimate) | {{ storage_month }} | {{ storage_year }} |
| **Total** | **{{ total_month }}** | **{{ total_year }}** |

*Warum:* Diese Übersicht bildet die monatlichen und jährlichen Plattformkosten (Capacity + Lizenzen) ab; optional ergänzt um Storage. Implementierung und Wartung erscheinen in den Bausteinen und in der TCO.

## Kosten nach Bausteinen
{{ building_blocks_table }}

*Warum:* Die Aufteilung nach Bausteinen zeigt, wo die Kosten entstehen, und erleichtert die Abstimmung mit Fachbereichen sowie die Prüfung durch Einkauf/Controlling.

## Scope – Included
{{ scope_in }}

## Scope – Not included
{{ scope_out }}

*Warum:* Nur die unter „Included“ genannten Leistungen sind in dieser Kalkulation abgedeckt. Alles Weitere (z. B. Schulung, individuelle Anpassungen) ist separat zu kalkulieren.

## Daten-Rollen / FTE
{{ role_breakdown_table }}

*Warum:* Die FTE-Zuordnung zeigt, wer die Plattform aufbaut (Implementation) und wer sie dauerhaft betreut (Maintenance). Konkrete Personen/Ansprechpartner sollten spätestens beim Kick-off benannt werden, damit Verantwortung und Kapazität klar sind.

## Kundenbeiträge / Voraussetzungen
{{ customer_contributions }}

*Warum:* Damit Implementierung und Zeitplan halten, sind folgende Beiträge des Kunden erforderlich.

## Implementierung / Meilensteine
{{ implementation_milestones_table }}

*Warum:* Überblick über Phasen und Deliverables für Planung und Abnahme.

## Viewer / Licenses
{{ viewer_note }}

*Warum:* Die Lizenzierung der Viewer hängt von der gewählten Production-Capacity ab (F64+ = Free Viewer; darunter benötigen Viewer Pro). Das beeinflusst Gesamtkosten und Nutzerakzeptanz.

## Capacity breakdown
{{ capacity_breakdown }}

## License breakdown
{{ license_breakdown }}

*Warum:* Die Aufteilung nach Umgebungen (Dev/Test/Prod) bzw. Lizenzen ermöglicht die Nachvollziehbarkeit der Kalkulation und spätere Anpassungen (z. B. Skalierung Prod).

## Cost projection (horizons)
{{ projection_table }}

*Warum:* Die Projektion zeigt die erwartete Kostenentwicklung bei Skalierung (z. B. mehr Nutzer, größere Capacity). Sie dient der mittel- bis langfristigen Planung.

## TCO
- TCO (3 years): {{ tco_3y }} USD
- TCO (5 years): {{ tco_5y }} USD

*Warum:* TCO über 3 bzw. 5 Jahre unterstützt die Investitionsentscheidung und den Vergleich mit Alternativen; inkl. einmaliger Implementierung und laufender Wartung.

## Sensitivität
{{ sensitivity_note }}

*Warum:* Transparenz zu den Annahmen; bei Änderung der Treiber (Nutzer, Capacity, Region) das Ergebnis neu bewerten.

## Assumptions
- Contract term: {{ contract_term_months }} months
- Region: {{ region }}
- Price basis: {{ price_basis }}
- Prices as of {{ valid_from }}. Quote valid until {{ quote_valid_until }}.

*Warum:* Alle Angaben basieren auf diesen Annahmen. Änderungen (Region, Laufzeit, Preisstand) beeinflussen das Ergebnis; bei Abweichung bitte neu kalkulieren.
