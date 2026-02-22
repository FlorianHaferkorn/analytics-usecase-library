# PM-driven flow (Backlog → Done)

**Purpose:** Describes the single flow from backlog to done: how the PM agent, scripts, and GitHub automations work together so the user does as little as possible. Status transitions and the PR review summary are automated; the only recurring manual step is running the next-task script and telling the Implementer which issue to implement.

**See also:** [OPERATING_MODEL.md](OPERATING_MODEL.md), [PROJECT_FIELDS_AND_LABELS.md](PROJECT_FIELDS_AND_LABELS.md).

---

## 1. Status values and flow

| Status      | Meaning |
|------------|--------|
| **Backlog** | Not yet scheduled. |
| **Planned** | Scheduled (Milestone, Area, Priority set). |
| **In progress** | Someone is working on it (Implementer agent). |
| **In review** | PR open; human (and optional Review agent) reviews. |
| **Done** | PR merged; issue closed. |

Flow: **Backlog / Planned → In progress → In review → Done.**

---

## 2. Step-by-step (what is automated vs manual)

### 2.1 Backlog → In progress (one manual step)

1. **PM agent:** User asks "assign next task" or "start next task". PM outputs the next prioritized task (from BACKLOG_GRANULAR or Project) and tells the user to run the script.
2. **User runs** (from repo root):
   ```powershell
   .\tooling\project_mgmt\start_next_task.ps1
   ```
   The script:
   - Finds project items with Status = **Backlog** or **Planned** (sorted by Priority P0 → P1 → P2).
   - Sets the chosen item’s Status to **In progress**.
   - Prints: issue number, title, Area, recommended expert.
3. **User** opens an **Implementer** (or recommended expert) session and says: **Implement issue #&lt;N&gt;** (N from script output).

There is no Cursor API to start an agent automatically; this is the one recurring manual step.

### 2.2 In progress → In review (automated)

- When a **PR that references the issue** is **opened**, Project automation (if enabled on the repo’s Project) sets the linked issue’s Status to **In review**.  
- Alternatively, you can set it manually: `.\tooling\project_mgmt\set_issue_status.ps1 -Issue N -Status "In review"`.

### 2.3 PR review summary (automated)

- Workflow [.github/workflows/pr_review_summary.yml](../../.github/workflows/pr_review_summary.yml) runs on **pull_request** (opened, synchronize).
- It posts or updates **one comment** on the PR with:
  - PR title and description
  - Files changed (name-status list)
  - Diff stats
- The comment is marked with `<!-- pr-review-summary -->` so it can be updated on each push. The user always has a single place to see **what was created/changed** before approving.

### 2.4 In review → Done (automated)

- When the **linked PR is merged**, Project automation (if enabled) sets the issue’s Status to **Done** and the issue is closed (e.g. via "Fixes #N").
- Human only: **review the PR** (using the summary comment), then **merge**. No need to move status manually.

---

## 3. Scripts and workflows

| What | Where | Purpose |
|------|--------|--------|
| **start_next_task.ps1** | `tooling/project_mgmt/` | Picks one Backlog/Planned item, sets Status to In progress, prints issue # and expert. |
| **set_issue_status.ps1** | `tooling/project_mgmt/` | Sets Status for one or more issues (e.g. `-Issue 23 -Status "In review"`). |
| **pr_review_summary.yml** | `.github/workflows/` | PR comment with title, description, files changed, diff stats. |
| **project_status_update.yml** | `.github/workflows/` | Weekly draft Project status update (separate from this flow). |

Project automations (in GitHub: Project → … → Workflows) that set **In review** on PR open and **Done** on PR merge must be enabled on your Project for full automation of 2.2 and 2.4.

---

## 4. Summary

- **Automated:** Backlog/Planned → In progress (via script); In progress → In review (PR open / Project workflow); PR summary comment; In review → Done (PR merge / Project workflow).
- **Manual:** Run `start_next_task.ps1` and tell the Implementer "Implement issue #N"; then review the PR (using the summary comment) and merge.
