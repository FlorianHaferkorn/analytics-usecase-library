# Agent setup — roles, experts, workday

**Purpose:** Overview of the agent workflow, roles, expert rules, and workday control. Use this after the GitHub Project and backlog are in place (see [SETUP_CHECKLIST.md](SETUP_CHECKLIST.md), [WHAT_I_NEED.md](WHAT_I_NEED.md)).

---

## Roles

| Role | When | What |
|------|------|------|
| **Implementer** | Working on an assigned GitHub Issue | Follows [.cursor/rules/agent-workflow.mdc](../../.cursor/rules/agent-workflow.mdc): workday check, skill selection, branch, Stage 1, PR. |
| **Reviewer** | Reviewing a PR | Same rules and skills; use a separate Cursor session with a prompt like "Review this PR against .cursor/rules and the relevant skills; check Stage 1 compliance." |
| **PM (Project Manager)** | Prioritization, intake, integration | Use [.cursor/rules/pm-agent.mdc](../../.cursor/rules/pm-agent.mdc) in a dedicated session. Input: BACKLOG_GRANULAR, project status, or new requirements. Output: prioritized next tasks; or intake of new ideas into [IDEAS_AND_REQUIREMENTS.md](IDEAS_AND_REQUIREMENTS.md) and optional issue body for manual creation. May only edit `internal/project_mgmt/` and backlog docs in `tooling/project_mgmt/`. |

---

## Experts (context by area)

Experts are implemented as Cursor rules with globs; the agent workflow routes by Area and path.

| Expert | Scope | Rule | When to use |
|--------|-------|------|-------------|
| **Framework** | core/, tooling/ir/, data_contracts/, tooling/validation/, tooling/ontology/ | [.cursor/rules/framework-expert.mdc](../../.cursor/rules/framework-expert.mdc) | Area: Framework, Docs (framework topics). No TMDL, DAX, or other tool syntax. |
| **Fabric** | products/fabric_powerbi/ | [.cursor/rules/fabric-expert.mdc](../../.cursor/rules/fabric-expert.mdc) | Area: FabricPowerBI. TMDL, DAX, run_fabric_checks. |
| (Future tools) | products/&lt;tool&gt;/ | .cursor/rules/&lt;tool&gt;-expert.mdc | Add one rule per adapter when you add Tableau, Looker, etc. |

Skills (e.g. edit-factsheet-safely, fabric-powerbi-validation) are listed in the workflow rule and in each expert rule.

---

## Workday (start/end)

Agents may only **start new implementation** when the workday is **open**. You control this with a marker file and two scripts.

| State | Meaning | How |
|-------|---------|-----|
| **Open** | Agents may accept new work | File `internal/project_mgmt/AGENT_WORKDAY_OPEN` exists. |
| **Closed** | No new work; running sessions may finish | File removed. |

**Scripts (from repo root):**

- Start workday: `.\tooling\project_mgmt\workday_start.ps1`
- End workday: `.\tooling\project_mgmt\workday_end.ps1`

Details (including optional Task Scheduler): [AGENT_WORKDAY.md](AGENT_WORKDAY.md).

---

## What you do manually

- **Cursor:** Enable Background Agents in Settings if you want agents to work on assigned issues without an open chat.
- **GitHub:** Create the Project, set token and project number (e.g. via .env), run `.\tooling\project_mgmt\setup_project_full.ps1` once (see [WHAT_I_NEED.md](WHAT_I_NEED.md)).
- **Workday:** Run `workday_start.ps1` when you start, `workday_end.ps1` when you finish (or schedule them).
- **PM:** Open a Cursor session and ask for "next prioritized tasks" (or "take these new requirements and add them to IDEAS_AND_REQUIREMENTS") with the PM rule; see [IDEAS_AND_REQUIREMENTS.md](IDEAS_AND_REQUIREMENTS.md) for intake.

All rules and skills live under `.cursor/rules/` and `.cursor/skills/`; the workflow rule ties them together.
