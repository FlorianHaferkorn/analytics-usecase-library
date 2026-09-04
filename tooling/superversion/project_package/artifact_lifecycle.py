"""Deterministic projections for the project artifact and publication lifecycle."""

from __future__ import annotations

import hashlib
from copy import deepcopy
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


class ArtifactLifecycleError(ValueError):
    """Raised when a publication projection cannot be produced safely."""


def _local_path(package_root: Path, ref: str) -> Path | None:
    relative = Path(ref)
    if relative.is_absolute():
        raise ArtifactLifecycleError(f"local artifact ref must be relative: {ref!r}")
    parsed = urlparse(ref)
    if parsed.scheme:
        return None
    resolved = (package_root / relative).resolve()
    try:
        resolved.relative_to(package_root.resolve())
    except ValueError as exc:
        raise ArtifactLifecycleError(f"local artifact ref escapes package root: {ref!r}") from exc
    return resolved


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reconcile_artifact_files(package_root: Path, registry: dict[str, Any]) -> list[str]:
    """Compare every package-local source and projection with its recorded raw-file hash."""
    errors: list[str] = []
    checks: list[tuple[str, str, str]] = []
    for artifact in registry.get("artifacts", []):
        checks.append((artifact["id"], artifact["source_ref"], artifact["source_sha256"]))
        checks.extend(
            (output["id"], output["output_ref"], output["sha256"])
            for output in artifact.get("generated_outputs", [])
        )

    for artifact_ref, file_ref, expected_hash in checks:
        try:
            path = _local_path(package_root, file_ref)
        except ArtifactLifecycleError as exc:
            errors.append(str(exc))
            continue
        if path is None:
            continue
        if not path.is_file():
            errors.append(f"artifact {artifact_ref!r} local file is missing: {file_ref}")
            continue
        actual_hash = _file_sha256(path)
        if actual_hash != expected_hash:
            errors.append(
                f"artifact {artifact_ref!r} file hash drift: {file_ref} "
                f"expected {expected_hash}, actual {actual_hash}"
            )
    return errors


def render_artifact_index(registry: dict[str, Any]) -> str:
    """Render a stable human-readable inventory from the machine-readable registry."""
    rows = [
        "# Artifact inventory",
        "",
        "This file is generated from the Project Package artifact registry. Do not edit it directly.",
        "",
        "| Artifact | Audience | Authority | Content | Publication | Customer decision | Revision |",
        "|---|---|---|---|---|---|---:|",
    ]
    for artifact in sorted(registry.get("artifacts", []), key=lambda item: item["id"]):
        title = artifact["title"].replace("|", "\\|").replace("\n", " ")
        rows.append(
            "| "
            + " | ".join(
                [
                    f"{title} (`{artifact['id']}`)",
                    artifact["audience"],
                    artifact["authority"],
                    artifact["content_state"],
                    artifact["publication_state"],
                    artifact["customer_decision"]["state"],
                    str(artifact["revision"]),
                ]
            )
            + " |"
        )
    rows.append("")
    return "\n".join(rows)


def build_publication_manifest(registry: dict[str, Any], event_id: str) -> dict[str, Any]:
    """Freeze the exact artifact revision and distribution evidence for one event."""
    events = [event for event in registry.get("publication_events", []) if event.get("id") == event_id]
    if len(events) != 1:
        raise ArtifactLifecycleError(f"expected exactly one publication event {event_id!r}")
    event = events[0]

    artifacts = [
        artifact
        for artifact in registry.get("artifacts", [])
        if artifact.get("id") == event.get("artifact_ref")
    ]
    if len(artifacts) != 1:
        raise ArtifactLifecycleError(
            f"event {event_id!r} does not resolve to exactly one artifact"
        )
    artifact = artifacts[0]
    if event["artifact_revision"] != artifact["revision"]:
        raise ArtifactLifecycleError(
            f"event {event_id!r} does not describe the current artifact revision"
        )

    return {
        "schema_version": "1.0.0",
        "event": {
            key: deepcopy(event[key])
            for key in (
                "id",
                "event_type",
                "occurred_at",
                "actor_ref",
                "channel",
                "destination_ref",
                "file_ref",
                "file_sha256",
                "evidence_refs",
            )
        },
        "artifact": {
            "id": artifact["id"],
            "title": artifact["title"],
            "revision": artifact["revision"],
            "audience": artifact["audience"],
            "authority": artifact["authority"],
            "source_ref": artifact["source_ref"],
            "source_sha256": artifact["source_sha256"],
            "content_state": artifact["content_state"],
            "publication_state": artifact["publication_state"],
            "customer_decision_state": artifact["customer_decision"]["state"],
            "decision_refs": deepcopy(artifact["decision_refs"]),
            "evidence_refs": deepcopy(artifact["evidence_refs"]),
        },
    }
