# Semantic Models

## Purpose
Provide the technical backbone of the ActionReady Analytics Framework.  
Semantic Models turn data contracts into governed, AI-ready analytical structures with consistent logic, measures, and relationships.

---

## Scope

Included:
- Domain-level semantic model definitions
- Measure dictionaries per domain
- ActionReady semantic model (reference implementation)
- Metadata required for governance & Copilot-readiness

Not included:
- Tool-specific deployment scripts
- Customer-specific model variants
- Report visuals or page templates

---

## Structure

```
semantic_models/
  domains/
    sales/
      measure_dictionary_sales.md
    finance/
      measure_dictionary_finance.md
    scm/
      measure_dictionary_scm.md
    esg/
      measure_dictionary_esg.md

  core_action_ready/
    model_definition.yaml
    measures/
      *.md
```

### domains/
Each domain folder holds its semantic dictionary including:
- Canonical measures (naming, format, description)
- KPI relationships
- Grain assumptions tied to data contracts

### core_action_ready/
Contains the reference semantic model used by Action Codes and cross-domain analytics:
- Shared dimensions
- Action aggregates
- Execution layer
- Trigger-level logic (L1–L3)

---

## Usage

### For Customers
- Understand how raw data becomes governed analytical logic.
- Validate which KPIs, measures, and domains are supported.
- Use domain dictionaries as onboarding documentation.

### For Delivery Teams
- Implement semantic models consistently across clients.
- Reuse domain patterns and extend through measure groups.
- Validate models using semantic rules and BPA configurations.

### For Framework Evolution
- Add new domains when expanding industry support.
- Version measure dictionaries carefully to maintain stability.

---

## Relations

- **WHY →** Domains originate from the Company Layer.
- **HOW →** Semantic design follows the Operating Model standards.
- **WITH WHAT →** Measures, templates, and Action Codes rely on semantic consistency.
- **TEMPLATES →** Measure templates and naming rules govern implementation.

---

## Next Step
Start with:
- `core_action_ready/model_definition.yaml`
- Then explore each domain’s measure dictionary.

---

**Location:** `semantic_models/README.md`
