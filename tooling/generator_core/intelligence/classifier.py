"""
Error Classifier — maps raw error strings to structured categories.

Categories align with the knowledge base sections in errors.yaml so that
the FixSuggester can look up the right entry after classification.

Usage
-----
    from tooling.generator_core.intelligence.classifier import ErrorClassifier

    clf = ErrorClassifier()
    category = clf.classify("[MISSING_KPI] KPI 'com.foo' not found in catalog")
    # → ErrorCategory.MISSING_KPI_REF

    buckets = clf.classify_batch(["[TMDL-001] invalid indent", "[MISSING_KPI] ..."])
    # → {ErrorCategory.TMDL_SYNTAX: [...], ErrorCategory.MISSING_KPI_REF: [...]}
"""

from __future__ import annotations

import re
from collections import defaultdict
from enum import Enum
from typing import Dict, List, Tuple


# ---------------------------------------------------------------------------
# Category enum
# ---------------------------------------------------------------------------

class ErrorCategory(str, Enum):
    TMDL_SYNTAX          = "tmdl_syntax"
    SCHEMA_VIOLATION     = "schema_violation"
    MISSING_KPI_REF      = "missing_kpi_ref"
    MISSING_ACTION_CODE  = "missing_action_code"
    VISUAL_TYPE_MISMATCH = "visual_type_mismatch"
    DATA_CONTRACT        = "data_contract"
    DAX_SYNTAX           = "dax_syntax"
    PBIP_STRUCTURE       = "pbip_structure"
    MEASURE_DUPLICATE    = "measure_duplicate"
    BRACKET_FIELD        = "bracket_field"
    ACTION_PANEL         = "action_panel"
    DATASET_REFERENCE    = "dataset_reference"
    LAYOUT               = "layout"
    UNKNOWN              = "unknown"


# ---------------------------------------------------------------------------
# Classification rules
# ---------------------------------------------------------------------------

# List of (pattern, category) tuples — evaluated in order, first match wins.
# Patterns are case-insensitive and matched against the full error string.

_RULES: List[Tuple[str, ErrorCategory]] = [
    # Check IDs (from preflight checks)
    (r"\[MISSING_KPI\]",              ErrorCategory.MISSING_KPI_REF),
    (r"\[MISSING_ACTION_CODE\]",      ErrorCategory.MISSING_ACTION_CODE),
    (r"\[ACTION_PANEL",               ErrorCategory.ACTION_PANEL),
    (r"\[BRACKET_MISSING_FIELD\]",    ErrorCategory.BRACKET_FIELD),
    (r"\[BRACKET_SCHEMA_VIOLATION\]", ErrorCategory.SCHEMA_VIOLATION),
    (r"\[DUPLICATE_MEASURE\]",        ErrorCategory.MEASURE_DUPLICATE),
    (r"\[DATA_CONTRACT",              ErrorCategory.DATA_CONTRACT),
    (r"\[EVIDENCE_COL",               ErrorCategory.DATA_CONTRACT),
    (r"\[NO_PRIMARY_KPIS\]",          ErrorCategory.BRACKET_FIELD),
    (r"\[PBIP_",                      ErrorCategory.PBIP_STRUCTURE),

    # TMDL patterns
    (r"tmdl.*indent|invalid indent|indent.*error|\bindent\b.*tmdl|tabs_only|tab.*space|space.*tab", ErrorCategory.TMDL_SYNTAX),
    (r"formatString.*missing|measure.*no formatString|ungültiger Einzug", ErrorCategory.TMDL_SYNTAX),
    (r"description:.*tmdl|tmdl.*description:",     ErrorCategory.TMDL_SYNTAX),
    (r"summarizeBy.*missing|summarize.*none",       ErrorCategory.TMDL_SYNTAX),
    (r"tmdl.*syntax|syntax.*tmdl",                 ErrorCategory.TMDL_SYNTAX),
    (r"compatibilityLevel|definitionProperties",   ErrorCategory.TMDL_SYNTAX),
    (r"definition\.pbism|definition\.pbir",        ErrorCategory.PBIP_STRUCTURE),

    # DAX
    (r"dax.*error|invalid expression|:=|cannot.*evaluate|measure not found", ErrorCategory.DAX_SYNTAX),
    (r"column.*does not exist|table.*not found.*dax",                         ErrorCategory.DAX_SYNTAX),

    # PBIP structure
    (r"definition\.pbir|\.pbip.*missing|pbip.*structure|report\.json.*missing", ErrorCategory.PBIP_STRUCTURE),
    (r"\$schema.*missing|schema.*not found|unrecognizedSchema",               ErrorCategory.PBIP_STRUCTURE),
    (r"pages\.json|page\.json|visual\.json",                                  ErrorCategory.PBIP_STRUCTURE),
    (r"byPath|byConnection|datasetReference",                                 ErrorCategory.DATASET_REFERENCE),

    # Visual type
    (r"visual_?type.*mismatch|wrong.*visual|cardvisual|linechart.*expected",  ErrorCategory.VISUAL_TYPE_MISMATCH),
    (r"kpi_cards.*missing|main_\d.*missing|detail_matrix.*missing",          ErrorCategory.VISUAL_TYPE_MISMATCH),

    # Schema
    (r"schema.*violation|does not conform|additional properties",             ErrorCategory.SCHEMA_VIOLATION),
    (r"jsonschema|json schema",                                               ErrorCategory.SCHEMA_VIOLATION),

    # Layout
    (r"layout|diagram|position|x=|y=|width|height",                          ErrorCategory.LAYOUT),
    (r"spaghetti|_measures.*position|fact.*y=0",                              ErrorCategory.LAYOUT),

    # Data contract
    (r"data contract|data_contract|gold.*table|parquet",                      ErrorCategory.DATA_CONTRACT),
    (r"evidence.*column|grain.*missing",                                      ErrorCategory.DATA_CONTRACT),
]

