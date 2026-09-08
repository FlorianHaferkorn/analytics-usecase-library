# Studio project authority and views

Status: implemented integration boundary, 2026-09-07. This record describes software behavior, not customer approval or deployment readiness.

## One interface, explicit sources

The header identifies the working view. Library examples remain reusable reference material; selecting a customer does not turn these examples into customer evidence. Project views read the selected project's validated, saved Project Package. Discovery and Package are always project surfaces. Library, its definition manager, and templates are library surfaces. Administration remains separate.

| Surface | Source and behavior |
| --- | --- |
| Overview | Selected revision's objectives, plan, effort basis and recorded decisions. No fabricated completion score. |
| Blueprint / Data lineage | Declared domains, use cases and data contracts. The current graph shows ownership, not a proven physical item-level data flow. |
| Approvals | Recorded recommendations, options and evidence from the selected revision. Viewing does not approve anything. |
| Health / Drift | Recorded observations and evidence. Absence of observations is not a clean tenant result. |
| Discover | Project-scoped SQLite draft with explicit Save and conflict detection. Draft evidence is not approved Package content. |
| Project Package | Existing Python-validated immutable repository; explicit load, edit, compare and save. |
| Generate | Approved project input release, or explicitly labelled library preview. These are different outputs. |
| Simulate | Library simulation remains available. Unsupported project simulation is explained rather than populated with unrelated examples. |

## Version and access contract

Project views pin a saved revision hash. `Load latest` is an explicit action. Switching project clears cached reference data, selection and the previous revision. Stale asynchronous responses cannot replace the current project's view. Session storage contains selection metadata only, not Discovery source contents.

`GET /api/projects/{projectId}/view` checks viewer access before loading a repository snapshot, verifies its project identity, and disables shared caching. The Python repository retains validation, hashing and decision authority; the TypeScript projection only prepares read-only display data.

The project selector lists only accessible projects. New project IDs use a snake-case-compatible UUID format; existing IDs are not renamed. No permissions are granted by this migration.

Legacy project-prefixed library and governance aliases fail closed instead of mutating or reading the global library under a customer URL. Implicit rewrites to a default project were removed. Existing unscoped library tools remain library tools; this change is not a complete security audit of every legacy endpoint.

## Consolidated navigation

Library offers Browse assets and Manage definitions. `/catalog` redirects to the management view and preserves supported deep-link parameters. Existing catalog capabilities are retained. Project Discovery does not expose the old global draft-branch writer.

## Release and persistence

See [Discovery persistence](DISCOVERY_PERSISTENCE.md) and [Project input release](PROJECT_INPUT_RELEASE.md) for storage, role checks, evidence semantics and recovery. Back up SQLite and the configured Package repository data root, including release attestations. Do not restore one by silently relabelling it as another project.

No database reset, customer decision change, tenant deployment, dependency installation or repository commit was performed for this integration. Existing user edits were preserved. Rollback must be selective because this checkout contains unrelated work; restoring the whole worktree is not a safe rollback plan.

## Acceptance evidence and remaining work

- Unit and route tests cover project/revision isolation, authorization-before-read, no shared caching and retired unsafe aliases.
- Browser fixture tests cover selection, reload, pinned revision, switching projects and Library consolidation. Fixtures are not a live customer-authorization test.
- Discovery tests cover real temporary SQLite persistence, concurrent-save conflicts and UI recovery; AI behavior is fixture-based, not a live provider quality assessment.
- Release tests exercise a real temporary Python repository and role-bound Studio routes. An input release is not evidence that a platform adapter or tenant deployment succeeded.

The next integration slices are explicit candidate-to-Package mapping with review and evidence retention, followed by target adapters consuming the pinned compiler input. Physical artifact-level architecture needs a corresponding governed input schema. Project simulation and automated reconciliation against live tenant state are not implemented by these views.

**Follow-up, 2026-09-07:** The first candidate-to-module mapping and bounded architecture
generation are now implemented. `/engagement` is the Delivery workspace; `/architecture`
renders Python-compiled project contracts and exposes released outputs. See
[E2E integration status](STUDIO_E2E_DELIVERY.md) for the exact implemented scope and
remaining gaps; the earlier paragraph records the preceding integration boundary.
