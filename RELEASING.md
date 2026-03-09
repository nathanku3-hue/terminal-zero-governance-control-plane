# Releasing

This repository is a script-first governance control plane.  
Releases publish source, docs, and validation evidence.  
No hosted-service deployment steps are part of this release process.

## Current Release Mode

- Release remains **manual-only** for now.
- A human release owner performs the cut and publishes release notes.

## First Public Release Cut Criteria

Before cutting the first public release:
- Required repository docs are present and aligned: `README.md`, `SECURITY.md`, `CONTRIBUTING.md`, and `RELEASING.md`.
- Governance/operator docs are internally consistent with current behavior (`docs/runbook_ops.md`, `docs/loop_operating_contract.md`).
- Validation commands pass on release candidate `HEAD`:

```powershell
python scripts/startup_codex_helper.py --help
python scripts/run_loop_cycle.py --help
python scripts/supervise_loop.py --max-cycles 1
python scripts/run_fast_checks.py --repo-root .
python -m pytest -q
```

## Version and Tag Rule

- Use SemVer tags in the form `vX.Y.Z`.
- Tag version must match `project.version` in `pyproject.toml`.
- First public release should use the current project version as the initial public tag (for example, `v0.1.0` when `pyproject.toml` is `0.1.0`).

## Release Notes Source

- Release notes are authored manually in the GitHub release body.
- Primary sources:
  - merged PR summaries since the previous tag,
  - relevant governance decisions in `docs/decision log.md`,
  - user-visible contract/runbook changes in core docs.

## Release Authority

- Only repository maintainers with write access may cut a release.
- Each release must name a single release owner in the release notes.

## Follow-Up Note (Approved)

- If CODEOWNERS maintainer-handle confirmation is not finalized before release, the release owner must record it as a follow-up item immediately after release and link that follow-up in the release notes.

