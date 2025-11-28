# Action-Ready Semantic Model – Full Blueprint

Purpose:
- Reference blueprint for the ActionReady Semantic Model used by downstream semantic_models.
- Defines mandatory layers, aggregates, grains, and relationships required to operationalize Action Codes and AI-ready analytics.

Core Principles:
- Stable domain aggregates at clear business grains.
- Action-specific aggregates for triggers and root causes.
- Action execution tracking to measure impact.
- AI-ready star schema with governed metadata.

Domain Data Aggregates (conceptual YAML):
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

Action Aggregates (examples):
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

Action Execution Layer:
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

Pattern (illustrative):
```
dim_product ----
                 dim_customer ----- fact_pricing_agg ---- agg_price_leakage ---- fact_action_execution
                 //
dim_date --------
```

Notes for implementation:
- Measures follow framework naming/formatting; dimensions are conformed across domains.
- Action aggregates support multi-level triggers (L1–L3); execution layer supports before/after (7/30/60d).
- Align to semantic layer standards and lint rules (`_internal/tools/linters`).
