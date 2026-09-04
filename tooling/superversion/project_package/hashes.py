"""Deterministic hashes for source modules and package revisions."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_bytes(value: Any) -> bytes:
    """Return a timestamp-independent canonical JSON representation."""
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    """Hash structured content after deterministic JSON normalization."""
    return hashlib.sha256(canonical_bytes(value)).hexdigest()
