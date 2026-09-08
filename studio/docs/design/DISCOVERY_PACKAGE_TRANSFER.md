# Reviewed Discovery to Project Package

## Authority and workflow

Discovery remains an editable, project-scoped evidence draft. In Extracted Elements, **Review for Project Package** opens a review of the saved Discovery revision and current Package HEAD. The reviewer selects exact-quote-backed candidates, reads the source excerpts, supplies a rationale and explicitly confirms the change.

An editor can map a selected strategy anchor to a draft project objective. The preview shows the exact objective list before and after. Python appends the objective without duplicates, changes opportunity scope to `draft`, adds a source reference to the review dossier and commits a new `working` Package revision. Overview then reads that pinned revision. Existing customer decisions are not changed or approved.

KPI and action suggestions can be preserved as proposals, but are not automatically registered, approved or referenced as governed definitions. A name match is not proof of identical business meaning. Their registry mapping remains a separate review step.

## Evidence and concurrency

- `GET /api/projects/{projectId}/discovery/transfer` requires editor access and returns the current validated Package revision and objective list.
- `POST` accepts `discoveryRevision`, `expectedHeadRevisionHash`, `candidateKeys`, `objectiveKeys`, `rationale`, and `confirmed`.
- The server takes the document from its saved project draft and the actor from authentication. Client-supplied evidence, actor or project identity cannot override them.
- A changed Discovery revision is rejected before transfer. The captured saved revision is then an immutable input to that transfer, even if subsequent drafting continues. Concurrent Package changes are rejected by Python's locked optimistic commit.
- Only linked, exact source quotes pass the transfer gate. The versioned dossier contains selected candidates, exact source snapshots, source content hashes, reviewer, rationale and module mapping.
- Duplicate selections or overlaps from the same Discovery revision are rejected. A later Discovery revision is new evidence and can be reviewed again; repeated objective strings are not duplicated.
- Review dossiers live under `discovery/reviews/` as supplementary versioned files. No Project Package 2.0 schema semantics or observed-target-state records were changed.

## Boundaries

This is an evidence-to-draft-objective vertical slice, not automatic requirement acceptance, registry authoring, architecture inference or deployment authorization. A Package must already exist. No tenant call occurs. Repository history and input exports preserve the dossier; downstream compilers must not treat its proposals as approved definitions.

## Validation

Python integration tests use a real temporary immutable repository to verify source preservation, objective mapping, module isolation, working state, stale HEAD, duplicates and mismatched projects. API tests verify editor authorization, server-owned inputs and conflicts. A Playwright fixture tests selection, before/after preview, confirmation and revision-pinned transfer without live AI or customer data.
