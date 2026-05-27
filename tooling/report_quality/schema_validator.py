"""PBIR JSON schema validation with Microsoft schema URL rewrite and cache."""

from __future__ import annotations

import hashlib
import json
import logging
import os
from urllib.request import urlopen
from pathlib import Path
from typing import Iterable

from .models import Violation

logger = logging.getLogger(__name__)

DEFAULT_CACHE_DIR = Path(
    os.environ.get(
        "REPORT_QUALITY_SCHEMA_CACHE",
        Path.home() / ".cache" / "analytics_usecase_library" / "schemas",
    )
)

SCHEMA_URL_REWRITES = (
    (
        "https://developer.microsoft.com/json-schemas/",
        "https://raw.githubusercontent.com/microsoft/json-schemas/main/",
    ),
)


def resolve_schema_url(url: str) -> str:
    """Rewrite Microsoft schema identifier URLs to fetchable GitHub raw URLs."""

    for prefix, replacement in SCHEMA_URL_REWRITES:
        if url.startswith(prefix):
            return replacement + url[len(prefix) :]
    return url


def cache_path(url: str, cache_dir: Path = DEFAULT_CACHE_DIR) -> Path:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:32]
    return cache_dir / f"{digest}.json"


def fetch_schema(url: str, *, cache_dir: Path = DEFAULT_CACHE_DIR, force: bool = False) -> dict | None:
    """Fetch a schema, using a local cache and returning None if unavailable."""

    cache_dir.mkdir(parents=True, exist_ok=True)
    cached = cache_path(url, cache_dir)
    if cached.exists() and not force:
        try:
            return json.loads(cached.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            cached.unlink(missing_ok=True)

    try:
        with urlopen(resolve_schema_url(url), timeout=30) as response:  # noqa: S310 - schema URL is registry input.
            schema = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # pragma: no cover - network dependent
        logger.warning("Could not fetch schema %s: %s", url, exc)
        return None

    cached.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    return schema


def _build_registry(schema_url: str | None, schema: dict, cache_dir: Path):
    """Build a jsonschema referencing registry for relative `$ref` schemas."""

    from referencing import Registry, Resource
    from referencing.exceptions import NoSuchResource
    from referencing.jsonschema import DRAFT7

    def retrieve(uri: str):
        ref_schema = fetch_schema(uri, cache_dir=cache_dir)
        if ref_schema is None:
            raise NoSuchResource(ref=uri)
        return Resource.from_contents(ref_schema, default_specification=DRAFT7)

    registry = Registry(retrieve=retrieve)
    if schema_url:
        registry = registry.with_resource(
            uri=schema_url,
            resource=Resource.from_contents(schema, default_specification=DRAFT7),
        )
    return registry


def validate_against_schema(
    data: object,
    schema: dict,
    *,
    schema_url: str | None = None,
    cache_dir: Path = DEFAULT_CACHE_DIR,
) -> list[tuple[str, str]]:
    """Return `(json_pointer, message)` schema errors."""

    from jsonschema import Draft7Validator

    try:
        validator = Draft7Validator(schema, registry=_build_registry(schema_url, schema, cache_dir))
    except Exception:
        validator = Draft7Validator(schema)

    errors: list[tuple[str, str]] = []
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path)):
        pointer = "/" + "/".join(str(p) for p in err.absolute_path)
        errors.append((pointer, err.message))
    return errors


def validate_json_file(
    path: Path,
    *,
    cache_dir: Path = DEFAULT_CACHE_DIR,
    root: Path | None = None,
) -> list[Violation]:
    """Validate one JSON/PBIR file against its declared `$schema`."""

    rel = str(path.relative_to(root)) if root else str(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return [Violation("schema:invalid-json", "critical", rel, f"File is not valid JSON: {exc}")]

    schema_url = data.get("$schema") if isinstance(data, dict) else None
    if not schema_url:
        return [Violation("schema:no-schema-url", "info", rel, "File has no $schema field; skipped")]

    schema = fetch_schema(schema_url, cache_dir=cache_dir)
    if schema is None:
        return [Violation("schema:fetch-failed", "warning", rel, f"Could not fetch schema {schema_url}")]

    return [
        Violation("schema:violation", "critical", f"{rel}#{ptr}", message, expected=schema_url)
        for ptr, message in validate_against_schema(data, schema, schema_url=schema_url, cache_dir=cache_dir)
    ]


def validate_report_directory(
    report_dir: Path,
    *,
    cache_dir: Path = DEFAULT_CACHE_DIR,
    patterns: Iterable[str] = ("**/definition/**/*.json", "**/definition.pbir", "*.pbip"),
) -> list[Violation]:
    """Validate PBIR/PBIP JSON files in a report directory."""

    violations: list[Violation] = []
    seen: set[Path] = set()
    for pattern in patterns:
        for path in report_dir.glob(pattern):
            if path.is_file() and path not in seen:
                seen.add(path)
                violations.extend(validate_json_file(path, cache_dir=cache_dir, root=report_dir))
    return violations
