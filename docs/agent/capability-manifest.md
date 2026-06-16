# Capability Manifest (`aluca.capabilities.yaml`) — spec sketch

> **Decision record:** [`../architecture/adr/0003-customer-activation-and-capability-gating.md`](../architecture/adr/0003-customer-activation-and-capability-gating.md)
>
> **Status:** Proposed schema, **not yet wired**. This describes the single
> declarative file that governs agent activation (ADR-0003): the one thing the
> Studio writes and the one thing a security reviewer reads.

## Purpose

One file is the **allowlist** for everything an agent may do in this repo. The
`docs/agent/` generator consumes it and emits per-agent configs + MCP
registration **only for allowed capabilities**. Anything not listed is neither
generated nor active.

## Example (annotated)

```yaml
version: 1
profile: acme-finance              # customer/profile name (for audit)
target: powerbi                    # emit target: powerbi | metabase | superset | grafana

tiers:                             # ADR-0001 capability tiers
  tier0_floor: true                # always on (pure-Python); cannot be disabled
  tier1_oracle: false              # opt-in: official validate / authoring MCP
  tier2_desktop: false             # opt-in: Power BI Desktop bridge / live render

external:                          # ADR-0001 compliance mode (default off)
  allow_external: false            # no foreign binaries until explicitly true
  allow_network: false             # no outbound calls until explicitly true
  pin:
    skills-for-fabric: "x.y.z"     # pin upstream; snapshot preferred over deep-link

skills:
  official:                        # consumed from skills-for-fabric (only if listed)
    - semantic-model-authoring
    - power-bi-report-authoring
  overlay:                         # ALUCA governance deltas (the moat)
    - aluca-kpi-governance
    - aluca-3-30-300-pages
    - aluca-golden-thread

tools:
  mcp:
    powerbi-modeling:
      enabled: false               # least-privilege: off by default
      auth: entra                  # no implicit credentials

generate:                          # which agent configs the generator emits
  - AGENTS.md
  - CLAUDE.md
  - .github/copilot-instructions.md
  - .cursor/rules
  - .claude
```

## Generator flow

```
aluca.capabilities.yaml
        │
        ▼
docs/agent/ SSOT  ─►  generate_tool_configs.py (manifest-aware)
        │                       │
        │                       ├─► AGENTS.md / CLAUDE.md / .cursor / .github / .claude   (allowed skills+rules only)
        │                       └─► MCP registration                                       (only enabled tools)
        ▼
   `aluca doctor` reflects the resulting active tier/state
```

Rules the generator enforces:

- **`tier0_floor` is always emitted**; it is not togglable.
- **External capabilities are omitted unless `allow_external: true`** — a manifest
  with external off produces configs that reference no foreign binaries and make
  no outbound calls (clean security review by construction).
- **Only listed skills/tools are wired.** Adding a capability is an explicit edit;
  removing it and regenerating makes it disappear from every agent at once.
- **Cross-tool from one source:** the same manifest drives Claude Code, Copilot,
  Cursor, etc. — no per-agent drift.

## Why one file

- **Single audit surface** — security review reads the manifest, not N agent
  configs.
- **Deterministic** — configs are generated, never hand-edited (matches the
  existing `docs/agent/` AUTO-GENERATED convention).
- **Studio-writable** — the Studio is just a friendly editor over this file (see
  [`studio-activation-ux.md`](studio-activation-ux.md)); the manifest stays the
  source of truth.
