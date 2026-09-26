# Draft alternative impact against a released baseline

Status: implemented in the decision engine and in Studio (WB-008). No tenant execution, no approval, no release.

## Purpose

WB-008 requires that a draft alternative shows its effect on impacts, plan, staffing, architecture, manifests and tests without changing the accepted baseline. The reviewed derivation ([PROJECT_DECISION_DERIVATION.md](PROJECT_DECISION_DERIVATION.md)) only applies approved decisions. The alternative comparison answers the question before that point: what would change if the alternative were chosen, and what must happen before it could be released.

## Behavior

`compare_alternative(repository, project_ref, baseline_revision, decision_ref, option_ref)` in `tooling/superversion/project_package/alternative_impact.py`:

1. Verifies the baseline is the current HEAD and has a release attestation. It reads the attestation; it never writes one.
2. Requires the baseline decision to be approved and confirmed, the alternative option to be declared for that decision, and the alternative to differ from the baseline selection.
3. Evaluates the authored decision rules on an in-memory copy with the alternative selected. The same rule engine as the reviewed derivation runs, including every blocker: topology presence, plan effects, stale preconditions, completed tasks with evidence.
4. Projects baseline and alternative side by side and reports the differences.
5. Fingerprints repository history, HEAD and release records before and after. Any change raises an error.

| Impact class | Reported as |
|---|---|
| Architecture | Added and removed environment stages |
| Plan | Before/after of work packages and acceptance tasks linked to the decision |
| Staffing | Role demand delta and effort totals by unit; named staffing, rates and duration are not evaluated |
| Topology | Per detailed domain and stage: selected and authored, selected but missing, authored but unselected |
| Manifests | Added, removed and changed projected workspace request and item definition hashes |
| Tests | Decision-impact checks before/after, lane acceptance criteria, execution obligations (workspace readback, item environment bindings) |

`obligations` lists what remains before the alternative could be released: a new decision revision and approval, the reviewed derivation, a new input release, topology to retire or author, and acceptance criteria to reconfirm. `status` is `impact_ready` or `blocked`; `approval_granted`, `release_granted` and `tenant_actions_performed` are always false.

## Reference fixture

`core/fixtures/neutral/alternative-impact-reference/` is synthetic and customer-neutral: an invented industrial equipment manufacturer with a sales domain (order to cash) and a finance domain (general ledger). The declared source system is SAP S/4HANA; standard table names serve as contract labels only. No SAP system, SAP demo data, real organisation, customer, tenant or extract rows are included. The Meridian SAP standard packs are not copied; see the IP boundary in [SHARED_SUBSTANCE.md](../../../SHARED_SUBSTANCE.md).

The accepted baseline is DEV / TEST / PROD for both domains; the draft alternative is DEV / PROD. The reverse direction is also covered: an expansion without authored TEST topology is blocked and names the missing workspaces, and with authored topology it adds manifests, role demand and test obligations.

## CLI

```text
py -3 -m tooling.superversion.project_package.alternative_impact --schemas tooling/generator/schemas
py -3 -m tooling.superversion.project_package.alternative_impact --schemas <trusted> --repository <trusted>
```

Without `--repository` the synthetic reference is built in a fresh temporary directory and compared. With `--repository`, stdin takes `{project_ref, revision_hash, decision_ref, option_ref}`. Output is `{ok: true, value}` or `{ok: false, error, status: 409}`.

## Verification

`tooling/tests/test_project_alternative_impact.py`: byte-identical repository and release records after comparison, all impact classes, determinism, blocked expansion without topology, expansion with authored topology, missing alternative mapping, completed task with evidence, invalid options, unreleased or non-HEAD baseline, unknown decision, foreign project, fixture neutrality and the CLI. Network and process creation are forbidden during the comparison.

## Studio

**Architecture → Decision effects → Compare an alternative.** The panel appears when the decision review lists a rule with status `not_selected`, i.e. an authored mapping for an option that is not the accepted one. Selecting it calls `GET /api/projects/{id}/architecture/alternatives?revision=&decision=&option=` (viewer role, `private, no-store`). The route accepts only a pinned revision hash and two identifiers; it rejects any result whose project, revision, decision or option differ from the request, or that claims approval, release, tenant action or a changed baseline.

The view follows a bill-of-materials reading order: summary tiles (stages, role demand, effort, parts, test obligations), a parts list of the workspaces and native items that are added or removed, the delivery-plan changes, the test obligations, and the ordered steps before the alternative could be released. An unreleased or non-HEAD revision shows the engine's refusal instead of a comparison.

Files: `studio/src/lib/bridge/project-alternatives.ts`, `studio/src/app/api/projects/[projectId]/architecture/alternatives/route.ts`, `studio/src/components/project/project-alternative-impact.tsx` (+ module CSS, governed by the design-token gate). Tests: `studio/tests/api/project-alternatives.test.ts`, `studio/tests/components/project-alternative-impact.test.tsx`, one case in `project-decision-review.test.tsx`.

## Remaining scope

- Browser workflow against the real engine is recorded as an opt-in test, not part of the standard suite: `studio/e2e/alternative-impact.spec.ts` with `playwright.alternative-impact.config.ts`. It signs in with the demo login, creates a Studio project, builds the synthetic reference under that project (`alternative_impact --build-reference <dir> --project-ref <id>`), and checks through real routes and the real Python engine: the comparison response, tiles, all six parts, the topology step, no write request, no runner or deployment request, no page error, and no horizontal overflow at 768 px. Passed on 26.09.2026 in 25.9 s; desktop and narrow screenshots inspected.

  ```powershell
  # server (separate shell): fresh data root, dedicated .e2e database
  $env:STUDIO_PACKAGE_DATA_ROOT = '<new empty temp dir>'; $env:STUDIO_DB_PATH = '.e2e/alternative-impact.db'
  node scripts/reset-studio-db.mjs; npx next dev -p 3107
  # test
  $env:STUDIO_ALTERNATIVE_IMPACT_E2E = '1'; $env:STUDIO_E2E_PORT = '3107'; $env:STUDIO_PACKAGE_DATA_ROOT = '<same dir>'
  npx playwright test --config=playwright.alternative-impact.config.ts
  ```
- Named staffing, proposal assumptions, duration and cost drivers belong to WB-009.
- Fabric runtime behavior is proven separately in an isolated test tenant with synthetic data and its own identities. The comparison never contacts a tenant.
- The rule engine still cannot add or remove topology elements. The comparison reports these as obligations instead of generating them.
