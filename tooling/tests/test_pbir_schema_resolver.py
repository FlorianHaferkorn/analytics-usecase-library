"""Security and path-resolution tests for pbir_schema_resolver."""

from __future__ import annotations

import pytest
from pathlib import Path

from products.fabric.powerbi.tooling.validation.pbir_schema_resolver import (
    MICROSOFT_SCHEMA_PREFIX,
    cache_file_path,
    validate_instance,
)

_VALID_VISUAL = (
    MICROSOFT_SCHEMA_PREFIX
    + "fabric/item/report/definition/visualContainer/2.7.0/schema.json"
)


def test_cache_file_path_stays_under_microsoft_root(tmp_path: Path) -> None:
    schema_dir = tmp_path / "pbir"
    target = cache_file_path(schema_dir, _VALID_VISUAL)
    assert target.is_relative_to((schema_dir / "microsoft").resolve())


@pytest.mark.parametrize(
    "malicious_url",
    [
        MICROSOFT_SCHEMA_PREFIX + "../../../etc/passwd",
        MICROSOFT_SCHEMA_PREFIX + "fabric/../secret/schema.json",
        MICROSOFT_SCHEMA_PREFIX + "%2e%2e%2fsecret/schema.json",
        "file:///etc/passwd",
        "https://evil.example/schema.json\x00.json",
    ],
)
def test_cache_file_path_rejects_traversal(tmp_path: Path, malicious_url: str) -> None:
    with pytest.raises(ValueError):
        cache_file_path(tmp_path / "pbir", malicious_url)


def test_validate_instance_rejects_unsafe_schema_url(tmp_path: Path) -> None:
    instance = tmp_path / "visual.json"
    instance.write_text(
        '{"$schema": "'
        + MICROSOFT_SCHEMA_PREFIX
        + '../../../outside/schema.json", "name": "x"}',
        encoding="utf-8",
    )
    errors = validate_instance(instance, tmp_path / "pbir", allow_fetch=False)
    assert any("Unsafe" in msg or "invalid" in msg.lower() for _, msg in errors)
