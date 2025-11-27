# Action Codes Portfolio v2

> Draft status: v2 – AI-ready, sales-ready, operational-ready. Covers all domains and all 73 use cases at a reusable action level.

---

## 1. Overview

This document defines the standardized Action Codes used across the analytics-usecase-library. Each Action Code represents a reusable, operational measure that translates KPI deviations into concrete actions.

**Core principles:**
- KPI-linked and trigger-based (L1–L3)
- Realistic, range-based impact (no pseudo-precision)
- Operationally executable (roles, steps, effort)
- Risk-aware (trade-offs and side effects)
- AI-ready (Copilot and automation hooks)
- Reusable across multiple use cases

The portfolio is structured by domain:

1. Commercial
2. Operational Efficiency
3. Customer & Market
4. Corporate & Strategy
5. ESG
6. Governance & Compliance
7. Innovation & People

Each Action Code follows the same template structure.

---

## 2. Template

```yaml
Code:
Name:
Domain:
Primary KPI:
Secondary KPIs: []

Trigger:
  type: Deviation | Pattern | Risk | Structural
  L1: "..."   # Early warning
  L2: "..."   # Required intervention
  L3: "..."   # Critical
  L3_note: "Applies only if trend persists >2 periods or in strategic segments."

Impact:
  category: Low | Medium | High
  range: "..."           # realistic range, not a single number
  derivation: "Range based on historical benchmarks in relevant domain."
  mechanism:
    - "..."
  confidence: High | Medium | Low

OperationalExecution:
  roles:
    - "..."
  steps:
    - "..."
  effort: Low | Medium | High
  risks:
    - "..."

DataRequirements:
  - "..."

MaturityLevel: Basic | Advanced | Expert

SuccessMeasurement:
  baseline: "..."            # how to define the pre-action state
  kpi_7d: "..."              # optional for fast-moving KPIs
  kpi_30d: "..."             # standard review point
  kpi_60d: "..."             # for structural actions
  success_definition: "..."   # what success means

Automation:
  triggers:
    - "..."   # alert logic / rule
  actions:
    - "..."   # workflow / task
  copilot_prompts:
    
    - "Summarize risks and opportunities."
    - "Generate recommended next steps."
    - "Explain expected impact range with rationale."- "Explain why this action was suggested for my KPI deviations."
    - "Summarize the operational steps for this action for my team."
```

All Action Codes below are instances of this template.

---

# Commercial Action Codes

## C-P1 – Price & Discount Management

```yaml
Code: C-P1.1
Name: Correct Price Leakage (Micro Adjustments)
Domain: Commercial
Primary KPI: Price Realization %
Secondary KPIs: [Gross Margin %, Revenue Growth %]

Trigger:
  type: Deviation
  L1: "Price Realization % < Target − 1.0 pp"
  L2: "Price Realization % < Target − 2.5 pp"
  L3: "Price Realization % < Target − 4.0 pp"
  L3_note: "Applies only if trend persists >2 periods or in strategic segments."

Impact:
  category: Medium
  range: "+0.1 to +0.5 pp Gross Margin %"
  derivation: "Range based on historical benchmarks in relevant domain."
  mechanism:
    - "Reduce excessive discounts or unapproved markdowns."
    - "Align transactional prices to agreed list/net prices."
  confidence: Medium

OperationalExecution:
  roles:
    - "Pricing Manager"
    - "Sales Controller"
  steps:
    - "Identify SKUs and customers with highest price leakage relative to list/net prices."
    - "Cluster segments by elasticity and strategic relevance."
    - "Apply small list/net price corrections or stricter discount rules for low-elasticity clusters."
    - "Communicate new guardrails to sales and update pricing tools."
    - "Monitor GM% and Price Realization for 30 days."
  effort: Medium
  risks:
    - "Potential churn in highly price-sensitive customer segments."
    - "Sales pushback if changes are not communicated and justified."

DataRequirements:
  - "Net price per SKU and customer"
  - "List price / reference price"
  - "Discount structure"
  - "Price Realization % by segment"

MaturityLevel: Advanced

SuccessMeasurement:
  baseline: "Price Realization % and Gross Margin % per segment over last 3 months."
  kpi_7d: "Early check of complaints/churn signals in affected segments."
  kpi_30d: "Compare Price Realization % and GM% vs baseline, adjusted for volume."
  kpi_60d: "Stability check; ensure no hidden leakages reappear."
  success_definition: "+0.1–0.3 pp GM% improvement without material churn increase."

Automation:
  triggers:
    - "Alert when Price Realization % < Target − 2.5 pp for at least 2 consecutive periods."
  actions:
    - "Generate list of SKUs/customers with highest leakage for review."
  copilot_prompts:
    
    - "Summarize risks and opportunities."
    - "Generate recommended next steps."
    - "Explain expected impact range with rationale."- "Which SKUs show the highest price leakage and should be targeted by C-P1.1?"
    - "Draft a communication for sales explaining the C-P1.1 action and rationale."
```

```yaml
Code: C-P1.2
Name: Tighten Discount Policy
Domain: Commercial
Primary KPI: Discount Rate %
Secondary KPIs: [Gross Margin %, Revenue Growth %]

Trigger:
  type: Deviation
  L1: "Discount Rate % > Target + 2 pp"
  L2: "Discount Rate % > Target + 4 pp"
  L3: "Discount Rate % > Target + 6 pp"
  L3_note: "Applies only if trend persists >2 periods or in strategic segments."

Impact:
  category: Medium
  range: "+0.2 to +0.7 pp Gross Margin %"
  derivation: "Range based on historical benchmarks in relevant domain."
  mechanism:
    - "Reduce unprofitable discount levels on low-elasticity products."
    - "Shift from blanket rebates to targeted, performance-based conditions."
  confidence: Medium

OperationalExecution:
  roles:
    - "Pricing Manager"
    - "Key Account Manager"
    - "Sales Director"
  steps:
    - "Identify customers and products with highest relative discount vs target grid."
    - "Simulate GM% impact for reducing discounts within agreed bands."
    - "Negotiate updated conditions for selected accounts."
    - "Adjust discount schemas in ERP/CRM systems."
    - "Monitor margin, volume, and churn signals."
  effort: High
  risks:
    - "Loss of key accounts if conditions are tightened too aggressively."
    - "Short-term volume decline while customers adapt."

DataRequirements:
  - "Invoice-level discount information"
  - "Target discount grid per segment"
  - "Gross Margin % by account and product"

MaturityLevel: Advanced

SuccessMeasurement:
  baseline: "Discount Rate %, GM%, and volume per account/segment before implementation."
  kpi_30d: "GM% vs baseline and volume stability."
  kpi_60d: "Sustained GM% uplift with acceptable volume and churn."
  success_definition: "+0.2–0.5 pp GM% gain with no structural churn in strategic segments."

Automation:
  triggers:
    - "Alert when Discount Rate % exceeds target band for >3 consecutive periods."
  actions:
    - "Generate list of outlier accounts and SKUs with excessive discounts."
  copilot_prompts:
    
    - "Summarize risks and opportunities."
    - "Generate recommended next steps."
    - "Explain expected impact range with rationale."- "Identify which accounts are most suitable for C-P1.2 discount tightening."
    - "Summarize the expected GM% impact if we apply C-P1.2 to top 20 accounts."
```

