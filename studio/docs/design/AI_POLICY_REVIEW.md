# AI policy review boundary

The Project Package may contain an optional `ai_data_handling` module. Its route is bound to an approved `decision_set` instance and exact route hash by the Python package validator. That package content is still editor-controlled; it is decision input, not independent permission for model egress.

## Team review

1. An editor saves the complete package in `in_review` or `approved` state and submits a named AI route from the Project Package screen.
2. Studio pins the current repository HEAD, checks the decision/ADR scope, exact route hash, provider evidence and expiry, and records a `pending` review with project, revision and route hash.
3. A different project administrator reviews the saved policy and evidence, then approves or rejects with a reason of at least 20 characters. The same identity cannot submit and approve. The decision and metadata are audit-logged; prompt or document contents are not logged in this review.
4. A newer package revision never inherits the prior review. A changed route requires a new submission even if its route ID is unchanged. A rejected route may be submitted again.

`GET /api/projects/{projectId}/ai-policy-reviews` lists the latest review receipts for project viewers. `POST` accepts only `submit` with `revisionHash` and `routeId`, or `approve`/`reject` with a saved `reviewId` and rationale. The server enforces editor/admin roles and the two-person rule; the buttons in the browser are only affordances.

## Explicit non-claims

- An approved review **does not enable AI egress**. The current model routes remain default-deny.
- A package-declared provider region or local URL is not runtime proof of provider location, network routing, retention or training terms.
- The exact outbound payload, resolved provider/model and streamed output still need enforcement and tests before any route can be opened. Scanner findings alone are not a safe allow decision.
- SQLite audit chaining is local tamper evidence, not an external WORM log or customer approval.
- Project admin access follows Studio's current authentication and RBAC. Enterprise identity/session hardening and attributable customer authorization remain separate deployment prerequisites.
