"""test_gold_generator_product_count.py — der Generator muss so viele Produkte liefern,
wie die Konfiguration bestellt.

Gemessener Anlass (11.08.2026): `_generate_dim_product()` verteilte je Kategorie
`product_count // len(subcategories)` Produkte. Solange das Firmenprofil nur „Basic" und
„Premium" kannte, ging die Division auf. Mit echten Subkategorien ergaben 1000
Consumer-Electronics-Produkte auf 6 Subkategorien nur 996 — `dim_product` endete bei
ProductKey 4996, und `fact_plan_sales` referenzierte 4999 ins Leere (ORPHAN-FK).

Der Verlust war still: niemand vergleicht 4996 mit der Summe der `product_count`. Genau
diese Summe haelt dieser Test fest. Er prueft ausserdem, dass das Modul ueberhaupt
importierbar ist — der Pfad zu den Gold-Utilities zeigte auf `core/showcases/…` statt auf
`<repo>/showcases/…`, das Skript brach also bei jedem Aufruf schon beim Import ab. Beide
Defekte kosteten nichts, solange niemand regenerierte; beide waeren beim naechsten Lauf
wieder aufgeschlagen.

Die fachliche Deckung Fakt-FK → Dimension-PK prueft `check_data_model.py` (ORPHAN-FK) und
wird hier nicht nachgebaut — dieser Test schaut auf den Erzeuger, jener auf das Ergebnis.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")
pytest.importorskip("pandas")
pytest.importorskip("numpy")

REPO = Path(__file__).resolve().parents[2]
GENERATOR = REPO / "core" / "data_contracts" / "sources" / "synthetic" / "generate_gold_layer_contract_v2.py"
CONFIG = REPO / "core" / "data_contracts" / "sources" / "synthetic" / "synthetic_config_core_v1.yaml"


def _generator_module():
    """Importiert das Generator-Skript ueber seinen Pfad — es ist kein Paketmodul."""
    spec = importlib.util.spec_from_file_location("_gold_generator_under_test", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_the_module_imports_at_all():
    """Der Utility-Pfad zeigte auf `core/showcases/…` und existiert dort nicht."""
    assert _generator_module() is not None


def test_dim_product_holds_every_configured_product():
    module = _generator_module()
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    bestellt = sum(c["product_count"] for c in config["products"]["categories"])

    generator = module.GoldLayerGenerator(str(CONFIG), "/tmp/does-not-matter", "aurora")
    df = generator._generate_dim_product()

    assert len(df) == bestellt, (
        f"{bestellt - len(df)} Produkte verschluckt — die Ganzzahldivision ueber die "
        f"Subkategorien verliert den Rest; genau so entstand die Waise ProductKey 4999"
    )
    assert df["ProductKey"].is_unique
    assert df["ProductKey"].tolist() == list(range(1, bestellt + 1)), (
        "die Schluessel muessen luecken- und sprungfrei bei 1 beginnen — Fakten "
        "referenzieren sie direkt"
    )
