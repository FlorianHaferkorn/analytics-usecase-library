"""
BrandSpec loader — I/O boundary for brand derivations.

Single responsibility: read a brand_spec.yaml from disk and return a
validated dict. All downstream converters accept that dict and assume
it is structurally valid (no defensive fallbacks inside business logic).

Raises ValueError with the exact missing field path so errors are
caught at the boundary, not silently swallowed inside converters.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
    _YAML_OK = True
except ImportError:
    _YAML_OK = False


# Fields that all downstream converters depend on.
# Dot-notation paths into the loaded dict.
_REQUIRED_FIELDS: tuple[str, ...] = (
    "identity.brand_id",
    "identity.brand_name",
    "color.primary",
    "color.secondary",
    "color.semantic.positive.color",
    "color.semantic.negative.color",
    "color.semantic.warning.color",
    "color.semantic.neutral.color",
    "color.neutral_scale.50",
    "color.neutral_scale.100",
    "color.neutral_scale.200",
    "color.neutral_scale.400",
    "color.neutral_scale.700",
    "color.neutral_scale.900",
    "typography.font_family.primary",
    "typography.tool_minimums.powerbi.body_pt",
    "typography.tool_minimums.powerbi.label_pt",
    "typography.tool_minimums.powerbi.kpi_pt",
    "spacing.scale.sm",
    "spacing.scale.md",
    "spacing.scale.lg",
    "spacing.scale.xl",
)


def load_brand_spec(path: Path) -> dict[str, Any]:
    """
    Load a brand_spec.yaml and return the validated dict.

    Args:
        path: Absolute or relative path to a brand_spec.yaml file.

    Returns:
        Validated dict matching the BrandSpec schema.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If YAML is malformed or a required field is missing.
        ImportError: If PyYAML is not installed (hint provided).
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Brand spec not found: {path}")

    if not _YAML_OK:
        raise ImportError("PyYAML is required: pip install pyyaml")

    raw = path.read_text(encoding="utf-8")
    try:
        spec = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise ValueError(f"YAML parse error in {path}: {exc}") from exc

    if not isinstance(spec, dict):
        raise ValueError(f"Brand spec must be a YAML mapping, got {type(spec).__name__}")

    _validate_required_fields(spec, path)
    return spec


def _validate_required_fields(spec: dict[str, Any], source: Path) -> None:
    """Raise ValueError listing every missing required field."""
    missing = [fp for fp in _REQUIRED_FIELDS if not _field_present(spec, fp)]
    if missing:
        formatted = "\n  ".join(missing)
        raise ValueError(
            f"Brand spec {source} is missing required fields:\n  {formatted}"
        )


def _field_present(spec: dict[str, Any], dot_path: str) -> bool:
    """Return True if the dot-notation path resolves to a non-None value."""
    node: Any = spec
    for key in dot_path.split("."):
        if not isinstance(node, dict):
            return False
        node = node.get(key)
        if node is None:
            return False
    return True
