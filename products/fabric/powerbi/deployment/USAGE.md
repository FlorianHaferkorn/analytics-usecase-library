# Fabric Architecture Automation — Usage Guide

This guide explains how to set up and use the Fabric architecture automation scripts and pipelines.

## Testing Without Fabric Capacity

**You can validate and simulate the automation without a Fabric capacity!**

### Quick Test

```powershell
# Run validation and dry-run simulation
.\scripts\test_without_fabric.ps1 --environment dev --Simulate

# Or validate all environments
.\scripts\test_without_fabric.ps1 --AllEnvironments --Simulate
```

This will:
1. Validate JSON configuration files (structure, required fields)
2. Simulate workspace creation (show what would be created)
3. Simulate connection setup
4. Show permission assignments

### Manual Validation

```powershell
# Validate configuration files
python scripts/validate_config.py --environment dev --simulate

# Dry-run setup (simulates without executing)
python scripts/fabric_setup.py --environment dev --dry-run
```

**Note:** Dry-run mode (`--dry-run`) skips authentication and Fabric API calls, so you can test the logic without a capacity.

## Prerequisites

### 1. Fabric Capacity

- A Microsoft Fabric capacity (or Power BI Premium capacity) assigned to your tenant
- Tenant admin access or capacity admin permissions

**For testing/validation:** Not required — use `--dry-run` mode or `test_without_fabric.ps1`

### 2. Service Principal

Create an Azure AD service principal with Fabric API permissions:

1. Register an app in Azure AD (App registrations)
2. Create a client secret
3. Grant the service principal **Fabric Administrator** or **Capacity Administrator** role
4. Note down: `tenant_id`, `client_id`, `client_secret`

### 3. Git Repository

- Azure DevOps or GitHub repository
- Repository URL, organization/project name, repository name
- (Optional) GitHub Personal Access Token if using GitHub

### 4. Python Environment

- Python 3.9 to 3.12
- Install dependencies: `pip install -r products/fabric/powerbi/deployment/resources/requirements.txt`

### 5. Fabric CLI

Install Fabric CLI:
```bash
pip install ms-fabric-cli==1.7.0
```

## Configuration

### Step 1: Configure Environment JSON Files

Edit the environment configuration files in `resources/environments/`:

1. **`infrastructure.json`** — Base configuration:
   - Update `capacity_name` to your **non-production** Fabric capacity (dev, tst and feature
     workspaces). Production runs on a separate capacity (D-596), named in `infrastructure.prd.json`
   - Update `permissions` with your Azure AD group/user IDs
   - Adjust `fabric_connections` if needed

2. **`infrastructure.dev.json`** — Dev environment:
   - Update `git_settings` with your repository details
   - Update `permissions` for dev environment

3. **`infrastructure.tst.json`** and **`infrastructure.prd.json`** — Test and production:
   - Update `git_settings` (usually same repo, different branches)
   - Update `permissions` (more restrictive for prod)
   - `infrastructure.prd.json`: set `generic.capacity_name` to the **production** capacity

### Step 2: Configure Azure Pipelines Secrets

In Azure DevOps, add pipeline variable group or secrets:

- `SPN_TENANT_ID` — Service principal tenant ID
- `SPN_CLIENT_ID` — Service principal client ID
- `SPN_CLIENT_SECRET` — Service principal client secret (secret variable)
- `GITHUB_PAT` — GitHub PAT (if using GitHub; secret variable)

## Usage

### Option 1: Manual Setup (Local Script)

#### Setup Workspaces

```powershell
cd products/fabric/powerbi/deployment

# Set environment variables
$env:TENANT_ID = "your-tenant-id"
$env:CLIENT_ID = "your-client-id"
$env:CLIENT_SECRET = "your-client-secret"
$env:GITHUB_PAT = "your-github-pat"  # Only if using GitHub

# Run setup for dev environment
python scripts/fabric_setup.py --environment dev

# Run setup for test environment
python scripts/fabric_setup.py --environment tst

# Run setup for production environment
python scripts/fabric_setup.py --environment prd
```

#### Release Items to Fabric

