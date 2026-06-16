# ADR 0002 — Official-First Agent Integration and the Guided Agent Development Workflow

- **Status:** Accepted
- **Date:** 2026-06-16
- **Scope:** Agent skills/tools strategy; how ALUCA consumes first-party vendor agent tooling
- **Supersedes:** —
- **Related:** [`0001-pluggable-validation-backends-and-capability-tiers.md`](0001-pluggable-validation-backends-and-capability-tiers.md), [`0003-customer-activation-and-capability-gating.md`](0003-customer-activation-and-capability-gating.md), [`../prior-art-agentic-integration-and-migration.md`](../prior-art-agentic-integration-and-migration.md), [`../../agent/README.md`](../../agent/README.md), [`../../agent/guided-agent-development-workflow.md`](../../agent/guided-agent-development-workflow.md)

---

## Context

When [ADR-0001](0001-pluggable-validation-backends-and-capability-tiers.md) was
written, the official agent tooling for Power BI was an *emerging* signal:
preview CLIs and community plugins (for example
`data-goblin/power-bi-agentic-development`, assessed in
`REVIEW_DATA_GOBLIN_POWER_BI_AGENTIC_DEV.md`). ADR-0001 therefore framed every
external tool as an **optional oracle, never a hard dependency**, with a
pure-Python Tier-0 floor that stays complete offline.

Since then the ground has shifted. Microsoft has shipped a **first-party**
agent offering — **Power BI Agentic** via the **Skills for Fabric** marketplace
(`microsoft/skills-for-fabric`):

- It is **not a feature you turn on**; it is a curated bundle of **agent
  skills** (instructions + scripts) and **tools** (MCP servers + CLI bridges)
  you install *into your agent*.
- It is optimized for **GitHub Copilot CLI** but ships **cross-tool
  compatibility shims for Claude Code, Cursor, VS Code Copilot, Codex/Jules,
  and Windsurf**.
