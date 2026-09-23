"""layer_tools.report_documenter — branded handover docs from the model (task I-5.2,
DOCX closed in I-10.4).

A Layer-Tool (Invariant I4: standalone + integratable) that turns a
``CanonicalModel`` into a **branded handover document** with a business section
(what the report shows, which KPIs and what they mean) and a technical section
(semantic model: tables, measures + DAX/HITL, relationships, row-level security).

Both output formats share one content extraction (``_extract_content``) so the
business logic — which pages/measures/tables/RLS roles show up, and how RLS's
three-way branch (real filters / roles-without-filters / no roles) resolves —
lives in exactly one place. ``render_markdown`` and ``_build_handover_doc`` are
both thin formatters over that shared ``_ModelContent``, not two independent
walks of ``CanonicalModel`` that could silently drift apart.

Two output formats:
  - **Markdown** (``render_markdown``) — Invariant I2: pure, byte-deterministic,
    snapshot-testable. The shipping default (I-5.2 rollback) and the fallback
    when DOCX rendering fails.
  - **DOCX** (``render_docx``, I-10.4) — branded via the repo's own governed
    ``core/brand`` BrandSpec system (NOT Meridian's ``docx_branding``, which is
    not vendored anywhere in this repo and has no vendoring precedent beyond
    the one-time ``pbi_engine`` sync — see ADR-0005/I-2.2). Uses
    ``core.brand.derivations.docx_document`` (a pure BrandSpec → docx.Document
    converter, the same "define once, derive everywhere" pattern as
    ``pbi_theme.py``/``css_variables.py``) and the real ``python-docx``
    dependency. DOCX bytes are not byte-stable across runs (OOXML embeds a
    creation timestamp + per-run relationship IDs) — see
    ``docx_document.py``'s determinism note; content/styling is deterministic,
    the serialized zip is not.
"""
from __future__ import annotations

import argparse
import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from core.brand.derivations.docx_document import DocSection, DocTable, HandoverDoc, spec_to_docx
from core.brand.derivations.loader import load_brand_spec
from tooling.superversion.canonical_contract import CanonicalModel
from tooling.superversion.from_aluca import from_bracket_file

_REPO_ROOT = Path(__file__).resolve().parents[3]
_KPIS = _REPO_ROOT / "core" / "kpi_catalog" / "kpis"
_DEFAULT_BRACKET = (
    _REPO_ROOT / "core" / "usecases" / "core" / "COM-001_Sales_Performance" / "UseCase_Bracket.yaml"
)
_DEFAULT_BRAND_SPEC = _REPO_ROOT / "core" / "brand" / "samples" / "generic_brand.yaml"


@dataclass(frozen=True)
class Branding:
    """Minimal branding applied to the Markdown title block. The DOCX renderer
    (I-10.4) uses the richer ``core/brand`` BrandSpec instead — see
    ``render_docx``."""
    product_name: str = "ALUCA Superversion"
    tagline: str = "Analytics Library of Use Cases — governed delivery"


class DocxRenderError(Exception):
    """Raised when DOCX rendering fails — callers fall back to Markdown."""


# --------------------------------------------------------------------------- #
# Shared content extraction (CanonicalModel -> _ModelContent, format-neutral) #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class _PageInfo:
    label: str
    is_hidden: bool
    visual_count: int
    visual_types: str  # sorted, comma-joined; "—" if none


@dataclass(frozen=True)
class _MeasureInfo:
    name: str
    purpose: str
    format_string: str
    table: str
    dax: str


@dataclass(frozen=True)
class _TableInfo:
    name: str
    column_count: int
    measure_count: int


@dataclass(frozen=True)
class _RlsRole:
    name: str
    filters: str  # "table: expr; table2: expr2"


@dataclass(frozen=True)
class _RlsInfo:
    roles_with_filters: list[_RlsRole] = field(default_factory=list)
    role_count: int = 0  # total sm.roles count, for the "N roles, no filter" case


@dataclass(frozen=True)
class _ModelContent:
    report_name: str
    semantic_model_name: str
    pages: list[_PageInfo]
    measures: list[_MeasureInfo]
    table_count: int
    relationship_count: int
    role_count: int
    tables: list[_TableInfo]
    rls: _RlsInfo


def _measure_index(model: CanonicalModel) -> dict[str, str]:
    """measure name → owning table (deterministic, first occurrence wins)."""
    owner: dict[str, str] = {}
    for table in model.semantic.tables:
        for m in table.measures:
            owner.setdefault(m.name, table.name)
    return owner


def _dax_of(measure) -> str:
    dialect = (getattr(measure, "expressions", None) or {}).get("dax", "")
    if dialect:
        return dialect.strip()
    if measure.expression:
        return measure.expression.strip()
    return "BLANK()  (HITL: DAX dialect to be defined)"


