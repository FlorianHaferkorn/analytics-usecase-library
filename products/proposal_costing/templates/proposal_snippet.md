# Cost summary – {{ scenario_id }}

**Pricing:** {{ pricing_mode }}

| Item | USD/month | USD/year |
|------|-----------|----------|
| Fabric capacity | {{ capacity_month }} | {{ capacity_year }} |
| Power BI licenses | {{ license_month }} | {{ license_year }} |
| OneLake Storage (estimate) | {{ storage_month }} | {{ storage_year }} |
| **Total** | **{{ total_month }}** | **{{ total_year }}** |

## Kosten nach Bausteinen
{{ building_blocks_table }}

## Scope – Included
{{ scope_in }}

## Scope – Not included
{{ scope_out }}

## Daten-Rollen / FTE
{{ role_breakdown_table }}

## Viewer / Licenses
{{ viewer_note }}

## Capacity breakdown
{{ capacity_breakdown }}

## License breakdown
{{ license_breakdown }}

## Cost projection (horizons)
{{ projection_table }}

## TCO
- TCO (3 years): {{ tco_3y }} USD
- TCO (5 years): {{ tco_5y }} USD

## Assumptions
- Contract term: {{ contract_term_months }} months
- Region: {{ region }}
- Price basis: {{ price_basis }}
- Prices as of {{ valid_from }}. Quote valid until {{ quote_valid_until }}.
