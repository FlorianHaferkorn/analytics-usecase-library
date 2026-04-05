#!/usr/bin/env python3
"""
Full project setup: create granular milestones, labels, issues; add every issue
to the repo-scope GitHub Project and set Status, Milestone, Area, Priority, Risk.

Requires: GITHUB_TOKEN (repo + project scope), PROJECT_NUMBER (default 1).
          GITHUB_REPOSITORY or git remote origin for owner/repo.
Run from repo root. See internal/project_mgmt/WHAT_I_NEED.md.
"""

import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

GRAPHQL_URL = "https://api.github.com/graphql"
REST_BASE = "https://api.github.com"

# Single source of truth: same file as PowerShell sync and list_granular_issues.ps1
_JSON_PATH = Path(__file__).resolve().parent / "granular_issues.json"
with open(_JSON_PATH, "r", encoding="utf-8") as f:
    GRANULAR_ISSUES = json.load(f)


def gql(req: dict, token: str) -> dict:
    data = json.dumps(req).encode("utf-8")
    r = urllib.request.Request(
        GRAPHQL_URL, data=data,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(r) as res:
        out = json.loads(res.read().decode("utf-8"))
    if out.get("errors"):
        raise RuntimeError("GraphQL errors: " + json.dumps(out["errors"]))
    return out


def rest(method: str, path: str, token: str, body: dict = None) -> dict:
    url = REST_BASE + path
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
        r = urllib.request.Request(url, data=data, headers=headers, method=method)
    else:
        r = urllib.request.Request(url, headers=headers, method=method)
    with urllib.request.urlopen(r) as res:
        return json.loads(res.read().decode("utf-8"))


def get_repo(token: str) -> tuple[str, str]:
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if repo and "/" in repo:
        return tuple(repo.split("/", 1))
    try:
        with open(".git/config", "r", encoding="utf-8") as f:
            content = f.read()
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("url = ") and "github.com" in line:
                url = line.split("=", 1)[1].strip()
                if "github.com:" in url:
                    part = url.split("github.com:")[1].rstrip("/")
                else:
                    part = url.split("github.com/")[1].rstrip("/")
                part = part.replace(".git", "")
                if "/" in part:
                    return tuple(part.split("/", 1))
    except Exception:
        pass
    raise RuntimeError("Set GITHUB_REPOSITORY to owner/repo or run from repo with origin pointing to GitHub.")


def ensure_milestones(owner: str, repo: str, token: str) -> dict[str, int]:
    wanted = ["Project completion", "Framework Package 1", "Phase 2", "Technical backlog"]
    existing = rest("GET", f"/repos/{owner}/{repo}/milestones?state=all", token)
    by_title = {m["title"]: m["number"] for m in existing}
    out = {}
    for title in wanted:
        if title in by_title:
            out[title] = by_title[title]
            print(f"  Milestone exists: {title} (#{by_title[title]})")
        else:
            created = rest("POST", f"/repos/{owner}/{repo}/milestones", token, {"title": title})
            out[title] = created["number"]
            print(f"  Created milestone: {title} (#{created['number']})")
    return out


def ensure_labels(owner: str, repo: str, token: str) -> None:
    existing = rest("GET", f"/repos/{owner}/{repo}/labels", token)
    names = {lb["name"] for lb in existing}
    for name, color, desc in [("epic", "7C4DFF", "Epic"), ("bug", "d73a4a", "Bug"), ("blocker", "b60205", "Blocker")]:
        if name not in names:
            rest("POST", f"/repos/{owner}/{repo}/labels", token, {"name": name, "color": color, "description": desc})
            print(f"  Created label: {name}")


def create_issues(owner: str, repo: str, token: str, milestones: dict[str, int]) -> list[dict]:
    created = []
    for item in GRANULAR_ISSUES:
        ms_num = milestones.get(item["milestone"])
        body = f"**Milestone:** {item['milestone']} | **Area:** {item['area']} | **Priority:** {item['priority']}\n\n{item['body']}"
        payload = {"title": item["title"], "body": body, "labels": item["labels"], "milestone": ms_num}
        issue = rest("POST", f"/repos/{owner}/{repo}/issues", token, payload)
        created.append({"number": issue["number"], "node_id": issue["node_id"], "title": issue["title"], "milestone": item["milestone"], "area": item["area"], "priority": item["priority"]})
        print(f"  Created issue #{issue['number']}: {item['title'][:60]}...")
    return created


def get_project_and_fields(owner: str, repo: str, project_number: int, token: str) -> tuple[str, dict]:
    scope = os.environ.get("PROJECT_SCOPE", "repo").lower()
    if scope == "user":
        # User-level project: https://github.com/users/FlorianHaferkorn/projects/2
        project_owner = os.environ.get("PROJECT_OWNER", owner)
        q = """
        query($login: String!, $number: Int!) {
          user(login: $login) {
            projectV2(number: $number) {
              id
              fields(first: 30) {
                nodes {
                  __typename
                  ... on ProjectV2SingleSelectField {
                    id
                    name
                    options {
                      id
                      name
                    }
                  }
                }
              }
            }
          }
        }
        """
        out = gql({"query": q, "variables": {"login": project_owner, "number": project_number}}, token)
        proj = out["data"]["user"]["projectV2"] if out.get("data", {}).get("user") else None
    else:
        q = """
        query($owner: String!, $repo: String!, $number: Int!) {
          repository(owner: $owner, name: $repo) {
            projectV2(number: $number) {
              id
              fields(first: 30) {
                nodes {
                  __typename
                  ... on ProjectV2SingleSelectField {
                    id
                    name
                    options {
                      id
                      name
                    }
                  }
                }
              }
            }
          }
        }
        """
        out = gql({"query": q, "variables": {"owner": owner, "repo": repo, "number": project_number}}, token)
        proj = out["data"]["repository"]["projectV2"] if out.get("data", {}).get("repository") else None
    if not proj:
        raise RuntimeError("Project not found. Check PROJECT_NUMBER and PROJECT_SCOPE (user vs repo).")
    project_id = proj["id"]
    field_map = {}
    for node in proj["fields"]["nodes"]:
        if node.get("__typename") == "ProjectV2SingleSelectField" and node.get("options"):
            opts = {opt["name"]: opt["id"] for opt in node["options"]}
            field_map[node["name"]] = {"id": node["id"], "options": opts}
    return project_id, field_map


def add_item_to_project(project_id: str, content_id: str, token: str) -> str:
    q = """
    mutation($projectId: ID!, $contentId: ID!) {
      addProjectV2ItemById(input: { projectId: $projectId, contentId: $contentId }) {
        projectItem { id }
      }
    }
    """
    out = gql({"query": q, "variables": {"projectId": project_id, "contentId": content_id}}, token)
    return out["data"]["addProjectV2ItemById"]["projectItem"]["id"]


def set_single_select(project_id: str, item_id: str, field_id: str, option_id: str, token: str) -> None:
    q = """
    mutation($input: UpdateProjectV2ItemFieldValueInput!) {
      updateProjectV2ItemFieldValue(input: $input) { projectItem { id } }
    }
    """
    gql({"query": q, "variables": {"input": {"projectId": project_id, "itemId": item_id, "fieldId": field_id, "value": {"singleSelectOptionId": option_id}}}}, token)


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        try:
            import subprocess
            token = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=False).stdout.strip()
        except Exception:
            pass
    if not token:
        print("Set GITHUB_TOKEN or GH_TOKEN (repo + project scope). See internal/project_mgmt/WHAT_I_NEED.md.", file=sys.stderr)
        sys.exit(1)
    project_number = int(os.environ.get("PROJECT_NUMBER", "1"))
    owner, repo = get_repo(token)
    print(f"Repo: {owner}/{repo} | Project number: {project_number}")

    print("\n1. Milestones")
    milestones = ensure_milestones(owner, repo, token)
    print("\n2. Labels")
    ensure_labels(owner, repo, token)
    print("\n3. Issues (granular)")
    issues = create_issues(owner, repo, token, milestones)

    print("\n4. Project: add items and set fields")
    project_id, field_map = get_project_and_fields(owner, repo, project_number, token)
    status_field = field_map.get("Status")
    milestone_field = field_map.get("Milestone")
    area_field = field_map.get("Area")
    priority_field = field_map.get("Priority")
    risk_field = field_map.get("Risk")
    if not all([status_field, milestone_field, area_field, priority_field]):
        print("  WARNING: Project is missing required fields (Status, Milestone, Area, Priority). Add them in Project Settings -> Fields. Skipping field updates.", file=sys.stderr)
    else:
        for i in issues:
            item_id = add_item_to_project(project_id, i["node_id"], token)
            if status_field and "Backlog" in status_field.get("options", {}):
                set_single_select(project_id, item_id, status_field["id"], status_field["options"]["Backlog"], token)
            if milestone_field and i["milestone"] in milestone_field.get("options", {}):
                set_single_select(project_id, item_id, milestone_field["id"], milestone_field["options"][i["milestone"]], token)
            if area_field and i["area"] in area_field.get("options", {}):
                set_single_select(project_id, item_id, area_field["id"], area_field["options"][i["area"]], token)
            if priority_field and i["priority"] in priority_field.get("options", {}):
                set_single_select(project_id, item_id, priority_field["id"], priority_field["options"][i["priority"]], token)
            if risk_field and "On track" in risk_field.get("options", {}):
                set_single_select(project_id, item_id, risk_field["id"], risk_field["options"]["On track"], token)
            print(f"  Added #{i['number']} to project, set Status/Milestone/Area/Priority")
    print("\nDone. Issues:", [i["number"] for i in issues])


if __name__ == "__main__":
    main()
