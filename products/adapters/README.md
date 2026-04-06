# Tool Adapters (Multi-Tool Architecture)

> **Rolle: Framework-Infrastruktur** — Dieser Ordner ist kein auslieferbares Produkt, sondern definiert den Vertrag (Schema + Konventionen), an den sich alle tool-spezifischen Adapter halten müssen. Er ist nicht Bestandteil des Fabric Showcases, wird aber aktiv von `products/fabric/powerbi/adapter.json` und `tooling/ir/` referenziert.

## Purpose

This folder defines the **adapter contract** for tool-specific implementations.

An adapter is a versioned package that:

- consumes the **Core ABI** / **IR** (not ad-hoc parsing of `core/`)
- builds tool artifacts into a deterministic `dist/`
- validates tool artifacts with tool-specific checks
- optionally deploys to an environment (with strict gates)

## Adapter contract (standard commands)

Each adapter must expose the same high-level commands:

- **build**: `build(ir) -> dist/` — Build consumes IR (and optionally Core ABI outputs). The reference Fabric adapter is **IR-first**: it runs `build_ir.py --kpi-catalog` to produce IR with `measure_spec`, then the measure generator reads only IR (`-IRPath`); no direct reads of `core/usecases` or `core/kpi_catalog` during build.
- **validate**: `validate(dist) -> report`
- **deploy**: `deploy(dist, env) -> audit log` (optional; gated)

Adapters declare their capabilities and compatibility in an **adapter manifest**.

## Manifest

- Schema: `products/adapters/adapter_manifest.schema.json`
- One manifest per adapter, stored within the adapter package (e.g. `products/<tool>/adapter/adapter.json`).

## Reference adapter

- `products/fabric_powerbi/` is the first reference tool product.

