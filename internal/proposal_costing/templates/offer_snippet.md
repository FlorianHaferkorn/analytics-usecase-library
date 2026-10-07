# Angebot

**Kunde:** {{ customer_name }}

**Datum:** {{ offer_date }}

**Paket / Referenz:** {{ package_name }} – Szenario {{ scenario_id }}

**Preisbasis:** {{ pricing_mode }}. Gültig bis {{ quote_valid_until }}.

---

## Leistungsübersicht

| Position | {{ currency }}/Monat | {{ currency }}/Jahr |
|----------|-----------|----------|
| Plattform (Capacity + Lizenzen) | {{ total_month }} | {{ total_year }} |
| Implementierung (einmalig) | — | {{ implementation_one_time }} |
| Wartung (jährlich) | — | {{ maintenance_year }} |

Details: {{ building_blocks_table }}

## TCO

- TCO (3 Jahre): {{ tco_3y }} {{ currency }}
- TCO (5 Jahre): {{ tco_5y }} {{ currency }}

## Implementierung / Meilensteine

{{ implementation_milestones_table }}

## Kundenbeiträge / Voraussetzungen

{{ customer_contributions }}

## Annahmen

- Laufzeit: {{ contract_term_months }} Monate
- Region: {{ region }}
- Preisbasis: {{ price_basis }}
- Preise stand: {{ valid_from }}. Angebot gültig bis {{ quote_valid_until }}.
