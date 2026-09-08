# Studio product audit remediation

Scope: Studio interaction, hierarchy, readability and design-system enforcement. Customer decisions, source KPI definitions, authorization policy and tenant resources are unchanged. This is not a whole-product accessibility or production-readiness certification.

## Implemented sequence

| Work package | Implementation | Verification |
| --- | --- | --- |
| Graph and filters | Existing React Flow dependency replaces custom viewport/edge handling. Real bounds-based Fit, zoom, keyboard selection, inspector and searchable full-label list. Layout and rendered node dimensions match. Focused use cases use compact left-to-right layout; the first available use case is selected initially, with all use cases still available. Metrics use the same filtered set. | `e2e/canvas-interactions.spec.ts`; desktop/narrow browser review |
| Discovery | Validated file drop; native accessible dialogs with Escape, focus return and Tab containment; aligned columns; readable loaded messages and extraction; correct plain-text stream contract; workflow advances only after parsed candidates exist. | `e2e/discovery-interactions.spec.ts`; Discovery unit tests, including split UTF-8 chunks |
| Error states | Package loading/401/403/errors do not imply zero data, synchronization or readiness. Retry and recovery guidance; writes disabled while unavailable. Value assumptions distinguish unavailable from failed/loading and are explicitly illustrative. | Package and value-assumption component tests; live permission-denied UI review |
| Design system | Semantic primitives, supported tone variants, labelled inputs, keyboard segmented controls, resolved token cycles and density inheritance. Optional assumptions no longer permanently consume graph width. | Primitive tests, token-rule tests, TypeScript and targeted ESLint |
| Page hierarchy | Simulator prioritizes scenario, results and drivers, retaining a short illustrative-data disclaimer. Detailed reasoning is collapsible. Overview identifies library scope, prioritizes a next task and does not claim project readiness. | Overview/simulator/navigation component tests and responsive route checks |
| Language and navigation | Simulate instead of Compose; one Data lineage entry with preserved deep links; Decision guides, Improvement proposals, readable saved-version wording, consistent ALUCA Studio login/page title. Collapsed global controls retain accessible names. | Route checks and visual review |
| Simulation correctness | Negative and zero baselines have usable, increasing slider ranges. Percentage-point deltas and grouped values use explicit unit metadata. Unchanged results and zero impacts are neutral. | Twelve targeted tests, scoped ESLint and narrow browser inspection |

## Verification record

- All sixteen listed routes were checked at 1440 × 900, 1024 × 768 and 768 × 900. Initial failures were corrected and the affected cases rerun successfully.
- Graph interaction and optical checks: five tests passed, including a 560-pixel viewport, list-row content bounds, keyboard selection and node fit. Updated optical references were inspected.
- Authentication, navigation and shell interaction checks: eight tests passed. Value-assumption loading from its actual route passed separately.
- Discovery: four browser tests and eighteen unit tests passed. Shared components and error-state coverage: nineteen tests passed. Token enforcement: nine rule tests passed.
- Final simulator responsive rerun: three browser tests passed after the range/formatting corrections. TypeScript and the token gate also passed on the final state; scoped ESLint passed for the modified components. Tests use the existing local server, fixtures where indicated, and no live AI provider request.

## Repeatable checks

Run from `studio`. Use `PLAYWRIGHT_REUSE_SERVER=1` only when deliberately testing the existing local server; the default Playwright configuration starts an isolated test database.

```text
npx tsc --noEmit
node --test tooling/check_tokens.test.mjs
npm run lint:tokens
npx playwright test e2e/studio-quality.spec.ts e2e/canvas-interactions.spec.ts e2e/discovery-interactions.spec.ts
npx playwright test e2e/design-system-optical.spec.ts
```

Optical references are updated only after inspecting the intended change. A regenerated screenshot is not, by itself, an acceptance test. Failed assertions during migration must be corrected and rerun, not masked or silently omitted.

## Follow-up implementation: project authority and legacy migration

The functional follow-up separates Library reference data from project evidence throughout the shell. Project-backed views pin a saved Package revision; changing projects clears the previous data. Discovery now saves project-scoped drafts with conflict recovery. Generate offers an explicitly attested, approved-input release rather than passing a customer URL into the global library exporter. Library and definition management now share one navigation entry. See [Project authority and views](PROJECT_AUTHORITY_AND_VIEWS.md), [Discovery persistence](DISCOVERY_PERSISTENCE.md), and [Project input release](PROJECT_INPUT_RELEASE.md).

The design-system and testing skills guided semantic-component migration and negative-path tests. The architecture skill guided the separation between reusable references, draft evidence, approved input and actual deployment. These are implementation rules, not customer decisions.

### Follow-up verification

- Final focused unit/route/component runs: 50 tests passed. Nine token-rule tests, TypeScript, the token gate and scoped ESLint passed.
- Browser coverage: 48 route/viewport checks, three graph interactions, illustrative-assumption loading, three shell checks, one project-switch/revision workflow and five Discovery interactions. All covered cases passed, including corrective reruns; this is not a claim of one uninterrupted green run.
- The first concurrent development-server run returned four page HTTP 500 responses. All four passed in the complete sequential route rerun, without weakening the HTTP-error assertion. Their underlying cause was not established, so production stability is not certified by that rerun.
- The graph-height assertion initially failed after adding the source indicator. Compact header spacing was corrected; the same assertion then passed without changing its threshold.
- Browser screenshots of the compact Blueprint, project Overview/architecture and loaded Discovery were inspected. Project fixtures verify display and isolation, not customer approval. No live AI-provider call was made.
- Evidence directories: `.e2e/final-product`, `.e2e/final-rerun`, `.e2e/graph-height-final`, `.e2e/project-final`. These are local test outputs, not customer deliverables.

## Remaining constraints

- A complete portfolio graph cannot show hundreds of full labels legibly in one viewport. Fit is an overview, not a reading-size guarantee. Use-case focus, 100% zoom, the inspector and List serve different tasks; the list preserves full names without scaling.
- Twenty files are under strict token rules. Across 425 inventoried source files, the tracked small-text and literal-color backlog is now zero; the baseline contains no findings. Eight exact theme-data exceptions remain because they represent editable theme values. This gate does not certify all CSS, contrast, content or accessibility behavior.
- The current AI endpoint streams text, not structured tool-result events. Text streaming and candidate parsing are tested with fixtures; live provider success and structured tool execution are not claimed.
- The current demo account lacks access to the default project package. The error experience is verified; authorized package delivery is covered by response-fixture/component tests, not a newly granted live role.
- Project Overview now reads recorded objectives, decisions, work packages and effort from the pinned Package. Missing plan data stays missing; this is not automatic scheduling or live release certification.
- The broader product audit is not fully closed. Automatic reviewed Discovery-to-Package mapping and target adapters consuming the pinned compiler input remain separate implementation slices. Physical artifact-level graphs and project simulation need corresponding governed inputs. The current approved-input download is not a deployable Fabric blueprint.
- No dependency, authorization grant, customer naming rule, deployment or repository commit was added by this remediation.

Related contracts: [Quality standard](STUDIO_QUALITY_STANDARD.md), [Dialog](STUDIO_DIALOG.md), [Token enforcement](../design-system-enforcement.md).
