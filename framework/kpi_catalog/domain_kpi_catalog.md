---

## Growth
| kpi_id | name | domain | purpose | definition_short | unit | grain | agg | target | lineage |
|--------|------|--------|---------|------------------|------|-------|-----|--------|---------|
| sales.revenue.growth_pct | Revenue Growth % | Growth | Top-line momentum | (Net Sales - LY) / LY | % | month | avg | Positive vs LY | fact_sales[Net Sales Amount], fact_sales[Net Sales Amount LY] |
| sales.net_sales.amount | Net Sales Amount | Growth | Core revenue base | Sum of net sales after discounts | EUR | invoice_line / month | sum | Meet/beat Plan/LY | fact_sales[Net Sales Amount] |
| sales.net_sales.delta_pct.ly | Net Sales Delta % vs LY | Growth | Growth vs LY | (Net Sales - LY) / LY | % | month | avg | >= +3 to +5% | fact_sales[Net Sales Amount], fact_sales[Net Sales Amount LY] |
| sales.net_sales.delta_amount.ly | Net Sales Delta Amount vs LY | Growth | Absolute growth | Net Sales - LY Net Sales | EUR | month | sum | Positive | fact_sales[Net Sales Amount], fact_sales[Net Sales Amount LY] |
| sales.net_sales.channel_share.pct | Channel Revenue Share % | Growth | Channel mix | Channel revenue / total revenue | % | month | avg | Per channel target | fact_sales[Net Sales Amount], dim_org[Channel] |
| margin.gm.channel_contribution.amount | Channel Gross Margin Contribution | Growth | Profit by channel | Gross margin by channel | EUR | month | sum | Improve vs plan | fact_sales[Net Sales Amount], fact_sales[Cost of Goods Sold Amount], dim_org[Channel] |

---

## Profitability
| kpi_id | name | domain | purpose | definition_short | unit | grain | agg | target | lineage |
|--------|------|--------|---------|------------------|------|-------|-----|--------|---------|
| margin.gm.pct | Gross Margin % | Profitability | Margin quality | Gross Margin / Net Sales | % | month | avg | >= target | fact_sales[Net Sales Amount], fact_sales[Cost of Goods Sold Amount] |
| margin.gm.amount | Gross Margin Amount | Profitability | Margin pool | Net Sales - COGS | EUR | month | sum | Improve vs Plan/LY | fact_sales[Net Sales Amount], fact_sales[Cost of Goods Sold Amount] |
| margin.gm.delta_amount | Gross Margin Delta Amount | Profitability | Absolute change vs baseline | Gross Margin - baseline | EUR | month | sum | Positive | fact_sales[Net Sales Amount], fact_sales[Cost of Goods Sold Amount], baseline GM |
| margin.gm.delta_pct | Gross Margin Delta % | Profitability | Relative change vs baseline | (GM % - baseline GM %) / baseline | % | month | avg | >= 0 | Gross Margin %, baseline GM % |
| profit.ebitda_margin | EBITDA Margin | Profitability | Profitability after op costs | EBITDA / Net Sales | % | month | avg | >= target | fact_finance[EBITDA], fact_finance[Net Sales] |
| cost.cogs.amount | COGS Amount | Profitability | Cost base | Cost of goods sold | EUR | invoice_line / month | sum | Control vs plan | fact_sales[Cost of Goods Sold Amount] |
| sales.promo.incremental.amount | Incremental Sales Amount | Profitability | Promo uplift sizing | Sales with promo - baseline sales | EUR | promotion | sum | Positive with ROI target | fact_sales[Net Sales Amount], baseline |
| sales.promo.roi.pct | Promotion ROI % | Profitability | Promo profitability | Incremental GM / Promo Cost | % | promotion | avg | >= 120% | fact_sales[Incremental GM], fact_promo[Promo Cost] |
| margin.promo.gm.pct | Promo Gross Margin % | Profitability | Profit quality in promo | GM / Net Sales during promo | % | promotion | avg | >= category target | fact_sales[Net Sales Amount], fact_sales[Cost of Goods Sold Amount], promo flag |

---

