"""AI instructions — Freitext-Geschäftskontext für "Prep data for AI" (Preview).

Erzeugt aus governance.json (Glossar, Ownership) + kpi.json (Bedeutung, Formeln,
Schwellen) + strategy.json (Ziel-Kontext) einen kompakten, copy-paste-fähigen
Text in zwei Varianten: Markdown (Doku/Review) und Plaintext (Eingabefeld im
Power-BI-Service). Deterministisch — gleicher Core, gleicher Text.
"""
from __future__ import annotations

from products.meridian_copilot_readiness.generator.loader import (
    CopilotCore,
    pick_label,
)

# Ein Abschnitt = (Überschrift, Zeilen). Zeilen mit führendem "- " sind Bullets.
Section = tuple[str, list[str]]


def _fmt_value(value: object, unit: str) -> str:
    if value is None:
        return "—"
    text = f"{value:,}".replace(",", ".") if isinstance(value, int) else str(value)
    return f"{text} {unit}".strip()


def _direction_text(direction: str) -> str:
    return {
        "higher_is_better": "höher ist besser",
        "lower_is_better": "niedriger ist besser",
    }.get(direction, direction or "—")


def _alert_text(kpi: dict) -> str:
    alert = (kpi.get("targets") or {}).get("alert_threshold") or {}
    value = alert.get("value")
    if value is None:
        return ""
    unit = (kpi.get("definition") or {}).get("unit") or ""
    word = "Unterschreitung" if kpi.get("direction") == "higher_is_better" else "Überschreitung"
    return f"Alert bei {word} von {_fmt_value(value, unit)}"


def _kpi_lines(core: CopilotCore, kpi: dict) -> list[str]:
    label_de = pick_label(kpi.get("label"), "de")
    definition = kpi.get("definition") or {}
    targets = kpi.get("targets") or {}
    meta = kpi.get("meta") or {}
    data_source = kpi.get("data_source") or {}
    unit = definition.get("unit") or ""

    parts: list[str] = [
        f"- **{label_de} ({kpi.get('id', '?')})** — Formel: {definition.get('formula', '—')}. "
        f"Einheit: {unit or '—'}. Richtung: {_direction_text(kpi.get('direction', ''))}."
    ]

    target = (targets.get("strategic_target") or {})
    baseline = (targets.get("baseline") or {})
    detail: list[str] = []
    if target.get("value") is not None:
        owner = target.get("owner")
        detail.append(
            f"Ziel: {_fmt_value(target.get('value'), unit)}"
            + (f" (Owner: {owner})" if owner else "")
        )
    if baseline.get("value") is not None:
        detail.append(f"Baseline: {_fmt_value(baseline.get('value'), unit)} ({baseline.get('method', '—')})")
    alert = _alert_text(kpi)
    if alert:
        detail.append(alert)
    if detail:
        parts.append("  " + "; ".join(detail) + ".")

    domain_id = data_source.get("domain_id")
    src = []
    if domain_id:
        src.append(f"Datenquelle: {domain_id} ({core.domain_label(domain_id, 'de')}), Feld `{data_source.get('field', '—')}`")
    if meta.get("owner"):
        src.append(f"verantwortlich: {meta['owner']}")
    if meta.get("update_frequency"):
        src.append(f"Aktualisierung: {meta['update_frequency']}")
    if src:
        parts.append("  " + "; ".join(src) + ".")
    return parts


