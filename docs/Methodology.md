# Methodology & Rationale
_Version 2.0 | Last updated: 12.10.2025_

---

## 1. Purpose & Scope
This methodology ensures all analytics follow a **consistent, traceable, and business-aligned** approach.  
It defines *how* insights are built, standardized, and mapped to strategic impact.

---

## 2. Standardization Philosophy

| Principle | Description |
|------------|-------------|
| **One language** | Shared KPIs and naming conventions across all domains. |
| **Separation of concerns** | Business logic in Markdown, implementation in model. |
| **Reuse over reinvent** | Conformed dimensions and shared measures first. |
| **Documentation-first** | Every use case can stand alone and be reused. |

**Outcome:** Faster onboarding, fewer errors, and AI/Copilot readiness.

---

## 3. Core Design Principles

### 3.1 3–30–300 Communication
- **3s:** 4–5 KPI cards with deltas (the “story headline”).  
- **30s:** Trends, rankings, and bridges (why it changed).  
- **300s:** Drill tables, details, correlations (how to act).

### 3.2 Semantic Modeling 101
- Star schema structure, clear fact–dimension separation.  
- Measures > calculated columns, use display folders by domain.  
- Referential integrity ≥ 99.9 %, RLS/OLS on dimensions only.

### 3.3 Naming & Formatting Standards
| Type | Convention | Example |
|------|-------------|----------|
| Currency | Ends with `Amount` | Net Sales Amount |
| Quantity | Ends with `Qty` | Units Qty |
| Variance | Starts with `Δ` | Δ Net Sales Amount |
| Variance % | Starts with `Δ%` | Δ% Gross Margin |
| Percentages | End with `%` | Gross Margin % |

---

## 4. KPI Lifecycle

```
Define -> Document -> Validate -> Map -> Improve
```

| Stage | Objective | Example Output |
|--------|------------|----------------|
| Define | Agree on metric meaning | Gross Margin % |
| Document | Add to KPI Catalog | YAML entry with lineage |
| Validate | Verify logic & QA rules | Range [−100%; +100%] |
| Map | Link to Use Case & Action | COM-002 Gross Margin |
| Improve | Reassess impact quarterly | Changelog entry |

---

## 5. Mapping Use Cases to Strategic KPIs

### 5.1 Purpose
Ensure every analysis directly supports a measurable business objective.

```
Strategic KPI -> Supporting KPI -> Use Case -> Action Code -> Impact
```

### 5.2 Step-by-Step Mapping

| Step | Guiding Question | Output |
|------|-------------------|--------|
| 1 | Which business goal? | Strategic KPI |
| 2 | What drives it? | Supporting KPI |
| 3 | Which analysis explains it? | Use Case |
| 4 | How to act? | Action Code |
| 5 | What improves? | Expected Impact |

### 5.3 Example Mapping

| Strategic KPI | Supporting KPI | Use Case | Action Codes | Expected Impact |
|----------------|----------------|-----------|----------------|----------------|
| **Revenue Growth %** | Volume Growth %, Price Realization % | COM-001 Sales Performance, COM-004 Price Realization | P1, P2 | +3–5 pp Revenue Growth % |
| **Working Capital %** | DSO, DPO, Inventory Days | COR-001 Working Capital | W1, I1 | −5 days CCC |
| **Gross Margin %** | Price Discount %, COGS Amount | COM-002 Gross Margin | P2, PC2 | +0.5–1 pp GM % |

### 5.4 Expected Outcome for Analytics Teams
Each Use Case must include the following fields:

```yaml
supports_strategic_kpi: [Revenue Growth %, Gross Margin %]
expected_impact: "+2–3 pp Revenue Growth %, +0.5 pp Gross Margin %"
```

---

## 6. Governance & Continuous Improvement

| Process | Description |
|----------|--------------|
| **Review Workflow** | Each UC reviewed by Business & Data reviewer. |
| **Definition of Done** | All fields filled, naming correct, cross-references valid. |
| **Versioning** | Major for KPI changes, minor for text updates. |

**Goal:** Continuous learning loop between analytics and business execution.

---

## 7. Summary

One consistent chain ensures business impact:

```
Metric -> Meaning -> Action -> Impact
```

> **Key takeaway:** Every Use Case must explain not just *what happened*, but *why* and *what to do next*.





