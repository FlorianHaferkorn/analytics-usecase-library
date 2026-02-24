# Semantic Layer

The semantic layer is the structural foundation that connects business intent with analytical execution.

While the Golden Thread defines which decisions matter and why, and the Operating Model governs how analytical logic is maintained, the semantic layer provides the stable structure in which this logic is expressed.

It does not introduce strategy, KPIs, or actions.
It enables their consistent implementation across domains, use cases, and tools.

## 1. Role in the framework

The semantic layer operationalizes the Golden Thread within analytical models.

- Strategy, KPIs, and use cases define intent and decision logic.
- The semantic layer translates this intent into governed analytical structures.
- Measures, reports, and actions consume these structures without redefining meaning.

The semantic layer acts as the contract between business meaning and technical implementation.

## 2. Core Modeling Principles

The semantic layer follows a small set of structural principles to ensure consistency and scalability.

Facts are modeled at explicit business grains.
Dimensions are shared and conformed across domains.
Business logic is implemented through measures rather than calculated columns.

Where decision-making requires action-oriented analysis, dedicated aggregates are introduced.
These aggregates support detection, explanation, and prioritization of actions without enforcing execution.

Explicit metadata enables interpretation, governance, and assisted analytics.

## 3. Domain Aggregates

Each domain semantic model follows a consistent structural pattern.

Domain aggregates represent stable business facts at auditable grains.
They are designed to support analytical consumption across multiple use cases.

Shared dimensions provide consistent slicing and alignment across domains.
This allows domains to evolve independently while remaining analytically compatible.

## 4. Action Aggregates

Action-oriented analysis is supported through dedicated aggregates aligned with Action Codes.

These aggregates quantify deviation, impact, and intervention potential.
They enable prioritization and root-cause analysis without automating decisions.

Action aggregates provide signals only. Thresholds, levels (L1-L3), and decision
rules are defined exclusively in Action Codes.

## 5. Action Execution Layer (Optional / Future)

Where actions are taken, execution can be recorded explicitly.
This layer is optional and intended for later phases once action outcome tracking is in scope.

The action execution layer links analytical insight to observed outcomes.
It enables learning, comparison, and evaluation of decision effectiveness over time.

Execution tracking supports learning and improvement.
It does not enforce action.

## 6. End-to-End Semantic Pattern

Across domains, the same structural logic applies:

- conformed dimensions,
- domain aggregates,
- action-oriented aggregates,
- and optional execution tracking.

This ensures analytical consistency even as domains, use cases, and tools evolve.

## 7. Normative Semantic Modeling Standards

The semantic layer defines binding structural standards for all analytical models.

These standards exist to ensure analytical consistency, comparability, and scalability across domains.
They are normative, not instructional.

### 7.1 Fact Modeling

Facts are modeled at explicit, auditable business grains.
Each fact table represents a single, well-defined business process or aggregate.
Grain ambiguity is not permitted.

### 7.2 Dimension Modeling

Dimensions are conformed and reused across domains.
Shared dimensions represent common business concepts and must not be redefined locally.
Role-playing dimensions are explicitly modeled.

### 7.3 Relationships

Relationships follow a star-schema pattern.
Many-to-many relationships are avoided unless required by business logic and explicitly documented.
Bridge tables are introduced only when semantic clarity cannot be achieved otherwise.

### 7.4 Business Logic

Business logic is implemented through measures, not calculated columns.
Calculated columns are limited to technical or classification purposes.

### 7.5 Action-Oriented Structures

Action-oriented aggregates follow the same structural standards as analytical facts.
They quantify deviation, impact, and prioritization potential.
They do not enforce execution.

### 7.6 Metadata and Documentation

All semantic objects require clear naming and descriptive metadata.
Metadata supports interpretation, governance, and assisted analytics.

## 8. Governance and Validation

Semantic standards are enforced through validation and review.

Checks ensure alignment with the Golden Thread, the Operating Model, and the Measure System.
Governance protects meaning and dependencies rather than enforcing process.

Validation mechanisms support consistency and trust at scale.

## 9. Usage Guidance

This document (semantic_layer.md) is the canonical reference for semantic layer structure.

Domains instantiate the pattern using their data contracts, UseCase_Bracket orchestration, and KPIs.
Use cases and reports consume the semantic layer without redefining structure.

Showcase implementations (e.g. Aurora domain semantic models) follow this pattern but do not extend it.

## 10. Outcome

When applied consistently, the semantic layer ensures that:

- business meaning is preserved across analytical assets,
- domains scale without fragmentation,
- and action-oriented analytics remains interpretable and governed.

The semantic layer enables decision intelligence by providing structure, not control.
