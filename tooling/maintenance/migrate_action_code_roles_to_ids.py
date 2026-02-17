#!/usr/bin/env python3
"""
Lean 2.0 maintenance: normalize Action Code governance roles to Org-Registry role IDs.

Goal:
- Action Codes must store `owner_role` / `steward_role` as role IDs (snake_case),
  not human titles.
- All referenced role IDs must exist in the org role registry (see path below).

Strategy:
1) Load org role registry (ids, titles, aliases).
2) For each Action Code YAML in core/action_codes/**:
   - Map current owner_role/steward_role:
     - If already an org role id -> keep
     - Else if matches an existing title/alias (case-insensitive) -> replace with that id
     - Else create a new role entry (id derived from title) and replace with that id
3) Write updated org_roles.yaml and Action Code YAML files (only with --apply).
4) Print a summary and exit non-zero if unresolved roles remain (should not happen).
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
# Framework-context only: use core org_roles (this script may write new roles there).
# For validation against a full customer list, use registry/Stage 1 (showcase override).
ORG_ROLES_PATH = REPO_ROOT / "core" / "organization" / "org_roles.yaml"
ACTION_CODES_ROOT = REPO_ROOT / "core" / "action_codes"


def slugify_role_id(title: str) -> str:
    s = title.strip().lower()
    # normalize common separators
    s = s.replace("&", " and ")
    s = s.replace("/", " ")
    s = s.replace("-", " ")
    # remove non-alphanum/underscore/space
    s = re.sub(r"[^a-z0-9_\s]+", "", s)
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    if not s:
        s = "role"
    if not re.match(r"^[a-z]", s):
        s = f"role_{s}"
    return s


def read_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def write_yaml(path: Path, data: Any) -> None:
    # Keep YAML stable and readable
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


@dataclass
class OrgRoleIndex:
    roles: List[Dict[str, Any]]
    ids: set[str]
    by_name_lower: Dict[str, str]  # title/alias -> id


def build_org_index(org_data: Dict[str, Any]) -> OrgRoleIndex:
    roles = org_data.get("roles") or []
    if not isinstance(roles, list):
        raise ValueError("org_roles.yaml must contain a top-level list at key 'roles'.")
    ids: set[str] = set()
    by_name_lower: Dict[str, str] = {}
    for r in roles:
        if not isinstance(r, dict):
            continue
        rid = r.get("id")
        if isinstance(rid, str) and rid.strip():
            rid = rid.strip()
            ids.add(rid)
            title = r.get("title")
            if isinstance(title, str) and title.strip():
                by_name_lower[title.strip().lower()] = rid
            for a in (r.get("aliases") or []):
                if isinstance(a, str) and a.strip():
                    by_name_lower[a.strip().lower()] = rid
    return OrgRoleIndex(roles=roles, ids=ids, by_name_lower=by_name_lower)


def ensure_unique_id(base: str, existing: set[str]) -> str:
    if base not in existing:
        return base
    i = 2
    while f"{base}_{i}" in existing:
        i += 1
    return f"{base}_{i}"


def infer_domain(action_owner_domain: Optional[str]) -> str:
    if isinstance(action_owner_domain, str) and action_owner_domain.strip():
        return action_owner_domain.strip()
    return "Enterprise"


def normalize_role_value(
    raw_value: Any,
    *,
    index: OrgRoleIndex,
    roles_to_add: List[Dict[str, Any]],
    action_owner_domain: Optional[str],
) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Returns (role_id, new_role_dict_if_created).
    """
    if not isinstance(raw_value, str):
        return None, None
    v = raw_value.strip()
    if not v:
        return None, None
    # already an id?
    if v in index.ids:
        return v, None
    # match by title/alias
    mapped = index.by_name_lower.get(v.lower())
    if mapped:
        return mapped, None
    # create new role
    base_id = slugify_role_id(v)
    new_id = ensure_unique_id(base_id, index.ids)
    domain = infer_domain(action_owner_domain)
    new_role = {
        "id": new_id,
        "title": v,
        "domain": domain,
        "aliases": [v],
    }
    # update index in-memory
    index.ids.add(new_id)
    index.by_name_lower[v.lower()] = new_id
    roles_to_add.append(new_role)
    return new_id, new_role


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Write changes to disk.")
    args = ap.parse_args()

    if not ORG_ROLES_PATH.exists():
        raise SystemExit(f"Missing org roles registry: {ORG_ROLES_PATH}")

    org_data = read_yaml(ORG_ROLES_PATH)
    if not isinstance(org_data, dict):
        raise SystemExit("org_roles.yaml must be a YAML mapping/object.")

    index = build_org_index(org_data)
    roles_to_add: List[Dict[str, Any]] = []

    action_paths = sorted([p for p in ACTION_CODES_ROOT.rglob("*.yaml") if p.is_file()])
    changed_actions: List[Path] = []
    created_roles: List[Dict[str, Any]] = []

    for p in action_paths:
        data = read_yaml(p)
        if not isinstance(data, dict):
            continue
        owner_domain = data.get("owner_domain")
        changed = False
        for key in ("owner_role", "steward_role"):
            rid, new_role = normalize_role_value(
                data.get(key),
                index=index,
                roles_to_add=roles_to_add,
                action_owner_domain=owner_domain,
            )
            if new_role:
                created_roles.append(new_role)
            if rid and data.get(key) != rid:
                data[key] = rid
                changed = True
        if changed:
            changed_actions.append(p)
            if args.apply:
                write_yaml(p, data)

    if roles_to_add:
        # append roles at end; keep schema_version
        org_data["roles"] = (org_data.get("roles") or []) + roles_to_add
        if args.apply:
            write_yaml(ORG_ROLES_PATH, org_data)

    print(f"Action codes scanned: {len(action_paths)}")
    print(f"Action codes updated: {len(changed_actions)}")
    print(f"New org roles created: {len(roles_to_add)}")
    if roles_to_add:
        print("New role IDs:")
        for r in roles_to_add[:50]:
            print(f"- {r['id']}  ({r.get('domain')})  title={r.get('title')}")
        if len(roles_to_add) > 50:
            print(f"... {len(roles_to_add) - 50} more")

    if not args.apply:
        print("\nDry-run only. Re-run with --apply to write changes.")


if __name__ == "__main__":
    main()

