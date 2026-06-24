"""layer_tools.report_documenter — branded handover docs from the model (task I-5.2).

A Layer-Tool (Invariant I4: standalone + integratable) that turns a
``CanonicalModel`` into a **branded handover document** with a business section
(what the report shows, which KPIs and what they mean) and a technical section
(semantic model: tables, measures + DAX/HITL, relationships, row-level security).

Output format: **Markdown** (Invariant I2: pure, deterministic → snapshot-testable).
Meridian's ``docx_branding``/``xlsx_branding`` is NOT vendored yet and
``python-docx`` is not a dependency, so the DOCX path is deferred; per the I-5.2
rollback, Markdown is the shipping format. The branding is applied as a title
block + section scaffold so the DOCX renderer can later consume the same
structure.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from tooling.superversion.canonical_contract import CanonicalModel
from tooling.superversion.from_aluca import from_bracket_file


@dataclass(frozen=True)
class Branding:
    """Minimal branding applied to the handover doc (the DOCX renderer, when
    Meridian's docx_branding is vendored, will consume the same fields)."""
    product_name: str = "ALUCA Superversion"
    tagline: str = "Analytics Library of Use Cases — governed delivery"


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


def render_markdown(model: CanonicalModel, *, branding: Branding = Branding()) -> str:
    """CanonicalModel → branded Markdown handover doc. Deterministic (Invariant I2)."""
    sm, rep = model.semantic, model.report
    owner = _measure_index(model)
    L: list[str] = []

    # --- Title block (branding) -------------------------------------------- #
    L.append(f"# {rep.name} — Handover Documentation")
    L.append("")
    L.append(f"> **{branding.product_name}** · {branding.tagline}")
    L.append(f"> Layer-Tool: report-documenter · Semantic model: `{sm.name}`")
    L.append("")

    # --- Business ---------------------------------------------------------- #
    L.append("## Business")
    L.append("")
    L.append("### Report Pages")
    if rep.pages:
        for p in rep.pages:
            hidden = " _(hidden)_" if p.is_hidden else ""
            types = ", ".join(sorted({v.visual_type for v in p.visuals})) or "—"
            L.append(f"- **{p.display_name or p.name}**{hidden} — {len(p.visuals)} visual(s): {types}")
    else:
        L.append("- _(no pages)_")
    L.append("")
    L.append("### KPIs & Meaning")
    L.append("")
    L.append("| Measure | Purpose | Format |")
    L.append("|---|---|---|")
    for table in sm.tables:
        for m in table.measures:
            purpose = " ".join((m.description or "").split()) or "—"
            fmt = m.format_string or "—"
            L.append(f"| {m.name} | {purpose} | {fmt} |")
    L.append("")

    # --- Technical --------------------------------------------------------- #
    L.append("## Technical")
    L.append("")
    L.append(f"### Semantic Model: `{sm.name}`")
    L.append(f"- Tables: {len(sm.tables)} · Relationships: {len(sm.relationships)} · "
             f"Roles: {len(sm.roles)}")
    L.append("")
    L.append("### Tables")
    for t in sm.tables:
        L.append(f"- **{t.name}** — {len(t.columns)} column(s), {len(t.measures)} measure(s)")
    L.append("")
    L.append("### Measures (DAX dialect / HITL)")
    L.append("")
    L.append("| Measure | Table | DAX |")
    L.append("|---|---|---|")
    for table in sm.tables:
        for m in table.measures:
            L.append(f"| {m.name} | {owner.get(m.name, table.name)} | `{_dax_of(m)}` |")
    L.append("")
    L.append("### Row-Level Security")
    rls_roles = [r for r in sm.roles if any((tp.filter_expression or '').strip()
                                            for tp in r.table_permissions)]
    if rls_roles:
        for r in rls_roles:
            filters = "; ".join(f"{tp.table}: {tp.filter_expression}" for tp in r.table_permissions
                                if (tp.filter_expression or "").strip())
            L.append(f"- **{r.name}** — {filters}")
    elif sm.roles:
        L.append(f"- {len(sm.roles)} role(s) defined; no row-level filter (RLS placeholder)")
    else:
        L.append("- _(no roles)_")
    L.append("")
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------- #
# Standalone CLI                                                              #
# --------------------------------------------------------------------------- #

_REPO_ROOT = Path(__file__).resolve().parents[3]
_KPIS = _REPO_ROOT / "core" / "kpi_catalog" / "kpis"
_DEFAULT_BRACKET = (
    _REPO_ROOT / "core" / "usecases" / "core" / "COM-001_Sales_Performance" / "UseCase_Bracket.yaml"
)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tooling.superversion.layer_tools.report_documenter",
        description="Report-Documenter: branded Markdown handover doc from a bracket (I-5.2).",
    )
    parser.add_argument("bracket", nargs="?", type=Path, default=_DEFAULT_BRACKET,
                        help="UseCase_Bracket.yaml (default: COM-001)")
    parser.add_argument("--kpis", type=Path, default=_KPIS, help="KPI catalog dir")
    parser.add_argument("--out", type=Path, default=None, help="write Markdown here (else stdout)")
    args = parser.parse_args(argv)

    if not args.bracket.exists():
        print(f"[documenter] bracket not found: {args.bracket}")
        return 1
    model = from_bracket_file(args.bracket, args.kpis)
    md = render_markdown(model)
    if args.out:
        args.out.write_text(md, encoding="utf-8")
        print(f"[documenter] wrote {args.out}")
    else:
        print(md, end="")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
