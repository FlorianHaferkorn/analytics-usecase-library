# Glossary

This glossary defines standardized business, analytical, and governance terminology used across the **Analytics Use Case Library**.  
It ensures semantic consistency between business, data, and AI-driven documentation.

---

## 1. Purpose
The glossary provides:
- Shared definitions for KPIs, attributes, and governance concepts.
- A consistent semantic foundation across clusters and use cases.
- Clear linkage between strategic dimensions, metrics, and business outcomes.

---

## 2. Strategic KPI Dimensions
Core impact dimensions used to classify all strategic KPIs and Use Cases.

| Dimension | Definition | Typical KPIs |
|------------|-------------|---------------|
| **Growth** | Measures expansion in revenue, volume, and market share. | Revenue Growth %, Volume Growth %, Market Share % |
| **Profitability** | Measures the company’s ability to generate profit from revenue. | Gross Margin %, EBITDA Margin %, Net Profit Margin % |
| **Liquidity** | Measures cash generation and working capital efficiency. | Working Capital %, DSO, DPO, Free Cash Flow |
| **Efficiency** | Measures process performance, cost, and productivity. | OEE, Cost per Unit, Labor Productivity % |
| **Customer Value** | Measures loyalty, satisfaction, and customer lifetime revenue. | Retention %, CLV, NPS Score |
| **ESG** | Measures environmental and social responsibility. | Carbon Intensity, Energy Efficiency %, Sustainability Score |
| **Governance & Compliance** | Measures data integrity, risk control, and transparency. | Data Quality %, Compliance Breach Count |
| **Innovation & People** | Measures transformation capacity, digital maturity, and engagement. | Innovation Index, Digital Adoption %, Engagement Score |

> Each Use Case and KPI references exactly one **Impact Dimension** to maintain alignment between strategy and analytics.

---

## 3. Reporting & Analytics Terms

| Term | Definition |
|------|-------------|
| **Use Case** | A standardized, documented business question answered through data analysis. |
| **Cluster** | A logical grouping of Use Cases under one functional domain (e.g., Commercial, Operational Efficiency). |
| **KPI (Key Performance Indicator)** | Quantitative metric used to measure progress toward a business objective. |
| **Strategic KPI** | Top-level indicator directly linked to business strategy and long-term goals. |
| **Tactical KPI** | Mid-level measure used for department or function control. |
| **Operational KPI** | Day-to-day performance measure supporting process-level optimization. |
| **3-30-300 Principle** | Report design rule: 3 seconds (overview), 30 seconds (story), 300 seconds (detail). |
| **Variance Analysis** | Technique to explain deviations from Plan or LY (Δ, Δ%, Mix, Price, Volume). |
| **Semantic Model** | Logical layer in Power BI defining relationships, measures, and hierarchies. |
| **Star Schema** | Modeling approach with fact tables and conformed dimensions for clarity and performance. |
| **Fact Table** | Table storing measurable transactional data at defined grain. |
| **Dimension Table** | Table storing descriptive attributes (Org, Product, Date, Customer). |
| **Conformed Dimension** | A shared dimension used across multiple fact tables. |
| **Measure** | DAX expression returning a single value, reused across visuals. |
| **Data Contract** | YAML specification defining tables, columns, data types, and grain. |
| **KPI Catalog** | Master list of all approved metrics with formulas and QA rules. |
| **Action Code** | Standardized operational lever describing what actions influence KPIs. |
| **Reporting Level** | Classifies a Use Case as Strategic, Tactical, or Operational. |
| **Analytics Stage** | Descriptive, Diagnostic, Predictive, or Prescriptive — defines analytical maturity. |

---

## 4. Governance & Data Quality Terms

| Term | Definition |
|------|-------------|
| **Business Owner** | Person accountable for KPI meaning and business interpretation. |
| **Data Owner** | Responsible for data lineage, accuracy, and refresh cadence. |
| **Report Owner** | Ensures report usability and decision context. |
| **Governance Board** | Cross-functional team reviewing and approving Use Cases and KPIs. |
| **RLS (Row-Level Security)** | Access control filtering data per user role. |
| **OLS (Object-Level Security)** | Access control hiding or exposing tables/measures. |
| **Referential Integrity (RI)** | Degree of consistency between related dimension and fact keys. |
| **Data Lineage** | Traceability of a data field from source to report. |
| **QA Rule** | Quality check defining acceptable value range or logic validation. |
| **Version Control** | Process of tracking document or model changes via Git commits. |
| **Changelog** | Log of all approved updates (Use Cases, KPIs, Actions). |
| **Definition of Done (DoD)** | Criteria that confirm a Use Case or KPI is complete and validated. |
| **Certified Dataset** | Dataset approved by governance board for use in reports. |
| **Ownership Matrix** | Document mapping KPIs to their responsible Business and Data Owners. |

---

## 5. AI & Copilot Readiness Terms

| Term | Definition |
|------|-------------|
| **Copilot Readiness** | Degree to which documentation and metadata are complete and structured for AI use. |
| **Metadata Completeness** | Extent to which KPI definitions, purpose, and lineage are documented. |
| **Semantic Coverage** | Ratio of KPIs and columns with descriptions to total entities in the model. |
| **Context Linking** | Use of consistent field names and references to allow AI navigation between Use Cases, KPIs, and Actions. |
| **Natural Language Prompting** | AI technique to query reports using descriptive business language. |
| **Copilot Action Suggestions** | AI-driven recommendations mapped to Action Codes. |
| **Explainability** | Transparency of KPI logic and variance explanation to business users. |
| **Governed AI** | AI usage with traceable data lineage, approvals, and ethical safeguards. |

---

## 6. Cross-References
| File | Purpose |
|------|----------|
| [`/_includes/Strategic_KPIs.md`](./Strategic_KPIs.md) | Defines top-level KPIs mapped to the 8 dimensions. |
| [`/_includes/KPI_Catalog`](./kPI_catalog/README.md) | Provides formulas, QA, and lineage for all KPIs. |
| [`/_includes/ActionCodes.md`](./ActionCodes.md) | Lists standardized operational levers impacting KPIs. |
| [`/docs/Methodology.md`](../docs/Methodology.md) | Describes modeling, naming, and visualization standards. |
| [`/docs/Reporting_Strategy.md`](../docs/Reporting_Strategy.md) | Outlines governance layers, reporting levels, and lifecycle. |

---

**Governance Note:**  
All glossary changes require Pull Request approval by the Governance Board and update of `/docs/Changelog.md`.

---

_Last updated: 12.10.2025_
