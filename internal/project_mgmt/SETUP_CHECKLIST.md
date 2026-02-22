# Setup checklist: Project, Branch Protection, Migration

**Purpose:** Execute these steps once to complete the operative package.

**Vollautomatischer Weg (empfohlen):** Du legst nur das Project in der UI an und fügst die Felder hinzu (Abschnitt 1). Danach: Token + Projekt-Nummer setzen und [tooling/project_mgmt/setup_project_full.py](../../tooling/project_mgmt/setup_project_full.py) ausführen. Das Skript erstellt **granulare** Issues, fügt sie dem Project hinzu und setzt alle Felder. Details: [WHAT_I_NEED.md](WHAT_I_NEED.md).

**Repo:** `FlorianHaferkorn/analytics-usecase-library` (adjust if different).

---

## 1. Create the GitHub Project (Repository project, in UI)

1. Open **https://github.com/FlorianHaferkorn/analytics-usecase-library**
2. Go to **Projects** (top bar) → **New project** → choose **Board** or **Table**.
3. Select **Repository project** (link to this repo). Name: **Analytics Use Case Library – Delivery**.
4. In project **Settings** (gear): ensure the project is linked to this repository.

### Add fields (Settings → Fields)

Create each field with **exact** name and options (required for the weekly status script):

| Field name   | Type         | Options (comma-separated or one per line) |
|-------------|--------------|--------------------------------------------|
| Status      | Single select | `Backlog`, `Planned`, `In progress`, `In review`, `Done` |
| Area        | Single select | `Framework`, `FabricPowerBI`, `Aurora`, `Tooling`, `Docs` |
| Priority    | Single select | `P0`, `P1`, `P2` |
| Risk        | Single select | `On track`, `At risk` |
| Target date | Date         | — |
| Milestone   | Single select | `Project completion`, `Phase 2`, `Technical backlog` |
| Owner       | Text         | — |
| Blocked by  | Text         | — |

### Add views (Views → New view)

- **Board:** Group by **Status**. Optionally add swimlanes by **Milestone**.
- **Table:** Group by **Milestone**, sort by **Priority**, filter out **Status = Done**.
- **Roadmap:** Layout = Roadmap; items need **Target date** for timeline.

### Automations (Settings → Workflows)

- **When item is added to project** → Set **Status** to `Backlog`.
- **When an issue is closed** → Set **Status** to `Done`.
- **When a pull request that references an issue is opened** → Set that issue’s **Status** to `In review`.

### Note the project number

After creation, the project URL looks like `.../projects/1` (or 2, 3, …). This number is **Project number**. Set it in the repo (Settings → Secrets and variables → Actions → Variables) as `PROJECT_NUMBER` so the weekly workflow can use it, or leave default `1` in the workflow.

---

## 2. Branch protection (optional, in UI)

1. **Settings** → **Branches** → **Add branch protection rule** (or edit existing for `main`).
2. **Branch name pattern:** `main`.
3. Enable:
   - **Require a pull request before merging** (required approvals: 1).
   - **Require review from Code Owners** (so [.github/CODEOWNERS](../../.github/CODEOWNERS) is enforced).
   - **Require status checks to pass before merging** → add the check name from the Stage 1 workflow (e.g. **Stage 1 checks** or the job name from [.github/workflows/stage1.yml](../../.github/workflows/stage1.yml)).
4. Save.

---

## 3. CODEOWNERS (optional adjustment)

Current [.github/CODEOWNERS](../../.github/CODEOWNERS) uses `@florianhaferkorn`. To use a team instead, replace with e.g. `@FlorianHaferkorn/your-team-name` (replace with your org and team). No change needed if the current owner is correct.

---

## 4. Run the backlog migration (Issues + Milestones)

Use the script that creates milestones and issues via the GitHub API. You need a **GitHub token** with `repo` scope (and `project` if you want to add issues to the project via script; otherwise add them manually in the Project UI).

### Option A: With GitHub CLI (`gh`)

If you install [GitHub CLI](https://cli.github.com/) and run `gh auth login`:

```powershell
cd "c:\Users\florianhaferkorn\VSCode\analytics-usecase-library"
.\tooling\project_mgmt\run_backlog_migration.ps1
```

The script will use `gh auth token` or `GITHUB_TOKEN` / `GH_TOKEN` from the environment.

### Option B: With token only (no `gh`)

1. Create a Personal Access Token (Settings → Developer settings → Personal access tokens) with scope **repo** (and **project** if the script adds items to the project).
2. In PowerShell:

```powershell
$env:GITHUB_TOKEN = "ghp_xxxxxxxx"
cd "c:\Users\florianhaferkorn\VSCode\analytics-usecase-library"
.\tooling\project_mgmt\run_backlog_migration.ps1
```

### After the script

1. Open the **Project** → **Add items** → add the new issues by number (the script prints the list).
2. For each item, set **Status** = Backlog, **Milestone** and **Area** as in [BACKLOG_MIGRATION.md](BACKLOG_MIGRATION.md).
3. Optionally set **Target date** on the two Phase 2 epics for the Roadmap view.

---

## 5. Labels (optional)

In **Issues** → **Labels**, create if missing: `epic`, `bug`, `blocker`, `area:framework`, `area:tooling`, `area:fabric-powerbi`. The migration script can create these; the issue templates use `epic` and `bug`.

---

## 6. Agent-Setup (optional)

For agent-driven workflow (prioritization, implementation, workday control): see [AGENT_SETUP.md](AGENT_SETUP.md) (roles, experts, workflow) and [AGENT_WORKDAY.md](AGENT_WORKDAY.md) (start/end workday scripts).
