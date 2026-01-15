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


- measure_name: "Complaint Rate %"
  is_kpi_measure: true
  kpi_id_ref: "crm.complaint.rate.pct"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "02_CX"
  category: "KPI"
  expression:
    dax: |
      VAR Complaints = DISTINCTCOUNT ( fact_experience[Complaint ID] )
      VAR Interactions = DISTINCTCOUNT ( fact_experience[Interaction ID] )
      RETURN DIVIDE ( Complaints, Interactions )
    formatString: "0.0 %"
  documentation:
    description: "Complaint incidence rate."
    notes: "Requires interaction base definition."
  dependencies:
    columns:
      - "fact_experience[Complaint ID]"
      - "fact_experience[Interaction ID]"
  governance:
    owner: "CX BI"
    status: "planned"
    version: "v1.0"
    last_review: "TBD"
```

