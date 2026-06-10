"""Best-effort readers for the markdown-fenced KPI catalog and measure dictionaries.

The IR :class:`BracketCompiler` historically resolved KPIs by globbing for
``<kpi_id>.yaml`` files under ``core/kpi_catalog/`` -- files that do not exist
(the catalog lives in ``KPI_Catalog.md``). These readers parse the real sources
so the compiler can resolve a ``kpi_id`` to its display-name measure AND its DAX:

* ``KPI_Catalog.md``                    -> kpi_id -> display name (``kpi_key``)
* ``Measure_Dictionary_*.md`` (domains) -> display name -> DAX (per domain)

Resolution is by display name (``kpi_key``) because that is what report visuals
bind to. ``kpi_id_ref`` in the dictionaries is unreliable (blank for several
primary measures, and ``(XD)`` variants tag the same id), so it is not used.

All readers are best-effort: a missing or malformed file yields an empty mapping,
so the compiler degrades gracefully (and synthetic unit-test fixtures that use
per-KPI YAML files keep working via the compiler's existing fallback).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List

import yaml

_FENCE_RE = re.compile(r"```yaml\s*\n(.*?)```", re.DOTALL)
_KPI_CHUNK_RE = re.compile(r"(?m)^\s*-\s*kpi_id\s*:\s*([^\s#\r\n]+)")
_KPI_KEY_RE = re.compile(r'(?m)^\s*kpi_key\s*:\s*(?:"([^"]*)"|([^\r\n#]+))')


def load_kpi_catalog_names(catalog_md: Path) -> Dict[str, str]:
    """Return ``kpi_id -> display name`` (``kpi_key``) parsed from ``KPI_Catalog.md``.

    Uses chunk-based parsing (split by ``- kpi_id:``) to tolerate the large,
    occasionally non-strict YAML block -- mirroring the scaffold generator's
    ``config_loader`` so both paths resolve names identically.
    """
    if not catalog_md.is_file():
        return {}
    content = catalog_md.read_text(encoding="utf-8")
    fence = _FENCE_RE.search(content)
    block = fence.group(1) if fence else content

    names: Dict[str, str] = {}
    chunks = list(_KPI_CHUNK_RE.finditer(block))
    for i, mo in enumerate(chunks):
        kpi_id = mo.group(1).strip()
        end = chunks[i + 1].start() if i + 1 < len(chunks) else len(block)
        key_m = _KPI_KEY_RE.search(block[mo.start():end])
        if key_m:
            kpi_key = (key_m.group(1) or (key_m.group(2) or "").strip())
            if kpi_key:
                names[kpi_id] = kpi_key.strip()
    return names


def _strip_assignment(logical: str) -> str:
    """``'Gross Margin % = DIVIDE(...)'`` -> ``'DIVIDE(...)'`` (split on first ``=``)."""
    return logical.split("=", 1)[1].strip() if "=" in logical else logical.strip()


def load_measure_dictionary(domains_dir: Path) -> Dict[str, List[dict]]:
    """Parse every ``Measure_Dictionary_*.md`` under ``domains_dir``.

    Returns ``display name -> [ {"name", "dax", "display_folder", "domain"} ]``.
    Multiple domains may define the same measure name (e.g. ``Gross Margin %`` and
    ``Gross Margin % (XD)``); the compiler picks the entry whose ``domain`` matches
    the use case's domain.
    """
    by_name: Dict[str, List[dict]] = {}
    if not domains_dir.is_dir():
        return by_name

    for md in domains_dir.rglob("Measure_Dictionary_*.md"):
        domain = md.parent.name
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
            if not isinstance(m, dict):
                continue
            name = m.get("measure_name")
            if not name:
                continue
            logical = ((m.get("expression") or {}).get("logical")) or ""
            by_name.setdefault(name, []).append({
                "name": name,
                "dax": _strip_assignment(logical) if logical else "BLANK()",
                "display_folder": m.get("display_folder", ""),
                "domain": domain,
            })
    return by_name
