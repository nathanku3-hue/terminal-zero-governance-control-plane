# Terminal Zero Governance Container Images

Official container images for Terminal Zero Governance are published for production and evaluation workflows.

## Registries

- GHCR: `ghcr.io/<org>/terminal-zero-governance`
- Docker Hub: `docker.io/<org>/terminal-zero-governance`

## Quick Start

```bash
docker pull ghcr.io/<org>/terminal-zero-governance:latest
docker run --rm ghcr.io/<org>/terminal-zero-governance:latest sop healthcheck
docker run --rm ghcr.io/<org>/terminal-zero-governance:latest sop version
```

Expected: `sop healthcheck` exits 0.

## Tags

| Tag | Meaning |
|---|---|
| `latest` | Most recent stable release tag publish |
| `edge` | Latest main/master branch publish |
| `X.Y.Z` | Immutable semver release image |
| `X` | Major-line alias for semver release |

## Run Against a Repo

```bash
docker run --rm \
  -v "$PWD:/workspace" \
  ghcr.io/<org>/terminal-zero-governance:latest \
  sop run --repo-root /workspace --skip-phase-end
```

## Verify Signature and SBOM

```bash
cosign verify \
  --certificate-identity-regexp='https://github.com/.+/.+/.github/workflows/publish-images.yml' \
  --certificate-oidc-issuer='https://token.actions.githubusercontent.com' \
  ghcr.io/<org>/terminal-zero-governance:latest

cosign download sbom ghcr.io/<org>/terminal-zero-governance:latest
```

## Docs

- Getting started: `docs/getting-started.md`
- User guide: `USER_GUIDE.md`
- Cloud deployment guides: `docs/deploy/`

## Release Entry Policy

- Intended release entrypoint: `.github/workflows/release-bump-and-tag.yml`
- `.github/workflows/publish-images.yml` manual dispatch is for controlled operator use only.
- Manual dispatch requires explicit `mode`:
  - `mode=edge` for branch refs
  - `mode=release` for `v*` tag refs
- Mode/ref mismatch fails fast by design to prevent accidental release-mode misuse.
