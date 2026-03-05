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
# IR only (use_cases, kpis, action_codes from registry)
py -3 tooling/ir/build_ir.py

# IR + measure_spec for IR-first adapters (no direct Core reads by adapters)
py -3 tooling/ir/build_ir.py --kpi-catalog core/kpi_catalog

# With Fabric measure overlay (tool-agnostic core; DAX in products/fabric/powerbi/specs)
py -3 tooling/ir/build_ir.py --kpi-catalog core/kpi_catalog --fabric-overlay products/fabric/powerbi/specs/fabric_measure_overlay.yaml

# One-time: write current catalog DAX fields to overlay YAML
py -3 tooling/ir/build_ir.py --kpi-catalog core/kpi_catalog --write-fabric-overlay products/fabric/powerbi/specs/fabric_measure_overlay.yaml
```

Output (ignored by git): `tooling/ir/out/ir_v1.json`

When `--kpi-catalog` is provided, the script scans the KPI catalog for DAX/formats and adds a top-level `measure_spec` (kpi_id → dax_expression, format_string, dax_name, etc.). With `--fabric-overlay`, Fabric-specific fields are merged from the overlay (see tool-agnostic separation in `products/fabric/powerbi/docs/tool_agnostic_separation.md`). Adapters can then generate TMDL/measures from IR only.

## IR-first adapter flow

1. **Core ABI** (registry) is produced by ontology/tooling (Stage 1 and registry build).
2. **IR** is built with `build_ir.py --kpi-catalog core/kpi_catalog` so that `measure_spec` is populated.
3. **Adapter build** (e.g. Fabric `adapter_build.ps1`) calls the measure generator with `-IRPath tooling/ir/out/ir_v1.json`. The generator reads only IR (use cases + KPIs from orchestration, measure content from `measure_spec`); it does not read `core/usecases` or `core/kpi_catalog` directly.
4. Tool artifacts (e.g. `_Measures.tmdl`) are written to the adapter’s dist/output.

This keeps the boundary clear: Core → ABI/IR → Adapter; adapters do not parse Core artifacts.

