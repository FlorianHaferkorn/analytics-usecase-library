# Azure Pipelines for Fabric Deployment

This directory contains Azure DevOps pipeline definitions for automating Fabric workspace setup and solution releases.

## Pipeline Files

### `solution_setup.yml`
**Purpose**: Initial infrastructure setup (one-time or when adding new environments)

**Triggers**: Manual only (`workflow_dispatch`)

**What it does**:
- Creates Fabric workspaces (DE, DM, BI, Shared layers)
- Sets up Fabric connections
- Configures Git integration
- Assigns permissions

**Usage**:
```yaml
# Run manually with parameters:
environments: 'dev,tst,prd'
```

---

### `solution_release_multistages.yml`
**Purpose**: Multi-stage release pipeline with environment-based approval gates (Recommended)

**Triggers**:
- PR to `main` (builds and validates only)
- Push to `releases/release*` branches (full release flow)

**Stages**:
1. **Build**: Validates solution, runs Stage 1 checks, builds artifacts
2. **ReleaseTest**: Deploys to TEST environment (requires approval if configured)
3. **ReleaseProd**: Deploys to PRODUCTION environment (requires approval if configured)

**Approval Gates**:
- Uses Azure DevOps Environments (`Fabric-TEST`, `Fabric-PRODUCTION`)
- Configure approvals in Azure DevOps UI (see [USAGE.md](../USAGE.md#approval-configuration))
- Approvers receive notifications and can approve/reject deployments
- **Advantages**: Centralized approval management, audit trail, reusable across pipelines

---

### `solution_release_simple.yml`
**Purpose**: Simple release pipeline with task-based manual approvals (Alternative)

**Triggers**: Same as `solution_release_multistages.yml`

**Stages**: Same as multi-stage pipeline

**Approval Gates**:
- Uses `ManualValidation@0` tasks embedded in pipeline
- Approvers configured via pipeline variables
- **Advantages**: No environment setup required, simpler for small teams
- **Disadvantages**: Less flexible, harder to reuse across pipelines

**When to use**: Use this if you prefer task-based approvals or don't want to configure Azure DevOps Environments.

---

### `feature_fabric_branch.yml`
**Purpose**: Automatic workspace creation for feature branches

**Triggers**: Branch creation on `feature/*` branches

**What it does**:
- Creates isolated Fabric workspace for feature development
- Connects workspace to feature branch in Git
- Enables parallel development without conflicts

---

## Templates

### `_template_build_solution.yml`
Reusable template for build stage:
- Checks out repository
- Installs Python dependencies
- Runs Stage 1 validation (`run_stage1_checks.ps1`)
- Runs Fabric checks (`run_fabric_checks.ps1`)
- Builds parameter files
- Publishes artifacts

### `_template_release_solution.yml`
Reusable template for release steps:
- Downloads artifacts
- Installs Python dependencies
- Executes `fabric_release.py` to deploy items
- Optional manual approval fallback
- Post-deployment validation

---

## Setup Instructions

### 1. Choose Your Pipeline

**Option A: Environment-Based Approvals** (Recommended)
- Use `solution_release_multistages.yml`
- Requires Azure DevOps Environments setup
- Better for enterprise scenarios with multiple pipelines

**Option B: Task-Based Approvals** (Simpler)
- Use `solution_release_simple.yml`
- No environment setup required
- Good for small teams or quick setup

### 2. Import Pipeline

In Azure DevOps:
1. Go to **Pipelines > Pipelines**
2. Click **New pipeline**
3. Select your repository
4. Choose **Existing Azure Pipelines YAML file**
5. Select the pipeline file:
   - `solution_release_multistages.yml` (environment-based)
   - `solution_release_simple.yml` (task-based)

### 2. Configure Environments (Only for `solution_release_multistages.yml`)

If using environment-based approvals:

1. **Pipelines > Environments**
2. Create:
   - `Fabric-TEST`
   - `Fabric-PRODUCTION`
3. Configure approvals (see [USAGE.md](../USAGE.md#approval-configuration))

**Skip this step** if using `solution_release_simple.yml` (task-based approvals).

### 3. Configure Variable Groups

Create variable group: `Fabric-Release-Variables`

**Required variables**:
- `SPN_TENANT_ID` (Service Principal Tenant ID)
- `SPN_CLIENT_ID` (Service Principal Client ID)
- `SPN_CLIENT_SECRET` (Service Principal Secret - mark as secret)

**Optional variables**:
- `APPROVAL_NOTIFY_USERS` (comma-separated email addresses for approval notifications)

### 4. Configure Service Connections

Ensure service connections are configured:
- **Fabric API**: Service Principal with appropriate permissions
- **Git**: Azure DevOps or GitHub connection for Git integration

---

## Approval Configuration

### Environment-Based Approvals (Recommended)

1. Open environment (e.g., `Fabric-PRODUCTION`)
2. Click **Approvals and checks**
3. Add **Approvals** check:
   - Add approvers (individuals or groups)
   - Set minimum approvals required
   - Configure timeout
   - Add instructions for approvers

### Manual Approval Fallback

If environment approvals are not configured, you can use manual approval tasks by modifying the pipeline:

```yaml
- template: _template_release_solution.yml
  parameters:
    environment: 'prd'
    requireManualApproval: true
    approvalTimeoutMinutes: 1440
```

---

## Pipeline Variables

### Build Stage Variables

- `PYTHONIOENCODING`: utf-8
- `PYTHONUNBUFFERED`: 1

### Release Stage Variables

- `SPN_TENANT_ID`: From variable group
- `SPN_CLIENT_ID`: From variable group
- `SPN_CLIENT_SECRET`: From variable group (secret)
- `APPROVAL_NOTIFY_USERS`: From variable group (optional)

---

## Branch Strategy

### Development Flow

1. **Feature branches** (`feature/*`):
   - Automatically creates isolated workspace
   - Develop and test in isolation

2. **Pull requests to `main`**:
   - Triggers build and validation
   - No deployment (safety gate)

3. **Release branches** (`releases/release*`):
   - Triggers full release pipeline
   - Build → Test (with approval) → Prod (with approval)

**Branch rule in the pipeline (I-21 W5.4, 01.10.2026).** Until 01.10.2026 the "no deployment"
in point 2 was only prose: both release pipelines trigger on PRs to `main`, and their release
stages had `condition: succeeded()`, so a PR build ran into `ReleaseTest`/`ReleaseProd`.
`ReleaseTest` and `ReleaseProd` now carry

```yaml
condition: and(succeeded(), startsWith(variables['Build.SourceBranch'], 'refs/heads/releases/'), ne(variables['Build.Reason'], 'PullRequest'))
```

so only a run on `releases/*` that is not a PR build deploys; a manual run from another branch
builds and stops. Pinned by `scripts/tests/test_release_plan_and_pipeline_rules.py`.

### Secret Scan (Build Stage)

`_template_build_solution.yml` installs `detect-secrets==1.5.0` and runs
`scripts/secret_scan_gate.py` before any artifact is published. Scope: the release automation
(`deployment/scripts`, `deployment/resources`, without `tests/`). Exit 0 = scanned, no
findings; 1 = findings; 2 = the scan did not run (tool missing, tool error, empty scope) — both
1 and 2 fail the build.

- Measured 01.10.2026 (local `detect-secrets 1.5.0`): scope 0 findings in 26 files; a planted
  AWS key in a test copy gives exit 1. The whole repository has 630 findings in 50 files
  without a baseline, which is why the gate is scoped and not repo-wide.
- First choice on Azure Repos is **GitHub Advanced Security for Azure DevOps** secret scanning
  with push protection (repository setting; Learn `azure/devops/repos/security/
  github-advanced-security-secret-scanning`). The gate covers repositories without it.

### Known Defects (not fixed in this round)

- `ManualValidation@0` runs only in an **agentless** job (Learn `manual-validation-v0`,
  read 01.10.2026). `solution_release_simple.yml` and the fallback step in
  `_template_release_solution.yml` place it in agent jobs, so the task-based approval path
  does not run as written. Use `solution_release_multistages.yml` (environment approvals)
  until the simple pipeline gets a `pool: server` job.
- `solution_setup.yml` and `feature_fabric_branch.yml` still use `script:` with `pwsh: true`;
  `pwsh` is not a property of a `script` step. The release template was switched to a `pwsh:`
  step on 01.10.2026; the two other files are unchanged.
- Fixed 01.10.2026: `--unpublish_items` was parsed with `type=bool`, so `false` also yielded `True`; it now accepts only true/false (`_parse_bool`).

### Branch Protection

Configure branch protection rules in Azure DevOps:
- Require PR reviews for `main`
- Require status checks (build stage must pass)
- Prevent force push to `main`

---

## Troubleshooting

### Approval Not Triggering

- Verify environment name matches exactly (`Fabric-TEST`, `Fabric-PRODUCTION`)
- Check that environment has approvals configured
- Verify approvers have permissions

### Deployment Fails

- Check service principal credentials
- Verify Fabric capacity is available
- Review pipeline logs for specific errors
- Ensure parameter files are correctly configured

### Artifacts Not Found

- Verify build stage completed successfully
- Check artifact names match (`automation`, `solution`)
- Ensure artifacts are published before release stages

---

## Security Best Practices

1. **Secrets Management**:
   - Store all secrets in Azure DevOps variable groups (marked as secret)
   - Never commit secrets to repository
   - Use service principals with least privilege

2. **Approval Gates**:
   - Require approvals for production deployments
   - Use multiple approvers for critical changes
   - Set appropriate timeout values

3. **Branch Protection**:
   - Protect `main` branch
   - Require PR reviews
   - Enforce status checks

4. **Audit Trail**:
   - All deployments are logged in Azure DevOps
   - Approval actions are tracked
   - Pipeline runs are auditable

---

## References

- [Azure Pipelines Documentation](https://docs.microsoft.com/en-us/azure/devops/pipelines/)
- [Environments and Approvals](https://docs.microsoft.com/en-us/azure/devops/pipelines/process/environments)
- [Deployment Jobs](https://docs.microsoft.com/en-us/azure/devops/pipelines/process/deployment-jobs)
- [Manual Validation Task](https://docs.microsoft.com/en-us/azure/devops/pipelines/tasks/utility/manual-validation)
