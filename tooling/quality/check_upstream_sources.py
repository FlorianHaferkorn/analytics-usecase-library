"""Check allowlisted upstream sources for new versions of BPA rules and external references.

Allowed source registry (allowlist only -- never pulls unapproved sources):
  - TabularEditor/BestPracticeRules  (bpa-rules-semanticmodel.json)
  - data-goblin/power-bi-agentic-development (reviewed upstream reference, read-only)
  - microsoft/skills-for-fabric  (kind ``github``: pinned release tag, Meridian D-603)
  - PyPI fabric-notebook-toolkit (kind ``pypi``: internal dev tool only, Meridian D-603)

Source kinds (``kind``; absent = the GitHub REST probe via ``api_url``):
  - ``github`` -- a repo consumed by release tag (e.g. the Claude Code marketplace ref in
    ``.claude/settings.json``). Read via ``git ls-remote --tags`` (no token, no rate limit),
    three findings as in Meridian ``scripts/check_upstream_freshness.py``: pinned tag missing,
    pinned tag moved off the pinned commit (the ref would pull unreviewed content), newer
    SemVer tag. Reports, never bumps.
  - ``pypi`` -- a package pinned to an exact version; newer ``info.version`` is reported.

Usage:
    python tooling/quality/check_upstream_sources.py [--summary] [--output PATH]

Exit codes:
  0  All sources up-to-date or check inconclusive (network unavailable).
  1  New versions available for one or more allowlisted sources.
  2  Configuration error.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ALLOWLIST = [
    {
        "id": "bpa.tabular_editor",
        "name": "TabularEditor BPA Rules",
        "source": "TabularEditor/BestPracticeRules",
        "api_url": "https://api.github.com/repos/TabularEditor/BestPracticeRules/releases/latest",
        "local_pin_comment": "tooling/linters/powerbi/bpa-rules-semanticmodel.json",
        "review_required": True,
        "license": "MIT",
        "last_checked": "2026-05",
        "local_owner": "fabric",
    },
    {
        "id": "ref.data_goblin",
        "name": "data-goblin power-bi-agentic-development",
        "source": "data-goblin/power-bi-agentic-development",
        "api_url": "https://api.github.com/repos/data-goblin/power-bi-agentic-development/commits/main",
        "local_pin_comment": "docs/agent/skills/ (reviewed upstream reference)",
        "review_required": True,
        "license": "MIT",
        "last_checked": "2026-05",
        "local_owner": "fabric",
    },
    {
        # Pinned since 30.09.2026 (Meridian D-603, decision Florian): the marketplace
        # ``fabric-collection`` in .claude/settings.json uses ``ref`` = ``pin``, autoUpdate off.
        # Claude Code pins a marketplace source only by ref (branch/tag); the tag can move,
        # hence ``commit``. Measured 30.09.2026 via ``git ls-remote --tags``:
        # refs/tags/v0.3.18 = 6c11ad58c25992e5d1435ce7cd80d217d5598a31. A bump changes
        # settings.json and this entry in the same commit (peer test
        # tooling/tests/test_upstream_sources_pins.py).
        "id": "ref.skills_for_fabric",
        "name": "Microsoft skills-for-fabric",
        "kind": "github",
        "source": "microsoft/skills-for-fabric",
        "repo": "microsoft/skills-for-fabric",
        "pin": "v0.3.18",
        "commit": "6c11ad58c25992e5d1435ce7cd80d217d5598a31",
        "api_url": "https://github.com/microsoft/skills-for-fabric.git (git ls-remote --tags)",
        "local_pin_comment": ".claude/settings.json (extraKnownMarketplaces.fabric-collection) "
                             "+ .ruler/ shims + docs/architecture/adr/0002",
        "tools": ["fabric-skills@fabric-collection"],
        # Off until its MCP server can be pinned: powerbi-authoring starts
        # ``npx @microsoft/powerbi-modeling-mcp@latest`` (decision Florian 30.09.2026).
        "disabled_tools": ["powerbi-authoring@fabric-collection"],
        "review_required": True,
        "license": "MIT",
        "last_checked": "2026-09-30",
        "local_owner": "fabric",
    },
    {
        # Meridian D-603: internal developer tool only (dev workspaces, own loop).
        # Proprietary pre-release licence (no redistribution, 2e). Never in products/,
        # tooling/, core/, requirements*.txt or .github/ -- enforced by
        # tooling/check_fntk_boundary.py (Stage 1).
        "id": "pkg.fabric_notebook_toolkit",
        "name": "Fabric Notebook Toolkit (fntk)",
        "kind": "pypi",
        "source": "pypi:fabric-notebook-toolkit",
        "package": "fabric-notebook-toolkit",
        "pin": "0.0.1a10",
        "api_url": "https://pypi.org/pypi/fabric-notebook-toolkit/json",
        "local_pin_comment": "docs/agent/agent-developer-tools.md (internal only)",
        "review_required": True,
        "license": "Microsoft pre-release licence (no redistribution)",
        "last_checked": "2026-09-30",
        "local_owner": "fabric",
    },
]

_LS_REMOTE_TIMEOUT_S = 30

ACTIONABLE = ("update_available", "check_manually", "pin_missing", "pin_moved")

OUTPUT_PATH = Path("internal/reviews/upstream_sources_report.md")


def _fetch_json(url: str) -> dict | None:
    """Fetch JSON from a URL; return None on error."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "pbi-quality-tools/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception:  # noqa: BLE001
        return None