```yaml
Code: C-P1.3
Name: Strategic Repricing
Domain: Commercial
Primary KPI: Gross Margin %
Secondary KPIs: [Revenue Growth %, Market Share %]

Trigger:
  type: Pattern
  L1: "Gross Margin % below target for 3 consecutive periods"
  L2: "Gross Margin % below target and Revenue Growth % < Plan − 2 %"
  L3: "Gross Margin % below target and Revenue declining vs LY in strategic segments"
  L3_note: "Applies only if trend persists >2 periods or in strategic segments."

Impact:
  category: High
  range: "+0.5 to +2.0 pp Gross Margin % over 6–12 months"
  derivation: "Range based on historical benchmarks in relevant domain."
  mechanism:
    - "Redesign overall price architecture by segment, channel, and value proposition."
    - "Align prices with value perception and competitor benchmarks."
  confidence: Medium

OperationalExecution:
  roles:
    - "Head of Pricing"
    - "Business Unit Lead"
    - "Finance / Controlling"
  steps:
    - "Segment customers and products by value, elasticity, and strategic relevance."
    - "Benchmark competitor price levels and value-add features."
    - "Redesign the price list and discount structures per segment."
    - "Pilot new pricing in selected regions or channels."
    - "Roll out globally with governance and monitoring."
  effort: High
  risks:
    - "Significant churn in price-sensitive segments if value gap is not addressed."
    - "Channel conflict when price levels differ between routes-to-market."

DataRequirements:
  - "Historical GM% and revenue by segment"
  - "Competitor price benchmarks"
  - "Elasticity estimates"

MaturityLevel: Expert

SuccessMeasurement:
  baseline: "GM%, revenue, and market share by segment over last 12 months."
  kpi_30d: "Early feedback and volume response in pilot segments."
  kpi_60d: "First trend check after initial rollout."
  kpi_180d: "Full assessment of GM%, revenue, and market share vs baseline."
  success_definition: "+0.5–1.5 pp GM% with stable or growing market share in target segments."

Automation:
  triggers:
    - "Flag segments where GM% is consistently below target and no pricing action was executed in last 12 months."
  actions:
    - "Generate a pricing review pack for identified segments."
  copilot_prompts:
    
    - "Summarize risks and opportunities."
    - "Generate recommended next steps."
    - "Explain expected impact range with rationale."- "Which segments should undergo C-P1.3 Strategic Repricing based on last 12 months of performance?"
    - "Summarize key risks and opportunities for a C-P1.3 action in the Commercial domain."
```

## C-M1 – Mix & Promotion Management

```yaml
Code: C-M1.1
Name: Product Mix Optimization
Domain: Commercial
Primary KPI: Gross Margin %
Secondary KPIs: [Product Mix %, Revenue Growth %]

Trigger:
  type: Deviation
  L1: "Share of low-margin products > 55 % of volume"
  L2: "Share of low-margin products > 60 % of volume"
  L3: "Share of low-margin products > 65 % of volume or GM% < Target − 2 pp"
  L3_note: "Applies only if trend persists >2 periods or in strategic segments."

Impact:
  category: Medium
  range: "+0.2 to +0.8 pp Gross Margin %"
  derivation: "Range based on historical benchmarks in relevant domain."
  mechanism:
    - "Shift demand from low-margin to higher-margin SKUs within same category."
    - "Adjust promo mechanics and sales focus to favor profitable SKUs."
  confidence: Medium

OperationalExecution:
  roles:
    - "Category Manager"
    - "Sales Manager"
  steps:
    - "Identify categories with unfavorable mix and GM% underperformance."
    - "Classify SKUs into low, medium, and high margin tiers."
    - "Design promo and incentive schemes to boost mid/high-margin SKU share."
    - "Align sales scripts and merchandising guidelines."
    - "Monitor mix and GM% weekly during campaign."
  effort: Medium
  risks:
    - "Short-term volume risk if high-margin products are less price-competitive."
    - "Channel resistance if incentives are not aligned."

DataRequirements:
  - "GM% by SKU"
  - "Volume and revenue by SKU"
  - "Promo calendar and mechanics"

MaturityLevel: Basic

SuccessMeasurement:
  baseline: "GM% and product mix % by category before intervention."
  kpi_30d: "Change in mix and GM% vs baseline."
  kpi_60d: "Stability of improved mix after campaign."
  success_definition: "Increase in high-margin SKU share by 3–5 pp with +0.2–0.5 pp GM%."

Automation:
  triggers:
    - "Alert when low-margin SKU share exceeds 60 % of volume in a category."
  actions:
    - "Generate list of SKUs per margin tier and suggest candidate SKUs for uplift."
  copilot_prompts:
    
    - "Summarize risks and opportunities."
    - "Generate recommended next steps."
    - "Explain expected impact range with rationale."- "Which categories require C-M1.1 based on current product mix and GM% performance?"
```

