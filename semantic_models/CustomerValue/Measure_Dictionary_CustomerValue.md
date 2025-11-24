# Measure Dictionary - CustomerValue

Schema: see `/_includes/kpi_catalog/Domain_Measure_Dictionary_Schema.md`

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
    description: "Base measure summing net sales for all transactions in fact_sales."
    notes: "Excludes VAT and returns; currency conversion handled upstream."
  dependencies:
    columns:
      - "fact_sales[Net Sales Amount]"
  governance:
    owner: "CRM BI"
    status: "active"
    version: "v1.1"
    last_review: "22.11.2025"

- measure_name: "Active Customers"
  is_kpi_measure: true
  kpi_id_ref: "crm.active_customers.count"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "01_Retention"
  category: "KPI"
  expression:
    dax: "DISTINCTCOUNT(fact_sales[CustomerKey])"
    formatString: "#,0"
  documentation:
    description: "Distinct customers with at least one qualified transaction in the selected period."
    notes: "Filters from outer context (Date, Org, Product) automatically apply."
  dependencies:
    columns:
      - "fact_sales[CustomerKey]"
  governance:
    owner: "CRM BI"
    status: "active"
    version: "v1.1"
    last_review: "22.11.2025"

- measure_name: "Active Customers Start"
  is_kpi_measure: true
  kpi_id_ref: "crm.active_customers_start.count"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "01_Retention"
  category: "KPI"
  expression:
    dax: |
      VAR StartDate =
          MINX ( ALLSELECTED ( dim_date[Date] ), dim_date[Date] )
      RETURN
          CALCULATE (
              [Active Customers],
              KEEPFILTERS ( dim_date[Date] = StartDate )
          )
    formatString: "#,0"
  documentation:
    description: "Active customers evaluated at the first date inside the current filter context."
    notes: "Uses ALLSELECTED to respect slicers while isolating the opening snapshot."
  dependencies:
    measures:
      - "Active Customers"
    columns:
      - "dim_date[Date]"
  governance:
    owner: "CRM BI"
    status: "active"
    version: "v1.1"
    last_review: "22.11.2025"

- measure_name: "Active Customers End"
  is_kpi_measure: true
  kpi_id_ref: "crm.active_customers_end.count"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "01_Retention"
  category: "KPI"
  expression:
    dax: |
      VAR EndDate =
          MAXX ( ALLSELECTED ( dim_date[Date] ), dim_date[Date] )
      RETURN
          CALCULATE (
              [Active Customers],
              KEEPFILTERS ( dim_date[Date] = EndDate )
          )
    formatString: "#,0"
  documentation:
    description: "Active customers counted at the last date of the current context."
    notes: "Provides the closing base for retention and reactivation KPIs."
  dependencies:
    measures:
      - "Active Customers"
    columns:
      - "dim_date[Date]"
  governance:
    owner: "CRM BI"
    status: "active"
    version: "v1.1"
    last_review: "22.11.2025"

- measure_name: "Churned Customers"
  is_kpi_measure: true
  kpi_id_ref: "crm.churned_customers.count"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "01_Retention"
  category: "KPI"
  expression:
    dax: |
      CALCULATE (
          DISTINCTCOUNT ( fact_sales[CustomerKey] ),
          KEEPFILTERS ( fact_sales[CustomerStatus] = "Churned" )
      )
    formatString: "#,0"
  documentation:
    description: "Customers marked as churned within the current slice (lifecycle status provided by CRM)."
    notes: "Lifecycle tagging logic maintained in the data pipeline; measure simply filters on the flag."
  dependencies:
    columns:
      - "fact_sales[CustomerKey]"
      - "fact_sales[CustomerStatus]"
  governance:
    owner: "CRM BI"
    status: "active"
    version: "v1.1"
    last_review: "22.11.2025"

- measure_name: "Customer Retention %"
  is_kpi_measure: true
  kpi_id_ref: "crm.retention.pct"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "01_Retention"
  category: "KPI"
  expression:
    dax: |
      VAR Opening = [Active Customers Start]
      VAR Closing = [Active Customers End]
      RETURN
          DIVIDE ( Closing, Opening )
    formatString: "0.0 %"
  documentation:
    description: "Share of the opening active customers that stay active by period end."
    notes: "Assumes churned customers have already been removed from the closing base."
  dependencies:
    measures:
      - "Active Customers Start"
      - "Active Customers End"
  governance:
    owner: "CRM BI"
    status: "active"
    version: "v2.1"
    last_review: "22.11.2025"

- measure_name: "Churn Rate %"
  is_kpi_measure: true
  kpi_id_ref: "crm.churn.pct"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "01_Retention"
  category: "KPI"
  expression:
    dax: "DIVIDE([Churned Customers], [Active Customers Start])"
    formatString: "0.0 %"
  documentation:
    description: "Customers lost during the period divided by the opening active base."
    notes: "Complements Customer Retention % (1 - retention)."
  dependencies:
    measures:
      - "Churned Customers"
      - "Active Customers Start"
  governance:
    owner: "CRM BI"
    status: "active"
    version: "v2.1"
    last_review: "22.11.2025"

