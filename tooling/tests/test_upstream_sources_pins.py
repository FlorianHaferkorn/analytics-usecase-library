"""Upstream pin sensor, kinds ``github`` and ``pypi`` (Meridian D-603, 30.09.2026).

Peer test: the Claude Code marketplace ``fabric-collection`` in ``.claude/settings.json``
and the ``github`` pin in ``tooling/quality/check_upstream_sources.py`` name the same repo
and tag, and the enabled/disabled plugins match the pin entry. A bump must touch both.
"""
from __future__ import annotations

import json
from pathlib import Path

from tooling.quality.check_upstream_sources import (
    ACTIONABLE,
    ALLOWLIST,
    evaluate_github_tags,
    evaluate_pypi,
    latest_semver_tag,
    parse_ls_remote_tags,
)

REPO = Path(__file__).resolve().parents[2]
SETTINGS = REPO / ".claude" / "settings.json"
MARKETPLACE = "fabric-collection"


def _entry(kind: str) -> dict:
    hits = [s for s in ALLOWLIST if s.get("kind") == kind]
    assert len(hits) == 1, kind
    return hits[0]


def test_settings_marketplace_equals_github_pin() -> None:
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    pin = _entry("github")
    market = settings["extraKnownMarketplaces"][MARKETPLACE]
    assert market["source"] == {"source": "github", "repo": pin["repo"], "ref": pin["pin"]}
    assert market["autoUpdate"] is False
    enabled = settings["enabledPlugins"]
    for tool in pin["tools"]:
        assert enabled[tool] is True, tool
    for tool in pin["disabled_tools"]:
        assert enabled[tool] is False, tool
    ours = {k for k in enabled if k.endswith(f"@{MARKETPLACE}")}
    assert ours == set(pin["tools"]) | set(pin["disabled_tools"])


def test_github_pin_is_exact() -> None:
    pin = _entry("github")
    assert pin["pin"] == "v0.3.18"
    assert pin["commit"] == "6c11ad58c25992e5d1435ce7cd80d217d5598a31"


def test_settings_keeps_existing_hooks() -> None:
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    commands = [h["command"] for block in settings["hooks"]["PostToolUse"] for h in block["hooks"]]
    assert "bash .claude/hooks/validate_tmdl_style.sh" in commands
    assert "bash .claude/hooks/validate_pbir_structure.sh" in commands


_LS = (
    "1111111111111111111111111111111111111111\trefs/tags/v0.3.17\n"
    "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\trefs/tags/v0.3.18\n"
    "6c11ad58c25992e5d1435ce7cd80d217d5598a31\trefs/tags/v0.3.18^{}\n"
    "2222222222222222222222222222222222222222\trefs/tags/v0.4.0-rc1\n"
)


def test_parse_ls_remote_prefers_peeled_commit() -> None:
    tags = parse_ls_remote_tags(_LS)
    assert tags["v0.3.18"] == "6c11ad58c25992e5d1435ce7cd80d217d5598a31"
    assert latest_semver_tag(tags) == "v0.3.18"   # pre-release never counts as newest


def test_github_up_to_date() -> None:
    status, remote, _ = evaluate_github_tags(_entry("github"), parse_ls_remote_tags(_LS))
    assert (status, remote) == ("up_to_date", "v0.3.18")
    assert status not in ACTIONABLE


def test_github_newer_tag_moved_tag_missing_tag() -> None:
    src = _entry("github")
    newer = parse_ls_remote_tags(_LS + "3333333333333333333333333333333333333333\trefs/tags/v0.3.19\n")
    assert evaluate_github_tags(src, newer)[:2] == ("update_available", "v0.3.19")

    moved = {"v0.3.18": "9" * 40}
    assert evaluate_github_tags(src, moved)[0] == "pin_moved"

    assert evaluate_github_tags(src, {"v0.3.17": "1" * 40})[0] == "pin_missing"
    for status in ("update_available", "pin_moved", "pin_missing"):
        assert status in ACTIONABLE


def test_pypi_exact_pin() -> None:
    src = _entry("pypi")
    assert src["pin"] == "0.0.1a10"
    assert evaluate_pypi(src, {"info": {"version": "0.0.1a10"}})[0] == "up_to_date"
    assert evaluate_pypi(src, {"info": {"version": "0.0.1a11"}})[:2] == ("update_available", "0.0.1a11")
    assert evaluate_pypi(src, {})[0] == "unknown"
