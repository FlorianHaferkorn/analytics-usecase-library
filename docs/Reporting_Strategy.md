# Reporting Strategy
_Version 2.0 | Last updated: 12.10.2025_

---

## 1. Purpose & Vision
The **Reporting Strategy** defines how analytics and reporting align with corporate goals.  
Every report must connect **data to decision** and **insight to impact**.

> “A report is only valuable if it changes a business outcome.”

---

## 2. Reporting Layers Overview

| Level | Purpose | Example Use Case |
|--------|----------|------------------|
| **Strategic** | Measures company performance against long-term goals | COR-001 Working Capital |
| **Tactical** | Analyzes business drivers and accountability areas | COM-002 Gross Margin |
| **Operational** | Supports daily execution and monitoring | OPS-001 OEE |

Each layer builds on the previous one. Tactical reports explain *why* strategic KPIs move, and operational reports show *how* execution delivers the result.

---

## 3. Framework Principles

| Principle | Description |
|------------|--------------|
| **Consistency** | KPIs and calculations remain identical across layers. |
| **Context** | Every report starts from a defined business question. |
| **Clarity** | 3–30–300 design ensures intuitive user flow and readability. |
| **Governance** | RLS/OLS, lineage, and review cycles ensure trust and control. |
| **Reusability** | Standardized templates accelerate time-to-insight. |

---

## 4. Strategic Alignment Framework

### 4.1 Purpose
To link corporate objectives, analytical Use Cases, and operational actions into one continuous logic.

```
Strategic KPI → Business Driver → Use Case → Action Code → Business Impact
```

### 4.2 Layer Definition

| Layer | Key Question | Example |
|--------|---------------|----------|
| **Strategic KPI** | What do we aim to achieve? | Revenue Growth % |
| **Business Driver** | What influences it? | Volume Growth %, DSO, Price Realization % |
| **Analytical Use Case** | Where can analytics help? | COM-001 Sales Performance, COR-001 Working Capital |
| **Action Code** | What should be done? | P2 Tighten Discounts, W1 Accelerate Collections |
| **Impact** | What will change? | +3–5 pp Revenue Growth %, −5 days DSO |

### 4.3 Outcome for Analytics Teams
- Each Use Case must reference **at least one Strategic KPI**.  
- Each Use Case must quantify its **expected business impact**.  
- This linkage is maintained in `/_includes/Strategic_Alignment_Map.md`.

---

## 5. Governance & Review Model

| Role | Responsibility |
|------|----------------|
| **Business Owner** | Defines KPI meaning and thresholds. |
| **Data Owner** | Guarantees data quality and lineage. |
| **Steward** | Maintains the KPI and ensures QA compliance. |
| **Governance Board** | Reviews, approves, and archives KPIs. |

**Review Frequency:** Quarterly or after each fiscal cycle.  
**Quality Gate:** IR ≥ 99.9 %, Copilot-ready metadata, lineage verified.

---

## 6. Summary & Next Steps

- Maintain the **Strategic Alignment Map** as a living document.  
- Validate quarterly that each analytics initiative supports at least one strategic KPI.  
- Use the same logic in dashboards, performance reviews, and AI Copilot prompts.

> “When business goals, KPIs, and analytics move together, the organization learns faster.”