- measure_name: "Reactivated Customers Count"
  is_kpi_measure: true
  kpi_id_ref: "crm.reactivated_customers.count"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "01_Retention"
  category: "KPI"
  expression:
    dax: |
      CALCULATE (
          DISTINCTCOUNT ( fact_sales[CustomerKey] ),
          KEEPFILTERS ( fact_sales[CustomerActivity] = "Reactivated" )
      )
    formatString: "#,0"
  documentation:
    description: "Customers tagged as reactivated (were lost previously) in the selected timeframe."
    notes: "Requires lifecycle field fact_sales[CustomerActivity] maintained by CRM."
  dependencies:
    columns:
      - "fact_sales[CustomerKey]"
      - "fact_sales[CustomerActivity]"
  governance:
    owner: "CRM BI"
    status: "active"
    version: "v1.0"
    last_review: "22.11.2025"

- measure_name: "Reactivation Rate %"
  is_kpi_measure: true
  kpi_id_ref: "crm.reactivation.pct"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "01_Retention"
  category: "KPI"
  expression:
    dax: "DIVIDE([Reactivated Customers Count], [Churned Customers])"
    formatString: "0.0 %"
  documentation:
    description: "Share of churned customers that become active again within the period."
    notes: "Interpret alongside win-back campaign exposure."
  dependencies:
    measures:
      - "Reactivated Customers Count"
      - "Churned Customers"
  governance:
    owner: "CRM BI"
    status: "active"
    version: "v1.0"
    last_review: "22.11.2025"

- measure_name: "At-Risk Customers Count"
  is_kpi_measure: true
  kpi_id_ref: "crm.at_risk_customers.count"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "01_Retention"
  category: "KPI"
  expression:
    dax: |
      CALCULATE (
          DISTINCTCOUNT ( fact_sales[CustomerKey] ),
          KEEPFILTERS ( fact_sales[CustomerStatus] = "At Risk" )
      )
    formatString: "#,0"
  documentation:
    description: "Active customers flagged as high churn risk by the scoring model."
    notes: "Status values provided through fact_sales[CustomerStatus]."
  dependencies:
    columns:
      - "fact_sales[CustomerKey]"
      - "fact_sales[CustomerStatus]"
  governance:
    owner: "CRM BI"
    status: "active"
    version: "v1.0"
    last_review: "22.11.2025"

- measure_name: "At-Risk Share %"
  is_kpi_measure: true
  kpi_id_ref: "crm.at_risk_share.pct"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "01_Retention"
  category: "KPI"
  expression:
    dax: "DIVIDE([At-Risk Customers Count], [Active Customers])"
    formatString: "0.0 %"
  documentation:
    description: "Percentage of the current active base flagged as at-risk."
    notes: "Helps size mitigation playbooks and outreach capacity."
  dependencies:
    measures:
      - "At-Risk Customers Count"
      - "Active Customers"
  governance:
    owner: "CRM BI"
    status: "active"
    version: "v1.0"
    last_review: "22.11.2025"

- measure_name: "CLV"
  is_kpi_measure: true
  kpi_id_ref: "crm.clv.amount"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "03_Customer"
  category: "KPI"
  expression:
    dax: "SUM(fact_customer_value[CLVAmount])"
    formatString: "EUR #,0.00"
  documentation:
    description: "Discounted lifetime gross margin per customer sourced from the CLV data mart."
    notes: "fact_customer_value already applies discounting and cohort logic."
  dependencies:
    columns:
      - "fact_customer_value[CLVAmount]"
  governance:
    owner: "CRM BI"
    status: "active"
    version: "v1.0"
    last_review: "22.11.2025"

- measure_name: "Customer Revenue Share %"
  is_kpi_measure: true
  kpi_id_ref: "sales.customer.revenue_share.pct"
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "03_Customer"
  category: "KPI"
  expression:
    dax: |
      VAR TotalSales = CALCULATE ( [Net Sales Amount], ALL ( dim_customer ) )
      RETURN DIVIDE ( [Net Sales Amount], TotalSales )
    formatString: "0.0 %"
  documentation:
    description: "Share of total net sales contributed by the current customer or segment."
    notes: "Uses ALL(dim_customer) to benchmark each customer against the entire customer set."
  dependencies:
    measures:
      - "Net Sales Amount"
    columns:
      - "dim_customer[CustomerKey]"
  governance:
    owner: "CRM BI"
    status: "active"
    version: "v1.0"
    last_review: "22.11.2025"

- measure_name: "Promoters Count"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "02_CX"
  category: "Base"
  expression:
    dax: "SUM(fact_survey[Promoters])"
    formatString: "#,0"
  documentation:
    description: "Number of survey respondents scoring 9-10 (promoters)."
    notes: "Input measure for NPS."
  dependencies:
    columns:
      - "fact_survey[Promoters]"
  governance:
    owner: "CX BI"
    status: "active"
    version: "v1.0"
    last_review: "22.11.2025"

- measure_name: "Detractors Count"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "CustomerValue_SemanticModel"
  display_folder: "02_CX"
  category: "Base"
  expression:
    dax: "SUM(fact_survey[Detractors])"
    formatString: "#,0"
  documentation:
    description: "Number of survey respondents scoring 0-6 (detractors)."
    notes: "Input measure for NPS."
  dependencies:
    columns:
      - "fact_survey[Detractors]"
  governance:
    owner: "CX BI"
