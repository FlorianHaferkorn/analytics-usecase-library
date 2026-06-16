# ADR 0003 — Customer Activation and Capability-Gating

- **Status:** Proposed
- **Date:** 2026-06-16
- **Scope:** How customers activate agent skills/tools securely; the onboarding surface
- **Supersedes:** —
- **Related:** [`0001-pluggable-validation-backends-and-capability-tiers.md`](0001-pluggable-validation-backends-and-capability-tiers.md), [`0002-official-first-agent-integration-and-guided-workflow.md`](0002-official-first-agent-integration-and-guided-workflow.md), [`../../agent/capability-manifest.md`](../../agent/capability-manifest.md), [`../../agent/studio-activation-ux.md`](../../agent/studio-activation-ux.md)

---

## Context

[ADR-0002](0002-official-first-agent-integration-and-guided-workflow.md) decides
*what* we integrate (official skills/tools as the execution layer, ALUCA as the
overlay). It does not answer *how a customer turns it on safely*.

The official tooling is activated through **developer-centric** mechanisms:
install a CLI plugin, run `/skills` slash commands, hand-edit agent config files,
register MCP servers. That is fine for our engineers. It is **not** a
customer-facing onboarding path:

- **Many customers are non-technical.** Slash commands and manual config editing
  are unfamiliar, intimidating, and error-prone for them. Slash commands are an
  acceptable *power-user* affordance, not a *customer* affordance.
- **"Activate the agent" must not mean "turn on arbitrary external tools."** An
  activation model that silently enables MCP servers, foreign binaries, or
  outbound calls fails security review and breaks ADR-0001's compliance posture.
- **Activation must be consistent across agents** (Claude Code, GitHub Copilot,
  Cursor, …) without N hand-maintained config sets that drift.

We already own two assets that make a better model possible: the `docs/agent/`
**SSOT generator** (canonical Markdown + `_index.yaml` → tool configs) and the
**Studio** web app.

## Decision

**Activation is repo-config-driven, governed by a single capability manifest, and
operated through the Studio. Slash commands remain an optional power-user path —
never the customer path.**

Five rules:

1. **The repo is the activation surface.** Capabilities are activated by config
   files that agents auto-load — `AGENTS.md`, `CLAUDE.md`,
   `.github/copilot-instructions.md`, `.cursor/rules/*`, and MCP registration.
   *Opening the repo in an agent is the activation.* There is nothing to type.
2. **One manifest governs everything.** A single `aluca.capabilities.yaml`
   declares the allowed skills, tools, tiers, and emit target. The `docs/agent/`
   generator emits config **only** for allowed capabilities. A security reviewer
   reads one file. (Spec: [`../../agent/capability-manifest.md`](../../agent/capability-manifest.md).)
3. **Default-off, opt-in, auditable.** Inherits ADR-0001 compliance mode:
   external tools / MCP / network are off until explicitly enabled in the
   manifest; `doctor` reports the resulting active tier. Enabling is a deliberate,
   logged change.
4. **The Studio is the human control panel.** Non-technical users flip
   plain-language toggles in the Studio; the Studio writes the manifest and runs
   the generator. They never see YAML or a slash command. (UX:
   [`../../agent/studio-activation-ux.md`](../../agent/studio-activation-ux.md).)
5. **One-command bootstrap for setup.** Initial provisioning uses `aluca init` /
   a template repo ("Use this template") that lands a wired, agent-ready repo with
   safe defaults — done once by an admin/consultant, not the end user.

## Activation layers

| Layer | Who | Mechanism | Frequency |
|---|---|---|---|
| **Bootstrap** | admin / consultant | `aluca init` or template repo | once per repo |
| **Operate** | non-technical customer | Studio toggles → manifest → generator | ongoing |
| **Power-user** | engineer | edit manifest / use slash commands directly | as needed |

Each lower layer is a thin convenience over the same manifest; they never
diverge because they all write the **one** source of truth.

## Security model

- **Capability allowlist:** the manifest is an allowlist, not a denylist —
  anything not listed is not generated and not active.
- **Default-off external:** ADR-0001 compliance mode is the floor; enabling
  Tier-1/2 (official CLI, MCP, Desktop) is explicit and auditable.
- **Pinned + vendored upstream:** pin the `skills-for-fabric` version; prefer the
  ADR-0001 snapshot pattern over live upstream; no raw deep-links.
- **Least privilege:** MCP servers scoped and off by default; Entra-auth for
  remote; no outbound unless `allow_network`.
- **Always legible:** `doctor` reflects the active state so activation is never a
  silent surprise; the manifest is the single audit artifact.

## Consequences

**Positive**
- Non-technical customers can activate/limit capabilities without CLI or slash
  commands; security reviewers audit one file.
- Cross-agent by construction (one manifest → all agent configs).
- Reuses existing assets (the `docs/agent/` generator and the Studio) rather than
  new surface.

**Negative / cost**
- The Studio must grow into the activation control surface (product work).
- The generator must become manifest-aware and gain the ADR-0002 targets
  (`skills-for-fabric` / Copilot / MCP registration).
- A template/bootstrap and the upstream pin become standing maintenance.

**Neutral**
- Slash commands and direct manifest edits remain for engineers — demoted from
  "the way" to "a way."

## Alternatives considered

- **Slash commands / manual config as the customer path.** Rejected: unfriendly
  to non-technical users, error-prone, and no central audit surface.
- **Fully managed/hosted activation (we flip it server-side).** Deferred: many
  customers require activation inside their own repo/tenant, and a hosted-only
  model conflicts with the air-gapped Tier-0 guarantee.
- **One hand-maintained mega-config per agent.** Rejected: N configs drift; the
  SSOT + manifest collapse them to a single generated source.

## References

- Internal: [`0001-pluggable-validation-backends-and-capability-tiers.md`](0001-pluggable-validation-backends-and-capability-tiers.md),
  [`0002-official-first-agent-integration-and-guided-workflow.md`](0002-official-first-agent-integration-and-guided-workflow.md),
  [`../../agent/capability-manifest.md`](../../agent/capability-manifest.md),
  [`../../agent/studio-activation-ux.md`](../../agent/studio-activation-ux.md),
  [`../../agent/README.md`](../../agent/README.md)
