# Decision Taxonomy

## 1. Purpose

This document defines **decision types** that describe *how* analytics supports decisions, not only *what* is reported. Use cases and action codes can be tagged with these types to clarify intent, improve prioritization, and support UX (e.g. 3-30-300 layers or conversational AI).

Decision types are **conceptual** and tool-agnostic.

---

## 2. Decision Types

| Type | Description | Typical use case focus | Example key question |
|------|-------------|------------------------|----------------------|
| **Steer** | Set or adjust direction; monitor whether we are on track. | Executive views; strategic KPIs; high-level performance vs plan. | Are we on track? Where do we need to intervene? |
| **Diagnose** | Explain why a KPI or outcome changed; identify drivers and root causes. | Most tactical use cases (sales, margin, OEE, inventory, etc.). | Why did margin drop? What drove the gap? |
| **Allocate** | Decide where to assign resources (capacity, spend, people, inventory). | Resource utilization; capacity planning; inventory allocation; marketing/customer spend. | Where should we allocate capacity or budget? |
| **Forecast** | Use past and leading indicators to anticipate outcomes or risks. | Forecast vs actual; cash and liquidity; churn/CLV; demand planning. | What will happen if we do nothing? Where is risk? |
| **Intervene** | Choose and execute a concrete action (pricing, maintenance, replenishment, escalation). | All use cases linked to action codes; prescriptive execution. | Which action do we take, when, and with what guardrails? |

---

## 3. Mapping: Use Cases to Decision Types

A use case often supports **multiple** decision types; the table below shows the **primary** and **secondary** types per use case.

| Use Case ID | Primary | Secondary | Notes |
|-------------|---------|-----------|-------|
| COM-001 | Diagnose | Steer, Intervene | Explain sales gap; steer via plan/LY; intervene via action codes |
| COM-002 | Diagnose | Intervene | Explain margin leakage; intervene on price/mix/cost |
| COM-003 | Diagnose | Allocate, Forecast | CLV and churn; allocate retention/upsell; forecast at-risk revenue |
| COM-004 | Diagnose | Intervene | Explain promo ROI; intervene on promo mechanics |
| FIN-001 | Steer, Diagnose | Forecast | Cash position; diagnose CCC drivers; forecast liquidity |
| FIN-002 | Diagnose | Intervene | Explain cost variance; intervene on cost levers |
| OPS-001 | Diagnose | Intervene | Explain OEE; intervene on availability/performance/quality |
| OPS-002 | Diagnose | Intervene | Explain downtime; intervene on PM and reliability |
| OPS-003 | Diagnose | Intervene | Explain yield/COPQ; intervene on defects |
| SCM-001 | Diagnose | Allocate, Intervene | Explain DIO/stockout; allocate inventory; intervene on levers |
| SCM-002 | Diagnose | Intervene | Explain OTIF; intervene on delivery and service |
| SCM-003 | Diagnose | Forecast, Intervene | Explain forecast error; forecast impact; intervene on planning |
| XD-001 | Diagnose | Intervene | Explain SLA/FCR/backlog; intervene on service levers |
| XD-002 | Diagnose | Allocate | Explain utilization; allocate capacity across queues |
| XD-003 | Steer | Diagnose | Enterprise steering; diagnose cross-domain risk |

---

## 4. Mapping: Action Codes to Decision Types

Action codes are **Intervene** by definition (they prescribe what to do when triggers fire). The taxonomy still helps by grouping action code *themes*:

| Pattern / theme | Decision type | Example action code groups |
|-----------------|---------------|----------------------------|
| Governance / orchestration | Intervene (coordinate) | Inventory Governance, Service Governance, Liquidity Steering, Reliability Governance |
| Control / containment | Intervene (correct) | Price Realization Guardrails, Receivables Control, Availability Control, Defect Control |
| Allocate / rebalance | Allocate | Capacity Allocation Control, Portfolio & Mix Steering |
| Escalate / route | Intervene | Enterprise Risk Steering, Executive Accountability |

Use case metadata can optionally include `decision_type: [Diagnose, Intervene]` etc.; action codes are implicitly Intervene with the sub-themes above.

---

## 5. Relationship to Other Artifacts

- **Use Case Inventory:** Key Questions and purpose already reflect decision intent; this taxonomy makes it explicit.
- **3-30-300:** Steer often maps to 3-second layer; Diagnose to 30-second; Intervene and detail to 300-second.
- **Golden Thread:** Key Questions → Use Cases → Actions; decision types tag the use case layer for clarity.
- **Optional:** Add `decision_type` to Business Factsheet template and schema if tooling or AI should filter by type.
