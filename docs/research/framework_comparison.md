# Framework Comparison: Analytics Use Case Library

How does our Analytics Strategy-to-Action Framework compare to other approaches for organizing, prioritizing, and governing analytics use cases?

This document summarizes research into 8 external frameworks and provides a structured comparison.

---

## Our Framework at a Glance

- **Golden Thread**: Strategy &rarr; KPIs (113) &rarr; Use Cases (21) &rarr; Semantic Models &rarr; Action Codes (64) &rarr; Decisions
- **UseCase_Bracket.yaml**: Machine-readable YAML with JSON Schema validation and CI gate (Stage 1)
- **Health Scorecard**: H1-H5 metrics for automated framework health measurement
- **Value Driver Model**: Formula, impact direction, threshold embedded in each use case
- **UX Layout Rules**: 3-30-300 model (KPI band &rarr; driver charts &rarr; detail tables) defined per use case
- **Tooling**: Golden Thread Discovery Studio (Streamlit + AI chat), UX Layout Editor, Registry Builder
- **Governance**: owner_role + steward_role per use case, CODEOWNERS, pre-commit validation

---

## 8 External Frameworks Compared

### 1. Bernard Marr - Data Use Case Template

Simple, accessible template with 6 sections: description, data requirements, analytics approach, technology/infrastructure, governance (quality, ethics, privacy, ownership), and expected outcomes.

