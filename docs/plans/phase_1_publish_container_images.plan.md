# Phase 1 Plan: Publish & Automate Container Image Distribution

**Sprint:** External Maturity Sprint  
**Date:** 2026-03-31  
**Status:** Ready to execute  
**Impact:** Production Readiness 6 -> 7/10

---

## Objective

Publish official container images for Terminal Zero Governance and make them consumable by external operators.

Primary success outcome: a user can run:

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
- Registry README (`docs/deploy/image-registry.md`)
- Docs updates:
  - `docs/getting-started.md` (container path)
  - `docs/deploy/aws-eks.md`
  - `docs/deploy/azure-aks.md`
  - `docs/deploy/gcp-gke.md`

### Out of scope
- Multi-arch (`arm64`) release images
- Vulnerability scan gating
- Helm chart publication automation

---

## Baseline / Current State

- `.github/workflows/publish-images.yml` exists and is structurally correct.
- `CHANGELOG.md` contains `0.2.0` entry (no semver gate gap).
- Gap: `docs/getting-started.md` has no container path.
- Gap: cloud deploy docs still emphasize local build/push instead of published image pull.
- Gap: `docs/deploy/image-registry.md` missing.
- Gap: this plan file was previously truncated at Step 9.

---

## Workflow Behavior Clarification (patched)

`workflow_dispatch` runs against the selected ref.

Current behavior is ref-based:
- Tag refs (`v*`) -> full publish/sign/SBOM path (GHCR + Docker Hub + sign + SBOM)
- Branch refs -> edge publish path

In short: full publish/sign/SBOM only occur on tag refs (`v*`), while branch refs follow edge path.

---

## Deliverables

- [x] `.github/workflows/publish-images.yml` present
- [ ] `docs/deploy/image-registry.md` created
- [ ] `docs/getting-started.md` updated with container quickstart
- [ ] `docs/deploy/aws-eks.md` updated for published image-first flow
- [ ] `docs/deploy/azure-aks.md` updated for published image-first flow
- [ ] `docs/deploy/gcp-gke.md` updated for published image-first flow
- [ ] `docs/evidence/phase1_image_publish_evidence.md` captured after first publish run

---

## Acceptance Gates

1. `docker pull ghcr.io/<org>/terminal-zero-governance:latest` succeeds.
2. `docker pull docker.io/<org>/terminal-zero-governance:latest` succeeds.
3. Image digest stable across repeated pulls.
4. `cosign download sbom` succeeds on published GHCR image.
5. `cosign verify` succeeds for GHCR release image.
6. Publish workflow run is green on release tag push.
7. `sop healthcheck` in container exits 0.
8. Getting-started doc references published image path.

---

## Execution Steps

### Step 1 — Pre-flight (human)
- Ensure `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` secrets exist in GitHub repo.
- Confirm Docker Hub repo exists.
- After first successful publish, set GHCR package visibility to public.

### Step 2 — Docs patch set
- Create `docs/deploy/image-registry.md`.
- Update getting-started to include container quickstart.
- Update AWS/Azure/GCP deploy docs to show pull-from-GHCR first.

### Step 3 — Commit
```bash
cd e:\Code\SOP\quant_current_scope
git add .github/workflows/publish-images.yml docs/
git commit -m "docs(phase1): patch container publish gaps and deployment docs"
```

### Step 4 — Release publish trigger
```bash
git push origin main
git tag v0.2.0
git push origin v0.2.0
```

### Step 5 — Verify gates + capture evidence
Create `docs/evidence/phase1_image_publish_evidence.md` with pull, signature, and SBOM outputs.

---

## Risk Notes

- If `DOCKERHUB_USERNAME` secret is missing, release path will fail on Docker Hub-related push/tag generation; GHCR path still validates workflow wiring.
- `workflow_dispatch` on branches publishes edge path only by design.
- Phase 1 completion unblocks Phase 3, 4, and 6 execution in parallel.