def _semver(tag: str) -> tuple[int, ...] | None:
    """``v0.3.18`` -> (0, 3, 18); pre-releases and foreign formats -> None (never "latest")."""
    core = tag[1:] if tag[:1] in ("v", "V") else tag
    parts = core.split(".")
    if not parts or not all(p.isdigit() for p in parts):
        return None
    return tuple(int(p) for p in parts)


def latest_semver_tag(tags: dict[str, str]) -> str | None:
    candidates = [(v, t) for t in tags if (v := _semver(t)) is not None]
    return max(candidates)[1] if candidates else None


def parse_ls_remote_tags(out: str) -> dict[str, str]:
    """``git ls-remote --tags`` output -> {tag: commit}. For annotated tags the peeled
    entry ``tag^{}`` carries the commit and wins over the tag-object hash."""
    tags: dict[str, str] = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) != 2 or not parts[1].startswith("refs/tags/"):
            continue
        sha, name = parts[0], parts[1][len("refs/tags/"):]
        if name.endswith("^{}"):
            tags[name[:-3]] = sha
        else:
            tags.setdefault(name, sha)
    return tags


def evaluate_github_tags(source: dict, tags: dict[str, str]) -> tuple[str, str | None, str]:
    """Pure core of the ``github`` kind: (status, remote_version, message).

    ``pin_missing`` / ``pin_moved`` are actionable like ``update_available``; a moved tag
    matters most, because the settings ``ref`` would then pull unreviewed content.
    """
    repo, pin, commit = source["repo"], str(source["pin"]), str(source.get("commit", ""))
    latest = latest_semver_tag(tags)
    if pin not in tags:
        return "pin_missing", latest, f"{repo}: pinned tag {pin} no longer exists upstream."
    if commit and not tags[pin].startswith(commit):
        return ("pin_moved", tags[pin][:12],
                f"{repo}: tag {pin} now points to {tags[pin][:12]}, pinned is {commit[:12]} "
                "-- tag moved, content unreviewed.")
    pin_v, latest_v = _semver(pin), _semver(latest) if latest else None
    if latest and pin_v is not None and latest_v is not None and latest_v > pin_v:
        return ("update_available", latest,
                f"{repo}: pin {pin} -> newest tag {latest}. Read CHANGELOG, bump settings + pin together.")
    return "up_to_date", pin, f"{repo}: tag {pin} = {tags[pin][:12]}, newest SemVer tag."


