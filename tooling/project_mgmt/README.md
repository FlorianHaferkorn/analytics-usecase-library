# Project management tooling

**Purpose:** Scripts and automation for the repo-scope GitHub Project. Primary artifact: the weekly status update script that queries the project (GraphQL) and creates a draft Project status update for human review.

**See:**

- [internal/project_mgmt/OPERATING_MODEL.md](../../internal/project_mgmt/OPERATING_MODEL.md) — cadence and roles.
- [internal/project_mgmt/PROJECT_FIELDS_AND_LABELS.md](../../internal/project_mgmt/PROJECT_FIELDS_AND_LABELS.md) — project fields and API reference.

**Artifacts (implemented in this repo):**

- `weekly_status_update.ps1` (or `.py`): Queries project items, computes progress and risks, calls `createProjectV2StatusUpdate`. Invoked by [.github/workflows/project_status_update.yml](../../.github/workflows/project_status_update.yml).
