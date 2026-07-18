# Render-Gated Runbook — ALUCA Report-Quality (K6/K7)

> Companion to [`KONZEPT_REPORT_QUALITAET.md`](KONZEPT_REPORT_QUALITAET.md). Everything the
> boutique-quality track could do from the **governed spec** is already committed and scored
> (structural coverage is essentially exhausted). What remains needs a **renderer, the
> official Power BI CLI, or a model looking at a rendered report** — none of which run in the
> headless Linux CI. This runbook is the turnkey checklist for a **Windows + Fabric laptop
> session with the CLIs and an API key**. Run the steps top-to-bottom; each is independent and
> re-runnable, and every one degrades gracefully (skip / advisory) if a tool is missing.
>
> **All commands run from the repo root.**

## 0 · Prerequisites (once per machine)

| Tool | Install | Needed for |
|---|---|---|
| Node + `powerbi-report-author` | `npm install -g @microsoft/powerbi-report-authoring-cli` | steps 1, 3 (official PBIR oracle) |
| Power BI Desktop / Fabric | Windows only | steps 4, 6 (render + screenshot) |
| Anthropic SDK | `pip install anthropic` | step 5 (LLM judge) |
| API credentials | `export ANTHROPIC_API_KEY=…` (or `ant auth login`) | step 5 |
| Model id | `export ANTHROPIC_MODEL=<your Claude model id>` — use the latest Opus model id | step 5 |

> The pinned CLI is **public preview 0.1.1** — pin it (`npm install -g @microsoft/powerbi-report-authoring-cli@0.1.1`) so the vendored snapshot stays reproducible.

---

## 1 · Refresh the authoring-metadata snapshot (official visual-type oracle)

Re-vendor Microsoft's visual-type/role metadata so the native validators check against the
current official catalog rather than a stale snapshot.

```bash
python tooling/report_quality/refresh_authoring_metadata.py
git diff --stat tooling/schemas/pbir/authoring_metadata_snapshot.json
```

- **Expected:** either no diff (snapshot already current) or a reviewed diff of added/changed
  visual types. Commit the snapshot if it changed.
- **No CLI installed:** the script prints an install hint and exits 0 — nothing to commit.

---

## 2 · Regenerate the `.Report` dist so spec ↔ dist align (Windows/Fabric)

The committed spec carries changes that the distributed `.Report` must reflect — the FIN-001
`waterfall` (was `bar_chart`), the benchmark reference-labels on KPI cards, and the
`Benchmark_Caption` text box. Recompile each affected bracket through the pbip adapter, passing
the **client sector** so empirical benchmarks resolve to the right peer segment.

```bash
# one bracket (repeat per use case, or script the loop):
python -m tooling.generator_core compile \
    --bracket core/usecases/core/FIN-001/UseCase_Bracket.yaml \
    --adapter pbip \
    --deployment-industry "Omnichannel Retail"
```

- **`--deployment-industry`** selects the peer segment for empirical benchmark labels; unset →
  the honest cross-industry fallback (`"vs. cross-industry X (no sector match)"`).
- **Dry-run first** to preview the spec (`--dry-run` prints the compiled IR incl.
  `benchmark_reference` without writing files).
- After regen, re-run the structural gate (step 7) — the FIN-001 waterfall and benchmark
  captions should now be present in the dist and no longer flagged as spec↔dist drift.

---

## 3 · Verify the render-gated PBIR shapes against the CLI oracle

Four shapes are **advisory-only today** because they have **zero occurrences in the proven
PBIR corpus** — we refuse to emit an unverified structure into a client deliverable. Each has a
native advisory validator that lists what is *awaiting* the emit. On the laptop, verify the
shape against the official CLI, and only **then** flip the emit on.

| Rule | Advisory validator (lists candidates) | Shape to verify | CLI check |
|---|---|---|---|
| BC-CHART-05 | `python tooling/validation/check_reference_lines.py` | reference-line PBIR object on trend visuals | `powerbi-report-author validate <Report.Report>` |
| BC-TYPE-02 | `python tooling/validation/check_tabular_numerals.py` | per-column `tabular-nums` on number columns | `powerbi-report-author formatting …` |
| BC-CHART-10 | (top-N filter on evidence tables) | `topN` filter object | `powerbi-report-author validate` |
| — | (hero-card native reference-line) | native reference-line on the hero KPI card | `powerbi-report-author validate` |

