# Guided Agent Development Workflow (GADW)

> **Decision record:** [`../architecture/adr/0002-official-first-agent-integration-and-guided-workflow.md`](../architecture/adr/0002-official-first-agent-integration-and-guided-workflow.md)
>
> This is the **executable skeleton** of the workflow ADR-0002 defines: a
> stage-gated path where each stage borrows its *mechanics* from a first-party
> vendor agent skill and hangs an **ALUCA governance gate** on the seam. It is
> tool-agnostic at the gate level and Power-BI-specific only where the vendor
> skill is.

## How to read this

Each stage has:

- **Skill (mechanics)** — the official `skills-for-fabric` skill (or MCP/tool)
  that does the work. Opt-in (Tier-1/2 per ADR-0001).
- **ALUCA gate** — the always-on Tier-0 check that must pass *before the stage
  is considered done*. These are existing ALUCA commands/hooks; nothing here is
  new code, only sequencing.
- **Exit criterion** — the objective signal that gates the next stage.

If a vendor skill is unavailable (air-gapped / no Node), the stage falls back to
ALUCA's own generator (`generator_core` / `page_scaffold_generator`); the gate is
identical. **The gates are the contract; the mechanics are pluggable.**

---

## Entry — repo reading order (before any stage)

The workflow runs inside the repo's navigation discipline
([`../NAVIGATION_PHILOSOPHY.md`](../NAVIGATION_PHILOSOPHY.md)). Before Stage 0 the
agent enters **top-down — never scan folders**:

1. `GOI_DOKTRIN.md` (how to work) → `CLAUDE.md` (project rules + Bereichs-Landkarte).
2. Task type → open the area `_INDEX.md` ([`_INDEX.md`](_INDEX.md) for agent work,
   [`../architecture/_INDEX.md`](../architecture/_INDEX.md) for the ADRs) → follow its
   „lies-wenn" row to the 1–2 detail docs.
3. Read the relevant **ledger** first (what is already decided?); on completion tick
   it off **in the same step** and keep `check_index.py --strict` green.

Only then proceed to Stage 0.

## Stage 0 — Use Case (contract)

| | |
|---|---|
| **Skill (mechanics)** | — (human/agent authors `UseCase_Bracket.yaml`) |
| **ALUCA gate** | `aluca preflight` — KPI catalog binding, Golden Thread, `primary_kpi_ids`, action-code references |
| **Exit criterion** | preflight green for the use case (no missing KPI ids, no dangling action codes) |

The bracket is the single source of truth. No downstream stage runs against a
bracket that fails preflight.

## Stage 1 — Plan

| | |
|---|---|
| **Skill (mechanics)** | `power-bi-report-planner` (MS guided workflow) |
| **ALUCA gate** | Inject the 3-30-300 page spec (`core/templates/page_templates/Design_Spec_3_30_300.md`) and the use case's **decision spine** (`core/action_codes/decision_spines/`) as planning constraints |
| **Exit criterion** | A plan whose pages/visuals map to bracketed KPIs and the decision spine — no orphan visuals, no KPI without a home |

The vendor planner proposes layout; the ALUCA gate constrains it to governed
KPIs and the decision logic, so the plan is *accountable to the use case*.

## Stage 2 — Model (semantic model)

| | |
|---|---|
| **Skill (mechanics)** | `semantic-model-authoring` + Power BI Modeling MCP |
| **ALUCA gate** | TMDL hard-rules hook (`.claude/hooks/validate_tmdl_style.sh`: no tabs, no `:=`, no `description:`) + catalog↔TMDL drift check |
| **Exit criterion** | Model builds; every catalog KPI has a corresponding measure; drift check clean |

ALUCA does **not** re-teach the agent how to write TMDL/DAX — the vendor skill
does. ALUCA enforces the star-schema/naming policy and that the model stays
faithful to the governed KPI catalog.

## Stage 3 — Report (PBIR)

| | |
|---|---|
| **Skill (mechanics)** | `power-bi-report-authoring` (+ `power-bi-report-design`) |
| **ALUCA gate** | `validate_pbir_structure.sh` hook + `page_scaffold_generator/visual_validator.py` (queryState roles, no-data-role guard, bindings) + report-binding existence |
| **Exit criterion** | PBIR structurally valid; visuals bound to real measures; 3-30-300 layout honored |

This is the stage where the data-goblin "adopt" list (rename-cascade,
pbir-structure, visual formatting) is now **borrowed from the vendor** instead
of hand-maintained.

## Stage 4 — Validate

| | |
|---|---|
| **Skill (mechanics)** | MS PBIR `validate` + Desktop Bridge (Tier-1/2 oracle) |
| **ALUCA gate** | Tier-0 floor always on: `tooling/report_quality/` (`pbi-quality validate`), schema gates |
| **Exit criterion** | Tier-0 floor: 0 criticals. If the oracle is present, its findings are *additive*, never a substitute for the floor |

Straight out of ADR-0001: the official validator is the opt-in oracle; the
Python floor is the deterministic, offline guarantee.

## Stage 5 — Prep-for-AI

| | |
|---|---|
| **Skill (mechanics)** | `semantic-model-authoring` AI-readiness path |
| **ALUCA gate** | `linguistic_schema.py` (synonyms / Q&A surface) + lineage completeness |
| **Exit criterion** | Linguistic schema present and consistent with the catalog; lineage resolvable end-to-end |

"Prep your data for AI" (Microsoft's term) maps onto ALUCA's existing
linguistic-schema + lineage work — the place where the governed semantics pay
off for downstream Copilot / data-agent consumption.

---

## Fallback matrix (deployability)

| Environment | Stages 1–3 mechanics | Stage 4 oracle | Gates |
|---|---|---|---|
| Microsoft-first, Node permitted | `skills-for-fabric` skills + MCP | MS validate / Desktop | unchanged |
| Locked-down / air-gapped / no Node | ALUCA `generator_core` / `page_scaffold_generator` | Tier-0 floor only | unchanged |

The right-hand column never changes. That is the whole point: **swapping the
execution layer does not change what "done" means.**

## Gate command (bundled Tier-0)

The always-on gates run as one command — `python3 scripts/gadw_gate.py`:

| Gate | Stage | Check |
|---|---|---|
| Navigation | — | `check_index.py --strict` (index/ledger drift) |
| Use Case | 0 | `aluca preflight` (KPI catalog / Golden Thread) |
| Validate | 4 | `pbi-quality validate` (report-quality Tier-0 floor) |

Per-stage PASS/FAIL, non-zero exit if any gate fails (`--verbose` shows each
gate's output). This is the **fast, offline dev-loop gate**; the heavier Stage-1
governance + Fabric quality gate (PowerShell) stays the full CI gate. The
right-hand "Gates" column of the fallback matrix above *is* this command —
unchanged across environments.

## Open items (tracked in ADR-0002)

- Add a `skills-for-fabric`-compatible **target** to the `docs/agent/` generator
  so ALUCA overlay skills emit in the official `SKILL.md` shape.
- Pin the upstream `skills-for-fabric` version and schedule a quarterly
  re-review (the data-goblin review's cadence note still applies).
- Decide which existing ALUCA skill docs are now **retired in favor of upstream**
  (the data-goblin "adopt" mechanics) vs. **kept as overlay** (governance).
