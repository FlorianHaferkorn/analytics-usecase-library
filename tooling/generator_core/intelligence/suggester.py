"""
Fix Suggester — maps classified errors to concrete fix suggestions.

Combines the knowledge base (errors.yaml) with the error classifier to
produce actionable suggestions the generator (or a human) can act on.

Usage
-----
    from tooling.generator_core.intelligence.classifier import ErrorClassifier
    from tooling.generator_core.intelligence.suggester import FixSuggester

    clf = ErrorClassifier()
    suggester = FixSuggester()

    errors = ["[MISSING_KPI] KPI 'com.foo.bar' not found in catalog"]
    buckets = clf.classify_batch(errors)
    fixes = suggester.suggest_for_buckets(buckets)
    for fix in fixes:
        print(fix.description)
        for cmd in fix.commands:
            print(f"  $ {cmd}")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .classifier import ErrorCategory
from .kb import KBEntry, KnowledgeBase


# ---------------------------------------------------------------------------
# Fix suggestion
# ---------------------------------------------------------------------------

@dataclass
class FixSuggestion:
    description: str
    category: ErrorCategory
    auto_fixable: bool = False
    commands: List[str] = field(default_factory=list)
    doc_reference: str = ""         # Section in KNOWN_ERRORS_AND_FIXES.md or KB entry ID
    source_errors: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Built-in fallback suggestions per category
# (used when the KB has no matching entry)
# ---------------------------------------------------------------------------

_FALLBACK: Dict[ErrorCategory, FixSuggestion] = {
    ErrorCategory.MISSING_KPI_REF: FixSuggestion(
        description="KPI referenced in bracket not found in catalog. Add it to core/kpi_catalog/ or remove the reference.",
        category=ErrorCategory.MISSING_KPI_REF,
        auto_fixable=False,
        commands=["python tooling/validation/check_factsheet_vs_kpi.py"],
        doc_reference="KNOWN_ERRORS_AND_FIXES.md#dax--measures",
    ),
    ErrorCategory.MISSING_ACTION_CODE: FixSuggestion(
        description="Action code referenced in bracket not found. Create the YAML or remove the reference.",
        category=ErrorCategory.MISSING_ACTION_CODE,
        auto_fixable=False,
        commands=["python tooling/validation/check_action_codes_vs_kpi.py"],
        doc_reference="KNOWN_ERRORS_AND_FIXES.md#dax--measures",
    ),
    ErrorCategory.TMDL_SYNTAX: FixSuggestion(
        description="TMDL syntax violation. Run the normalize script to auto-fix common issues.",
        category=ErrorCategory.TMDL_SYNTAX,
        auto_fixable=True,
        commands=[
            ".\\products\\fabric\\powerbi\\tooling\\normalize_tmdl_tabs.ps1",
            ".\\products\\fabric\\powerbi\\tooling\\tmdl_render_and_fix.ps1",
        ],
        doc_reference="KNOWN_ERRORS_AND_FIXES.md#tmdl--pbip",
    ),
    ErrorCategory.DAX_SYNTAX: FixSuggestion(
        description="DAX expression error. Check the KPI catalog formula and run DAX best-practices linter.",
        category=ErrorCategory.DAX_SYNTAX,
        auto_fixable=False,
        commands=[
            ".\\products\\fabric\\powerbi\\tooling\\validation\\check_dax_best_practices.ps1",
        ],
        doc_reference="KNOWN_ERRORS_AND_FIXES.md#dax--measures",
    ),
    ErrorCategory.PBIP_STRUCTURE: FixSuggestion(
        description="PBIP file structure issue. Run Desktop-readiness check to find missing artifacts.",
        category=ErrorCategory.PBIP_STRUCTURE,
        auto_fixable=True,
        commands=[
            ".\\products\\fabric\\powerbi\\tooling\\ensure_pbip_desktop_ready.ps1",
        ],
        doc_reference="KNOWN_ERRORS_AND_FIXES.md#tmdl--pbip",
    ),
    ErrorCategory.VISUAL_TYPE_MISMATCH: FixSuggestion(
        description="Visual type in report does not match bracket declaration. Re-scaffold or fix visual.json.",
        category=ErrorCategory.VISUAL_TYPE_MISMATCH,
        auto_fixable=False,
        commands=[
            "python products/fabric/powerbi/tooling/validation/check_page_template_compliance.py",
        ],
        doc_reference="KNOWN_ERRORS_AND_FIXES.md#report-visuals-pbip--page_scaffold_generator",
    ),
    ErrorCategory.SCHEMA_VIOLATION: FixSuggestion(
        description="YAML does not conform to its JSON schema. Check tooling/generator/schemas/ for the governing schema.",
        category=ErrorCategory.SCHEMA_VIOLATION,
        auto_fixable=False,
        commands=[
            ".\\tooling\\validation\\check_schema_validation.ps1",
        ],
        doc_reference="tooling/generator/schemas/usecase_bracket.schema.json",
    ),
    ErrorCategory.BRACKET_FIELD: FixSuggestion(
        description="Required field missing from UseCase_Bracket.yaml. Check the bracket schema.",
        category=ErrorCategory.BRACKET_FIELD,
        auto_fixable=False,
        commands=[],
        doc_reference="tooling/generator/schemas/usecase_bracket.schema.json",
    ),
    ErrorCategory.DATA_CONTRACT: FixSuggestion(
        description="Data contract issue. Verify column names in core/data_contracts/ match the bracket.",
        category=ErrorCategory.DATA_CONTRACT,
        auto_fixable=False,
        commands=[
            ".\\tooling\\validation\\check_data_contract_kpi_coverage.ps1",
        ],
        doc_reference="KNOWN_ERRORS_AND_FIXES.md#datasetreference",
    ),
    ErrorCategory.DATASET_REFERENCE: FixSuggestion(
        description="Report datasetReference is wrong. For local PBIP use byPath; for Fabric REST use byConnection.",
        category=ErrorCategory.DATASET_REFERENCE,
        auto_fixable=False,
        commands=[
            ".\\products\\fabric\\powerbi\\tooling\\ensure_pbip_desktop_ready.ps1",
        ],
        doc_reference="KNOWN_ERRORS_AND_FIXES.md#datasetreference",
    ),
    ErrorCategory.MEASURE_DUPLICATE: FixSuggestion(
        description="Duplicate measure name detected. Remove the duplicate from _Measures.tmdl or KPI catalog.",
        category=ErrorCategory.MEASURE_DUPLICATE,
        auto_fixable=False,
        commands=[
            ".\\products\\fabric\\powerbi\\tooling\\validation\\check_tmdl_vs_measure_dictionary.ps1",
        ],
        doc_reference="KNOWN_ERRORS_AND_FIXES.md#measures-shared-domain-model-multiuse-case",
    ),
    ErrorCategory.ACTION_PANEL: FixSuggestion(
        description="Action panel issue. Verify orchestration.action_code_ids are set and action code YAMLs exist.",
        category=ErrorCategory.ACTION_PANEL,
        auto_fixable=False,
        commands=[
            "python products/fabric/powerbi/tooling/generate_action_payload.py --use-case <ID>",
        ],
        doc_reference="KNOWN_ERRORS_AND_FIXES.md#report-visuals-pbip--page_scaffold_generator",
    ),
    ErrorCategory.LAYOUT: FixSuggestion(
        description="Model view or visual layout issue. Run diagram layout validation.",
        category=ErrorCategory.LAYOUT,
        auto_fixable=False,
        commands=[
            ".\\products\\fabric\\powerbi\\tooling\\validation\\check_diagram_layout.ps1",
        ],
        doc_reference="KNOWN_ERRORS_AND_FIXES.md#semantic-model-relationships-layout",
    ),
    ErrorCategory.UNKNOWN: FixSuggestion(
        description="Unknown error — check KNOWN_ERRORS_AND_FIXES.md and pipeline logs.",
        category=ErrorCategory.UNKNOWN,
        auto_fixable=False,
        commands=[".\\tooling\\run_stage1_checks.ps1"],
        doc_reference="internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md",
    ),
}


# ---------------------------------------------------------------------------
# Suggester
# ---------------------------------------------------------------------------

class FixSuggester:
    """
    Maps classified error buckets → FixSuggestion objects.

    Looks up the KB first; falls back to built-in suggestions per category.
    Appends new unknown patterns to the KB when auto_append=True.
    """

    def __init__(self, kb: Optional[KnowledgeBase] = None) -> None:
        self.kb = kb or KnowledgeBase()

    def suggest(
        self,
        error_message: str,
        category: ErrorCategory,
    ) -> FixSuggestion:
        """Return the best fix suggestion for a single error."""
        kb_entry = self.kb.lookup(error_message)
        if kb_entry:
            return self._from_kb(kb_entry, category, [error_message])

        # Auto-append to KB so the error is tracked
        if category == ErrorCategory.UNKNOWN:
            self.kb.append_unknown(error_message, category=category.value)

        fallback = _FALLBACK.get(category, _FALLBACK[ErrorCategory.UNKNOWN])
        return FixSuggestion(
            description=fallback.description,
            category=category,
            auto_fixable=fallback.auto_fixable,
            commands=list(fallback.commands),
            doc_reference=fallback.doc_reference,
            source_errors=[error_message],
        )

    def suggest_for_buckets(
        self,
        buckets: Dict[ErrorCategory, List[str]],
    ) -> List[FixSuggestion]:
        """
        Return deduplicated suggestions for a classified error dict.

        Groups errors by category and returns one suggestion per category,
        enriched with all the source error messages.
        """
        suggestions: List[FixSuggestion] = []
        for category, errors in buckets.items():
            # Try KB first with the first error message as representative
            kb_entry = self.kb.lookup(errors[0]) if errors else None
            if kb_entry:
                fix = self._from_kb(kb_entry, category, errors)
            else:
                if category == ErrorCategory.UNKNOWN:
                    for err in errors:
                        self.kb.append_unknown(err, category=category.value)
                fallback = _FALLBACK.get(category, _FALLBACK[ErrorCategory.UNKNOWN])
                fix = FixSuggestion(
                    description=fallback.description,
                    category=category,
                    auto_fixable=fallback.auto_fixable,
                    commands=list(fallback.commands),
                    doc_reference=fallback.doc_reference,
                    source_errors=errors,
                )
            suggestions.append(fix)
        return suggestions

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    @staticmethod
    def _from_kb(entry: KBEntry, category: ErrorCategory, errors: List[str]) -> FixSuggestion:
        return FixSuggestion(
            description=f"[{entry.id}] {entry.fix}",
            category=category,
            auto_fixable=bool(entry.auto_fix_commands),
            commands=list(entry.auto_fix_commands),
            doc_reference=f"KNOWN_ERRORS_AND_FIXES.md#{entry.id}",
            source_errors=errors,
        )