## ESG
| kpi_id | name | domain | purpose | definition_short | unit | grain | agg | target | lineage |
|--------|------|--------|---------|------------------|------|-------|-----|--------|---------|
| esg.carbon_intensity.tco2e_per_revenue | Carbon Emission Intensity | ESG | Carbon efficiency | Total CO2 emissions / revenue | tCO2e per revenue | quarter | avg | Reduce vs baseline | fact_sustainability[CO2 Emissions], fact_sales[Net Sales Amount] |
| esg.aligned_revenue.pct | ESG-Aligned Revenue % | ESG | Sustainable revenue share | ESG-aligned revenue / total revenue | % | quarter | avg | Increase vs target | fact_sales[ESG Aligned Revenue], fact_sales[Net Sales Amount] |
| esg.energy.renewable_kwh | Renewable Energy kWh | ESG | Renewable consumption | Renewable energy consumed | kWh | month | sum | Increase vs target | fact_energy[Renewable kWh] |
| esg.energy.total_kwh | Total Energy kWh | ESG | Total consumption | Total energy consumed | kWh | month | sum | Monitor | fact_energy[Total kWh] |
| esg.co2.total.tco2e | Total CO2 Emissions | ESG | Carbon footprint | Total CO2 equivalent emissions | tCO2e | month | sum | Reduce vs baseline | fact_sustainability[CO2 Emissions] |
| esg.ltifr.rate | LTIFR | ESG | Safety performance | Lost time injuries / hours worked * 1e6 | rate | month | avg | Reduce vs target | fact_safety[LTIs], fact_safety[Hours Worked] |

---

## Governance
| kpi_id | name | domain | purpose | definition_short | unit | grain | agg | target | lineage |
|--------|------|--------|---------|------------------|------|-------|-----|--------|---------|
| gov.data_quality.pct | Data Quality % | Governance | Data trustworthiness | Valid records / total records | % | dataset / month | avg | >= 98% | fact_dq[Valid Records], fact_dq[Total Records] |
| gov.records.total.count | Records Total Count | Governance | Volume context | Total records processed | count | dataset / month | sum | Monitor | fact_dq[Total Records] |
| gov.valid_records.count | Valid Records Count | Governance | Data quality numerator | Count of valid records | count | dataset / month | sum | Maximize | fact_dq[Valid Records] |
| gov.compliance.incidents.count | Compliance Incidents Count | Governance | Compliance tracking | Number of compliance incidents | count | month | sum | Reduce vs target | fact_compliance[Incidents] |
| gov.compliance.breach.count | Compliance Breach Count | Governance | Breach tracking | Number of compliance breaches | count | month | sum | Zero tolerance | fact_compliance[Breaches] |
| gov.audit.findings.count | Audit Findings Count | Governance | Audit posture | Total audit findings | count | audit | sum | Reduce vs target | fact_audit[Findings] |
| gov.audit.findings.open.count | Open Audit Findings Count | Governance | Risk exposure | Open audit findings | count | audit | sum | Close to plan | fact_audit[Open Findings] |
| corp.project.roi.pct | Project ROI % | Governance | Benefits realization | Project ROI | % | project | avg | >= hurdle | fact_projects[Benefit], fact_projects[Cost] |
| corp.benefit.realization.pct | Benefit Realization % | Governance | Benefit tracking | Realized benefit / planned benefit | % | project | avg | >= target | fact_projects[Benefit], fact_projects[Planned Benefit] |
| corp.budget.adherence.pct | Budget Adherence % | Governance | Cost control | Actual vs budget | % | project | avg | >= target | fact_projects[Actual Cost], fact_projects[Budget] |
| corp.schedule.adherence.pct | Schedule Adherence % | Governance | Timeline control | On-time milestones / total milestones | % | project | avg | >= target | fact_projects[Milestone On Time], fact_projects[Milestone Total] |
| corp.payback.months | Payback Period (months) | Governance | Capital efficiency | Months to recover investment | months | project | avg | <= target | fact_projects[Cashflows] |
| sec.incident.count | Security Incidents Count | Governance | Security posture | Number of security incidents | count | month | sum | Reduce vs baseline | fact_security[Incidents] |
| sec.incident.critical.count | Critical Security Incidents Count | Governance | Critical events | Number of critical security incidents | count | month | sum | Zero tolerance | fact_security[Critical Incidents] |
| sec.incident.mttr.hours | Security MTTR (hours) | Governance | Recovery speed | Mean time to recover security incidents | hours | month | avg | Reduce vs target | fact_security[MTTR] |

---