**Procedure per shape:**
1. Hand-author the shape into **one** `.Report` and run `powerbi-report-author validate` on it.
2. If it validates clean, add it to the generator emit (the adapter in
   `products/fabric/powerbi/tooling/adapters/pbip.py`), regenerate (step 2), and re-validate the
   whole dist.
3. Flip the corresponding advisory validator from advisory → scored (it becomes a real gate),
   and update the scorecard wiring + its regression floor.
4. If it does **not** validate, leave it advisory and note the CLI error in
   `internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md` — do **not** ship an unverified shape.

---

## 4 · Render the report (Windows) for the visual judge

Open each regenerated `.Report` in Power BI Desktop (or Fabric) and export the rendered
evidence the judge will read in step 5. For each summary page, capture either a screenshot or
the CLI page/visual inventory as text:

```bash
# textual evidence per report (works headless where Desktop is not available):
powerbi-report-author preview-pages   <Report.Report> > build/render_evidence/_report.txt
powerbi-report-author preview-visuals <Report.Report> >> build/render_evidence/_report.txt
```

Drop the evidence into `build/render_evidence/`:
- a **shared** `_report.txt` / `_report.html` reused for every render-only rule, **and/or**
- a **per-rule** file (`BC-COLOR-01.txt`, `BC-CHART-03.txt`, …) when a rule needs a specific crop.

The judge reads per-rule first, then falls back to the shared file (see `llm_backend.py`).

---

## 5 · Wire the LLM judge over the rendered reports (the ~9 render-only rules)

The judge seam is already built and unit-tested; the concrete Anthropic backend is
`tooling/report_quality/llm_backend.py`. With the env vars from step 0 set and evidence on disk
from step 4, this is **one command**:

```bash
export ANTHROPIC_API_KEY=…            # from step 0
export ANTHROPIC_MODEL=<your Claude model id>
python -m tooling.report_quality.boutique_scorecard \
    --render-evidence build/render_evidence --json build/scorecard.json
```

- The scorecard swaps in `CompositeJudge([SpecHeuristicJudge(), LLMJudge(...)])`: cheap
  spec-heuristics decide what they can, the model scores only the genuinely render-only rules
  (BC-COLOR-01, BC-CHART-03/06, BC-NARR-05, …) against the evidence.
- **No key / no model / no SDK → the model half abstains** (score stays `None`, coverage
  unchanged). It never fabricates a verdict — that is the whole safety contract.
- Malformed model output → abstain (parsed by the unit-tested `parse_verdict`).
- Review the JSON: each newly-scored rule carries `method: "llm"` and a one-line rationale.
  Spot-check the rationales before trusting the lift in coverage.

---

## 6 · K7 — Desktop render + visual acceptance

Final human/LLM acceptance of the rendered deliverable:
1. Render every use-case report in Desktop.
2. Run step 5 with per-rule screenshot evidence for the rules that need a visual crop.
3. Confirm no scored knock-out fails and the coverage lift is real (not an abstain masquerading
   as a pass — check `method`).
4. Record the accepted coverage in `KONZEPT_REPORT_QUALITAET.md` §12.

---

## 7 · Close-out — local validation (CI is out until August)

The GitHub Actions usage limit is exhausted repo-wide until early August (see `CLAUDE.md`),
so validate **locally** and let the maintainer decide on merge:

```bash
bash tooling/run_local_ci_check.sh                       # drift-gate + pytest + Fabric + studio
python -m tooling.report_quality.boutique_scorecard      # structural scorecard (no LLM)
python scripts/check_index.py --strict                   # drift-gate hard
```

- **Windows-only gap:** `tooling/run_stage1_checks.ps1` and `tooling/quality/run_quality_gate.ps1`
  do not run in the bash check — run them in your Windows session before merge.
- A task is never done while validation shows errors.
