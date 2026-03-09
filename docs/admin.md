# Admin Operations Guide

## Purpose
Define operator cadence, escalation thresholds, and override discipline for daily loop supervision.

## Scope
- Applies to active loop operations and phase-end cycles in `quant_current_scope`.
- Focuses on operational governance, not feature design.

## Supervisor Cadence
### Per-cycle (every loop run)
1. Confirm latest cycle artifacts exist and are fresh:
   - `docs/context/loop_cycle_summary_latest.json`
   - `docs/context/loop_closure_status_latest.json`
   - `docs/context/ceo_go_signal.md`
2. Verify gate outcomes:
   - truth checks pass
   - closure status aligns with recommendation
3. Confirm recommendation consistency:
   - `GO` only when closure says `READY_TO_ESCALATE`
   - `HOLD`/`REFRAME` implies `NOT_READY`

### Daily
1. Start-of-day review: open blockers, unresolved incidents, stale artifacts.
2. Mid-day check: drift thresholds and SLA timers.
3. End-of-day summary: status to PM (and CEO when escalated).

### Weekly
1. Review drift trends and recurring disagreement categories.
2. Review override usage and exceptions.
3. Confirm checklist compliance and close unresolved S2/S3 items.

## Drift Escalation Thresholds
Trigger escalation to PM when any threshold is met:
1. Any truth validator returns `exit 2` (infra/input failure).
2. Weekly/GO/closure values are inconsistent in same cycle.
3. Closure indicates `READY_TO_ESCALATE` while recommendation is not `GO`.
4. Required evidence artifact is missing or stale for active cycle.
5. Repeated `HOLD` due to same unresolved blocker for 2+ consecutive cycles.

Escalate to CEO when:
1. PM decision is blocked beyond SLA for a high-severity issue.
2. Strategic `GO/HOLD/REFRAME` conflict cannot be resolved by PM.
3. Risk impacts rollout decision or executive commitment.

## Auto-Action Policy (Force HOLD / Stop Escalation)
Force `HOLD` and stop escalation immediately when:
1. Any critical gate returns `exit 2`.
2. `tdd_contract_gate` is not `PASS`.
3. `go_signal_action_gate` fails (`GO` not present).
4. Required closure evidence is missing.
5. Incident class S0/S1 is open.

Do not resume escalation until:
1. blocking gate re-run passes
2. evidence is refreshed
3. closure status returns to eligible state

## Notification Protocol (PM / CEO)
### PM notification (default)
Send within same cycle for high severity, next cycle for medium:
1. `run_id`
2. current recommendation (`GO|HOLD|REFRAME`)
3. failed gate/check + exit code
4. impacted artifacts
5. required decision and due time

### CEO notification (escalated only)
Send when PM escalation criteria are met:
1. concise executive impact statement
2. recommendation options with preferred action
3. evidence links and ETA to recovery

## Override Authority and Logging
1. Worker cannot self-override Auditor high-risk blocks.
2. Auditor cannot approve strategic escalation; CEO decides `GO/HOLD/REFRAME`.
3. PM can approve operational overrides within policy bounds.
4. CEO resolves strategic conflicts or unresolved PM escalations.
5. Every override requires a log entry in `docs/decision log.md`:
   - timestamp (UTC)
   - approver role/name
   - reason
   - evidence links
   - rollback condition

## Daily Checklist
- [ ] Cycle executed and latest artifacts refreshed
- [ ] Truth checks reviewed (`weekly`, `memory`, `closure`)
- [ ] Recommendation and closure state aligned
- [ ] No open S0/S1 incidents
- [ ] PM notified for any threshold breach
- [ ] Decision log updated for exceptions/overrides

## Weekly Checklist
- [ ] Drift trend reviewed (frequency, type, impact)
- [ ] Repeat blockers identified and owner assigned
- [ ] Override log reviewed with PM
- [ ] Escalation quality reviewed (signal-to-noise)
- [ ] Process adjustments documented (if needed)

## Concise Operator Run Card
1. Run cycle.
2. Validate gates.
3. If any hard failure: force `HOLD`.
4. Notify PM with evidence.
5. Re-run after fix.
6. Escalate to CEO only when closure is truly ready.
