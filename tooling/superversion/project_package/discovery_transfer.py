"""Append reviewed discovery proposals without creating governed definitions."""
from __future__ import annotations

import hashlib
import json
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .hashes import canonical_sha256
from .repository import ProjectPackageRevisionRepository, RevisionRecord, StaleProjectPackageDraftError


def transfer_discovery(repository: ProjectPackageRevisionRepository, payload: dict[str, Any]) -> RevisionRecord:
    required = {"projectId", "discoveryRevision", "expectedHeadRevisionHash", "candidateKeys", "objectiveKeys", "rationale", "actor", "document"}
    if not isinstance(payload, dict) or set(payload) != required:
        raise ValueError("Invalid discovery transfer request")
    for field in ("discoveryRevision", "expectedHeadRevisionHash"):
        if not isinstance(payload[field], str) or not re.fullmatch(r"[a-f0-9]{64}", payload[field]):
            raise ValueError(f"Invalid {field}")
    if not isinstance(payload["rationale"], str) or not 20 <= len(payload["rationale"].strip()) <= 4000:
        raise ValueError("Review rationale must contain 20 to 4000 characters")
    if not isinstance(payload["actor"], str) or not payload["actor"].strip():
        raise ValueError("Authenticated reviewer required")
    document = payload["document"]
    if not isinstance(document, dict) or document.get("schemaVersion") != 1:
        raise ValueError("Unsupported Discovery document")
    keys = payload["candidateKeys"]
    if not isinstance(keys, list) or not keys or len(keys) > 500 or any(not isinstance(key, str) for key in keys) or len(set(keys)) != len(keys):
        raise ValueError("Select unique candidate keys")
    sources = {source["id"]: source for source in document["sources"]}
    candidates = {f'{item["type"]}:{item["id"]}': item for item in document["candidates"]}
    selected = []
    for key in sorted(keys):
        item = candidates.get(key)
        source = sources.get(item.get("sourceId")) if item else None
        if not item or item.get("status") != "draft" or item.get("evidenceStatus") != "quote-verified" or not source or not item.get("sourceContext") or item["sourceContext"] not in source["content"] or item["source"] != source["name"]:
            raise ValueError(f"Candidate requires an exact verified source quote: {key}")
        selected.append(item)
    objective_keys = payload["objectiveKeys"]
    if not isinstance(objective_keys, list) or len(set(objective_keys)) != len(objective_keys) or any(key not in keys or candidates[key]["type"] != "anchor" for key in objective_keys):
        raise ValueError("Only selected strategy anchors can map to draft objectives")
    current = repository.head()
    if not current or current.revision_hash != payload["expectedHeadRevisionHash"]:
        raise StaleProjectPackageDraftError("Package HEAD changed; review the latest revision before transferring")
    if current.project_ref != payload["projectId"]:
        raise ValueError("Project Package belongs to a different project")
    identity = canonical_sha256({"projectId": payload["projectId"], "discoveryRevision": payload["discoveryRevision"], "candidateKeys": sorted(keys)})
    evidence = [dict(sources[source_id], contentSha256=hashlib.sha256(sources[source_id]["content"].encode("utf-8")).hexdigest()) for source_id in sorted({item["sourceId"] for item in selected})]
    with tempfile.TemporaryDirectory(prefix="discovery-transfer-") as temporary:
        root = repository.checkout(Path(temporary) / "package", current.revision_hash)
        target = root / "discovery" / "reviews" / f"{identity}.json"
        if target.exists():
            raise ValueError("This exact Discovery selection has already been transferred")
        # A candidate is not duplicated by selecting a larger subset on the next click.
        for prior in target.parent.glob("*.json") if target.parent.exists() else []:
            record = json.loads(prior.read_text(encoding="utf-8"))
            if record.get("discovery_revision") == payload["discoveryRevision"] and set(record.get("candidate_keys", [])) & set(keys):
                raise ValueError("One or more candidates from this Discovery revision were already transferred")
        target.parent.mkdir(parents=True, exist_ok=True)
        manifest_path = root / "package.yaml"
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        mappings = []
        if objective_keys:
            opportunity_path = root / next(item["path"] for item in manifest["modules"] if item["module_type"] == "opportunity")
            opportunity = yaml.safe_load(opportunity_path.read_text(encoding="utf-8"))
            for key in objective_keys:
                objective = candidates[key]["name"]
                if objective not in opportunity["objectives"]:
                    opportunity["objectives"].append(objective)
                mappings.append({"candidate_key": key, "module": opportunity_path.relative_to(root).as_posix(), "field": "objectives", "value": objective})
            opportunity["scope_status"] = "draft"
            opportunity.setdefault("source_refs", []).append(target.relative_to(root).as_posix())
            opportunity_path.write_text(json.dumps(opportunity, ensure_ascii=False, indent=2) if opportunity_path.suffix == ".json" else yaml.safe_dump(opportunity, sort_keys=False, allow_unicode=True), encoding="utf-8", newline="\n")
        target.write_text(json.dumps({
            "schema_version": "1.0.0", "record_type": "reviewed_discovery_proposals", "status": "proposed",
            "project_ref": payload["projectId"], "discovery_revision": payload["discoveryRevision"],
            "reviewed_against_package_revision": current.revision_hash, "candidate_keys": sorted(keys),
            "reviewed_by": payload["actor"], "reviewed_at": datetime.now(timezone.utc).isoformat(),
            "review_rationale": payload["rationale"].strip(), "candidates": selected, "sources": evidence,
            "draft_module_mappings": mappings,
            "authority": "Evidence review only. Not customer approval, a governed registry mapping, an architecture decision or deployment authorization.",
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        manifest["state"] = "working"
        manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8", newline="\n")
        return repository.commit_draft(root, expected_head_hash=current.revision_hash)
