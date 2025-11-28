# Glossary

## Purpose
Provide a clear, standardized vocabulary for business, technical, and semantic terms used across the **ActionReady Analytics Framework**.  
A consistent glossary ensures:
- shared understanding across teams,
- clean metadata for AI/Copilot,
- alignment in semantic modeling and reporting.

This is a foundational governance artifact.

---

## Scope

Included:
- Business terminology (KPIs, processes, domains)
- Technical terminology (facts, dims, grains, keys)
- Semantic model terminology (aggregates, action layers)
- Action Codes terminology (L1, L2, L3 triggers)
- AI/Copilot meta-definitions

Not included:
- Customer-specific terminology
- Platform implementation details

---

## Structure

```
glossary/
  business_glossary.md     → Business terms, KPIs, processes
  technical_glossary.md    → Data modeling & architecture terminology
  README.md                → This file
```

### business_glossary.md
Defines:
- KPI names & meanings  
- Business processes (Finance, Sales, SCM, ESG)  
- Domain-specific vocabulary  
- KPIs linked to strategy  

Ideal for onboarding business users and aligning cross-functional teams.

### technical_glossary.md
Defines:
- Fact, dimension, grain  
- Surrogate keys, business keys  
- Semantic layer components  
- Action aggregate, execution layer  
- Naming conventions  

Critical for semantic governance and implementation consistency.

---

## Usage

### For Customers
- Ensures shared terminology across business and analytics teams  
- Supports guided onboarding and decision-making clarity  
- Enables consistent KPI interpretation  

### For Delivery Teams
- Use as reference in workshops, documentation, and semantic model builds  
- Align language across all model descriptions and measure documentation  
- Improve metadata quality for Copilot/AI  

### For AI/Copilot Readiness
- Glossary definitions are used as semantic grounding  
- Enables accurate natural language interpretation  
- Ensures consistent responses in Copilot scenarios  

---

## Relations

- **WHY →** Glossary reflects business concepts defined in the Company Layer  
- **HOW →** Supports Operating Model needs (UX, semantic standards, AI readiness)  
- **WITH WHAT →** Used by templates, Action Codes, and KPI Catalog  
- **TEMPLATES →** Factsheet templates reference glossary terms  

---

## Next Step
Populate:
1. `business_glossary.md`  
2. `technical_glossary.md`  

Use domain KPIs and semantic measures as first input.

---

**Location:**  
`framework/glossary/README.md`
