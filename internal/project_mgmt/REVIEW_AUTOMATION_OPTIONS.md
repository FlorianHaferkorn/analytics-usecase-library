# Review automation options

**Purpose:** What is already automated in the PR review flow, and how to add more (including optional LLM-based review).

---

## Current automation (every PR)

| Check | Where | Runs |
|-------|--------|------|
| **Stage 1** | [.github/workflows/stage1.yml](../../.github/workflows/stage1.yml) | On every `pull_request` and `push` to main. Blocks merge if configured as required. |
| **Closes #N** | [.github/workflows/pr_review_summary.yml](../../.github/workflows/pr_review_summary.yml) (job `check-closes-issue`) | On every PR; fails for delivery-style PRs that lack Closes #N. |
| **PR summary comment** | Same workflow (job `summary`) | Posts/updates the review summary comment with "Automated checks" and "Manual: Reviewer Agent". |

So for every new PR: Stage 1 and Closes #N run automatically; the only non-automated step is the **Reviewer Agent** (rules/skills/scope judgment in Cursor).

---

## Making Stage 1 a required check

To enforce that PRs cannot be merged when Stage 1 fails:

1. GitHub repo → **Settings** → **Branches** → branch protection rule for `main`.
2. Under **Require status checks to pass before merging**, add the check **Stage 1 checks** (the job name from stage1.yml).
3. Save.

Then every PR must have Stage 1 green before merge.

---

## Option B: LLM-based automated review (optional)

To automate the *content* of the Reviewer Agent (rules/skills alignment, scope, PR metadata) in CI, you need a workflow that:

1. Fetches the PR diff and description.
2. Calls an LLM API (OpenAI, Anthropic, etc.) with a system prompt derived from [.cursor/rules/reviewer-agent.mdc](../../.cursor/rules/reviewer-agent.mdc).
3. Posts the model output as a PR comment.

**Requirements:**

- A secret (e.g. `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`) in the repo.
- A new workflow, e.g. `.github/workflows/pr_review_llm.yml`, that runs on `pull_request` and:
  - Uses the API to generate a short structured review (checklist, findings, verdict).
  - Posts it with a marker like `<!-- pr-review-llm -->` so it can be updated on each push.

**Trade-offs:**

- Cost and rate limits of the API.
- The model does not have access to your full `.cursor/rules` or repo context unless you inject them into the prompt; you may need to paste the checklist from reviewer-agent.mdc into the workflow.
- Optional: run only when the secret is set, so the workflow file can live in the repo but do nothing if the key is not configured.

If you want this, the next step is to add `pr_review_llm.yml` (skeleton that checks for the secret and, if present, calls the API and posts the comment).
