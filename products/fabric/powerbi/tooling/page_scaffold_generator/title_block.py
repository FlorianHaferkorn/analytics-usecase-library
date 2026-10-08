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

from typing import Any, Dict, List, Optional

from .title_policy import DEFAULT_KEY_MESSAGE_POSITION, TitleLines, ibcs_lines

#: Height of the title block on the 1920×1080 canvas: key message (14 pt) plus three lines (11 pt).
#: Same value as Meridian ``title_block.HOEHE_PX``.
TITLE_BLOCK_HEIGHT = 112

_SIZE_KEY_MESSAGE = 14
_SIZE_LINE = 11


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
