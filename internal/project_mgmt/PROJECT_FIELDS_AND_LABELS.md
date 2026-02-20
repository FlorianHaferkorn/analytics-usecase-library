# GitHub Project: Fields, Views, and Automations

**Purpose:** Single source of truth for the repo-scope GitHub Project. Use this document to create or reconfigure the project. The board is the operational SSOT for plan and status; agents work via Issues/PRs, humans review and approve.

**Language:** English.

---

## 1. Create the project (one-time, in GitHub UI)

1. In the repository: **Projects** → **New project** → **Board** or **Table** (you will add multiple views).
2. Choose **Repository project** (not Organization).
3. Name: e.g. **Analytics Use Case Library – Delivery**.
4. In **Settings**: Link the project to this repository so new issues can be added automatically.
5. Add the fields and views below. Document the **Project number** (or Project ID from URL/settings); the weekly status script needs the project ID (numeric or node ID from GraphQL).

---

## 2. Project fields (Project V2)

Create these as **Single select** or **Text** / **Date** as indicated. Field names and options must match so automation and the weekly status script work.

| Field name   | Type        | Options / usage |
|-------------|-------------|------------------|
| **Status**  | Single select | `Backlog`, `Planned`, `In progress`, `In review`, `Done` |
| **Area**    | Single select | `Framework`, `FabricPowerBI`, `Aurora`, `Tooling`, `Docs` |
| **Priority**| Single select | `P0`, `P1`, `P2` |
| **Risk**    | Single select | `On track`, `At risk` |
| **Target date** | Date     | For epics; used in Roadmap view. |
| **Milestone**   | Single select | Values match GitHub Milestones or your phases, e.g. `Project completion`, `Phase 2`, `Technical backlog`. |
| **Owner**   | Text (or Assignees) | Owner of the item. |
| **Blocked by**  | Text     | Comma-separated issue numbers or "None". |

**Notes:**

- Use **Assignees** for Owner if you prefer; then the script can read assignees via GraphQL.
- **Milestone** can mirror GitHub Milestones (e.g. same names) so the Roadmap view and milestone progress stay aligned.

---

## 3. Views

Configure three views; all use the same project items.

| View name   | Layout  | Group by     | Sort / filter | Purpose |
|-------------|---------|--------------|---------------|---------|
| **Board**   | Board   | Status       | Optional: swimlanes by Milestone | Daily flow: Backlog → In progress → In review → Done. |
| **Table**   | Table   | Milestone    | Sort by Priority; filter Status ≠ Done | Backlog and progress per milestone. |
| **Roadmap** | Roadmap | —            | Items with Target date; optional iteration | Timeline of epics and key deliverables. |

---

## 4. Built-in automations (Project settings → Workflows)

Enable or add these behaviors so the board stays in sync with Issues/PRs without manual updates.

| Trigger                    | Action |
|---------------------------|--------|
| **Item added to project** | When a new issue is added to the project, set default **Status** = `Backlog` (if not set). |
| **Pull request merged**   | When a linked issue’s PR is merged (or issue is closed), set **Status** = `Done`. |
| **Pull request opened**   | When a PR that references an issue is opened, set that issue’s **Status** = `In review`. |

If your project uses “Item closed” instead of “PR merged”, configure: **When an issue is closed** → set **Status** = `Done`. GitHub’s “Close issue when PR is merged” will then drive Status to Done automatically.

---

## 5. Labels (repository-level, optional)

Use labels for filtering and for the weekly status heuristics (e.g. at-risk detection):

| Label      | Color  | Use |
|-----------|--------|-----|
| `blocker` | red    | Item blocks others; treat as at-risk if overdue. |
| `epic`    | purple | Epic-level issue (optional if you use issue type in title/template). |
| `area:framework` | —  | Alternative to Area field for filtering. |
| `area:tooling`   | —  | Same. |
| `area:fabric-powerbi` | — | Same. |

Labels are optional; the script can rely only on Project fields (Priority, Risk, Target date, Blocked by).

---

## 6. Weekly status update (automated)

A scheduled workflow runs the script in [tooling/project_mgmt/](../../tooling/project_mgmt/). The script:

- Queries the project (GraphQL) for items, Status, Milestone, Priority, Risk, Target date, Blocked by.
- Computes: Done/Total per milestone, overdue P0, blocked items, merged PRs since last run.
- Sets **At risk** heuristics: e.g. P0 overdue, or P0 blocked, or epic past target date.
- Calls `createProjectV2StatusUpdate` with body (markdown) and status `ON_TRACK` or `AT_RISK`.

The generated update is a **draft** for human review; a human reviews and publishes in the Project’s status updates. See [internal/project_mgmt/OPERATING_MODEL.md](OPERATING_MODEL.md) for cadence.

---

## 7. Reference: GraphQL and script

- Project data: [Using the API to manage Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects).
- Status updates: `createProjectV2StatusUpdate` mutation; see [GitHub Changelog – GraphQL and webhook support for project status updates](https://github.blog/changelog/2024-06-27-github-issues-projects-graphql-and-webhook-support-for-project-status-updates-and-more/).

The script needs:

- `GITHUB_TOKEN` (or `GH_TOKEN`) with `repo` and `project` scope (for project and status update). If the weekly workflow fails with a permission error on `createProjectV2StatusUpdate`, add a PAT with project scope as a repository secret (e.g. `PROJECT_STATUS_TOKEN`) and set `GITHUB_TOKEN` to that secret in the workflow.
- Project identifier: organization/repo project number, or the project’s node ID from GraphQL `repository.projectV2(number: N)`.
