"""
Validate Use Case Bracket (and UseCaseDraft) against usecase_bracket.schema.json.
Used on YAML import and before Export (Pre-Export-Gate).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Schema path relative to this file
_SCHEMA_PATH = Path(__file__).resolve().parent
_REPO_ROOT = _SCHEMA_PATH.parents[1]
_DEFAULT_SCHEMA = _REPO_ROOT / "tooling" / "ai" / "schemas" / "usecase_bracket.schema.json"


def load_schema(schema_path: Path | None = None) -> Dict[str, Any]:
    """Load JSON schema from path. Default: tooling/ai/schemas/usecase_bracket.schema.json."""
    path = schema_path or _DEFAULT_SCHEMA
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def validate_bracket(data: Dict[str, Any], schema_path: Path | None = None) -> Tuple[bool, List[str]]:
    """
    Validate a bracket-like dict against usecase_bracket.schema.json.
    Returns (valid, list of error messages).
    """
    try:
        import jsonschema
    except ImportError:
        return False, ["jsonschema not installed; pip install jsonschema"]

    schema = load_schema(schema_path)
    if not schema:
        return False, ["Schema file not found"]

    try:
        jsonschema.validate(instance=data, schema=schema)
        return True, []
    except jsonschema.ValidationError as e:
        return False, [str(e.message)]
    except jsonschema.SchemaError as e:
        return False, [f"Schema error: {e}"]


def validate_bracket_yaml_string(yaml_text: str, schema_path: Path | None = None) -> Tuple[bool, List[str]]:
    """Parse YAML string and validate. Returns (valid, errors)."""
    try:
        import yaml
    except ImportError:
        return False, ["pyyaml not installed; pip install pyyaml"]
    try:
        data = yaml.safe_load(yaml_text)
    except Exception as e:
        return False, [f"YAML parse error: {e}"]
    if not isinstance(data, dict):
        return False, ["YAML root must be a mapping (bracket object)"]
    return validate_bracket(data, schema_path)
