# Templates (Pattern Library)

## Purpose

Provide reusable design, modeling, and documentation templates used across the  
**ActionReady Analytics Framework**.  
These templates guarantee consistency, speed, and quality across all analytics solutions.

Templates turn the framework into a **repeatable product**.

---

## Scope

Included:

- Page templates (3-30-300-aligned)
- Measure templates (naming, logic, documentation)
- Data contract templates (fact/dim patterns)
- Standard structures for consistent use case delivery

Not included:

- Customer-specific variants
- Actual KPIs, measures, or pages (in use cases or semantic models)
- Platform-specific configuration

---

## Structure

```yaml
templates/
  page_templates/
    README.md
    page_types/
    mappings/
    governance/
    components/

  measure_templates/
    measure_template.md

  data_contract_templates/
    fact_template.yaml
    dim_template.yaml

  silver_to_gold/
    silver_to_gold_mapping_template.yaml   # Silver→Gold mapping (repeatable setup)
    README.md

  README.md
```

### page_templates/

Defines the canonical page types:

- **T1 Strategic Overview**
- **T2 Tactical Variance**
- **T3 Operational Monitoring**
- **T4 Prescriptive Recommendation**

Only these four types are allowed. See `framework/templates/page_templates/README.md`.

### measure_templates/

Defines:

- Naming conventions (Amount, Qty, Count, %, Rate, Variance)  
- Formatting rules (currency, decimal, percent)  
- Documentation template (Purpose, Definition, Grain, Unit, Lineage, QA)  
- Foldering standards  

Ensures complete Copilot-readiness and semantic integrity.

### data_contract_templates/

Contains standard YAML structures for:

- Fact tables (grain, keys, metrics, units)
- Dimension tables (keys, business codes, names, hierarchies)

These support consistent upstream modeling across all domains.

### silver_to_gold/

Declarative mapping template for **Silver → Gold** transformation so setup is repeatable:

- One mapping file per domain (or solution) listing Gold dimensions, facts, and action aggregates with Silver source(s), grain, and column/aggregation rules.
- Same structure every time; ETL/ELT or codegen can produce Gold from Silver from this spec.
- See `framework/strategy_operating_model/operating_model/data_layers_standard.md` (§5).

---

## Usage

### For Customers

- Apply templates to enforce consistent analytics design.  
- Accelerate delivery by reusing patterns.  
- Ensure alignment between business strategy and reporting.  

### For Delivery Teams

- Start every report, measure, or contract from these templates.  
- Maintain strict compliance with naming and foldering rules.  
- Integrate templates into project scaffolding and automation.  

### For Framework Evolution

- V1 is a fixed baseline; templates are instantiated, not extended.  
- Any changes require explicit framework governance outside customer projects.  

---

## Relations

- **WHY ?** Templates reflect the business priorities and KPIs defined in the Company Layer.  
- **HOW ?** Templates enforce the standards defined in the Operating Model.  
- **WITH WHAT ?** Forms the practical toolkit used by delivery teams.  
- **TEMPLATES ?** Core of reproducible use case design.  

---

**Location:**  
`framework/templates/README.md`