## Risk
| kpi_id | name | domain | purpose | definition_short | unit | grain | agg | target | lineage |
|--------|------|--------|---------|------------------|------|-------|-----|--------|---------|
| fin.risk.pd.pct | Probability of Default (PD) % | Risk | Credit risk | Probability of default over horizon | % | exposure / month | avg | Within risk band | fact_credit_risk[PD] |
| fin.risk.lgd.pct | Loss Given Default (LGD) % | Risk | Credit risk | Loss severity on default | % | exposure / month | avg | Within risk band | fact_credit_risk[LGD] |
| fin.risk.ead.amount | Exposure at Default Amount | Risk | Credit risk | Exposure amount at default | EUR | exposure / month | sum | Monitor/limit | fact_credit_risk[EAD] |

---

## Innovation & People
| kpi_id | name | domain | purpose | definition_short | unit | grain | agg | target | lineage |
|--------|------|--------|---------|------------------|------|-------|-----|--------|---------|
| people.new_product_share | New Product Share % | Innovation & People | Innovation revenue mix | Revenue from new products / total revenue | % | month | avg | Increase vs target | fact_sales[New Product Revenue], fact_sales[Net Sales Amount] |
| people.innovation_rate.pct | Innovation Rate % | Innovation & People | Pace of innovation | New launches / total portfolio | % | month | avg | Increase vs target | dim_product[Launch Date], dim_product[Active] |
| people.digital_adoption.pct | Digital Adoption % | Innovation & People | Tool adoption | Digital tool users / total employees | % | month | avg | Increase vs target | fact_it[Digital Users], fact_hr[Headcount] |
| hr.absenteeism.pct | Absenteeism % | Innovation & People | Workforce availability | Absent hours / scheduled hours | % | month | avg | <= target | fact_hr[Absent Hours], fact_hr[Scheduled Hours] |
| hr.turnover.pct | Employee Turnover % | Innovation & People | People stability | Leavers / avg headcount | % | month | avg | <= target | fact_hr[Leavers], fact_hr[Headcount] |
| hr.gm_per_fte.amount | GM per FTE Amount | Innovation & People | Productivity | Gross margin / FTE | EUR | month | avg | Increase vs target | fact_sales[Net Sales Amount], fact_sales[Cost of Goods Sold Amount], fact_hr[FTE] |
| hr.personnel_cost_ratio.pct | Personnel Cost Ratio % | Innovation & People | Cost share | Personnel cost / revenue | % | month | avg | <= target | fact_hr[Personnel Cost], fact_finance[Revenue] |

---

## Service & Experience
| kpi_id | name | domain | purpose | definition_short | unit | grain | agg | target | lineage |
|--------|------|--------|---------|------------------|------|-------|-----|--------|---------|
| svc.sla.attainment.pct | SLA Attainment % | Service | SLA compliance | Cases meeting SLA / total cases | % | day_queue / month | avg | >= target | fact_cases[SLA Met Flag] |
| svc.fcr.pct | First Contact Resolution % | Service | One-touch resolution | First contact resolved cases / total cases | % | day_queue / month | avg | >= target | fact_cases[FCR Flag] |
| svc.aht.minutes | Average Handling Time (minutes) | Service | Efficiency per contact | Avg handling time per case | minutes | day_queue / month | avg | <= target | fact_cases[Handle Time] |
| svc.backlog.count | Backlog Count | Service | Work in queue | Open cases not resolved | count | day_queue / month | sum | Controlled backlog | fact_cases[Backlog Flag] |
| svc.nps.index | NPS Index | Service | Experience quality | %Promoters - %Detractors | index | month | avg | Improve vs target | fact_nps[NPS Score] |
| svc.escalation.pct | Escalation % | Service | Escalation rate | Escalated cases / total cases | % | day_queue / month | avg | <= target | fact_cases[Escalation Flag] |
| res.utilization.pct | Utilization % | Service | Productive use of time | Productive time / paid time | % | agent_day / queue_day | avg | 75-85% typical | fact_wfm[Work Time], fact_wfm[Paid Time] |
| res.occupancy.pct | Occupancy % | Service | Active vs idle | (Talk + Wrap) / (Talk + Wrap + Idle) | % | agent_day / queue_day | avg | Balanced vs SLA | fact_wfm[Talk], fact_wfm[Wrap], fact_wfm[Idle] |
| res.overtime.pct | Overtime % | Service | Overtime share | Overtime hours / total hours | % | agent_day / region_week | avg | <= target | fact_wfm[Overtime Hours], fact_wfm[Total Hours] |
| res.shrinkage.pct | Shrinkage % | Service | Non-productive share | Non-productive time / paid time | % | agent_day | avg | <= target | fact_wfm[Shrinkage], fact_wfm[Paid Time] |
