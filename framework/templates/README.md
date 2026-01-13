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
    overview_page_template.md
    insights_page_template.md
    explorer_page_template.md

  measure_templates/
    measure_template.md

  data_contract_templates/
    fact_template.yaml
    dim_template.yaml

  README.md
```

### page_templates/

Defines the canonical page patterns:

- **Overview Page (3-second view)** → KPI Cards + Delta  
- **Insights Page (30-second view)** → Trends, Rankings, Multiples  
- **Explorer Page (300-second view)** → Table/Matrix, drill, export  

These enforce consistent UX aligned with Apple/iOS-inspired design principles.

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

- Extend or improve templates based on real project outcomes.  
- Keep changes minimal and backward-compatible.  

---

## Relations

- **WHY →** Templates reflect the business priorities and KPIs defined in the Company Layer.  
- **HOW →** Templates enforce the standards defined in the Operating Model.  
- **WITH WHAT →** Forms the practical toolkit used by delivery teams.  
- **TEMPLATES →** Core of reproducible use case design.  

---

**Location:**  
`framework/templates/README.md`
