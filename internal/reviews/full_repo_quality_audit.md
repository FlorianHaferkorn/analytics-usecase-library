# Full Repo Quality Audit

Date: 2026-05-26

Scope: root governance files, CI and quality gates, core/generator assets, Aurora gold data, Fabric/Power BI output, OSS adapters, Studio/MCP, and internal project-management docs.

## Executive Summary

The repository has a solid Stage 1 foundation and clear Golden Thread ownership, but report quality is still split across several partial checks. The highest-value next move is not deleting many files at once; it is consolidating report-quality checks into one canonical gate, moving historical repair logic upstream into generators, and making generated output boundaries unambiguous.

Phase 2 P0 has started with a new additive static report-quality package under `tooling/report_quality/`. It currently validates PBIR structure, content placeholders, measure references, optional Microsoft schema validation, and deterministic self-healing for safe structural fixes.

## Decision Matrix

| Area | Status | Affected Files | Why Relevant | Risk If Unchanged | Recommended Change | Validation |
|---|---|---|---|---|---|---|
| Root agent governance | keep + harden | `AGENTS.md`, `CLAUDE.md`, `README.md`, `.cursor/rules/` | `AGENTS.md` is now the universal agent entry point. | Future agents may still follow stale tool-specific instructions. | Keep `AGENTS.md` canonical and keep tool-specific files as thin overlays generated or synchronized from canonical docs. | Stage 1 docs link check plus periodic agent-config drift check. |
| Stage 1 local gate | keep + integrate | `tooling/run_stage1_checks.ps1`, `tooling/validation/` | This is the strongest existing hard gate. | Checks remain framework-focused and do not fully cover generated report quality. | Keep Stage 1 as source/use-case gate; call report quality from a separate quality gate first, then promote once stable. | `.\tooling\run_stage1_checks.ps1`. |
| GitHub Stage 1 workflow | harden | `.github/workflows/stage1.yml` | CI duplicates local logic and runs some extra report checks independently. | CI/local behavior can drift; report gates may pass locally but not in CI, or vice versa. | Replace standalone binding/drift jobs with calls to canonical scripts where possible; upload report-quality JSON artifacts. | GitHub Actions plus `tooling/quality/run_quality_gate.ps1`. |
| Fabric report checks | integrate | `products/fabric/powerbi/tooling/run_fabric_checks.ps1`, `products/fabric/powerbi/tooling/validation/` | Many useful checks already exist, but ownership is fragmented. | New checks become optional or forgotten. | Keep Fabric checks for domain-specific validation and add `check_report_quality.ps1` once P0 remains green. | `.\products\fabric\powerbi\tooling\run_fabric_checks.ps1`. |
| PBIR schema versioning | harden | `products/fabric/powerbi/tooling/schema_registry.py`, `check_schema_versions.py`, `update_schema_manifest.py` | Registry is pinned and useful, but still partly manual. | Microsoft schema drift is detected late or requires manual tracking. | Phase 2 next: add latest schema discovery/cache/update workflow and automated PR output. | Schema discovery test plus schema version check. |
| Generated Power BI output | keep + mark | `products/fabric/powerbi/dist/` | This is the canonical generated target requested by the user. | Manual edits can mask generator defects. | Treat as generated output; validate hard; fix generator/templates before editing output. | Report quality gate, Fabric checks, PBIR schema checks. |
| Historical Aurora semantic mirror | delete complete | `products/fabric/showcases/aurora_group/semantic_models/` | Previously confusing generated/mirrored model area. | Duplicate semantic truth and stale references. | Keep deleted; ensure docs point to `products/fabric/powerbi/dist/`. | Stage 1 docs link check. |
| Aurora gold repair scripts | integrate + delete later | `showcases/aurora_group/data/gold/generate_missing_facts.py` | Name and purpose indicate post-generation repair. | Incomplete initial generation becomes normalized. | Move completeness rules into the normal gold generation/data-contract flow; then delete script. | New gold completeness validator. |
| Archive maintenance scripts | archive | `internal/archive/**/fix_*.ps1`, `internal/archive/**/add_missing_*.ps1`, archived smoke/daemon scripts | They are correctly under archive but still show the historical pattern. | Agents may copy obsolete workaround patterns. | Keep archived only if docs say reference-only; exclude from active references and gates. | Docs link/deprecated path checks. |
| Active fix script | review + integrate | `tooling/fix_bracket_component30s.py` | Active root-level fix script suggests schema/generator gap. | Brackets may require after-the-fact repair. | Audit usage; either integrate into bracket generator/schema migration or move to archive. | Bracket schema tests. |
| TMDL render/fix script | review + constrain | `products/fabric/powerbi/tooling/tmdl_render_and_fix.ps1` | Auto-fix can be valuable, but needs deterministic scope. | Silent report/model changes without regression tests. | Keep only safe fixes; document classes in `KNOWN_ERRORS_AND_FIXES.md`; add tests for every fix class. | TMDL syntax/readiness tests. |
| Markdown lint | keep focused | `.markdownlint-cli2.jsonc`, `.markdownlintignore`, `tooling/validation/check_markdownlint.ps1` | Recently reworked and now meaningful. | Docs can drift back into unreadable/inconsistent shape. | Keep focused rules only; expand cautiously when violations are low. | Stage 1 markdownlint check. |
| OSS stack validation | keep + align | `products/open_source_stack/tooling/`, `products/oss_adapters/` | OSS has its own validation, but not yet the same visual contract. | Power BI quality can diverge from Evidence/Grafana/Metabase/Superset. | Define adapter-neutral visual test manifest after P0. | OSS checks plus future visual manifest runner. |
| Studio/MCP quality loop | integrate later | `studio/` | Studio/MCP can host self-healing and preview workflows. | Fixes stay local to scripts instead of becoming repeatable agent tools. | Reuse `tooling/report_quality` from MCP tools, but keep writes approval-scoped. | MCP tool tests and static report gate. |
| Internal project management docs | keep + prune | `internal/project_mgmt/KNOWN_GAPS.md`, `KNOWN_ERRORS_AND_FIXES.md`, `internal/reviews/` | Captures self-learning and audit trail. | Resolved gaps remain as stale priorities. | After each phase, close/update resolved gaps and add new error classes with tests. | Stage 1 docs link check; manual review. |

