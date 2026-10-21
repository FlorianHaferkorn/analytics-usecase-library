"""ID-Muster aus den JSON-Schemas — die eine Quelle fuer Use-Case-, KPI- und Action-Code-IDs.

Wer eine ID prueft, liest das Muster hier (und damit aus dem Schema), statt es abzuschreiben.
`tooling/validation/_index.yaml` (Taxonomie) fuehrt dieselben Strings; ein Test haelt sie gleich.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

SCHEMAS = Path(__file__).resolve().parents[1] / "generator" / "schemas"


@lru_cache(maxsize=None)
def _pattern(schema_file: str, field: str) -> str:
    data = json.loads((SCHEMAS / schema_file).read_text(encoding="utf-8"))
    return data["properties"][field]["pattern"]


def use_case_pattern() -> str:
    return _pattern("usecase_bracket.schema.json", "id")


def kpi_pattern() -> str:
    return _pattern("kpi_definition.schema.json", "kpi_id")


def action_code_pattern() -> str:
    return _pattern("action_code.schema.json", "id")


def use_case_re() -> re.Pattern[str]:
    return re.compile(use_case_pattern())


def kpi_re() -> re.Pattern[str]:
    return re.compile(kpi_pattern())


def action_code_re() -> re.Pattern[str]:
    return re.compile(action_code_pattern())
