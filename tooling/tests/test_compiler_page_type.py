"""IR compiler: unknown page_type/template_variant raises, like the template loader."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from tooling.generator_core.ir.compiler import (
    UnknownPageTypeError,
    _resolve_page_type,
)
from tooling.generator_core.ir.specs import PageType

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("T1", PageType.T1_STRATEGIC_OVERVIEW),
        ("T2_DriverBridge", PageType.T2_TACTICAL_VARIANCE),
        ("T3_Operational_Monitoring", PageType.T3_OPERATIONAL_MONITORING),
        ("T4_ActionDecision", PageType.T4_PRESCRIPTIVE_RECOMMENDATION),
    ],
)
def test_known_forms_resolve(raw: str, expected: PageType) -> None:
    assert _resolve_page_type(raw) is expected


@pytest.mark.parametrize("raw", ["T5_Foo", "X1", "T2x", "Strategic", "t", ""])
def test_unknown_form_raises(raw: str) -> None:
    with pytest.raises(UnknownPageTypeError):
        _resolve_page_type(raw)


def test_every_bracket_value_resolves() -> None:
    """Der strengere Resolver bricht keinen Bestand: alle Bracket-Werte sind gueltig."""
    seen = 0
    for path in sorted((ROOT / "core" / "usecases").rglob("UseCase_Bracket.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        page1 = (data.get("ux_layout_rules") or {}).get("page_1_summary") or {}
        raw = page1.get("template_variant") or page1.get("page_type")
        if raw:
            _resolve_page_type(raw)
            seen += 1
    assert seen >= 20, f"nur {seen} Brackets mit page_type gelesen"
