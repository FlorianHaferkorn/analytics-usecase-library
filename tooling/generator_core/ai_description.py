"""Standard AI-description template: pull governed metadata from the KPI catalog,
the domain measure dictionaries and the data contracts, and project it into the
two AI-facing surfaces -- the semantic layer (TMDL ``///`` doc block) and the
visualization tool (a compact tooltip string).

One governed source, multiple rendered projections (no hand-written prose, no
drift). See ``AI_Description_Standard.md`` for the field contract and depth bar.

All loaders are best-effort: a missing field is omitted from the render, never
guessed.
"""

from __future__ import annotations

import functools
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

_FENCE_RE = re.compile(r"```yaml\s*\n(.*?)```", re.DOTALL)
_KPI_SPLIT_RE = re.compile(r"(?m)^(?=- kpi_id:)")
_GRAIN_RE = re.compile(r"Grain:\s*([^.\n]+)", re.IGNORECASE)
_UNIT_RE = re.compile(r"Unit:\s*([^.\n]+)", re.IGNORECASE)


# ──────────────────────────────────────────────────────────────────────────────
# Source loaders (best-effort)
# ──────────────────────────────────────────────────────────────────────────────


@functools.lru_cache(maxsize=8)
def load_kpi_catalog(catalog_md: Path) -> Dict[str, dict]:
    """Return ``kpi_id -> full kpi dict`` parsed from ``KPI_Catalog.md``.

    Parses each ``- kpi_id:`` chunk independently so one malformed entry never
    breaks the rest.
    """
    if not catalog_md.is_file():
        return {}
    fence = _FENCE_RE.search(catalog_md.read_text(encoding="utf-8"))
    if not fence:
        return {}
    out: Dict[str, dict] = {}
    for chunk in _KPI_SPLIT_RE.split(fence.group(1)):
        chunk = chunk.strip()
        if not chunk.startswith("- kpi_id:"):
            continue
        try:
            parsed = yaml.safe_load(chunk)
        except yaml.YAMLError:
            continue
        if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
            entry = parsed[0]
            kid = entry.get("kpi_id")
            if kid:
                out[str(kid)] = entry
    return out


@functools.lru_cache(maxsize=8)
def load_measure_dictionary(domains_dir: Path) -> Dict[str, List[dict]]:
    """Return ``measure_name -> [measure dict, ...]`` across all domain dictionaries.

    Each measure dict is annotated with its ``_domain`` (the folder name) so the
    caller can prefer the use case's own domain.
    """
    by_name: Dict[str, List[dict]] = {}
    if not domains_dir.is_dir():
        return by_name
    for md in domains_dir.rglob("Measure_Dictionary_*.md"):
        fence = _FENCE_RE.search(md.read_text(encoding="utf-8"))
        if not fence:
            continue
        try:
            measures = yaml.safe_load(fence.group(1)) or []
        except yaml.YAMLError:
            continue
        if not isinstance(measures, list):
            continue
        for m in measures:
            if isinstance(m, dict) and m.get("measure_name"):
                m = {**m, "_domain": md.parent.name}
                by_name.setdefault(m["measure_name"], []).append(m)
    return by_name


