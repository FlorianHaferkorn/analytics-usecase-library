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
- Install dependencies: `pip install -r products/fabric_powerbi/deployment/resources/requirements.txt`

### 5. Fabric CLI

Install Fabric CLI:
```bash
pip install fabric-cli
```

## Configuration

### Step 1: Configure Environment JSON Files

Edit the environment configuration files in `resources/environments/`:

1. **`infrastructure.json`** — Base configuration:
   - Update `capacity_name` to your Fabric capacity name
   - Update `permissions` with your Azure AD group/user IDs
   - Adjust `fabric_connections` if needed

2. **`infrastructure.dev.json`** — Dev environment:
   - Update `git_settings` with your repository details
   - Update `permissions` for dev environment

3. **`infrastructure.tst.json`** and **`infrastructure.prd.json`** — Test and production:
   - Update `git_settings` (usually same repo, different branches)
   - Update `permissions` (more restrictive for prod)

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
cd products/fabric_powerbi/deployment

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
   - PR to `main` (builds and validates)
   - Push to `releases/release*` (builds → releases to test → releases to prod)
4. Manual runs also supported

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

## Troubleshooting

### Authentication Failures

- Verify service principal has Fabric Administrator role
- Check tenant_id, client_id, client_secret are correct
- Ensure Fabric CLI is installed: `pip install fabric-cli`

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
