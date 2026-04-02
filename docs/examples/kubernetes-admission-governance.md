# Kubernetes Admission Governance

## Context
A platform SRE team wants to gate Kubernetes admission policy updates through Terminal Zero before applying policy bundles to production clusters.

## Inputs
- Admission policy repository with pending changes.
- `terminal-zero-governance` installed in operator environment.
- Current policy bundle path: `policies/admission/`.
- Approval expectation: block on unresolved governance failures.

## Commands
```bash
pip install terminal-zero-governance
sop init admission-governed-repo
sop run --repo-root admission-governed-repo --skip-phase-end
sop audit --repo-root admission-governed-repo --tail 10
sop validate --repo-root admission-governed-repo
```

## Output
```text
$ sop audit --repo-root admission-governed-repo --tail 10
2026-03-31T09:14:22Z gate=policy decision=PASS trace_id=trc-9f2a1e4b
2026-03-31T09:14:23Z gate=admission-risk decision=HOLD trace_id=trc-9f2a1e4b
2026-03-31T09:14:24Z gate=closure decision=PASS trace_id=trc-9f2a1e4b

$ sop validate --repo-root admission-governed-repo
status=READY_TO_ESCALATE
```

## Expected Decision
Proceed when governance indicates `PASS` or a documented `HOLD` with human sign-off. Do not roll out admission policy changes if governance emits `FAIL` or `BLOCK`.

## Replay Proof (Kubernetes Scenario Class)
- Proof type: cluster governance replay excerpt.
- Required evidence commands: `sop audit --repo-root admission-governed-repo --tail 10` and `sop validate --repo-root admission-governed-repo`.
- Verification rule: decision trail and readiness status must be coherent with rollout approval policy.
