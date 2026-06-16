"""Check allowlisted upstream sources for new versions of BPA rules and external references.

Allowed source registry (allowlist only -- never pulls unapproved sources):
  - TabularEditor/BestPracticeRules  (bpa-rules-semanticmodel.json)
  - data-goblin/power-bi-agentic-development (reviewed upstream reference, read-only)

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
        "id": "ref.skills_for_fabric",
        "name": "Microsoft skills-for-fabric",
        "source": "microsoft/skills-for-fabric",
        "api_url": "https://api.github.com/repos/microsoft/skills-for-fabric/commits/main",
        "local_pin_comment": ".ruler/ shims + docs/architecture/adr/0002 (official-first overlay)",
        "review_required": True,
        "license": "MIT",
        "last_checked": "2026-06",
        "local_owner": "fabric",
    },
]

OUTPUT_PATH = Path("internal/reviews/upstream_sources_report.md")


def _fetch_json(url: str) -> dict | None:
    """Fetch JSON from a URL; return None on error."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "pbi-quality-tools/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception:  # noqa: BLE001
        return None


def check_source(source: dict) -> dict:
    """Check one source entry for new versions. Returns a result dict."""
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
    out.write_text(report, encoding="utf-8")

    if args.summary:
        updates = [r for r in results if r["status"] in ("update_available", "check_manually")]
        print(f"Upstream sources checked: {len(results)}. Updates/reviews needed: {len(updates)}.")
        for r in updates:
            print(f"  {r['id']}: {r['message']}")
    else:
        print(report)

    print(f"Report written: {out}")

    # Exit 1 if any source has actionable updates
    if any(r["status"] in ("update_available", "check_manually") for r in results):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
