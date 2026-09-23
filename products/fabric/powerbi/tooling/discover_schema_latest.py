#!/usr/bin/env python3
"""
discover_schema_latest.py — Automated Microsoft schema latest-version discovery.

Queries the microsoft/json-schemas GitHub repository to find the newest
available version for each PBIR/PBIP schema, then compares against the
versions pinned in schema_registry.py. Results are cached so local gates
never break on network outages.

Modes
-----
(default / --check)
    Print a table of pinned vs. latest versions. Exit 0 — informational only.

--fail-if-behind
    Exit 1 if any schema is behind the latest known version.

--update-comments
    Rewrite "Latest known: X.Y.Z" comments in schema_registry.py only.
    Does NOT change pinned version constants — safe to run in CI.

--update-manifest
    After --update-comments, also regenerates schema_manifest.json via
    update_schema_manifest.py.

Usage (from repository root):
    py -3 products/fabric/powerbi/tooling/discover_schema_latest.py
    py -3 products/fabric/powerbi/tooling/discover_schema_latest.py --fail-if-behind
    py -3 products/fabric/powerbi/tooling/discover_schema_latest.py --update-comments
    py -3 products/fabric/powerbi/tooling/discover_schema_latest.py --update-comments --update-manifest
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from products.fabric.powerbi.tooling.schema_registry import all_schemas

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

_CACHE_PATH = _REPO_ROOT / "tooling" / "schemas" / "pbir" / "latest_discovery.json"
_REGISTRY_PATH = Path(__file__).with_name("schema_registry.py")
_GITHUB_API = "https://api.github.com/repos/microsoft/json-schemas/contents"
_GITHUB_PBI_SAMPLES_API = (
    "https://api.github.com/repos/microsoft/powerbi-desktop-samples/contents"
    "/Report%20Theme%20JSON%20Schema"
)

# Maps logical schema name → GitHub path under microsoft/json-schemas
_SCHEMA_GITHUB_PATHS: dict[str, str] = {
    "report": "fabric/item/report/definition/report",
    "page": "fabric/item/report/definition/page",
    "visual": "fabric/item/report/definition/visualContainer",
    "pages_metadata": "fabric/item/report/definition/pagesMetadata",
    "version_metadata": "fabric/item/report/definition/versionMetadata",
    "definition_pbir": "fabric/item/report/definitionProperties",
    "semantic_model": "fabric/item/semanticModel/definitionProperties",
    "platform_properties": "fabric/gitIntegration/platformProperties",
}

_SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
_THEME_VER_RE = re.compile(r"reportThemeSchema-(\d+\.\d+)\.json")


# ── Types ──────────────────────────────────────────────────────────────────────

class SchemaStatus(NamedTuple):
    name: str
    pinned: str
    latest: str | None  # None = could not determine
    source: str  # "github" | "cache" | "offline"
    behind: bool


# ── Version helpers ────────────────────────────────────────────────────────────

def _semver_tuple(v: str) -> tuple[int, ...]:
    m = _SEMVER_RE.match(v.strip())
    if m:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    # Fallback: split by "." and parse integers
    try:
        return tuple(int(p) for p in v.strip().split("."))
    except ValueError:
        return (0,)


def _is_behind(pinned: str, latest: str) -> bool:
    return _semver_tuple(pinned) < _semver_tuple(latest)


# ── GitHub fetchers ────────────────────────────────────────────────────────────

def _github_fetch(url: str, timeout: int = 10) -> list[dict]:
    """Fetch a GitHub directory listing. Returns [] on any error."""
    try:
        req = urllib.request.Request(
            url,
            headers={"Accept": "application/vnd.github+json", "User-Agent": "analytics-usecase-library-schema-bot"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        logger.debug("GitHub fetch failed for %s: %s", url, exc)
        return []


def _latest_version_from_github(path: str) -> str | None:
    """List version directories on GitHub and return the highest semver."""
    entries = _github_fetch(f"{_GITHUB_API}/{path}")
    if not entries:
        return None
    versions: list[str] = []
    for entry in entries:
        name = entry.get("name", "")
        if _SEMVER_RE.match(name):
            versions.append(name)
    if not versions:
        return None
    return max(versions, key=_semver_tuple)


def _latest_theme_version_from_github() -> str | None:
    """Scan powerbi-desktop-samples theme schema files and return the latest version."""
    entries = _github_fetch(_GITHUB_PBI_SAMPLES_API)
    if not entries:
        return None
    versions: list[str] = []
    for entry in entries:
        m = _THEME_VER_RE.match(entry.get("name", ""))
        if m:
            versions.append(m.group(1))
    if not versions:
        return None
    return max(versions, key=lambda v: _semver_tuple(v + ".0"))


# ── Pinned versions ────────────────────────────────────────────────────────────

def _pinned_versions() -> dict[str, str]:
    """Extract pinned version strings from schema_registry URLs."""
    schemas = all_schemas()
    result: dict[str, str] = {}
    for name, url in schemas.items():
        if name in ("theme_url", "theme_pinned_version"):
            continue
        # Extract version from URL segment like /2.3.0/schema.json
        m = re.search(r"/(\d+\.\d+\.\d+)/schema\.json", url)
        if m:
            result[name] = m.group(1)
    # Theme version is a separate key
    if "theme_pinned_version" in schemas:
        result["theme"] = str(schemas["theme_pinned_version"])
    return result


# ── Cache ──────────────────────────────────────────────────────────────────────

def _load_cache() -> dict[str, str]:
    """Load the cached latest-version map. Returns {} if absent or malformed."""
    if not _CACHE_PATH.exists():
        return {}
    try:
        data = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
        return data.get("latest_versions", {})
    except Exception:
        return {}


def _save_cache(latest_versions: dict[str, str]) -> None:
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "_note": "Auto-generated by discover_schema_latest.py. Do not edit manually.",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "latest_versions": latest_versions,
    }
    _CACHE_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")


# ── Main discovery ─────────────────────────────────────────────────────────────

def discover(use_cache_on_failure: bool = True) -> list[SchemaStatus]:
    """Discover latest versions and return a status list."""
    pinned = _pinned_versions()
    cached = _load_cache()
    results: list[SchemaStatus] = []
    fetched: dict[str, str] = {}
    network_ok = False

    # Try to fetch non-theme schemas from GitHub
    for name, gh_path in _SCHEMA_GITHUB_PATHS.items():
        if name not in pinned:
            continue
        latest = _latest_version_from_github(gh_path)
        if latest:
            network_ok = True
            fetched[name] = latest
        elif cached.get(name):
            fetched[name] = cached[name]

    # Theme version
    theme_latest = _latest_theme_version_from_github()
    if theme_latest:
        network_ok = True
        fetched["theme"] = theme_latest
    elif cached.get("theme"):
        fetched["theme"] = cached["theme"]

    # Save updated cache only if we got fresh data
    if network_ok and fetched:
        merged = {**cached, **fetched}
        _save_cache(merged)

    for name, p in pinned.items():
        l = fetched.get(name)
        source = "github" if (network_ok and name in fetched) else ("cache" if l else "offline")
        results.append(SchemaStatus(
            name=name,
            pinned=p,
            latest=l,
            source=source,
            behind=_is_behind(p, l) if l else False,
        ))

    return results


# ── Registry comment updater ───────────────────────────────────────────────────

def _update_registry_comments(statuses: list[SchemaStatus]) -> bool:
    """Rewrite 'Latest known: X.Y.Z' comments in schema_registry.py. Returns True if any changed."""
    text = _REGISTRY_PATH.read_text(encoding="utf-8")
    original = text
    for s in statuses:
        if s.latest is None:
            continue
        # Pattern: |  Latest known: <old_version>
        pattern = rf"(Latest known: ){re.escape(s.pinned if not s.behind else '.*?')}(\s*)"
        # Safer: replace exact "Latest known: <current>" with "Latest known: <latest>"
        old_comment = f"Latest known: {s.pinned}"
        new_comment = f"Latest known: {s.latest}"
        if old_comment in text and old_comment != new_comment:
            text = text.replace(old_comment, new_comment, 1)
    if text != original:
        _REGISTRY_PATH.write_text(text, encoding="utf-8", newline="\n")
        return True
    return False


# ── CLI ────────────────────────────────────────────────────────────────────────

def _print_table(statuses: list[SchemaStatus]) -> None:
    print(f"\n{'Schema':<24} {'Pinned':<10} {'Latest':<10} {'Source':<8} Status")
    print("-" * 70)
    for s in statuses:
        latest_str = s.latest or "unknown"
        status = "BEHIND" if s.behind else ("OK" if s.latest else "OFFLINE")
        flag = " <-- update available" if s.behind else ""
        print(f"{s.name:<24} {s.pinned:<10} {latest_str:<10} {s.source:<8} {status}{flag}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--fail-if-behind", action="store_true", help="Exit 1 if any schema is behind latest.")
    parser.add_argument("--update-comments", action="store_true", help="Rewrite 'Latest known' comments in schema_registry.py.")
    parser.add_argument("--update-manifest", action="store_true", help="Also regenerate schema_manifest.json (implies --update-comments).")
    parser.add_argument("--json-out", action="store_true", help="Output result as JSON to stdout.")
    args = parser.parse_args(argv)

    statuses = discover()

    if args.json_out:
        data = [s._asdict() for s in statuses]
        print(json.dumps(data, indent=2))
        return 0

    _print_table(statuses)
    behind = [s for s in statuses if s.behind]

    if args.update_comments or args.update_manifest:
        changed = _update_registry_comments(statuses)
        if changed:
            print(f"\nUpdated 'Latest known' comments in {_REGISTRY_PATH.name}.")
        else:
            print("\nNo comment updates needed in schema_registry.py.")

    if args.update_manifest:
        manifest_script = Path(__file__).with_name("update_schema_manifest.py")
        import subprocess
        result = subprocess.run([sys.executable, str(manifest_script)], capture_output=True, text=True, encoding="utf-8", errors="replace")
        print(result.stdout.strip())
        if result.returncode != 0:
            print(result.stderr.strip(), file=sys.stderr)
            return result.returncode

    if behind:
        behind_names = ", ".join(s.name for s in behind)
        print(f"\n{len(behind)} schema(s) behind latest: {behind_names}")
        if args.fail_if_behind:
            print("Exiting 1 (--fail-if-behind).", file=sys.stderr)
            return 1

    if not behind:
        print("\nAll schemas are up to date (or latest could not be determined).")

    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    sys.exit(main())
