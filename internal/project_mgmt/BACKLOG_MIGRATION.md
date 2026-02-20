# Backlog migration to GitHub Issues and Project

**Purpose:** One-time migration of items from [internal/technical_backlog.md](../technical_backlog.md) and [internal/vision/phase2_backlog.md](../vision/phase2_backlog.md) into GitHub Issues, added to the repo-scope Project with Milestone and Area set. Agents or humans can create these issues (e.g. via GitHub UI or `gh issue create`); then add each issue to the Project and set fields.

**Language:** English.

---

## Milestones to create (in GitHub)

Create these milestones in the repository if they do not exist:

- **Project completion** — Blocker resolution, review adjustments, zero-tolerance documentation (from presentation_status_and_roadmap).
- **Phase 2** — 3-30-300 complete, Strategy Pattern / AI urgency (from phase2_backlog).
- **Technical backlog** — MCP, Fabric, synthetic data, scaffold, Aurora models (from technical_backlog).

---

## Phase 2 (Epics from phase2_backlog.md)

Create as **Epic** issues; add to Project; set **Milestone** = Phase 2.

| Title | Area | Priority | Definition of Done |
|-------|------|----------|--------------------|
| [Epic] 3-30-300 complete: 300s page from action-code YAML | FabricPowerBI | P1 | 300s page in report shows action text and evidence table sourced from action-code YAML; generated from framework. |
| [Epic] Strategy Pattern / AI urgency and automated reasoning | Framework | P2 | Strategy pattern precise enough for tooling; AI urgency and automated reasoning demonstrated or documented scope. |

---

## Technical backlog (Tasks from technical_backlog.md)

Create as **Task** (or **Bug** where applicable) issues; add to Project; set **Milestone** = Technical backlog, **Area** as in table.

### Power BI MCP / Fabric

| Title | Area | Priority | Notes |
|-------|------|----------|--------|
| [Task] Call Power BI MCP table_operations from table_ops.ps1 | Tooling | P2 | tooling/powerbi_mcp/table_ops.ps1 ~line 138. |
| [Task] Call Power BI MCP relationship_operations from relationship_ops.ps1 | Tooling | P2 | tooling/powerbi_mcp/relationship_ops.ps1 ~line 199. |
| [Task] Fabric Workspace and semantic model API in deploy.ps1 | Tooling | P2 | deploy.ps1: GET/POST workspace, Import PBIP/TMDL, Publish report, Refresh schedule, RLS/security_user_org. |
| [Task] TMDL/display folders, relationship update, visuals, REST, refresh, security in AUTOMATION_FLOW | Tooling | P2 | See tooling/powerbi_mcp/AUTOMATION_FLOW.md. |

### Aurora Models (Operations, Finance)

| Title | Area | Priority | Notes |
|-------|------|----------|--------|
| [Task] Complete Aurora Operations and Finance domain models | Aurora | P1 | relationships/measures/display folders; DAX in KPI Catalog; Measure_Dictionary per domain. See showcases/aurora_group/models/README.md. |

### Synthetic data

| Title | Area | Priority | Notes |
|-------|------|----------|--------|
| [Task] Synthetic data: Lakehouse pre-create and backbone notebook stubs | Tooling | P2 | fabric_nb_generate_backbone_core_v1.py: create Lakehouse first; implement stub blocks (date range, joins, bands, schema). |
| [Task] Synthetic data: optional holiday logic in generate_gold_layer | Tooling | P2 | generate_gold_layer.py line 121: is_holiday. |

### Page scaffold generator

| Title | Area | Priority | Notes |
|-------|------|----------|--------|
| [Task] Page scaffold: BOM support in YAML scanner | Tooling | P2 | scanner.py line 187. |
| [Task] Page scaffold: tab handling rules in YAML scanner | Tooling | P2 | scanner.py line 761. |

---

## After creating issues

1. Add each new issue to the GitHub Project (repo-scope).
2. Set **Status** = Backlog (or Planned), **Milestone** and **Area** as in the tables.
3. Link Tasks to Epics where applicable (e.g. Phase 2 Epics as parent).
4. Optionally set **Target date** on Epics for Roadmap view.
5. Update [internal/technical_backlog.md](../technical_backlog.md) and [internal/vision/phase2_backlog.md](../vision/phase2_backlog.md) with a short note at the top: *"Tracking has moved to GitHub Project; see BACKLOG_MIGRATION in internal/project_mgmt and the repo Project."* (No markdown link needed, or use `project_mgmt/BACKLOG_MIGRATION.md` when the note lives under `internal/`.)

---

## Optional: create issues via `gh` CLI

Example (adjust body and labels):

```bash
gh issue create --title "[Task] Call Power BI MCP table_operations from table_ops.ps1" \
  --body "See internal/technical_backlog.md. File: tooling/powerbi_mcp/table_ops.ps1 ~line 138." \
  --label "area:tooling"
```

Then add the issue to the Project in the GitHub UI and set Milestone and Area fields.
