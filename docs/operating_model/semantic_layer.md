Status: Draft (Internal)
Purpose: Reference blueprint for the Action-Ready Semantic Model used by all downstream semantic_models.

# Action-Ready Semantic Model (Full Blueprint)
This document provides the reference blueprint for an Action-Ready Semantic Model. It defines the mandatory layers, aggregates, data grains and relationships required to operationalize Action Codes across all domains. The blueprint serves as architectural guidance for building scalable, AI-ready semantic models in Microsoft Fabric and Power BI, ensuring that KPI deviations can trigger actionable, data-driven interventions with measurable impact.

## 1. Principles
- Stable domain aggregates
- Action-specific aggregates
- Action execution tracking
- AI-ready star schema

## 2. Domain Data Aggregates
```yaml
dimension:
  - name: dim_date
    columns:
      - {name: DateKey, type: date_key, role: key}
      - {name: Date, type: date}
      - {name: Week, type: int}
      - {name: Month, type: text}
      - {name: Year, type: int}

  - name: dim_product
    columns:
      - {name: ProductKey, type: int, role: key}
      - {name: ProductName, type: text}
      - {name: Category, type: text}

  - name: dim_customer
    columns:
      - {name: CustomerKey, type: int, role: key}
      - {name: Segment, type: text}
      - {name: ChurnRiskLevel, type: text}

fact:
  - name: fact_pricing_agg
    grain: product_customer_week
    columns:
      - {name: Price Realization %, type: number}
      - {name: Gross Margin %, type: number}
      - {name: Actual Price, type: number}
      - {name: List Price, type: number}
      - {name: Discount %, type: number}
```

## 3. Action Aggregates
```yaml
fact:
  - name: agg_price_leakage
    grain: product_customer_week
    columns:
      - {name: Leakage %, type: number}
      - {name: Margin Loss Amount, type: currency}
      - {name: Target Price, type: number}
      - {name: Required Correction %, type: number}
      - {name: L1_Flag, type: boolean}
      - {name: L2_Flag, type: boolean}
      - {name: L3_Flag, type: boolean}

  - name: agg_downtime_rootcause
    grain: asset_day
    columns:
      - {name: Failure Count, type: int}
      - {name: Failure Duration Min, type: int}
      - {name: OEE Loss %, type: number}
      - {name: Primary Root Cause, type: text}
      - {name: L1_Flag, type: boolean}
      - {name: L2_Flag, type: boolean}
      - {name: L3_Flag, type: boolean}
```

## 4. Action Execution Layer
```yaml
fact:
  - name: fact_action_execution
    grain: action_event
    columns:
      - {name: ActionExecutionKey, type: int, role: key}
      - {name: ActionCode, type: text}
      - {name: TriggerLevel, type: text}
      - {name: ExecutedByUser, type: text}
      - {name: ExecutedDate, type: date}
      - {name: Domain, type: text}
      - {name: Pre_KPI_Value, type: number}
      - {name: Post_KPI_Value_7d, type: number}
      - {name: Post_KPI_Value_30d, type: number}
      - {name: Post_KPI_Value_60d, type: number}
      - {name: Action Success %, type: number}
      - {name: Notes, type: text}
```

## 5. Semantic Model Blueprint
```
dim_product ----
                 \
dim_customer ----- fact_pricing_agg ---- agg_price_leakage ---- fact_action_execution
                 //
dim_date --------
```