def load_fact_grains(contracts_dir: Path) -> Dict[str, str]:
    """Return ``fact_table -> grain`` across all domain data contracts (best-effort)."""
    grains: Dict[str, str] = {}
    if not contracts_dir.is_dir():
        return grains
    for yml in contracts_dir.rglob("*.yaml"):
        try:
            doc = yaml.safe_load(yml.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        tables = doc.get("tables") or doc.get("facts") or []
        if isinstance(tables, list):
            for t in tables:
                if isinstance(t, dict) and t.get("name") and t.get("grain"):
                    grains.setdefault(str(t["name"]), str(t["grain"]))
    return grains


# ──────────────────────────────────────────────────────────────────────────────
# Canonical description + renderers
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class AIDescription:
    kpi_id: str
    name: str
    definition: str = ""
    formula: str = ""
    grain: str = ""
    unit: str = ""
    good_is: str = ""          # optional KPI field: "higher" | "lower"
    impact_dimension: str = ""
    drivers: List[Tuple[str, str]] = field(default_factory=list)  # (name, direction)
    owner: str = ""
    status: str = ""
    action_codes: List[str] = field(default_factory=list)
    synonyms: List[str] = field(default_factory=list)   # optional KPI field
    example_question: str = ""                           # optional KPI field
    domain: str = ""

    def render_semantic_layer(self) -> str:
        """Render the TMDL ``///`` doc block (one line per populated facet)."""
        lines: List[str] = []
        if self.definition:
            lines.append(f"/// {self.definition}")
        if self.formula:
            lines.append(f"/// Formula: {self.formula}")
        meta = []
        if self.grain:
            meta.append(f"Grain: {self.grain}")
        if self.unit:
            meta.append(f"Unit: {self.unit}")
        if self.good_is:
            meta.append(f"Good: {self.good_is}_is_better")
        if meta:
            lines.append("/// " + " · ".join(meta))
        if self.drivers:
            driver_str = ", ".join(f"{n} ({d})" for n, d in self.drivers[:3])
            lines.append(f"/// Drivers: {driver_str}")
        gov = []
        if self.owner:
            gov.append(f"Owner: {self.owner}")
        if self.status:
            gov.append(f"Status: {self.status}")
        if self.action_codes:
            gov.append(f"Actions: {', '.join(self.action_codes)}")
        if gov:
            lines.append("/// " + " · ".join(gov))
        return "\n".join(lines)

    def render_viz(self) -> str:
        """Render a compact, tool-agnostic tooltip string for a visualization tool."""
        parts: List[str] = []
        if self.definition:
            parts.append(self.definition.rstrip("."))
        qualifiers = []
        if self.unit:
            qualifiers.append(self.unit)
        if self.good_is:
            qualifiers.append(f"{self.good_is} is better")
        if qualifiers:
            parts[-1] = f"{parts[-1] or self.name} ({', '.join(qualifiers)})"
        if self.drivers:
            parts.append("Top drivers: " + ", ".join(n for n, _ in self.drivers[:3]))
        return ". ".join(p for p in parts if p) + ("." if parts else "")


def _extract(notes: str, pattern: re.Pattern) -> str:
    m = pattern.search(notes or "")
    return m.group(1).strip() if m else ""


def _strip_assignment(logical: str) -> str:
    return logical.split("=", 1)[1].strip() if "=" in logical else logical.strip()


def build_description(kpi_id: str, repo_root: Path) -> Optional[AIDescription]:
    """Assemble the standard AI description for ``kpi_id`` from the governed sources."""
    repo_root = Path(repo_root)
    catalog = load_kpi_catalog(repo_root / "core" / "kpi_catalog" / "KPI_Catalog.md")
    kpi = catalog.get(kpi_id)
    if not kpi:
        return None

    name = kpi.get("kpi_key", kpi_id)
    domains = kpi.get("domain_tag") or []
    domain = domains[0] if domains else ""

    by_name = load_measure_dictionary(repo_root / "core" / "semantic_models" / "domains")
    entries = by_name.get(name, [])
    measure = next((e for e in entries if e.get("_domain") == domain), entries[0] if entries else {})

    doc = (measure.get("documentation") or {}) if measure else {}
    notes = doc.get("notes", "")
    logical = ((measure.get("expression") or {}).get("logical")) or "" if measure else ""
    gov = (measure.get("governance") or {}) if measure else {}

    # Drivers from causal_links (resolve influencing ids to display names).
    drivers: List[Tuple[str, str]] = []
    for link in ((kpi.get("causal_links") or {}).get("links") or []):
        inf = link.get("influencing_kpi_id", "")
        inf_name = catalog.get(inf, {}).get("kpi_key", inf)
        direction = (link.get("effect") or {}).get("direction", "")
        if inf_name:
            drivers.append((inf_name, direction))

    return AIDescription(
        kpi_id=kpi_id,
        name=name,
        definition=doc.get("description", ""),
        formula=_strip_assignment(logical),
        grain=_extract(notes, _GRAIN_RE),
        unit=_extract(notes, _UNIT_RE),
        good_is=str(kpi.get("good_is", "")).strip(),
        impact_dimension=kpi.get("impact_dimension", ""),
        drivers=drivers,
        owner=gov.get("owner", ""),
        status=gov.get("status", ""),
        action_codes=list(kpi.get("action_code_ref") or []),
        synonyms=list(kpi.get("synonyms") or []),
        example_question=str(kpi.get("example_question", "")).strip(),
        domain=domain,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Tables & columns (from the data contracts)
# ──────────────────────────────────────────────────────────────────────────────

_CURRENCY_TYPES = {"currency", "money"}


@dataclass
class ColumnDescription:
    name: str
    data_type: str = ""
    role: str = ""           # key | foreign_key | measure | attribute
    unit: str = ""
    ref: str = ""            # FK target table
    nullable: bool = False
    description: str = ""
    allowed_values: List[str] = field(default_factory=list)   # the gap that most helps NL->column
    synonyms: List[str] = field(default_factory=list)

    def render_semantic_layer(self) -> str:
        """Render the column's TMDL ``///`` doc line."""
        meta = []
        if self.data_type:
            meta.append(f"Type: {self.data_type}")
        if self.unit:
            meta.append(f"Unit: {self.unit}")
        if self.role:
            meta.append(f"Role: {self.role}")
        if self.ref:
            meta.append(f"FK->{self.ref}")
        if self.allowed_values:
            meta.append("Values: " + ", ".join(str(v) for v in self.allowed_values))
        if self.synonyms:
            meta.append("Synonyms: " + ", ".join(self.synonyms))
        head = self.description.rstrip(".") if self.description else self.name
        suffix = (" " + " · ".join(meta)) if meta else ""
        return f"/// {head}.{suffix}"


@dataclass
class TableDescription:
    name: str
    kind: str = ""           # fact | dimension
    description: str = ""
    purpose: str = ""
    grain: str = ""
    columns: List[ColumnDescription] = field(default_factory=list)

    def render_semantic_layer(self) -> str:
        bits = [b.rstrip(".") for b in (self.description, self.purpose) if b]
        head = ". ".join(bits) or self.name
        meta = []
        if self.grain:
            meta.append(f"Grain: {self.grain}")
        if self.kind:
            meta.append(f"Type: {self.kind}")
        suffix = (" " + " · ".join(meta)) if meta else ""
        return f"/// {head}.{suffix}"

    def render_viz(self) -> str:
        return (self.description.rstrip(".") if self.description else self.name) + "."


def _column_role(col: dict) -> str:
    if col.get("role") == "key" or str(col.get("name", "")).endswith("Key"):
        return "foreign_key" if col.get("ref") else "key"
    if col.get("agg"):
        return "measure"
    return "attribute"


def _column_unit(col: dict) -> str:
    if col.get("unit"):
        return str(col["unit"])
    return "EUR" if col.get("type") in _CURRENCY_TYPES else ""


def _table_kind(table: dict) -> str:
    name = str(table.get("name", ""))
    if name.startswith("fact"):
        return "fact"
    if name.startswith("dim"):
        return "dimension"
    return "fact" if table.get("grain") else "dimension"


def build_table_descriptions(contract_path: Path) -> List[TableDescription]:
    """Build table + column descriptions from one data-contract YAML (best-effort)."""
    contract_path = Path(contract_path)
    if not contract_path.is_file():
        return []
    try:
        doc = yaml.safe_load(contract_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return []
    out: List[TableDescription] = []
    tables = []
    for key in ("fact", "dimension", "tables", "facts"):
        val = doc.get(key)
        if isinstance(val, list):
            tables.extend(val)
    for t in tables:
        if not isinstance(t, dict) or not t.get("name"):
            continue
        cols: List[ColumnDescription] = []
        for c in (t.get("columns") or []):
            if not isinstance(c, dict) or not c.get("name"):
                continue
            cols.append(ColumnDescription(
                name=str(c["name"]),
                data_type=str(c.get("type", "")),
                role=_column_role(c),
                unit=_column_unit(c),
                ref=str(c.get("ref", "")),
                nullable=bool(c.get("nullable", False)),
                description=str(c.get("description", "")),
                allowed_values=list(c.get("allowed_values") or []),
                synonyms=list(c.get("synonyms") or []),
            ))
        out.append(TableDescription(
            name=str(t["name"]),
            kind=_table_kind(t),
            description=str(t.get("description", "")),
            purpose=str(t.get("purpose", "")),
            grain=str(t.get("grain", "")),
            columns=cols,
        ))
    return out
