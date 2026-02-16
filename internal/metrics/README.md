# Metrics Tracking

This directory tracks Stage 1 CI failures, Cursor skill usage, and effectiveness metrics to measure guardrail impact and identify improvement opportunities.

## Purpose

Inspired by the [BI guardrails article](https://dredyson.com/fix-ai-coding-chaos-in-enterprise-bi-a-data-analysts-step-by-step-guide-to-implementing-guardrails-with-cursor-and-power-bi/), we measure:
- **Stage 1 failure rate**: % of runs that fail (target: <10%)
- **Resolution time**: Minutes to fix failures (target: <15 min)
- **Skill adoption**: % of incidents where a Cursor skill was used (target: >70%)
- **Preventable incidents**: How often pre-flight checks (e.g., `assess-change-impact`) stop breaking changes

## Files

- **`stage1_incident_log.yaml`**: Per-incident tracking of Stage 1 failures
- **`skill_usage_log.yaml`**: Weekly snapshots of runs, failures, and skill invocations
- **`retrospective_template.md`**: Monthly review template for identifying patterns and improvements

## Tracking workflow

### When Stage 1 fails

1. **Note the time** before you start fixing.
2. **Fix the issue** (ideally using a Cursor skill like `fix-stage1-failure` or `add-kpi-reference-safely`).
3. **Note the resolution time** (minutes from failure to Stage 1 passing).
4. **Log the incident** in `stage1_incident_log.yaml`:

```yaml
incidents:
  - date: "2026-02-13"
    check_failed: "check_factsheet_vs_kpi"
    resolution_time_minutes: 12
    skill_used: "add-kpi-reference-safely"
    notes: "Missing sales.units KPI ID in SCM-001 bracket"
```

### Weekly snapshot (Friday)

1. **Count Stage 1 runs** from your git log or terminal history (search for `run_stage1_checks.ps1`).
2. **Count failures** from `stage1_incident_log.yaml` for that week.
3. **Summarize failure types** (group by `check_failed`).
4. **Count skill invocations** (estimate from incident log + your memory/notes).
5. **Append snapshot** to `skill_usage_log.yaml`:

```yaml
weekly_snapshots:
  - week_ending: "2026-02-20"
    stage1_runs: 14
    stage1_failures: 3
    failure_breakdown:
      check_factsheet_vs_kpi: 2
      check_forbidden_content: 1
    skills_invoked:
      stage1-pre-commit: 14
      fix-stage1-failure: 3
      add-kpi-reference-safely: 2
```

### Monthly retrospective

1. **Run at month-end** (or first week of following month).
2. **Copy `retrospective_template.md`** to `retrospective_YYYY_MM.md`.
3. **Fill in metrics** from `stage1_incident_log.yaml` and `skill_usage_log.yaml`.
4. **Identify patterns**: What are the top 3 failure modes? Which skills prevented the most issues?
5. **Define action items**: New skills/rules to add, existing skills to improve, processes to change.
6. **Track trends**: Compare to previous month (failure rate, resolution time, skill adoption).

## Success metrics (90-day targets)

Based on the article's proven results (42% → 6% defect rate, 8h → 23m resolution time):

| Metric | Baseline | 30-day target | 90-day target |
|--------|----------|---------------|---------------|
| Stage 1 failure rate | TBD (measure first month) | -20% | -50% |
| Average resolution time | TBD | <20 min | <15 min |
| Skill adoption rate | 0% (new skills) | >50% | >70% |
| Preventable incidents | 0 (no impact-assessment) | >5 caught | >15 caught |

## Tips

- **Be honest**: Log all failures, even "quick fixes." Patterns emerge from honest data.
- **Be consistent**: Weekly snapshots are lightweight (5 min) but high-value for trend analysis.
- **Be retrospective**: Monthly reviews turn raw data into actionable improvements.
- **Automate gradually**: Consider scripting weekly snapshot generation once the manual process is proven.

## Example analysis

After 3 months of tracking, you might discover:
- **Top failure mode**: `check_factsheet_vs_kpi` (45% of failures) → strengthen `add-kpi-reference-safely` skill
- **Fastest fixes**: Incidents using `fix-stage1-failure` skill average 8 min vs. 28 min manual
- **New pattern**: Friday afternoon commits have 3x higher failure rate → reminder to run Stage 1 before EOD
