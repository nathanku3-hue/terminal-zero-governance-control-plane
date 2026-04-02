# Phase 1 Scope — Publish & Distribute Official Artifacts

**Phase ID:** `phase1`  
**Status:** `implementation_complete_evidence_pending`  
**Canonical Phase:** `true`

## Contract

- **hard_dependencies:** `[]`
- **soft_dependencies:** `[]`
- **parallel_safe_with:** `["phase3", "phase4", "phase6"]`
- **owns_artifacts:** `["docs/context/phase_scope_phase1.md", "docs/evidence/phase1_image_publish_evidence.md"]`
- **consumes_artifacts:** `[]`

## Execution Intent

Establish trusted distribution for official Terminal Zero Governance container artifacts:

- release-tag publish to GHCR + Docker Hub
- keyless image signing (cosign + OIDC)
- SBOM generation + attestation
- release validation and semver/tag automation

## Completion Semantics

This phase is considered **fully closed** only when first live release-tag evidence is appended to:

- `docs/evidence/phase1_image_publish_evidence.md`

Required live evidence fields:

- pushed tag
- workflow run IDs/URLs/timestamps
- published image references + digest
- `cosign verify` output
- `cosign download sbom` output
- smoke-test output
