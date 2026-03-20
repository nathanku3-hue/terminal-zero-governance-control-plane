# Releasing

This repository is a script-first governance control plane.
Releases publish source, docs, and validation evidence.
No hosted-service, plugin-runtime, worker-fleet, or rollout-automation deployment steps are part of this release process.

## Current Release Mode

- Release remains **manual-only** for now.
- A human release owner performs the cut and publishes release notes.

## 1.0 Release Boundary

**Shipped product:**
- `sop` CLI (`sop startup`, `sop run`, `sop validate`, `sop takeover`, `sop supervise`, `sop init`)
- Kernel templates for truth surfaces
- PyPI install path (`pip install terminal-zero-governance`)

**Supported platforms:**
- Python 3.12+
- Windows, Linux (macOS best-effort)

**Compatibility preserved:**
- `scripts/*.py` entrypoints remain functional for existing workflows
- New users should prefer `sop` CLI

**Not promised (future work):**
- Hosted service
- npm/npx scaffolding
- GitHub Action
- VS Code extension
- Zero-human autopilot

## Release Cut Criteria

Before cutting a release:

1. **Docs aligned:** `README.md`, `USER_GUIDE.md`, `RELEASING.md`, `SECURITY.md`, `CONTRIBUTING.md` are present and consistent.

2. **Tests pass:**
   ```bash
   python -m pytest -q
   ```

3. **CLI smoke test:**
   ```bash
   sop --help
   sop version
   sop init /tmp/smoke-test
   ```

4. **Version tag matches pyproject.toml.**

5. **Changelog has entry for version.**

## Version and Tag Rule

- Use SemVer tags in the form `vX.Y.Z`.
- Tag version must match `project.version` in `pyproject.toml`.
- First public release should use the current project version as the initial public tag (for example, `v0.1.0` when `pyproject.toml` is `0.1.0`).
- Public-beta framing may live in the GitHub release title/body while the tag remains stable SemVer (`v0.1.0` instead of a prerelease suffix) when maintainers want a cleaner package/version boundary.

## Release Notes Source

- Release notes are authored manually in the GitHub release body.
- Primary sources:
  - merged PR summaries since the previous tag,
  - relevant governance decisions in `docs/decision log.md`,
  - user-visible contract/runbook changes in core docs.

## Release Authority

- Only repository maintainers with write access may cut a release.
- Each release must name a single release owner in the release notes.

## PyPI Publishing

Releases are automatically published to PyPI when a version tag is pushed, **after** all validation checks pass.

### One-Time Setup (Trusted Publisher)

Before the first release, configure Trusted Publisher on PyPI:

1. Go to: https://pypi.org/manage/project/terminal-zero-governance/settings/publishing/
2. Add a new trusted publisher:
   - **Owner**: Your GitHub username or org
   - **Repository**: Your repo name
   - **Workflow**: `release-validation.yml`
   - **Environment**: Leave blank (or create an environment if desired)

3. Save the configuration.

After this one-time setup, pushing a version tag (`git push origin v0.1.0`) will:
1. Trigger `release-validation.yml`
2. Run all validation jobs (CLI smoke, backward compat, semver check, release gate, tests)
3. **Only if all validation passes**: Build wheel and publish to PyPI
4. If validation fails: No publish (tag is rejected)

### Cutting a Release

1. Verify all release cut criteria above are met.
2. Update `pyproject.toml` version if needed.
3. Create and push the tag:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```
4. Monitor the workflow at: Actions → Release Validation
5. Once published, create a GitHub release with notes.

### Verifying Installation

After publish:
```bash
pip install terminal-zero-governance
sop --help
sop version
```

## Follow-Up Note (Approved)

- If CODEOWNERS maintainer-handle confirmation is not finalized before release, the release owner must record it as a follow-up item immediately after release and link that follow-up in the release notes.

