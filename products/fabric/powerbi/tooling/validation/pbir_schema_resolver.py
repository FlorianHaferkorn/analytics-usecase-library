"""Resolve PBIR $schema URLs to cached Microsoft JSON Schema files."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from pathlib import Path
from urllib.parse import unquote
from urllib.request import urlopen

logger = logging.getLogger(__name__)

MICROSOFT_SCHEMA_PREFIX = "https://developer.microsoft.com/json-schemas/"
GITHUB_RAW_PREFIX = "https://raw.githubusercontent.com/microsoft/json-schemas/main/"

# Versions used in dist/ and pinned in schema_registry (fetch all for offline CI).
DEFAULT_SCHEMA_URLS: tuple[str, ...] = (
    "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.3.0/schema.json",
    "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.7.0/schema.json",
    "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.9.0/schema.json",
    "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json",
    "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
    "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.0.0/schema.json",
    "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.2.0/schema.json",
    "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.3.0/schema.json",
    "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
    "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
    "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
    "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json",
)


def resolve_fetch_url(schema_url: str) -> str:
    """Map developer.microsoft.com schema identifiers to fetchable raw GitHub URLs."""
    _validate_schema_url(schema_url)
    if schema_url.startswith(MICROSOFT_SCHEMA_PREFIX):
        return GITHUB_RAW_PREFIX + _microsoft_relative_string(schema_url)
    return schema_url


def _validate_schema_url(schema_url: str) -> None:
    """Reject schema URLs that cannot be mapped safely under schema_dir."""
    if not schema_url or not isinstance(schema_url, str):
        raise ValueError("Schema URL must be a non-empty string")
    url = schema_url.strip()
    if "\x00" in url or ".." in url:
        raise ValueError(f"Unsafe schema URL (path traversal): {schema_url!r}")
    if url.startswith(MICROSOFT_SCHEMA_PREFIX):
        return
    if url.startswith(("https://", "http://")):
        return
    raise ValueError(f"Unsupported schema URL scheme or host: {schema_url!r}")


def _microsoft_relative_string(schema_url: str) -> str:
    """Return the path suffix after MICROSOFT_SCHEMA_PREFIX with traversal segments removed."""
    if not schema_url.startswith(MICROSOFT_SCHEMA_PREFIX):
        raise ValueError(f"Not a Microsoft schema URL: {schema_url!r}")
    raw = unquote(schema_url[len(MICROSOFT_SCHEMA_PREFIX) :].split("?")[0].split("#")[0])
    raw = raw.replace("\\", "/").lstrip("/")
    parts: list[str] = []
    for part in raw.split("/"):
        if not part or part == ".":
            continue
        if part == "..":
            raise ValueError(f"Unsafe schema URL (path traversal): {schema_url!r}")
        if part in (":",) or ":" in part:
            raise ValueError(f"Unsafe schema URL segment: {part!r}")
        parts.append(part)
    if not parts:
        raise ValueError(f"Microsoft schema URL has no path segments: {schema_url!r}")
    return "/".join(parts)


def _assert_under_dir(path: Path, root: Path) -> Path:
    """Resolve path and ensure it stays inside root (no .. escape)."""
    resolved = path.resolve()
    root_resolved = root.resolve()
    if resolved == root_resolved:
        return resolved
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(f"Path escapes allowed directory {root_resolved}: {resolved}") from exc
    return resolved


def cache_file_path(schema_dir: Path, schema_url: str) -> Path:
    """Deterministic on-disk path for a schema URL under schema_dir/microsoft/..."""
    _validate_schema_url(schema_url)
    base = schema_dir.resolve()
    if schema_url.startswith(MICROSOFT_SCHEMA_PREFIX):
        rel = _microsoft_relative_string(schema_url)
        target = base / "microsoft" / rel
        return _assert_under_dir(target, base / "microsoft")
    digest = hashlib.sha256(schema_url.encode("utf-8")).hexdigest()[:32]
    target = base / "external" / f"{digest}.schema.json"
    return _assert_under_dir(target, base / "external")


def fetch_schema_bytes(schema_url: str, *, timeout: int = 30) -> bytes:
    _validate_schema_url(schema_url)
    fetch_url = resolve_fetch_url(schema_url)
    if not fetch_url.startswith(("https://", "http://")):
        raise ValueError(f"Refusing to fetch non-http(s) schema URL: {fetch_url!r}")
    req_headers = {"User-Agent": "analytics-usecase-library-pbir-schema-cache"}
    with urlopen(fetch_url, timeout=timeout) as response:  # noqa: S310
        return response.read()


def cache_schema(schema_dir: Path, schema_url: str, *, force: bool = False) -> Path:
    """Download schema_url into schema_dir if missing (or force). Returns cache path."""
    target = cache_file_path(schema_dir, schema_url)
    if target.exists() and not force:
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = fetch_schema_bytes(schema_url)
    data = json.loads(payload.decode("utf-8"))
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return target


def load_cached_schema(schema_dir: Path, schema_url: str, *, allow_fetch: bool = True) -> dict | None:
    """Load schema from cache; optionally fetch on miss."""
    path = cache_file_path(schema_dir, schema_url)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            logger.warning("Corrupt cached schema %s; refetching", path)
    if not allow_fetch:
        return None
    try:
        cache_schema(schema_dir, schema_url, force=True)
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Could not fetch schema %s: %s", schema_url, exc)
        return None


def legacy_schema_fallback(schema_dir: Path, instance_path: Path) -> Path | None:
    """Map file type to legacy stub schemas when $schema is absent."""
    name = instance_path.name.lower()
    mapping = {
        "visual.json": "visual.schema.json",
        "page.json": "page.schema.json",
        "definition.pbir": "definition.pbir.schema.json",
        "report.json": "report.schema.json",
    }
    stub = mapping.get(name)
    if not stub:
        return None
    candidate = schema_dir / stub
    try:
        safe = _assert_under_dir(candidate, schema_dir.resolve())
    except ValueError:
        return None
    return safe if safe.exists() else None


def schema_url_from_instance(instance_path: Path) -> str | None:
    try:
        data = json.loads(instance_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if isinstance(data, dict):
        url = data.get("$schema")
        return url if isinstance(url, str) and url.strip() else None
    return None


def validate_instance(
    instance_path: Path,
    schema_dir: Path,
    *,
    allow_fetch: bool = True,
) -> list[tuple[str, str]]:
    """Return list of (json_pointer, message) validation errors."""
    try:
        import jsonschema
    except ImportError as exc:
        raise RuntimeError("jsonschema not installed") from exc

    try:
        instance = json.loads(instance_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return [("(root)", f"JSON parse error: {exc}")]

    schema_url = instance.get("$schema") if isinstance(instance, dict) else None
    schema: dict | None = None

    if schema_url:
        try:
            schema = load_cached_schema(schema_dir, schema_url, allow_fetch=allow_fetch)
        except ValueError as exc:
            return [("(root)", f"Unsafe or invalid $schema URL: {exc}")]
        if schema is None:
            return [("(root)", f"Could not load schema for $schema: {schema_url}")]

    if schema is None:
        legacy = legacy_schema_fallback(schema_dir, instance_path)
        if legacy:
            schema = json.loads(legacy.read_text(encoding="utf-8"))
        else:
            return [("(root)", "No $schema field and no legacy stub schema found")]

    # Prefer report_quality registry when available (handles $ref across Microsoft schemas).
    try:
        _repo = Path(__file__).resolve().parents[5]
        import sys

        tooling = _repo / "tooling"
        if str(tooling) not in sys.path:
            sys.path.insert(0, str(tooling))
        from report_quality.schema_validator import validate_against_schema

        return validate_against_schema(
            instance,
            schema,
            schema_url=schema_url if isinstance(schema_url, str) else None,
            cache_dir=schema_dir / "fetch_cache",
        )
    except Exception:
        validator = jsonschema.Draft7Validator(schema)
        errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.path))
        return [
            (
                "/" + "/".join(str(p) for p in err.path) if err.path else "(root)",
                err.message,
            )
            for err in errors
        ]


def collect_schema_urls_from_report(def_dir: Path) -> set[str]:
    """Scan a report definition folder for all declared $schema URLs."""
    urls: set[str] = set()
    if not def_dir.is_dir():
        return urls
    patterns = ("**/page.json", "**/visual.json", "report.json", "definition.pbir", "version.json", "pages.json")
    for pattern in patterns:
        for path in def_dir.glob(pattern):
            if not path.is_file():
                continue
            url = schema_url_from_instance(path)
            if url:
                urls.add(url)
    return urls