```yaml
Code: C-M1.2
Name: Promotion ROI Optimization
Domain: Commercial
Primary KPI: Promo ROI %
Secondary KPIs: [Revenue Growth %, Gross Margin %]

Trigger:
  type: Deviation
  L1: "Promo ROI % < 1.0"
  L2: "Promo ROI % < 0.8"
  L3: "Recurring promos with ROI % < 0.8 in same category over 3 periods"
  L3_note: "Applies only if trend persists >2 periods or in strategic segments."

Impact:
  category: Medium
  range: "+10 to +30 % Promo ROI"
  derivation: "Range based on historical benchmarks in relevant domain."
  mechanism:
    - "Reduce or redesign low-ROI promotions."
    - "Shift spend to high-ROI channels, products, and mechanics."
  confidence: Medium

OperationalExecution:
  roles:
    - "Trade Marketing Manager"
    - "Category Manager"
    - "Finance Business Partner"
  steps:
    - "Analyze historic promo performance by mechanic, channel, and product."
    - "Identify bottom quartile promos by ROI."
    - "Redesign or cancel low-ROI promos and reallocate budget."
    - "Test alternative mechanics (e.g., mix bundles, value packs)."
    - "Review post-promo lift and ROI."
  effort: Medium
  risks:
    - "Short-term volume dip if aggressive discounts are reduced."
    - "Retailer pressure if promo support is cut."

DataRequirements:
  - "Promo spend and incremental sales"
  - "Baseline volume estimates"
  - "Channel and mechanic details"

MaturityLevel: Advanced

SuccessMeasurement:
  baseline: "Average Promo ROI % for last 3–6 months."
  kpi_30d: "ROI % of redesigned promos vs historic baseline."
  kpi_60d: "Category-level GM% and revenue trend."
  success_definition: "Improvement of Promo ROI by 10–30 % with stable or better category revenue."

Automation:
  triggers:
    - "Alert when a planned promo resembles past low-ROI mechanics in same category."
  actions:
    - "Suggest alternative promo mechanics based on historic top quartile performance."
  copilot_prompts:
    
    - "Summarize risks and opportunities."
    - "Generate recommended next steps."
    - "Explain expected impact range with rationale."- "Which upcoming promotions should be challenged with C-M1.2?"
```
# Operational Efficiency Action Codes

## O-E1 – Equipment & Maintenance

```yaml
Code: O-E1.1
Name: Reduce Unplanned Downtime via Maintenance Planning
Domain: Operational Efficiency
Primary KPI: OEE
Secondary KPIs: [Downtime %, Cost per Unit]

Trigger:
  type: Pattern
  L1: "Unplanned downtime > 3 % for 2 periods"
  L2: "Unplanned downtime > 5 % for 2 periods"
  L3: "Unplanned downtime > 8 % or repeated failures"
  L3_note: "Applies only if trend persists >2 periods or in strategic segments."

Impact:
  category: Medium
  range: "+1 to +3 pp OEE"
  derivation: "Range based on historical benchmarks in relevant domain."
  mechanism:
    - "Shift from reactive to preventive maintenance."
  confidence: Medium

OperationalExecution:
  roles:
    - "Maintenance Manager"
    - "Production Planner"
  steps:
    - "Analyze downtime logs and classify root causes."
    - "Define preventive tasks and standard intervals."
    - "Plan maintenance windows in low-demand slots."
    - "Monitor OEE and downtime weekly and adjust plan."
  effort: Medium
  risks:
    - "Temporary capacity reduction during planned maintenance."

DataRequirements:
  - "Downtime logs (reason, duration)"
  - "OEE components (availability, performance, quality)"

MaturityLevel: Basic

SuccessMeasurement:
  baseline: "Last 3–6 periods OEE and unplanned downtime %."
  kpi_30d: "Reduction in unplanned downtime and improvement in OEE."
  kpi_60d: "Sustained OEE uplift and stable output."
  success_definition: "Unplanned downtime −1–2 pp with stable or better throughput."

Automation:
  triggers:
    - "Unplanned downtime > 5 % in 2 consecutive periods."
  actions:
    - "Generate maintenance priority list with top recurring failure modes."
```

```yaml
Code: O-E1.2
Name: Throughput Balancing
Domain: Operational Efficiency
Primary KPI: Throughput
Secondary KPIs: [OEE, Cycle Time]

Trigger:
  type: Deviation
  L1: "Utilization < 85 % for 2 periods"
  L2: "Utilization < 80 % and backlog rising"
  L3: "Utilization < 75 % and backlog rising in multiple lines"
  L3_note: "Applies only if trend persists >2 periods or in strategic segments."

Impact:
  category: Medium
  range: "+2 to +5 % throughput"
  derivation: "Range based on historical benchmarks in relevant domain."
  mechanism:
    - "Relieve bottlenecks and rebalance workload across lines."
  confidence: Medium

OperationalExecution:
  roles:
    - "Operations Lead"
    - "Line Supervisor"
  steps:
    - "Identify bottlenecks via cycle time and WIP analysis."
    - "Reallocate workforce or adjust shift patterns."
    - "Optimize lot sizes and sequencing."
    - "Monitor throughput daily and fine-tune balancing."
  effort: Medium
  risks:
    - "Short-term instability while new patterns settle."

DataRequirements:
  - "Cycle time per step"
  - "Utilization per line"
  - "Backlog / WIP levels"

MaturityLevel: Basic

SuccessMeasurement:
  baseline: "Throughput and utilization vs target for last 4–8 weeks."
  kpi_30d: "Throughput uplift and reduced backlog."
  kpi_60d: "Stable throughput with utilization in target band."
  success_definition: "+2–5 % throughput in constrained areas."
```

## O-I1 – Inventory Management

