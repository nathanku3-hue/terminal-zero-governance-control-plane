# Phase 1 Image Publish Evidence

**Date:** 2026-03-31  
**Phase:** Phase 1 — Publish & Distribute Official Artifacts  
**Owner Artifact:** `docs/context/phase_scope_phase1.md`  
**Status:** Implementation-complete, awaiting first live tag-run proof

## Scope

This evidence records Phase A implementation readiness for:

- GHCR + Docker Hub publish workflow (`.github/workflows/publish-images.yml`)
- keyless signing (`cosign sign`)
- SBOM generation + attestation (`anchore/sbom-action`, `cosign attest`)
- release validation gate (`.github/workflows/release-validation.yml`)
- semver bump/tag automation (`.github/workflows/release-bump-and-tag.yml`)

## Workflow Correctness Patches Applied

1. `release-bump-and-tag.yml`: commit/tag path hardened for no-op commit case.
2. `publish-images.yml`: manual dispatch now requires explicit `mode` and validates mode/ref compatibility.
3. Operational policy clarified in docs: release entrypoint is **Release Bump and Tag**; manual publish dispatch is controlled operator use only.

## Current Evidence (Readiness)

- Publish workflow present and tag/edge split implemented
- Release validation workflow present
- Signing + SBOM/attest path present
- Registry and deployment docs updated
- Phase 1 owner artifact now present: `docs/context/phase_scope_phase1.md`

## Live Tag-Run Evidence (Required for final closure)

> Pending first production tag execution.

### To append after first live run

- **Tag pushed:** `<vX.Y.Z>`
- **Release Bump and Tag run:** `<URL>` | `<run-id>` | `<timestamp UTC>`
- **Release Validation run:** `<URL>` | `<run-id>` | `<timestamp UTC>`
- **Publish Images run:** `<URL>` | `<run-id>` | `<timestamp UTC>`
- **Published image refs:**
  - `ghcr.io/<org>/terminal-zero-governance:<tag>`
  - `docker.io/<org>/terminal-zero-governance:<tag>`
- **Published digest:** `<sha256:...>`
- **cosign verify output:** `<paste command + output>`
- **SBOM retrieval output:** `<paste cosign download sbom output>`
- **Smoke-test output:** `<paste sop healthcheck/sop version output>`

## Fresh Validation Metadata (local)

- **Date (UTC):** 2026-03-31
- **Interpreter:** Python 3.14.0
- **Command:** `python -m pytest -q`
- **Result:** 1102 passed, 5 skipped, 2 failed
- **Failure scope:** `tests/test_phase10_cleanup.py` expects root-level matrix schema (`phase-status-matrix/v1`) not aligned with current root `docs/context/phase_status_matrix_latest.json`

## Evidence Footer

**Observability**: 4/5  
**Evidence Paths**: `docs/evidence/phase1_image_publish_evidence.md`; `docs/context/phase_scope_phase1.md`; `.github/workflows/release-bump-and-tag.yml`; `.github/workflows/publish-images.yml`  
**Validation Results**: `PhaseAImplementationValidation: PASS`; `PhaseAClosureValidation: BLOCK (awaiting first live tag-run evidence)`; `LocalPytest: BLOCK (1102 passed, 5 skipped, 2 failed)`  
**Run Metadata**: Date: 2026-03-31; Python: 3.14.0; Tests: 1102 passed, 5 skipped, 2 failed
