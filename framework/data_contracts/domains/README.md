# Domain Data Contracts

## Purpose

Define the **canonical data contracts** for each business domain within the  
**ActionReady Analytics Framework**.  
These contracts formalize the structure, grain, units, keys, and lineage expected from upstream data sources.

Domain Data Contracts ensure:

- stable schemas,
- consistent semantics,
- predictable ingestion into semantic models,
- and full cross-domain interoperability.

## Scope

Included:

- YAML-based data contracts for Sales, Finance, SCM, ESG, and others  
- Mandatory fields per fact and dimension  
- Grain definitions and surrogate key requirements  
- Unit rules, format rules, and data categories  
- Lineage metadata per field

Not included:

- Transformation logic (ETL/Dataflows/Data Pipelines)  
- Customer-specific data structures  
- Semantic model definitions (see `framework/semantic_models/`)  

## Structure

```yaml
framework/data_contracts/
  domains/
    commercial_sales.yaml
    finance.yaml
    supply_chain.yaml
    operations.yaml
    experience.yaml
    executive.yaml
    README.md  # this file
```

Each domain file contains:

- **Dimensions** (keys, names, hierarchies)  
- **Facts** (grain, metrics, units)  
- **Integrity expectations**  
- **Lineage metadata**  

Example snippet:

```yaml
fact:
  - name: fact_sales
    grain: invoice_line
    columns:
      - {name: DateKey, type: date_key, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: ProductKey, type: int, ref: dim_product}
      - {name: Net Sales Amount, type: currency, agg: sum}
```

## Usage

### For Customers

- Validate whether existing systems can supply the required data  
- Understand what “good” analytical data looks like per domain  
- Support IT ↔ BI alignment through clear contracts

### For Delivery Teams

- Use domain contracts as stable input for ingestion layers  
- Map customer systems to the standardized domain structure  
- Guarantee consistent downstream semantic models  

### For Framework Evolution

- Add new contracts only when domain boundaries expand  
- Maintain backward compatibility where possible  

## Relations

- **WHY Contracts derive from domain definitions in `framework/strategy_operating_model/company/domains.md`  
- **HOW Semantic layer rules enforce contracts during modeling  
- **WITH WHAT Measure TEMPLATES, naming rules, and KPI Catalog rely on contract structure  
- **TEMPLATES Fact and dimension TEMPLATES live under `framework/TEMPLATES/data_contract_TEMPLATES/`

**Location:**  
`framework/framework/data_contracts/domains/README.md`