```yaml
Code: O-I1.1
Name: Inventory Policy Adjustment
Domain: Operational Efficiency
Primary KPI: DIO
Secondary KPIs: [Stockout Rate %, Working Capital %]

Trigger:
  type: Deviation
  L1: "DIO > Target +5 days"
  L2: "DIO > Target +10 days"
  L3: "DIO > Target +15 days or stockouts rising in parallel"
  L3_note: "Applies only if trend persists >2 periods or in strategic segments."

Impact:
  category: Medium
  range: "−3 to −10 days DIO"
  derivation: "Range based on historical benchmarks in relevant domain."
  mechanism:
    - "Align safety stocks and reorder parameters with demand variability and lead times."
  confidence: Medium

OperationalExecution:
  roles:
    - "Supply Chain Planner"
    - "Inventory Manager"
  steps:
    - "Segment SKUs by volatility and criticality."
    - "Recalculate safety stocks and reorder points per segment."
    - "Implement new parameters in planning system."
    - "Monitor DIO, stockouts, and service level weekly."
  effort: Medium
  risks:
    - "Higher stockout risk if reductions are too aggressive."

DataRequirements:
  - "Demand history (by SKU)"
  - "Lead times"
  - "Current safety stock parameters"

MaturityLevel: Advanced

SuccessMeasurement:
  baseline: "DIO and stockout rate by segment before adjustment."
  kpi_30d: "DIO reduction and service level monitoring."
  kpi_60d: "Stable DIO with acceptable stockouts."
  success_definition: "DIO reduction within target range without material service level drop."
```

## O-C1 – Cost Efficiency

```yaml
Code: O-C1.1
Name: Process Simplification
Domain: Operational Efficiency
Primary KPI: Cost per Unit
Secondary KPIs: [Cycle Time, Error Rate]

Trigger:
  type: Structural
  L1: "Process steps > benchmark +10 %"
  L2: "Cycle time > target +15 %"
  L3: "Cycle time > target +20 % and error rate rising"
  L3_note: "Applies only if trend persists >2 periods or in strategic segments."

Impact:
  category: Medium
  range: "−2 to −5 % cost per unit"
  derivation: "Range based on historical benchmarks in relevant domain."
  mechanism:
    - "Remove non-value-adding activities and simplify process flows."
  confidence: Medium

OperationalExecution:
  roles:
    - "Operations Lead"
    - "Lean Specialist"
  steps:
    - "Map current processes (value stream mapping)."
    - "Identify waste (waiting, rework, transport, overprocessing)."
    - "Redesign workflows and standard work."
    - "Pilot new process in a limited scope and scale if successful."
  effort: Medium
  risks:
    - "Change resistance."
    - "Risk of missing control steps if simplification is overdone."

DataRequirements:
  - "Process maps and SOPs"
  - "Cycle time per step"
  - "Cost per unit baseline"

MaturityLevel: Basic

SuccessMeasurement:
  baseline: "Cost per unit, cycle time, and error rate before simplification."
  kpi_30d: "Cycle time reduction and error rate stability."
  kpi_60d: "Cost per unit reduction within expected range."
  success_definition: "−2–5 % cost per unit with stable or improved quality."
```
# Customer & Market Action Codes

## CM-R1 – Retention & Churn Management

```yaml
Code: CM-R1.1
Name: Early Churn Signal Intervention
Domain: Customer & Market
Primary KPI: Churn %
Secondary KPIs: [Retention %, CLV]

Trigger:
  type: Risk
  L1: "Churn probability > 0.25"
  L2: "Churn probability > 0.35"
  L3: "Churn probability > 0.45 or negative NPS trend"
  L3_note: "Applies only if trend persists >2 periods or in strategic segments."

Impact:
  category: Medium
  range: "+1 to +3 pp retention"
  derivation: "Range based on historical benchmarks in relevant domain."
  mechanism:
    - "Targeted offers or personalized outreach to at-risk customers."
  confidence: Medium

OperationalExecution:
  roles:
    - "CRM Manager"
    - "Customer Success Lead"
  steps:
    - "Identify risk segments using churn model."
    - "Prioritize customers by revenue and margin relevance."
    - "Launch personalized outreach (email/call/offers)."
    - "Track retention signals over 30–60 days."
  effort: Medium
  risks:
    - "Over-discounting."
    - "Training customers to wait for offers."

DataRequirements:
  - "Churn model scores"
  - "Customer segmentation"
  - "NPS and feedback data"

MaturityLevel: Advanced

SuccessMeasurement:
  baseline: "Last 3-month churn % and retention % by segment."
  kpi_30d: "Retention uplift in targeted groups."
  kpi_60d: "Sustained reduction in churn vs baseline."
  success_definition: "+1–3 pp retention in targeted groups."
```

```yaml
Code: CM-R1.2
Name: Win-Back Campaign
Domain: Customer & Market
Primary KPI: Retention %
Secondary KPIs: [CLV]

Trigger:
  type: Pattern
  L1: "Customer inactive > 30 days"
  L2: "Customer inactive > 60 days"
  L3: "Customer inactive > 90 days and high CLV segment"
  L3_note: "Applies only if trend persists >2 periods or in strategic segments."

Impact:
  category: Medium
  range: "+1 to +2 pp retention (targeted)"
  derivation: "Range based on historical benchmarks in relevant domain."
  mechanism:
    - "Reactivation through high-value win-back offers."
  confidence: Medium

OperationalExecution:
  roles:
    - "CRM Manager"
    - "Marketing Lead"
  steps:
    - "Identify inactive customers by cohort."
    - "Define win-back offers by segment."
    - "Send email/push automation."
    - "Monitor reactivation and second purchase rate."
  effort: Low
  risks:
    - "Cannibalization if offers are too generous or too frequent."

DataRequirements:
  - "Customer activity logs"
  - "CLV calculations"
  - "Campaign response data"

MaturityLevel: Basic

SuccessMeasurement:
  baseline: "Inactivity distribution and baseline win-back rate."
  kpi_30d: "Win-back rate vs baseline."
  kpi_60d: "Retention stability of reactivated customers."
  success_definition: "+1–2 pp retention in target cohorts."
```

## CM-N1 – NPS & Service Quality

