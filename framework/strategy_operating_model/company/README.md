# Company Layer (WHY)

Purpose:
The Company layer defines **why analytics exists** in the organization.  
It establishes the strategic context, priorities, and decision logic that all downstream analytics artifacts must support.

This layer is **business-owned** and independent of tools, technologies, or implementation details.

## What belongs here

This folder contains the **strategic foundation** of the Analytics Framework:

- Business strategy and strategic intent
- Strategic focus areas and KPIs
- Executive-level key questions
- Strategic alignment between KPIs, use cases, and actions
- Reporting and design principles at company level
- Domain definitions and boundaries

These documents define *what matters* and *why it matters*.

## What does NOT belong here

The following topics are intentionally out of scope for this layer:

- Technical implementation details (semantic models, measures, tooling)
- Data models or data contracts
- Page layouts or visual templates
- Tool-specific guidance
- Use case implementation details

Those topics are handled in downstream layers.

## Primary entry points (start here)

### 1. Company Strategy & Strategic Alignment

**`company_strategy.md`**

This is the **primary business entry point** for executives and decision-makers.

It defines:

- Strategic objectives and focus areas
- The canonical set of Strategic KPIs
- Executive key questions
- Strategic alignment from KPIs to use cases and actions
- Governance and review principles

> If you read only one document in this folder, read this one.

### 2. Reporting Principles & Design Standards

**`reporting_principles.md`**

Defines the **non-negotiable principles** for how reporting is designed and consumed.

It explains:

- Reporting as a decision instrument
- Actionability and progressive disclosure (3EUR"30EUR"300)
- Cognitive simplicity and consistency
- User-centric design and transparency

This document defines the **reporting DNA** of the organization.

### 3. Domains

**`domains.md`**

Defines:

- Business domains and their scope
- Ownership boundaries
- How domains structure analytics responsibility

Domains provide the **organizational and semantic structure** for use cases, KPIs, and data contracts.

## Relationship to other framework layers

The Company layer defines the **WHY**.

It is operationalized by:

- **Analytics Operating Model (HOW):**  
  `framework/strategy_operating_model/operating_model/`
- **Use Cases (WHAT):**  
  `usecases/`
- **Semantic Models, KPIs, Measures (WITH WHAT):**  
  `framework/` and `semantic_models/`

All downstream artifacts must be traceable back to the documents in this folder.

## Guiding principle

If a KPI, use case, report, or action cannot be linked back to this layer,
it should be questioned.

This layer ensures that analytics remains:

- Strategy-driven
- Decision-oriented
- Consistent across the organization

