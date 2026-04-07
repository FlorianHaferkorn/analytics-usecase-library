"""
Shared YAML loading utility for tooling scripts.

Usage:
    from tooling.utils.yaml_loader import load_yaml
    data = load_yaml(Path("core/kpi_catalog/KPI_Catalog.md"))
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: Path | str) -> dict[str, Any]:
    """Load a YAML file and return its contents as a dict.

    Returns an empty dict if the file is empty or parses to None.
    Raises FileNotFoundError or yaml.YAMLError on failure.
    """
    p = Path(path)
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}
