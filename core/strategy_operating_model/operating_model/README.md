# Analytics Operating Model (HOW)

Purpose:
This folder defines **how analytics is designed, governed, built, and operated** to consistently translate business strategy into action-ready insights.  
It is the methodological backbone of the framework.

## 1. Scope

### What belongs here

- How strategy is translated into analytics
- Semantic modeling principles and standards
- Measure governance and single source of truth
- Distribution, UX, and reporting standards
- Operational governance (quality, ownership)
- Automation and AI readiness

### 2. What does NOT belong here

- Business strategy or KPI definitions
- Individual use case content
- Platform-specific implementation details
- Customer- or showcase-specific examples

## 3. Core Concepts

### 3.1 Golden Thread – Strategy to Action

Explains how strategy, KPIs, use cases, semantic models, reports, and actions are logically connected.

File: `golden_thread_strategy_to_action.md`

### 3.2 Operating Model Overview

High-level explanation of the analytics operating model, roles, responsibilities, and flows.

File: `operating_model_overview.md`

### 3.2a Data Layers Standard (Silver-First)

Standard data layers (4 physical + 1 logical). We **define** Silver via contracts; we **deliver** Gold + Semantics. Staging/Bronze out of scope unless included.

File: `data_layers_standard.md`

### 3.3 Semantic Layer

Defines how analytical models are structured to be scalable, reusable, and action-ready.

Files:

- `semantic_layer.md`
- `reference/ActionReady_SemanticModel_Blueprint.md`
- `reference/TMDL_Allowed_Subset.md`
- `reference/TMDL_Official_Refs.md`

### 3.4 Measure System & Single Source of Truth

Rules for defining, naming, governing, and validating measures and KPIs.

Files:

- `measure_system.md`
- `reference/single_source_of_truth.md`

### 3.5 UX & Reporting Standards

Defines how insights are presented consistently using the 3–30–300 principle.

File: `ux_design_system.md`

### 3.6 Distribution Architecture

How analytics is distributed to users (reports, apps, exports, automation).

File: `distribution_architecture.md`

### 3.7 Governance & Operations

Defines ownership, quality gates, lifecycle management, and operational monitoring.

Files:

- `data_governance.md` — includes artifact design laws (§7), framework audit & registry engine (§8), and trust signals (§9)
- `usecases/Usecase_DoD_Core.md`

### 3.8 Automation & AI Readiness

Explains how the framework enables automation and AI-driven analytics.

File: `ai_readiness.md`

## 4. Usage Guidance

Use this folder to:

- Understand how analytics is organized and governed
- Align teams on modeling and reporting standards
- Ensure scalability across domains and use cases
- Enable automation and AI without rework

This operating model is **platform-agnostic by design**, with platform-specific implementations defined elsewhere.

## 5. Relation to the Framework

Layer mapping:

- WHY -> `core/strategy_operating_model/company/`
- HOW -> `core/strategy_operating_model/operating_model/`
- WHAT ->' `usecases/`
- TEMPLATES ->' `core/templates/`

The operating model connects strategy with execution.

