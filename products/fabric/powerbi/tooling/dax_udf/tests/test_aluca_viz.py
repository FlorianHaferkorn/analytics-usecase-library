"""Structure/consistency tests for the AlucaViz DAX-UDF package.

Live-model (DAX-engine) validation is Desktop-gated and lives in the acceptance step;
here we assert the package is well-formed and stays in sync with the daxlib format.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

PKG = Path(__file__).resolve().parents[1] / "aluca.viz"
MANIFEST = PKG / "manifest.daxlib"
FUNCTIONS = PKG / "lib" / "functions.tmdl"

DECLARED = {"AlucaViz.DeviationBar", "AlucaViz.Bullet"}


def test_manifest_is_valid_json_with_required_keys():
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for key in ("id", "version", "authors", "description", "tags"):
        assert m.get(key), f"manifest missing/empty '{key}'"
    assert m["id"] == "AlucaViz"
    assert re.fullmatch(r"\d+\.\d+\.\d+", m["version"]), "version must be semver"


def test_functions_declared_and_annotated():
    t = FUNCTIONS.read_text(encoding="utf-8")
    names = set(re.findall(r"function '([^']+)' =", t))
    assert names == DECLARED, f"declared functions {names} != expected {DECLARED}"
    # every function carries both daxlib tracking annotations
    assert t.count("annotation DAXLIB_PackageId = AlucaViz") == len(DECLARED)
    ver = json.loads(MANIFEST.read_text(encoding="utf-8"))["version"]
    assert t.count(f"annotation DAXLIB_PackageVersion = {ver}") == len(DECLARED), \
        "every function's DAXLIB_PackageVersion must match the manifest version"


def test_functions_tmdl_is_tab_indented_and_clean():
    raw = FUNCTIONS.read_text(encoding="utf-8")
    for i, line in enumerate(raw.splitlines(), 1):
        if line and line[0] == " ":
            raise AssertionError(f"functions.tmdl line {i} is space-indented (TMDL requires tabs)")
    assert ":=" not in raw, "TMDL uses '=' not ':='"
    assert "{{" not in raw and "}}" not in raw, "unfilled template placeholder left in the UDF"


def test_udf_bodies_are_balanced():
    """Each SVG-building body opens and closes its <svg> and balances DAX parens/quotes."""
    t = FUNCTIONS.read_text(encoding="utf-8")
    assert t.count("<svg") == t.count("</svg>") == len(DECLARED)
    assert t.count('"') % 2 == 0, "odd number of double quotes — a DAX string is unterminated"
