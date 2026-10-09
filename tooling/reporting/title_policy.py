"""title_policy.py — honest title policy for GENERATED reports (BC-NARR-01, IBCS UN 2.1/2.2).

Why this exists
---------------
"Say it in the title" (BC-NARR-01 until 08.10.2026) only works when a human authors a report *after*
seeing the period's data, and IBCS 2.0 UN 2.2 has since ruled it out altogether (titles describe, the
conclusion has its own slot, see the title model below). A **generated** report adds a second reason:
at generation time we do **not** know the data, and a classic BI tool (Power BI) renders a **static**
visual whose title cannot recompute itself. So hard-coding a conclusion like
"Win rate is dragging coverage below plan" as the title risks the title **contradicting the chart** the
moment the data says otherwise — the title would lie.

The only text that is *always* true is the **question** the visual is built to answer. So:

  • The QUESTION is the default header — it guides the read and never lies, even when the chart shows
    "nothing unusual" (which is itself a valid finding: the user reads it and moves on).
  • The MESSAGE is a governed **expected finding** (a hypothesis to verify), not a per-refresh fact.
    It renders as a framed subtitle (``EXPECTED_PREFIX + message``), clearly a thing to check — not an
    asserted verdict.
  • Only when the finding is **value_verified** (a real computed snapshot backs it, ADR-0017 gate) OR a
    **dynamic narrative** measure recomputes the statement live (smart-narrative DAX / a dynamic tier)
    may the MESSAGE drop its frame — because then something *guarantees* it is true. It still never
    becomes the title (see the title model below).

This keeps the deterministic static report honest and pushes the "spoon-fed conclusion" to exactly the
places that can stand behind it. It changes only *which governed string* becomes the title — it never
invents text.

Title model after IBCS 2.0 UN 2.1 / UN 2.2 (A-34, Freelancing D-641, 08.10.2026)
--------------------------------------------------------------------------------
A title **describes**, it never judges. UN 2.2 describes a page with three title lines — who (reporting
unit), what (measure in bold, unit normal: "Gross margin in %"), when (period, scenarios). UN 2.1 gives
the key message its own slot at a fixed position, above the title. Until 08.10.2026 a verified, context-
safe verdict on a live tool could itself lead as the title (``verdict_render == "statement_title"``) and a
value-verified message replaced the header. Both are **locked**: the verdict renders in the key-message
slot (``"key_message"``) and the message stays out of the title in every case.

The content is held once (``TitleLines`` + key message); the line form is presentation, the same split as
Meridian ``meridian/semantics/titel.py`` (parity tested there against the mirror of this file):

  - ``ibcs_lines``   key message above three lines (variant IBCS and the PBIR output)
  - ``hybrid``       one line "measure in unit" with the measure bold, subtitle "who · when" (Story, Brand)
  - ``single_line``  the three lines joined with " | " (UN 2.2, small screens)
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping, Optional, Tuple, Union

# Frames the governed message as a hypothesis-to-verify, not an asserted fact, in the static case.
EXPECTED_PREFIX = "Expected finding — "

#: Title format after D-641: three descriptive lines, key message separate (Meridian ``titel.IBCS``).
IBCS_THREE_LINE = "ibcs_three_line"
#: Positions of the key message (UN 2.1). One per organisation; default above the title.
KEY_MESSAGE_POSITIONS = ("above_title", "right_of_title")
DEFAULT_KEY_MESSAGE_POSITION = "above_title"
#: Where ``title_contract`` may render the verdict. ``statement_title`` is not among them (locked, D-641).
VERDICT_RENDERS = ("key_message", "annotation", "kpi_status", "omit")
#: Render slots that put the verdict into the title. Kept as data so a test can assert none is returned.
LOCKED_VERDICT_RENDERS = frozenset({"statement_title"})


@dataclass(frozen=True)
class TitleLines:
    """The content of a page title, independent of its line form (IBCS UN 2.2)."""

    who: str
    what: str
    unit: str = ""
    when: str = ""

    def what_line(self) -> str:
        """Line 2 as text: "measure in unit" (without a unit only the measure)."""
        return f"{self.what} in {self.unit}" if self.unit else self.what

    def lines(self) -> Tuple[str, str, str]:
        """The three lines who / what / when."""
        return (self.who, self.what_line(), self.when)


TitleLinesLike = Union[TitleLines, Mapping[str, Optional[str]]]


def title_lines_from(value: Optional[TitleLinesLike]) -> Optional[TitleLines]:
    """``TitleLines`` from a mapping ``{who, what, unit?, when}`` (bracket / template form) or as is.

    ``None`` stays ``None``. ``who`` and ``what`` are required: a title without reporting unit or measure
    does not describe the page (UN 2.2) — raises ``ValueError`` rather than rendering half a title.
    """
    if value is None:
        return None
    if isinstance(value, TitleLines):
        lines = value
    else:
        lines = TitleLines(who=str(value.get("who") or "").strip(), what=str(value.get("what") or "").strip(),
                           unit=str(value.get("unit") or "").strip(), when=str(value.get("when") or "").strip())
    if not lines.who or not lines.what:
        raise ValueError("title_lines need 'who' and 'what' (IBCS UN 2.2)")
    return lines


def check_key_message_position(position: Optional[str]) -> str:
    """The key-message position, default ``above_title``; unknown values raise ``ValueError``."""
    pos = position or DEFAULT_KEY_MESSAGE_POSITION
    if pos not in KEY_MESSAGE_POSITIONS:
        raise ValueError(f"key_message position {pos!r} unknown (allowed: {', '.join(KEY_MESSAGE_POSITIONS)})")
    return pos


def ibcs_lines(lines: TitleLines, key_message: Optional[str] = None,
               position: str = DEFAULT_KEY_MESSAGE_POSITION) -> list:
    """Presentation (a): key message above three title lines, as ``(role, text)``.

    Roles: ``key_message``, ``who``, ``what``, ``when``. Empty lines drop out; the key message is only in
    the sequence for ``above_title`` (``right_of_title`` is placed beside it by the renderer). An unknown
    ``position`` raises ``ValueError`` (``check_key_message_position``).
    """
    position = check_key_message_position(position)
    out: list = []
    if key_message and position == "above_title":
        out.append(("key_message", key_message))
    who, what, when = lines.lines()
    out += [(r, t) for r, t in (("who", who), ("what", what), ("when", when)) if t]
    return out


def hybrid(lines: TitleLines, key_message: Optional[str] = None) -> dict:
    """Presentation (b): one line with the measure bold, subtitle "who · when" (Story, Brand)."""
    return {
        "strong": lines.what,
        "rest": f"in {lines.unit}" if lines.unit else "",
        "subtitle": " · ".join(t for t in (lines.who, lines.when) if t),
        "key_message": key_message or "",
    }


def single_line(lines: TitleLines) -> str:
    """The three lines as one, joined with " | " (UN 2.2 for small screens)."""
    return " | ".join(t for t in lines.lines() if t)

# VERIFIED filter-context constraint (MS Learn "expression-based titles" + community): a Power BI
# dynamic title measure evaluates in the page/report/slicer/cross-filter context but does NOT reliably
# receive the visual's own visual-level / Top-N filters. So a measure-driven statement title may only
# assert a WHOLE-SUBJECT SCALAR (the KPI value + its variance vs target). A Top-N / locally-filtered /
# "where it concentrates" claim would silently miscompute in the title — those stay as the question (or
# live in the evidence area / a card with matching visual-level filters), never as a dynamic title.
_LOCAL_FILTER_CLAIM = re.compile(
    r"\b(top\s*\d+|a few|a handful|handful|concentrat\w+|in a few|couple of|mid-tier|"
    r"lowest[- ]\w+|highest[- ]\w+|worst\s+\w+|leak\w*\s+at|where\b)\b", re.I)


def title_context_safe(text: Optional[str]) -> bool:
    """True when a statement can be a dynamic measure-title — i.e. it is a whole-subject scalar claim,
    not a Top-N / locally-filtered one that the title's filter context can't compute (see above)."""
    t = (text or "").strip()
    if not t:
        return False
    return _LOCAL_FILTER_CLAIM.search(t) is None


def _norm(text: str) -> str:
    """Compare form: whitespace collapsed, case folded."""
    return " ".join(text.split()).casefold()


def title_contract(descriptor: Optional[str], question: Optional[str], verdict: Optional[str],
                   *, verdict_verified: bool = False, tool_live_compute: bool = False,
                   context_safe: Optional[bool] = None, title_lines: Optional[TitleLinesLike] = None,
                   key_message_position: Optional[str] = None) -> dict:
    """The ONE uniform title logic for EVERY viz tool. The logic is identical on Power BI, Databricks
    AI/BI, React — only the *render slot* of the verdict differs, never the rule. Roles:

      • title       = ``descriptor`` — a true, data-independent statement of WHAT the visual shows
                      ("Stage Conversion %, last 12 months"). Same on every tool; can never lie. Without a
                      descriptor, line 2 of ``title_lines`` ("measure in unit") is the title.
      • title_lines = ``{who, what, unit, when}`` (IBCS UN 2.2), ``None`` when not given — the same form as
                      ``TitleLines`` and the bracket field ``page_1_summary.title_lines``: ``what`` is the
                      measure, ``unit`` separate (line 2 renders "what in unit").
      • subtitle    = the governed ``question`` the visual answers — the interpretation aid.
      • verdict     = the governed message / Einordnung — a SEPARATE element, never the title (D-641):
                     'key_message' — verified AND context-safe AND live/scalar → the verdict leads in the
                                     key-message slot above the title (UN 2.1, ``key_message_position``);
                     'annotation'  — verified + live tool, not context-safe → callout at the mark;
                     'kpi_status'  — verified, static tool → KPI value + semantic colour;
                     'omit'        — not verified → shown nowhere (never fabricated; the user reads).
                     'statement_title' (until 08.10.2026) is locked: ``LOCKED_VERDICT_RENDERS``.

    Raises ``ValueError`` when the title *is* a rendered verdict (compared case- and whitespace-insensitive) —
    that would be the statement title again. An omitted verdict is shown nowhere and is not compared.

    Returns {title, title_lines, subtitle, verdict, verdict_render, key_message_position}."""
    lines = title_lines_from(title_lines)
    position = check_key_message_position(key_message_position)
    v = (verdict or "").strip() or None
    title = (descriptor or "").strip() or (lines.what_line() if lines else None)
    safe = title_context_safe(v) if context_safe is None else context_safe
    if not v or not verdict_verified:
        render = "omit"
    elif tool_live_compute and safe:
        render = "key_message"
    elif tool_live_compute:
        render = "annotation"
    else:
        render = "kpi_status"
    if render != "omit" and title and _norm(title) == _norm(v):
        raise ValueError("D-641: the title must describe, the verdict belongs in the key-message slot")
    return {"title": title,
            "title_lines": ({"who": lines.who, "what": lines.what, "unit": lines.unit, "when": lines.when}
                            if lines else None),
            "subtitle": (question or "").strip() or None,
            "verdict": v,
            "verdict_render": render,
            "key_message_position": position}


def resolve_header(
    question: Optional[str],
    message: Optional[str],
    *,
    value_verified: bool = False,
    dynamic_narrative: bool = False,
) -> Tuple[Optional[str], Optional[str]]:
    """Return ``(header, subtitle)`` for a generated visual. The message never becomes the header (D-641).

    - with a question → the **question** leads. The message follows as subtitle: unframed when a
      guarantee backs it (``value_verified``, or ``dynamic_narrative`` with a context-safe claim), else
      framed as *expected finding* (a hypothesis to verify).
    - without a question → no header (``None``; the caller keeps its descriptive label) and the message as
      subtitle, framed by the same rule.
    - no message → ``(question, None)``.

    Until 08.10.2026 a verified message led as the header (IBCS "say it in the title"). IBCS 2.0 UN 2.2
    forbids evaluative titles, and UN 2.1 gives the key message its own slot; the page-level key message
    sits in the title block above the page title (``page_builder``).
    """
    q = (question or "").strip() or None
    m = (message or "").strip() or None
    if not m:
        return q, None
    # A live measure title can't receive the visual-level/Top-N filter: only a context-safe scalar counts as
    # backed. A static value-verified statement is a STRING, no filter-context trap.
    backed = value_verified or (dynamic_narrative and title_context_safe(m))
    return q, (m if backed else f"{EXPECTED_PREFIX}{m}")


def frame_key_message(message: Optional[str], question: Optional[str] = None, *,
                      value_verified: bool = False) -> Optional[str]:
    """The page's key message as rendered in the header / title block (UN 2.1), by the rule of
    ``resolve_header``: verified → as is; unverified → always framed as *expected finding*, after the
    page's question when there is one. Never an unframed, unverified statement.
    """
    m = (message or "").strip() or None
    if not m or value_verified:
        return m
    q = (question or "").strip()
    return f"{q}  \u00b7  {EXPECTED_PREFIX}{m}" if q else f"{EXPECTED_PREFIX}{m}"
