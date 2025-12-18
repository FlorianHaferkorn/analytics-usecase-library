# Implementation Guides

These guides are optional.
They explain how to implement the framework on specific platforms.
They are not required to understand or use the framework.

## Purpose
Translate the **ActionReady Operating Model** (semantics, UX, governance, AI-readiness)  
into concrete, platform-specific implementation practices.

These guides explain **how** to realize the conceptual framework inside specific analytics platforms such as:
- Microsoft Fabric / Power BI  
- Databricks  
- Snowflake + Tableau  
- Looker  

They ensure that every technical implementation delivers the same high-quality, governed result — regardless of the underlying technology stack.

---

## Scope

Included:
- Platform-specific mappings of:
  - Semantic Layer design  
  - Measure System enforcement  
  - Data Contract consumption  
  - Action Codes integration  
  - KPI governance  
  - Distribution & navigation patterns  
  - RLS/OLS patterns  
  - AI/Copilot-enablement  
- Recommended workspace / project structures  
- Best practices for pipelines, orchestration, and refresh

Not included:
- Raw ETL pipelines  
- Customer-specific provisioning processes  
- Tool-agnostic operating model principles (see `docs/operating_model/`)

---

## Structure

```
implementation_guides/
  fabric_powerbi.md        → Implementation in Microsoft Fabric + Power BI ecosystem
  databricks.md            → Implementation in Databricks (Unity Catalog, Lakehouse)
  snowflake_tableau.md     → Snowflake Warehouse + Tableau semantic alignment
  looker.md                → LookML modeling, governance, and KPI mapping
  README.md                → This file
```

### fabric_powerbi.md
Covers:
- PBIP structure  
- Dataset modeling & semantic alignment  
- Dataflows Gen2 / Lakehouse ingestion  
- Workspace structure (Dev/Test/Prod)  
- RLS/OLS patterns  
- Measure & DisplayFolder enforcement  
- App navigation & UX rules (3-30-300)

### databricks.md
Covers:
- Delta Lake contracts  
- Unity Catalog mapping  
- Semantic consistency between SQL & BI tool  
- Metrics layer definitions  
- Governance & lineage alignment

### snowflake_tableau.md
Covers:
- Snowflake schema & scalable warehouse patterns  
- Custom SQL / Tableau Data Models  
- Foldering via Tableau Projects  
- Metric Layer in Tableau (if used)

### looker.md
Covers:
- LookML views & explores  
- Metrics standardization  
- Permissions & governance  
- Content navigation rules

---

## Usage

### For Customers
- Understand how to realize the ActionReady Operating Model on their chosen platform  
- Validate readiness of their current architecture  
- Align internal IT & analytics teams on a common approach  

### For Delivery Teams
- Implement the same framework consistently across platforms  
- Use platform guides during solution design & review  
- Ensure all deliverables match the standards of the Operating Model  

### For Framework Evolution
- Add new platform guides as adoption expands  
- Keep platform patterns aligned with the core Operating Model  

---

## Relations

- **WHY →** Derived from business strategy & domain definitions  
- **HOW →** Platform-specific realization of the Operating Model  
- **WITH WHAT →** Implements templates, Action Codes, KPIs, measure system  
- **TEMPLATES →** Page templates and semantic templates map directly to platform structures

---

## Next Step
Start with:
- `fabric_powerbi.md` if you are implementing in Microsoft Fabric  
- Or open the platform guide relevant for your organization

---

**Location:**  
`framework/implementation_guides/README.md`
