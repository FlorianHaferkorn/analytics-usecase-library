# Action-Ready Semantic Layer

## 1. Role in the Operating Model

The **semantic layer** is the central contract between:
- business intent (strategic KPIs, domains, use cases) and  
- technical implementation (data contracts, models, measures, reports).

This document defines the **conceptual blueprint** for the ActionReady semantic model and how it is implemented in tools such as Microsoft Fabric / Power BI using TMDL/PBIP.

It answers:
- Which tables and grains are required?
- How do Action Codes connect to KPIs and facts?
- Which patterns must every domain follow?

---

## 2. Core Principles

Every ActionReady semantic model must follow these principles:

1. **Star Schema First**  
   - Facts at clearly defined business grains  
   - Shared, conformed dimensions across domains  

2. **Stable Domain Aggregates**  
   - Domain facts modeled at repeatable, auditable grains (e.g. product_customer_week).  

3. **Action-Specific Aggregates**  
   - Separate aggregation tables for Action Codes (leakage, root causes, uplift, etc.).  

4. **Action Execution Tracking**  
   - Dedicated fact table tracking which actions were executed, by whom, and with what effect.  

5. **Measure-Driven (Not Column-Driven)**  
   - Business logic is implemented as measures (see `measure_system.md`), not as calculated columns.  

6. **AI-Ready Metadata**  
   - Tables, columns, and measures must carry descriptions suitable for Copilot/AI usage.  

---

## 3. Domain Data Aggregates (Example Blueprint)

This section shows a **conceptual YAML blueprint** for domain aggregates.  
Each implementation can extend this pattern, but the structure should remain consistent.

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

This pattern should be adapted per domain (Sales, Margin, Inventory, SCM, ESG, …) but follow the same logic:
- clear grain,
- clear key references to dimensions,
- measures separated from structure via the measure system.

---

## 4. Action Aggregates

ActionReady models introduce **action-centric aggregates** aligned with Action Codes.  
These tables are used to flag where interventions are needed and quantify impact potential.

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

Flags (L1/L2/L3) are linked to Action Codes and drive:
- alerting,
- root cause analysis,
- and recommended next-best-actions.

---

## 5. Action Execution Layer

The **Action Execution Layer** closes the loop between analytics and realized business actions.

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

This table allows:
- measuring action effectiveness,
- attributing impact to Action Codes,
- and learning which interventions work best.

---

## 6. End-to-End Semantic Model Pattern

At a high level, the ActionReady model can be illustrated as:

```text
dim_product ----
                \
dim_customer ---- fact_pricing_agg ---- agg_price_leakage ---- fact_action_execution
                //
dim_date -------
```

Across domains, the same pattern applies:
- shared dimensions,
- domain fact tables,
- action aggregates,
- and one shared action execution fact.

---

## 7. TMDL Standards & Allowed Subset

The conceptual model above is implemented in Microsoft Fabric / Power BI using **PBIP + TMDL**.

Two companion documents define the **technical constraints**:

- `tmdl_allowed_subset.md`  
  → defines the allowed TMDL subset (naming, data types, RLS, descriptions, object types).  

- `tmdl_official_refs.md`  
  → links to the official Microsoft documentation and references for TMDL/PBIP.

**Location:**
- `docs/operating_model/tmdl_allowed_subset.md`
- `docs/operating_model/tmdl_official_refs.md`

The semantic layer must always comply with these constraints.

---

## 8. Governance & Linters

To enforce semantic standards, internal linting & BPA rules are maintained under:

```text
_internal/tools/linters/
  lint.rules.yaml
  bpa-rules-dax.json
  bpa-rules-report.json
  bpa-rules-semanticmodel.json
```

These configurations support:
- measure naming & foldering validation,
- description & metadata checks,
- report layout best practices,
- semantic model integrity rules.

They are **internal-only** and not exposed to customers, but all customer models should pass these checks before being considered production-ready.

---

## 9. How to Use This Blueprint

### For Domain Semantic Models
- Start from this pattern when designing `semantic_models/domains/<domain>/…`.
- Reuse:
  - shared dimensions (dim_date, dim_org, dim_product, dim_customer, …),
  - action aggregates where relevant,
  - the action execution layer when Action Codes are in scope.

### For New Customers
- Map customer data contracts to this semantic pattern.
- Implement the model in PBIP/TMDL under the constraints from `tmdl_allowed_subset.md`.
- Use BPA/lint rules from `_internal/tools/linters` to validate quality.

### For the Aurora Group Showcase
- The Aurora semantic model is a **concrete realization** of this blueprint:
  - see `showcases/aurora_group/semantic_model/`.

---

**Location:**  
`docs/operating_model/semantic_layer.md`

