# Intermediate Representation (IR)

## Purpose

The IR is the **stable adapter ABI** between the tool-agnostic Core SSOT and tool-specific products/adapters.

It is derived **deterministically** from the Core ABI outputs:

- `tooling/ontology/out/master_registry.json`
- `tooling/ontology/out/value_map.json`

Adapters should consume the IR (not scrape `core/` directly).

## Versioning

- IR is versioned via `ir_version` (SemVer-like string, starting with `1.0`).
- Additive changes are allowed (new optional fields).
- Breaking changes require a new major IR version and adapter compatibility updates.

## Schema

- Canonical schema: `tooling/ir/schemas/ir_v1.schema.json`

## Build (deterministic)

From repo root (after running Stage 1 / registry once so ABI outputs exist):

```powershell
py -3 tooling/ir/build_ir.py
```

Output (ignored by git): `tooling/ir/out/ir_v1.json`