# Compile patterns for speed
_COMPILED_RULES: List[Tuple[re.Pattern, ErrorCategory]] = [
    (re.compile(pattern, re.IGNORECASE), category)
    for pattern, category in _RULES
]


# ---------------------------------------------------------------------------
# Classifier
# ---------------------------------------------------------------------------

class ErrorClassifier:
    """
    Classifies error message strings into ErrorCategory values.

    Matching is purely pattern-based (no ML) for determinism and speed.
    Add rules to _RULES above to improve accuracy.
    """

    def classify(self, error_message: str) -> ErrorCategory:
        """Return the first matching category, or UNKNOWN."""
        for pattern, category in _COMPILED_RULES:
            if pattern.search(error_message):
                return category
        return ErrorCategory.UNKNOWN

    def classify_batch(
        self, errors: List[str]
    ) -> Dict[ErrorCategory, List[str]]:
        """
        Classify a list of error messages.

        Returns a dict mapping category → [error messages in that category].
        """
        buckets: Dict[ErrorCategory, List[str]] = defaultdict(list)
        for msg in errors:
            cat = self.classify(msg)
            buckets[cat].append(msg)
        return dict(buckets)

    def top_categories(
        self, errors: List[str], top_n: int = 5
    ) -> List[Tuple[ErrorCategory, int]]:
        """Return the top N error categories by count."""
        buckets = self.classify_batch(errors)
        sorted_cats = sorted(buckets.items(), key=lambda x: len(x[1]), reverse=True)
        return [(cat, len(msgs)) for cat, msgs in sorted_cats[:top_n]]

    def priority_order(self, categories: List[ErrorCategory]) -> List[ErrorCategory]:
        """
        Sort categories by fix priority — fix these first for the highest
        improvement in first-try success rate.
        """
        _PRIORITY = [
            ErrorCategory.BRACKET_FIELD,
            ErrorCategory.MISSING_KPI_REF,
            ErrorCategory.MISSING_ACTION_CODE,
            ErrorCategory.SCHEMA_VIOLATION,
            ErrorCategory.TMDL_SYNTAX,
            ErrorCategory.DAX_SYNTAX,
            ErrorCategory.PBIP_STRUCTURE,
            ErrorCategory.DATASET_REFERENCE,
            ErrorCategory.VISUAL_TYPE_MISMATCH,
            ErrorCategory.DATA_CONTRACT,
            ErrorCategory.MEASURE_DUPLICATE,
            ErrorCategory.ACTION_PANEL,
            ErrorCategory.LAYOUT,
            ErrorCategory.UNKNOWN,
        ]
        priority_map = {cat: i for i, cat in enumerate(_PRIORITY)}
        return sorted(categories, key=lambda c: priority_map.get(c, 999))
