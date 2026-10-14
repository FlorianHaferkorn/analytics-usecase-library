"""Title block of a PBIR page: key message above three title lines (A-34, IBCS 2.0 UN 2.1/2.2).

One textbox top left above the canvas grid (Zone 0, the ``Header`` visual), four paragraphs:

  1. key message (UN 2.1), bold 14 pt — the page's governed ``big_idea`` (framed as expected finding while
     unverified, ``config_loader``)
  2. who   — reporting unit
  3. what  — measure bold, "in <unit>" normal (UN 2.2 line 2)
  4. when  — period and scenarios

Content and line form come from ``tooling/reporting/title_policy.py`` (``TitleLines``, ``ibcs_lines``);
this module only builds the PBIR object. Same structure as Meridian
``meridian/tool-layers/fabric/generators/title_block.py`` (D-641); sizes 14/11 pt as there.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from .title_policy import DEFAULT_KEY_MESSAGE_POSITION, TitleLines, ibcs_lines

#: Minimum height of the title block on the 1920×1080 canvas: key message (14 pt) plus three lines
#: (11 pt). Same value as Meridian ``title_block.HOEHE_PX``. Longer key messages wrap and the block
#: grows (``title_block_height``).
TITLE_BLOCK_HEIGHT = 112
#: Width of the title textbox (canvas 1920 minus the 32 px outer margins).
TITLE_BLOCK_WIDTH = 1856

_SIZE_KEY_MESSAGE = 14
_SIZE_LINE = 11

#: Wrap estimate. ANNAHME, ungeprueft (kein Desktop-Render im Container): mittlere Zeichenbreite
#: von Segoe UI als Anteil der Schriftgroesse, fett gerechnet und damit eher zu breit -- zu breit
#: geschaetzt heisst eine Zeile zu viel Platz, zu schmal hiesse abgeschnittener Text. Gleiche
#: Rolle wie Meridians ``ZEICHEN_BREITE``; messen, sobald ein Render da ist.
CHAR_WIDTH_EM = 0.6
LINE_HEIGHT_EM = 1.4
#: Inner padding of a Power BI textbox, top plus bottom (ANNAHME, ungeprueft).
PADDING_PX = 16


def _px(size_pt: float) -> float:
    return size_pt * 96 / 72


def wrapped_lines(text: str, size_pt: float, width_px: float = TITLE_BLOCK_WIDTH - PADDING_PX) -> int:
    """Lines a paragraph needs at ``size_pt`` in ``width_px`` (greedy word wrap, estimated widths)."""
    per_line = max(1, int(width_px // (_px(size_pt) * CHAR_WIDTH_EM)))
    lines, used = 1, 0
    for word in (text or "").split():
        need = len(word) if used == 0 else used + 1 + len(word)
        if need <= per_line:
            used = need
        else:
            # A word that does not fit an empty line starts on that line; only its overflow adds lines.
            lines += (0 if used == 0 else 1) + (len(word) - 1) // per_line
            used = len(word) % per_line or per_line
    return lines


def title_block_height(lines: TitleLines, key_message: Optional[str] = None,
                       position: str = DEFAULT_KEY_MESSAGE_POSITION) -> int:
    """Height in px the block needs: each paragraph's wrapped lines × line height, at least
    ``TITLE_BLOCK_HEIGHT``. The grid moves down by exactly this height (page_builder)."""
    total = 0.0
    for role, text in ibcs_lines(lines, key_message, position):
        size = _SIZE_KEY_MESSAGE if role == "key_message" else _SIZE_LINE
        total += wrapped_lines(text, size) * _px(size) * LINE_HEIGHT_EM
    return max(TITLE_BLOCK_HEIGHT, math.ceil(total + PADDING_PX))


def _run(value: str, *, bold: bool = False, size: int = _SIZE_LINE) -> Dict[str, Any]:
    style: Dict[str, Any] = {"fontSize": f"{size}pt"}
    if bold:
        style["fontWeight"] = "bold"
    return {"value": value, "textStyle": style}


def build_title_objects(lines: TitleLines, key_message: Optional[str] = None,
                        position: str = DEFAULT_KEY_MESSAGE_POSITION) -> Dict[str, Any]:
    """PBIR ``objects`` of the title textbox (``general.paragraphs``)."""
    if position != "above_title":
        # right_of_title needs a second textbox beside the title; no bracket asks for it.
        raise ValueError(f"key_message position {position!r}: PBIR renders above_title only")
    paragraphs: List[Dict[str, Any]] = []
    for role, text in ibcs_lines(lines, key_message, position):
        if role == "key_message":
            runs = [_run(text, bold=True, size=_SIZE_KEY_MESSAGE)]
        elif role == "what":
            runs = [_run(lines.what, bold=True)]
            if lines.unit:
                runs.append(_run(f" in {lines.unit}"))
        else:
            runs = [_run(text)]
        paragraphs.append({"textRuns": runs})
    return {"general": [{"properties": {"paragraphs": paragraphs}}]}


def textbox_paragraphs(visual: Dict[str, Any]) -> List[str]:
    """Paragraph texts of a textbox visual: ``objects.general`` paragraphs, else the ``objects.text``
    literal as one paragraph (the Header form before A-34)."""
    objects = (visual.get("visual") or {}).get("objects") or {}
    out: List[str] = []
    for entry in objects.get("general") or []:
        for para in (entry.get("properties") or {}).get("paragraphs") or []:
            out.append("".join(str(r.get("value") or "") for r in para.get("textRuns") or []))
    if out:
        return out
    for entry in objects.get("text") or []:
        expr = (((entry.get("properties") or {}).get("text") or {}).get("expr") or {})
        raw = (expr.get("Literal") or {}).get("Value", "")
        if raw.startswith("'") and raw.endswith("'"):
            raw = raw[1:-1].replace("''", "'")
        out.append(raw)
    return out