| Aspect | Assessment |
|---|---|
| **Strength** | Easy to communicate to non-technical stakeholders |
| **Weakness** | No golden thread, no semantic model, static PDF (not machine-readable), no prioritization |
| **Source** | [bernardmarr.com](https://bernardmarr.com/how-to-define-a-data-use-case-with-handy-template/) |

### 2. Schwarz et al. - Systematic Evaluation Framework (Academic)

9-criteria scoring model for early-stage screening, developed through action design research with Bundesdruckerei GmbH across 3 iterative design cycles.

| Aspect | Assessment |
|---|---|
| **Strength** | Only framework with rigorous early-stage screening; addresses "most data initiatives fail" |
| **Weakness** | Academic only, no execution framework, no tooling integration |
| **Source** | [University of Hawaii](https://scholarspace.manoa.hawaii.edu/items/34b627d7-a300-40a8-a826-d66b4bd10d43) |

### 3. RICE / ICE / Value-Effort Matrix

RICE (Reach x Impact x Confidence / Effort) developed by Intercom, used by 38% of teams. ICE is its simpler sibling (Impact x Confidence x Ease). Value-Effort Matrix creates four quadrants: Quick Wins, Big Bets, Fill-ins, Money Pits.

| Aspect | Assessment |
|---|---|
| **Strength** | Objective scoring reduces bias; RICE's Reach component prevents "features I'd use" bias |
| **Weakness** | No use case structure, no KPI/action integration - purely scoring tools for product features |
| **Sources** | [ProductPlan](https://www.productplan.com/glossary/rice-scoring-model/), [Growth Method](https://growthmethod.com/prioritisation-frameworks/) |

### 4. Analytics Maturity Models (Gartner / TDWI / DELTA Plus)

Three major models: Gartner (Descriptive &rarr; Diagnostic &rarr; Predictive &rarr; Prescriptive), TDWI (5 phases across 5 dimensions, 35 assessment questions), DELTA Plus (7 elements across 5 stages scored 1.00-5.99).

| Aspect | Assessment |
|---|---|
| **Strength** | Strategic, organization-wide view for roadmapping; shows organizational maturity |
| **Weakness** | Assessment-focused, not execution-focused; no use case template or semantic model |
| **Sources** | [MDPI](https://www.mdpi.com/2078-2489/11/3/142), [IIA](https://iianalytics.com/resources/delta-plus-model-and-five-stages-of-analytics-maturity-a-primer) |

### 5. Value Driver Trees (VDTs) / KPI Trees

Hierarchical decomposition: root node (business objective) &rarr; branch nodes (KPI drivers) &rarr; leaf nodes (operational metrics/use cases). Used by ZS Associates specifically to identify data-driven use cases. SAP Analytics Cloud has native VDT support for simulation.

| Aspect | Assessment |
|---|---|
| **Strength** | Makes cause-and-effect explicit; enables scenario simulation; natural prioritization |
| **Weakness** | Assumes hierarchical cause-and-effect (reality is nonlinear) |
| **Note** | Our `value_driver_model` field already implements this concept |
| **Sources** | [ZS Associates](https://medium.com/zs-associates/identifying-data-driven-use-cases-with-a-value-driver-tree-bd5795e26e21), [ResearchGate](https://www.researchgate.net/publication/377567987_Value_Driver_Trees_for_KPI-Based_Decision_Analytics_Process_Performance_in_the_Order-to-Delivery_Process) |

### 6. Data Mesh (Zhamak Dehghani / ThoughtWorks)

4 principles: domain ownership, data as a product, self-serve data platform, federated computational governance.

| Aspect | Assessment |
|---|---|
| **Strength** | Scales for large/complex organizations; addresses data silos (82% of enterprises affected) |
| **Weakness** | Complex to implement; no standard use case template; no KPI catalog |
| **Source** | [Martin Fowler](https://martinfowler.com/articles/data-mesh-principles.html) |

### 7. BI Center of Excellence (CoE) Governance Framework

Use case intake, prioritization queue (governance committee), standards/templates, content library, community of practice. Key concept: "managed self-service" - empower business within governed guardrails.

| Aspect | Assessment |
|---|---|
| **Strength** | Most mature governance model; real-world proven (NTT DOCOMO: 10x analyst productivity) |
| **Weakness** | Often Microsoft-centric; can become bureaucratic; no formal KPI catalog |
| **Sources** | [Microsoft Fabric CoE](https://learn.microsoft.com/en-us/power-bi/guidance/fabric-adoption-roadmap-center-of-excellence), [GoCollectiv](https://gocollectiv.com/blog/power-bi-center-of-excellence-framework/) |

### 8. Databricks Unity Catalog Metrics / Semantic Layer

Metrics as first-class governed assets defined in YAML. Metric Views separate measures from dimensions, enabling "define once, use everywhere" across dashboards, AI/ML, pipelines.

| Aspect | Assessment |
|---|---|
| **Strength** | True metric standardization; lineage; fine-grained access control; version-controllable |
| **Weakness** | Databricks-specific (vendor lock-in); no use case framework; no strategy-to-action |
| **Source** | [Databricks](https://docs.databricks.com/aws/en/metric-views/) |

---

## What Our Framework Does Better

| Differentiator | Closest Competitor | Why We Are Better |
|---|---|---|
| **Full Golden Thread** (Strategy &rarr; KPIs &rarr; Use Cases &rarr; Semantic Model &rarr; Actions) | None covers the full chain | Others stop at KPIs or dashboards; we go to action |
| **Action Codes with trigger thresholds** | BI CoE has "recommendations" but not formalized | Unique insight-to-action mechanism with machine-readable triggers |
| **Machine-readable use cases (YAML) with CI validation** | Unity Catalog Metrics has YAML for metrics | No other has use cases as YAML with schema validation + CI gate |
| **Health Scorecard (H1-H5)** | Maturity models have assessment | We measure continuously and automatically, not manually once |
| **Value Driver Model in use case** | VDTs exist separately | We integrate formula + impact logic directly in the use case |
| **UX Layout Rules in use case** | None | Unique bridging of analytics logic to report design (3-30-300) |
| **AI-powered Discovery** (Golden Thread Studio) | None for use case creation | AI chat generates use cases from documents |
| **Graph-based ontology** (master_registry.json) | OpenMetadata has lineage graph | We have Use Case + KPI + Measure + Data Contract + Action in one graph |

---

## What Others Do Better - Improvements Adopted

| Gap | Who Does It Better | Action Taken |
|---|---|---|
| **No formal prioritization scoring** | RICE/ICE, Schwarz et al. | Added `prioritization` block to UseCase_Bracket (business_value, implementation_effort, confidence, reach, priority_score) |
| **No readiness assessment** | Schwarz et al., Gartner | Added `readiness` block to UseCase_Bracket (data_availability, org_capability, stakeholder_alignment, overall_readiness) |

### Potential Future Improvements

| Gap | Who Does It Better | Recommendation |
|---|---|---|
| **No Community of Practice / adoption model** | BI CoE Framework | Establish training concept, champion network, "managed self-service" |
| **No self-assessment for organizations** | TDWI, DELTA Plus | Questionnaire showing "where do you stand?" and recommending entry point |
| **Federated governance for multi-org** | Data Mesh | Integrate domain ownership principles when scaling to multiple organizations |
| **Scenario simulation** | SAP Analytics Cloud VDTs | The `value_driver_model` field has the structure - add simulation capability |
| **Onboarding for non-technical users** | BI CoE, Bernard Marr | Simpler entry point for non-technical stakeholders |

---

## Summary

Our framework is the most comprehensive in the comparison. No other approach combines strategy-to-action traceability, machine-readable use cases, automated validation, KPI catalog, action codes, semantic model, and UX rules in one system.

The biggest improvement potential lies not in architecture (which is superior) but in:
1. **Accessibility** - Lower entry barriers for non-technical users
2. **Adoption** - Community model and self-assessment tools
3. **Simulation** - Making the existing value driver model interactive
