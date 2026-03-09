# Governance

## Purpose

This project maintains a script-driven AI engineering governance control plane with auditable startup, loop, closure, and takeover artifacts.

Governance decisions should preserve:
- deterministic local execution,
- explicit evidence and artifact contracts,
- fail-closed escalation behavior.

## Project Authorities

- Maintainers review and merge contributions, steward policy, and decide roadmap priorities.
- Contributors propose changes via pull requests and issues.
- In case of tie or ambiguity, maintainer judgment is final for repository decisions.

## Decision Process

1. Propose change in an issue or pull request.
2. Link behavior changes to concrete script/doc/test updates.
3. Require review before merge for non-trivial changes.
4. Record major policy/operational decisions in `docs/decision log.md`.

## Change Classes

- **Routine**: docs clarifications, small test improvements, non-behavioral cleanup.
- **Operational**: script behavior changes affecting loop execution or closure outcomes.
- **Governance-critical**: changes to truth checks, escalation gates, authority model, or artifact integrity guarantees.

Operational and governance-critical changes should include explicit validation evidence in PR notes.

## Release and Compatibility Posture

- The repository is operated as a script-first control plane.
- Backward compatibility should be considered for artifact contracts consumed by downstream scripts.
- If a contract must change, document migration impact in the same PR.

## Related References

- `docs/loop_operating_contract.md`
- `docs/runbook_ops.md`
- `docs/decision log.md`
- `OPERATOR_LOOP_GUIDE.md`