```yaml
Code: CM-N1.1
Name: Complaint Reduction Initiative
Domain: Customer & Market
Primary KPI: Complaint Rate %
Secondary KPIs: [NPS]

Trigger:
  type: Pattern
  L1: "Complaint rate rising for 2 periods"
  L2: "Complaint rate rising for 3 periods"
  L3: "Complaint rate rising and NPS < Target − 5 pts"
  L3_note: "Applies only if trend persists >2 periods or in strategic segments."

Impact:
  category: Medium
  range: "−0.2 to −0.5 pp complaint rate"
  derivation: "Range based on historical benchmarks in relevant domain."
  mechanism:
    - "Identify main complaint drivers and fix root causes in product and service."
  confidence: Medium

OperationalExecution:
  roles:
    - "Service Manager"
    - "Quality Lead"
  steps:
    - "Categorize complaints by type and channel."
    - "Identify top 3–5 drivers by volume and impact."
    - "Define and implement corrective actions."
    - "Monitor complaint trend and NPS monthly."
  effort: Medium
  risks:
    - "Slow implementation if cross-functional alignment is weak."

DataRequirements:
  - "Complaint logs with categories"
  - "NPS score and verbatims"

MaturityLevel: Basic

SuccessMeasurement:
  baseline: "Complaint rate by category and NPS baseline."
  kpi_30d: "Early sign of complaint reduction in key categories."
  kpi_60d: "NPS stabilization or improvement."
  success_definition: "Complaint rate −0.2–0.5 pp with stable or better NPS."
```

## CM-M1 – Market & Channel Performance

```yaml
Code: CM-M1.1
Name: Channel Performance Boost
Domain: Customer & Market
Primary KPI: Channel Sales %
Secondary KPIs: [Revenue Growth %, Conversion Rate %]

Trigger:
  type: Deviation
  L1: "Channel Sales % < Target − 2 pp"
  L2: "Channel Sales % < Target − 4 pp"
  L3: "Channel Sales % < Target − 6 pp and conversion rate declining"
  L3_note: "Applies only if trend persists >2 periods or in strategic segments."

Impact:
  category: Medium
  range: "+2 to +6 % channel sales uplift"
  derivation: "Range based on historical benchmarks in relevant domain."
  mechanism:
    - "Optimize channel mix, spend allocation, and promotional focus."
  confidence: Medium

OperationalExecution:
  roles:
    - "Channel Manager"
    - "Marketing Lead"
  steps:
    - "Identify underperforming channels vs target."
    - "Reallocate marketing spend to high-ROI channels."
    - "Adjust creative and offer strategy."
    - "Monitor sales and conversion by channel weekly."
  effort: Medium
  risks:
    - "Performance dilution in other channels."
    - "Short-term volatility during reallocation."

DataRequirements:
  - "Channel performance data (traffic, conversion, revenue)"
  - "Marketing spend data"

MaturityLevel: Advanced

SuccessMeasurement:
  baseline: "Channel revenue and conversion trends pre-intervention."
  kpi_30d: "Sales uplift in focus channels."
  kpi_60d: "Sustained conversion improvement and ROI."
  success_definition: "+2–6 % channel sales uplift with positive ROI."
```

## CM-S1 – Market Share

```yaml
Code: CM-S1.1
Name: Market Share Stabilization
Domain: Customer & Market
Primary KPI: Market Share %
Secondary KPIs: [Revenue Growth %]

Trigger:
  type: Pattern
  L1: "Market share stagnant for 2 periods"
  L2: "Market share stagnant for 3 periods"
  L3: "Market share declining and competitor prices dropping"
  L3_note: "Applies only if trend persists >2 periods or in strategic segments."

Impact:
  category: Medium
  range: "0.3 to 1.0 pp market share improvement"
  derivation: "Range based on historical benchmarks in relevant domain."
  mechanism:
    - "Competitive pricing, positioning, and channel adjustments."
  confidence: Medium

OperationalExecution:
  roles:
    - "Product Manager"
    - "Competitive Intelligence Lead"
  steps:
    - "Analyze market share by segment and channel."
    - "Review competitor pricing and proposition."
    - "Define targeted responses (pricing, packs, promotions)."
    - "Monitor share monthly by segment."
  effort: Medium
  risks:
    - "Margin compression if pricing response is too aggressive."

DataRequirements:
  - "Market share data by segment"
  - "Competitor pricing and activity intel"

MaturityLevel: Advanced

SuccessMeasurement:
  baseline: "Market share and revenue trend over last 3–6 periods."
  kpi_60d: "Trend reversal in key segments."
  kpi_90d: "Stabilized or growing market share vs baseline."
  success_definition: "0.3–1.0 pp improvement in focus segments."
```
# ESG Action Codes

## ESG-E1 – Emissions Management

```yaml
Code: ESG-E1.1
Name: CO₂ Intensity Reduction
Domain: ESG
Primary KPI: CO2 Intensity
Secondary KPIs: [Energy Consumption, Cost per Unit]

Trigger:
  type: Deviation
  L1: "CO₂ intensity > target +5 %"
  L2: "CO₂ intensity > target +10 %"
  L3: "CO₂ intensity > target +15 % or rising trend > 3 periods"
  L3_note: "Applies only if trend persists >2 periods or in strategic segments."

Impact:
  category: Medium
  range: "−3 to −8 % CO₂ intensity"
  derivation: "Range based on historical benchmarks in relevant domain."
  mechanism:
    - "Optimize energy usage and shift to lower-emission processes and sources."
  confidence: Medium

OperationalExecution:
  roles:
    - "ESG Manager"
    - "Operations Lead"
  steps:
    - "Identify emission hotspots by process, site, and energy source."
    - "Prioritize high-impact efficiency and substitution measures."
    - "Implement selected measures and track energy and emission data."
  effort: Medium
  risks:
    - "Upfront CapEx and potential operational disruption."

DataRequirements:
  - "Energy usage by source"
  - "Emission factors"
  - "Production output"

MaturityLevel: Advanced

SuccessMeasurement:
  baseline: "CO₂ intensity trend for last 6–12 months."
  kpi_60d: "Early reduction trend in targeted areas."
  kpi_120d: "Structural improvements visible in normalized intensity."
  success_definition: "−3–8 % CO₂ intensity in targeted perimeter."
```

## ESG-R1 – Renewable Energy Share

