# Releasing

This repository is a script-first governance control plane.  
Releases publish source, docs, and validation evidence.  
No hosted-service, plugin-runtime, worker-fleet, or rollout-automation deployment steps are part of this release process.

## Current Release Mode

- Release remains **manual-only** for now.
- A human release owner performs the cut and publishes release notes.

## Shipped v1 Release Boundary

- A release covers only the current local governance control-plane kernel:
  - `scripts/startup_codex_helper.py`
  - `scripts/run_loop_cycle.py`
  - `scripts/validate_loop_closure.py`
  - `scripts/print_takeover_entrypoint.py`
  - `scripts/supervise_loop.py`
  - the supporting operator docs, tests, and artifact contracts for that flow
- Release validation is against that current shipped `v1` surface only.
- Phase 5 future-state architecture surfaces remain draft ideas, not shipped release commitments.
- Plugin architecture, benchmark harness productization, skills registry productization, subagent routing, worker inner-loop automation, rollout automation, adaptive guardrails, and broader memory optimization are out of scope for the current release boundary unless they are separately approved, implemented, and added to this checklist.

## Stream C Implementation Status (Non-Scope-Expanding)

- Stream C implementation is complete in-repo through C2 (`d8a3240`).
- C2 introduced the `should_compact` versus `can_compact` decision split and deterministic compaction reporting in loop summaries.
- Hygiene debt remains deferred and non-blocking (`MILESTONE_OPTIMALITY_REVIEW_LATEST.md`, `docs/context/phase_end_logs/` churn).
- This status note does not expand release scope by itself.

## First Public Release Cut Criteria

Before cutting the first public release:
- Required repository docs are present and aligned: `README.md`, `SECURITY.md`, `CONTRIBUTING.md`, and `RELEASING.md`.
- Governance/operator docs are internally consistent with current behavior (`docs/runbook_ops.md`, `docs/loop_operating_contract.md`).
- Future-state architecture notes remain explicitly marked as draft material and do not redefine the shipped `v1` boundary.
- Validation commands pass on release candidate `HEAD` for the current shipped `v1` surface:

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

