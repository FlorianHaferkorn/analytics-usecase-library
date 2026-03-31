# PM-driven flow (Backlog → Done)

**Purpose:** Describes the single flow from backlog to done: how the PM agent, **Assistant Agent** (daily briefing), scripts, and GitHub automations work together so the user does as little as possible. Status transitions and the PR review summary are automated; the only recurring manual steps are: ask the Assistant for a daily briefing, then run the next-task script and tell the Implementer which issue to implement.

**See also:** [OPERATING_MODEL.md](OPERATING_MODEL.md), [PROJECT_FIELDS_AND_LABELS.md](PROJECT_FIELDS_AND_LABELS.md), [ASSISTANT_BRIEFING.md](ASSISTANT_BRIEFING.md) (daily briefing with minimal manual steps). For what runs automatically on every PR and how to add LLM-based review: [REVIEW_AUTOMATION_OPTIONS.md](REVIEW_AUTOMATION_OPTIONS.md).

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

### 2.1 Backlog → In progress (minimal manual steps)

**Option A — Mit Daily Briefing (empfohlen):** User fragt den **Assistant Agent** nach einem **Daily Briefing** (z. B. "Briefing" oder "Was steht an?"). Der Assistant liest [PROJECT_SNAPSHOT.md](PROJECT_SNAPSHOT.md) (erzeugt von `refresh_project_snapshot.ps1`) und [BACKLOG_GRANULAR.md](BACKLOG_GRANULAR.md) und liefert Fokus, Bottlenecks und **genau die nächste Aufgabe inkl. Anweisung** (Skript + "Implement issue #N"). User führt nur noch diese Anweisung aus. Siehe [ASSISTANT_BRIEFING.md](ASSISTANT_BRIEFING.md).

**Option B — Ohne Briefing:** User fragt den PM Agent "assign next task" / "start next task"; PM gibt die nächste Aufgabe und die Skript-Anweisung aus.

**Gemeinsamer Schritt:** User runs (from repo root):
   ```powershell
   .\tooling\project_mgmt\start_next_task.ps1
   ```
   The script:
- Finds project items with Status = **Backlog** or **Planned** (sorted by Priority P0 → P1 → P2).
- Sets the chosen item’s Status to **In progress**.
- Prints: issue number, title, Area, recommended expert.
- **User** then opens an **Implementer** (or recommended expert) session and says: **Implement issue #&lt;N&gt;** (N from script output).

There is no Cursor API to start an agent automatically; this is the one recurring manual step.

### 2.2 In progress → In review (automated)

- When a **PR that references the issue** is **opened**, Project automation (if enabled on the repo’s Project) sets the linked issue’s Status to **In review**.  
- Alternatively, you can set it manually: `.\tooling\project_mgmt\set_issue_status.ps1 -Issue N -Status "In review"`.

### 2.3 PR review summary (automated) and Reviewer Agent

**Order: run the Reviewer Agent first, then use the automated summary and CI.**

1. **Reviewer Agent (before script-based review):** Start a Cursor session with [.cursor/rules/reviewer-agent.mdc](../../.cursor/rules/reviewer-agent.mdc) and say: **Review PR #N**. The Reviewer agent checks the PR against rules and skills and outputs a structured review (checklist, findings, approve/request changes). Do this before relying on the workflow comment or CI.
2. **PR summary (automated):** Workflow [.github/workflows/pr_review_summary.yml](../../.github/workflows/pr_review_summary.yml) runs on **pull_request** (opened, synchronize) and posts or updates **one comment** with PR title, description, files changed, diff stats. The comment is marked with `<!-- pr-review-summary -->`. Use this summary together with the Reviewer Agent output before approving.

### 2.4 In review → Done (automated)

- When the **linked PR is merged**, Project automation (if enabled) sets the issue’s Status to **Done** and the issue is closed (e.g. via "Fixes #N").
- Human only: **review the PR** — first run the Reviewer Agent (§2.3), then use the summary comment and CI; then **merge**. No need to move status manually.

---

## 3. Scripts and workflows

| What | Where | Purpose |
|------|--------|--------|
| **start_next_task.ps1** | `tooling/project_mgmt/` | Picks one Backlog/Planned item, sets Status to In progress, prints issue # and expert. |
| **set_issue_status.ps1** | `tooling/project_mgmt/` | Sets Status for one or more issues (e.g. `-Issue 23 -Status "In review"`). |
| **pr_review_summary.yml** | `.github/workflows/` | PR comment with title, description, files changed, diff stats. |
| **refresh_project_snapshot.ps1** | `tooling/project_mgmt/` | Reads Backlog/Planned (no status change), writes PROJECT_SNAPSHOT.md for the Assistant. |

Project automations (in GitHub: Project → … → Workflows) that set **In review** on PR open and **Done** on PR merge must be enabled on your Project for full automation of 2.2 and 2.4.

---

## 4. Summary

- **Automated:** Backlog/Planned → In progress (via script); In progress → In review (PR open / Project workflow); PR summary comment; In review → Done (PR merge / Project workflow).
- **Minimal manual:** (1) Once per day: optionally run `refresh_project_snapshot.ps1`, then ask the **Assistant** for a **daily briefing** — you get focus, bottlenecks, and the exact next step. (2) When starting work: run `start_next_task.ps1` and tell the Implementer "Implement issue #N" (as in the briefing). (3) Review the PR (using the summary comment) and merge.
