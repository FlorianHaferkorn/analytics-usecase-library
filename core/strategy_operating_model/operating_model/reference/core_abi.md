# Core ABI (Stable Machine Interface)

## Purpose

The **Core ABI** is the stable, machine-consumable interface between:

- **Core SSOT** (`core/…`) and governance tooling, and
- **tool-specific adapters** (`products/<tool>/…`) and automation.

Adapters must **not** parse Core artifacts ad-hoc. They must consume the ABI outputs listed below (or a versioned IR derived from them).

## Stability guarantee (what “stable” means)

- The **meaning** of ABI fields evolves only via explicit, versioned changes.
- Additive changes are allowed (new optional fields).
- Breaking changes require a major version bump of the ABI/IR and an adapter compatibility update.

## Canonical ABI outputs

### 1) Master registry graph (required)

- **File**: `tooling/ontology/out/master_registry.json`
- **Produced by**: `tooling/ontology/registry_builder.py`
- **Role**: resolved object graph (Use Cases, KPIs, Action Codes) plus edges and issues.
- **Used for**:
  - adapter generation inputs (linked sets, governance, subscriptions)
  - trust/risk signals (e.g., data contract risk)
  - dependency analysis (edges)

### 2) Value map (required if impact paths are needed)

- **File**: `tooling/ontology/out/value_map.json`
- **Produced by**: `tooling/ontology/registry_builder.py`
- **Role**: impact-path linkage and causal links for UI/frontends and prioritization.

### 3) Stage 1 results (optional, but recommended for CI integration)

- **File**: `tooling/validation/results/latest_results.json`
- **Produced by**: `tooling/run_stage1_checks.ps1`
- **Role**: consolidated validation status consumed by registry/trust integration.

## Adapter boundary rule (hard)

Tool-specific products/adapters must treat `core/` as **data**, not as an API:

- ✅ Allowed: consume `master_registry.json` / `value_map.json` (and versioned IR derived from them).
- ✅ Allowed: consume `products/<tool>/…` local configuration and templates.
- ❌ Forbidden: implementing tool logic by directly scraping/parsing `core/` artifacts in an unversioned way.

Rationale: direct parsing creates silent coupling, breaks compatibility, and prevents safe AI-first automation.

## Versioning model

- **Core schema versions** live in the governed artifact schemas (e.g. `UseCase_Bracket.yaml` `schema_version: "2.0"`).
- The **Core ABI** is versioned independently (e.g. `core_abi_version: 1.x`), with a compatibility matrix per adapter.
- A future **IR (Intermediate Representation)** is treated as the adapter ABI and is derived deterministically from the registry outputs.

