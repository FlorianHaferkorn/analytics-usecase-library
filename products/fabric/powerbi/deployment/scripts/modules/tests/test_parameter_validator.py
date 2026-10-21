"""semantic_model_binding: current fabric-cicd format (default/models) and the deprecated list.

fabric-cicd >= 1.2.0 reads semantic_model_binding as an object with ``default`` and/or
``models``; the former list of {connection_id, semantic_model_name} still works but logs a
deprecation warning (fabric-cicd 1.4.0, ``_items/_semanticmodel.py``). The validator, the
JSON schema, the template and the generator must agree on that.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from modules.parameter_validator import (
    validate_parameter_file,
    validate_semantic_model_binding,
)

_PARAMS = Path(__file__).resolve().parents[3] / "resources" / "parameters"
_TEMPLATE = _PARAMS / "parameter.yml.template"
_SCHEMA = _PARAMS / "parameter.schema.json"
_GUID = "0f3c2a1e-5b7d-4c9a-8e21-6d4b3a2f1c0e"


def _write(tmp_path: Path, data: dict) -> str:
    path = tmp_path / "parameter.yml"
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return str(path)


def test_template_validates_against_schema_without_warnings() -> None:
    ok, errors, details = validate_parameter_file(str(_TEMPLATE), schema_path=str(_SCHEMA))
    assert ok, errors
    assert "warnings" not in details


def test_template_uses_current_binding_format() -> None:
    binding = yaml.safe_load(_TEMPLATE.read_text(encoding="utf-8"))["semantic_model_binding"]
    assert isinstance(binding, dict)
    assert set(binding) <= {"default", "models"}


@pytest.mark.parametrize(
    "binding",
    [
        {"default": {"connection_id": {"prd": _GUID}}},
        {"models": [{"semantic_model_name": "DM_Core", "connection_id": {"_ALL_": _GUID}}]},
        {"models": [{"semantic_model_name": ["A", "B"], "connection_id": {"prd": [_GUID, _GUID]}}]},
    ],
)
def test_current_format_is_valid(tmp_path: Path, binding: dict) -> None:
    ok, errors, details = validate_parameter_file(
        _write(tmp_path, {"semantic_model_binding": binding}), schema_path=str(_SCHEMA)
    )
    assert ok, errors
    assert "warnings" not in details


def test_deprecated_list_is_accepted_with_warning(tmp_path: Path) -> None:
    legacy = {"semantic_model_binding": [{"connection_id": _GUID, "semantic_model_name": "DM_Core"}]}
    ok, errors, details = validate_parameter_file(_write(tmp_path, legacy), schema_path=str(_SCHEMA))
    assert ok, errors
    assert any("deprecated" in w for w in details["warnings"])


@pytest.mark.parametrize(
    ("binding", "fragment"),
    [
        ({}, "needs 'default' and/or 'models'"),
        ({"model": []}, "unknown keys"),
        ({"default": {}}, "default: missing connection_id"),
        ({"models": [{"connection_id": {"prd": _GUID}}]}, "missing semantic_model_name"),
        ({"models": [{"semantic_model_name": "X"}]}, "missing connection_id"),
        ({"models": [{"semantic_model_name": "X", "connection_id": _GUID}]}, "must map environment keys"),
        ({"models": [{"semantic_model_name": "X", "connection_id": {"prd": "abc-123"}}]}, "GUID or placeholder"),
    ],
)
def test_invalid_current_format_is_reported(binding: dict, fragment: str) -> None:
    errors, _ = validate_semantic_model_binding(binding)
    assert any(fragment in e for e in errors), errors


def test_generator_emits_current_format() -> None:
    from utils_build_parameter_file import generate_parameter_file

    configs = {
        "dev": {"layers": {"DM": {"items": {"SemanticModel": [{"item_name": "DM_Core"}]}}}},
        "tst": {},
        "prd": {},
    }
    data = generate_parameter_file(configs)
    binding = data["semantic_model_binding"]
    assert binding["models"][0]["semantic_model_name"] == "DM_Core"
    assert set(binding["models"][0]["connection_id"]) == {"tst", "prd"}
    errors, warnings = validate_semantic_model_binding(binding)
    assert not errors and not warnings