```yaml
Code: ESG-R1.1
Name: Increase Renewable Energy Share
Domain: ESG
Primary KPI: Renewable Energy Share %
Secondary KPIs: [CO₂ Intensity]

Trigger:
  type: Structural
  L1: "Renewable share < target −5 pp"
  L2: "Renewable share < target −10 pp"
  L3: "Renewable share < target −15 pp or energy cost rising significantly"
  L3_note: "Applies only if trend persists >2 periods or in strategic segments."

Impact:
  category: Medium
  range: "+5 to +15 pp renewable share"
  derivation: "Range based on historical benchmarks in relevant domain."
  mechanism:
    - "Shift procurement and on-site generation towards renewable sources."
  confidence: Medium

OperationalExecution:
  roles:
    - "ESG Manager"
    - "Procurement Lead"
  steps:
    - "Assess current energy contracts and mix."
    - "Negotiate renewable PPA or green tariffs."
    - "Evaluate and implement on-site renewable projects where feasible."
    - "Monitor mix and effective costs vs baseline."
  effort: Medium
  risks:
    - "Supplier price volatility."
    - "Contract complexity."

DataRequirements:
  - "Energy supplier data"
  - "Contract terms"
  - "Consumption by site"

MaturityLevel: Advanced

SuccessMeasurement:
  baseline: "Renewable share and CO₂ intensity baseline."
  kpi_60d: "Contracted mix improvement."
  kpi_120d: "Realized share increase in actual consumption."
  success_definition: "+5–15 pp renewable share with acceptable cost impact."
```

## ESG-W1 – Waste & Recycling

```yaml
Code: ESG-W1.1
Name: Waste Reduction Initiative
Domain: ESG
Primary KPI: Waste Volume %
Secondary KPIs: [Recycling Rate %]

Trigger:
  type: Pattern
  L1: "Waste volume rising for 2 periods"
  L2: "Waste volume rising for 3 periods"
  L3: "Waste rising and Recycling Rate < target −5 pp"
  L3_note: "Applies only if trend persists >2 periods or in strategic segments."

Impact:
  category: Medium
  range: "−3 to −7 % waste"
  derivation: "Range based on historical benchmarks in relevant domain."
  mechanism:
    - "Material optimization, process redesign, and higher reuse/recycling."
  confidence: Medium

OperationalExecution:
  roles:
    - "ESG Manager"
    - "Operations Lead"
    - "Quality Manager"
  steps:
    - "Identify main waste sources by material and process."
    - "Run root cause analysis for top contributors."
    - "Define process changes, material substitutions, or reuse options."
    - "Improve sorting and recycling infrastructure."
  effort: Medium
  risks:
    - "Operational disruption during changes."
    - "Quality risks if materials are substituted."

DataRequirements:
  - "Waste logs by type"
  - "Material usage"
  - "Recycling data"

MaturityLevel: Basic

SuccessMeasurement:
  baseline: "Waste volume and recycling rate baseline."
  kpi_30d: "Early improvement in waste trend."
  kpi_60d: "Visible uplift in recycling and reduction in landfill/incineration share."
  success_definition: "−3–7 % waste with stable product quality."
```
# Corporate & Strategy Action Codes

## CS-F1 – Financial Performance & Forecasting

```yaml
Code: CS-F1.1
Name: Forecast Accuracy Improvement
Domain: Corporate & Strategy
Primary KPI: Forecast Accuracy %
Secondary KPIs: [Revenue Growth %, EBITDA Margin %]

Trigger:
  type: Deviation
  L1: "Forecast Accuracy < 90 %"
  L2: "Forecast Accuracy < 85 %"
  L3: "Forecast Accuracy < 80 % for 2 consecutive cycles"
  L3_note: "Applies only if trend persists >2 periods or in strategic segments."

Impact:
  category: Medium
  range: "+3 to +8 pp forecast accuracy"
  derivation: "Range based on historical benchmarks in relevant domain."
  mechanism:
    - "Improve forecast inputs and driver-based models, and shorten feedback loops."
  confidence: Medium

OperationalExecution:
  roles:
    - "FP&A Lead"
    - "Business Controller"
  steps:
    - "Analyze forecast vs actual variance by driver."
    - "Identify weak drivers and missing variables."
    - "Refine models and assumptions."
    - "Implement rolling forecast process."
    - "Review accuracy every cycle."
  effort: Medium
  risks:
    - "Overfitting models to past patterns."

DataRequirements:
  - "Historic forecasts and actuals"
  - "Driver data (volume, price, mix, etc.)"

MaturityLevel: Advanced

SuccessMeasurement:
  baseline: "Forecast Accuracy % over last 6–12 months."
  kpi_30d: "Early improvement in key drivers."
  kpi_90d: "Sustained accuracy uplift."
  success_definition: "+3–8 pp improvement in forecast accuracy."
```

## CS-E1 – Expense Management

```yaml
Code: CS-E1.1
Name: SG&A Ratio Optimization
Domain: Corporate & Strategy
Primary KPI: SG&A Ratio %
Secondary KPIs: [EBITDA Margin %]

Trigger:
  type: Deviation
  L1: "SG&A > Target +1 pp"
  L2: "SG&A > Target +2 pp"
  L3: "SG&A > Target +3 pp or EBITDA Margin < Target"
  L3_note: "Applies only if trend persists >2 periods or in strategic segments."

Impact:
  category: Medium
  range: "−1 to −3 % SG&A"
  derivation: "Range based on historical benchmarks in relevant domain."
  mechanism:
    - "Reduce low-value SG&A cost while protecting growth and compliance-critical spend."
  confidence: Medium

OperationalExecution:
  roles:
    - "Finance Lead"
    - "Department Heads"
  steps:
    - "Break down SG&A by function, cost type, and owner."
    - "Identify low-value activities and contracts."
    - "Plan targeted reductions and efficiency measures."
    - "Monitor SG&A and service impact monthly."
  effort: Medium
  risks:
    - "Over-cutting critical capabilities."

DataRequirements:
  - "SG&A breakdown"
  - "Vendor and contract data"

MaturityLevel: Advanced

SuccessMeasurement:
  baseline: "SG&A ratio and level by function."
  kpi_60d: "Visible downward trend in SG&A ratio."
  success_definition: "−1–3 % SG&A ratio with stable or better operational performance."
```

## CS-W1 – Working Capital Optimization

