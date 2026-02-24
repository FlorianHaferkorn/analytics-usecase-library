# Project operating model

**Purpose:** Defines how we work: roles, Definition of Ready/Done, cadence, and how agents vs. humans interact. The GitHub Project is the SSOT for plan and status; this document is the contract for behavior. Milestones, Area, and Priority on project items are set by the backlog sync ([granular_issues.json](../../tooling/project_mgmt/granular_issues.json)). Status is set to Backlog only when an item is newly added to the project; existing Status (In progress, In review, Done) is not overwritten by the sync.

**Language:** English.

---

## 1. Roles

| Role | Responsibility |
|------|----------------|
| **Agent (Cursor / automation)** | Creates/updates issues, moves work through Status, opens PRs, runs Stage 1, generates weekly status update draft. |
| **Human (reviewer)** | Reviews PRs, approves merges, reviews and publishes weekly Project status update. |
| **Owner (per item)** | Accountable for an Epic or Task; set in Project field **Owner**. Optional: use GitHub Assignees. |

No PR is merged without at least one human approval. CODEOWNERS enforce reviewers for `core/`, `tooling/`, `internal/vision/`, `.github/`.

---

## 2. Definition of Ready (DoR) — before work starts

An issue is ready when:

- It is in the GitHub Project with **Status** = `Backlog` or `Planned`.
- **Milestone** and **Area** are set.
- **Priority** (P0/P1/P2) is set.
- For Tasks: acceptance criteria or DoD are in the issue body (or linked Epic).
- Dependencies are noted in **Blocked by** or in the issue body.

Agents may create issues from backlog docs or from triage; they should set these fields so the board stays meaningful.

---

## 3. Definition of Done (DoD) — before an item is closed

An issue is done when:

- The change is in a **merged** PR that references the issue (e.g. `Fixes #123`).
- **Stage 1 passes** on the PR (see [.github/workflows/stage1.yml](../../.github/workflows/stage1.yml)).
- Docs that claim status or scope are updated if the change affects them (e.g. [internal/presentation_status_and_roadmap.md](../presentation_status_and_roadmap.md) for major milestones).
- Project automation sets **Status** = `Done` when the issue is closed (or when the linked PR is merged and the issue is auto-closed).

Agents implement and open the PR; humans perform review and merge.

---

## 4. Cadence

| Cadence | What | Who |
|---------|------|-----|
| **Continuous** | Board and Table views reflect current state from Issues/PRs. | Automatic (Project + workflows). |
| **On every PR** | Stage 1 runs; reviewer approves. | CI + human. |
| **Weekly (e.g. Friday)** | Scheduled workflow generates a Project status update (progress, done, next, risks). | Agent generates draft; human reviews and publishes. |
| **Monthly** | Retrospective on Stage 1 and skills (see [internal/metrics/README.md](../metrics/README.md)). | Human (optional: agent prepares summary). |
| **Quarterly / before release** | Curated stakeholder doc [internal/presentation_status_and_roadmap.md](../presentation_status_and_roadmap.md) updated; references Project/Milestones as source. | Human. |

---

## 5. Intake (new requirements and ideas)

New ideas and requirements are captured in [IDEAS_AND_REQUIREMENTS.md](IDEAS_AND_REQUIREMENTS.md). The **PM agent** (see [AGENT_SETUP.md](AGENT_SETUP.md)) can add entries there from user input (suggested Title, Area, Milestone, Priority). During triage (e.g. weekly), the human decides which items to promote: create a GitHub Issue, add to the Project, set fields; then mark the idea as promoted in the doc. Small or clear requests can go directly to an Issue; larger or fuzzy ideas go to IDEAS_AND_REQUIREMENTS first.

---

## 6. Weekly status update (Variante B)

- **Automated:** A GitHub Action runs the script in `tooling/project_mgmt/`. The script queries the Project (GraphQL), computes progress and risks, and creates a **draft** Project status update via `createProjectV2StatusUpdate`.
- **Human:** Someone opens the Project, reviews the draft status update (On track / At risk, narrative, next steps), adjusts if needed, and **publishes** it. This keeps the narrative accurate while keeping data entry automatic.

---

## 7. Flow summary

1. **Backlog → Planned:** Triage or agent sets Milestone, Area, Priority; item is scheduled.
2. **Planned → In progress:** Work starts; agent or human moves Status (or automation when PR is opened for the issue).
3. **In progress → In review:** PR opened that references the issue; automation can set Status = `In review`.
4. **In review → Done:** PR merged; issue closed; automation sets Status = `Done`. Milestone progress updates automatically.
5. **Weekly:** Draft status update is created; human reviews and publishes.

For the PM-driven flow (start next task, PR review summary, automations), see [PM_FLOW.md](PM_FLOW.md). See also [PROJECT_FIELDS_AND_LABELS.md](PROJECT_FIELDS_AND_LABELS.md) for fields and automations.