```powershell
# Release to dev
python scripts/fabric_release.py --environment dev --repo_path ./solution

# Release to test (specific layers)
python scripts/fabric_release.py --environment tst --layers DE,DM --repo_path ./solution

# Release to production (specific item types)
python scripts/fabric_release.py --environment prd --item_types SemanticModel,Report --repo_path ./solution
```

### Option 2: Azure Pipelines

#### Initial Setup

1. Import pipeline: `.azure-pipelines/solution_setup.yml`
2. Configure pipeline variables (secrets)
3. Run pipeline manually with parameter `environments: dev,tst,prd`

#### Regular Releases

**Option A: Environment-Based Approvals** (Recommended)
1. Import pipeline: `.azure-pipelines/solution_release_multistages.yml`
2. **Configure Approval Gates** (see [Approval Configuration](#approval-configuration) below)
3. Pipeline triggers on:
   - PR to `main` (builds and validates; the release stages are skipped)
   - Push to `releases/release*` (builds → releases to test → releases to prod)
4. Manual runs also supported; they deploy only when started on a `releases/*` branch
   (branch rule in the stage conditions, see `.azure-pipelines/README.md`)
5. The build stage runs a secret scan over the release automation before publishing
   artifacts (`scripts/secret_scan_gate.py`)

**Option B: Task-Based Approvals** (Simpler)
1. Import pipeline: `.azure-pipelines/solution_release_simple.yml`
2. Configure `APPROVAL_NOTIFY_USERS` variable (comma-separated emails)
3. Same triggers as Option A
4. No environment setup required

#### Feature Branches

1. Import pipeline: `.azure-pipelines/feature_fabric_branch.yml`
2. Pipeline triggers automatically on branch creation (`feature/*`)
3. Creates isolated workspace for feature development

#### Approval Configuration

The multi-stage release pipeline uses Azure DevOps Environments for approval gates. Configure as follows:

**Step 1: Create Environments**

1. Go to **Pipelines > Environments** in Azure DevOps
2. Click **Create environment**
3. Create two environments:
   - `Fabric-TEST` (for test deployments)
   - `Fabric-PRODUCTION` (for production deployments)

**Step 2: Configure Approvals**

For each environment (especially `Fabric-PRODUCTION`):

1. Open the environment (e.g., `Fabric-PRODUCTION`)
2. Click **Approvals and checks** (or **...** menu > **Approvals and checks**)
3. Click **+** and select **Approvals**
4. Configure:
   - **Approvers**: Add individuals or groups (e.g., "Data Engineering Leads", "BI Architects")
   - **Minimum number of approvals**: Set to 1 or more
   - **Timeout**: Set timeout (e.g., 24 hours) - pipeline will fail if not approved
   - **Instructions**: Optional message for approvers
5. Save the approval check

**Step 3: Optional - Add Additional Checks**

You can add additional checks:
- **Branch control**: Only allow deployments from specific branches
- **Required template**: Enforce specific pipeline templates
- **Work item**: Require linked work items
- **Exclusive lock**: Prevent parallel deployments

**Step 4: Configure Variable Groups**

1. Create variable group: `Fabric-Release-Variables`
2. Add variables:
   - `SPN_TENANT_ID` (Service Principal Tenant ID)
   - `SPN_CLIENT_ID` (Service Principal Client ID)
   - `SPN_CLIENT_SECRET` (Service Principal Secret - mark as secret)
   - `APPROVAL_NOTIFY_USERS` (optional: comma-separated email addresses)

**Approval Flow:**

1. **Build Stage**: Runs automatically, no approvals
2. **ReleaseTest Stage**: 
   - Waits for approval if `Fabric-TEST` environment has approvals configured
   - Approvers receive notification
   - After approval, deployment proceeds
3. **ReleaseProd Stage**:
   - Waits for approval if `Fabric-PRODUCTION` environment has approvals configured
   - Typically requires more approvers or higher-level approval
   - After approval, deployment proceeds

**Manual Approval Fallback:**

If environment approvals are not configured, you can enable manual approval tasks by setting `requireManualApproval: true` in the pipeline template parameters. This uses `ManualValidation@0` task as a fallback.

## Parameterization

### Using parameter.yml

1. Copy `resources/parameters/parameter.yml.template` to your repository directory root (per workspace/layer)
2. Update with actual IDs from your environments:
   - Dev IDs (find_value)
   - Test/Prod IDs (replace_value)
   - Use dynamic variables (`$workspace.$id`, `$items...`) where possible

### Generating Parameter Files

```powershell
# Generate parameter.yml from environment configs
python scripts/utils_build_parameter_file.py --environments dev,tst,prd --output ./solution/parameter.yml
```

**Note:** Review and update generated file with actual Fabric item IDs.

## Workspace Structure

After setup, you'll have workspaces per environment:

- **DEV:**
  - `DE_Lakehouse [dev]`
  - `DM_Core [dev]`
  - `BI_Apps [dev]`
  - `Shared_Datasets [dev]` (if configured)

- **TEST:**
  - `DE_Lakehouse [tst]`
  - `DM_Core [tst]`
  - `BI_Apps [tst]`
  - `Shared_Datasets [tst]`

- **PROD:**
  - `DE_Lakehouse [prd]`
  - `DM_Core [prd]`
  - `BI_Apps [prd]`
  - `Shared_Datasets [prd]`

## Workspace Target Picture (Network, Surge Protection, Item Types)

`fabric_setup.py` declares per workspace type what the setup itself does **not** apply, and
prints it after the workspaces are created. `--target-picture` prints the same as JSON without
authentication:

```powershell
python scripts/fabric_setup.py --environment prd --target-picture
```

Sources: Microsoft Learn, read 01.10.2026 (pages named per row). Declared in
`NETWORK_STANCE_BY_LAYER`, `SURGE_CLASS_BY_ENVIRONMENT`, `ALLOWED_ITEM_TYPES_BY_LAYER`; pinned
by `scripts/tests/test_workspace_target_picture.py` (golden files in `scripts/tests/fixtures/`).

| Workspace | Outbound access protection (OAP) | Allowed item types (target picture) |
|---|---|---|
| DE | open decision (lakehouse, notebooks, pipelines support OAP) | Lakehouse, Notebook, DataPipeline |
| DM | **on, with rules**: SQL Server rule for the DE lakehouse SQL endpoint FQDN, ADLS Gen2 rule for the DE OneLake URL; without them the refresh fails | SemanticModel |
| BI | **off**: reports bind to models in DM; under OAP a report binds only to a model in the same workspace (preview), and the OAP overview still lists reports as unsupported | Report |
| Shared | open decision | not restricted |

- **OAP preconditions** (`workspace-outbound-access-protection-overview`, `…-semantic-models`,
  `cicd/cicd-security`): tenant setting *Configure workspace-level outbound network rules*,
  F SKU (no trial), no unsupported item in the workspace, **Allow Git integration** on before
  any Git operation (setup connects the workspaces to Git), and a
  `PUT …/networking/communicationPolicy` must also send `inbound`, else it resets to Allow.
- **Release path**: `fabric_release.py` publishes through fabric-cicd (Items APIs), not through
  Fabric deployment pipelines, so "deployment pipelines are not supported with workspace
  inbound access protection" does not block it. With inbound protection the build agent must
  still reach Fabric from an allowed network.
- **Surge protection** (`enterprise/surge-protection`, workspace level in preview): prd
  workspaces `Mission critical`; dev/tst `Available` under the workspace CU limit of the
  non-production capacity. That limit is **one percentage per capacity** (rolling 24 h), held
  in `generic.surge_protection.workspace_cu_limit_pct`; it is `null` until the capacity admin
  sets it. Learn documents portal steps only, no API: OneLake catalog → Govern → Capacities.
  Learn contradicts itself on whether *Mission critical* is exempt from capacity-level surge
  protection (state table: yes; limitations: "doesn't override") — plan with "no".
- **Item creation policy** (`governance/fabric-policies-overview`, `fabric-policies-item-creation`,
  preview, capacity scope): one allow rule per restricted workspace plus a catch-all rule
  "all other workspaces", otherwise every other workspace on the capacity is blocked. Workspace
  conditions take workspace IDs (the JSON shows names as placeholders). **Not available in
  West Europe, North Europe and West US.** ANNAHME, ungeprüft: whether the policy also
  evaluates item creation by a service principal through the Items API (fabric-cicd), and
  whether the policy UI uses the same item-type spelling as the REST item types listed here.

## Deployment Plan (Preview)

A deployment plan orders items and runs pre-/post-deploy actions. Learn
(`cicd/deployment-plan/deployment-plan-automation`, read 01.10.2026): it is attached by adding
`options.deploymentPlan` to **Update From Git**, **Deploy Stage Content** or **Bulk Import Item
Definitions**, each with `?beta=true` and the additional scope `Item.Execute.All`; the same page
states that **the fabric-cicd library does not support deployment plans**.

`fabric_release.py --deployment_plan_logical_id <guid>` (off by default) therefore only works
with `--dry_run`: it prints the documented Bulk Import request per workspace
(`POST /v1/workspaces/{id}/items/bulkImportDefinitions?beta=true`,
`{"options": {"allowPairingByName": false, "deploymentPlan": {"logicalId": "<guid>",
"referenceType": "ByLogicalId"}}}`). A live release with the flag stops with exit 1 instead of
publishing without the plan. Take the logical ID from the plan's `.platform` file.

## Branch Workspace Admin Profile (Preview)

Learn `cicd/git-integration/branch-workspace-admin-profile` (read 01.10.2026): on a
Git-connected workspace, *Workspace settings → Git integration → Branch workspaces → Allow
branch workspace admin profile*. Branch-out then creates the workspace, assigns the capacity,
connects Git and adds members on the admin's behalf, so developers need no right to create
workspaces. It is an alternative to `feature_fabric_branch.yml` /
`fabric_feature_maintenance.py`.

- **Admins**: enter a **security group** (the field accepts users or groups), not a person,
  so branch workspaces keep an admin when someone leaves.
- **Consented identity is always a person**: every branch-out runs under the identity of the
  workspace admin who **last saved** the profile. Save it from a long-lived admin account, and
  re-check it after staff changes: a profile becomes invalid when that admin leaves the tenant
  or loses a permission.
- Not configurable on a branch workspace itself; the capacity and the Git repository must be in
  the same geography unless the tenant allows cross-region operations.

## Semantic Model Refresh After a Release

What the release automation does about refresh, and which refresh options exist beyond it.
Microsoft facts checked on Microsoft Learn on 29.09.2026.

```yaml
refresh_contract:
  on_demand_refresh_trigger: none          # no POST .../refreshes in scripts/ or ../orchestrator/
  schedule: orchestrator/deploy.ps1        # step 6, PATCH datasets/{id}/refreshSchedule
  schedule_scope: whole_model              # the schedule API has no table or schema option
  schema_sync_via_api: not_documented      # no refresh `type` for "Sync schema only"
  table_refresh_via_api: enhanced_refresh  # POST .../refreshes with "objects"
```

`scripts/tests/test_refresh_contract.py` compares this block with the code. If a script
starts to trigger a refresh, the test fails until this section describes it.

### What ALUCA triggers

- `scripts/fabric_release.py` publishes items with fabric-cicd and triggers no refresh.
- `../orchestrator/deploy.ps1` sets a refresh **schedule** (step 6, skip with `-SkipRefresh`).
  The schedule always covers the whole semantic model: the request body
  (`RefreshSchedule`) has only `days`, `times`, `enabled`, `localTimeZoneId` and
  `notifyOption` ([Update Refresh Schedule In Group](https://learn.microsoft.com/rest/api/power-bi/datasets/update-refresh-schedule-in-group)).
- Nothing in the pipeline starts an on-demand refresh. The first data load after a release
  comes from the schedule or from a manual step.

### Refresh options in Power BI Desktop and the service

The **Refresh** button in the Home ribbon and the Data pane offers three options
([Data refresh in Power BI, "Power BI refresh options"](https://learn.microsoft.com/power-bi/connect-data/refresh-data#power-bi-refresh-options)):

| Option | Effect |
|---|---|
| Refresh schema and data | Schema sync first, then data refresh (what **Refresh** always did before) |
| Sync schema only | Updates the model to the source structure (new columns, changed types) |
| Refresh data only | Loads fresh data and keeps the current model schema |

Each option also works for a single table: select the table and choose schema, data or both.
Desktop has had the options since the September 2025 update; the service followed with the
August 2026 update ("More control over semantic model refresh in Power BI Service", listed
without a preview mark in [What's new in Power BI](https://learn.microsoft.com/power-bi/fundamentals/whats-new)).

When to use which after a release:

- **Direct Lake, Lakehouse table gained a column the model should not show yet:**
  *Refresh data only*. A schema sync would bring the column into the model.
- **Release changed a single table:** refresh only that table instead of the whole model.
- **Source column renamed or removed:** *Sync schema only* removes it from the model and can
  break measures, relationships and RLS that depend on it. Align the TMDL in the repo first,
  release, then sync.

### Refresh by API (enhanced refresh)

For automation, the [enhanced refresh API](https://learn.microsoft.com/power-bi/connect-data/asynchronous-refresh)
(`POST https://api.powerbi.com/v1.0/myorg/groups/{groupId}/datasets/{datasetId}/refreshes`)
accepts in the request body:

- `type`: `full`, `clearValues`, `calculate`, `dataOnly`, `automatic` or `defragment`
  (aligned with the TMSL refresh types; `add` is not supported).
- `objects`: a list of `{"table": "..."}` or `{"table": "...", "partition": "..."}`. Without
  `objects`, the whole model refreshes.
- `commitMode`, `maxParallelism`, `retryCount`, `applyRefreshPolicy`, `effectiveDate`, `timeout`.

Limits compared with the UI options:

- No `type` is documented as a schema sync, so **Sync schema only** has no documented API
  equivalent. Do not equate the UI option **Refresh data only** with `type: dataOnly`;
  Learn documents no such mapping.
- `refreshType` is a **response** field of `GET .../refreshes` (`OnDemand`, `Scheduled`,
  `ViaApi`, `ViaEnhancedApi`), not a request parameter.
- Requires a Premium, Premium per user or Power BI Embedded model and the
  `Dataset.ReadWrite.All` scope; the service accepts one refresh per model at a time
  (`400 Bad Request` otherwise).

Example: refresh one table after a release (token audience as in
`../docs/references/fabric-api-core.md`, "Refresh triggern"):

```bash
az rest --method post \
  --resource "https://analysis.windows.net/powerbi/api" \
  --url "https://api.powerbi.com/v1.0/myorg/groups/$WS_ID/datasets/$MODEL_ID/refreshes" \
  --headers "Content-Type=application/json" \
  --body '{"type":"full","objects":[{"table":"FactSales"}]}'
```

## Troubleshooting

### Authentication Failures

- Verify service principal has Fabric Administrator role
- Check tenant_id, client_id, client_secret are correct
- Ensure Fabric CLI is installed: `pip install ms-fabric-cli==1.7.0`

### Workspace Creation Fails

- Verify capacity name exists in tenant
- Check capacity has available workspace slots
- Ensure service principal has capacity admin permissions

### Git Connection Fails

- Verify repository URL is correct
- For Azure DevOps: ensure service principal has repo access
- For GitHub: verify PAT has repo scope
- Check branch name exists in repository

### Release Fails

- Verify repository directory path exists
- Check `parameter.yml` has correct IDs (if using)
- Ensure workspace exists and is accessible
- Verify item types are supported by fabric-cicd

### Pipeline Fails

- Check pipeline variables/secrets are set correctly
- Verify Python version (3.9-3.12)
- Check Fabric CLI authentication in pipeline logs
- Ensure repository checkout succeeds

## Best Practices

1. **Start with dev:** Always test setup/release in dev first
2. **Use parameterization:** Avoid hardcoding IDs; use `parameter.yml` or dynamic variables
3. **Validate before release:** Run Stage 1 + Fabric checks before deploying
4. **Restrict production:** Limit who can deploy to production; use pipeline approvals
5. **Monitor deployments:** Check Fabric portal after release to verify items deployed
6. **Clean up features:** Delete feature workspaces when branch is merged/deleted

## Next Steps

- Review `fabric_architecture_best_practices.md` for architecture guidance
- Configure deployment rules in Fabric deployment pipelines (UI)
- Set up monitoring and alerting for deployments
- Document your organization-specific customizations
