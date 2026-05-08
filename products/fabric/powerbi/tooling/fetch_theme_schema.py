"""
fetch_theme_schema.py — Resolve the pinned Power BI report theme JSON schema.

Schema source: microsoft/powerbi-desktop-samples / Report Theme JSON Schema
  https://github.com/microsoft/powerbi-desktop-samples/tree/main/Report%20Theme%20JSON%20Schema

Strategy (in priority order):
  1. If a local pinned copy exists at SCHEMA_CACHE_PATH, use it.
  2. If not and network is available, download the pinned version and cache it.
  3. If network is unavailable, return None — caller decides whether to skip or fail.

Pinned version is controlled by schema_registry.THEME_SCHEMA_PINNED_VERSION.
Update that constant when upgrading to a new Power BI Desktop release.
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

from products.fabric.powerbi.tooling.schema_registry import (
    THEME_SCHEMA_PINNED_VERSION as PINNED_VERSION,
    THEME_SCHEMA_URL as SCHEMA_URL,
)

SCHEMA_FILENAME = f"reportThemeSchema-{PINNED_VERSION}.json"

_HERE = Path(__file__).resolve().parent
SCHEMA_CACHE_PATH = _HERE / SCHEMA_FILENAME


def get_schema_path() -> Path | None:
    """Return path to the local schema file, downloading if necessary.

    Returns None if the schema cannot be resolved (network unavailable, no cache).
    """
    if SCHEMA_CACHE_PATH.exists():
        return SCHEMA_CACHE_PATH

    try:
        with urllib.request.urlopen(SCHEMA_URL, timeout=10) as resp:
            data = resp.read()
        json.loads(data)  # validate parseable before caching
        SCHEMA_CACHE_PATH.write_bytes(data)
        return SCHEMA_CACHE_PATH
    except Exception:
        return None
