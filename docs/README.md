# ActionReady Analytics Platform — Entry Point

This is the single public navigation entry for all audiences.

## For executives

- Start with: `docs/presentations/executive_summary.md`
- Full narrative: `docs/presentations/framework_overview.md`

## For implementers

- Core framework (tool-agnostic): `core/`
- Platform product (Fabric/Power BI): `products/fabric_powerbi/`
- Implementation playbook: `core/implementation_guides/playbook_strategy_to_first_report.md`

## For maintainers

- Shared tooling and checks: `tooling/`
- Maintainer-only strategy/CI/archive: `internal/`

## Quality gates

- Stage 1 (mandatory): `.\tooling\run_stage1_checks.ps1`
- Full validation: `.\tooling\run_all_checks.ps1`
- Fabric-only checks: `.\products\fabric_powerbi\tooling\run_fabric_checks.ps1`

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
