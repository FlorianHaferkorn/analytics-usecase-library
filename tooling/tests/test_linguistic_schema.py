"""Tests for products/fabric/powerbi/tooling/linguistic_schema.py (Epic A2).

Covers the acceptance criteria for the linguistic-schema projection:
  - deterministic / idempotent build (same contract -> identical output)
  - round-trip: render -> parse recovers the LSDL document
  - Aurora Commercial synonyms are bound (Region, Channel, Net Sales Amount)
  - rendered TMDL is style-clean (tab indent, no ':=', no 'description:')
  - the committed Commercial culture file matches the generator (drift guard)
  - model.tmdl references the culture
  - columns without synonyms produce no entity
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tooling.generator_core.ai_description import (
    ColumnDescription,
    TableDescription,
    build_table_descriptions,
)
from products.fabric.powerbi.tooling.linguistic_schema import (
    DEFAULT_CULTURE,
    build_linguistic_schema,
    emit_for_domain,
    parse_culture_tmdl,
    render_culture_tmdl,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CONTRACT = _REPO_ROOT / "core" / "data_contracts" / "domains" / "commercial_sales.yaml"
_COMMERCIAL_DEF = (
    _REPO_ROOT
    / "products" / "fabric" / "powerbi" / "dist"
    / "Commercial.SemanticModel" / "definition"
)


def _commercial_tables() -> list[TableDescription]:
    return build_table_descriptions(_CONTRACT)


def _terms(entity: dict) -> list[str]:
    """Flatten an LSDL entity's Terms to the list of term strings."""
    return [next(iter(term)) for term in entity["Terms"]]


# ---------------------------------------------------------------------------
# Determinism / idempotency
# ---------------------------------------------------------------------------

def test_build_is_deterministic():
    tables = _commercial_tables()
    assert build_linguistic_schema(tables) == build_linguistic_schema(tables)


def test_render_is_idempotent():
    schema = build_linguistic_schema(_commercial_tables())
    assert render_culture_tmdl(schema) == render_culture_tmdl(schema)


# ---------------------------------------------------------------------------
# Round-trip (risk mitigation: validate the format before wiring breadth)
# ---------------------------------------------------------------------------

def test_render_parse_roundtrip():
    schema = build_linguistic_schema(_commercial_tables())
    recovered = parse_culture_tmdl(render_culture_tmdl(schema))
    assert recovered == schema


def test_lsdl_envelope():
    schema = build_linguistic_schema(_commercial_tables())
    assert schema["Version"] == "1.0.0"
    assert schema["Language"] == DEFAULT_CULTURE
    assert isinstance(schema["Entities"], dict)


# ---------------------------------------------------------------------------
# Aurora Commercial proof — bindings + curated synonyms
# ---------------------------------------------------------------------------

def test_commercial_region_channel_and_net_sales_bound():
    entities = build_linguistic_schema(_commercial_tables())["Entities"]

    region = entities["dim_org.region"]
    assert region["Definition"]["Binding"] == {
        "ConceptualEntity": "dim_org",
        "ConceptualProperty": "Region",
    }
    assert _terms(region) == ["Region", "Sales Region", "Geo"]

    channel = entities["dim_org.channel"]
    assert channel["Definition"]["Binding"]["ConceptualProperty"] == "Channel"
    assert _terms(channel) == ["Channel", "Sales Channel", "Route to Market"]

    net_sales = entities["fact_sales.net_sales_amount"]
    assert net_sales["Definition"]["Binding"] == {
        "ConceptualEntity": "fact_sales",
        "ConceptualProperty": "Net Sales Amount",
    }
    assert _terms(net_sales) == ["Net Sales Amount", "Revenue", "Net Revenue", "Umsatz"]


def test_authored_synonyms_are_tagged():
    net_sales = build_linguistic_schema(_commercial_tables())["Entities"][
        "fact_sales.net_sales_amount"
    ]
    # first term = the object's own name (Generated); the rest = Authored synonyms
    assert net_sales["Terms"][0]["Net Sales Amount"]["State"] == "Generated"
    assert net_sales["Terms"][1]["Revenue"] == {
        "Type": "Noun",
        "State": "Authored",
        "Source": "User",
    }


def test_columns_without_synonyms_are_excluded():
    tables = [
        TableDescription(
            name="dim_test",
            columns=[
                ColumnDescription(name="NoSyn"),
                ColumnDescription(name="WithSyn", synonyms=["Alias"]),
            ],
        )
    ]
    entities = build_linguistic_schema(tables)["Entities"]
    assert list(entities) == ["dim_test.withsyn"]


# ---------------------------------------------------------------------------
# TMDL style (must satisfy the PostToolUse hook)
# ---------------------------------------------------------------------------

def test_rendered_tmdl_is_style_clean():
    text = render_culture_tmdl(build_linguistic_schema(_commercial_tables()))
    for n, line in enumerate(text.split("\n"), 1):
        assert not line.startswith("  "), f"leading spaces on line {n}: {line!r}"
        assert ":=" not in line, f"':=' on line {n}"
        assert not re.match(r"^\s*description:", line), f"'description:' on line {n}"
    assert text.startswith(
        f"culture {DEFAULT_CULTURE}\n\tlinguisticMetadata\n\t\tcontentType: Json\n\t\tcontent =\n"
    )


# ---------------------------------------------------------------------------
# Drift guard — committed golden build matches the generator
# ---------------------------------------------------------------------------

def test_committed_commercial_culture_matches_generator():
    committed = (_COMMERCIAL_DEF / "cultures" / "en-US.tmdl").read_text(encoding="utf-8")
    regenerated = render_culture_tmdl(build_linguistic_schema(_commercial_tables()))
    assert committed == regenerated, (
        "Committed cultures/en-US.tmdl is out of sync with the data contract. "
        "Re-run: python3 -m products.fabric.powerbi.tooling.linguistic_schema --domain Commercial"
    )


def test_committed_model_tmdl_references_culture():
    model = (_COMMERCIAL_DEF / "model.tmdl").read_text(encoding="utf-8")
    assert f"ref culture {DEFAULT_CULTURE}" in model


# ---------------------------------------------------------------------------
# Emitter is idempotent end-to-end (writes the same bytes, no duplicate ref)
# ---------------------------------------------------------------------------

def test_emit_for_domain_idempotent(tmp_path):
    def_dir = tmp_path / "Commercial.SemanticModel" / "definition"
    def_dir.mkdir(parents=True)
    (def_dir / "model.tmdl").write_text(
        "model Model\n\tculture: en-US\nref table fact_sales\n", encoding="utf-8"
    )
    contracts_dir = _CONTRACT.parent

    out1, n1, added1 = emit_for_domain("Commercial", tmp_path, contracts_dir)
    first = out1.read_text(encoding="utf-8")
    model_after_first = (def_dir / "model.tmdl").read_text(encoding="utf-8")

    out2, n2, added2 = emit_for_domain("Commercial", tmp_path, contracts_dir)
    second = out2.read_text(encoding="utf-8")
    model_after_second = (def_dir / "model.tmdl").read_text(encoding="utf-8")

    assert first == second
    # 8 synonym-bearing commercial entities after the dim_promo additions (was 3)
    assert (n1, n2) == (8, 8)
    assert added1 is True and added2 is False           # ref added once, not duplicated
    assert model_after_first == model_after_second
    assert model_after_first.count("ref culture en-US") == 1
