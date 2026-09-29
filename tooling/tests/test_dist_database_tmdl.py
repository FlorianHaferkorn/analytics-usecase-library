"""Jedes Domain-Modell in dist traegt eine database.tmdl.

Experience und SupplyChain hatten keine: `orchestrate_full_model.ps1` schrieb je
Domain nur `definition.pbism`, nie `database.tmdl`. TMDL-Ordnerlader (Power BI
modeling MCP `ConnectFolder`, `TmdlSerializer`) lehnen ein Modell ohne sie ab;
Commercial/Finance/Operations luden nur, weil ihre Datei aus anderen Quellen
stammte (pbip-Adapter bzw. `table_ops.ps1 -Operation WriteModelFiles`).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / "products" / "fabric" / "powerbi" / "dist"
ORCHESTRATOR = ROOT / "products" / "fabric" / "powerbi" / "orchestrator" / "orchestrate_full_model.ps1"
TEMPLATE = (ROOT / "core" / "strategy_operating_model" / "operating_model" / "reference"
            / "tmdl_base_templates" / "database.tmdl.template")

MODELLE = sorted(p for p in DIST.glob("*.SemanticModel") if (p / "definition" / "model.tmdl").is_file())


def test_dist_has_domain_models():
    assert len(MODELLE) >= 5, [m.name for m in MODELLE]


@pytest.mark.parametrize("modell", MODELLE, ids=lambda p: p.name)
def test_database_tmdl_present_and_well_formed(modell):
    datei = modell / "definition" / "database.tmdl"
    assert datei.is_file(), f"{modell.name}: definition/database.tmdl fehlt"
    text = datei.read_text(encoding="utf-8")
    name = modell.name.removesuffix(".SemanticModel")
    kopf = text.splitlines()[0]
    assert re.fullmatch(rf"database (?:{re.escape(name)}|'{re.escape(name)}')", kopf), kopf
    assert re.search(r"^\tcompatibilityLevel: (\d+)$", text, re.M), "compatibilityLevel fehlt oder nicht mit Tab"
    assert int(re.search(r"compatibilityLevel: (\d+)", text).group(1)) >= 1702
    assert "\r" not in text and ":=" not in text


def test_orchestrator_seeds_database_tmdl_from_template_only_if_missing():
    quelle = ORCHESTRATOR.read_text(encoding="utf-8")
    assert "database.tmdl.template" in quelle, "Orchestrator schreibt keine database.tmdl aus der Vorlage"
    assert re.search(r"if \(-not \(Test-Path \$dbPath\)\)", quelle), "database.tmdl wuerde ueberschrieben"
    assert "{{MODEL_NAME}}" in TEMPLATE.read_text(encoding="utf-8")
