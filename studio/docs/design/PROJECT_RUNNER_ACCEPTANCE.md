# Workspace readiness and first acceptance procedure

Status: implemented as read-only Studio diagnostics and a guided, exportable review protocol. No host was enabled and no tenant test was performed by this implementation.

## Operator path

Open **Automation → Deployment preflight** for the selected project version. The page now follows this order:

1. **Runner readiness**: resolve configuration blockers and distinguish them from operational evidence not yet verified.
2. **Workspace deployment preflight**: supply explicit target observations and inspect the exact operations.
3. **Protected workspace execution**: save the reviewed approval, then separately confirm execution only after actual test authorization.
4. **First workspace acceptance**: open the six-step procedure and download its project/version-scoped JSON review protocol.

Preparing, rechecking or downloading does not initiate sign-in, request a Fabric token, execute a CLI command, create resources or change host settings. The existing protected approval and execution actions remain separate operations.

## Readiness contract

The status response includes `checked_at` and checks with `id`, `title`, `state`, `detail` and `action`. Host status explicitly reports `readiness_scope: configuration_only` and `tenant_actions_performed: false`.

| State | Meaning | What it does not establish |
|---|---|---|
| Configured | The specified local configuration or reference check succeeded | Valid credentials, compatible CLI operation, effective Fabric permissions or acceptance |
| Action needed | A prerequisite is absent or access/configuration could not be checked | Permission for Studio to install dependencies, change identities or enable the host |
| Not verified | Independent operational evidence is required | A failed tenant test; diagnostics do not run such a test |

Authenticated diagnostics combine four Studio checks with twelve host checks. Studio checks cover provider/project access, minimum session-secret configuration, recent sign-in and exact origin. Host checks cover policy, project scope, independent approval/execution roles, signing and identity references, SDK metadata, CLI discovery and storage-path metadata. Actual identity/permissions, host protection/recovery and tenant acceptance remain not verified.

On an access failure, the original HTTP refusal remains and only a safe access remediation is returned; private host configuration is not inspected. On an authenticated host failure, Studio reports a host-configuration/runtime blocker without exposing paths, secrets or raw subprocess diagnostics. Rechecking is manual and read-only.

Approval and execution keep independent actor allowlists. An approval-only operator is not blocked from approving merely because execution authority belongs to someone else. Neither configuration labels nor the protocol grant either permission. Server-side guards and the protected host remain authoritative.

## Six acceptance cases

| Case | Procedure | Required outcome and retained evidence |
|---|---|---|
| Authorize the test | Agree one disposable DEV or TEST workspace, exact tenant/principal, capacity/domain assignment and recovery owner; review its plan | Dated authorization and exact target/plan hash. The suggested first-create scope requires exactly one create operation; PROD and broader plans are outside this procedure |
| Confirm host prerequisites | Resolve configuration blockers; independently review private ACLs, secret management, backup/restore, identity and permissions | Dated operational review. A present secret reference or discovered executable is not proof of usability |
| Create and read back | Save the exact approval; separately confirm the authorized execution; retrieve the saved outcome | `workspace_verified` plus matching target IDs/names/assignments in signed host records and per-operation receipts. `completed` alone is insufficient |
| Repeat planning | Obtain a fresh observation from the same trusted identity and rebuild against the same released contract; never replay a consumed approval | No-change operations, unchanged workspace IDs and no duplicates. Imported observations require independent review |
| Recover | Reload and retrieve the saved ID. Rehearse interrupted claims separately using an isolated host with a fake tenant client; verify disabled-policy evidence retrieval | No additional execution after reload; one-shot claim cannot replay; evidence survives interruption. Do not inject faults into a customer run |
| Reconcile and accept | Review actual results, close uncertain attempts and agree retention or explicit cleanup | Dated acceptance in the project authority. The runner never deletes resources automatically. Workspace acceptance does not cover items, data, security or CI/CD |

Each case in the Studio procedure includes the action, expected result and evidence to retain. No user checkbox can mark a case accepted. A matching `workspace_verified` result becomes **Evidence available**, not acceptance. A no-op plan becomes **Review required**, not proof of a successful live rerun. Foreign project/revision or mismatched result bindings are excluded from the protocol.

The download is `kind: workspace_acceptance_review_protocol`, `authoritative: false`, `acceptance_status: not_accepted`. It contains bounded scope, current plan/approval/result identifiers and the six procedures; it does not contain credential values or raw host configuration. It is neither signed execution authority nor a replacement for retained host evidence. Historical acceptance storage and automatic evidence aggregation across runs are not implemented here; record formal acceptance in the existing project authority.

## Reproducible offline checks

From the repository root:

```powershell
py -3 -m pytest tooling/tests/test_project_runner_host.py tooling/tests/test_project_protected_runner.py tooling/tests/test_project_deployment_plan.py -q
```

From `studio`, with the existing local development server running:

```powershell
npx vitest run tests/api/project-runner.test.ts tests/lib/runner-access.test.ts tests/lib/runner-acceptance.test.ts tests/components/project-runner.test.tsx tests/components/project-runner-readiness.test.tsx
$env:PLAYWRIGHT_REUSE_SERVER='1'
npx playwright test e2e/project-runner.spec.ts e2e/project-automation.spec.ts --workers=1
```

The Python tests use fake credentials/tenant clients and temporary private state. Chromium tests use API fixtures, check desktop and narrow layout, inspect the downloaded protocol, preserve input focus after plan changes, and exercise approval, uncertain response and reload recovery. These commands are implementation checks, not live tenant acceptance. Reuse the server to avoid the test configuration's database-reset startup path.

## Design-system pattern and limitations

The surface reuses `StudioPanel` and `StudioButton`, with shared spacing, typography, surface and status tokens. Blockers appear first, while configured checks and detailed procedures are expandable. Text labels convey states independently of color. Native disclosure elements remain keyboard-operable; the refresh button is disabled while a check or mutation is pending. Plan changes clear execution intent without remounting the planning inputs.

No new library, autonomous host repair, live test launcher, fault injection or cleanup endpoint was added. Host setup, target authorization and actual tenant evidence are the next operational gate. See [host configuration](PROJECT_RUNNER_HOST.md) and [end-to-end completion gates](STUDIO_E2E_DELIVERY.md).
