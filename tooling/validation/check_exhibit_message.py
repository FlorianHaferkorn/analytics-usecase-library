"""
check_exhibit_message.py — Boutique rubric BC-NARR-01 structural validator

BC-NARR-01 since 08.10.2026 (A-34, IBCS 2.0 UN 2.1/2.2; Freelancing D-641): titles describe, the
conclusion sits in its own key-message slot and never in the title. Until then the rule read
"title = statement, not label". Two structural halves, both at the INTENT layer:

1. Key message present and a conclusion: every 30-second-layer exhibit (component_30s) carries a
   `message` that reads as a conclusion, not a bare "<metric> by <dimension>" label. The message is
   the key message (UN 2.1), no longer the title.
2. Message never the title, checked on the RENDERED report: no visual title in the committed PBIR
   (`products/fabric/powerbi/dist/<use case>.Report/**/visual.json`, `visualContainerObjects.title`)
   equals an exhibit message (case- and whitespace-insensitive). A bracket without a committed report
   is reported as NOT CHECKED, never as passed.

Rubric: core/templates/page_templates/tokens/boutique_craft_rubric.yaml (BC-NARR-01). Origin: K2 slice
of docs/plans/KONZEPT_REPORT_QUALITAET.md — "Aussage als Daten".

Scope: renderer-agnostic. Validates the governed bracket intent, not a PBIR render.

Usage:
    python tooling/validation/check_exhibit_message.py                 # all use cases
    python tooling/validation/check_exhibit_message.py COM-002          # single use case
    python tooling/validation/check_exhibit_message.py --exit-zero      # warn mode (CI)
    python tooling/validation/check_exhibit_message.py --strict         # missing message = fail

Exit codes:
    0 — all present messages are statements and none leads a header (or --exit-zero)
    1 — a message reads as a label or would lead the header (BC-NARR-01 violation), or --strict and a
        message is missing
"""
from __future__ import annotations

import argparse
import json
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
        return None, "no message set — the key-message slot stays empty (BC-NARR-01)"

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


DIST = REPO / "products" / "fabric" / "powerbi" / "dist"


#: Prefix of the one line that marks a bracket as not checked (a WARN line may quote "NOT CHECKED").
NOT_CHECKED = "    NOT CHECKED rendered titles"


def _norm(text: str) -> str:
    return " ".join(text.split()).casefold()


def _literal(entries: Any) -> Optional[str]:
    """Text of a PBIR ``[{properties: {text: {expr: {Literal: {Value}}}}}]`` entry, unquoted."""
    try:
        raw = entries[0]["properties"]["text"]["expr"]["Literal"]["Value"]
    except (KeyError, IndexError, TypeError):
        return None
    if isinstance(raw, str) and len(raw) >= 2 and raw[0] == raw[-1] == "'":
        return raw[1:-1].replace("''", "'")
    return raw if isinstance(raw, str) else None


def rendered_titles(report_dir: Path) -> list[tuple[str, str]]:
    """``(visual path, title)`` of every visual title in a committed PBIR report
    (``visualContainerObjects.title``, the header Power BI draws above the visual)."""
    out: list[tuple[str, str]] = []
    for vj in sorted(report_dir.glob("definition/pages/*/visuals/*/visual.json")):
        try:
            data = json.loads(vj.read_text(encoding="utf-8"))
        except ValueError:
            continue
        vco = (data.get("visual") or {}).get("visualContainerObjects") or {}
        title = _literal(vco.get("title"))
        if title and title.strip():
            out.append((vj.relative_to(report_dir).as_posix(), title))
    return out


def rendered_title_findings(bracket_path: Path, exhibits: list[dict[str, Any]],
                            dist: Path = DIST) -> tuple[bool, list[str]]:
    """BC-NARR-01 against the RENDERED report: no visual title may carry an exhibit message.

    Returns ``(checked, findings)``. ``checked`` is False when the bracket has no committed report under
    ``dist`` — then nothing was compared ("not checked", never "passed").
    """
    name = bracket_path.parent.name
    # The bracket's report and its variants (`<name>_<variant>.Report`, e.g. COM-001 ..._vs_Plan_LY).
    reports = [r for r in [dist / f"{name}.Report", *sorted(dist.glob(f"{name}_*.Report"))] if r.is_dir()]
    if not reports:
        return False, []
    messages = {_norm(m): m for m in ((ex.get("message") or "").strip() for ex in exhibits) if m}
    findings = [f"{rep.name}/{vis}: title is the message {title!r} — titles describe (BC-NARR-01, D-641)"
                for rep in reports for vis, title in rendered_titles(rep) if _norm(title) in messages]
    return True, findings


def check_bracket(path: Path, dist: Path = DIST) -> tuple[int, int, int, list[str]]:
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
            lines.append(f"    WARN {slot}: {reason}")
    checked, findings = rendered_title_findings(path, exhibits, dist)
    failed += len(findings)
    lines += [f"    ✗ {f}" for f in findings]
    if not checked:
        lines.append(f"{NOT_CHECKED}: no committed report under dist/")
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
    not_checked = with_exhibits = 0
    for b in brackets:
        passed, warned, failed, lines = check_bracket(b)
        with_exhibits += bool(lines or passed or warned or failed)
        not_checked += any(ln.startswith(NOT_CHECKED) for ln in lines)
        total_passed += passed
        total_warned += warned
        total_failed += failed
        if lines:
            print(f"{b.relative_to(REPO)}")
            print("\n".join(lines))

    print(
        f"\nBC-NARR-01: {total_passed} statement(s), {total_warned} advisory, "
        f"{total_failed} violation(s)."
    )
    print(f"Rendered titles: {with_exhibits - not_checked} report(s) checked, {not_checked} NOT CHECKED "
          f"(no committed report).")
    if args.exit_zero:
        return 0
    fail = total_failed > 0 or (args.strict and total_warned > 0)
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
