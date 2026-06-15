# Supply Chain & Security for Adapters / MCP (Operating Standard)

## Purpose

Define the minimum security and supply-chain requirements for:

- tool adapters (`products/<tool>/…`)
- MCP servers integrated via an internal marketplace/registry
- AI-first automation that can deploy or operate tools

This is a **binding operating standard**.

## Non-negotiable requirements

### 1) No secrets in the repository

- Secrets must never be stored in `core/`, `products/`, `tooling/`, or `internal/`.
- Adapter manifests may declare `required_secrets`, but values are resolved at runtime from a secret store.

### 2) Signed artifacts

Every adapter/server package must be signed at build time and verified at install time:

- container images: signed and verified before execution
- zip/npm/pypi artifacts: signed and verified before installation

### 3) SBOM + provenance

Each published adapter/server version must provide:

- an SBOM reference (CycloneDX or SPDX)
- build provenance / attestation (who built what, from which commit, with which toolchain)

### 4) Least privilege permissions

- Permissions must be declared in the adapter manifest (high-level).
- The runner must enforce least privilege:
  - separate identities for build vs deploy
  - separate environments (dev/test/prod) with strict access boundaries

### 5) Auditability

For every operation (install/update/build/validate/deploy), emit immutable audit events:

- who/what executed (agent identity)
- what version (adapter/server)
- inputs (IR/core ABI version)
- outputs (checksums, reports)
- environment target

## Threat model (pragmatic)

- **Supply chain poisoning**: malicious adapter update → prevent via signing + allowlist + pinning.
- **Permission escalation**: adapter deploy uses broad credentials → prevent via least privilege + environment separation.
- **Silent semantic drift**: AI changes meaning indirectly → prevent via gates + human approval for semantics.
- **Data exfiltration**: MCP server reads more than allowed → prevent via explicit permissions, network egress controls, and auditing.

## Enforcement points

- Internal registry/marketplace verifies signatures, SBOM presence, compatibility, and allowlist status.
- CI pipelines produce attestations and publish artifacts.
- Deploy gates (e.g., contract + registry strict) block risky releases.

## Related documents

- Core Constitution: `core_constitution.md`
- Core ABI: `reference/core_abi.md`
- IR: `tooling/ir/`
- Adapter manifest schema: `products/adapters/adapter_manifest.schema.json`

---

## Sources & Grounding

The supply-chain controls in this standard — signed artifacts, build provenance/attestation,
SBOMs, and secure-development practices — mirror the prevailing industry frameworks for
software supply-chain integrity. Grounded in:

- **SLSA (Supply-chain Levels for Software Artifacts)** (build-track levels, provenance, and
  attestation that underpin the "signed artifacts" + "SBOM + provenance" requirements) —
  official specification: <https://slsa.dev/spec/v1.0/levels> · OpenSSF project page:
  <https://openssf.org/projects/slsa/>
- **NIST SSDF, SP 800-218** (Secure Software Development Framework — the secure-build and
  least-privilege practices behind this standard) — NIST CSRC:
  <https://csrc.nist.gov/pubs/sp/800/218/final>
- **SBOM (Software Bill of Materials)** (the "SBOM reference" requirement, including the NTIA
  minimum-elements lineage) — CISA: <https://www.cisa.gov/sbom>
- **CycloneDX** (OWASP / Ecma ECMA-424 SBOM format accepted by this standard) —
  <https://cyclonedx.org/> · **SPDX** (Linux Foundation / ISO/IEC 5962 SBOM format accepted by
  this standard) — <https://spdx.dev/>
- **Sigstore** (keyless signing + transparency log, the reference toolchain for "signed and
  verified" artifacts) — <https://www.sigstore.dev/>
- **OpenSSF (Open Source Security Foundation)** (umbrella for SLSA, Sigstore, and supply-chain
  best practices) — <https://openssf.org/>

> These are external reference frameworks. This document remains a **binding internal operating
> standard**: where a framework offers options, the requirements above (signing, SBOM+provenance,
> least privilege, auditability) are the enforced floor for this repository.

