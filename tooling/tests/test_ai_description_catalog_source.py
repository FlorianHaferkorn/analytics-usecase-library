"""Owner und Grain der AI-Beschreibung kommen aus dem KPI-Katalog.

Quelle: governance.business_owner und business.grain_scope je KPI-Datei. Das Measure
Dictionary springt nur ein, wo der Katalog leer oder ein Platzhalter (TBD) ist.
Dazu OTIF (KPI-SCM-007): gemessen wird der gemeinsame Anteil (OTIF Flag), nicht das
Produkt der Komponenten -- keine Messabhaengigkeit, keine "multiplicative"-Erzaehlung.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from tooling.generator_core.ai_description import _catalog_value, build_description

ROOT = Path(__file__).resolve().parents[2]
KPIS = ROOT / "core" / "kpi_catalog" / "kpis"
SCM002 = ROOT / "core" / "usecases" / "core" / "SCM-002_Supply_Reliability_OTIF"


@pytest.mark.parametrize("value", ["", None, "TBD", " tbd ", "n/a", "-"])
def test_placeholder_is_empty(value: object) -> None:
    assert _catalog_value(value) == ""


def test_all_catalog_kpis_use_catalog_owner_and_grain() -> None:
    n = 0
    for p in sorted(KPIS.glob("KPI-*.yaml")):
        kpi = yaml.safe_load(p.read_text(encoding="utf-8"))
        owner = _catalog_value((kpi.get("governance") or {}).get("business_owner"))
        grain = _catalog_value((kpi.get("business") or {}).get("grain_scope")).rstrip(".")
        d = build_description(kpi["kpi_id"], ROOT)
        if d is None:
            continue
        n += 1
        if owner:
            assert d.owner == owner, p.name
        if grain:
            assert d.grain == grain, p.name
    assert n >= 100, f"nur {n} KPIs geprueft"


def test_otif_has_no_measure_dependency() -> None:
    kpi = yaml.safe_load((KPIS / "KPI-SCM-007.yaml").read_text(encoding="utf-8"))
    tech = kpi["technical"]
    assert tech["calculation"]["column"] == "OTIF Flag"
    assert tech["depends_on_measures"] == []


@pytest.mark.parametrize("path", [
    SCM002 / "Business_Factsheet.md",
    SCM002 / "Domain_Evidence_Pack.yaml",
    ROOT / "docs" / "process" / "evidence-to-model-uplift-scope.md",
])
def test_otif_narrative_is_joint_share(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert "multiplicative" not in text.lower(), path.name
    for bad in ("OTIF = On-Time x In-Full", "OTIF = On-Time × In-Full",
                "OTIF = On-Time rate x In-Full rate"):
        assert bad not in text, (path.name, bad)
