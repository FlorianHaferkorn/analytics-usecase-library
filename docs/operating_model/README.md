# Analytics Operating Model (HOW)

## Purpose
Define how the **ActionReady Analytics Framework** is operated end-to-end:  
from data contracts to semantic models, UX, operations, and AI-readiness.  
This layer turns strategic intent (WHY) into a reliable, scalable analytics system.

---

## Scope

What belongs here:
- Principles for data governance and ownership
- Design of the semantic layer and measure system
- Global UX & interaction standards (3-30-300, Apple/iOS-inspired)
- Distribution & consumption architecture (apps, navigation, roles)
- Operational standards (SLAs, monitoring, data quality)
- AI/Copilot readiness (metadata, glossary, intent patterns)

What does **not** belong here:
- Company-specific business strategy or domains (see `docs/company/`)
- Tool-specific configuration details (see `framework/implementation_guides/`)
- Customer-specific project setups (live in separate project repos)
- Raw data pipelines or ETL code

---

## Structure

```
operating_model/
  data_governance.md          → Roles, responsibilities, policies
  semantic_layer.md           → Conceptual semantic model design
  ActionReady_SemanticModel_Blueprint.md → Deep dive blueprint (action-ready model)
  measure_system.md           → Measure conventions, naming, documentation
  ux_design_system_3-30-300.md → Global UX/visual standards
  distribution_architecture.md → How analytics is delivered to users
  operations_sla_monitoring.md → SLAs, monitoring, incident handling
  ai_readiness.md             → Metadata, glossary, prompts & AI integration
```

### data_governance.md
Defines ownership (data owners, model owners), approval flows, and governance rules for semantic models and KPIs.

### semantic_layer.md
Explains the conceptual structure of the semantic layer across domains: shared dimensions, domain models, and use case extensions.

### ActionReady_SemanticModel_Blueprint.md
Provides a reference blueprint for an action-ready semantic model, including aggregates, grains, and the action execution layer.

### measure_system.md
Defines how measures are named, structured, formatted, documented, and governed across all domains.

### ux_design_system_3-30-300.md
Captures global UX rules: 3-30-300 model, component standards, navigation patterns, and Apple/iOS-aligned design principles.

### distribution_architecture.md
Describes how users access analytics: apps/portals, navigation flows, role concepts, and dataset/report separation.

### operations_sla_monitoring.md
Defines operational standards: refresh windows, SLAs, monitoring dashboards, alerting, and incident processes.

### ai_readiness.md
Describes how metadata, glossary, semantic consistency, and prompt patterns make the framework AI/Copilot-ready.

---

## Usage

- **For customers:**
  - Use this layer to define how analytics should work in daily operations.
  - Align IT, data, and business teams on a single operating model.
  - Derive platform-agnostic requirements for implementation.

- **For delivery teams:**
  - Use as the master reference when designing models, reports, and operations.
  - Ensure every project meets the same minimum standards (governance, UX, SLAs).
  - Map these concepts to specific tools in the implementation guides.

- **For continuous improvement:**
  - Evolve these documents as your organization matures.
  - Keep them stable enough to function as a long-term standard.

---

## Relations

- **WHY (Company Layer)**  
  The operating model translates strategy, domains, KPIs, and key questions into concrete design and operational rules.

- **WITH WHAT (Framework Standards)**  
  Action Codes, KPI Catalog, Glossaries, and Templates are implemented in line with the operating model.

- **TEMPLATES (Patterns & Blueprints)**  
  Page templates, measure templates, and data contract templates are practical expressions of the rules defined here.

---

## Next Step

After reading this README:

1. Start with `semantic_layer.md` and `ux_design_system_3-30-300.md` to understand the core design standards.  
2. Review `measure_system.md` and `data_governance.md` to align on ownership and logic.  
3. Use `operations_sla_monitoring.md` and `ai_readiness.md` to define how the framework runs and how AI/Copilot is enabled.

---

**Location to place this file:**  
`docs/operating_model/README.md`
