"""provision_translations — TMDL culture files for a multilingual semantic model.

A German enterprise usually wants German captions in Power BI while the model itself stays
in the English technical naming the pipeline generates. Tabular supports exactly that
through **cultures**: one `definition/cultures/<culture>.tmdl` per language, translating
`caption`, `description` and `displayFolder` per object, with the client selecting a
language via `LocaleIdentifier` on the connection string.

Nothing in this repo emitted them; the TMDL parser only skips the folder.

**What this module refuses to do.** It does not translate. `fact_orders` → *Aufträge* is a
business-vocabulary decision that belongs to the glossary and the domain owner, not to a
generator — a machine-plausible German caption that is subtly wrong is worse than an
English one, because nobody reviews what already looks finished. So a caption is emitted
only where a governed translation exists; every other object is emitted **without** a
caption (valid TMDL — it simply has no translation yet) and listed in a gaps file.

Where translations come from, in order:
  1. the governed catalog's ``translations`` map on a table/measure, when it carries one;
  2. nothing — the object appears in the gaps list.

TMDL specifics that are easy to get wrong and are pinned by tests:
  * **tab** indentation (the repo's TMDL hardrule and the TMDL default);
  * object names containing whitespace, ``.``, ``=``, ``:`` or ``'`` must be single-quoted,
    with embedded quotes doubled;
  * `model.tmdl` needs a ``ref culture <name>`` per culture, or the file is ignored on
    deserialization.
"""
from __future__ import annotations

from typing import Any

# The three properties Tabular can translate per object.
TRANSLATABLE = ("caption", "description", "displayFolder")

# Characters that force single-quoting of a TMDL object name.
_NEEDS_QUOTES = (" ", ".", "=", ":", "'")


def tmdl_name(name: str) -> str:
    """Quote a TMDL object name when the syntax requires it; escape embedded quotes.

    Getting this wrong is a parse error at load time, not a warning — and measure names
    with spaces (`'Sales Amount'`) are the norm, not the exception.
    """
    text = str(name)
    if any(ch in text for ch in _NEEDS_QUOTES):
        return "'" + text.replace("'", "''") + "'"
    return text


def _catalog_translation(obj: dict[str, Any], culture: str) -> dict[str, str]:
    """Governed translations for one object in one culture, or {} when none exist."""
    translations = obj.get("translations")
    if not isinstance(translations, dict):
        return {}
    entry = translations.get(culture)
    if not isinstance(entry, dict):
        return {}
    return {k: str(v) for k, v in entry.items() if k in TRANSLATABLE and str(v).strip()}


