# Deployment (setup / teardown by code)

Goal: make the Fabric/Power BI implementation **easy to create and delete** (idempotent, parameterized, environment-aware).

## Architecture and best practices

**See:** `implementations/microsoft_fabric_powerbi/guide/fabric_architecture_best_practices.md`

That document defines workspace strategy (DE_/DM_/BI_/Shared), repo and Git strategy, CI/CD pipeline design (Stage 1 + Fabric checks; optional setup/release automation), governance, and adoption paths (minimal → standard → full). It aligns with FabCon/FabricAutomation patterns and this framework.

## Implementation Status

**V1 Complete** — Fabric CLI + Python automation with Azure Pipelines integration.

### Implemented Components

- **Environment definitions:** `resources/environments/` — Base + dev/tst/prd JSON configs
- **Workspace provisioning:** `scripts/fabric_setup.py` — Creates workspaces (DE_/DM_/BI_/Shared), connections, Git integration, permissions
- **Release automation:** `scripts/fabric_release.py` — Deploys PBIP/TMDL items from Git to Fabric using fabric-cicd
- **Parameterization:** `resources/parameters/parameter.yml.template` — Environment-specific value replacement
- **CI/CD pipelines:** `.azure-pipelines/` — Build, release (multi-stage), setup, feature branch workflows
- **Helper modules:** `scripts/modules/` — Fabric CLI wrappers, JSON utilities
- **Documentation:** `USAGE.md` — Setup and usage guide

### Quick Start

**Test without Fabric capacity:**
```powershell
.\scripts\test_without_fabric.ps1 --environment dev --Simulate
```

**With Fabric capacity:**
1. **Configure environments:** Edit `resources/environments/infrastructure.*.json`
2. **Validate config:** `python scripts/validate_config.py --environment dev --simulate`
3. **Run setup:** `python scripts/fabric_setup.py --environment dev`
4. **Release items:** `python scripts/fabric_release.py --environment dev --repo_path ./solution`

See `USAGE.md` for detailed instructions.

### Architecture Decision

**Chosen:** Fabric CLI + Python (aligned with [FabricAutomation](https://github.com/peerinsights/FabricAutomation) patterns)

**Rationale:**
- Fabric CLI provides stable API abstraction
- Python ecosystem (fabric-cicd) handles item dependencies and parameterization
- Reuses proven patterns from FabricAutomation
- Easy to extend and maintain

**Future considerations:**
- Terraform provider (when Fabric provider matures)
- PowerShell + REST APIs (if team prefers PowerShell)
