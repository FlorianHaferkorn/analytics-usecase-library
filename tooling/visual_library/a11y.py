"""a11y.py — accessibility generation for the Visual Library (zero-dependency).

Today the only screen-reader affordance is a single hard-coded `aria-label` in each idiom's
preview_svg — the idiom NAME, nothing data-driven. This composes the two things the roadmap named,
grounded in Chartability (Elavsky) and the UK Government Analysis Function chart-a11y guidance:

  1. real per-idiom ALT-TEXT / aria description — chart type + what it shows (from the idiom's
     governed purpose) + an optional data-driven clause (count, highest/lowest, direction);
  2. a screen-reader DATA-TABLE fallback — the equivalent non-visual representation, as accessible
     HTML (`<caption>` + `scope="col"`) and Markdown.

It reads the same SoT the resolver does (index.yaml purpose questions + <idiom>.yaml), needs no
per-idiom hand-authoring, and is pure Python — so it ships in the Workflow-B bundle and both
workflows can attach an accessible name to every generated visual.

For the Deneb / web track, `vegalite_description()` returns the string to drop into a Vega-Lite spec's
top-level `description` (which Vega-Lite renders as the SVG aria-label) at GENERATION time — the frozen
goldens are left untouched. The deeper keyboard-navigable tree (olli) is a documented follow-up.

CLI:
  a11y.py alt <idiom> [--profile p]     # the composed alt-text / aria description
  a11y.py label <idiom>                 # the short aria-label
  a11y.py list                          # alt-text for every implemented idiom
"""
from __future__ import annotations

import html
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render  # noqa: E402

LIB = render.LIB

# Governed one-line phrasing of each analytical purpose (see index.yaml). The a11y layer must cover
# every purpose in the chooser — test_a11y enforces it, so a new purpose cannot ship label-less.
PURPOSE_PHRASE = {
    "time_comparison":       "how a measure develops over time",
    "deviation_from_target": "how far actuals sit from target",
    "compare_categories":    "how categories rank against each other",
    "contribution_to_change": "which drivers moved the total from one value to another",
    "part_to_whole":         "each part's share of the whole",
    "correlation":           "how two measures relate",
    "flow_between_stages":   "how quantity flows between stages",
    "driver_breakdown":      "which dimension drives the number",
    "distribution":          "the spread, median and outliers of a measure",
    "evidence_detail":       "the worst rows and the next action",
    "value_verdict":         "the headline value and its verdict",
}

# Which Chartability (Elavsky) heuristic families this generator helps satisfy — for the audit trail.
CHARTABILITY_REFS = {
    "alt_text":    "Perceivable — a text alternative conveying the chart's message",
    "data_table":  "Perceivable/Robust — an equivalent data-table representation",
    "not_colour_only": "Perceivable — colour is never the sole channel (see contrast.py series_cap)",
}


def _purpose_phrase(purposes: "list[str]") -> str:
    return "; ".join(PURPOSE_PHRASE.get(p, p.replace("_", " ")) for p in (purposes or []))


def _summary_clause(s: dict) -> str:
    """Turn a small data summary into a sentence clause. `s` may carry: n, unit (what the rows are),
    top/bottom {label, value}, direction."""
    bits = []
    if s.get("n") is not None:
        unit = s.get("unit", "items")
        bits.append(f"{s['n']} {unit}")
    if s.get("top"):
        t = s["top"]
        bits.append(f"highest {t.get('label')} ({t.get('value')})")
    if s.get("bottom"):
        b = s["bottom"]
        bits.append(f"lowest {b.get('label')} ({b.get('value')})")
    if s.get("direction"):
        bits.append(f"trend {s['direction']}")
    return (" " + "; ".join(bits) + ".") if bits else ""


def alt_text(idiom: str, summary: "dict | None" = None) -> str:
    """The full alt-text / aria description: chart type + what it shows + optional data clause.
    An explicit `a11y.alt` in the idiom YAML overrides the composed base."""
    e = render.load_entry(idiom)
    override = (e.get("a11y") or {}).get("alt")
    base = override or f"{e.get('name')} showing {_purpose_phrase(e.get('purpose'))}."
    return base + (_summary_clause(summary) if summary else "")


def aria_label(idiom: str, summary: "dict | None" = None) -> str:
    """A short single-line accessible name (role=img aria-label). Same content as alt_text; kept as a
    separate entry point so callers pick the right ARIA slot."""
    return alt_text(idiom, summary)


def vegalite_description(idiom: str, summary: "dict | None" = None) -> str:
    """The string to set as a Vega-Lite spec's top-level `description` (→ SVG aria-label) when the
    generator emits the Deneb/web realization. Frozen goldens are not modified."""
    return alt_text(idiom, summary)


def data_table(headers: "list[str]", rows: "list[list]", caption: str = "") -> dict:
    """A screen-reader data-table fallback as accessible HTML (`<caption>` + `scope='col'`) and
    Markdown. Deterministic; the caller supplies the bound data."""
    cap = html.escape(caption) if caption else ""
    th = "".join(f'<th scope="col">{html.escape(str(h))}</th>' for h in headers)
    trs = "".join(
        "<tr>" + "".join(f"<td>{html.escape(str(c))}</td>" for c in row) + "</tr>"
        for row in rows
    )
    html_out = (f'<table>{f"<caption>{cap}</caption>" if cap else ""}'
                f"<thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>")

    md_head = "| " + " | ".join(str(h) for h in headers) + " |"
    md_sep = "| " + " | ".join("---" for _ in headers) + " |"
    md_rows = ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    md = "\n".join(([f"**{caption}**", ""] if caption else []) + [md_head, md_sep, *md_rows])
    return {"html": html_out, "markdown": md}


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def _implemented() -> "list[str]":
    return yaml.safe_load((LIB / "index.yaml").read_text(encoding="utf-8")).get("implemented", [])


def main(argv: "list[str]") -> int:
    if not argv:
        print(__doc__)
        return 2
    cmd = argv[0]
    rest = [a for a in argv[1:] if not a.startswith("--")]
    if cmd == "alt" and rest:
        print(alt_text(rest[0]))
        return 0
    if cmd == "label" and rest:
        print(aria_label(rest[0]))
        return 0
    if cmd == "list":
        for iid in _implemented():
            print(f"  {iid:18s} {alt_text(iid)}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
