"""Guards for ``label_short`` — the English short name of every catalog KPI (13.11.2026).

Story reports put this name into their key sentence ("Cash Conversion Cycle (CCC) is at
40.4 days ..."). The KPI catalog is the only source of KPI naming (Golden Thread), so the
field is required in ``kpi_definition.schema.json``; this test checks coverage, the length
limit read from the schema (no second constant), uniqueness and the abbreviation form.
The number of checked KPIs is part of the assert: an empty catalog is not a pass.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
KPIS = REPO / "core/kpi_catalog/kpis"
SCHEMA = REPO / "tooling/generator/schemas/kpi_definition.schema.json"

# Lower bound of the catalog size on 13.11.2026 (145 KPIs). Guards against a run that
# silently checks nothing; raise it when the catalog grows, never lower it silently.
MIN_KPIS = 145


def _spec() -> dict:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert "label_short" in schema["required"], "label_short must be a required field"
    return schema["properties"]["label_short"]


def _entries() -> dict[str, dict]:
    order = yaml.safe_load((KPIS / "_index.yaml").read_text(encoding="utf-8"))["order"]
    return {kid: yaml.safe_load((KPIS / f"{kid}.yaml").read_text(encoding="utf-8")) for kid in order}


def missing_or_invalid(entries: dict[str, dict], spec: dict) -> dict[str, str]:
    """kpi_id -> reason for every entry whose label_short is absent or breaks the schema."""
    max_len, pattern = spec["maxLength"], re.compile(spec["pattern"])
    bad: dict[str, str] = {}
    for kid, e in entries.items():
        label = e.get("label_short")
        if not isinstance(label, str) or not label.strip():
            bad[kid] = "missing"
        elif len(label) > max_len:
            bad[kid] = f"{len(label)} > {max_len} chars: {label!r}"
        elif not pattern.match(label):
            bad[kid] = f"not plain English/ASCII: {label!r}"
    return bad


def test_every_kpi_has_label_short_within_limit():
    entries, spec = _entries(), _spec()
    assert len(entries) >= MIN_KPIS, f"only {len(entries)} KPIs read, expected >= {MIN_KPIS}"
    bad = missing_or_invalid(entries, spec)
    assert not bad, f"{len(bad)} of {len(entries)} KPIs without valid label_short: {bad}"


def test_label_short_is_unique():
    labels: dict[str, str] = {}
    dupes = []
    for kid, e in _entries().items():
        key = str(e.get("label_short", "")).casefold()
        if key in labels:
            dupes.append((labels[key], kid, e.get("label_short")))
        labels[key] = kid
    assert not dupes, f"label_short must identify one KPI: {dupes}"


def test_abbreviation_form():
    """'Full Name (ABBR)': the bracket comes last and holds an upper-case abbreviation."""
    bad = {}
    for kid, e in _entries().items():
        label = str(e.get("label_short", ""))
        if "(" in label:
            m = re.fullmatch(r"[^()]+ \(([A-Z][A-Z0-9&]{1,5})\)", label)
            if not m:
                bad[kid] = label
    assert not bad, f"abbreviation must be a trailing '(ABBR)': {bad}"


def test_detector_catches_a_missing_field():
    """Counter-check: the coverage check really goes red when one KPI loses the field."""
    entries = _entries()
    kid = next(iter(entries))
    broken = {k: dict(v) for k, v in entries.items()}
    del broken[kid]["label_short"]
    assert missing_or_invalid(broken, _spec()).get(kid) == "missing"
