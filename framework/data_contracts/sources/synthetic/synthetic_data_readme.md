# Synthetic Data Design – README

This folder defines the design principles, contracts and scope for all synthetic data used in the analytics-usecase-library.  
It serves as the single source of truth for generating consistent, scalable and AI-ready data for the Aurora Group.

---

## 1. Purpose

The synthetic data layer provides:
- A stable backbone for all 73 Use Cases.  
- Deterministic and reproducible datasets for demos, development and testing.  
- A domain driven structure aligned with the semantic model and naming conventions.  
- A foundation for AI agents and Copilot to provide consistent answers.

---

## 2. Core Components

### 2.1 `synthetic_data_contract.yaml`
Defines the **full data model**, including:
- Dimensions (grain, keys, columns, descriptions, QA rules)  
- Facts (grain, keys, reference dimensions, measures, QA)  
- Formatting, aggregation behavior, hiding rules  
- Naming conventions (Amount, Qty, %, Rate, DateKey)  
- Semantic best practices (Star Schema, conformed dimensions)

It enforces how tables must be built and prevents inconsistent or ad-hoc structures.

### 2.2 `synthetic_data_scope.yaml`
Specifies:
- Which datasets exist  
- Their generation status (planned / generated)  
- Time periods  
- Expected row counts / volume hints  
- Which Use Cases each dataset supports  

This is the **evolution plan** for the synthetic data landscape.

---

## 3. How the files work together

1. **Define or update the Contract**  
   - When new Use Cases require new tables or columns, the contract is extended.  
   - Breaking changes are avoided (or versioned).

2. **Update the Scope**  
   - When implementing new data tables, update `status`, `period`, and `covers_usecases`.

3. **Implement in the generator**  
   - Synthetic data notebooks/scripts read the Contract.  
   - They fill the Scope with generated datasets.

4. **Validate using QA rules**  
   - Referential integrity  
   - Numeric ranges  
   - Business plausibility (e.g., margin bands, stock ≥ 0)

---

## 4. Folder recommendations

A recommended structure in the repo:

```
/docs/data_design
    synthetic_data_contract.yaml
    synthetic_data_scope.yaml
    synthetic_data_readme.md
    /generators        # Notebooks or scripts
    /samples           # Optional: CSV samples for inspection
```

This keeps design, implementation and samples cleanly separated.

---

## 5. Versioning rules

- Contract changes require version increments.  
- Additive changes (new columns, new tables) → minor version.  
- Structural changes (grain, keys) → major version.  
- Scope changes (status, periods) → no version bump.

---

## 6. AI-Readiness Notes

To enable consistent Copilot/Agent answers:
- All tables and columns must include **Purpose**, **Definition**, **Grain**, **Unit**, **Lineage**, **QA**.  
- The contract acts as the semantic grounding layer.  
- No definitions outside the Contract.  
- No hidden business logic in code or notebooks only in the Contract.

Later we will add:
- `usecase_dictionary.yaml`  
- `domain_measure_catalog.yaml`  
- `ai_semantic_layer.yaml`  
- `ai_rules.md`

These ensure deterministic KI behavior.

---

## 7. Contribution Workflow

1. Add or update Use Case.  
2. Map to required tables/measures.  
3. Update **Contract** (if structure changes).  
4. Update **Scope** (if dataset required).  
5. Implement generator logic.  
6. Validate via QA.  
7. Push updated Contract + Scope.

This ensures every data artifact stays consistent with the entire ecosystem.

---

## 8. Contact

This documentation is part of the *analytics-usecase-library*.  
All decisions follow the Aurora Group domain model and the 73 Use Case definitions.