```yaml
Code: CS-W1.1
Name: Reduce Days Sales Outstanding (DSO)
Domain: Corporate & Strategy
Primary KPI: DSO
Secondary KPIs: [Cash Conversion Cycle]

Trigger:
  type: Deviation
  L1: "DSO > Target +3 days"
  L2: "DSO > Target +6 days"
  L3: "DSO > Target +10 days"
  L3_note: "Applies only if trend persists >2 periods or in strategic segments."

Impact:
  category: Medium
  range: "−2 to −7 days DSO"
  derivation: "Range based on historical benchmarks in relevant domain."
  mechanism:
    - "Tighten credit and collection processes."
  confidence: Medium

OperationalExecution:
  roles:
    - "AR Manager"
    - "Finance Lead"
  steps:
    - "Segment customers by payment behavior and risk."
    - "Prioritize follow-up for high-risk/high-balance accounts."
    - "Use structured reminders and escalation paths."
    - "Negotiate payment plans where needed."
  effort: Medium
  risks:
    - "Relationship strain with key accounts if too aggressive."

DataRequirements:
  - "AR aging report"
  - "Payment history"

MaturityLevel: Basic

SuccessMeasurement:
  baseline: "Current DSO and aging structure."
  kpi_30d: "Collections increase in overdue buckets."
  kpi_60d: "DSO reduction by 2–7 days."
  success_definition: "DSO trend converging towards target without major write-offs."
```

## CS-C1 – Capital Allocation

```yaml
Code: CS-C1.1
Name: CapEx Prioritization Review
Domain: Corporate & Strategy
Primary KPI: CapEx Allocation Efficiency
Secondary KPIs: [EBITDA Margin %]

Trigger:
  type: Structural
  L1: "CapEx pipeline > budget by 10 %"
  L2: "CapEx pipeline > budget by 20 %"
  L3: "Large share of CapEx without clear ROI or strategic justification"
  L3_note: "Applies only if trend persists >2 periods or in strategic segments."

Impact:
  category: High
  range: "5–15 % CapEx reduction or reallocation"
  derivation: "Range based on historical benchmarks in relevant domain."
  mechanism:
    - "Rank projects by ROI and strategic fit and rebalance portfolio."
  confidence: Medium

OperationalExecution:
  roles:
    - "CFO"
    - "PMO Lead"
  steps:
    - "Collect business cases and ROI assumptions."
    - "Score projects by ROI, risk, and strategic impact."
    - "Defer or cancel low-value projects."
    - "Reallocate budget to high-impact initiatives."
  effort: High
  risks:
    - "Strategic delay if critical projects are misclassified."

DataRequirements:
  - "CapEx pipeline and budget"
  - "Project ROI and risk data"

MaturityLevel: Expert

SuccessMeasurement:
  baseline: "CapEx distribution by category and ROI."
  kpi_60d: "Adjusted CapEx plan approved."
  kpi_180d: "Observed impact on returns and margins."
  success_definition: "5–15 % CapEx efficiency gain vs original plan."
```
# Governance & Compliance Action Codes

## G-C1 – Compliance Management

```yaml
Code: G-C1.1
Name: Compliance Breach Mitigation
Domain: Governance & Compliance
Primary KPI: Compliance Rate %
Secondary KPIs: [Incident Count]

Trigger:
  type: Risk
  L1: "Compliance Rate % < Target − 2 pp"
  L2: "Compliance Rate % < Target − 4 pp"
  L3: "Compliance Rate % < Target − 6 pp or repeated breaches in same area"
  L3_note: "Applies only if trend persists >2 periods or in strategic segments."

Impact:
  category: Medium
  range: "+2 to +5 pp compliance"
  derivation: "Range based on historical benchmarks in relevant domain."
  mechanism:
    - "Address root causes of repeated breaches and enforce stronger controls."
  confidence: Medium

OperationalExecution:
  roles:
    - "Compliance Manager"
    - "Legal Lead"
  steps:
    - "Analyze incidents by category, root cause, and organization unit."
    - "Update or clarify policies and procedures."
    - "Roll out targeted training and awareness measures."
    - "Introduce additional controls or approvals where needed."
  effort: Medium
  risks:
    - "Training fatigue."
    - "Perceived bureaucracy."

DataRequirements:
  - "Incident and breach logs"
  - "Audit reports"
  - "Policy mapping to processes"

MaturityLevel: Basic

SuccessMeasurement:
  baseline: "Compliance rate and incident frequency baseline."
  kpi_30d: "Decline in new incidents in targeted categories."
  kpi_60d: "Sustained improvement in compliance rate."
  success_definition: "+2–5 pp compliance rate improvement in targeted scope."
```

## G-D1 – Data Quality & Integrity

```yaml
Code: G-D1.1
Name: Data Quality Improvement
Domain: Governance & Compliance
Primary KPI: Data Quality Score
Secondary KPIs: [Incident Count]

Trigger:
  type: Structural
  L1: "DQ Score < 92 %"
  L2: "DQ Score < 88 %"
  L3: "DQ Score < 85 % or data incidents rising"
  L3_note: "Applies only if trend persists >2 periods or in strategic segments."

Impact:
  category: Medium
  range: "+3 to +7 pp data quality"
  derivation: "Range based on historical benchmarks in relevant domain."
  mechanism:
    - "Fix structural data issues and strengthen validation rules and stewardship."
  confidence: Medium

OperationalExecution:
  roles:
    - "Data Governance Lead"
    - "Data Stewards"
  steps:
    - "Identify critical fields and domains with low data quality."
    - "Investigate root causes (source system, process, integration)."
    - "Define and implement data quality rules and remediation flows."
    - "Establish continuous monitoring and stewardship ownership."
  effort: Medium
  risks:
    - "Slower processes due to additional validations."

DataRequirements:
  - "DQ dashboards and metrics"
  - "Incident and defect logs"

MaturityLevel: Basic

SuccessMeasurement:
  baseline: "Data Quality Score and incident history."
  kpi_30d: "Early improvements in critical fields."
  kpi_60d: "Stable uplift in overall DQ score."
  success_definition: "+3–7 pp DQ score in critical domains."
```

## G-S1 – Security & Access Governance

