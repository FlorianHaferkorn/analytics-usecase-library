# Reporting Strategy

---

## 1. Purpose & Vision

The **Reporting Strategy** defines how analytics and reporting align with corporate goals.  
Every report must connect **data to decision** and **insight to impact**.

> “A report is only valuable if it changes a business outcome.”

---

## 2. Reporting Layers Overview (Layer Axis)

We distinguish three reporting levels – this is the **Layer Axis** and wird im FactSheet als `reporting_level` gepflegt.

| Level          | Purpose                                                | Example Use Case                                                |
|----------------|--------------------------------------------------------|-----------------------------------------------------------------|
| **Strategic**  | Measures company performance against long-term goals   | XD-003 Executive KPI Overview                                   |
| **Tactical**   | Analyzes drivers and accountability for KPIs           | COM-001 Sales Performance, COM-002                              |
| **Operational**| Supports daily execution and monitoring                | FIN-001 Cash & Liquidity Performance, OPS-002 Asset Performance |

Each layer builds on the previous one. Tactical reports explain _why_ strategic KPIs move, and operational reports show _how_ execution delivers the result.

In the Use Case FactSheet:

- `reporting_level: Strategic` — board/management view on Strategic KPIs.  
- `reporting_level: Tactical` — cluster/segment view explaining KPI movements.  
- `reporting_level: Operational` — process/line-level view for daily execution.

---

## 3. Analytics Stages (Analytics Axis)

Orthogonal to the reporting levels we distinguish **analytics stages**. These are captured in the FactSheet as `analytics_stage`.

| Stage           | Question Type                  | Examples in this library                                                    |
|-----------------|--------------------------------|-----------------------------------------------------------------------------|
| **Descriptive** | What happened?                 | COM-001 Sales Performance, FIN-001 Cash & Liquidity Performance             |
| **Diagnostic**  | Why did it happen?             | COM-002 Gross Margin Analysis, COM-004 PVM                                  |
| **Predictive**  | What is likely to happen?      | COM-003 Customer Value, SCM-003 Forecast vs Actual                          |
| **Prescriptive**| What should we do next?        | SCM-001 Inventory Performance (target policy)                               |

Guidance for FactSheets:

- Start with `analytics_stage: Descriptive` or `Diagnostic` for most use cases.  
- Use `Predictive` / `Prescriptive` intentionally when models/optimization are truly in scope.  
- Auch ein strategischer Use Case kann „nur“ descriptive sein – und umgekehrt kann ein operativer Use Case prescriptive Logik enthalten.

---

## 4. Framework Principles

| Principle       | Description                                                   |
|-----------------|---------------------------------------------------------------|
| **Consistency** | KPIs and calculations remain identical across layers.         |
| **Context**     | Every report starts from a defined business question.         |
| **Clarity**     | 3–30–300 design ensures intuitive user flow and readability.  |
| **Governance**  | RLS/OLS, lineage, and review cycles ensure trust and control. |
| **Reusability** | Standardized templates accelerate time-to-insight.            |

---

## 5. Strategic Alignment Framework

### 4.1 Purpose

To link corporate objectives, analytical Use Cases, and operational actions into one continuous logic.

```yaml
Strategic KPI → Business Driver → Use Case → Action Code → Business Impact
```

### 4.2 Layer Definition

| Layer                   | Key Question               | Example                                                         |
|-------------------------|----------------------------|-----------------------------------------------------------------|
| **Strategic KPI**       | What do we aim to achieve? | Revenue Growth %                                                |
| **Business Driver**     | What influences it?        | Volume Growth %, DSO, Price Realization %                       |
| **Analytical Use Case** | Where can analytics help?  | COM-001 Sales Performance, FIN-001 Cash & Liquidity Performance |
| **Action Code**         | What should be done?       | P2 Tighten Discounts, W1 Accelerate Collections                 |
| **Impact**              | What will change?          | +3–5 pp Revenue Growth %, −5 days DSO                           |

### 4.3 Outcome for Analytics Teams

- Each Use Case must reference **at least one Strategic KPI**.  
- Each Use Case must quantify its **expected business impact**.  
- This linkage is maintained in `/_includes/Strategic_Alignment_Map.md`.

---

## 6. Governance & Review Model

| Role                 | Responsibility                               |
|----------------------|----------------------------------------------|
| **Business Owner**   | Defines KPI meaning and thresholds.          |
| **Data Owner**       | Guarantees data quality and lineage.         |
| **Steward**          | Maintains the KPI and ensures QA compliance. |
| **Governance Board** | Reviews, approves, and archives KPIs.        |

**Review Frequency:** Quarterly or after each fiscal cycle.  
**Quality Gate:** IR ≥ 99.9 %, Copilot-ready metadata, lineage verified.

---

## 7. Summary & Next Steps

- Maintain the **Strategic Alignment Map** as a living document.  
- Validate quarterly that each analytics initiative supports at least one strategic KPI.  
- Use the same logic in dashboards, performance reviews, and AI Copilot prompts.

> “When business goals, KPIs, and analytics move together, the organization learns faster.”
