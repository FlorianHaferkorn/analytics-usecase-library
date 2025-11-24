# ESG-002 Energy Efficiency Optimization - Business Factsheet

## 1. Summary
- **Business Goal:** Reduce energy cost, intensity, and emissions by identifying inefficient sites, prioritizing retrofits, and scaling renewable sourcing.
- **Target Audience:** Operations leaders, Sustainability, Facility management, Finance.
- **Business Priority:** High; energy cost volatility and ESG targets require continuous optimization.
- **Expected Impact:** -8 % energy cost and -5 % carbon intensity through efficiency and fuel-switch measures.

## 2. Core Questions
- Which sites or assets consume the most energy relative to production output, and how does this trend over time?
- What share of energy comes from renewable sources versus fossil fuels, and which interventions improve the mix?
- Where do energy costs spike, and how do tariffs, utilization, or maintenance backlog contribute?
- Which action codes (retrofit, automation, sourcing) deliver the best ROI and emissions impact?

## 3. KPI Set (Business View)
| KPI Name | Purpose | Business Definition | Interpretation | Decision Relevance |
|----------|---------|---------------------|----------------|--------------------|
| Total Energy (kWh) | Measures absolute consumption. | Aggregated metered energy per site/month across sources. | High values require contextualization vs output. | Guides energy budgeting and intensity tracking. |
| Renewable Energy (kWh) | Tracks clean energy adoption. | Energy classified as renewable (onsite/offsite). | Higher share reduces emissions exposure. | Supports PPAs, onsite generation planning. |
| Renewable Share % | Highlights energy mix quality. | Renewable kWh / Total kWh. | Target >50 % for priority regions; <30 % triggers action. | Drives sourcing strategy. |
| Energy Cost Amount | Quantifies spend exposure. | Total energy cost per site/month. | Spikes indicate tariff changes or inefficiency. | Input for procurement and hedging. |
| Carbon Intensity (tCO2e/unit) | Links energy to emissions. | Emissions from energy divided by production or revenue (business description). | Ensures energy program aligns with ESG targets. | Prioritizes projects on abatement cost curve. |

## 4. Business Logic & Thresholds
- Renewable Share % threshold: <30 % = red, 30-50 % = amber, >50 % = green (customizable per region).
- Energy intensity benchmarks stored per site type; >10 % variance for two periods triggers action code M1.
- Carbon intensity uses same emission factors as ESG-001 to maintain consistency.
- Energy cost measured net of taxes/rebates; FX translation at period average.

## 5. Action Codes (Business Perspective)
| Code | Name | Business Description | Typical Trigger | Expected Effect |
|------|------|-----------------------|-----------------|------------------|
| S1 | Sustainability Investment Wave | Fund capex for efficiency upgrades, onsite renewables, or PPAs. | Renewable Share % gap >15 pp vs roadmap. | +10 pp renewable share, -5 % intensity. |
| M1 | Maintenance and Optimization | Address equipment inefficiencies, recalibrate systems, optimize schedules. | Energy intensity > benchmark or cost spikes. | -8 % energy cost, stabilizes operations. |

## 6. 3-30-300 Page Layout
### 6.1 3-Second Layer (Insight)
- KPI cards for Total Energy, Renewable Share %, Energy Cost Amount, Carbon Intensity with plan/target deltas.
- Alert banner for sites exceeding thresholds.

### 6.2 30-Second Layer (Story)
- Trend lines (12-24 months) for energy consumption, cost, and renewable share.
- Waterfall showing cost variance drivers (volume, rate, mix).
- Heatmap Region > Site with renewable share and cost per unit.

### 6.3 300-Second Layer (Detail)
- Drillable table Site > Asset Type with KPIs, action codes, payback status.
- Project pipeline view linking initiatives to expected savings and carbon impact.
- Export-ready dataset for facility teams and procurement.

## 7. Dependencies & Constraints
- Requires reliable metering data (hourly/daily aggregated to monthly) with clear mapping to sites and energy sources.
- Renewable classification aligned with sustainability definitions; PPAs and certificates tracked separately.
- Production or revenue baseline required to contextualize energy intensity; ensure same org/time keys as finance.
- Tariff tables maintained for accurate cost calculations; contract changes captured with effective dates.

## 8. Success Criteria
- Leading: 90 % of sites submit energy data within 3 business days; action code updates logged monthly.
- Lagging: -8 % energy cost and +10 pp renewable share for targeted portfolio within 12 months.
