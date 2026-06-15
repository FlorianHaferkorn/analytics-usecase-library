# Skill Usability Test Report

**Date**: 2026-02-13  
**Purpose**: Verify Cursor skills are discoverable and their workflows are executable.

---

## Test 1: stage1-pre-commit

**Workflow executed**:
1. Ensure repo root → Set-Location to repo root
2. Run Stage 1 → `.\tooling\run_stage1_checks.ps1`

**Result**: PASS  
- Exit code: 0  
- All 11 Stage 1 checks completed  
- Skills instruct "run from repo root" and "run Stage 1" — both steps executed successfully  
- **Conclusion**: Skill instructions are actionable; agent can follow this skill to run pre-commit checks.

---

## Test 2: assess-change-impact (dry run)

**Scenario**: "What's the impact of renaming or removing KPI ID `sales.price.realization_pct`?"

**Workflow executed** (per skill):
1. Identified artifact: KPI ID `sales.price.realization_pct`
2. Scanned for references (grep across core/usecases, core/action_codes, core/kpi_catalog, etc.)
3. Reported blast radius
4. No changes applied (dry run)

### Blast radius (actual scan results)

| Location | File | References |
|----------|------|------------|
| Use cases | COM-002_Margin_Price_Performance/UseCase_Bracket.yaml | lines 12, 21, 37 |
| Use cases | COM-004_Promotion_Effectiveness/UseCase_Bracket.yaml | lines 13, 22, 38 |
| Action codes | Commercial/C-M2.1.yaml | lines 16, 20, 57, 67, 77, 106 |
| KPI catalog | KPI_Catalog.md | lines 2405, 2431, 3274, 3284 |
| KPI taxonomy | KPI_Taxonomy.md | line 24 |
| UseCase_Inventory | UseCase_Inventory.md | lines 10, 12 |
| Semantic models | Measure_Dictionary_Growth.md | line 62 |
| Strategy | strategy_patterns.md | line 29 |
| Agent prompt | Commercial_Sales_Agent_COM-002.system_prompt.md | line 93 |

**Summary**:
- **Use cases affected**: 2 (COM-002, COM-004)
- **Brackets affected**: 2
- **Action codes affected**: 1 (C-M2.1)
- **Total files requiring updates**: 9+
- **Recommended strategy**: Option A (update all references) — high blast radius; do not rename/delete without coordinated update.

**Result**: PASS  
- Skill workflow (identify → scan → report → recommend) was executed using repo tools (grep, file paths from skill).  
- Output format matches skill's "Output format" section (blast radius, affected artifacts, recommended strategy).  
- **Conclusion**: Agent can use this skill to perform pre-flight impact assessment; instructions and paths are correct.

---

## Test 3: Skill file structure

**Check**: All skills have valid YAML frontmatter and are under `.cursor/skills/<name>/SKILL.md`.

| Skill | Path | Frontmatter |
|-------|------|-------------|
| stage1-pre-commit | .cursor/skills/stage1-pre-commit/SKILL.md | name, description |
| fix-stage1-failure | .cursor/skills/fix-stage1-failure/SKILL.md | name, description |
| add-kpi-reference-safely | .cursor/skills/add-kpi-reference-safely/SKILL.md | name, description |
| add-action-code-and-wire-up | .cursor/skills/add-action-code-and-wire-up/SKILL.md | name, description |
| add-usecase-scaffold | .cursor/skills/add-usecase-scaffold/SKILL.md | name, description |
| edit-factsheet-safely | .cursor/skills/edit-factsheet-safely/SKILL.md | name, description |
| edit-usecase-bracket-safely | .cursor/skills/edit-usecase-bracket-safely/SKILL.md | name, description |
| fabric-powerbi-validation | .cursor/skills/fabric-powerbi-validation/SKILL.md | name, description |
| assess-change-impact | .cursor/skills/assess-change-impact/SKILL.md | name, description |

**Result**: PASS  
- 9 skills present; each has `name` and `description` (used by Cursor for discovery and triggers).

---

## Overall

| Test | Result |
|------|--------|
| stage1-pre-commit workflow | PASS |
| assess-change-impact dry run | PASS |
| Skill file structure | PASS |

**Conclusion**: Skills are usable. The workflows defined in the skills can be executed (run Stage 1, run impact scan, report blast radius). Cursor will discover skills from `.cursor/skills/` and match them via description triggers; this test confirms the instruction content is correct and the repo paths/commands work.

**Note**: Cursor's automatic skill invocation (matching user message to skill description) is a product behavior; we validated that the skill content and commands are correct. For full end-to-end verification, reload Cursor and ask e.g. "Run Stage 1 checks" or "What's the impact of renaming sales.price.realization_pct?" to confirm the agent selects and applies the right skill.
