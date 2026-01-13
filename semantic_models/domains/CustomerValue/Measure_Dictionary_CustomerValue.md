# Measure Dictionary - CustomerValue

Schema: see `/semantic_models/domains/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: "Net Sales Amount"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "00_Base"
  category: "Base"
  expression:
    dax: "SUM(fact_sales[Net Sales Amount])"
    formatString: "EUR #,0.00"
  documentation:
    description: "Base measure summing net sales for all transactions."
    notes: "Excludes VAT/returns; currency conversion handled upstream."
  dependencies:
    columns:
      - "fact_sales[Net Sales Amount]"
  governance:
    owner: "CRM BI"
    status: "active"
    version: "v1.2"
    last_review: "12.12.2025"

- measure_name: "Customer Lifetime Value Amount"
  is_kpi_measure: true
  kpi_id_ref: "crm.clv.amount"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "04_Customer"
  category: "KPI"
  expression:
    dax: "SUM(fact_customer_value[CLV Amount])"
    formatString: "EUR #,0.00"
  documentation:
    description: "Discounted lifetime value per customer sourced from the CLV mart."
    notes: "CLV methodology (horizon, discount rate) defined upstream."
  dependencies:
    columns:
      - "fact_customer_value[CLV Amount]"
  governance:
    owner: "CRM BI"
    status: "active"
    version: "v1.2"
    last_review: "12.12.2025"

- measure_name: "Customer Lifetime Revenue Amount"
  is_kpi_measure: true
  kpi_id_ref: "crm.lifetime_revenue.amount"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "01_Revenue"
  category: "KPI"
  expression:
    dax: "CALCULATE( [Net Sales Amount], ALL(dim_date) )"
    formatString: "EUR #,0.00"
  documentation:
    description: "Total realised revenue per customer across lifecycle; resets date context to accumulate."
    notes: "Uses Net Sales Amount as base; lifecycle completeness handled upstream."
  dependencies:
    measures:
      - "Net Sales Amount"
    columns:
      - "dim_customer[CustomerKey]"
  governance:
    owner: "CRM BI"
    status: "active"
    version: "v1.2"
    last_review: "12.12.2025"

- measure_name: "Active Customers Count"
  is_kpi_measure: true
  kpi_id_ref: "crm.active_customers.count"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "01_Retention"
  category: "KPI"
  expression:
    dax: |
      CALCULATE (
          DISTINCTCOUNT ( dim_customer[CustomerKey] ),
          KEEPFILTERS ( fact_customer_events[Activity Flag] = TRUE() )
      )
    formatString: "#,0"
  documentation:
    description: "Active customers in the period based on activity flag."
    notes: "Forms the base for retention/churn metrics."
  dependencies:
    columns:
      - "dim_customer[CustomerKey]"
      - "fact_customer_events[Activity Flag]"
  governance:
    owner: "CRM BI"
    status: "active"
    version: "v1.2"
    last_review: "12.12.2025"

- measure_name: "Churned Customers Count"
  is_kpi_measure: true
  kpi_id_ref: "crm.churned_customers.count"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "01_Retention"
  category: "KPI"
  expression:
    dax: |
      CALCULATE (
          DISTINCTCOUNT ( dim_customer[CustomerKey] ),
          KEEPFILTERS ( fact_customer_events[Churn Flag] = TRUE() )
      )
    formatString: "#,0"
  documentation:
    description: "Customers flagged as churned in the selected period."
    notes: "Depends on churn flag in fact_customer_events."
  dependencies:
    columns:
      - "dim_customer[CustomerKey]"
      - "fact_customer_events[Churn Flag]"
  governance:
    owner: "CRM BI"
    status: "active"
    version: "v1.2"
    last_review: "12.12.2025"

- measure_name: "Customer Retention %"
  is_kpi_measure: true
  kpi_id_ref: "crm.retention.pct"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "01_Retention"
  category: "KPI"
  expression:
    dax: |
      VAR Opening = [Active Customers Count]
      VAR Churned = [Churned Customers Count]
      RETURN DIVIDE ( Opening - Churned, Opening )
    formatString: "0.0 %"
  documentation:
    description: "Retained customers as share of opening active base in the period."
    notes: "Relies on activity/churn flags in fact_customer_events."
  dependencies:
    measures:
      - "Active Customers Count"
      - "Churned Customers Count"
  governance:
    owner: "CRM BI"
    status: "active"
    version: "v1.2"
    last_review: "12.12.2025"

- measure_name: "Revenue at Risk Amount"
  is_kpi_measure: true
  kpi_id_ref: "crm.revenue_at_risk.amount"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "01_Retention"
  category: "KPI"
  expression:
    dax: |
      // Attrition Risk % expected as 0–100; auto-scales to 0–1 if needed
      VAR RiskPct =
          VAR raw = SELECTEDVALUE ( fact_customer_events[Attrition Risk %] )
          RETURN IF ( raw > 1, raw / 100, raw )
      RETURN
          SUMX (
              fact_customer_value,
              fact_customer_value[CLV Remaining Amount] * RiskPct
          )
    formatString: "EUR #,0.00"
  documentation:
    description: "Exposure sizing from churn-risk customers based on CLV remaining and attrition risk."
    notes: "Attrition Risk % delivered as 0–100 is auto-scaled to 0–1. CLV and Remaining follow finance-approved discount rate and CLV horizon (use finance WACC and agreed horizon)."
  dependencies:
    columns:
      - "fact_customer_value[CLV Remaining Amount]"
      - "fact_customer_events[Attrition Risk %]"
  governance:
    owner: "CRM BI"
    status: "planned"
    version: "v1.2"
    last_review: "12.12.2025"

- measure_name: "NPS Score"
  is_kpi_measure: true
  kpi_id_ref: "crm.nps.index"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "02_CX"
  category: "KPI"
  expression:
    dax: "AVERAGE ( fact_nps[NPS Score] )"
    formatString: "0"
  documentation:
    description: "Average NPS score across responses in the current context."
    notes: "Use survey weights upstream if required."
  dependencies:
    columns:
      - "fact_nps[NPS Score]"
  governance:
    owner: "CX BI"
    status: "active"
    version: "v1.2"
    last_review: "12.12.2025"

- measure_name: "Customer Complaints Count"
  is_kpi_measure: true
  kpi_id_ref: "crm.complaint.count"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "02_CX"
  category: "KPI"
  expression:
    dax: "COUNTROWS ( fact_experience )"
    formatString: "#,0"
  documentation:
    description: "Total complaint events in the selected context."
    notes: "Relies on fact_experience complaint records."
  dependencies:
    columns:
      - "fact_experience[Complaint ID]"
  governance:
    owner: "CX BI"
    status: "active"
    version: "v1.2"
    last_review: "12.12.2025"

- measure_name: "COGS Amount"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "02_Margin"
  category: "Supporting"
  expression:
    dax: "SUM ( fact_sales[Cost of Goods Sold Amount] )"
    formatString: "EUR #,0.00"
  documentation:
    description: "Cost of goods sold aggregated for the current filter context."
    notes: ""
  dependencies:
    columns:
      - "fact_sales[Cost of Goods Sold Amount]"
  governance:
    owner: "CRM BI"
    status: "active"
    version: "v1.2"
    last_review: "12.12.2025"

- measure_name: "Margin Amount"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "02_Margin"
  category: "Supporting"
  expression:
    dax: "[Net Sales Amount] - [COGS Amount]"
    formatString: "EUR #,0.00"
  documentation:
    description: "Margin amount calculated as Net Sales minus COGS."
    notes: ""
  dependencies:
    measures:
      - "Net Sales Amount"
      - "COGS Amount"
  governance:
    owner: "CRM BI"
    status: "active"
    version: "v1.2"
    last_review: "12.12.2025"

- measure_name: "Gross Margin %"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "02_Margin"
  category: "Supporting"
  expression:
    dax: "DIVIDE ( [Margin Amount], [Net Sales Amount] )"
    formatString: "0.0 %"
  documentation:
    description: "Gross margin percentage derived from margin and net sales."
    notes: "Supporting only; not a required KPI in CustomerValue scope."
  dependencies:
    measures:
      - "Margin Amount"
      - "Net Sales Amount"
  governance:
    owner: "CRM BI"
    status: "active"
    version: "v1.2"
    last_review: "12.12.2025"

- measure_name: "Active Customers Start Count"
  is_kpi_measure: true
  kpi_id_ref: "crm.active_customers_start.count"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "01_Retention"
  category: "KPI"
  expression:
    dax: "/* TODO: snapshot active customers at period start */"
    formatString: "#,0"
  documentation:
    description: "Active customer base at the start of the period."
    notes: "Uses period start snapshot or opening balance logic."
  dependencies:
    columns:
      - "dim_customer[CustomerKey]"
  governance:
    owner: "CRM BI"
    status: "planned"
    version: "v1.0"
    last_review: "TBD"

- measure_name: "Active Customers End Count"
  is_kpi_measure: true
  kpi_id_ref: "crm.active_customers_end.count"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "01_Retention"
  category: "KPI"
  expression:
    dax: "/* TODO: snapshot active customers at period end */"
    formatString: "#,0"
  documentation:
    description: "Active customer base at the end of the period."
    notes: "Uses period end snapshot or closing balance logic."
  dependencies:
    columns:
      - "dim_customer[CustomerKey]"
  governance:
    owner: "CRM BI"
    status: "planned"
    version: "v1.0"
    last_review: "TBD"

- measure_name: "Churn %"
  is_kpi_measure: true
  kpi_id_ref: "crm.churn.pct"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "01_Retention"
  category: "KPI"
  expression:
    dax: "DIVIDE ( [Churned Customers Count], [Active Customers Start Count] )"
    formatString: "0.0 %"
  documentation:
    description: "Churned customers as share of starting active base."
    notes: "Aligns with retention definition; uses opening base."
  dependencies:
    measures:
      - "Churned Customers Count"
      - "Active Customers Start Count"
  governance:
    owner: "CRM BI"
    status: "planned"
    version: "v1.0"
    last_review: "TBD"

- measure_name: "Reactivated Customers Count"
  is_kpi_measure: true
  kpi_id_ref: "crm.reactivated_customers.count"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "01_Retention"
  category: "KPI"
  expression:
    dax: "/* TODO: count customers reactivated in period */"
    formatString: "#,0"
  documentation:
    description: "Customers returning after churn/inactivity."
    notes: "Requires reactivation flag in events."
  dependencies:
    columns:
      - "fact_customer_events[Reactivation Flag]"
  governance:
    owner: "CRM BI"
    status: "planned"
    version: "v1.0"
    last_review: "TBD"

- measure_name: "Reactivation %"
  is_kpi_measure: true
  kpi_id_ref: "crm.reactivation.pct"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "01_Retention"
  category: "KPI"
  expression:
    dax: "DIVIDE ( [Reactivated Customers Count], [Churned Customers Count] )"
    formatString: "0.0 %"
  documentation:
    description: "Share of churned customers that are reactivated."
    notes: "Defines reactivation window (e.g., 6-12 months)."
  dependencies:
    measures:
      - "Reactivated Customers Count"
      - "Churned Customers Count"
  governance:
    owner: "CRM BI"
    status: "planned"
    version: "v1.0"
    last_review: "TBD"

- measure_name: "At-Risk Customers Count"
  is_kpi_measure: true
  kpi_id_ref: "crm.at_risk_customers.count"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "01_Retention"
  category: "KPI"
  expression:
    dax: "/* TODO: count customers above attrition risk threshold */"
    formatString: "#,0"
  documentation:
    description: "Customers flagged as at-risk based on attrition model."
    notes: "Threshold defined by CRM governance."
  dependencies:
    columns:
      - "fact_customer_events[Attrition Risk %]"
  governance:
    owner: "CRM BI"
    status: "planned"
    version: "v1.0"
    last_review: "TBD"

- measure_name: "At-Risk Share %"
  is_kpi_measure: true
  kpi_id_ref: "crm.at_risk_share.pct"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "01_Retention"
  category: "KPI"
  expression:
    dax: "DIVIDE ( [At-Risk Customers Count], [Active Customers Count] )"
    formatString: "0.0 %"
  documentation:
    description: "At-risk customers as a share of active base."
    notes: "Uses active base in current context."
  dependencies:
    measures:
      - "At-Risk Customers Count"
      - "Active Customers Count"
  governance:
    owner: "CRM BI"
    status: "planned"
    version: "v1.0"
    last_review: "TBD"

- measure_name: "Basket Size Amount"
  is_kpi_measure: true
  kpi_id_ref: "crm.basket_size.amount"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "03_Commercial"
  category: "KPI"
  expression:
    dax: "/* TODO: average order value per transaction */"
    formatString: "EUR #,0.00"
  documentation:
    description: "Average basket value per transaction."
    notes: "Order/transaction grain required."
  dependencies:
    columns:
      - "fact_sales[Net Sales Amount]"
  governance:
    owner: "CRM BI"
    status: "planned"
    version: "v1.0"
    last_review: "TBD"

- measure_name: "Basket Size Units"
  is_kpi_measure: true
  kpi_id_ref: "crm.basket_size.units"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "03_Commercial"
  category: "KPI"
  expression:
    dax: "/* TODO: average units per transaction */"
    formatString: "#,0.0"
  documentation:
    description: "Average basket size in units."
    notes: "Order/transaction grain required."
  dependencies:
    columns:
      - "fact_sales[Quantity]"
  governance:
    owner: "CRM BI"
    status: "planned"
    version: "v1.0"
    last_review: "TBD"

- measure_name: "Cross-Sell Ratio %"
  is_kpi_measure: true
  kpi_id_ref: "crm.cross_sell_ratio.pct"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "03_Commercial"
  category: "KPI"
  expression:
    dax: "/* TODO: share of customers buying >1 category */"
    formatString: "0.0 %"
  documentation:
    description: "Share of customers with cross-category purchases."
    notes: "Requires category mapping at transaction level."
  dependencies:
    columns:
      - "fact_sales[ProductKey]"
  governance:
    owner: "CRM BI"
    status: "planned"
    version: "v1.0"
    last_review: "TBD"

- measure_name: "Customer Revenue Share %"
  is_kpi_measure: true
  kpi_id_ref: "sales.customer.revenue_share.pct"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "03_Commercial"
  category: "KPI"
  expression:
    dax: |
      VAR CustRev = SUM ( fact_sales[Net Sales Amount] )
      VAR TotalRev = CALCULATE ( SUM ( fact_sales[Net Sales Amount] ), ALL ( dim_customer ) )
      RETURN DIVIDE ( CustRev, TotalRev )
    formatString: "0.0 %"
  documentation:
    description: "Revenue contribution of a customer or segment."
    notes: "Use with customer/segment filters."
  dependencies:
    columns:
      - "fact_sales[Net Sales Amount]"
      - "dim_customer[CustomerKey]"
  governance:
    owner: "CRM BI"
    status: "planned"
    version: "v1.0"
    last_review: "TBD"

- measure_name: "Opportunities Open Amount"
  is_kpi_measure: true
  kpi_id_ref: "crm.opportunities.open.amount"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "05_Pipeline"
  category: "KPI"
  expression:
    dax: "/* TODO: sum open opportunity amount */"
    formatString: "EUR #,0.00"
  documentation:
    description: "Open opportunity pipeline value."
    notes: "Open stage logic defined by CRM."
  dependencies:
    columns:
      - "fact_crm_opportunity[Amount]"
      - "fact_crm_opportunity[Stage]"
  governance:
    owner: "CRM BI"
    status: "planned"
    version: "v1.0"
    last_review: "TBD"

- measure_name: "Opportunities Won Amount"
  is_kpi_measure: true
  kpi_id_ref: "crm.opportunities.won.amount"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "05_Pipeline"
  category: "KPI"
  expression:
    dax: "/* TODO: sum won opportunity amount */"
    formatString: "EUR #,0.00"
  documentation:
    description: "Closed-won opportunity value."
    notes: "Won stage logic defined by CRM."
  dependencies:
    columns:
      - "fact_crm_opportunity[Amount]"
      - "fact_crm_opportunity[Stage]"
  governance:
    owner: "CRM BI"
    status: "planned"
    version: "v1.0"
    last_review: "TBD"

- measure_name: "Opportunity Win Rate %"
  is_kpi_measure: true
  kpi_id_ref: "crm.opportunities.win_rate.pct"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "05_Pipeline"
  category: "KPI"
  expression:
    dax: "/* TODO: won opportunities / total opportunities */"
    formatString: "0.0 %"
  documentation:
    description: "Share of opportunities that are won."
    notes: "Use consistent stage mapping."
  dependencies:
    columns:
      - "fact_crm_opportunity[Stage]"
  governance:
    owner: "CRM BI"
    status: "planned"
    version: "v1.0"
    last_review: "TBD"

- measure_name: "Opportunity Stage Conversion %"
  is_kpi_measure: true
  kpi_id_ref: "crm.opportunities.stage_conversion.pct"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "05_Pipeline"
  category: "KPI"
  expression:
    dax: "/* TODO: stage-to-stage conversion rate */"
    formatString: "0.0 %"
  documentation:
    description: "Conversion rate between pipeline stages."
    notes: "Define stage path and conversion logic."
  dependencies:
    columns:
      - "fact_crm_opportunity[Stage]"
  governance:
    owner: "CRM BI"
    status: "planned"
    version: "v1.0"
    last_review: "TBD"

- measure_name: "Acquisition Leads Count"
  is_kpi_measure: true
  kpi_id_ref: "crm.acquisition.leads.count"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "06_Acquisition"
  category: "KPI"
  expression:
    dax: "SUM ( fact_crm_leads[Leads] )"
    formatString: "#,0"
  documentation:
    description: "Total leads acquired in period."
    notes: "Lead definition aligned with CRM."
  dependencies:
    columns:
      - "fact_crm_leads[Leads]"
  governance:
    owner: "CRM BI"
    status: "planned"
    version: "v1.0"
    last_review: "TBD"

- measure_name: "Acquisition Conversions Count"
  is_kpi_measure: true
  kpi_id_ref: "crm.acquisition.conversions.count"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "06_Acquisition"
  category: "KPI"
  expression:
    dax: "SUM ( fact_crm_leads[Conversions] )"
    formatString: "#,0"
  documentation:
    description: "Converted leads in period."
    notes: "Conversion logic aligned with CRM."
  dependencies:
    columns:
      - "fact_crm_leads[Conversions]"
  governance:
    owner: "CRM BI"
    status: "planned"
    version: "v1.0"
    last_review: "TBD"

- measure_name: "Acquisition Conversion Rate %"
  is_kpi_measure: true
  kpi_id_ref: "crm.acquisition.conversion_rate.pct"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "06_Acquisition"
  category: "KPI"
  expression:
    dax: "DIVIDE ( [Acquisition Conversions Count], [Acquisition Leads Count] )"
    formatString: "0.0 %"
  documentation:
    description: "Conversions divided by leads."
    notes: "Guard for zero leads."
  dependencies:
    measures:
      - "Acquisition Conversions Count"
      - "Acquisition Leads Count"
  governance:
    owner: "CRM BI"
    status: "planned"
    version: "v1.0"
    last_review: "TBD"

- measure_name: "Acquisition CAC Amount"
  is_kpi_measure: true
  kpi_id_ref: "crm.acquisition.cac.amount"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "06_Acquisition"
  category: "KPI"
  expression:
    dax: "/* TODO: acquisition spend / conversions */"
    formatString: "EUR #,0.00"
  documentation:
    description: "Customer acquisition cost per converted lead."
    notes: "Requires acquisition spend allocation."
  dependencies:
    measures:
      - "Acquisition Conversions Count"
  governance:
    owner: "CRM BI"
    status: "planned"
    version: "v1.0"
    last_review: "TBD"

- measure_name: "Complaint Rate %"
  is_kpi_measure: true
  kpi_id_ref: "crm.complaint.rate.pct"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "02_CX"
  category: "KPI"
  expression:
    dax: "/* TODO: complaints / total interactions */"
    formatString: "0.0 %"
  documentation:
    description: "Complaint incidence rate."
    notes: "Requires interaction base definition."
  dependencies:
    columns:
      - "fact_experience[Complaint ID]"
  governance:
    owner: "CX BI"
    status: "planned"
    version: "v1.0"
    last_review: "TBD"

- measure_name: "Market Share %"
  is_kpi_measure: true
  kpi_id_ref: "market.share.total.pct"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "07_Market"
  category: "KPI"
  expression:
    dax: "/* TODO: company revenue / total market revenue */"
    formatString: "0.0 %"
  documentation:
    description: "Total market share for the selected market."
    notes: "Market sizing source documented."
  dependencies:
    columns:
      - "fact_market[Market Revenue]"
  governance:
    owner: "Market Intelligence"
    status: "planned"
    version: "v1.0"
    last_review: "TBD"

- measure_name: "Relative Market Share %"
  is_kpi_measure: true
  kpi_id_ref: "market.share.relative.pct"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "07_Market"
  category: "KPI"
  expression:
    dax: "/* TODO: company share vs top competitor share */"
    formatString: "0.0 %"
  documentation:
    description: "Relative share versus primary competitor."
    notes: "Competitor selection rules documented."
  dependencies:
    columns:
      - "fact_market[Market Revenue]"
  governance:
    owner: "Market Intelligence"
    status: "planned"
    version: "v1.0"
    last_review: "TBD"

- measure_name: "Brand Awareness %"
  is_kpi_measure: true
  kpi_id_ref: "mkt.brand.awareness.pct"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "07_Market"
  category: "KPI"
  expression:
    dax: "/* TODO: survey awareness % */"
    formatString: "0.0 %"
  documentation:
    description: "Brand awareness rate from surveys."
    notes: "Survey methodology documented."
  dependencies:
    columns:
      - "fact_brand_survey[Awareness %]"
  governance:
    owner: "Market Intelligence"
    status: "planned"
    version: "v1.0"
    last_review: "TBD"

- measure_name: "Brand Preference %"
  is_kpi_measure: true
  kpi_id_ref: "mkt.brand.preference.pct"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "07_Market"
  category: "KPI"
  expression:
    dax: "/* TODO: survey preference % */"
    formatString: "0.0 %"
  documentation:
    description: "Brand preference rate from surveys."
    notes: "Survey methodology documented."
  dependencies:
    columns:
      - "fact_brand_survey[Preference %]"
  governance:
    owner: "Market Intelligence"
    status: "planned"
    version: "v1.0"
    last_review: "TBD"
```
