"""Tests for discover_schema_latest.py — offline-only, no network calls."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))

from products.fabric.powerbi.tooling.discover_schema_latest import (
    _is_behind,
    _semver_tuple,
    _pinned_versions,
    _load_cache,
    _save_cache,
    _update_registry_comments,
    discover,
    SchemaStatus,
)


class TestSemverHelpers:
    def test_standard_semver(self):
        assert _semver_tuple("2.3.0") == (2, 3, 0)
        assert _semver_tuple("10.0.1") == (10, 0, 1)

    def test_two_part_version(self):
        assert _semver_tuple("2.152") == (2, 152)

    def test_is_behind_false_when_equal(self):
        assert _is_behind("2.3.0", "2.3.0") is False

    def test_is_behind_true_when_patch_behind(self):
        assert _is_behind("2.3.0", "2.3.1") is True

    def test_is_behind_true_when_minor_behind(self):
        assert _is_behind("2.0.0", "2.1.0") is True

    def test_is_behind_false_when_ahead(self):
        assert _is_behind("3.0.0", "2.9.9") is False


class TestPinnedVersions:
    def test_returns_dict_with_known_schemas(self):
        pinned = _pinned_versions()
        assert "report" in pinned
        assert "page" in pinned
        assert "visual" in pinned
        assert "theme" in pinned

    def test_versions_are_semver_strings(self):
        pinned = _pinned_versions()
        for name, ver in pinned.items():
            assert re.match(r"\d+\.\d+", ver), f"{name} version {ver!r} not semver"

    def test_report_version_is_known(self):
        pinned = _pinned_versions()
        major = int(pinned["report"].split(".")[0])
        assert major >= 3, f"Report schema major version unexpectedly < 3: {pinned['report']}"


import re


class TestCache:
    def test_load_cache_returns_empty_on_missing_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "products.fabric.powerbi.tooling.discover_schema_latest._CACHE_PATH",
            tmp_path / "nonexistent.json",
        )
        assert _load_cache() == {}

    def test_save_and_load_round_trip(self, tmp_path, monkeypatch):
        cache_file = tmp_path / "discovery.json"
        monkeypatch.setattr(
            "products.fabric.powerbi.tooling.discover_schema_latest._CACHE_PATH",
            cache_file,
        )
        data = {"report": "4.0.0", "page": "3.0.0"}
        _save_cache(data)
        assert cache_file.exists()
        loaded = _load_cache()
        assert loaded == data

    def test_cache_file_has_metadata(self, tmp_path, monkeypatch):
        cache_file = tmp_path / "discovery.json"
        monkeypatch.setattr(
            "products.fabric.powerbi.tooling.discover_schema_latest._CACHE_PATH",
            cache_file,
        )
        _save_cache({"report": "3.0.0"})
        payload = json.loads(cache_file.read_text(encoding="utf-8"))
        assert "fetched_at" in payload
        assert "_note" in payload


class TestDiscoverOffline:
    """discover() must work offline: returns pinned versions with source='offline'."""

    def test_offline_returns_all_pinned_schemas(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            "products.fabric.powerbi.tooling.discover_schema_latest._CACHE_PATH",
            tmp_path / "cache.json",
        )
        # Patch GitHub fetch to always return []
        monkeypatch.setattr(
            "products.fabric.powerbi.tooling.discover_schema_latest._github_fetch",
            lambda *_a, **_kw: [],
        )
        monkeypatch.setattr(
            "products.fabric.powerbi.tooling.discover_schema_latest._latest_theme_version_from_github",
            lambda: None,
        )
        statuses = discover()
        assert len(statuses) > 0
        pinned = _pinned_versions()
        names = {s.name for s in statuses}
        assert "report" in names
        assert "visual" in names
        for s in statuses:
            assert s.pinned == pinned[s.name]

    def test_offline_never_marks_behind(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            "products.fabric.powerbi.tooling.discover_schema_latest._CACHE_PATH",
            tmp_path / "cache.json",
        )
        monkeypatch.setattr(
            "products.fabric.powerbi.tooling.discover_schema_latest._github_fetch",
            lambda *_a, **_kw: [],
        )
        monkeypatch.setattr(
            "products.fabric.powerbi.tooling.discover_schema_latest._latest_theme_version_from_github",
            lambda: None,
        )
        statuses = discover()
        assert all(not s.behind for s in statuses)

    def test_cache_used_when_offline(self, monkeypatch, tmp_path):
        cache_file = tmp_path / "cache.json"
        monkeypatch.setattr(
            "products.fabric.powerbi.tooling.discover_schema_latest._CACHE_PATH",
            cache_file,
        )
        # Pre-populate cache with a newer version for 'report'
        _save_cache({"report": "99.0.0"})

        monkeypatch.setattr(
            "products.fabric.powerbi.tooling.discover_schema_latest._github_fetch",
            lambda *_a, **_kw: [],
        )
        monkeypatch.setattr(
            "products.fabric.powerbi.tooling.discover_schema_latest._latest_theme_version_from_github",
            lambda: None,
        )
        statuses = discover()
        report = next(s for s in statuses if s.name == "report")
        assert report.latest == "99.0.0"
        assert report.behind is True
        assert report.source == "cache"


class TestUpdateRegistryComments:
    """_update_registry_comments must only change 'Latest known' comment lines."""

    def _make_registry(self, tmp_path: Path, content: str) -> Path:
        p = tmp_path / "schema_registry.py"
        p.write_text(content, encoding="utf-8")
        return p

    def test_updates_comment_when_behind(self, tmp_path, monkeypatch):
        content = "# Pinned: 2.0.0  |  Latest known: 2.0.0  |  Updated: 2026-05\nPAGE_SCHEMA = '...2.0.0/schema.json'\n"
        registry = self._make_registry(tmp_path, content)
        monkeypatch.setattr(
            "products.fabric.powerbi.tooling.discover_schema_latest._REGISTRY_PATH",
            registry,
        )
        statuses = [SchemaStatus(name="page", pinned="2.0.0", latest="2.1.0", source="github", behind=True)]
        changed = _update_registry_comments(statuses)
        assert changed
        updated = registry.read_text(encoding="utf-8")
        assert "Latest known: 2.1.0" in updated

    def test_no_change_when_up_to_date(self, tmp_path, monkeypatch):
        content = "# Pinned: 2.0.0  |  Latest known: 2.0.0  |  Updated: 2026-05\nPAGE_SCHEMA = '...2.0.0/schema.json'\n"
        registry = self._make_registry(tmp_path, content)
        monkeypatch.setattr(
            "products.fabric.powerbi.tooling.discover_schema_latest._REGISTRY_PATH",
            registry,
        )
        statuses = [SchemaStatus(name="page", pinned="2.0.0", latest="2.0.0", source="github", behind=False)]
        changed = _update_registry_comments(statuses)
        assert not changed

    def test_no_change_when_latest_is_none(self, tmp_path, monkeypatch):
        content = "# Latest known: 2.0.0\n"
        registry = self._make_registry(tmp_path, content)
        monkeypatch.setattr(
            "products.fabric.powerbi.tooling.discover_schema_latest._REGISTRY_PATH",
            registry,
        )
        statuses = [SchemaStatus(name="page", pinned="2.0.0", latest=None, source="offline", behind=False)]
        changed = _update_registry_comments(statuses)
        assert not changed