- It already includes the building blocks we were planning to build ourselves:
  `semantic-model-authoring`, `power-bi-report-authoring`,
  `power-bi-report-design`, `power-bi-report-management`, and — notably — a
  **guided** workflow skill, `power-bi-report-planner` ("define, plan, and
  build a new report from an existing semantic model"). The execution layer is
  the **Power BI Modeling MCP server** plus the **Desktop Bridge**.

This validates ADR-0001's core instinct but inverts the economics. The PBIR /
TMDL **authoring mechanics** — exactly the "adopt" list in the data-goblin
review (`rename-cascade`, `pbir-structure`, visual examples, formatting rules)
— are now maintained first-party by the vendor. Continuing to hand-maintain our
own copies of that mechanics layer is now the *expensive* path, and it drifts
against an emerging official standard.

What the official tooling does **not** provide is everything that makes ALUCA
ALUCA: governed KPI semantics, the `UseCase_Bracket.yaml` contract, the Golden
Thread / lineage, 3-30-300 page specs, decision spines, and — above all — a
**tool-agnostic intermediate representation** that can target Power BI *or*
Metabase / Superset / Grafana. The official skills are Power-BI-shaped; ALUCA's
value is tool-shaped-agnostic.

## Decision

**Adopt an "official core, ALUCA overlay" posture: consume first-party vendor
agent skills/tools as the execution layer, and contribute only ALUCA's
differentiated deltas as an overlay on top — never a parallel reimplementation.**

Three rules govern the design:

1. **Mechanics are borrowed, governance is ours.** Where a first-party skill
   covers authoring mechanics (PBIR structure, TMDL editing, DAX, visual
   formatting, validation, live render), ALUCA **consumes it** and stops
   maintaining a competing copy. ALUCA contributes only what the vendor does
   not: KPI-catalog governance, `UseCase_Bracket.yaml`, Golden Thread / lineage,
   3-30-300 page specs, decision spines, preflight gates.
2. **Extend, never fork.** ALUCA deltas are emitted **alongside** the official
   skills in the official `SKILL.md` format, not as edits to them. The existing
   `docs/agent/` SSOT generator (canonical Markdown + `_index.yaml` → tool
   configs) gains a **`skills-for-fabric`-compatible target** so the overlay is
   produced mechanically and stays a thin, reviewable diff against upstream.
3. **The Tier-0 floor from ADR-0001 stays.** Official skills/MCP are Tier-1/2
   (opt-in). The pure-Python floor (`tooling/report_quality/`, the `.claude`
   hooks, schema gates, `aluca preflight`) remains the always-on default so
   locked-down, air-gapped, and no-Node customers lose nothing. "Official-first"
   is about *where authoring mechanics come from*, not about making the vendor a
   hard dependency.

This is ADR-0001's tier model, re-pointed: the vendor now *is* the Tier-1
oracle, shipped first-party, and we wrap it instead of racing it.

## Three-layer architecture

| Layer | Owner | Contents |
|---|---|---|
| **Execution** | Microsoft (first-party) | `skills-for-fabric` skills + Power BI Modeling MCP + Desktop Bridge — authoring mechanics, DAX, PBIR validation, live verification |
| **Overlay (ALUCA delta)** | ALUCA | KPI-catalog governance, `UseCase_Bracket.yaml`, Golden Thread / lineage, 3-30-300 page specs, decision spines, preflight gates — emitted as overlay skills/rules from `docs/agent/` |
| **Tool-agnostic core** | ALUCA | `generator_core` IR (BracketCompiler → DashboardSpec → adapters), `products/oss_adapters/` (Metabase/Superset/Grafana), and the **Studio** |

The overlay is the seam. The execution layer is replaceable (today Power BI;
tomorrow another vendor's first-party agent); the tool-agnostic core is what
makes that replaceability real and is therefore the asset we invest in.

## The Guided Agent Development Workflow (GADW)

The integration is operationalized as a **stage-gated workflow** that wraps the
official skills and hangs an ALUCA governance gate on each seam. The vendor skill
supplies the *mechanics* of each stage; ALUCA supplies the *gate* before/after.
The executable detail lives in
[`../../agent/guided-agent-development-workflow.md`](../../agent/guided-agent-development-workflow.md);
in summary:

```
0  Use Case        UseCase_Bracket.yaml        ALUCA gate: aluca preflight (KPI catalog, Golden Thread)
1  Plan            power-bi-report-planner      MS guided; ALUCA injects 3-30-300 page specs + decision spine
2  Model           semantic-model-authoring     MS; ALUCA gate: TMDL hard-rules hook + catalog↔TMDL drift
3  Report          power-bi-report-authoring    MS; ALUCA gate: visual_validator + report-binding + layout
4  Validate        MS PBIR validate / Desktop   MS Tier-1/2 oracle (ADR-0001); ALUCA Tier-0 floor always on
5  Prep-for-AI     semantic-model AI-readiness  MS; ALUCA: linguistic_schema / synonyms / lineage
```

## Prior art

The "consume official, generate the overlay down to each tool" pattern is
well-trodden (full notes + sources:
[`../prior-art-agentic-integration-and-migration.md`](../prior-art-agentic-integration-and-migration.md)).
Microsoft's `skills-for-fabric` already auto-generates per-tool shims
(`CLAUDE.md`, `.cursorrules`, `AGENTS.md`, `.mcp.json`) from one bundle; the open
**Agent Skills** standard (`agentskills.io`) keeps skills portable; and
single-source → many-agent generators (`ruler`, `rulesync`, `npx skills`) already
do exactly what the `docs/agent/` generator does. So this is a build-vs-buy
decision, not a green-field build. **Decision (2026-06-16): adopt — evaluate
`ruler`** as the overlay generator (single canonical source → per-tool configs,
emits `.mcp.json`, `--check`-style drift gate that composes with `check_index.py`)
rather than hand-maintaining a bespoke one; the differentiator is the overlay
*content*, not the generator. Guardrail: a short spike must confirm `ruler` covers
our targets (`.claude`, `.cursor`, `.github/copilot-instructions.md`, `AGENTS.md`)
and keeps ADR-0001's default-off posture before it is wired in.

**Spike result (2026-06-16): confirmed.** `ruler apply` selects our targets
(`agentsmd`, `claude`, `copilot`, `cursor`; per-agent `output_path` configurable —
copilot → `.github/copilot-instructions.md`) and applies no MCP when no
`[mcp_servers]` are defined (`--no-mcp`), so the default-off posture holds; a
`--dry-run` wrote nothing. A `.ruler/ruler.toml` scaffold (default-off) is committed.
**Implemented (2026-06-16): shim-only.** Finding: the major agents (Copilot,
Cursor, Codex, Gemini, Windsurf, Zed, Kilo, Roo, …) already read **`AGENTS.md`**,
which this repo hand-authors — so they need no shim. `ruler` is therefore wired
for the **long-tail agents with distinct native config files** only (Cline,
Amazon Q, Crush, Goose, Junie, Kiro, Warp, Trae, Firebase, OpenHands, Augment,
Antigravity, Firebender); their generated shims (in `.ruler/00-canonical.md`)
point back to `AGENTS.md` / `docs/agent/` and are **git-ignored**
(`npx @intellectronica/ruler apply --no-mcp`). `AGENTS.md`, `CLAUDE.md`, and
`generate_tool_configs.py` are untouched. A **full cutover** (ruler owning
`AGENTS.md`/`CLAUDE.md`) was **deliberately not taken** — it would overwrite the
SSOT that the ecosystem standard (`AGENTS.md`) already uses.

## Consequences

**Positive**

- We stop maintaining the authoring-mechanics layer the vendor now owns, and
  redirect that effort to the governance + tool-agnostic core that is our moat.
- Lower drift risk: the overlay is a thin, reviewable diff against an official
  standard rather than a full parallel stack.
- Cross-tool reach for free: `skills-for-fabric` already ships Claude Code /
  Cursor / VS Code shims, so the overlay rides the vendor's distribution.
- ADR-0001's deployability guarantee is preserved: Tier-0 floor stays default.

**Negative / cost**

- We take a soft dependency on the cadence and stability of a vendor preview;
  the overlay generator and a periodic upstream re-review become standing work.
- Two formats to keep in sync (canonical `docs/agent/` Markdown → official
  `SKILL.md`); the generator target (`generate_official_skills()`) now bridges
  them mechanically, so this is a standing generate-and-check cost, not manual sync.
- Mapping ALUCA gates onto vendor stage boundaries assumes those boundaries stay
  reasonably stable; skill renames upstream will require overlay updates.

**Neutral**

- The data-goblin community review is now **partially superseded** by the
  first-party offering; it is retained as historical context with a forward
  banner, not deleted.
- Node 20 remains an opt-in toolchain (Tier-1/2), never a base requirement.

## Alternatives considered

- **Keep building ALUCA's own full agent stack (status quo / data-goblin
  adoption).** Rejected: duplicates mechanics the vendor now maintains
  first-party, and guarantees ongoing drift against the official standard.
- **Adopt the vendor wholesale and drop the ALUCA layer.** Rejected: discards
  the governance + tool-agnostic IR that is the entire differentiator and the
  basis for migration (see below). It would also re-introduce a hard external
  dependency that ADR-0001 explicitly avoids.
- **Wait until the preview stabilizes.** Rejected as a *default*: the overlay
  posture is low-cost and reversible, and waiting cedes the cross-tool
  distribution advantage. We do, however, treat upstream as preview (pin,
  re-review, do not deep-link).

## Migration corollary

The same tool-agnostic core that enables "official core, ALUCA overlay" also
makes ALUCA a **migration hub**. "Rebuild a Tableau dashboard in Power BI
without code" is a special case of *model once, generate many*: ingest a source
artifact into the ALUCA IR, then emit to any target (Power BI via the official
skills, or Metabase/Superset/Grafana via `oss_adapters`). The value is not in
the target tool (which is becoming commodity as vendors generate agentically) but
in the governance-bearing IR + Studio that survive the migration. The concrete
reverse-adapter sketch is captured separately in
[`../migration-ingest-adapter.md`](../migration-ingest-adapter.md).

## References

- Microsoft Learn — [Power BI Agentic overview](https://learn.microsoft.com/power-bi/developer/agentic/power-bi-agentic-overview)
- Microsoft Learn — [Power BI Report Authoring skill](https://learn.microsoft.com/power-bi/developer/agentic/power-bi-report-authoring-skill-overview)
- `microsoft/skills-for-fabric` marketplace (first-party agent skills for Fabric)
- Internal: [`0001-pluggable-validation-backends-and-capability-tiers.md`](0001-pluggable-validation-backends-and-capability-tiers.md),
  `REVIEW_DATA_GOBLIN_POWER_BI_AGENTIC_DEV.md` (historical, partially superseded),
  [`../../agent/README.md`](../../agent/README.md)
