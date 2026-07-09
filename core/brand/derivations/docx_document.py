"""
BrandSpec → branded Word document (python-docx) converter.

Single responsibility: translate a validated BrandSpec dict + a tool-agnostic
document content tree into a styled ``docx.Document``, following the same
"define once, derive everywhere" pattern as ``pbi_theme.py``/``css_variables.py``
(see ``core/brand/tool_derivations/`` for the PBI/CSS mapping references this
module's docstrings below mirror for DOCX).

This module knows nothing about ``CanonicalModel`` or any Superversion type —
callers (e.g. ``tooling/superversion/layer_tools/report_documenter.py``) build
a ``HandoverDoc`` from their own domain content and pass it in here.

Determinism note (I2): given the same BrandSpec + ``HandoverDoc``, the
document's STRUCTURE and STYLING are deterministic. The serialized ``.docx``
bytes are NOT byte-stable across runs — OOXML zips embed a creation timestamp
and per-part relationship IDs that vary run to run even with identical
content. Callers that need regression coverage should snapshot the extracted
paragraph/table TEXT and style names, not raw bytes (see
``spec_to_docx``'s module-level note and the paired test file).

Pure function — no file I/O, no side effects. The caller writes the returned
``Document`` to disk (``document.save(path)``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

# Standard print-safe page margins (Word's own default). BrandSpec's `spacing`
# tokens are a UI/component rhythm scale (8px grid), not a page-margin
# convention — using them for physical page margins would be a category
# error, so this stays a fixed, sensible print default instead of a
# brand-derived value.
_PAGE_MARGIN_IN = 1.0

# rem → pt conversion for print/export, mirroring pbi_theme.py's _PBI_PT_PER_REM
# pattern: BrandSpec's typography.tool_minimums.export_pdf already gives real
# pt floors for this exact medium, so those are used directly as the primary
# source; type_scale rem values are converted only where no export_pdf floor
# exists for a role.
_REM_TO_PT = 12.0


@dataclass(frozen=True)
class DocTable:
    headers: list[str]
    rows: list[list[str]]


@dataclass(frozen=True)
class DocSection:
    heading: str
    level: int  # 1 = heading_2 role (top section), 2 = heading_3 role (subsection)
    paragraphs: list[str] = field(default_factory=list)
    table: Optional[DocTable] = None


@dataclass(frozen=True)
class HandoverDoc:
    """Tool-agnostic content tree for a branded handover document."""
    title: str
    subtitle_lines: list[str]
    sections: list[DocSection]


def _hex_to_rgbcolor(hex_str: str) -> RGBColor:
    h = hex_str.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _enable_hyphenation(document: Document) -> None:
    """Document-level auto-hyphenation (w:autoHyphenation). python-docx has no
    high-level API for this Word setting, so it's set via the documented XML
    escape hatch (docx.oxml) rather than left unset."""
    settings = document.settings.element
    el = OxmlElement("w:autoHyphenation")
    el.set(qn("w:val"), "1")
    settings.append(el)


def _apply_page_setup(document: Document) -> None:
    section = document.sections[0]
    section.left_margin = Inches(_PAGE_MARGIN_IN)
    section.right_margin = Inches(_PAGE_MARGIN_IN)
    section.top_margin = Inches(_PAGE_MARGIN_IN)
    section.bottom_margin = Inches(_PAGE_MARGIN_IN)


def _apply_base_styles(document: Document, spec: dict[str, Any]) -> None:
    typo = spec["typography"]
    color = spec["color"]
    export_pdf = typo.get("tool_minimums", {}).get("export_pdf", {})
    body_pt = export_pdf.get("body_pt", 11)
    font_primary = typo["font_family"].get("primary", "Segoe UI").split(",")[0].strip()

    normal = document.styles["Normal"]
    normal.font.name = font_primary
    normal.font.size = Pt(body_pt)
    normal.font.color.rgb = _hex_to_rgbcolor(color["neutral_scale"]["900"])
    normal.paragraph_format.widow_control = True


def _heading_pt(spec: dict[str, Any], level: int) -> int:
    """Heading font size in pt: export_pdf floor as the safety net, scaled up
    per level so heading_1 > heading_2 > heading_3 (mirrors the type_scale
    role_map's heading_1/2/3 → 2xl/xl/lg ordering without hard-coding rem math
    per role — there is no export_pdf entry per heading role, only body/label)."""
    export_pdf = spec["typography"].get("tool_minimums", {}).get("export_pdf", {})
    floor = export_pdf.get("body_pt", 11)
    return {0: floor + 10, 1: floor + 6, 2: floor + 2}.get(level, floor)


def _add_title_block(document: Document, spec: dict[str, Any], doc: HandoverDoc) -> None:
    color = spec["color"]
    identity = spec["identity"]

    title = document.add_heading(level=0)
    title.paragraph_format.widow_control = True
    run = title.add_run(doc.title)
    run.font.color.rgb = _hex_to_rgbcolor(color["primary"])
    run.font.size = Pt(_heading_pt(spec, 0))

    brand_line = document.add_paragraph()
    brand_line.paragraph_format.widow_control = True
    brand_run = brand_line.add_run(identity.get("brand_name", identity.get("brand_id", "")))
    brand_run.bold = True
    brand_run.font.color.rgb = _hex_to_rgbcolor(color["secondary"])

    for line in doc.subtitle_lines:
        p = document.add_paragraph(line)
        p.paragraph_format.widow_control = True
        for run in p.runs:
            run.font.color.rgb = _hex_to_rgbcolor(color["neutral_scale"]["700"])
            run.font.size = Pt(spec["typography"].get("tool_minimums", {})
                                .get("export_pdf", {}).get("label_pt", 9))


def _add_section(document: Document, spec: dict[str, Any], section: DocSection) -> None:
    color = spec["color"]
    heading = document.add_heading(level=section.level + 1)
    heading.paragraph_format.widow_control = True
    heading.paragraph_format.keep_with_next = True  # a heading orphaned from its body reads as broken
    run = heading.add_run(section.heading)
    run.font.color.rgb = _hex_to_rgbcolor(color["primary"] if section.level == 1 else color["neutral_scale"]["900"])
    run.font.size = Pt(_heading_pt(spec, section.level))

    for text in section.paragraphs:
        p = document.add_paragraph(text)
        p.paragraph_format.widow_control = True

    if section.table is not None:
        _add_table(document, spec, section.table)


def _add_table(document: Document, spec: dict[str, Any], table_content: DocTable) -> None:
    color = spec["color"]
    n_cols = len(table_content.headers)
    table = document.add_table(rows=1, cols=max(n_cols, 1))
    table.style = "Light Grid Accent 1"

    header_cells = table.rows[0].cells
    for i, header in enumerate(table_content.headers):
        header_cells[i].text = header
        for p in header_cells[i].paragraphs:
            p.paragraph_format.widow_control = True
            for run in p.runs:
                run.bold = True
                run.font.color.rgb = _hex_to_rgbcolor(color["neutral_scale"]["50"])

    for row in table_content.rows:
        cells = table.add_row().cells
        for i, value in enumerate(row[:n_cols]):
            cells[i].text = str(value)
            for p in cells[i].paragraphs:
                p.paragraph_format.widow_control = True


def spec_to_docx(spec: dict[str, Any], doc: HandoverDoc) -> Document:
    """
    Convert a validated BrandSpec dict + a HandoverDoc content tree into a
    branded ``docx.Document`` — margins, hyphenation, and widow/orphan control
    are always applied (the DoD's "Margins/Silbentrennung/Widow-Control"
    requirement), typography/color come from the BrandSpec.

    Args:
        spec: Validated BrandSpec dict (from core.brand.derivations.loader.load_brand_spec).
        doc: Tool-agnostic document content (title, subtitle lines, sections).

    Returns:
        A ``docx.Document`` ready to ``.save(path)``.
    """
    document = Document()
    _apply_page_setup(document)
    _enable_hyphenation(document)
    _apply_base_styles(document, spec)
    _add_title_block(document, spec, doc)
    for section in doc.sections:
        _add_section(document, spec, section)
    return document
