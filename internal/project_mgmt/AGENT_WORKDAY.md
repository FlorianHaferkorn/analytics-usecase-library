# Agent workday (start/end)

**Purpose:** Control when agents may accept new work. The workday is "open" or "closed" via a repo marker file; agents check this before starting implementation.

## Marker

- **Path:** `internal/project_mgmt/AGENT_WORKDAY_OPEN`
- **Open:** File exists (content optional; scripts write a timestamp).
- **Closed:** File absent.

Do not add this file to `.gitignore` if you want the repo state to reflect workday open/closed for all clones. You can commit the file when you end the day ("workday closed") and remove it (or not create it) when starting.

## Scripts (run from repo root or from `tooling/project_mgmt`)

| Script | Effect |
|--------|--------|
| `.\tooling\project_mgmt\workday_start.ps1` | Creates the marker file. Agents may start new work. |
| `.\tooling\project_mgmt\workday_end.ps1`   | Removes the marker file. Agents do not start new work; running sessions may finish. |

## Optional: scheduled start/end (Windows)

Use Task Scheduler to run the scripts at fixed times, e.g.:

- **8:00** — Start task: run `powershell.exe -File "C:\Users\<you>\...\analytics-usecase-library\tooling\project_mgmt\workday_start.ps1"` (use your repo path).
- **18:00** — End task: run `workday_end.ps1` with the same working directory or script path.

Ensure "Start in" is the repo root or the folder containing the script so repo root detection works.

## Agent behaviour

The Agent-Workflow Rule (`.cursor/rules/agent-workflow.mdc`) instructs the agent to check for the marker before starting implementation. If the file is absent, the agent does not start new work and reports that the workday is closed.