```yaml
Code: G-S1.1
Name: Access Rights Optimization
Domain: Governance & Compliance
Primary KPI: Access Violations Count
Secondary KPIs: [Compliance Rate %]

Trigger:
  type: Structural
  L1: ">5 % of users with excessive permissions vs role matrix"
  L2: ">10 % of users with excessive permissions"
  L3: ">15 % or repeated high-severity access violations"
  L3_note: "Applies only if trend persists >2 periods or in strategic segments."

Impact:
  category: Medium
  range: "−20 to −50 % violations"
  derivation: "Range based on historical benchmarks in relevant domain."
  mechanism:
    - "Apply least privilege principles and clean up access rights."
  confidence: Medium

OperationalExecution:
  roles:
    - "Security Lead"
    - "IT Admin"
    - "Governance Manager"
  steps:
    - "Analyze current access vs role definitions."
    - "Identify users and groups with excessive permissions."
    - "Clean up rights and implement role-based access control."
    - "Introduce regular access review workflows."
  effort: Medium
  risks:
    - "Temporary access disruptions."
    - "User frustration if changes are not explained."

DataRequirements:
  - "Access logs"
  - "Role and permission model"
  - "Violation reports"

MaturityLevel: Advanced

SuccessMeasurement:
  baseline: "Access violation count and % of users with excessive rights."
  kpi_30d: "Reduction in violations and excessive rights."
  kpi_60d: "Stability and no major new violations."
  success_definition: "−20–50 % violations with maintained productivity."
```
# Innovation & People Action Codes

## IP-E1 – Employee Engagement

```yaml
Code: IP-E1.1
Name: Engagement Pulse Intervention
Domain: Innovation & People
Primary KPI: Engagement Score
Secondary KPIs: [Turnover %, Productivity Index]

Trigger:
  type: Pattern
  L1: "Engagement Score < Target − 3 pts"
  L2: "Engagement Score < Target − 5 pts"
  L3: "Engagement Score < Target − 7 pts or rising voluntary turnover"
  L3_note: "Applies only if trend persists >2 periods or in strategic segments."

Impact:
  category: Medium
  range: "+2 to +6 pts engagement"
  derivation: "Range based on historical benchmarks in relevant domain."
  mechanism:
    - "Resolve main engagement blockers (leadership, workload, clarity, recognition)."
  confidence: Medium

OperationalExecution:
  roles:
    - "HR Business Partner"
    - "Team Leads"
  steps:
    - "Analyze engagement survey results and drivers by team."
    - "Prioritize top 2–3 themes per unit."
    - "Define and implement concrete actions (e.g., feedback rituals, workload rebalancing)."
    - "Conduct a pulse survey after 30–60 days."
  effort: Medium
  risks:
    - "Low adoption by managers."
    - "Cynicism if actions are only symbolic."

DataRequirements:
  - "Engagement survey and driver breakdown"
  - "Turnover data"

MaturityLevel: Basic

SuccessMeasurement:
  baseline: "Engagement baseline vs target and benchmark."
  kpi_30d: "Pulse check uplift on targeted drivers."
  kpi_60d: "Sustained improvement in overall Engagement Score."
  success_definition: "+2–6 pts engagement in affected teams."
```

## IP-T1 – Training & Skill Development

```yaml
Code: IP-T1.1
Name: Targeted Skill Development Plan
Domain: Innovation & People
Primary KPI: Training Hours per FTE
Secondary KPIs: [Productivity Index]

Trigger:
  type: Structural
  L1: "Training hours < target − 10 %"
  L2: "Training hours < target − 20 %"
  L3: "Training hours < target − 30 % or visible performance gaps"
  L3_note: "Applies only if trend persists >2 periods or in strategic segments."

Impact:
  category: Medium
  range: "+5 to +15 % training hours"
  derivation: "Range based on historical benchmarks in relevant domain."
  mechanism:
    - "Establish structured individual learning plans and mandatory training cadence."
  confidence: Medium

OperationalExecution:
  roles:
    - "L&D Lead"
    - "Team Leads"
  steps:
    - "Identify key roles with skill gaps."
    - "Map required competencies vs current skill levels."
    - "Define training paths and content (internal, external, on-the-job)."
    - "Track completion and simple performance indicators."
  effort: Medium
  risks:
    - "Operational downtime."
    - "Low completion if not supported by managers."

DataRequirements:
  - "Training logs"
  - "Skill matrix or competency profiles"

MaturityLevel: Basic

SuccessMeasurement:
  baseline: "Training hours per FTE and skills coverage."
  kpi_30d: "Increase in completed relevant training."
  kpi_60d: "Initial improvements in performance proxies (error rate, throughput, quality)."
  success_definition: "+5–15 % training hours in targeted groups with visible skill uplift."
```

## IP-I1 – Innovation Adoption

```yaml
Code: IP-I1.1
Name: Digital Adoption Enhancement
Domain: Innovation & People
Primary KPI: Digital Adoption Rate %
Secondary KPIs: [Productivity Index]

Trigger:
  type: Pattern
  L1: "Adoption < Target − 5 pp"
  L2: "Adoption < Target − 10 pp"
  L3: "Adoption < Target − 15 pp or rising manual work share"
  L3_note: "Applies only if trend persists >2 periods or in strategic segments."

Impact:
  category: Medium
  range: "+5 to +12 pp adoption"
  derivation: "Range based on historical benchmarks in relevant domain."
  mechanism:
    - "Combine training, UX simplification, and nudges to increase usage of digital tools."
  confidence: Medium

OperationalExecution:
  roles:
    - "Digital Transformation Lead"
    - "HR Business Partner"
  steps:
    - "Identify teams and processes with low tool adoption."
    - "Collect feedback on blockers (UX, performance, fit)."
    - "Deploy focused training and in-app guidance."
    - "Simplify workflows or adjust tools where needed."
    - "Track adoption weekly by team and role."
  effort: Medium
  risks:
    - "Shadow systems if tools remain misaligned."
    - "Change fatigue."

DataRequirements:
  - "Usage logs per tool and role"
  - "Manual work proxies (e.g., offline spreadsheets)"

MaturityLevel: Advanced

SuccessMeasurement:
  baseline: "Digital adoption rate by team and role."
  kpi_30d: "Uplift in adoption for focus groups."
  kpi_60d: "Stabilized adoption at higher level."
  success_definition: "+5–12 pp adoption in target teams with productivity gains."
```
