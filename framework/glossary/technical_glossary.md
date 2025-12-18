# Technical Glossary

## Purpose

This glossary defines a **minimal, standardized technical vocabulary** used across the
Analytics Use Case Library.

It ensures:
- consistent semantic modeling
- unambiguous metadata for AI / Copilot
- shared understanding between analytics and data teams

This glossary is a **reference**, not a modeling guide.

---

## Core Technical Concepts

### Semantic Model
A governed analytical layer defining relationships, measures, hierarchies, and metadata.  
It is the **single analytical interface** for reporting and decision-making.

---

### Fact Table
A table storing **measurable data** at a defined grain (e.g. sales transactions, journal lines).

---

### Dimension Table
A table storing **descriptive attributes** used to analyze facts  
(e.g. Date, Organization, Product, Customer).

---

### Grain
The **lowest level of detail** at which data is stored and measures are evaluated  
(e.g. invoice line, daily snapshot).

---

### Star Schema
A data modeling pattern where fact tables are surrounded by conformed dimension tables.  
Used for clarity, performance, and scalability.

---

### Conformed Dimension
A shared dimension reused consistently across multiple fact tables and domains  
(e.g. Date, Organization, Product).

---

### Measure
A reusable calculation (e.g. DAX) returning a single aggregated value.  
Measures implement all business logic; calculated columns are avoided.

---

### KPI ID
A **stable, unique identifier** for a KPI using dot notation  
(e.g. `sales.net_sales.amount`).

KPI IDs are used across:
- KPI Catalogs
- Semantic Models
- Use Cases
- Action Codes
- AI prompts

---

### Data Contract
A governed specification defining:
- facts and dimensions
- grain
- keys
- units
- lineage
- quality expectations

Data Contracts define **what data must look like**, not how it is processed.

---

### Referential Integrity (RI)
The degree to which fact table keys correctly match corresponding dimension keys.

---

### QA Rule
A defined validation rule ensuring data or measure correctness  
(e.g. allowed value ranges, logical consistency).

---

### Action Code
A standardized, coded description of a **prescriptive business action** linked to KPI behavior.  
Action Codes operationalize prescriptive analytics.

---

### Trigger Level (L1–L3)
Classification of Action Code activation:
- **L1** – early warning  
- **L2** – intervention required  
- **L3** – execution required  

---

### Action Aggregate
A fact-like structure summarizing KPI deviations, triggers, or root causes  
used to activate Action Codes.

---

### Row-Level Security (RLS)
A security mechanism restricting data access at row level based on user context.

---

### Object-Level Security (OLS)
A security mechanism controlling visibility of tables, columns, or measures.

---

## Usage Rules

- Definitions must be **domain-independent**
- One term = one meaning
- No implementation instructions
- No repetition of Operating Model rules
- New terms are added only if reused across domains

---

**Location:**  
`framework/glossary/technical_glossary.md`
