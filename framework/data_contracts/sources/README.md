# Source Metadata & Synthetic Data

## Purpose

Provide **source-level metadata** and **synthetic example datasets** required for demos, development, and the Aurora Group Showcase.

This folder helps illustrate how real data maps into the ActionReady domain contracts — without exposing sensitive customer data.

## Scope

Included:

- Metadata describing source ↔ contract mappings  
- Synthetic datasets for development or demos  
- Sample parquet/csv files used for the Aurora Showcase  
- Data profiling summaries (optional)

Not included:

- Production datasets  
- Sensitive or identifiable information  
- ETL scripts (see project repos for customer implementations)

## Structure

```yaml
sources/
  synthetic/
    *.parquet
    metadata.json
  commercial.yaml
  operations.yaml
  supply_chain.yaml
  finance.yaml
  experience.yaml
  README.md  # this file
```

### synthetic/

Contains synthetic demo data aligned with domain contracts.  
Used primarily for:

- Aurora Group Showcase  
- Prototyping  
- Notebook-based validation  
- Teaching and training

`metadata.json` can describe:

- schema  
- sample distributions  
- lineage to contract fields  

## Usage

### For Customers

- Understand how raw data maps to domain-level contracts  
- Validate feasibility of feeding their systems into the framework  

### For Delivery Teams

- Use synthetic data during early development  
- Run notebooks, dataflows, and demo pipelines without customer data  
- Prototype semantic models and use cases quickly  

### For Framework Evolution

- Keep synthetic data aligned with domain contracts  
- Update metadata when contracts change  

## Relations

- **WHY Synthetic datasets illustrate business processes from `docs/company`  
- **HOW Contracts and semantic rules from the Operating Model validate data  
- **WITH WHAT Measures, KPIs, and Action Codes rely on this mapping  
- **TEMPLATES Data contract TEMPLATES define HOW source fields map to domain fields  

**Location:**  
`framework/data_contracts/sources/README.md`
