# Security Operations Policy (Internal Companion)

## Purpose
Define mandatory internal security controls for loop operations in this repository with fail-closed behavior.

## Relationship to Root `SECURITY.md`
- Root `SECURITY.md` is the public disclosure entrypoint for external reporters.
- This file is the internal operator/worker/auditor security operations companion.
- If there is any wording tension, use root `SECURITY.md` for external disclosure flow and this file for internal execution controls.
- This file does not define a bug bounty program or SLA commitment.

## Scope
- Applies to Worker, Auditor, and Operator actions in this repo.
- Applies to local CLI runs, artifact generation, escalation readiness, and governance evidence.
- Complements `docs/loop_operating_contract.md` and `docs/runbook_ops.md`.

## Command Safety Boundaries
1. Only run approved operational commands from runbook/contract paths.
2. Never bypass closure checks (`validate_loop_closure.py`) before escalation.
3. `--allow-hold` is reporting semantics only; it must not be treated as readiness.
4. Never force `READY_TO_ESCALATE` when `ceo_go_signal.md` is `HOLD` or `REFRAME`.
5. Never skip evidence gates (`tdd_contract_gate`, truth checks, memory truth checks) for speed.
6. Prohibit destructive repo commands during operations:
   - `git reset --hard`
   - `git checkout -- <file>`
   - `git clean -fd`
   - force push to protected branches
7. Prohibit suppression flags that disable safeguards unless explicitly approved and logged.
8. Execute commands with least privilege and repo-local paths only.

## Credential and Secret Handling
1. Do not store secrets in:
   - `docs/context/*`
   - `docs/*.md`
   - test fixtures or traceability files
2. Use environment variables for credentials, not inline CLI literals.
3. Redact secret-like values from logs and reports before sharing to PM/CEO.
4. Never commit `.env`, private keys, tokens, or credentials.
5. If accidental exposure occurs, treat as incident and rotate immediately.

## External Dependency and Network Constraints
1. Prefer local deterministic validators over network calls.
2. Any external API/network action must have:
   - clear operational need
   - bounded scope
   - evidence entry in decision/audit trail
3. Pin tool/script behavior to repo-controlled files where possible.
4. Do not fetch or execute remote code during active incident response.
5. Block escalation if artifact truth depends on unavailable external services.

## Incident Severity Classes
### S0 Critical
- Security breach, secret leak, or integrity compromise of escalation artifacts.
- Response expectation: immediate stop, force `HOLD`, notify PM+CEO same cycle.

### S1 High
- Infra error (`exit 2`) in truth/closure/memory validators.
- Gate contradiction that could produce false `READY_TO_ESCALATE`.
- Response expectation: stop escalation path, triage within same day.

### S2 Medium
- Drift or stale artifacts without security compromise.
- Missing required evidence links or incomplete audit packet.
- Response expectation: remediate in current or next cycle before escalation.

### S3 Low
- Non-blocking hygiene issues (formatting, optional fields, readability).
- Response expectation: backlog and resolve within weekly review.

## Response Expectations
1. S0/S1: stop escalation immediately and set recommendation to `HOLD`.
2. S0: rotate/disable affected credentials before resuming.
3. S1/S2: regenerate impacted artifacts and re-run failed gates.
4. No incident is closed without linked evidence and closure note.
5. If uncertainty remains, default to fail-closed (`HOLD`/`NOT_READY`).

## Evidence and Audit Trail Requirements
Each incident or security-relevant event must include:
1. `run_id` and UTC timestamp.
2. Trigger gate/check and exit code (`0/1/2`).
3. Impacted artifacts (absolute/relative paths).
4. Owner, triage action, and resolution status.
5. Evidence links:
   - `docs/context/loop_cycle_summary_latest.json`
   - `docs/context/loop_closure_status_latest.json`
   - `docs/context/ceo_go_signal.md`
6. Decision reference in `docs/decision log.md` when override or policy exception occurs.

## Minimum Security Audit Packet Before Escalation
1. Latest closure status exists and is `READY_TO_ESCALATE`.
2. GO signal recommendation is `GO`.
3. `tdd_contract_gate=PASS`.
4. Memory truth and weekly truth checks are `PASS`.
5. No open S0/S1 incidents.

## Non-Compliance
Failure to follow this policy requires:
1. immediate `HOLD`
2. incident entry
3. PM review before next escalation attempt
