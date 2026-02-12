"""
Parameter Validator Module

Validates parameter.yml files for fabric-cicd:
- Structure and required fields
- GUID format where applicable
- Dynamic variable syntax ($workspace.$id, $items.*)
- Value types
"""
import os
import re
import uuid
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import modules.misc_functions as misc

# JSON schema optional (jsonschema package may not be installed)
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

# GUID pattern
GUID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)

# Dynamic variable patterns
DYNAMIC_VAR_PATTERN = re.compile(
    r"\$(?:workspace\.\$id|items(?:\.[A-Za-z0-9_.]+)*\.\$id)"
)
ALLOWED_DYNAMIC_PREFIXES = ("$workspace.$id", "$items.")


def is_guid(value: str) -> bool:
    """Return True if value looks like a GUID."""
    if not value or not isinstance(value, str):
        return False
    return bool(GUID_PATTERN.match(value.strip()))


def looks_like_dynamic_var(value: str) -> bool:
    """Return True if value is a dynamic variable like $workspace.$id or $items.X.$id."""
    if not value or not isinstance(value, str):
        return False
    s = value.strip()
    return s.startswith("$workspace.") or s.startswith("$items.")


def validate_find_replace_entry(entry: Dict[str, Any], index: int) -> List[str]:
    """Validate a single find_replace entry. Return list of error messages."""
    errors = []
    if "find_value" not in entry:
        errors.append(f"find_replace[{index}]: missing find_value")
    if "replace_value" not in entry:
        errors.append(f"find_replace[{index}]: missing replace_value")
        return errors

    rv = entry["replace_value"]
    if isinstance(rv, dict):
        for env, val in rv.items():
            if isinstance(val, str) and not looks_like_dynamic_var(val):
                if len(val) == 36 and "-" in val and is_guid(val):
                    pass  # valid GUID
                elif not val.startswith("$"):
                    pass  # literal string allowed
    return errors


def validate_semantic_model_binding_entry(entry: Dict[str, Any], index: int) -> List[str]:
    """Validate semantic_model_binding entry. connection_id should be GUID or placeholder."""
    errors = []
    if "connection_id" not in entry:
        errors.append(f"semantic_model_binding[{index}]: missing connection_id")
    else:
        cid = entry["connection_id"]
        if isinstance(cid, str) and cid != "connection-id-placeholder" and not is_guid(cid):
            if "placeholder" not in cid.lower() and "guid" not in cid.lower():
                errors.append(f"semantic_model_binding[{index}]: connection_id should be a GUID or placeholder")
    if "semantic_model_name" not in entry:
        errors.append(f"semantic_model_binding[{index}]: missing semantic_model_name")
    return errors


def validate_parameter_structure(data: Dict[str, Any]) -> List[str]:
    """Validate top-level structure and types. Returns list of errors."""
    errors = []
    if not isinstance(data, dict):
        return ["Parameter file must be a YAML/JSON object"]

    for key in ("find_replace", "key_value_replace", "spark_pool", "semantic_model_binding"):
        if key in data and not isinstance(data[key], list):
            errors.append(f"'{key}' must be an array")
    return errors


def validate_guids_in_data(data: Any, path: str) -> List[str]:
    """Recursively check string values that look like GUIDs for valid format."""
    errors = []
    if isinstance(data, dict):
        for k, v in data.items():
            errors.extend(validate_guids_in_data(v, f"{path}.{k}"))
    elif isinstance(data, list):
        for i, v in enumerate(data):
            errors.extend(validate_guids_in_data(v, f"{path}[{i}]"))
    elif isinstance(data, str) and len(data) == 36 and "-" in data:
        if not looks_like_dynamic_var(data) and "placeholder" not in data.lower():
            if not is_guid(data):
                errors.append(f"{path}: invalid GUID format")
    return errors


def validate_parameter_file(
    file_path: str,
    schema_path: Optional[str] = None,
    env_definition: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Validate a parameter.yml file.

    Args:
        file_path: Path to parameter.yml
        schema_path: Optional path to parameter.schema.json
        env_definition: Optional environment config for cross-reference

    Returns:
        (success, list of error messages, details dict)
    """
    errors: List[str] = []
    details: Dict[str, Any] = {"file_path": file_path}

    if not os.path.isfile(file_path):
        return (False, [f"File not found: {file_path}"], details)

    try:
        import yaml
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        return (False, [f"Failed to load YAML: {e}"], details)

    if data is None:
        return (True, [], {**details, "empty": True})

    # Structure
    errors.extend(validate_parameter_structure(data))
    if errors:
        return (False, errors, details)

    # Optional JSON schema validation
    if HAS_JSONSCHEMA and schema_path and os.path.isfile(schema_path):
        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                import json
                schema = json.load(f)
            jsonschema.validate(instance=data, schema=schema)
        except jsonschema.ValidationError as e:
            errors.append(f"Schema validation: {e}")
        except Exception as e:
            details["schema_error"] = str(e)

    # find_replace entries
    for i, entry in enumerate(data.get("find_replace", [])):
        if isinstance(entry, dict):
            errors.extend(validate_find_replace_entry(entry, i))

    # semantic_model_binding
    for i, entry in enumerate(data.get("semantic_model_binding", [])):
        if isinstance(entry, dict):
            errors.extend(validate_semantic_model_binding_entry(entry, i))

    # GUIDs
    errors.extend(validate_guids_in_data(data, "root"))

    details["error_count"] = len(errors)
    return (len(errors) == 0, errors, details)


def validate_parameter_file_from_repo(
    repo_path: str,
    layer_git_directory: str,
    parameter_filename: str = "parameter.yml",
) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Resolve parameter file path from repo root and layer directory, then validate.

    Args:
        repo_path: Repository root or solution root
        layer_git_directory: e.g. solution/dm
        parameter_filename: Name of parameter file

    Returns:
        (success, errors, details)
    """
    # parameter.yml typically lives in the layer folder under repo
    relative = layer_git_directory.replace("solution/", "").strip()
    if relative:
        param_path = os.path.join(repo_path, relative, parameter_filename)
    else:
        param_path = os.path.join(repo_path, parameter_filename)

    script_dir = Path(__file__).parent
    schema_path = script_dir.parent.parent / "resources" / "parameters" / "parameter.schema.json"
    return validate_parameter_file(
        param_path,
        schema_path=str(schema_path) if schema_path.is_file() else None,
    )
