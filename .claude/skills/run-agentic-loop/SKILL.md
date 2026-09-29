---
name: run-agentic-loop
description: "Run the agentic loop S0-S7 (spec, model, report, sandbox, DAX runtime, render, image checks, teardown) through one command. Use when validating a use case end to end or preparing a tenant run."
version: "1.0.0"
license: MIT
source: ALUCA (Analytics Library of Use Cases) — governance overlay
---

<!-- AUTO-GENERATED from docs/agent/skills/ — do not edit; run tooling/generator/generate_tool_configs.py -->

# Run the Agentic Loop (S0–S7)

One entry point for the loop in `UMSETZUNGSPLAN_AGENTIC_LOOP.md`: specification → model → report →
sandbox → DAX runtime → render → image checks → teardown. The command orchestrates existing tools
only; fixes never go into rendered artifacts.

## Workflow

1. **Dry run first** (default; no tenant call, exit 2 names what could not run):
   ```bash
   python -m tooling.agentic_loop.schleife --use-case OPS-001 --run-id run-0001
   ```
   Read `out/agentic_loop/<run-id>/befunde.json`. Local stages S0–S2 must be `ok`.
2. **Local stages only** while iterating on a bracket, generator or rule:
   ```bash
   python -m tooling.agentic_loop.schleife --use-case OPS-001 --run-id run-0001 --stages S0,S1,S2
   ```
3. **Tenant run** only with `--apply` and `FABRIC_TENANT_ID`/`FABRIC_CLIENT_ID`/`FABRIC_CLIENT_SECRET`
   set in the environment (never in files). Always end with S7; check the manifest shows `deleted_at`.

## Exit codes

- `0` — every selected step ran and passed
- `1` — at least one finding (a finding outranks "not checkable")
- `2` — nothing failed, but at least one step could not run (dry run, missing credentials,
  not yet built, no Meridian checkout); the reason is in `grund`

## What the agent may do

- **S0:** draft or edit a bracket, then re-run S0.
- **S4–S6:** read findings and propose a fix as a diff against the bracket, a generator under
  `tooling/`, or a rule. Findings of the LLM judge are advisory only (E5).
- **Never** edit `products/fabric/powerbi/dist/` or gold data by hand; regenerate through the
  generator that owns them (Rückflusspflicht).
- **Never** skip S7 after an `--apply` run, and never point a step at a workspace that is not the
  one in the run manifest (the sandbox refuses it anyway).

## Not built yet (reported as "not checkable")

Loading the data slice into a lakehouse (AP-3), the dataset and report IDs from the deploy (needed
by S4 and S5), and the reference crop for the error-state check (AP-5).
