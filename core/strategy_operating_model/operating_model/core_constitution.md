# Core Constitution (Stability Contract)

## Purpose

This document defines the **stable logic** of the ActionReady framework: the **artifact roles**, the **allowed connections** between artifacts (Golden Thread), and the **naming/ID invariants** that must remain stable over time.

This constitution is intentionally **tool-agnostic**. Tool-specific implementations live in `products/` and must **consume** the Core contracts without redefining them.

## Non‑negotiable principles

- **Separation of concerns**: Use Cases orchestrate; they do not define KPI meaning or action logic.
- **Single Source of Truth (SSOT)** by artifact type (see below).
- **Referential integrity is mandatory**: every reference must resolve (enforced via Stage 1 + Registry).
- **Roles, not names**: governance points to role IDs, not persons.
- **Additive evolution**: extend by adding artifacts/fields; avoid breaking renames/removals.

## Artifact roles (SSOT)

### Strategy & Operating Model (WHY / HOW)

- **Location**: `core/strategy_operating_model/`
- **Role**: defines strategic intent, operating model, and governance laws.
- **SSOT**: narrative authority (not executable config).

### KPI Catalog (Meaning SSOT)

- **Location**: `core/kpi_catalog/`
- **Role**: authoritative KPI definitions (semantics, ownership/stewardship, interpretation, lineage metadata).
- **Invariant**: Use Cases and Action Codes may only **reference** KPI IDs; they must not redefine KPI meaning.

### Use Cases (Decision intent)

- **Location**: `core/usecases/`
- **Role**: human-readable business context and decision intent.
- **Invariant**: business factsheets are prose-only (Lean). Machine-readable config is not defined here.

### UseCase Bracket (Machine-readable SSOT for a Use Case)

- **Location**: `core/usecases/**/UseCase_Bracket.yaml`
- **Role**: orchestrates the use case:
  - the **strategic KPI** and **influencing KPIs** (by ID)
  - subscribed **action code IDs**
  - governance roles (owner/steward)
  - value-driver model metadata
  - structured UX layout rules (3-30-300, evidence grain)

### Action Codes (Action logic SSOT)

- **Location**: `core/action_codes/`
- **Role**: standardized, reusable steering logic:
  - trigger conditions and levels (L1–L3)
  - guardrails, outcomes, execution steps
  - governance roles (owner/steward)
- **Invariant**: Action Codes are standalone; they must not be embedded inside Use Cases.

### Data Contracts (Technical guarantees)

- **Location**: `core/data_contracts/`
- **Role**: governed technical contracts (facts/dimensions, grains, fields) that enable trust signals.
- **Invariant**: evidence grain in brackets must match governed grains from contracts.

### Templates (Reusable patterns)

- **Location**: `core/templates/`
- **Role**: reusable patterns for page layouts, measures, contracts, and action code structure.

## Allowed connections (Golden Thread)

The Core defines a fixed set of valid edges:

- **Strategy → Strategic KPIs** (defined in strategy docs, implemented as KPI catalog entries)
- **Strategic KPI → Use Case** (use case bracket references 1 strategic KPI)
- **Use Case → Influencing KPIs** (use case bracket references lever KPIs)
- **Use Case → Action Codes** (use case bracket subscribes to action codes)
- **Use Case → Data Contract** (bracket override reference; used for trust signals)
- **UX evidence grain → Data Contract grains** (governed)

No other edge types are considered stable without an explicit constitution update.

## Naming & ID invariants

- **Use Case IDs**: `COM-001`, `FIN-001`, `OPS-001`, `SCM-001`, `XD-001`, … (prefix + 3 digits).
- **KPI IDs**: `domain.topic.metric` (e.g. `sales.net_sales.amount`). IDs are immutable once published.
- **Action Code IDs**: domain prefix + topic + index (e.g. `C-M2.1`, `S-F3.2`, `X-E3.1`). IDs are immutable once published.
- **Paths**: governed artifacts live only under their canonical roots (`core/kpi_catalog`, `core/action_codes`, `core/usecases`, `core/data_contracts`).

## Evolution policy (stability)

### What may change freely (content evolution)

- Add new KPIs, Use Cases, Action Codes, templates, and data contracts (additive growth).
- Improve prose, examples, and guidance as long as SSOT boundaries remain intact.

### What is controlled (breaking risk)

- Renaming/deleting IDs, moving canonical artifact roots, changing edge semantics.
- Any schema change that would invalidate existing artifacts.

### Deprecation over deletion

- Deprecate artifacts by status fields where supported; keep IDs resolvable.
- Prefer compatibility shims/mappings over renames.

## Enforcement (Quality gates)

- **Stage 1 CI Gate**: `tooling/run_stage1_checks.ps1`
- **Registry Gate (ontology)**: `py -3 tooling/ontology/registry_builder.py --out-dir tooling/ontology/out --strict`
- **Tool-specific validation**: lives in `products/<tool>/tooling/` (must never redefine Core SSOT).

---

## Sources & Grounding

This constitution is **framework-internal by design**: the artifact roles, the Golden Thread
edge set, the ID schemes (`COM-001`, `domain.topic.metric`, …), and the SSOT boundaries are
**this repository's own invariants** and have no external authority — they should not be
attributed to a published standard. What *can* be grounded are the general governance practices
the document leans on:

- **ISO/IEC 38500 — Governance of IT for the organization** (the "roles, not names",
  separation of governance from execution, and decision-authority posture behind the
  non-negotiable principles) — ISO: <https://www.iso.org/standard/81684.html>
- **RFC 2119 / BCP 14 — normative requirement keywords** (the "must / non-negotiable /
  mandatory" language used throughout to mark absolute requirements vs. allowances) — IETF:
  <https://www.rfc-editor.org/rfc/rfc2119.html>
- **Architecture Decision Records (ADR)** (the "additive evolution / deprecation over deletion"
  and controlled-change posture; ADRs are the recognized practice for recording stable
  architectural decisions) — <https://adr.github.io/>

> The principles above are *informed by* these external practices; the **specific roles, IDs,
> edges, and SSOT rules in this document are internal framework law** and are authoritative only
> within this repository. They are not derived from, nor certified against, any external standard.

