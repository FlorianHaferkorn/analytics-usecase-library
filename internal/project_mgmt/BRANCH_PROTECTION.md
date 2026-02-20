# Branch protection recommendations

**Purpose:** Recommended repository settings so that PRs to the default branch require review and passing CI. Apply these in **Settings → Branches → Branch protection rules** (or your org’s equivalent).

**Language:** English.

---

## Recommended rule for `main`

| Setting | Recommendation |
|--------|-----------------|
| **Require a pull request before merging** | Yes |
| **Required approvals** | At least 1 |
| **Dismiss stale reviews when new commits are pushed** | Optional (your preference) |
| **Require review from Code Owners** | Yes (so CODEOWNERS are enforced for `core/`, `tooling/`, `internal/vision/`, `.github/`) |
| **Require status checks to pass** | Yes |
| **Status checks that are required** | The Stage 1 workflow (e.g. `stage1` or the name of the job that runs `run_stage1_checks.ps1`) |
| **Require branches to be up to date** | Optional (recommended so main is always green after merge) |
| **Do not allow bypassing the above settings** | For admins: per your policy |

---

## Notes

- The exact **status check name** is the one defined in [.github/workflows/stage1.yml](../../.github/workflows/stage1.yml) (job id or the name GitHub reports). Add that name under "Require status checks to pass."
- CODEOWNERS are listed in [.github/CODEOWNERS](../../.github/CODEOWNERS). Update the handles/teams there; then "Require review from Code Owners" will request them automatically for changes under the listed paths.
