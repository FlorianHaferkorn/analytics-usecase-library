# Action Code Templates

## Purpose

This directory contains **templates** related to Action Codes.
Templates are used to **create, instantiate, and govern** Action Codes and their contextual configuration in a controlled and scalable way.

Templates are **not executable framework assets**.

---

## Scope of This Folder

This folder may contain:

- `ActionCode_TEMPLATE.md` - canonical template for authoring Action Codes
- `ActionCode_KPI_Trigger_Map.yaml` - **reference template** for contextual trigger mappings
- `DecisionSpine_TEMPLATE.yaml` - canonical template for Decision Spines

Files in this folder exist to:

- provide structure and guidance
- enable automation and agent-based instantiation
- prevent business logic from leaking into the framework core

---

## Core Principle (Non-Negotiable)

> **Nothing under `framework/templates/` is production configuration.**

Templates may include examples, placeholders, and reference values.
They must never be interpreted as active or executable logic.

---

## Trigger Mapping Templates (Contextual, Non-Executable)

Trigger Mapping templates define **when** an Action Code becomes decision-relevant in a specific context.

They do **not** define:

- execution logic
- remediation steps
- KPI ownership
- cross-domain optimisation

They exist solely to control **surfacing and attention**.

---

## What Trigger Mapping Templates ARE

- Contextual configuration examples
- Scaffolding for customer-, tenant-, or environment-specific deployments
- Input for automation and AI-assisted instantiation
- A controlled place for example thresholds and scopes

---

## What Trigger Mapping Templates ARE NOT

- They do **not** override Action Code L1-L3 trigger logic
- They do **not** introduce new Action Codes
- They do **not** execute actions
- They do **not** replace governance decisions
- They do **not** represent production-ready configuration

---

## Mandatory Lifecycle & Workflow

1. **Template authoring**
   - Templates may contain placeholders and examples
   - No real business thresholds required

2. **Instantiation**
   - Templates are copied into a deployment-specific location, e.g.:

     ```yaml
     deployments/<customer>/actioncode_trigger_map.yaml
     ```

3. **Contextualisation**
   - Placeholders are replaced with:
     - concrete KPI IDs
     - thresholds
     - scopes

4. **Governance approval**
   - Review by Analytics / Business Governance
   - Only then may `status: approved` be set

5. **Consumption**
   - Reports, pages, and agents read these mappings
   - They never modify them

---

## Explicit Non-Goals

This folder must never be used to:

- store active Action Codes
- store customer-specific configuration
- bypass governance
- experiment with execution logic

---

## Key Takeaway

> **Templates explain *how* to configure Action Codes.**
> **They never decide *when* or *what* to execute in production.**
