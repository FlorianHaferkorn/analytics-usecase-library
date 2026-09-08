# Pinned project input release

Status: implemented bounded input-release seam. Not platform deployment.

## Authority and workflow

1. Load a saved Project Package revision. Project identity must match the selected Studio project.
2. Review the exact revision. Python validates the package and decisions; the package must already be approved with no unresolved decision blockers.
3. A project administrator explicitly attests release with a written rationale and confirmation. Actor identity comes from the authenticated session, not request data.
4. Download the exact snapshot, deterministic compiler input and immutable release record as an input JSON bundle. Every file retains its SHA-256 and base64 content; the release binds project, revision and compiler-input SHA-256.

The release CLI holds the same repository lock as commits while checking HEAD and recording the attestation. A stale, cross-project, unapproved or modified release is blocked. The first attestation is never silently replaced. Subsequent downloads require viewer access and the same approved HEAD. HTTP GET never creates an attestation.

## Chosen boundary

Reuse the Python Project Package authority and existing Studio project roles. Do not infer customer acceptance from a library quality gate or create a second TypeScript decision compiler. Approved-input download is useful for controlled handoff even while platform adapters are not package-bound.

Global target generation is explicitly a **library preview**. Project export aliases return an authenticated conflict rather than reading mutable global catalogs under a customer URL. Fabric/PBIR/OSI target adapters are not yet wired to pinned Project Package compiler inputs. An input bundle is therefore not a complete deployable tenant blueprint.

## Persistence and limits

Release attestations are append-only sidecar files in the configured Project Package data root (`repositories/release-attestations/<project>/`). They must be backed up together with that data root. Package history ZIPs intentionally do not carry local release attestations; imported history requires a fresh authorized attestation. Local hashes detect corruption and accidental modification; they are not cryptographic signatures against a malicious host administrator. No automatic role grants, approval writes to customer decisions or tenant deployment occur.

## Evidence

- Python repository tests cover real approved snapshot release, no-attestation blocking, immutable repeat download, unapproved/stale/cross-project rejection and modified-record detection.
- Studio route tests cover admin/viewer separation, authenticated actor binding, explicit confirmation, pinned hash headers and stale responses.
- Global exporter tests prove that project-scoped requests never enter the mutable library generator.
- No customer data was approved or deployed during implementation.