def _extract_content(model: CanonicalModel) -> _ModelContent:
    """CanonicalModel → format-neutral content. The single source of truth for
    what shows up in a handover doc — both render_markdown and
    _build_handover_doc format this same extraction, never the model directly."""
    sm, rep = model.semantic, model.report
    owner = _measure_index(model)

    pages = [
        _PageInfo(
            label=p.display_name or p.name,
            is_hidden=p.is_hidden,
            visual_count=len(p.visuals),
            visual_types=", ".join(sorted({v.visual_type for v in p.visuals})) or "—",
        )
        for p in rep.pages
    ]

    measures = [
        _MeasureInfo(
            name=m.name,
            purpose=" ".join((m.description or "").split()) or "—",
            format_string=m.format_string or "—",
            table=owner.get(m.name, table.name),
            dax=_dax_of(m),
        )
        for table in sm.tables for m in table.measures
    ]

    tables = [
        _TableInfo(name=t.name, column_count=len(t.columns), measure_count=len(t.measures))
        for t in sm.tables
    ]

    rls_roles = [r for r in sm.roles if any((tp.filter_expression or "").strip()
                                            for tp in r.table_permissions)]
    roles_with_filters = [
        _RlsRole(
            name=r.name,
            filters="; ".join(
                f"{tp.table}: {tp.filter_expression}" for tp in r.table_permissions
                if (tp.filter_expression or "").strip()
            ),
        )
        for r in rls_roles
    ]

    return _ModelContent(
        report_name=rep.name,
        semantic_model_name=sm.name,
        pages=pages,
        measures=measures,
        table_count=len(sm.tables),
        relationship_count=len(sm.relationships),
        role_count=len(sm.roles),
        tables=tables,
        rls=_RlsInfo(roles_with_filters=roles_with_filters, role_count=len(sm.roles)),
    )


# --------------------------------------------------------------------------- #
# Markdown formatter                                                          #
# --------------------------------------------------------------------------- #

def render_markdown(model: CanonicalModel, *, branding: Branding = Branding()) -> str:
    """CanonicalModel → branded Markdown handover doc. Deterministic (Invariant I2)."""
    content = _extract_content(model)
    L: list[str] = []

    # --- Title block (branding) -------------------------------------------- #
    L.append(f"# {content.report_name} — Handover Documentation")
    L.append("")
    L.append(f"> **{branding.product_name}** · {branding.tagline}")
    L.append(f"> Layer-Tool: report-documenter · Semantic model: `{content.semantic_model_name}`")
    L.append("")

    # --- Business ---------------------------------------------------------- #
    L.append("## Business")
    L.append("")
    L.append("### Report Pages")
    if content.pages:
        for p in content.pages:
            hidden = " _(hidden)_" if p.is_hidden else ""
            L.append(f"- **{p.label}**{hidden} — {p.visual_count} visual(s): {p.visual_types}")
    else:
        L.append("- _(no pages)_")
    L.append("")
    L.append("### KPIs & Meaning")
    L.append("")
    L.append("| Measure | Purpose | Format |")
    L.append("|---|---|---|")
    for m in content.measures:
        L.append(f"| {m.name} | {m.purpose} | {m.format_string} |")
    L.append("")

    # --- Technical --------------------------------------------------------- #
    L.append("## Technical")
    L.append("")
    L.append(f"### Semantic Model: `{content.semantic_model_name}`")
    L.append(f"- Tables: {content.table_count} · Relationships: {content.relationship_count} · "
             f"Roles: {content.role_count}")
    L.append("")
    L.append("### Tables")
    for t in content.tables:
        L.append(f"- **{t.name}** — {t.column_count} column(s), {t.measure_count} measure(s)")
    L.append("")
    L.append("### Measures (DAX dialect / HITL)")
    L.append("")
    L.append("| Measure | Table | DAX |")
    L.append("|---|---|---|")
    for m in content.measures:
        L.append(f"| {m.name} | {m.table} | `{m.dax}` |")
    L.append("")
    L.append("### Row-Level Security")
    if content.rls.roles_with_filters:
        for r in content.rls.roles_with_filters:
            L.append(f"- **{r.name}** — {r.filters}")
    elif content.rls.role_count:
        L.append(f"- {content.rls.role_count} role(s) defined; no row-level filter (RLS placeholder)")
    else:
        L.append("- _(no roles)_")
    L.append("")
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------- #
# DOCX formatter (I-10.4)                                                     #
# --------------------------------------------------------------------------- #

