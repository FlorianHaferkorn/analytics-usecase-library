# Project management tooling

**Purpose:** Scripts for the repo-scope GitHub Project. Manage backlog, status transitions, and project snapshots.

**See:**

- [internal/project_mgmt/OPERATING_MODEL.md](../../internal/project_mgmt/OPERATING_MODEL.md) — cadence and roles.
- [internal/project_mgmt/PROJECT_FIELDS_AND_LABELS.md](../../internal/project_mgmt/PROJECT_FIELDS_AND_LABELS.md) — project fields and API reference.

**Key scripts:**

- `start_next_task.ps1` — Picks the next Backlog/Planned item, sets Status to In progress, prints issue # and expert.
- `set_issue_status.ps1` — Sets Status for one or more issues (e.g. `-Issue 23 -Status "In review"`).
- `refresh_project_snapshot.ps1` — Reads Backlog/Planned (no status change), writes PROJECT_SNAPSHOT.md for the Assistant.