def _objects(bp: dict[str, Any], governed_catalog: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Every translatable object: gold tables from the IR, measures from the catalog.

    Tables come from the blueprint because gold products are what the architecture
    guarantees; measures come from the catalog because that is where they are governed.
    """
    gc = governed_catalog or {}
    by_table: dict[str, dict[str, Any]] = {}

    for product in bp.get("medallion", {}).get("gold", {}).get("data_products", []) or []:
        name = str(product.get("name") or "").strip()
        if name:
            by_table[name] = {"name": name, "kind": "table", "source": {}, "children": []}

    # A catalog table that the IR does not list still belongs in the culture file — it is
    # in the model, so a client will show its untranslated name.
    for table in gc.get("tables", []) or []:
        name = str(table.get("name") or "").strip()
        if not name:
            continue
        by_table.setdefault(name, {"name": name, "kind": "table", "source": {}, "children": []})
        by_table[name]["source"] = table

    for measure in gc.get("measures", []) or []:
        name = str(measure.get("measure_name") or "").strip()
        if not name:
            continue
        home = str(measure.get("table") or measure.get("home_table") or "").strip()
        parent = by_table.get(home)
        if parent is None:
            parent = by_table.setdefault(
                home or "_Measures",
                {"name": home or "_Measures", "kind": "table", "source": {}, "children": []},
            )
        parent["children"].append({"name": name, "kind": "measure", "source": measure})

    for table in by_table.values():
        table["children"].sort(key=lambda c: c["name"])
    return [by_table[k] for k in sorted(by_table)]


def model_name_of(bp: dict[str, Any], fallback: str = "Model") -> str:
    """The semantic model these translations belong to.

    Read from ``medallion.platinum.semantic_model_ref`` — the IR's own name for the semantic
    layer above gold. Hardcoding ``Model`` here would emit culture files that name a model
    the tenant does not have, and a translation attached to the wrong model is not a
    translation at all: it loads, it is ignored, and nothing says why.
    """
    ref = str((bp.get("medallion", {}).get("platinum", {}) or {}).get("semantic_model_ref") or "")
    # A path-ish or extension-carrying ref names a file; the TMDL object wants the bare name.
    stem = ref.replace("\\", "/").rsplit("/", 1)[-1]
    for suffix in (".SemanticModel", ".tmdl", ".pbip"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
    return stem.strip() or fallback


def culture_tmdl(bp: dict[str, Any], culture: str, model_name: str | None = None,
                 governed_catalog: dict[str, Any] | None = None) -> str:
    """One culture file. Tab-indented, per the TMDL default and the repo's TMDL hardrule."""
    model_name = model_name or model_name_of(bp)
    objects = _objects(bp, governed_catalog)

    lines = [f"culture {tmdl_name(culture)}", "\ttranslations", f"\t\tmodel {tmdl_name(model_name)}"]

    for table in objects:
        lines.append(f"\t\t\ttable {tmdl_name(table['name'])}")
        for prop, value in sorted(_catalog_translation(table["source"], culture).items()):
            lines.append(f"\t\t\t\t{prop}: {value}")
        for child in table["children"]:
            lines.append(f"\t\t\t\tmeasure {tmdl_name(child['name'])}")
            for prop, value in sorted(_catalog_translation(child["source"], culture).items()):
                lines.append(f"\t\t\t\t\t{prop}: {value}")

    return "\n".join(lines) + "\n"


def translation_gaps(bp: dict[str, Any], culture: str,
                     governed_catalog: dict[str, Any] | None = None) -> list[str]:
    """Objects with no governed caption in this culture — the list the glossary owner works.

    Deliberately not auto-filled: a machine-plausible caption that is subtly wrong is worse
    than an untranslated one, because nobody reviews what already looks finished.
    """
    gaps = []
    for table in _objects(bp, governed_catalog):
        if "caption" not in _catalog_translation(table["source"], culture):
            gaps.append(f"table {table['name']}")
        for child in table["children"]:
            if "caption" not in _catalog_translation(child["source"], culture):
                gaps.append(f"measure {table['name']}[{child['name']}]")
    return gaps


def model_refs(cultures: list[str]) -> str:
    """The ``ref culture`` lines `model.tmdl` needs.

    Without them the culture files are ignored on deserialization — the translations would
    sit in the repo, pass review, and simply never appear in Power BI.
    """
    return "\n".join(f"ref culture {tmdl_name(c)}" for c in cultures) + "\n"


def _readme(cultures: list[str], gaps_by_culture: dict[str, list[str]], total: int) -> str:
    lines = [
        "# Model translations (cultures)",
        "",
        "The semantic model keeps its English technical naming; client-facing captions come",
        "from culture files. A client picks a language with `LocaleIdentifier` on the",
        "connection string — that is preferable to setting the model `Language` property,",
        "which also affects processing and queries.",
        "",
        "## Wiring (easy to miss)",
        "",
        "`model.tmdl` must carry a `ref culture <name>` line per culture — see",
        "`model_refs.tmdl`. Without it the culture files are **ignored on deserialization**:",
        "the translations sit in the repo, pass review, and never show up in Power BI.",
        "",
        "## Coverage",
        "",
        "| Culture | Objects | Translated | Open |",
        "|---|---|---|---|",
    ]
    for culture in cultures:
        gaps = gaps_by_culture[culture]
        lines.append(f"| `{culture}` | {total} | {total - len(gaps)} | {len(gaps)} |")

    lines += [
        "",
        "## Why the gaps are not filled in",
        "",
        "`fact_orders` → *Aufträge* is a business-vocabulary decision. It belongs to the",
        "glossary and the domain owner, not to a generator: a machine-plausible caption that",
        "is subtly wrong is worse than an English one, because nobody reviews what already",
        "looks finished. Objects without a governed translation are therefore emitted without",
        "a caption — valid TMDL, and visibly untranslated in the client.",
        "",
        "To close a gap, add the translation to the governed catalog entry:",
        "",
        "```json",
        '{ "name": "fact_orders",',
        '  "translations": { "de-DE": { "caption": "…", "description": "…" } } }',
        "```",
        "",
        "and re-emit. `translation_gaps.md` lists what is still open per culture.",
    ]
    return "\n".join(lines) + "\n"


def emit_translations(bp: dict[str, Any], cultures: list[str] | None = None,
                      model_name: str | None = None,
                      governed_catalog: dict[str, Any] | None = None) -> dict[str, str]:
    """Return the translation artifact set (path → content)."""
    cultures = [c for c in (cultures or []) if str(c).strip()]
    if not cultures:
        return {}

    objects = _objects(bp, governed_catalog)
    if not objects:
        return {}
    total = sum(1 + len(t["children"]) for t in objects)

    out: dict[str, str] = {}
    gaps_by_culture: dict[str, list[str]] = {}

    for culture in cultures:
        out[f"translations/cultures/{culture}.tmdl"] = culture_tmdl(
            bp, culture, model_name=model_name, governed_catalog=governed_catalog
        )
        gaps_by_culture[culture] = translation_gaps(bp, culture, governed_catalog)

    out["translations/model_refs.tmdl"] = model_refs(cultures)

    gap_lines = ["# Open translations", ""]
    for culture in cultures:
        gaps = gaps_by_culture[culture]
        gap_lines.append(f"## `{culture}` — {len(gaps)} open")
        gap_lines.append("")
        gap_lines += ([f"- {g}" for g in gaps] if gaps
                      else ["Every object has a governed caption."])
        gap_lines.append("")
    out["translations/translation_gaps.md"] = "\n".join(gap_lines)

    out["translations/_TRANSLATIONS.md"] = _readme(cultures, gaps_by_culture, total)
    return out
