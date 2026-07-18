"""PBI adapter shim — the tool-neutral title policy now lives in `tooling/reporting/title_policy.py`.

Kept here only so existing `page_scaffold_generator` (relative) imports keep resolving; the logic is
the base's. Import direction is correct: this PBI module depends on the base, never the reverse.
"""
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[5]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from tooling.reporting.title_policy import (  # noqa: F401,E402
    EXPECTED_PREFIX, resolve_header, title_context_safe,
)
