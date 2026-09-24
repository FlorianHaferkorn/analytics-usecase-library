"""Emit a fail-closed Microsoft Fabric External Data Share delivery runtime.

The generated runtime uses only the documented v1 REST endpoints. It never embeds tokens and
refuses every mutation until the generated contract is explicitly completed and approved.
"""
from __future__ import annotations

import json
import re


_CONTRACT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["schema_version", "status", "apply_authorized", "provider", "recipient",
                 "consumer", "access", "evidence"],
    "additionalProperties": False,
    "properties": {
        "$schema": {"type": "string"},
        "schema_version": {"const": "1.0"},
        "status": {"enum": ["draft", "ready", "approved"]},
        "apply_authorized": {"type": "boolean"},
        "provider": {"type": "object"},
        "recipient": {"type": "object"},
        "consumer": {"type": "object"},
        "access": {"const": "read_only"},
        "evidence": {"type": "array", "minItems": 1, "items": {"type": "string"}},
    },
}


_RUNTIME = r'''#!/usr/bin/env python3
"""Create, accept, inventory or revoke a Fabric External Data Share.

Tokens are supplied at runtime through FABRIC_PROVIDER_TOKEN and FABRIC_CONSUMER_TOKEN. Every
Fabric request carries the skill attribution header required by the generator's delivery policy.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

BASE = "https://api.fabric.microsoft.com/v1"
SKILL_HEADER = "e2e-medallion-architecture"


def _request(method, url, token, payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "x-ms-fabric-skill": SKILL_HEADER,
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
    for attempt in range(4):
        try:
            with urlopen(Request(url, data=data, headers=headers, method=method), timeout=60) as response:
                body = response.read().decode("utf-8")
                return json.loads(body) if body else {}
        except HTTPError as error:
            if error.code == 429 and attempt < 3:
                time.sleep(int(error.headers.get("Retry-After", "10")))
                continue
            detail = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Fabric API {method} {url} failed: HTTP {error.code}: {detail}") from error
    raise RuntimeError("Fabric API retry budget exhausted")


def _load(path, mutation):
    contract = json.loads(Path(path).read_text(encoding="utf-8"))
    if mutation and (contract.get("status") != "approved" or contract.get("apply_authorized") is not True):
        raise ValueError("mutation blocked: set status=approved and apply_authorized=true after sign-off")
    return contract


def _require(obj, *keys):
    missing = [key for key in keys if obj.get(key) in (None, "", [], {})]
    if missing:
        raise ValueError("missing required contract values: " + ", ".join(missing))


def _recipient(raw):
    if raw.get("type") == "User":
        _require(raw, "user_principal_name")
        return {"type": "User", "userPrincipalName": raw["user_principal_name"],
                **({"tenantId": raw["tenant_id"]} if raw.get("tenant_id") else {})}
    if raw.get("type") == "ServicePrincipal":
        _require(raw, "principal_id", "tenant_id")
        return {"type": "ServicePrincipal", "principalId": raw["principal_id"],
                "tenantId": raw["tenant_id"]}
    raise ValueError("recipient.type must be User or ServicePrincipal")


def create(contract, token, dry_run=False):
    provider = contract["provider"]
    _require(provider, "workspace_id", "item_id", "paths")
    body = {"paths": provider["paths"], "recipient": _recipient(contract["recipient"])}
    url = f"{BASE}/workspaces/{provider['workspace_id']}/items/{provider['item_id']}/externalDataShares"
    if dry_run:
        return {"method": "POST", "url": url, "body": body}
    return _request("POST", url, token, body)


def accept(contract, token, invitation_id, dry_run=False):
    provider = contract["provider"]
    consumer = contract["consumer"]
    _require(provider, "tenant_id")
    _require(consumer, "workspace_id", "item_id", "target_path", "shortcut_names")
    detail_url = (f"{BASE}/externalDataShares/invitations/{invitation_id}"
                  f"?providerTenantId={quote(provider['tenant_id'])}")
    details = _request("GET", detail_url, token)
    requests = []
    for path in details.get("pathsDetails", []):
        name = path.get("name")
        shortcut_name = consumer["shortcut_names"].get(name)
        if not shortcut_name:
            raise ValueError(f"consumer.shortcut_names has no approved name for shared path {name!r}")
        requests.append({"pathId": path["pathId"], "shortcutName": shortcut_name})
    if not requests:
        raise ValueError("invitation contains no paths")
    body = {
        "providerTenantId": provider["tenant_id"],
        "workspaceId": consumer["workspace_id"],
        "itemId": consumer["item_id"],
        "payload": {"payloadType": "ShortcutCreation", "path": consumer["target_path"],
                    "createShortcutRequests": requests},
    }
    url = f"{BASE}/externalDataShares/invitations/{invitation_id}/accept"
    if dry_run:
        return {"method": "POST", "url": url, "body": body, "invitationDetails": details}
    return _request("POST", url, token, body)


def inventory(token):
    return _request("GET", f"{BASE}/admin/items/externalDataShares", token)


def revoke(contract, token, share_id, dry_run=False):
    provider = contract["provider"]
    _require(provider, "workspace_id", "item_id")
    url = (f"{BASE}/workspaces/{provider['workspace_id']}/items/{provider['item_id']}"
           f"/externalDataShares/{share_id}/revoke")
    if dry_run:
        return {"method": "POST", "url": url}
    return _request("POST", url, token, {})


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("create", "accept", "inventory", "revoke"))
    parser.add_argument("--contract", required=True)
    parser.add_argument("--invitation-id")
    parser.add_argument("--share-id")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    mutation = args.mode in {"create", "accept", "revoke"}
    contract = _load(args.contract, mutation)
    if args.mode == "accept":
        if not args.invitation_id:
            parser.error("accept requires --invitation-id")
        token = os.environ.get("FABRIC_CONSUMER_TOKEN", "")
        if not token:
            parser.error("FABRIC_CONSUMER_TOKEN is required")
        result = accept(contract, token, args.invitation_id, args.dry_run)
    else:
        token = os.environ.get("FABRIC_PROVIDER_TOKEN", "")
        if not token:
            parser.error("FABRIC_PROVIDER_TOKEN is required")
        if args.mode == "create":
            result = create(contract, token, args.dry_run)
        elif args.mode == "revoke":
            if not args.share_id:
                parser.error("revoke requires --share-id")
            result = revoke(contract, token, args.share_id, args.dry_run)
        else:
            result = inventory(token)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, RuntimeError) as error:
        print(f"external-share: {error}", file=sys.stderr)
        sys.exit(2)
'''


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "share"


