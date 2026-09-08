# Project architecture compilation

Status: implemented bounded increment. Date: 2026-09-07.

## Decision

The Studio architecture reads the same immutable Project Package revision as the engagement, decisions and release surfaces. Python validates and compiles it. The UI does not reconstruct customer architecture from Library examples.

The existing general `derive_blueprint` and Fabric architecture adapter were evaluated. They are useful for Library scaffolding, but currently invent default workspace names, ingestion choices and serving assumptions. They are not safe as an implicit compiler for customer-approved inputs. Their global behavior remains unchanged.

## Inputs and views

- `architecture_input` records domain, capacity, environment and contract scope.
- `use_case_delivery` provides explicit sources, products, transformations, analytical design, controls, orchestration and acceptance gates.
- Graph node labels retain authored identifiers. Edges come only from `source_refs`, `input_refs` and `output_refs`.
- Canonical, fallback and excluded sources retain their boundary status. Reference reports remain reference reports, not assumed target report/semantic-model bindings.
- Missing contracts are blockers, not generated defaults. No automatic DEV/TEST/PROD replication is inferred from one source-level contract.

The existing use-case delivery document renderer generates the detailed architecture specifications, including rationale, controls and open gates. JSON includes exact details and provenance so visualization and output share one compilation.

## Generated outputs

1. `architecture_bundle`: graph, compiler/input provenance, existing use-case architecture specifications and hash inventory.
2. `fabric_workspace_requests`: native Fabric Create Workspace JSON request bodies for only the explicit `architecture_input.physical_workspaces` array. This is an optional backward-compatible schema extension; no existing package is modified.

Each workspace must supply its exact name, domain reference, accepted environment, capacity UUID, domain UUID and approved decision references. Missing, unresolved, unapproved or unsupported inputs block this target. This output does not create the remaining project resources, apply security or implement CI/CD.

[Microsoft Create Workspace reference](https://learn.microsoft.com/en-us/rest/api/fabric/core/workspaces/create-workspace) was checked on 2026-09-07. The generated body uses `displayName`, `capacityId`, `domainId` and optional `description`. An executor must separately authenticate, resolve/verify IDs, detect existing workspaces, obtain tenant apply approval and retain response evidence. No executor or tenant write was introduced.

## Authority and API

- GET `/api/projects/{projectId}/architecture?revision={hash}` requires project viewer access. Omitted revision resolves once to HEAD and returns its hash. Responses are private/no-store.
- POST requires editor access and `{revisionHash, target, confirmGeneration: true}`. It consumes an **existing** release attestation; it cannot grant one.
- Python's existing release function requires the selected revision still be HEAD, approved inputs, approved decisions and a hash-valid attestation. Unsupported targets fail closed.
- Returned downloadable JSON contains named file contents and their SHA-256 manifest. It is not a ZIP, executable deployment or tenant acceptance certificate.

## Remaining boundary

Source/product contracts are not complete physical Fabric item definitions. A full tenant compiler still needs explicit item payloads, environments, dependency bindings, identities, policies, CI/CD, idempotent apply/rollback and runtime evidence adapters. `apply_ready` is always false for this increment. E2E delivery remains the product destination; this increment connects the architecture and a bounded native target output without claiming that destination has been reached.

## Verification

Python tests cover deterministic exact graph derivation, dangling/colliding references, foreign project rejection, workspace schema constraints, target gates, exact native bodies, hash inventory and real repository/attestation behavior. Studio route tests cover authentication before loading, revision pinning, confirmation, output scope and blocked generation without fallback.
