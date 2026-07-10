#!/usr/bin/env python3
"""
check_exhibit_message.py — Boutique rubric BC-NARR-01 structural validator

Enforces the "title = statement, not label" rule of the Boutique-Craft Rubric
(core/templates/page_templates/governance/Boutique_Craft_Rubric.md, rule BC-NARR-01)
at the INTENT layer: every 30-second-layer exhibit (component_30s) should carry a
`message` that reads as a conclusion (IBCS SAY), not a bare "<metric> by <dimension>"
label. This is the K2 slice of KONZEPT_REPORT_QUALITAET.md — "Aussage als Daten" —
and the structural seed of the K6 rubric gate.

Scope: renderer-agnostic. Validates the governed bracket intent, not a PBIR render.

Usage:
    python tooling/validation/check_exhibit_message.py                 # all use cases
    python tooling/validation/check_exhibit_message.py COM-002          # single use case
    python tooling/validation/check_exhibit_message.py --exit-zero      # warn mode (CI)
    python tooling/validation/check_exhibit_message.py --strict         # missing message = fail

Exit codes:
    0 — all present messages are statements (or --exit-zero)
    1 — a message reads as a label (BC-NARR-01 violation), or --strict and a message is missing
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    if __name__ == "__main__":
        print("ERROR: pyyaml not installed. Run: pip install pyyaml", file=sys.stderr)
        sys.exit(1)
    raise

REPO = Path(__file__).resolve().parents[2]

# A bare label: "<metric> by <dimension>" with no further structure (no comma, colon,
# verb, etc.). Char class deliberately excludes ',' ':' '—' so real statements that
# merely contain the word "by" (e.g. "GM eroded by price, not volume") do NOT match.
_LABEL_RE = re.compile(r"^[\w %€$/&.\-']+\bby\b[\w %€$/&.\-']+$", re.IGNORECASE)

# Tokens that signal an assertion (comparison / direction / quantity / finite verb),
# English + German. A statement should contain at least one — or a digit / percent.
_ASSERTION_TOKENS = {
    # comparison / direction (EN)
    "vs", "versus", "above", "below", "under", "over", "on track", "off track",
    "ahead", "behind", "up", "down", "gap", "shortfall", "not", "than",
    # finite verbs (EN)
    "is", "are", "was", "were", "fell", "rose", "grew", "grows", "declined", "drops",
    "drop", "drives", "driven", "driver", "explains", "explain", "compress",
    "compressing", "erodes", "eroding", "eroded", "exceeds", "exceed", "misses",
    "miss", "holds", "holding", "widened", "widening", "narrowed", "concentrated",
    "concentrat", "lags", "lagging", "outpaces", "beats", "trails",
    # comparison / direction + verbs (DE)
    "ist", "sind", "unter", "über", "gegen", "wächst", "fällt", "steigt", "treibt",
    "bricht", "verfehlt", "hält", "erodiert", "über plan", "unter plan", "nicht",
}


def classify_message(message: Optional[str]) -> tuple[Optional[bool], str]:
    """Classify an exhibit message against BC-NARR-01.

    Returns (status, reason):
      True  → passes (reads as a statement)
      False → fails  (reads as a bare label — BC-NARR-01 violation)
      None  → advisory (absent, or present but no clear assertion signal)
    Pure function — unit-tested in tooling/tests/test_exhibit_message.py.
    """
    if message is None or not str(message).strip():
        return None, "no message set — visual title will fall back to a label (BC-NARR-01)"

    text = str(message).strip()
    if _LABEL_RE.match(text):
        return False, f"message reads as a label, not a conclusion: {text!r} (BC-NARR-01)"

    lowered = text.lower()
    has_digit = any(ch.isdigit() for ch in text) or "%" in text
    words = set(re.findall(r"[a-zäöüß]+", lowered))
    has_token = bool(words & _ASSERTION_TOKENS) or any(
        phrase in lowered for phrase in ("on track", "off track", "über plan", "unter plan")
    )
    if has_digit or has_token:
        return True, f"statement: {text!r}"
    return None, f"message may not read as a conclusion — no comparison/quantity/verb signal: {text!r}"


def _exhibits(bracket: dict[str, Any]) -> list[dict[str, Any]]:
    ux = bracket.get("ux_layout_rules", {}) or {}
    out: list[dict[str, Any]] = []
    for page_key in ("page_1_summary", "page_2_execution"):
        page = ux.get(page_key, {}) or {}
        for ex in page.get("component_30s", []) or []:
            if isinstance(ex, dict):
                out.append(ex)
    return out


def check_bracket(path: Path) -> tuple[int, int, int, list[str]]:
    """Return (passed, warned, failed, messages) for one bracket."""
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    passed = warned = failed = 0
    lines: list[str] = []
    exhibits = _exhibits(data)
    if not exhibits:
        return 0, 0, 0, []
    for ex in exhibits:
        slot = ex.get("slot_id") or ex.get("visual_type") or "?"
        status, reason = classify_message(ex.get("message"))
        if status is True:
            passed += 1
        elif status is False:
            failed += 1
            lines.append(f"    ✗ {slot}: {reason}")
        else:
            warned += 1
            lines.append(f"    ⚠ {slot}: {reason}")
    return passed, warned, failed, lines


def main() -> int:
    parser = argparse.ArgumentParser(description="BC-NARR-01 exhibit-message validator")
    parser.add_argument("use_case_id", nargs="?", help="Validate a single use case by ID substring")
    parser.add_argument("--exit-zero", action="store_true", help="Always exit 0 (CI warn mode)")
    parser.add_argument("--strict", action="store_true", help="Treat missing message as a failure")
    args = parser.parse_args()

    brackets = sorted(REPO.glob("core/usecases/**/UseCase_Bracket.yaml"))
    if args.use_case_id:
        brackets = [b for b in brackets if args.use_case_id.lower() in str(b).lower()]
        if not brackets:
            print(f"No UseCase_Bracket.yaml found matching '{args.use_case_id}'", file=sys.stderr)
            return 1

    total_failed = total_warned = total_passed = 0
    for b in brackets:
        passed, warned, failed, lines = check_bracket(b)
        total_passed += passed
        total_warned += warned
        total_failed += failed
        if lines:
            print(f"{b.relative_to(REPO)}")
            print("\n".join(lines))

    print(
        f"\nBC-NARR-01: {total_passed} statement(s), {total_warned} advisory, "
        f"{total_failed} label violation(s)."
    )
    if args.exit_zero:
        return 0
    fail = total_failed > 0 or (args.strict and total_warned > 0)
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
