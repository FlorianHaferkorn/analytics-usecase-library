# Data Contracts

## Purpose
Define the formal, stable interface between operational data sources and the ActionReady Analytics Framework.  
Data Contracts ensure consistent schemas, grains, units, and lineage across all domains and use cases.

---

## Scope

Included:
- Domain-level data contracts (Sales, Finance, SCM, ESG)
- Source mappings and metadata
- Required fields, data types, keys, grains, units
- Validation rules and ownership model

Not included:
- ETL / ingestion pipelines
- Physical storage formats
- Customer-specific datasets

---

## Structure

```
data_contracts/
  domains/
    sales.yaml
    finance.yaml
    scm.yaml
    esg.yaml
  sources/
    synthetic/
      *.parquet
      metadata.json
```

### domains/
Contains canonical YAML-based contracts per domain.  
Each contract defines:
- Dimensions (keys, business codes, hierarchies)
- Facts (grain, metrics, units)
- Referential integrity expectations
- Lineage and ownership

### sources/
Holds synthetic/demo data and metadata for examples (e.g., Aurora Group Showcase).

---

## Usage

### For Customers
- Understand what data is required for analytics.
- Validate existing systems against contract requirements.
- Facilitate alignment between IT, analysts, and business owners.

### For Delivery Teams
- Use contracts as upstream specification for modeling & ingestion.
- Validate semantic model assumptions (keys, grains, measures).
- Ensure reproducible onboarding across clients.

### For Framework Evolution
- Extend contracts when domains evolve.
- Maintain backward compatibility where possible.

---

## Relations

- **WHY →** Derived from domains and KPIs in the Company Layer.
- **HOW →** Enforced by semantic layer rules in the Operating Model.
- **WITH WHAT →** Templates guide structure; semantic models rely on them.
- **TEMPLATES →** Fact & Dim contract templates define consistent patterns.

---

**Location:** `data_contracts/README.md`
