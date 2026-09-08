# Project Discovery drafts

Discovery is a project surface, not an editor for the shared library. The selected project ID determines both the authorization boundary and the persistence key. There is no fallback to a global project when loading or saving fails.

## User workflow

1. Select a project with a project role. Viewers can read and download; editors can change evidence and use the configured AI provider.
2. Add text sources or an explicitly selected library use case as reference material. Library material is copied as source evidence; this does not change the library definition.
3. Ask a question. The project-scoped AI route receives only the supplied project sources and conversation. It uses that project's configured model resolution and usage attribution.
4. Review suggested candidates. Every candidate is a draft. A source link and a verified exact quote are separate from business approval. Missing citations remain visibly unverified; the first source is never assumed to be evidence.
5. Save the draft explicitly. Sources, completed conversation messages and candidates are restored after reload. If another session saved a newer draft, saving returns a conflict; local changes are retained and can be downloaded before a deliberate reload.
6. Download draft evidence as JSON for handoff. The export includes project ID, saved revision, draft status and whether unsaved changes are included. This is not an approved deployment or library-change package.

## Authority and storage

- API: `GET/PUT /api/projects/{projectId}/discovery`; `POST /api/projects/{projectId}/discovery/chat`.
- Server authorization: `requireRole('viewer', projectId)` for read; editor for save and AI requests. No membership fallback or inferred grant is added by this implementation.
- Existing SQLite `discovery_sessions` table is reused without migration. New workspace drafts use `workspace:{projectId}` with an explicit `project_id` predicate on reads and writes. Existing historic sessions are not overwritten or silently relabelled.
- JSON schema validation rejects extra fields, invalid kinds, approval claims and oversized arrays/fields. Additional checks enforce unique source/candidate IDs, valid source references and exact quoted text.
- SHA-256 content revision is required for compare-and-save in a SQLite transaction. Audit events capture actor, project, old/new revisions and counts, not source content.
- Schema, storage and UI preserve the distinction between draft evidence, a candidate suggestion and an approved governed artifact.
- Unsaved drafts survive project switches within the mounted Discovery surface in memory only. A before-unload guard and `studio:unsaved-discovery` event support the shell's navigation warning. Saving remains the persistence boundary; do not rely on an unsaved browser tab as storage.

## Deliberate limits

- The former global “Create draft branch” action is not exposed from project Discovery because it bypasses project-package scope. The draft JSON handoff is available now; automatic candidate-to-package mapping must use an explicit governed schema and review step.
- Candidates are parsed from the documented `Source`, `Quote`, `kpi_id/name`, `action_id/name` and `Strategy anchor` text contract. Arbitrary prose is retained in chat but is not considered a structured candidate. This does not certify AI extraction accuracy or catalog compatibility.
- Text formats only: TXT, MD, CSV, YAML and YML. Per-file limit 10 MB, total saved request limit 12 MB, 50 sources, 200 messages and 500 candidates. The UI reports server validation failures and retains the local draft.
- No live AI-provider call, customer-role grant, customer acceptance or tenant deployment is performed by the automated tests.

## Verification

- Native SQLite tests close/reopen a temporary database, verify project isolation, stale-write rejection and preservation of invalid stored rows.
- Route tests verify role checks before any read/write, explicit project binding and rejected invalid/approved candidate payloads.
- Component tests verify reload, unsaved project-switch isolation, late-response rejection, read-only roles, conflict preservation and access-denied states.
- Chromium fixture tests exercise source import, dialogs, chat text, candidate evidence, Save, reload and draft download without contacting an AI provider.
