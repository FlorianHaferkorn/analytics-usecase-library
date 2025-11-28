# Action Codes

## Purpose
Action Codes translate analytical insights into **concrete business actions**.  
They are the operational engine of the **ActionReady Analytics Framework**, enabling measurable, repeatable, and governed interventions across domains.

This folder provides:
- The full Action Code portfolio (L1–L3)
- Usage rules & governance
- Trigger logic & relationships to KPIs and use cases
- Legacy versions (optional, for reference)

---

## Scope

Included:
- ActionCodes_Portfolio.md (Single Source of Truth)
- Trigger rules, thresholds, and level definitions (L1–L3)
- Instructions on how to embed Action Codes into use cases
- Mapping to KPIs, measures, semantic models, and page templates

Not included:
- Customer-specific Action Codes
- Tool-specific implementation logic
- Execution tracking model (see semantic model)

---

## Structure

```
action_codes/
  ActionCodes_Portfolio.md    → Complete governed portfolio (SSOT)
  how_to_use_action_codes.md   → Usage rules & governance
  ActionCodes_legacy.md        → (Optional) older versions
  README.md                    → This file
```

### ActionCodes_Portfolio.md
- Full list of all Action Codes in the framework  
- Level definitions (L1 = alert, L2 = diagnostic, L3 = prescriptive)  
- Trigger rules per KPI  
- Cross-domain applicability  
- Business impact & expected outcomes

### how_to_use_action_codes.md
- How Action Codes integrate into:
  - Use Cases  
  - Semantic Model (Action Aggregates)  
  - KPI Catalog  
  - Page Templates (3-30-300)  
- Governance rules for adding/modifying Action Codes  
- Best practices for adoption

### ActionCodes_legacy.md
- Contains deprecated or superseded versions  
- Kept only for reference, not for active use

---

## Usage

### For Customers
- Understand how insights turn into business actions  
- Align operational teams on trigger logic  
- Measure impact using the Action Execution Layer  
- Standardize decision processes across departments  

### For Delivery Teams
- Embed Action Codes directly into semantic models  
- Connect KPIs and thresholds with domain logic  
- Maintain strict governance over additions/changes  
- Ensure all use cases reference Action Codes consistently  

### For Framework Evolution
- Add new Action Codes only when business value is proven  
- Maintain immutable IDs for full lineage & tracking  
- Version major changes cleanly and transparently  

---

## Relations

- **WHY →** Action Codes operationalize strategic KPIs.  
- **HOW →** Trigger logic and semantic design follow Operating Model rules.  
- **WITH WHAT →** Page templates & measure templates rely on Action Codes.  
- **TEMPLATES →** Use case templates require Action Code mapping.  

---

**Location:**  
`framework/action_codes/README.md`
