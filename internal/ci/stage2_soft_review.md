# Stage 2 Soft Review (planned)

Stage 2 is a non-blocking, tool-agnostic "Soft CI Report" that produces a short, human-readable review summary. It never blocks merges and does not introduce new framework rules.
Stage 2 analyzes prose and narrative content only. Structured YAML/JSON validation is exclusively handled by Stage 1.

## Scope (what Stage 2 reviews)

Stage 2 checks only for:
- Possible contradictions between changed docs and SSOT/policies
- Ambiguous authority statements (who/what is authoritative)
- Drift red flags in prose (e.g., KPI meaning redefined outside catalog)
- Confusing optional vs required wording (core vs extended)

Stage 2 explicitly does **not**:
- Enforce style/formatting (markdownlint)
- Re-run Stage 1 checks
- Discuss implementation tools (DAX/TMDL/Fabric, etc.)
- Propose new artifacts or V2 features

## Inputs (diff-only)

Stage 2 consumes only changed files and an optional, fixed context set:
- `diff.patch` (required): unified diff containing only changed files
- `context_files[]` (optional, max 4): fixed references configured by repo
- `file_filters[]` (optional): include/exclude path rules
- `max_findings` (optional, default 10)

See: `tooling/stage2_review/stage2_review.contract.json`

## Outputs (stable format)

Stage 2 outputs a capped list of findings using a stable JSON schema:
- `finding_id` (deterministic)
- `severity` = high | medium | low
- `category` = consistency | authority | drift | wording
- `file`
- `location` (line or section, if available)
- `evidence` (max 200 chars)
- `risk` (1 sentence)
- `suggested_fix` (1 sentence)

Schema: `tooling/stage2_review/stage2_findings.schema.json`
Severity indicates review attention, not urgency or correctness.

### Human-readable rendering guideline

- Summary: 1-2 lines
- Top findings: max 10, each 1-2 lines
- No long explanations

## Provider-agnostic adapter concept (no implementation)

Stage 2 can run with:
- `provider = none` (disabled)
- `provider = llm` (adapter-based)

If `provider = llm`, the runtime uses this abstract interface:
- `STAGE2_PROVIDER`
- `STAGE2_ENDPOINT`
- `STAGE2_MODEL`
- `STAGE2_API_KEY`
- `STAGE2_TIMEOUT_SECONDS`

No provider is selected or integrated here.

## Noise controls (mandatory guardrails)

Stage 2 must:
- Run only on files changed in the PR
- Skip if diff exceeds a max size (default 200 KB)
- If skipped due to size, produce no output (silent skip)
- Post no output if there are no findings
- Deduplicate repeated findings
- Never exceed 10 findings

---

Done checklist:
- Non-blocking by design
- Diff-only input
- Stable findings JSON schema
- Provider-agnostic adapter contract
- Noise controls (caps, dedupe, size limits)
