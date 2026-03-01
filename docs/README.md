# ActionReady Analytics Platform — Entry Point

This is the single public navigation entry for all audiences.

## For executives

- Start with: `docs/presentations/executive_summary.md`
- Full narrative: `docs/presentations/framework_overview.md`
- Current status and roadmap: `internal/presentation_status_and_roadmap.md`

## For implementers

- Core framework (tool-agnostic): `core/`
- Platform product (Fabric/Power BI): `products/fabric/powerbi/`
- Implementation playbook: `core/implementation_guides/playbook_strategy_to_first_report.md`
- Core stability contract (artifact roles, IDs, allowed edges): `core/strategy_operating_model/operating_model/core_constitution.md`

## For maintainers

- Shared tooling and checks: `tooling/`
- Maintainer-only strategy/CI/archive: `internal/`

## Quality gates

- **Stage 1 (mandatory):** `.\tooling\run_stage1_checks.ps1` — schema, factsheets, KPI/action consistency, governance. No merge or release without Stage 1 green.
- Full validation: `.\tooling\run_all_checks.ps1`
- Fabric-only checks: `.\products\fabric/powerbi\tooling\run_fabric_checks.ps1`

**Zero tolerance:** CI and release must not skip Stage 1. Branch protection should require the Stage 1 check to pass before merge. See [.github/workflows/stage1.yml](../.github/workflows/stage1.yml) and [internal/project_mgmt/BRANCH_PROTECTION.md](../internal/project_mgmt/BRANCH_PROTECTION.md).

## Prerequisite

Run once from repo root:

```powershell
cd tooling\validation
npm ci
```

## Structure at a glance

```yaml
core/        # tool-agnostic framework SSOT
products/    # platform/domain product packages
tooling/     # shared generation/validation/automation
showcases/   # reference implementations
docs/        # entry points and architecture
internal/    # maintainer-only CI, strategy, archive
```
