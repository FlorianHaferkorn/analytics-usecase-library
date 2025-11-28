# Company Layer (WHY)

## Purpose
Provide the strategic foundation of the **ActionReady Analytics Framework** by capturing business context, domains, strategic KPIs, and key questions that guide all downstream analytics, semantic design, and use case development.

This layer ensures that the framework is always anchored in real business value — not technology.

---

## Scope
What belongs here:
- Company strategy, business model, and value creation logic  
- Domain definitions and operating model context  
- Strategic KPIs and their business relevance  
- Key questions that analytics must answer  
- Reporting design principles tailored to the company  

What does **not** belong here:
- Technical semantic layer details  
- Data contracts or pipelines  
- Visual page templates  
- Tool-specific implementation guidance  

---

## Structure

```
company/
  business_strategy.md        → Strategic direction, value chain, business priorities
  domains.md                  → Domain catalog (Finance, Sales, SCM, ESG…)
  strategic_kpis.md           → Top-level KPIs mapped to strategy
  key_questions.md            → High-value questions that drive use cases
  reporting_design_principles.md → Company-specific design & reporting standards
```

### business_strategy.md  
Defines the business context, strategic goals, value chain, and decision-making structure.

### domains.md  
Lists the functional/business domains, their responsibilities, and analytical boundaries.

### strategic_kpis.md  
Defines which KPIs matter most, how they align with strategy, and how they interact across domains.

### key_questions.md  
Frames the analytical scope via core business questions — the precursor to use case definition.

### reporting_design_principles.md  
Captures customer-specific design philosophy, branding constraints, and UI expectations.

---

## Usage

- **For customers:**  
  - Understand how analytics ties directly to strategy.  
  - Validate KPIs and domain ownership.  
  - Establish reporting & design expectations early.

- **For delivery teams:**  
  - Ensure all models, measures, and use cases are anchored in real business needs.  
  - Use domains to structure data contracts and semantic models.  
  - Derive use case prioritization and KPI governance.

- **For framework evolution:**  
  - Extendable per customer without changing the entire framework.  
  - Reusable across industries with minimal changes.

---

## Relations

- **WHY**  
  This folder defines everything that motivates analytics: goals, questions, KPIs, decision paths.

- **HOW** (Operating Model)  
  Semantic layer, measure system, UX standards, and operational processes depend directly on the strategic clarity defined here.

- **WITH WHAT** (Framework Standards)  
  KPI Catalogs, Action Codes, Glossaries, and Templates derive from domains and strategic KPIs.

- **TEMPLATES** (Use Case Patterns)  
  Business Factsheets and Use Case Blueprints rely on the key questions and domain structure defined in the Company Layer.

---

## Next Step
Start with:  
- `business_strategy.md`  
- `strategic_kpis.md`  
- `key_questions.md`  

These three documents together form the strategic backbone of the ActionReady Analytics Framework.

---

**Location to place this file:**  
`docs/company/README.md`
