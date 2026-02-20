#!/usr/bin/env python3
"""
Weekly Project status update: queries the repo-scope GitHub Project (V2),
computes progress and at-risk heuristics, and creates a draft status update
via createProjectV2StatusUpdate. Human reviews and publishes in the Project UI.

Requires: GITHUB_TOKEN (repo + project scope), GITHUB_REPOSITORY (owner/repo),
          PROJECT_NUMBER (default 1). Run from repo root or set env.
"""

import os
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from collections import defaultdict

GRAPHQL_URL = "https://api.github.com/graphql"


def gql(req: dict, token: str) -> dict:
    data = json.dumps(req).encode("utf-8")
    r = urllib.request.Request(
        GRAPHQL_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(r) as res:
        return json.loads(res.read().decode("utf-8"))


def get_project_id(owner: str, repo: str, number: int, token: str) -> str:
    q = """
    query($owner: String!, $repo: String!, $number: Int!) {
      repository(owner: $owner, name: $repo) {
        projectV2(number: $number) { id }
      }
    }
    """
    out = gql({"query": q, "variables": {"owner": owner, "repo": repo, "number": number}}, token)
    err = out.get("errors")
    if err:
        raise RuntimeError("GraphQL errors: " + json.dumps(err))
    pid = out.get("data", {}).get("repository", {}).get("projectV2", {}).get("id")
    if not pid:
        raise RuntimeError("Project not found. Check owner, repo, and PROJECT_NUMBER.")
    return pid


ALIASED_ITEMS_QUERY = """
query($id: ID!, $after: String) {
  node(id: $id) {
    ... on ProjectV2 {
      items(first: 100, after: $after) {
        nodes {
          content {
            ... on Issue { number title url }
          }
          statusField: fieldValueByName(name: "Status") {
            ... on ProjectV2ItemFieldSingleSelectValue { name }
          }
          milestoneField: fieldValueByName(name: "Milestone") {
            ... on ProjectV2ItemFieldSingleSelectValue { name }
          }
          priorityField: fieldValueByName(name: "Priority") {
            ... on ProjectV2ItemFieldSingleSelectValue { name }
          }
          riskField: fieldValueByName(name: "Risk") {
            ... on ProjectV2ItemFieldSingleSelectValue { name }
          }
          targetDateField: fieldValueByName(name: "Target date") {
            ... on ProjectV2ItemFieldDateValue { date }
          }
          blockedByField: fieldValueByName(name: "Blocked by") {
            ... on ProjectV2ItemFieldTextValue { text }
          }
        }
        pageInfo { endCursor hasNextPage }
      }
    }
  }
}
"""


def collect_items_v2(project_id: str, token: str) -> list[dict]:
    items = []
    cursor = None
    while True:
        variables = {"id": project_id, "after": cursor}
        out = gql({"query": ALIASED_ITEMS_QUERY, "variables": variables}, token)
        err = out.get("errors")
        if err:
            raise RuntimeError("GraphQL errors: " + json.dumps(err))
        node = out.get("data", {}).get("node", {})
        items_block = node.get("items", {})
        nodes = items_block.get("nodes", [])
        for n in nodes:
            content = n.get("content") or {}
            items.append({
                "number": content.get("number"),
                "title": content.get("title") or "",
                "url": content.get("url") or "",
                "Status": (n.get("statusField") or {}).get("name"),
                "Milestone": (n.get("milestoneField") or {}).get("name") or "—",
                "Priority": (n.get("priorityField") or {}).get("name"),
                "Risk": (n.get("riskField") or {}).get("name"),
                "Target date": (n.get("targetDateField") or {}).get("date"),
                "Blocked by": ((n.get("blockedByField") or {}).get("text") or "").strip() or None,
            })
        pi = items_block.get("pageInfo", {})
        if not pi.get("hasNextPage"):
            break
        cursor = pi.get("endCursor")
        if not cursor:
            break
    return items


def build_summary(items: list[dict]) -> tuple[str, str]:
    """Returns (body_markdown, status_enum). status_enum is ON_TRACK or AT_RISK."""
    by_milestone = defaultdict(lambda: {"done": 0, "total": 0})
    overdue_p0 = []
    blocked_p0 = []
    at_risk_items = []
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    for i in items:
        milestone = i.get("Milestone") or "—"
        by_milestone[milestone]["total"] += 1
        status = (i.get("Status") or "").strip()
        if status == "Done":
            by_milestone[milestone]["done"] += 1
        if (i.get("Priority") or "").strip() == "P0" and status and status != "Done":
            target = i.get("Target date")
            if target and target < today:
                overdue_p0.append((i.get("number"), i.get("title")))
            blocked = i.get("Blocked by")
            if blocked and blocked.lower() not in ("none", "n/a", ""):
                blocked_p0.append((i.get("number"), i.get("title")))
        if (i.get("Risk") or "").strip() == "At risk":
            at_risk_items.append((i.get("number"), i.get("title")))

    lines = [
        f"**Weekly status** ({datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC)",
        "",
        "## Progress by milestone",
        "",
    ]
    for milestone in sorted(by_milestone.keys()):
        d = by_milestone[milestone]
        pct = (d["done"] / d["total"] * 100) if d["total"] else 0
        lines.append(f"- **{milestone}**: {d['done']}/{d['total']} ({pct:.0f}%)")
    lines.append("")
    if overdue_p0:
        lines.append("## Overdue P0")
        lines.append("")
        for num, title in overdue_p0[:10]:
            lines.append(f"- #{num} {title}")
        lines.append("")
    if blocked_p0:
        lines.append("## Blocked P0")
        lines.append("")
        for num, title in blocked_p0[:10]:
            lines.append(f"- #{num} {title}")
        lines.append("")
    if at_risk_items:
        lines.append("## Marked At risk")
        lines.append("")
        for num, title in at_risk_items[:10]:
            lines.append(f"- #{num} {title}")
        lines.append("")

    lines.append("---")
    lines.append("*Review and publish this update in the Project. Adjust status (On track / At risk) if needed.*")

    body = "\n".join(lines)
    status_enum = "AT_RISK" if (overdue_p0 or blocked_p0 or at_risk_items) else "ON_TRACK"
    return body, status_enum


def create_status_update(project_id: str, body: str, status_enum: str, token: str) -> None:
    mut = """
    mutation($projectId: ID!, $body: String!, $status: ProjectV2StatusUpdateStatus!) {
      createProjectV2StatusUpdate(input: { projectId: $projectId, body: $body, status: $status }) {
        statusUpdate { id }
      }
    }
    """
    variables = {"projectId": project_id, "body": body, "status": status_enum}
    out = gql({"query": mut, "variables": variables}, token)
    err = out.get("errors")
    if err:
        raise RuntimeError("createProjectV2StatusUpdate failed: " + json.dumps(err))
    print("Status update created. Review and publish in the Project.", file=sys.stderr)


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("Set GITHUB_TOKEN (or GH_TOKEN) with repo and project scope.", file=sys.stderr)
        sys.exit(1)
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if "/" not in repo:
        print("Set GITHUB_REPOSITORY to owner/repo.", file=sys.stderr)
        sys.exit(1)
    owner, repo_name = repo.split("/", 1)
    project_number = int(os.environ.get("PROJECT_NUMBER", "1"))

    project_id = get_project_id(owner, repo_name, project_number, token)
    items = collect_items_v2(project_id, token)
    body, status_enum = build_summary(items)
    create_status_update(project_id, body, status_enum, token)
    print(body)


if __name__ == "__main__":
    main()
