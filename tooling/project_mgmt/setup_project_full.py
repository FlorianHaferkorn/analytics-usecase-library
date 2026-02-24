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

GRAPHQL_URL = "https://api.github.com/graphql"
REST_BASE = "https://api.github.com"

# Granular backlog: title, body snippet, milestone, area, priority, labels (e.g. ["epic"])
GRANULAR_ISSUES = [
    # Project completion
    {"title": "[Task] Resolve blockers from content review (company_strategy anchors, factsheet paths)", "milestone": "Project completion", "area": "Docs", "priority": "P0", "labels": [], "body": "From presentation_status_and_roadmap. Blocker resolution."},
    {"title": "[Task] Remaining review adjustments (style, link-backs, encoding)", "milestone": "Project completion", "area": "Docs", "priority": "P1", "labels": [], "body": "Review adjustments for project completion."},
    {"title": "[Task] Document CI/release without Stage-1 skip", "milestone": "Project completion", "area": "Tooling", "priority": "P1", "labels": [], "body": "Zero-tolerance documentation: CI/release without Stage-1 skip."},
    # Framework Package 1 (Demo Friday: P0 = must, P1 = should, P2 = optional)
    {"title": "[Epic] Framework Package 1 complete: Aurora customer-ready (Fabric/Power BI)", "milestone": "Framework Package 1", "area": "FabricPowerBI", "priority": "P1", "labels": ["epic"], "body": "Abschluss erstes Framework-Paket. Aurora zeigt: bei Kunden ohne Probleme/Bugs einsetzbar; reproduzierbar inkl. neuer Use Cases. Out of Scope: Evidence, andere Tools; Fabric Capacity; Generators/Interfaces. AC: PBIP opens, no known blockers, docs, page templates."},
    {"title": "[Task] Reproducible pipeline: Use Cases to PBIP (Aurora, configurable use-case set)", "milestone": "Framework Package 1", "area": "FabricPowerBI", "priority": "P0", "labels": [], "body": "Script/workflow from Use Case Inventory + Brackets to Aurora PBIP (configurable use-case set). Demo Friday: must-have."},
    {"title": "[Task] Verification: PBIP opens in Power BI Desktop; report and model load", "milestone": "Framework Package 1", "area": "FabricPowerBI", "priority": "P0", "labels": [], "body": "Check: Aurora PBIP opens in Power BI Desktop; report and model load without error. AC: Report pages show visual placeholders (KPI, Trend, Variance) and open without error."},
    {"title": "[Task] Report output: open generated report with CoreActionReady.SemanticModel (minimal .pbip or doc)", "milestone": "Framework Package 1", "area": "FabricPowerBI", "priority": "P0", "labels": [], "body": "Minimal .pbip for dist/<UC>.Report + CoreActionReady.SemanticModel, or clear doc how to open generated report with showcase model. Demo Friday: must-have."},
    {"title": "[Task] Verification: Pages align with page templates", "milestone": "Framework Package 1", "area": "FabricPowerBI", "priority": "P0", "labels": [], "body": "Verify pages align with core/templates/page_templates."},
    {"title": "[Task] Customer readiness checklist and known blockers", "milestone": "Framework Package 1", "area": "Docs", "priority": "P1", "labels": [], "body": "Customer readiness checklist; document prerequisites (versions, steps); capture known blockers."},
    {"title": "[Task] Add one new use case and regenerate Aurora report (reproducibility proof)", "milestone": "Framework Package 1", "area": "FabricPowerBI", "priority": "P2", "labels": [], "body": "Add one new (or defined) use case; run pipeline; Aurora report regenerates and opens without error. Proof: works with new use cases. Demo Friday: optional."},
    # Phase 2 – 3-30-300
    {"title": "[Epic] 3-30-300 complete: 300s page from action-code YAML", "milestone": "Phase 2", "area": "FabricPowerBI", "priority": "P1", "labels": ["epic"], "body": "Parent epic. 300s page shows action text and evidence from action-code YAML; generated from framework."},
    {"title": "[Task] Define 300s page layout in page template (layout_330300)", "milestone": "Phase 2", "area": "FabricPowerBI", "priority": "P1", "labels": [], "body": "core/templates/page_templates. Define 300s page layout."},
    {"title": "[Task] Generate action text from action-code YAML in report", "milestone": "Phase 2", "area": "FabricPowerBI", "priority": "P1", "labels": [], "body": "Action payload in 300s page from action-code YAML."},
    {"title": "[Task] Generate evidence table from data contract / action payload", "milestone": "Phase 2", "area": "FabricPowerBI", "priority": "P1", "labels": [], "body": "Evidence table for 300s page."},
    {"title": "[Task] Wire 300s page into report scaffold (Aurora)", "milestone": "Phase 2", "area": "FabricPowerBI", "priority": "P1", "labels": [], "body": "Report structure: 300s page in Aurora scaffold."},
    {"title": "[Task] Integration test: 300s page end-to-end", "milestone": "Phase 2", "area": "FabricPowerBI", "priority": "P2", "labels": [], "body": "Verify full 300s flow."},
    # Phase 2 – Strategy Pattern
    {"title": "[Epic] Strategy Pattern / AI urgency and automated reasoning", "milestone": "Phase 2", "area": "Framework", "priority": "P2", "labels": ["epic"], "body": "Parent epic. Strategy pattern precise enough for tooling; AI urgency and automated reasoning scope."},
    {"title": "[Task] Document urgency rules in strategy_patterns.md", "milestone": "Phase 2", "area": "Framework", "priority": "P2", "labels": [], "body": "core/strategy_operating_model/company. Urgency rules in strategy_patterns.md."},
    {"title": "[Task] Add tooling hook for urgency derivation (stub or spec)", "milestone": "Phase 2", "area": "Tooling", "priority": "P2", "labels": [], "body": "Optional automation for urgency derivation."},
    {"title": "[Task] Document automated reasoning scope and limits", "milestone": "Phase 2", "area": "Docs", "priority": "P2", "labels": [], "body": "internal/vision or strategy. Automated reasoning scope."},
    # Technical – MCP / Fabric
    {"title": "[Task] Call Power BI MCP table_operations from table_ops.ps1", "milestone": "Technical backlog", "area": "Tooling", "priority": "P2", "labels": [], "body": "tooling/powerbi_mcp/table_ops.ps1 ~line 138."},
    {"title": "[Task] Call Power BI MCP relationship_operations from relationship_ops.ps1", "milestone": "Technical backlog", "area": "Tooling", "priority": "P2", "labels": [], "body": "relationship_ops.ps1 ~line 199."},
    {"title": "[Task] Fabric: Workspace API (GET/POST) in deploy.ps1", "milestone": "Technical backlog", "area": "Tooling", "priority": "P2", "labels": [], "body": "deploy.ps1 – Workspace API."},
    {"title": "[Task] Fabric: Import PBIP/TMDL to semantic model API in deploy.ps1", "milestone": "Technical backlog", "area": "Tooling", "priority": "P2", "labels": [], "body": "deploy.ps1 – Import PBIP/TMDL."},
    {"title": "[Task] Fabric: Publish report and bind to dataset in deploy.ps1", "milestone": "Technical backlog", "area": "Tooling", "priority": "P2", "labels": [], "body": "deploy.ps1 – Publish report, bind to dataset."},
    {"title": "[Task] Fabric: Set refresh schedule via REST in deploy.ps1", "milestone": "Technical backlog", "area": "Tooling", "priority": "P2", "labels": [], "body": "deploy.ps1 – Refresh schedule."},
    {"title": "[Task] Fabric: Apply RLS / security_user_org mapping via API in deploy.ps1", "milestone": "Technical backlog", "area": "Tooling", "priority": "P2", "labels": [], "body": "deploy.ps1 – RLS/security_user_org."},
    {"title": "[Task] TMDL: default format strings and display folders (AUTOMATION_FLOW)", "milestone": "Technical backlog", "area": "Tooling", "priority": "P2", "labels": [], "body": "tooling/powerbi_mcp/AUTOMATION_FLOW.md."},
    {"title": "[Task] Update relationship via MCP (AUTOMATION_FLOW)", "milestone": "Technical backlog", "area": "Tooling", "priority": "P2", "labels": [], "body": "AUTOMATION_FLOW.md – relationship via MCP."},
    {"title": "[Task] Generate visuals from template (AUTOMATION_FLOW)", "milestone": "Technical backlog", "area": "Tooling", "priority": "P2", "labels": [], "body": "AUTOMATION_FLOW.md – visuals from template."},
    # Technical – Aurora
    {"title": "[Task] Aurora Operations model: complete relationships and measures (Operations.yaml)", "milestone": "Technical backlog", "area": "Aurora", "priority": "P1", "labels": [], "body": "showcases/aurora_group/models/Operations.yaml."},
    {"title": "[Task] Aurora Operations model: DAX in KPI Catalog, Measure_Dictionary", "milestone": "Technical backlog", "area": "Aurora", "priority": "P1", "labels": [], "body": "Operations domain – DAX and Measure_Dictionary."},
    {"title": "[Task] Aurora Finance model: complete relationships and measures (Finance.yaml)", "milestone": "Technical backlog", "area": "Aurora", "priority": "P1", "labels": [], "body": "showcases/aurora_group/models/Finance.yaml."},
    {"title": "[Task] Aurora Finance model: DAX in KPI Catalog, Measure_Dictionary", "milestone": "Technical backlog", "area": "Aurora", "priority": "P1", "labels": [], "body": "Finance domain – DAX and Measure_Dictionary."},
    # Technical – Synthetic
    {"title": "[Task] Synthetic: ensure Lakehouse exists before notebook run (create or doc)", "milestone": "Technical backlog", "area": "Tooling", "priority": "P2", "labels": [], "body": "fabric_nb_generate_backbone_core_v1.py."},
    {"title": "[Task] Synthetic: implement date range with Spark (backbone notebook)", "milestone": "Technical backlog", "area": "Tooling", "priority": "P2", "labels": [], "body": "Backbone notebook – date range."},
    {"title": "[Task] Synthetic: derive from sales + config.inventory (target_dio_range, coverage days)", "milestone": "Technical backlog", "area": "Tooling", "priority": "P2", "labels": [], "body": "Backbone notebook."},
    {"title": "[Task] Synthetic: implement join + ratio, Category join + GM% band check", "milestone": "Technical backlog", "area": "Tooling", "priority": "P2", "labels": [], "body": "Backbone notebook."},
    {"title": "[Task] Synthetic: RI dim_* vs facts, margin bands, DIO/CCC bands", "milestone": "Technical backlog", "area": "Tooling", "priority": "P2", "labels": [], "body": "Backbone notebook."},
    {"title": "[Task] Synthetic: Lakehouse and schema exist; map dims/facts to config.lakehouse.tables", "milestone": "Technical backlog", "area": "Tooling", "priority": "P2", "labels": [], "body": "Backbone notebook."},
    {"title": "[Task] Synthetic: optional holiday logic for is_holiday in generate_gold_layer.py", "milestone": "Technical backlog", "area": "Tooling", "priority": "P2", "labels": [], "body": "generate_gold_layer.py line 121."},
    # Technical – Page scaffold
    {"title": "[Task] Page scaffold: BOM support in YAML scanner", "milestone": "Technical backlog", "area": "Tooling", "priority": "P2", "labels": [], "body": "scanner.py line 187."},
    {"title": "[Task] Page scaffold: tab handling rules in YAML scanner", "milestone": "Technical backlog", "area": "Tooling", "priority": "P2", "labels": [], "body": "scanner.py line 761."},
]


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