## Immediate P0 Outcome

Implemented as additive tooling:

- `tooling/report_quality/schema_validator.py`: validates JSON files against declared Microsoft schemas, with cache and URL rewrite to Microsoft schema GitHub raw content.
- `tooling/report_quality/structural_validator.py`: checks PBIR page size, required slots, forbidden visual types, and visual bounds.
- `tooling/report_quality/content_validator.py`: detects placeholders, overly long text, and mixed German/English snippets.
- `tooling/report_quality/dax_reference_validator.py`: validates explicit report measure references against merged TMDL `_Measures` definitions.
- `tooling/report_quality/self_heal.py`: deterministic, bounded check-fix-recheck loop for safe structural fixes.
- `products/fabric/powerbi/tooling/validation/check_report_quality.ps1`: Power BI wrapper with robust Python launcher detection.
- `tooling/quality/run_quality_gate.ps1`: additive quality entry point for Stage 1, Fabric checks, and P0 report-quality checks.

## Findings To Carry Into Next Phases

1. Python launcher handling must be standardized. On this Windows environment, `python` resolves to the Microsoft Store alias, while `py -3` works. New wrappers should use the existing `py -3` / `python3` / `python` detection pattern.
2. The canonical generated report size is `1920x1080`, not `1280x720`. Validators must infer or encode the repo's actual template contract, not generic defaults.
3. PBIR `queryRef` cannot by itself classify a field as a measure. The DAX reference check must only treat explicit `Measure.Property` nodes as measure references unless it also resolves table/column metadata.
4. Schema validation should remain opt-in until the latest-schema workflow and cache behavior are fully automated, because network availability must not destabilize local hard gates.
5. Repair scripts should not be deleted blindly. Any active repair logic must either become generator behavior, a deterministic validator/self-heal rule with tests, or a clearly archived reference.

## Prioritized Action Lists

### Delete Or Archive Now

- Keep historical `internal/archive/**` scripts out of active workflows; add stronger archive warnings if agents continue to reference them.
- Review `tooling/fix_bracket_component30s.py` for current references. If unused, move to archive; if used, integrate into the bracket generator or schema migration path.

### Integrate Into Canonical Path

- Move `showcases/aurora_group/data/gold/generate_missing_facts.py` behavior into normal gold generation and add a gold completeness validator.
- Promote `check_report_quality.ps1` into `run_fabric_checks.ps1` after P0 remains stable against generated reports.
- Replace CI ad-hoc report jobs with canonical script calls and artifact upload.

### Build Missing Automation

- Automatic Microsoft schema discovery, cache refresh, and update PR output.
- BPA gate via Tabular Editor or Semantic Link Labs.
- Visual regression manifest that can run Power BI first, then OSS/Evidence adapters with the same contract.
- Self-healing registry where every fix has a regression test and `KNOWN_ERRORS_AND_FIXES.md` entry.

## Validation Snapshot

- `py -3 -m pytest tooling/tests/test_report_quality_p0.py -q`: passed.
- `powershell -NoProfile -ExecutionPolicy Bypass -File products\fabric\powerbi\tooling\validation\check_report_quality.ps1`: passed with `0 critical, 0 warning, 0 info`.
