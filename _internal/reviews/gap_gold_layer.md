# Gold Layer Gap List

Purpose: Missing tables/fields in data_contracts/domains needed to implement Measure Dictionaries.

## TODO Summary (Measure Dictionaries)

### A) Missing gold data (new table/column required)
- (none)

### B) Mapping/standardization required (use existing gold columns)

### C) Definition/baseline decision required

### D) Formula implementation pending (data available once mappings are set)

- (none)

## Commercial

Missing raw columns in gold layer (commercial_sales):

- fact_sales: Plan COGS Amount
- fact_sales: Rebate Amount
- fact_sales: Surcharge Amount

Mappings/derivations (no gap):

- (none)

## Growth

Missing raw columns in gold layer (required for calculations):

- fact_forecast: Net Sales Amount (revenue forecast missing in gold)

Mappings/derivations (no gap):

- fact_sales: Net Sales Amount LY -> Last Year Sales Amount
- fact_sales: Baseline Sales Amount -> fact_promo Baseline Sales Amount (table mismatch)
- fact_sales: Promo Sales Amount -> derive from fact_sales Net Sales Amount filtered by Promo Flag
- fact_promo: Promo Amount -> fact_promo Promo Cost (or Funding Amount) if definition aligns

## CustomerValue

Missing raw tables/columns in gold layer:

- fact_crm_opportunity (Stage, Amount)
- fact_crm_leads (Leads, Conversions, Acquisition Spend Amount)
- fact_market (Market Revenue, Top Competitor Revenue)
- fact_brand_survey (Awareness %, Preference %)

Mappings/derivations (no gap):

- fact_customer_events: Reactivation Flag -> derive from Activity/Churn history
- fact_experience: Interaction ID -> use Complaint ID (commercial_sales.fact_experience) or extend experience domain

## Efficiency

Missing raw tables/columns in gold layer:

- (none)

Mappings/derivations (no gap):

- (none)

## Liquidity

Missing raw columns in gold layer (finance):

- (none)

Mappings/derivations (no gap):

- fact_balance: Receivables/Inventory/Payables -> fact_ar[AR Amount], fact_inventory[Inventory Amount], fact_ap[AP Amount]
- fact_sales: Net Sales Amount -> fact_finance[Net Sales Amount]
- fact_cashflow: OperatingCashFlow -> Operating Cash Flow Amount
- fact_cashflow: CapEx -> CapEx Amount

## Profitability

Missing raw tables/columns in gold layer:

- (none)

Mappings/derivations (no gap):

- fact_sales: Promo Cost Amount -> fact_promo Promo Cost
- fact_sales: Baseline Non-Promo Sales Amount -> fact_promo Baseline Non-Promo Sales Amount

## InnovationPeople

Missing raw tables/columns in gold layer:

- fact_hr, fact_hr_cost, fact_hr_headcount, fact_hr_time, fact_hrsurvey
- fact_it (Digital Users)
- fact_marketing (Marketing Cost Amount)
- fact_product_investment (Product Investment Amount)
- dim_product: Active, Launch Date, Lifecycle Phase
- fact_sales: New Product Revenue

Mappings/derivations (no gap):

- fact_financials (RevenueAmount, GrossMarginAmount) -> fact_finance Net Sales Amount + COGS Amount
- fact_hr: Attrition Risk % -> fact_customer_events Attrition Risk % (commercial_sales)
- fact_sales: Promo Cost Amount -> fact_promo Promo Cost
- fact_sales: Contribution Margin Amount -> derive from Net Sales Amount - Cost of Goods Sold Amount (if definition aligns)

## Governance

Missing raw tables/columns in gold layer:

- (none)

Mappings/derivations (no gap):

- (none)

## Risk

Missing raw tables/columns in gold layer:

- fact_credit_risk (PD, LGD, EAD, Exposure ID)

Mappings/derivations (no gap):

- (none)

## ESG

Missing raw tables/columns in gold layer:

- fact_sustainability (CO2 Emissions)
- fact_energy (Renewable kWh, Total kWh)
- fact_safety (LTIs, Hours Worked)
- fact_sales: ESG Aligned Revenue

Mappings/derivations (no gap):

- (none)

## SupplyChain

Missing raw tables/columns in gold layer:

- fact_planning: Replan Count

Mappings/derivations (no gap):

- fact_inventory: Avg Inventory -> Average Inventory Amount
- fact_inventory: Obsolete Stock, Total Stock -> Obsolete Inventory Amount + Average Inventory Amount/Units (confirm definition)
- fact_cogs: COGS -> COGS Amount
- fact_forecast: Forecast -> Forecast Units
- fact_sales: Actual, Actual Units -> Sales Units
- fact_stockout: Lost Demand, Demand, Demand Occurrences -> Lost Demand Units, Demand Units (occurrences via row count)

## Service

Missing raw columns in gold layer (experience):

- (none)

Mappings/derivations (no gap):

- fact_cases: Open Cases -> Open Case Flag
- fact_nps: Is Promoter/Is Detractor -> derive from NPS Score

## Finance

Missing raw tables/columns in gold layer:

- (none)

Mappings/derivations (no gap):

- fact_cash: Cash Balance -> Cash Balance Amount
- plan_cash: Cash Balance -> fact_cash Plan Cash Amount
- fact_cashflow: OCF -> Operating Cash Flow Amount
- fact_ar: AR -> AR Amount
- fact_ap: AP -> AP Amount
- fact_inventory: Inventory -> Inventory Amount
- fact_sales: Net Sales Amount -> fact_finance Net Sales Amount
- fact_cogs: COGS -> COGS Amount
- fact_cost: COGS, Material Cost -> COGS Amount, Material Cost Amount
- fact_finance: Net Sales, COGS, EBITDA -> Net Sales Amount, COGS Amount, EBITDA Amount
- fact_opex: OpEx -> OpEx Amount
- plan_opex: Plan OpEx -> fact_finance Plan OpEx Amount
- fact_output: Units -> Output Units

## Operations

Missing raw columns in gold layer:

- fact_ops: Unplanned Downtime Minutes (no downtime type in gold)
- fact_ops: Unplanned Downtime

Mappings/derivations (no gap):

- fact_ops_failures: Failure Start/End -> Failure Start DateTime/Failure End DateTime
- fact_ops_failures: Repair Duration -> Repair Duration Hours
- fact_quality: Units -> Total Units
- fact_quality_costs: COPQ -> COPQ Amount
- fact_complaints: Complaints -> Complaint Count
- fact_shipments: Units -> Shipped Units
- fact_maintenance: Orders -> count rows
- fact_maintenance: PM On Time/PM Planned -> Order Type + On Time Flag

## People

Missing raw tables/columns in gold layer:

- fact_hr (Headcount, Leavers, Absent Hours, Scheduled Hours, FTE, Personnel Cost)
- fact_it (Digital Users)
- fact_survey (Engaged Responses, Total Responses, Training Hours)

Mappings/derivations (no gap):

- dim_date: MonthKey -> derive from DateKey/MonthNumber
- fact_finance: Revenue -> Net Sales Amount (finance)
- fact_sales: COGS -> Cost of Goods Sold Amount (commercial_sales)