def _draft_contract(workspace: str, shares: list[dict]) -> dict:
    candidates = sorted({f"Tables/{s['source_gold_ref']}" for s in shares if s.get("source_gold_ref")})
    return {
        "$schema": "./external_share_contract.schema.json",
        "schema_version": "1.0",
        "status": "draft",
        "apply_authorized": False,
        "provider": {
            "tenant_id": None,
            "workspace_name": workspace,
            "workspace_id": None,
            "item_id": None,
            "paths": [],
            "candidate_paths": candidates,
        },
        "recipient": {"type": "ServicePrincipal", "tenant_id": None, "principal_id": None},
        "consumer": {"workspace_id": None, "item_id": None, "target_path": None,
                     "shortcut_names": {}},
        "access": "read_only",
        "evidence": [
            "https://learn.microsoft.com/rest/api/fabric/core/external-data-shares-provider/create-external-data-share",
            "https://learn.microsoft.com/rest/api/fabric/core/external-data-shares-recipient/accept-external-data-share-invitation",
        ],
    }


def emit_external_share_runtime(bp: dict) -> dict[str, str]:
    """Return one draft contract per provider workspace plus a shared REST runtime."""
    groups: dict[str, list[dict]] = {}
    for share in bp.get("sharing") or []:
        groups.setdefault(str(share.get("workspace") or "<workspace>"), []).append(share)
    if not groups:
        return {}
    out = {
        "sharing/apply_external_share.py": _RUNTIME,
        "sharing/external_share_contract.schema.json": json.dumps(
            _CONTRACT_SCHEMA, indent=2, ensure_ascii=False) + "\n",
    }
    for workspace, shares in sorted(groups.items()):
        contract = _draft_contract(workspace, shares)
        out[f"sharing/external_share_{_slug(workspace)}.json"] = json.dumps(
            contract, indent=2, ensure_ascii=False) + "\n"
    return out
