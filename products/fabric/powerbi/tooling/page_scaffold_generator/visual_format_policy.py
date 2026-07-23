"""PBI adapter shim — the tool-neutral format/semantic/target policy now lives in
`tooling/reporting/format_policy.py`. Re-exported here so existing `page_scaffold_generator` imports
keep resolving. PBI-/DAX-specific rendering (e.g. the `format_string` grammar, and the DAX measures in
`status_measures.py`) is the adapter's concern; the decisions are the base's.
"""
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[5]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from tooling.reporting.format_policy import (  # noqa: F401,E402
    FormatSpec, benchmark_target, classify, deviation_spec, format_spec, format_string,
    good_direction, semantic_tokens, target_source, tooltip_measures, value_axis,
)
