# Phase 1 Plan: Publish & Automate Container Image Distribution

**Sprint:** External Maturity Sprint  
**Date:** 2026-03-31  
**Status:** Implementation-complete, evidence-closure pending first live tag run  
**Impact:** Production Readiness 6 -> 7/10

---

## Objective

Publish official container images for Terminal Zero Governance and make them consumable by external operators.

Primary success outcome:

```bash
docker pull ghcr.io/<org>/terminal-zero-governance:latest
docker run --rm ghcr.io/<org>/terminal-zero-governance:latest sop healthcheck
```

---

## Scope

### In scope
- CI publish workflow for GHCR + Docker Hub
- Release-tag publish path with signing + SBOM
- Edge publish path for main/master
- Semver bump/tag automation workflow
- Registry README (`docs/deploy/image-registry.md`)
- Docs updates:
  - `docs/getting-started.md`
  - `docs/deploy/aws-eks.md`
  - `docs/deploy/azure-aks.md`
  - `docs/deploy/gcp-gke.md`

### Out of scope
- Multi-arch (`arm64`) release images
- Vulnerability scan gating
- Helm chart publication automation

---

## Baseline / Current State

- `.github/workflows/publish-images.yml` present and patched with manual-dispatch mode/ref guard.
- `.github/workflows/release-bump-and-tag.yml` present and patched with no-op commit guard.
- `.github/workflows/release-validation.yml` present.
- `docs/deploy/image-registry.md` present and updated with release-entry policy.
- Phase owner artifact present in working repo: `docs/context/phase_scope_phase1.md`.
- Evidence doc present as readiness state: `docs/evidence/phase1_image_publish_evidence.md`.

---

## Workflow Behavior Clarification

Release entrypoint policy:
- Primary release entrypoint: `.github/workflows/release-bump-and-tag.yml`
- `.github/workflows/publish-images.yml` manual dispatch is controlled operator use only.

`publish-images.yml` behavior:
- Tag refs (`v*`) -> full publish/sign/SBOM path.
- Branch refs -> edge publish path.
- Manual dispatch requires explicit `mode` (`edge` or `release`) and validates mode/ref compatibility.

---

## Deliverables

- [x] `.github/workflows/publish-images.yml` present
- [x] `.github/workflows/release-bump-and-tag.yml` present
- [x] `.github/workflows/release-validation.yml` present
- [x] `docs/deploy/image-registry.md` present
- [x] `docs/getting-started.md` container quickstart present
- [x] `docs/deploy/aws-eks.md` image-first flow present
- [x] `docs/deploy/azure-aks.md` image-first flow present
- [x] `docs/deploy/gcp-gke.md` image-first flow present
- [x] `docs/evidence/phase1_image_publish_evidence.md` readiness state present
- [ ] First live release-tag run evidence appended (digest/signature/SBOM/run IDs)

---

## Acceptance Gates

1. `docker pull ghcr.io/<org>/terminal-zero-governance:latest` succeeds.
2. `docker pull docker.io/<org>/terminal-zero-governance:latest` succeeds.
3. Image digest stable across repeated pulls.
4. `cosign download sbom` succeeds on published GHCR image.
5. `cosign verify` succeeds for GHCR release image.
6. Publish workflow run is green on release tag push.
7. `sop healthcheck` in container exits 0.
8. Evidence doc includes live run IDs/URLs/timestamps and Evidence Footer.

---

## Remaining Closure Steps

1. Trigger Release Bump and Tag once in GitHub.
2. Confirm tag-triggered `release-validation.yml` passes.
3. Confirm tag-triggered `publish-images.yml` passes.
4. Append live outputs to `docs/evidence/phase1_image_publish_evidence.md`:
   - tag
   - image refs
   - digest
   - `cosign verify` output
   - SBOM retrieval output
   - smoke output
   - workflow URLs / run IDs / timestamps
5. Re-mark Phase 1 as fully closed.

---

## Risk Notes

- Missing Docker Hub secrets will fail Docker Hub publication.
- Phase 1 is currently **PASS for implementation** and **BLOCK for final closure** until live proof is appended.