def _build_handover_doc(model: CanonicalModel, branding: Branding) -> HandoverDoc:
    """_ModelContent → tool-agnostic HandoverDoc content tree, for the DOCX
    renderer. Formats the same shared extraction render_markdown formats —
    never re-derives content from CanonicalModel independently."""
    content = _extract_content(model)

    business_paras = ["Report Pages:"]
    if content.pages:
        for p in content.pages:
            hidden = " (hidden)" if p.is_hidden else ""
            business_paras.append(f"{p.label}{hidden} — {p.visual_count} visual(s): {p.visual_types}")
    else:
        business_paras.append("(no pages)")

    kpi_rows = [[m.name, m.purpose, m.format_string] for m in content.measures]
    measure_rows = [[m.name, m.table, m.dax] for m in content.measures]

    technical_paras = [
        f"Tables: {content.table_count} · Relationships: {content.relationship_count} · "
        f"Roles: {content.role_count}",
    ]
    tables_paras = [
        f"{t.name} — {t.column_count} column(s), {t.measure_count} measure(s)" for t in content.tables
    ]

    if content.rls.roles_with_filters:
        rls_paras = [f"{r.name} — {r.filters}" for r in content.rls.roles_with_filters]
    elif content.rls.role_count:
        rls_paras = [f"{content.rls.role_count} role(s) defined; no row-level filter (RLS placeholder)"]
    else:
        rls_paras = ["(no roles)"]

    return HandoverDoc(
        title=f"{content.report_name} — Handover Documentation",
        subtitle_lines=[
            f"{branding.product_name} · {branding.tagline}",
            f"Layer-Tool: report-documenter · Semantic model: {content.semantic_model_name}",
        ],
        sections=[
            DocSection(heading="Business", level=1, paragraphs=business_paras),
            DocSection(heading="KPIs & Meaning", level=2,
                       table=DocTable(headers=["Measure", "Purpose", "Format"], rows=kpi_rows)),
            DocSection(heading="Technical", level=1, paragraphs=technical_paras),
            DocSection(heading="Tables", level=2, paragraphs=tables_paras),
            DocSection(heading="Measures (DAX dialect / HITL)", level=2,
                       table=DocTable(headers=["Measure", "Table", "DAX"], rows=measure_rows)),
            DocSection(heading="Row-Level Security", level=2, paragraphs=rls_paras),
        ],
    )


def render_docx(
    model: CanonicalModel,
    *,
    branding: Branding = Branding(),
    brand_spec_path: Path = _DEFAULT_BRAND_SPEC,
) -> bytes:
    """CanonicalModel → branded DOCX handover doc, styled via the repo's own
    governed core/brand BrandSpec (I-10.4). Content/styling deterministic
    (I2); serialized bytes are not (see module docstring).

    Raises DocxRenderError on any failure (missing/invalid BrandSpec, python-docx
    error) — callers fall back to render_markdown per the I-10.4 DoD
    ("Branding-Layout bricht → MD-Fallback")."""
    try:
        spec = load_brand_spec(brand_spec_path)
        doc = _build_handover_doc(model, branding)
        document = spec_to_docx(spec, doc)
        buf = io.BytesIO()
        document.save(buf)
        return buf.getvalue()
    except Exception as exc:  # noqa: BLE001 — any failure here means "use the MD fallback"
        raise DocxRenderError(f"DOCX rendering failed: {exc}") from exc


# --------------------------------------------------------------------------- #
# Standalone CLI                                                              #
# --------------------------------------------------------------------------- #


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tooling.superversion.layer_tools.report_documenter",
        description="Report-Documenter: branded Markdown/DOCX handover doc from a bracket (I-5.2/I-10.4).",
    )
    parser.add_argument("bracket", nargs="?", type=Path, default=_DEFAULT_BRACKET,
                        help="UseCase_Bracket.yaml (default: COM-001)")
    parser.add_argument("--kpis", type=Path, default=_KPIS, help="KPI catalog dir")
    parser.add_argument("--format", choices=["md", "docx"], default="md",
                        help="output format (default: md — the shipping format, I-5.2)")
    parser.add_argument("--brand-spec", type=Path, default=_DEFAULT_BRAND_SPEC,
                        help="BrandSpec YAML for --format docx (default: core/brand/samples/generic_brand.yaml)")
    parser.add_argument("--out", type=Path, default=None,
                        help="write output here (else stdout for md; required for docx)")
    args = parser.parse_args(argv)

    if not args.bracket.exists():
        print(f"[documenter] bracket not found: {args.bracket}")
        return 1
    model = from_bracket_file(args.bracket, args.kpis)

    if args.format == "docx":
        if not args.out:
            print("[documenter] --out is required for --format docx (binary output)")
            return 1
        try:
            data = render_docx(model, brand_spec_path=args.brand_spec)
            args.out.write_bytes(data)
            print(f"[documenter] wrote {args.out}")
        except DocxRenderError as exc:
            # DoD: a broken branding layout falls back to Markdown, never a crash.
            fallback = args.out.with_suffix(".md")
            fallback.write_text(render_markdown(model), encoding="utf-8", newline="\n")
            print(f"[documenter] DOCX render failed ({exc}); wrote Markdown fallback to {fallback}")
        return 0

    md = render_markdown(model)
    if args.out:
        args.out.write_text(md, encoding="utf-8", newline="\n")
        print(f"[documenter] wrote {args.out}")
    else:
        print(md, end="")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