def build_sections(core: CopilotCore) -> list[Section]:
    """Strukturierte Abschnitte — gemeinsame Quelle für MD- und TXT-Variante."""
    sections: list[Section] = []

    # ── 1. Geschäftskontext ──────────────────────────────────────────────────
    ctx: list[str] = []
    intro = core.org_name()
    if core.org_sector():
        intro += f" — {core.org_sector()}"
    ctx.append(intro + ".")
    if core.objectives:
        ctx.append("Strategische Ziele:")
        for obj in core.objectives:
            label = pick_label(obj.get("label"), "de")
            horizon = obj.get("time_horizon")
            owner = obj.get("owner")
            suffix = ", ".join(x for x in [f"bis {horizon}" if horizon else "", f"Owner: {owner}" if owner else ""] if x)
            ctx.append(f"- {label}" + (f" ({suffix})" if suffix else "") + f": {obj.get('description', '')}")
    ns_id = core.north_star_kpi_id()
    if ns_id:
        ns = next((k for k in core.kpis if k.get("id") == ns_id), None)
        if ns is not None:
            ctx.append(f"Nordstern-KPI: {pick_label(ns.get('label'), 'de')} ({ns_id}).")
    sections.append(("Geschäftskontext", ctx))

    # ── 2. Verbindliche Begriffsdefinitionen (Glossar) ───────────────────────
    glos: list[str] = []
    if core.glossary:
        glos.append(
            "Die folgenden Begriffe sind unternehmensweit verbindlich definiert "
            "und von den Data Ownern freigegeben:"
        )
        for entry in core.glossary:
            term = entry.get("term", "?")
            domain = core.domain_label(entry.get("domain_id", ""), "de")
            approver = entry.get("approved_by", "—")
            approved = entry.get("approved_date", "—")
            definition = pick_label(entry.get("definition"), "de")
            line = f"- **{term}** ({domain}; freigegeben: {approver}, {approved}): {definition}"
            example = entry.get("example")
            if example:
                line += f" Beispiel: {example}"
            glos.append(line)
    else:
        glos.append("Kein freigegebenes Glossar im Core hinterlegt.")
    sections.append(("Verbindliche Begriffsdefinitionen (Glossar)", glos))

    # ── 3. KPI-Definitionen und Schwellenwerte ───────────────────────────────
    kpi_lines: list[str] = []
    for kpi in core.kpis:
        kpi_lines.extend(_kpi_lines(core, kpi))
    sections.append(("KPI-Definitionen und Schwellenwerte", kpi_lines))

    # ── 4. Antwortregeln ─────────────────────────────────────────────────────
    default_lang = "Englisch" if core.primary_language() == "en" else "Deutsch"
    rules = [
        "- Verwende für Begriffe und KPIs ausschließlich die obigen Definitionen; "
        "erfinde keine abweichenden Berechnungen oder Synonyme.",
        "- Bewerte KPI-Werte immer relativ zu Ziel und Alert-Schwelle "
        "(im Ziel / unter Ziel / Alert), nie absolut ohne Bezug.",
        "- Nenne bei KPI-Antworten Einheit und Bezugszeitraum.",
        "- Wenn eine Frage einen Begriff verwendet, der nicht im Glossar steht, "
        "weise auf die fehlende verbindliche Definition hin, statt zu raten.",
        f"- Antworte in der Sprache der Frage; Standardsprache ist {default_lang}.",
    ]
    sections.append(("Antwortregeln", rules))
    return sections


def _provenance_line(core: CopilotCore) -> str:
    src = ", ".join(
        f"{s.name}" + (f" ({s.last_updated})" if s.last_updated else "")
        for s in core.sources
    )
    return f"Quelle: Meridian Core — {src}. Deterministisch generiert (kein LLM)."


def render_markdown(core: CopilotCore) -> str:
    lines = [f"# AI Instructions — {core.org_name()}", "", f"> {_provenance_line(core)}", ""]
    for title, body in build_sections(core):
        lines.append(f"## {title}")
        lines.append("")
        lines.extend(body)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_plaintext(core: CopilotCore) -> str:
    """Plaintext-Variante für das AI-instructions-Eingabefeld im Service."""
    lines = [f"AI INSTRUCTIONS — {core.org_name()}", _provenance_line(core), ""]
    for title, body in build_sections(core):
        lines.append(title.upper())
        for raw in body:
            lines.append(raw.replace("**", "").replace("`", ""))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
