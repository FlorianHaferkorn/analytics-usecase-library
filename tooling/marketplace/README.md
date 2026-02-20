# Internal MCP / Adapter Marketplace (Design)

## Purpose

Provide an **internal, allowlisted registry** for:

- **MCP servers** (tool integrations / ops endpoints)
- **Tool adapters** (build/validate/deploy packages for specific BI/analytics tools)

This is intentionally **internal** (not shipped to customers).

## Why internal (not public)

The official MCP Registry is designed for publicly accessible servers and metadata. For enterprise-private servers, the recommended approach is a **private registry** that implements the same OpenAPI surface.

## Registry data model

### A) MCP server metadata (`server.json`)

Use the MCP Registry `server.json` format for MCP server discovery and installation instructions:

- server name (reverse-DNS namespace)
- package locator (npm/pypi/docker/remote)
- execution instructions (command/env)

### B) Adapter metadata (`adapter.json`)

Adapters additionally provide an ActionReady adapter manifest:

- schema: `products/adapters/adapter_manifest.schema.json`
- stored at: `products/<tool>/adapter.json` (within the adapter package)

## Minimal API (OpenAPI-compatible)

Implement the same coarse endpoints as the official MCP Registry, plus internal curation:

- `GET /v0/servers` (list MCP servers)
- `GET /v0/servers/{name}` (server detail)
- `GET /v0/adapters` (list adapters; allowlist curated)
- `GET /v0/adapters/{adapter_id}` (adapter detail + versions)
- `POST /v0/adapters/{adapter_id}/pin` (pin version per environment)
- `POST /v0/adapters/{adapter_id}/rollback` (rollback to last known good)

## Curation & governance (mandatory)

- **Allowlist**: only approved adapters/servers are exposed to host applications.
- **Ownership**: each adapter has owner/steward roles and an escalation path.
- **Lifecycle**: draft → active → deprecated (adapter level).
- **Compatibility matrix**: adapter version declares supported IR/Core ranges; registry enforces.

## Supply chain & security (mandatory)

- **Signing**: every adapter/MCP package must be signed; registry verifies signatures.
- **SBOM/attestations**: store SBOM references and build provenance.
- **Secrets**: never in metadata; resolved by runner from secret store.
- **Permissions**: least-privilege declarations in adapter manifest; enforced by runner.
- **Audit trail**: every install/update/deploy emits immutable audit events.

## Execution model (AI-first compatible)

Host applications (agents) must:

1. Resolve adapter/server from registry (allowlist)
2. Install pinned version
3. Execute standard commands (`build`, `validate`, optional `deploy`) through a runner
4. Block on gates; produce review artifacts for human approval

## Relation to this repository

- Core ABI: `core/strategy_operating_model/operating_model/reference/core_abi.md`
- IR: `tooling/ir/` (schema + builder)
- Adapter manifests: `products/*/adapter.json`

