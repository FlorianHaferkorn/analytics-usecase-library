# Includes Folder

This folder contains all **shared reference files** that define standardized terminology, KPIs, and operational levers across the **Analytics Use Case Library**.  
These files form the **semantic backbone** of the entire reporting framework.

---

## 1. Purpose
The `_includes` folder centralizes all reusable metadata definitions:  
- KPIs (formulas, QA, lineage)  
- Strategic KPI hierarchy (linking to business strategy)  
- Action Codes (standardized levers for operational action)  
- Glossary (semantic alignment across business and data teams)

Together, these files ensure:
- Consistent KPI and term usage across all clusters and reports  
- Clear traceability from **Strategic KPI → KPI Catalog → Use Case → Action Code**  
- Governance and version control via Pull Request workflow  

---

## 2. Structure

| File | Purpose |
|------|----------|
| **Glossary.md** | Defines standardized terminology and concepts for all business and governance terms. |
| **KPI Catalogs** | Dimension-spezifische Kataloge im Ordner `/_includes/kpi_catalog/` inkl. Master-Übersicht `KPI_Catalog_README.md`. |
| **Strategic_KPIs.md** | Defines the top-level KPI hierarchy grouped by eight Impact Dimensions (Growth, Profitability, Liquidity, Efficiency, Customer Value, ESG, Governance, Innovation & People). |
| **ActionCodes.md** | Lists standardized operational levers (Actions) that directly impact KPIs. |
| **README.md** | Explains how all include files interact and how they are maintained. |

---

## 3. File Interactions

```mermaid
flowchart LR
  RS[Reporting_Strategy] --> SK[Strategic_KPIs]
  SK --> UC[Use Cases]
  UC --> DK[Driver KPIs]
  DK --> AC[ActionCodes]
  AC --> EI[Expected Impact]

```

---

_Last updated: 12.10.2025_

