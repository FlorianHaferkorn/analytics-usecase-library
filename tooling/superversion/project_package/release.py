"""Explicit release attestations for immutable, approved Project Package inputs.

These records approve the input bundle only, not generated target artifacts or
tenant deployment. Studio authenticates the actor before invoking this seam.
"""

from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .compiler_input import build_compiler_input
from .hashes import canonical_sha256
from .repository import (
    ProjectPackageRevisionRepository, StaleProjectPackageDraftError,
    _repository_lock, _inventory,
)


def release_input(repository: ProjectPackageRevisionRepository, project_ref: str,
                  revision_hash: str, *, actor: str | None = None,
                  rationale: str | None = None) -> dict[str, Any]:
    """Attest once (actor present), or export an existing attestation (read-only).

    Use the same lock as commits so HEAD cannot move between validation and
    attestation. Records live beside repositories; history format stays intact.
    """
    with _repository_lock(repository.root):
        head = repository._head_unlocked()
        if head is None or head.revision_hash != revision_hash:
            raise StaleProjectPackageDraftError("Selected revision is no longer HEAD; review the latest version before release")
        record = repository._get_unlocked(revision_hash)
        if record.project_ref != project_ref:
            raise ValueError("Package project_ref does not match the selected project")
        compiler_input = build_compiler_input(record.package_root, repository.schema_root)
        if not compiler_input["readiness"]["build_ready"]:
            raise ValueError("Release blocked: " + ", ".join(compiler_input["readiness"]["blockers"]))
        input_hash = canonical_sha256(compiler_input)
        release_root = repository.root.parent / "release-attestations" / repository.root.name
        if release_root.is_symlink() or release_root.parent.is_symlink():
            raise ValueError("Release record directory cannot be a symbolic link")
        release_path = release_root / f"{revision_hash}.json"
        if release_path.is_symlink():
            raise ValueError("Release record cannot be a symbolic link")
        if not release_path.exists():
            if actor is None:
                raise ValueError("Release blocked: this revision has no explicit release attestation")
            if not actor.strip() or not rationale or not 20 <= len(rationale.strip()) <= 2000:
                raise ValueError("A named actor and a 20–2000 character release rationale are required")
            approval = {
                "schema_version": "1.0.0", "scope": "approved_project_input_bundle",
                "project_ref": project_ref, "revision_hash": revision_hash,
                "compiler_input_sha256": input_hash, "attested_by": actor,
                "attested_at": datetime.now(timezone.utc).isoformat(),
                "rationale": rationale.strip(),
            }
            approval["record_sha256"] = canonical_sha256(approval)
            release_root.mkdir(parents=True, exist_ok=True)
            with release_path.open("x", encoding="utf-8") as handle:
                json.dump(approval, handle, ensure_ascii=False, sort_keys=True)
        approval = json.loads(release_path.read_text(encoding="utf-8"))
        claimed_hash = approval.get("record_sha256")
        content = {key: value for key, value in approval.items() if key != "record_sha256"}
        if (canonical_sha256(content) != claimed_hash
                or approval.get("revision_hash") != revision_hash
                or approval.get("project_ref") != project_ref
                or approval.get("scope") != "approved_project_input_bundle"
                or approval.get("compiler_input_sha256") != input_hash):
            raise ValueError("Release record integrity or pinned compiler input mismatch")
        files = [dict(item, encoding="base64", contentBase64=base64.b64encode(
            (record.package_root / item["path"]).read_bytes()).decode("ascii"))
            for item in _inventory(record.package_root)]
        return {
            "release": approval, "compiler_input": compiler_input, "files": files,
            "output_type": "approved_project_input_bundle",
            "limitations": ["Not generated Fabric, Power BI or other platform deployment artifacts",
                            "No tenant validation, deployment approval or customer acceptance is implied"],
        }