def _github_tags(repo: str) -> dict[str, str] | None:
    """{tag: commit} via ``git ls-remote``; None = git missing or unreachable (soft skip)."""
    git = shutil.which("git")
    if git is None:
        return None
    try:
        proc = subprocess.run(
            [git, "ls-remote", "--tags", f"https://github.com/{repo}.git"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
            timeout=_LS_REMOTE_TIMEOUT_S, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    return parse_ls_remote_tags(proc.stdout)


def evaluate_pypi(source: dict, data: dict) -> tuple[str, str | None, str]:
    """Pure core of the ``pypi`` kind: exact pin vs ``info.version``."""
    remote = (data.get("info") or {}).get("version")
    if not remote:
        return "unknown", None, "Unexpected PyPI response shape."
    pin = str(source["pin"])
    if remote == pin:
        return "up_to_date", remote, f"{source['package']}=={pin} is the latest release."
    return ("update_available", remote,
            f"{source['package']}: pin {pin} -> latest {remote}. Re-check licence, telemetry "
            "switches and `fntk init` behaviour before bumping.")


def check_source(source: dict) -> dict:
    """Check one source entry for new versions. Returns a result dict."""
    kind = source.get("kind")
    if kind == "github":
        result = {"id": source["id"], "name": source["name"], "api_url": source["api_url"],
                  "status": "unknown", "remote_version": None, "message": ""}
        tags = _github_tags(source["repo"])
        if tags is None:
            result.update(status="unreachable", message="git ls-remote unavailable.")
            return result
        result["status"], result["remote_version"], result["message"] = \
            evaluate_github_tags(source, tags)
        return result
    if kind == "pypi":
        result = {"id": source["id"], "name": source["name"], "api_url": source["api_url"],
                  "status": "unknown", "remote_version": None, "message": ""}
        data = _fetch_json(source["api_url"])
        if data is None:
            result.update(status="unreachable", message="Network unavailable or rate-limited.")
            return result
        result["status"], result["remote_version"], result["message"] = \
            evaluate_pypi(source, data)
        return result

    result = {
        "id": source["id"],
        "name": source["name"],
        "api_url": source["api_url"],
        "status": "unknown",
        "remote_version": None,
        "message": "",
    }

    data = _fetch_json(source["api_url"])
    if data is None:
        result["status"] = "unreachable"
        result["message"] = "Network unavailable or rate-limited."
        return result

    if "tag_name" in data:
        result["remote_version"] = data["tag_name"]
        result["status"] = "update_available"
        result["message"] = f"Latest release: {data['tag_name']}. Review before updating local pin."
    elif "sha" in data:
        result["remote_version"] = data["sha"][:8]
        result["status"] = "check_manually"
        result["message"] = f"Latest commit: {data['sha'][:8]}. Review upstream changes before adopting."
    else:
        result["status"] = "unknown"
        result["message"] = "Unexpected API response shape."

    return result


def generate_report(results: list[dict], *, summary: bool = False) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Upstream Sources Report",
        "",
        f"Generated: {now}",
        "",
        "## Allowlisted Sources",
        "",
        "| ID | Source | Status | Remote Version | Notes |",
        "|---|---|---|---|---|",
    ]
    for r in results:
        status = r["status"]
        ver = r.get("remote_version") or "-"
        msg = r.get("message", "")
        lines.append(f"| `{r['id']}` | {r['name']} | {status} | `{ver}` | {msg} |")

    lines.append("")
    lines.append("## Policy")
    lines.append("")
    lines.append("- **Review required** before adopting any upstream change.")
    lines.append("- Every imported rule/skill must have: `source`, `license`, `last_checked`, `local_owner`, `review_status`.")
    lines.append("- Never auto-apply upstream changes. Create a PR and assign a human reviewer.")
    lines.append("")

    if not summary:
        lines.append("## Source Details")
        lines.append("")
        for r in results:
            lines.append(f"### {r['name']}")
            lines.append(f"- API: {r['api_url']}")
            lines.append(f"- Status: {r['status']}")
            lines.append(f"- Remote version: {r.get('remote_version') or 'unknown'}")
            lines.append(f"- Note: {r.get('message', '')}")
            lines.append("")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", action="store_true",
                        help="Compact output.")
    parser.add_argument("--output", default=str(OUTPUT_PATH), metavar="PATH",
                        help="Write Markdown report to this path.")
    args = parser.parse_args(argv)

    results = [check_source(src) for src in ALLOWLIST]
    report = generate_report(results, summary=args.summary)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8", newline="\n")

    if args.summary:
        updates = [r for r in results if r["status"] in ACTIONABLE]
        print(f"Upstream sources checked: {len(results)}. Updates/reviews needed: {len(updates)}.")
        for r in updates:
            print(f"  {r['id']}: {r['message']}")
    else:
        print(report)

    print(f"Report written: {out}")

    # Exit 1 if any source has actionable updates
    if any(r["status"] in ACTIONABLE for r in results):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
